#!/usr/bin/env python3
"""Detect leftover debug statements, empty error handlers, and style inconsistencies.

Findings are sorted by severity before the output cap is applied, so a codebase
full of TODOs can't drown an empty catch block. TODO/FIXME comments are reported
as a per-file summary — their exact locations are cheap to grep once you care.
"""
import os
import re
import sys
from collections import Counter

from common import iter_source_files, read_text

SOURCE_EXTS = ['.ts', '.tsx', '.js', '.jsx', '.vue', '.py', '.go', '.php']
JS_EXTS = ('.ts', '.tsx', '.js', '.jsx')

# Directories where print()/console.log are legitimate output, not leftovers.
CLI_HINT = re.compile(r'(^|/)(scripts?|bin|cli|tools?|examples?|tests?|__tests__)(/|$)')

MAX_ISSUES = 50


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else '.'
    high, medium, low = [], [], []
    todo_counts = Counter()

    for fpath in iter_source_files(root, SOURCE_EXTS):
        content = read_text(fpath)
        if content is None:
            continue
        lines = content.split('\n')
        is_js = fpath.endswith(JS_EXTS) or fpath.endswith('.vue')

        # Empty catch blocks (JS/TS), including optional binding `catch {}`.
        # Regex runs on the whole file so multi-line `catch (e) {\n}` is caught;
        # line number is recovered from the match offset.
        if is_js:
            for m in re.finditer(r'catch\s*(\([^)]*\))?\s*\{\s*\}', content):
                line_no = content[:m.start()].count('\n') + 1
                high.append(f"Empty catch block (error swallowed): {fpath}:{line_no}")

        # Bare except: pass (Python)
        if fpath.endswith('.py'):
            for i, line in enumerate(lines):
                if re.match(r'\s*except\b.*:', line) and i + 1 < len(lines):
                    body = lines[i + 1].split('#')[0].strip()
                    if body in ('pass', '...'):
                        high.append(f"Empty except (error swallowed): {fpath}:{i+1}")

        # Leftover debug statements — skipped in CLI/script/test paths where
        # printing is the point.
        if not CLI_HINT.search(fpath.replace(os.sep, '/')):
            if is_js:
                for i, line in enumerate(lines):
                    stripped = line.strip()
                    if re.match(r'console\.(log|debug)\(', stripped):
                        medium.append(f"console.log left in: {fpath}:{i+1}")
            if fpath.endswith('.py'):
                # print() in a file with a main entry point is CLI output, not debug.
                if '__main__' not in content:
                    for i, line in enumerate(lines):
                        if re.match(r'print\(', line.strip()):
                            medium.append(f"print() left in: {fpath}:{i+1}")

        # Mixed module systems (JS/TS): only count real CJS require assignments,
        # not the word "require" in strings or comments.
        if fpath.endswith(JS_EXTS):
            has_require = bool(re.search(
                r'^\s*(?:const|let|var)\s+.+=\s*require\s*\(', content, re.MULTILINE))
            has_import = bool(re.search(r'^import\s', content, re.MULTILINE))
            if has_require and has_import:
                low.append(f"Mixed require/import: {fpath}")

        # TODO/FIXME/HACK — summarized, not itemized.
        n = len(re.findall(r'(?://|#|<!--|\*)\s*(?:TODO|FIXME|HACK|XXX)\b', content))
        if n:
            todo_counts[fpath] = n

    issues = high + medium + low
    for issue in issues[:MAX_ISSUES]:
        print(issue)
    if len(issues) > MAX_ISSUES:
        print(f"... ({len(issues) - MAX_ISSUES} more, truncated lowest-severity-first)")

    if todo_counts:
        total = sum(todo_counts.values())
        print(f"\nTODO/FIXME/HACK comments: {total} across {len(todo_counts)} files")
        for fpath, n in todo_counts.most_common(10):
            print(f"  {n:3d}  {fpath}")

    if not issues and not todo_counts:
        print("No major inconsistencies detected.")


if __name__ == '__main__':
    main()
