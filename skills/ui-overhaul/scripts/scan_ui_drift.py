#!/usr/bin/env python3
"""Scan a codebase for UI drift: the measurements a UI consolidation pass runs on.

Zero dependencies. Scans markup (.vue/.jsx/.tsx/.svelte/.astro/.html) and .css
for the five kinds of drift that accumulate in a Tailwind codebase:

  1. Raw palette utilities (bg-zinc-500, text-red-400) — colours that dodge the
     semantic token layer, so dark mode is maintained by hand.
  2. Hand-maintained dark twins (bg-white dark:bg-zinc-900 on one line) — the
     strongest signal, each one is a value someone has to keep in sync forever.
  3. Arbitrary values (w-[280px], tracking-[0.08em]) grouped by spelling —
     a value repeated across 2+ files is shared vocabulary wanting a token.
  4. Inline font sizes (text-[13px], font-size: 13px) — the size ladder that
     grew instead of being decided.
  5. Raw shadow steps and hex colours in CSS — per-mode values with no token.

Counts are signal, not verdicts: read the flagged sites before acting on them.

Usage:  python3 scan_ui_drift.py [path] [--json]
"""

import json
import os
import re
import sys
from collections import defaultdict

MARKUP_EXT = {'.vue', '.jsx', '.tsx', '.svelte', '.astro', '.html', '.htm'}
CSS_EXT = {'.css', '.scss', '.less'}
SKIP_DIRS = {'node_modules', '.git', 'dist', 'build', 'vendor', '.nuxt', '.next',
             '.output', '.svelte-kit', 'coverage', '__pycache__', '.venv', 'venv'}

TAILWIND_FAMILIES = (
    'slate', 'gray', 'zinc', 'neutral', 'stone',
    'red', 'orange', 'amber', 'yellow', 'lime', 'green', 'emerald', 'teal',
    'cyan', 'sky', 'blue', 'indigo', 'violet', 'purple', 'fuchsia', 'pink', 'rose'
)

# A raw palette reference: any variant chain, any paint prefix, family-step.
RAW_PALETTE = re.compile(
    r'[\w:./\[\]-]*\b(?:' + '|'.join(TAILWIND_FAMILIES) + r')-(?:50|\d{2,3})\b[\w/.%\[\]-]*'
)
ARBITRARY = re.compile(r'\b([a-z][\w-]*)-\[([^\]]+)\]')
INLINE_TEXT_PX = re.compile(r'\btext-\[(\d+(?:\.\d+)?)px\]')
FONT_SIZE_PX = re.compile(r'font-size:\s*(\d+(?:\.\d+)?)px')
TRACKING = re.compile(r'\btracking-\[([^\]]+)\]|letter-spacing:\s*([^;}\n]+)')
RAW_SHADOW = re.compile(r'(?:[\w-]+:)*\bshadow-(2xs|xs|sm|md|lg|xl|2xl|inner)\b')
HEX_IN_CSS = re.compile(r'#[0-9a-fA-F]{3,8}\b')
# Also flag arbitrary shadows and coloured shadows (a hand-maintained dark value).
SHADOW_COLOURED = re.compile(
    r'(?:[\w-]+:)*\bshadow-(?:' + '|'.join(TAILWIND_FAMILIES) + r')-\d{2,3}(?:/\d+)?\b'
)


def blank_comments(text: str, is_markup: bool) -> str:
    """Blank comments but keep line numbers, so prose about a bad class
    (`<!-- never use bg-zinc-500 -->`) does not read as an instance of it."""
    keep_lines = lambda m: re.sub(r'[^\n]', '', m.group(0))
    text = re.sub(r'/\*[\s\S]*?\*/', keep_lines, text)
    text = re.sub(r'^\s*//.*$', '', text, flags=re.M)
    if is_markup:
        text = re.sub(r'<!--[\s\S]*?-->', keep_lines, text)
    return text


def walk(root: str):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith('.')]
        for name in filenames:
            ext = os.path.splitext(name)[1]
            if ext in MARKUP_EXT or ext in CSS_EXT:
                yield os.path.join(dirpath, name), ext in MARKUP_EXT


