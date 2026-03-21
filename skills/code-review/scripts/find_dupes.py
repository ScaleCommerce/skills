#!/usr/bin/env python3
"""Find duplicate code blocks across source files."""
import hashlib, os, sys
from collections import defaultdict


def find_dupes(root, extensions, min_lines=5):
    """Find duplicate code blocks across files."""
    blocks = defaultdict(list)

    for dirpath, _, filenames in os.walk(root):
        # Skip common non-source dirs
        skip = ['node_modules', '.git', 'vendor', 'dist', '.nuxt', '.next',
                '__pycache__', '.venv', 'build', 'coverage', '.output']
        if any(s in dirpath for s in skip):
            continue
        for fname in filenames:
            if not any(fname.endswith(ext) for ext in extensions):
                continue
            fpath = os.path.join(dirpath, fname)
            try:
                with open(fpath, 'r', errors='ignore') as f:
                    lines = f.readlines()
            except:
                continue
            # Sliding window of min_lines
            for i in range(len(lines) - min_lines + 1):
                block = lines[i:i + min_lines]
                # Normalize: strip whitespace for comparison
                normalized = ''.join(l.strip() for l in block if l.strip())
                if len(normalized) < 40:  # Skip trivial blocks
                    continue
                h = hashlib.md5(normalized.encode()).hexdigest()
                blocks[h].append((fpath, i + 1, ''.join(block).strip()[:200]))

    dupes = {k: v for k, v in blocks.items() if len(v) > 1}
    if not dupes:
        print("No significant duplicate blocks found.")
        return

    # Sort by number of occurrences
    for h, locations in sorted(dupes.items(), key=lambda x: -len(x[1]))[:15]:
        print(f"\n--- Duplicate block ({len(locations)} occurrences) ---")
        for fpath, line, preview in locations:
            print(f"  {fpath}:{line}")
        print(f"  Preview: {locations[0][2][:150]}...")


if __name__ == '__main__':
    root = sys.argv[1] if len(sys.argv) > 1 else '.'

    # Detect extensions from project
    exts = []
    for dirpath, _, files in os.walk(root):
        if any(s in dirpath for s in ['node_modules', '.git', 'vendor']):
            continue
        for f in files:
            if f.endswith(('.ts', '.tsx', '.js', '.jsx', '.vue', '.svelte')):
                exts = ['.ts', '.tsx', '.js', '.jsx', '.vue', '.svelte']; break
            elif f.endswith(('.py',)):
                exts = ['.py']; break
            elif f.endswith(('.go',)):
                exts = ['.go']; break
            elif f.endswith(('.rs',)):
                exts = ['.rs']; break
            elif f.endswith(('.php',)):
                exts = ['.php']; break
        if exts:
            break

    if not exts:
        exts = ['.ts', '.js', '.py', '.go', '.rs', '.php', '.rb', '.java']

    find_dupes(root, exts)
