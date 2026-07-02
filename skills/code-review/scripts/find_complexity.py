#!/usr/bin/env python3
"""
Find complexity hotspots: large files, long functions, cyclomatic complexity,
cognitive complexity, excessive parameters, and deep nesting.

Heuristic, not a parser. Known limitations: nested functions split their
parent's span; a function's span ends at the next function declaration.
Numbers are indicative — treat flagged functions as candidates to read,
not as precise metrics.
"""
import os
import re
import sys

from common import iter_source_files, read_text

root = sys.argv[1] if len(sys.argv) > 1 else "."

SOURCE_EXTS = {".ts", ".tsx", ".js", ".jsx", ".vue", ".py", ".go", ".php",
               ".java", ".cs", ".rs", ".rb"}
# Languages with real function-extraction patterns. Others (.rb) only get the
# large-file check — better an honest gap than garbage numbers.
FUNC_EXTS = {".ts", ".tsx", ".js", ".jsx", ".vue", ".py", ".go", ".php",
             ".java", ".cs", ".rs"}

# Thresholds
FILE_LINE_LIMIT = 300
FUNC_LINE_LIMIT = 50
CYCLOMATIC_LIMIT = 10       # NIST standard
COGNITIVE_LIMIT = 15        # SonarQube default
PARAM_LIMIT = 5
NESTING_LIMIT = 4
MAX_LARGE_FILES = 20

# Branch counting. Keywords need \b; operators must NOT use \b (\b&&\b can
# never match — & is a non-word char, so there is no word boundary around it).
BRANCH_PATTERNS_JS = re.compile(
    r"\b(?:if|for|while|case|catch)\b|&&|\|\||\?\?"
)
BRANCH_PATTERNS_PY = re.compile(
    r"\b(?:if|elif|for|while|except|and|or)\b"
)
BRANCH_PATTERNS_GO = re.compile(
    r"\b(?:if|for|case|select)\b|&&|\|\|"
)

NESTING_OPENERS_JS = re.compile(r"\b(?:if|for|while|switch|try)\b")
NESTING_OPENERS_PY = re.compile(r"\b(?:if|for|while|try|with)\b")

# Statement keywords that regex-based "method" detection must never treat as a
# function name — `if (cond) {` looks exactly like `method(args) {` otherwise.
STATEMENT_KEYWORDS = (
    "if|for|while|switch|catch|else|do|return|new|await|typeof|function|"
    "yield|throw|delete|void|in|of|with"
)

_STRING_RE = re.compile(
    r"'(?:\\.|[^'\\])*'|\"(?:\\.|[^\"\\])*\"|`(?:\\.|[^`\\])*`"
)
_LINE_COMMENT_RE = re.compile(r"//.*$|#.*$")


def strip_noise(line):
    """Remove string literal contents and trailing line comments so branch
    keywords inside strings/comments don't count as complexity."""
    line = _STRING_RE.sub('""', line)
    return _LINE_COMMENT_RE.sub("", line)


