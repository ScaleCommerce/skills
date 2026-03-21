#!/usr/bin/env python3
"""Detect naming convention inconsistencies, leftover debug statements, and code smells."""
import os, re, sys
from collections import Counter

root = sys.argv[1] if len(sys.argv) > 1 else '.'
issues = []

for dirpath, _, filenames in os.walk(root):
    skip = ['node_modules', '.git', 'vendor', 'dist', '__pycache__', '.venv', '.nuxt', '.next']
    if any(s in dirpath for s in skip):
        continue
    for fname in filenames:
        if not any(fname.endswith(e) for e in ['.ts', '.tsx', '.js', '.jsx', '.vue', '.py', '.go', '.php']):
            continue
        fpath = os.path.join(dirpath, fname)
        try:
            with open(fpath, 'r', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
        except:
            continue

        # Check: mixed import styles (JS/TS)
        if fname.endswith(('.ts', '.tsx', '.js', '.jsx')):
            has_require = bool(re.search(r'\brequire\s*\(', content))
            has_import = bool(re.search(r'^import\s', content, re.MULTILINE))
            if has_require and has_import:
                issues.append(f"Mixed require/import: {fpath}")

        # Check: inconsistent string quotes (JS/TS)
        if fname.endswith(('.ts', '.tsx', '.js', '.jsx')):
            singles = len(re.findall(r"(?<!=)'[^']*'", content))
            doubles = len(re.findall(r'(?<!=)"[^"]*"', content))
            if singles > 5 and doubles > 5:
                ratio = min(singles, doubles) / max(singles, doubles)
                if ratio > 0.3:  # More than 30% mix
                    issues.append(f"Mixed quote styles ({singles} single, {doubles} double): {fpath}")

        # Check: console.log / print statements left in
        if fname.endswith(('.ts', '.tsx', '.js', '.jsx', '.vue')):
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped.startswith('console.log(') and not stripped.startswith('//'):
                    issues.append(f"console.log left in: {fpath}:{i+1}")
        if fname.endswith('.py'):
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped.startswith('print(') and not stripped.startswith('#'):
                    issues.append(f"print() left in: {fpath}:{i+1}")

        # Check: TODO/FIXME/HACK/XXX comments
        for i, line in enumerate(lines):
            if re.search(r'\b(TODO|FIXME|HACK|XXX)\b', line):
                issues.append(f"{re.search(r'(TODO|FIXME|HACK|XXX)', line).group()}: {fpath}:{i+1} — {line.strip()[:80]}")

        # Check: empty catch/except blocks
        if fname.endswith(('.ts', '.tsx', '.js', '.jsx')):
            for i, line in enumerate(lines):
                if re.search(r'catch\s*\([^)]*\)\s*\{\s*\}', content):
                    issues.append(f"Empty catch block: {fpath}")
                    break
        if fname.endswith('.py'):
            for i, line in enumerate(lines):
                if 'except' in line and i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if next_line == 'pass' or next_line == '...':
                        issues.append(f"Empty except/pass: {fpath}:{i+1}")

for issue in issues[:50]:
    print(issue)

if not issues:
    print("No major inconsistencies detected.")
else:
    print(f"\n({len(issues)} issues total)")
