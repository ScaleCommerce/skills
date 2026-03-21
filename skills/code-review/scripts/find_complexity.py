#!/usr/bin/env python3
"""Find oversized files and long functions."""
import os, re, sys

root = sys.argv[1] if len(sys.argv) > 1 else '.'
large_files = []
long_functions = []

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
                lines = f.readlines()
        except:
            continue

        line_count = len(lines)
        if line_count > 300:
            large_files.append((fpath, line_count))

        # Detect long functions/methods
        func_start = None
        func_name = None
        depth = 0
        for i, line in enumerate(lines):
            # JS/TS function detection
            m = re.match(r'\s*(?:export\s+)?(?:async\s+)?(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=.*(?:=>|\bfunction\b))', line)
            if not m:
                m = re.match(r'\s*(?:async\s+)?(\w+)\s*\([^)]*\)\s*(?::\s*\w+)?\s*\{', line)
            if not m:
                # Python function detection
                m = re.match(r'\s*(?:async\s+)?def\s+(\w+)', line)

            if m:
                if func_start is not None and (i - func_start) > 50:
                    long_functions.append((fpath, func_name or "anonymous", func_start + 1, i - func_start))
                func_start = i
                func_name = m.group(1) or (m.group(2) if m.lastindex >= 2 else "anonymous")

        # Check last function
        if func_start is not None and (len(lines) - func_start) > 50:
            long_functions.append((fpath, func_name or "anonymous", func_start + 1, len(lines) - func_start))

if large_files:
    print("=== Large files (>300 lines) ===")
    for fpath, count in sorted(large_files, key=lambda x: -x[1]):
        print(f"  {count:>5} lines  {fpath}")

if long_functions:
    print("\n=== Long functions (>50 lines) ===")
    for fpath, name, start, length in sorted(long_functions, key=lambda x: -x[3])[:20]:
        print(f"  {length:>4} lines  {name}() at {fpath}:{start}")

if not large_files and not long_functions:
    print("No oversized files or functions found. Nice.")