class FunctionInfo:
    def __init__(self, name, fpath, start_line, language):
        self.name = name
        self.fpath = fpath
        self.start_line = start_line
        self.language = language
        self.end_line = start_line
        self.lines = []
        self.param_count = 0
        self.cyclomatic = 1  # base complexity
        self.cognitive = 0
        self.max_nesting = 0

    @property
    def line_count(self):
        return self.end_line - self.start_line + 1

    def analyze(self):
        if self.language == "py":
            branch_re, nesting_re = BRANCH_PATTERNS_PY, NESTING_OPENERS_PY
        elif self.language == "go":
            branch_re, nesting_re = BRANCH_PATTERNS_GO, NESTING_OPENERS_JS
        else:
            branch_re, nesting_re = BRANCH_PATTERNS_JS, NESTING_OPENERS_JS

        if self.language == "py":
            self._analyze_indent(branch_re, nesting_re)
        else:
            self._analyze_braces(branch_re, nesting_re)

    def _analyze_indent(self, branch_re, nesting_re):
        # Nesting depth from indentation. The def line itself is depth 0; the
        # first body line establishes the body indent and the indent unit, so
        # tabs and 2-space projects measure correctly.
        def_indent = None
        body_indent = None
        for raw in self.lines:
            line = raw.expandtabs(4)
            stripped = strip_noise(line).strip()
            if not stripped:
                continue
            indent = len(line) - len(line.lstrip())
            if def_indent is None:
                def_indent = indent
                continue  # the def line itself contributes no branches
            if body_indent is None:
                body_indent = indent
            unit = max(1, body_indent - def_indent)

            self.cyclomatic += len(branch_re.findall(stripped))
            current_depth = max(0, (indent - body_indent) // unit)
            self.max_nesting = max(self.max_nesting, current_depth)
            nesting_hits = len(nesting_re.findall(stripped))
            if nesting_hits:
                self.cognitive += nesting_hits * (1 + current_depth)

    def _analyze_braces(self, branch_re, nesting_re):
        brace_depth = 0
        first = True
        for raw in self.lines:
            stripped = strip_noise(raw).strip()
            if not stripped or stripped.startswith(("/*", "*")):
                brace_depth += stripped.count("{") - stripped.count("}")
                continue
            if first:
                first = False  # declaration line: count its braces, no branches
                brace_depth += stripped.count("{") - stripped.count("}")
                continue

            self.cyclomatic += len(branch_re.findall(stripped))
            current_depth = max(0, brace_depth - 1)  # depth 1 = function body
            self.max_nesting = max(self.max_nesting, current_depth)
            nesting_hits = len(nesting_re.findall(stripped))
            if nesting_hits:
                self.cognitive += nesting_hits * (1 + current_depth)
            brace_depth += stripped.count("{") - stripped.count("}")


def detect_language(fname):
    ext = os.path.splitext(fname)[1]
    if ext in (".ts", ".tsx", ".js", ".jsx", ".vue", ".svelte"):
        return "js"
    if ext == ".py":
        return "py"
    if ext == ".go":
        return "go"
    if ext == ".php":
        return "php"
    if ext == ".rs":
        return "rs"
    if ext in (".java", ".cs"):
        return "java"
    return "js"


def function_patterns(language):
    if language == "go":
        return [re.compile(r"\s*func\s+(?:\(\w+\s+\*?\w+\)\s+)?(\w+)\s*\(([^)]*)\)")]
    if language == "rs":
        return [re.compile(r"\s*(?:pub(?:\([^)]*\))?\s+)?(?:async\s+)?(?:unsafe\s+)?fn\s+(\w+)\s*[<(]([^)]*)\)?")]
    if language == "java":
        # modifiers + return type + name(params) {
        return [re.compile(
            r"\s*(?:(?:public|private|protected|static|final|abstract|synchronized|override|virtual|async)\s+)+"
            r"[\w<>\[\],\s]+?\s(\w+)\s*\(([^)]*)\)\s*(?:throws\s+[\w,\s]+)?\{"
        )]
    # JS/TS/PHP
    return [
        # function name(...) / async function name(...)  (also PHP)
        re.compile(r"\s*(?:export\s+)?(?:public\s+|private\s+|protected\s+|static\s+)*(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)"),
        # const name = (...) => / const name = function(...)
        re.compile(r"\s*(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?(?:\([^)]*\)|[^=\n])*?(?:=>|\bfunction\b)"),
        # class method: name(params) { — with a guard so `if (x) {` / `for (...) {`
        # are never mistaken for a method (that bug made every JS function end
        # at its first branch and produced garbage metrics)
        re.compile(
            r"\s*(?:async\s+)?(?:static\s+)?(?:get\s+|set\s+)?"
            r"(?!(?:" + STATEMENT_KEYWORDS + r")\b)"
            r"(\w+)\s*\(([^)]*)\)\s*(?::\s*[\w<>\[\]|&,.\s]+)?\s*\{"
        ),
    ]


def extract_functions_braces(lines, fpath, language):
    functions = []
    current = None
    patterns = function_patterns(language)

    for i, line in enumerate(lines):
        for pattern in patterns:
            m = pattern.match(line)
            if m:
                if current:
                    current.end_line = i
                    current.lines = lines[current.start_line - 1:i]
                    current.analyze()
                    functions.append(current)

                name = m.group(1)
                params_str = m.group(2) if (m.lastindex or 0) >= 2 else ""
                param_count = len([p for p in params_str.split(",") if p.strip()])

                current = FunctionInfo(name, fpath, i + 1, language)
                current.param_count = param_count
                break

    if current:
        current.end_line = len(lines)
        current.lines = lines[current.start_line - 1:]
        current.analyze()
        functions.append(current)

    return functions


def extract_functions_py(lines, fpath):
    functions = []
    current = None

    func_pattern = re.compile(r"^(\s*)(?:async\s+)?def\s+(\w+)\s*\(([^)]*(?:\([^)]*\))*[^)]*)\)")

    for i, line in enumerate(lines):
        m = func_pattern.match(line)
        if m:
            indent = len(m.group(1).expandtabs(4))
            if current and indent <= current._indent:
                current.end_line = i
                current.lines = lines[current.start_line - 1:i]
                current.analyze()
                functions.append(current)

            name = m.group(2)
            params = [p.strip().split(":")[0].split("=")[0].strip()
                      for p in m.group(3).split(",") if p.strip()]
            params = [p for p in params if p not in ("self", "cls", "*", "/")]

            current = FunctionInfo(name, fpath, i + 1, "py")
            current.param_count = len(params)
            current._indent = indent

    if current:
        current.end_line = len(lines)
        current.lines = lines[current.start_line - 1:]
        current.analyze()
        functions.append(current)

    return functions


def vue_script_lines(lines):
    """Only the <script> block of a Vue/Svelte SFC — analyzing the template
    would attribute v-if branches to whatever function came last in the script.
    Line numbers are preserved by blanking non-script lines."""
    out = []
    in_script = False
    for line in lines:
        if re.match(r"\s*<script\b", line):
            in_script = True
            out.append("")
            continue
        if re.match(r"\s*</script>", line):
            in_script = False
            out.append("")
            continue
        out.append(line if in_script else "")
    return out


def main():
    large_files = []
    all_functions = []
    file_check_only = set()

    for fpath in iter_source_files(root, SOURCE_EXTS):
        ext = os.path.splitext(fpath)[1]
        content = read_text(fpath)
        if content is None:
            continue
        lines = content.splitlines(keepends=True)

        if len(lines) > FILE_LINE_LIMIT:
            large_files.append((fpath, len(lines)))

        if ext not in FUNC_EXTS:
            file_check_only.add(ext)
            continue

        if ext in (".vue", ".svelte"):
            lines = vue_script_lines(lines)

        language = detect_language(fpath)
        if language == "py":
            all_functions.extend(extract_functions_py(lines, fpath))
        else:
            all_functions.extend(extract_functions_braces(lines, fpath, language))

    # --- Report ---
    has_output = False

    if large_files:
        has_output = True
        print(f"=== Large files (>{FILE_LINE_LIMIT} lines) ===")
        ranked = sorted(large_files, key=lambda x: -x[1])
        for fpath, count in ranked[:MAX_LARGE_FILES]:
            print(f"  {count:>5} lines  {fpath}")
        if len(ranked) > MAX_LARGE_FILES:
            print(f"  ... and {len(ranked) - MAX_LARGE_FILES} more files over the limit")

    long_funcs = [f for f in all_functions if f.line_count > FUNC_LINE_LIMIT]
    if long_funcs:
        has_output = True
        print(f"\n=== Long functions (>{FUNC_LINE_LIMIT} lines) ===")
        for fn in sorted(long_funcs, key=lambda x: -x.line_count)[:20]:
            print(f"  {fn.line_count:>4} lines  {fn.name}() at {fn.fpath}:{fn.start_line}")

    complex_funcs = [f for f in all_functions if f.cyclomatic > CYCLOMATIC_LIMIT]
    if complex_funcs:
        has_output = True
        print(f"\n=== High cyclomatic complexity (>{CYCLOMATIC_LIMIT}, NIST threshold) ===")
        for fn in sorted(complex_funcs, key=lambda x: -x.cyclomatic)[:20]:
            print(f"  CC={fn.cyclomatic:>3}  {fn.name}() at {fn.fpath}:{fn.start_line}  ({fn.line_count} lines)")

    cognitive_funcs = [f for f in all_functions if f.cognitive > COGNITIVE_LIMIT]
    if cognitive_funcs:
        has_output = True
        print(f"\n=== High cognitive complexity (>{COGNITIVE_LIMIT}, SonarQube threshold) ===")
        for fn in sorted(cognitive_funcs, key=lambda x: -x.cognitive)[:20]:
            print(f"  CogC={fn.cognitive:>3}  {fn.name}() at {fn.fpath}:{fn.start_line}  (nesting depth: {fn.max_nesting})")

    param_funcs = [f for f in all_functions if f.param_count > PARAM_LIMIT]
    if param_funcs:
        has_output = True
        print(f"\n=== Functions with many parameters (>{PARAM_LIMIT}) ===")
        for fn in sorted(param_funcs, key=lambda x: -x.param_count)[:15]:
            print(f"  {fn.param_count:>2} params  {fn.name}() at {fn.fpath}:{fn.start_line}")

    nested_funcs = [f for f in all_functions if f.max_nesting > NESTING_LIMIT]
    if nested_funcs:
        has_output = True
        print(f"\n=== Deep nesting (>{NESTING_LIMIT} levels) ===")
        for fn in sorted(nested_funcs, key=lambda x: -x.max_nesting)[:15]:
            print(f"  depth={fn.max_nesting}  {fn.name}() at {fn.fpath}:{fn.start_line}")

    if not has_output:
        print("No complexity hotspots found. Nice.")
    else:
        total = len(all_functions)
        flagged = len(set(
            f.name + f.fpath for f in all_functions
            if f.line_count > FUNC_LINE_LIMIT or f.cyclomatic > CYCLOMATIC_LIMIT
            or f.cognitive > COGNITIVE_LIMIT or f.param_count > PARAM_LIMIT
            or f.max_nesting > NESTING_LIMIT
        ))
        print(f"\n{flagged} of {total} functions flagged across all checks.")
    if file_check_only:
        exts = ", ".join(sorted(file_check_only))
        print(f"Note: {exts} files got the large-file check only (no reliable function metrics for these languages).")


if __name__ == "__main__":
    main()