def main() -> None:
    args = [a for a in sys.argv[1:] if a != '--json']
    as_json = '--json' in sys.argv
    root = os.path.abspath(args[0] if args else '.')

    raw_palette = []            # (file, line_no, utility)
    dark_twins = []             # (file, line_no, line_excerpt)
    arbitrary = defaultdict(lambda: defaultdict(int))   # utility -> file -> count
    font_sizes = defaultdict(list)                      # px -> [(file, line_no)]
    trackings = defaultdict(lambda: defaultdict(int))   # value -> file -> count
    raw_shadows = []            # (file, line_no, utility)
    css_hexes = defaultdict(lambda: defaultdict(int))   # hex -> file -> count
    files_scanned = 0

    for path, is_markup in walk(root):
        rel = os.path.relpath(path, root)
        try:
            text = blank_comments(open(path, encoding='utf-8', errors='replace').read(), is_markup)
        except OSError:
            continue
        files_scanned += 1

        for i, line in enumerate(text.split('\n'), 1):
            for m in RAW_PALETTE.finditer(line):
                raw_palette.append((rel, i, m.group(0)))
            palette_hits = RAW_PALETTE.findall(line)
            if any(h.startswith('dark:') or ':dark:' in h for h in palette_hits) \
                    and any('dark:' not in h for h in palette_hits):
                dark_twins.append((rel, i, line.strip()[:100]))
            for m in ARBITRARY.finditer(line):
                arbitrary[f'{m.group(1)}-[{m.group(2)}]'][rel] += 1
            for m in INLINE_TEXT_PX.finditer(line):
                font_sizes[m.group(1)].append((rel, i))
            for m in FONT_SIZE_PX.finditer(line):
                font_sizes[m.group(1)].append((rel, i))
            for m in TRACKING.finditer(line):
                value = (m.group(1) or m.group(2) or '').strip()
                if value and not value.startswith('var('):
                    trackings[value][rel] += 1
            for m in RAW_SHADOW.finditer(line):
                raw_shadows.append((rel, i, m.group(0)))
            for m in SHADOW_COLOURED.finditer(line):
                raw_shadows.append((rel, i, m.group(0)))
            if not is_markup or 'style=' in line:
                for m in HEX_IN_CSS.finditer(line):
                    css_hexes[m.group(0).lower()][rel] += 1

    shared_arbitrary = {u: files for u, files in arbitrary.items() if len(files) > 1}

    if as_json:
        print(json.dumps({
            'files_scanned': files_scanned,
            'raw_palette_utilities': [
                {'file': f, 'line': l, 'utility': u} for f, l, u in raw_palette],
            'dark_twin_lines': [
                {'file': f, 'line': l, 'excerpt': e} for f, l, e in dark_twins],
            'shared_arbitrary_values': {
                u: dict(files) for u, files in shared_arbitrary.items()},
            'one_off_arbitrary_values': sorted(
                u for u, files in arbitrary.items() if len(files) == 1),
            'inline_font_sizes_px': {
                px: [{'file': f, 'line': l} for f, l in sites]
                for px, sites in font_sizes.items()},
            'tracking_values': {v: dict(files) for v, files in trackings.items()},
            'raw_shadows': [
                {'file': f, 'line': l, 'utility': u} for f, l, u in raw_shadows],
            'hex_colours_in_css': {h: dict(files) for h, files in css_hexes.items()},
        }, indent=2))
        return

    print(f'UI drift scan: {root}  ({files_scanned} files)\n')

    print('=' * 72)
    print(f'RAW PALETTE UTILITIES: {len(raw_palette)} across '
          f'{len({f for f, _, _ in raw_palette})} files')
    print('Colours that bypass the semantic token layer. Dark mode for each is')
    print('maintained by hand or simply missing.')
    by_file = defaultdict(int)
    for f, _, _ in raw_palette:
        by_file[f] += 1
    for f, n in sorted(by_file.items(), key=lambda x: -x[1])[:15]:
        print(f'  {n:4}  {f}')
    if len(by_file) > 15:
        print(f'  … and {len(by_file) - 15} more files (use --json for all)')

    print()
    print(f'HAND-MAINTAINED DARK TWINS: {len(dark_twins)} lines pair a light value')
    print('with its dark: rewrite — each is two numbers someone keeps in sync.')
    for f, l, e in dark_twins[:10]:
        print(f'  {f}:{l}  {e}')
    if len(dark_twins) > 10:
        print(f'  … and {len(dark_twins) - 10} more')

    print()
    print(f'SHARED ARBITRARY VALUES: {len(shared_arbitrary)} spelled in 2+ files.')
    print('A value two files agree on is shared vocabulary wanting a token; a')
    print('one-off is a measurement of one component and is fine as a literal.')
    for u, files in sorted(shared_arbitrary.items(), key=lambda x: -len(x[1])):
        print(f'  {u}  — {len(files)} files: {", ".join(sorted(files)[:4])}'
              f'{" …" if len(files) > 4 else ""}')
    one_offs = sum(1 for files in arbitrary.values() if len(files) == 1)
    print(f'  ({one_offs} one-off arbitrary values not listed — those may stay literals)')

    print()
    sizes = sorted(font_sizes, key=float)
    total_size_sites = sum(len(s) for s in font_sizes.values())
    print(f'INLINE FONT SIZES: {total_size_sites} sites across {len(sizes)} distinct '
          f'sizes: {", ".join(s + "px" for s in sizes)}')
    print('This is the type ladder that grew instead of being decided. Collapse it')
    print('to a handful of named steps, each with a job.')

    print()
    print(f'TRACKING / LETTER-SPACING: {len(trackings)} distinct values')
    for v, files in sorted(trackings.items(), key=lambda x: -sum(x[1].values())):
        n = sum(files.values())
        print(f'  {v!r:20}  {n} sites / {len(files)} files')

    print()
    print(f'RAW SHADOWS: {len(raw_shadows)} Tailwind steps or coloured shadows —')
    print('each has a dark-mode value maintained by hand (or none). An elevation')
    print('ramp defined once per colour mode replaces all of them.')
    for f, l, u in raw_shadows[:10]:
        print(f'  {f}:{l}  {u}')

    print()
    print(f'HEX COLOURS IN CSS / style=: {len(css_hexes)} distinct')
    for h, files in sorted(css_hexes.items(), key=lambda x: -sum(x[1].values()))[:15]:
        print(f'  {h:9}  {sum(files.values())} sites / {len(files)} files')

    print()
    print('=' * 72)
    print('These numbers are the audit baseline: quote them in the report, and')
    print('rerun after each phase — the deltas are the progress record.')


if __name__ == '__main__':
    main()
