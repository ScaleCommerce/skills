#!/usr/bin/env python3
"""
Find complexity hotspots: large files, long functions, cyclomatic complexity,
cognitive complexity, excessive parameters, and deep nesting.
"""
import os
import re
import sys

root = sys.argv[1] if len(sys.argv) > 1 else "."

SKIP_DIRS = {
    "node_modules", ".git", "vendor", "dist", "__pycache__", ".venv",
    ".nuxt", ".next", ".output", "build", "coverage", ".tox", "venv",
}
SOURCE_EXTS = {".ts", ".tsx", ".js", ".jsx", ".vue", ".py", ".go", ".php", ".rb", ".java", ".rs"}

# Thresholds
FILE_LINE_LIMIT = 300
FUNC_LINE_LIMIT = 50
CYCLOMATIC_LIMIT = 10       # NIST standard
COGNITIVE_LIMIT = 15         # SonarQube default
PARAM_LIMIT = 5
NESTING_LIMIT = 4

# Branch keywords that increase cyclomatic complexity
BRANCH_PATTERNS_JS = re.compile(
    r"\b(?:if|else\s+if|for|while|case|catch|\?\?|&&|\|\|)\b|[^=!<>]=.*\?[^?]"
)
BRANCH_PATTERNS_PY = re.compile(
    r"\b(?:if|elif|for|while|except|and|or)\b"
)
BRANCH_PATTERNS_GO = re.compile(
    r"\b(?:if|else\s+if|for|switch|case|select|&&|\|\|)\b"
)

# Nesting increment keywords (subset of branches that actually create nesting)
NESTING_OPENERS_JS = re.compile(r"\b(?:if|for|while|switch|try)\b")
NESTING_OPENERS_PY = re.compile(r"\b(?:if|for|while|try|with)\b")


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
        """Calculate complexity metrics for this function."""
        if self.language in ("js", "ts"):
            branch_re = BRANCH_PATTERNS_JS
            nesting_re = NESTING_OPENERS_JS
        elif self.language == "py":
            branch_re = BRANCH_PATTERNS_PY
            nesting_re = NESTING_OPENERS_PY
        elif self.language == "go":
            branch_re = BRANCH_PATTERNS_GO
            nesting_re = NESTING_OPENERS_JS  # similar to JS
        else:
            branch_re = BRANCH_PATTERNS_JS
            nesting_re = NESTING_OPENERS_JS

        nesting_level = 0
        if self.language == "py":
            # Python: track nesting by indentation
            base_indent = None
            for line in self.lines:
                stripped = line.rstrip()
                if not stripped or stripped.startswith("#"):
                    continue

                indent = len(line) - len(line.lstrip())
                if base_indent is None:
                    base_indent = indent

                # Count branches for cyclomatic complexity
                branches = len(branch_re.findall(stripped))
                self.cyclomatic += branches

                # Cognitive complexity: increment for each nesting structure,
                # plus a penalty proportional to current nesting depth
                current_depth = max(0, (indent - base_indent) // 4)
                self.max_nesting = max(self.max_nesting, current_depth)

                nesting_hits = len(nesting_re.findall(stripped))
                if nesting_hits:
                    self.cognitive += nesting_hits * (1 + current_depth)
        else:
            # Brace-based languages: track nesting by brace depth
            brace_depth = 0
            base_depth = None
            for line in self.lines:
                stripped = line.strip()
                if not stripped or stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("*"):
                    continue

                if base_depth is None:
                    base_depth = brace_depth

                # Count branches for cyclomatic complexity
                branches = len(branch_re.findall(stripped))
                self.cyclomatic += branches

                # Cognitive complexity with nesting penalty
                current_depth = max(0, brace_depth - (base_depth or 0))
                self.max_nesting = max(self.max_nesting, current_depth)

                nesting_hits = len(nesting_re.findall(stripped))
                if nesting_hits:
                    self.cognitive += nesting_hits * (1 + current_depth)

                # Track brace depth
                brace_depth += stripped.count("{") - stripped.count("}")


def detect_language(fname):
    ext = os.path.splitext(fname)[1]
    if ext in (".ts", ".tsx", ".js", ".jsx", ".vue", ".svelte"):
        return "js"
    elif ext == ".py":
        return "py"
    elif ext == ".go":
        return "go"
    elif ext == ".php":
        return "php"
    elif ext == ".rb":
        return "rb"
    elif ext in (".java", ".rs", ".cs"):
        return ext.lstrip(".")
    return "js"


def extract_functions_js(lines, fpath, language):
    """Extract functions from JS/TS/Go/PHP/Java files."""
    functions = []
    current = None

    # Patterns for function declarations
    func_patterns = [
        # function name(...) or async function name(...)
        re.compile(r"\s*(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)"),
        # const name = (...) => or const name = function(...)
        re.compile(r"\s*(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?(?:\([^)]*\)|[^=])*?(?:=>|\bfunction\b)"),
        # method(params) { — class methods
        re.compile(r"\s*(?:async\s+)?(?:static\s+)?(\w+)\s*\(([^)]*)\)\s*(?::\s*[\w<>\[\]|&]+)?\s*\{"),
    ]
    # Go functions
    if language == "go":
        func_patterns = [
            re.compile(r"\s*func\s+(?:\(\w+\s+\*?\w+\)\s+)?(\w+)\s*\(([^)]*)\)"),
        ]

    for i, line in enumerate(lines):
        for pattern in func_patterns:
            m = pattern.match(line)
            if m:
                # Save previous function
                if current:
                    current.end_line = i
                    current.lines = lines[current.start_line - 1:i]
                    current.analyze()
                    functions.append(current)

                name = m.group(1)
                params_str = m.group(2) if m.lastindex >= 2 else ""
                param_count = len([p for p in params_str.split(",") if p.strip()]) if params_str else 0

                current = FunctionInfo(name, fpath, i + 1, language)
                current.param_count = param_count
                break

    # Close last function
    if current:
        current.end_line = len(lines)
        current.lines = lines[current.start_line - 1:]
        current.analyze()
        functions.append(current)

    return functions


def extract_functions_py(lines, fpath):
    """Extract functions from Python files."""
    functions = []
    current = None

    func_pattern = re.compile(r"^(\s*)(?:async\s+)?def\s+(\w+)\s*\(([^)]*(?:\([^)]*\))*[^)]*)\)")

    for i, line in enumerate(lines):
        m = func_pattern.match(line)
        if m:
            indent = len(m.group(1))
            # Save previous function (if same or lower indent level)
            if current and indent <= (current._indent if hasattr(current, "_indent") else 0):
                current.end_line = i
                current.lines = lines[current.start_line - 1:i]
                current.analyze()
                functions.append(current)

            name = m.group(2)
            params_str = m.group(3)
            # Count params, excluding self/cls
            params = [p.strip().split(":")[0].split("=")[0].strip()
                      for p in params_str.split(",") if p.strip()]
            params = [p for p in params if p not in ("self", "cls", "*", "/")]
            param_count = len(params)

            current = FunctionInfo(name, fpath, i + 1, "py")
            current.param_count = param_count
            current._indent = indent

    if current:
        current.end_line = len(lines)
        current.lines = lines[current.start_line - 1:]
        current.analyze()
        functions.append(current)

    return functions


def main():
    large_files = []
    all_functions = []

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fname in filenames:
            ext = os.path.splitext(fname)[1]
            if ext not in SOURCE_EXTS:
                continue
            fpath = os.path.join(dirpath, fname)
            try:
                with open(fpath, "r", errors="ignore") as f:
                    lines = f.readlines()
            except Exception:
                continue

            # Large file check
            if len(lines) > FILE_LINE_LIMIT:
                large_files.append((fpath, len(lines)))

            # Extract and analyze functions
            language = detect_language(fname)
            if language == "py":
                functions = extract_functions_py(lines, fpath)
            else:
                functions = extract_functions_js(lines, fpath, language)

            all_functions.extend(functions)

    # --- Report ---
    has_output = False

    if large_files:
        has_output = True
        print("=== Large files (>300 lines) ===")
        for fpath, count in sorted(large_files, key=lambda x: -x[1]):
            print(f"  {count:>5} lines  {fpath}")

    # Long functions
    long_funcs = [f for f in all_functions if f.line_count > FUNC_LINE_LIMIT]
    if long_funcs:
        has_output = True
        print("\n=== Long functions (>50 lines) ===")
        for fn in sorted(long_funcs, key=lambda x: -x.line_count)[:20]:
            print(f"  {fn.line_count:>4} lines  {fn.name}() at {fn.fpath}:{fn.start_line}")

    # High cyclomatic complexity
    complex_funcs = [f for f in all_functions if f.cyclomatic > CYCLOMATIC_LIMIT]
    if complex_funcs:
        has_output = True
        print(f"\n=== High cyclomatic complexity (>{CYCLOMATIC_LIMIT}, NIST threshold) ===")
        for fn in sorted(complex_funcs, key=lambda x: -x.cyclomatic)[:20]:
            print(f"  CC={fn.cyclomatic:>3}  {fn.name}() at {fn.fpath}:{fn.start_line}  ({fn.line_count} lines)")

    # High cognitive complexity
    cognitive_funcs = [f for f in all_functions if f.cognitive > COGNITIVE_LIMIT]
    if cognitive_funcs:
        has_output = True
        print(f"\n=== High cognitive complexity (>{COGNITIVE_LIMIT}, SonarQube threshold) ===")
        for fn in sorted(cognitive_funcs, key=lambda x: -x.cognitive)[:20]:
            print(f"  CogC={fn.cognitive:>3}  {fn.name}() at {fn.fpath}:{fn.start_line}  (nesting depth: {fn.max_nesting})")

    # Too many parameters
    param_funcs = [f for f in all_functions if f.param_count > PARAM_LIMIT]
    if param_funcs:
        has_output = True
        print(f"\n=== Functions with many parameters (>{PARAM_LIMIT}) ===")
        for fn in sorted(param_funcs, key=lambda x: -x.param_count)[:15]:
            print(f"  {fn.param_count:>2} params  {fn.name}() at {fn.fpath}:{fn.start_line}")

    # Deep nesting
    nested_funcs = [f for f in all_functions if f.max_nesting > NESTING_LIMIT]
    if nested_funcs:
        has_output = True
        print(f"\n=== Deep nesting (>{NESTING_LIMIT} levels) ===")
        for fn in sorted(nested_funcs, key=lambda x: -x.max_nesting)[:15]:
            print(f"  depth={fn.max_nesting}  {fn.name}() at {fn.fpath}:{fn.start_line}")

    if not has_output:
        print("No complexity hotspots found. Nice.")
    else:
        # Summary
        total = len(all_functions)
        flagged = len(set(
            f.name + f.fpath for f in all_functions
            if f.line_count > FUNC_LINE_LIMIT or f.cyclomatic > CYCLOMATIC_LIMIT
            or f.cognitive > COGNITIVE_LIMIT or f.param_count > PARAM_LIMIT
            or f.max_nesting > NESTING_LIMIT
        ))
        print(f"\n{flagged} of {total} functions flagged across all checks.")


if __name__ == "__main__":
    main()
