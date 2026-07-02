#!/usr/bin/env python3
"""Find duplicate code blocks across source files.

Hashes whitespace-normalized sliding windows, then merges runs of consecutive
matching windows into maximal spans so one 50-line copy-paste is reported as a
single block instead of ~46 overlapping ones.
"""
import hashlib
import os
import re
import sys
from collections import defaultdict

from common import iter_source_files, read_text

SOURCE_EXTS = ['.ts', '.tsx', '.js', '.jsx', '.vue', '.svelte', '.py', '.go',
               '.rs', '.php', '.rb', '.java', '.kt', '.cs']

MIN_LINES = 5
MAX_GROUPS = 15
MAX_LOCATIONS_PER_GROUP = 10

# Lines that duplicate legitimately: imports, license headers, comments.
BOILERPLATE = re.compile(
    r'^(import\s|from\s.+\simport\s|export\s+[{*]|const\s.+=\s*require\(|'
    r'use\s|#include|package\s|//|#|\*|/\*)'
)


def collect_windows(root):
    blocks = defaultdict(list)
    for fpath in iter_source_files(root, SOURCE_EXTS):
        content = read_text(fpath)
        if content is None:
            continue
        lines = content.splitlines()
        for i in range(len(lines) - MIN_LINES + 1):
            window = [l.strip() for l in lines[i:i + MIN_LINES]]
            meaningful = [l for l in window if l]
            # Blank lines are dropped in normalization, so windows that are
            # mostly blank hash equal to their own neighbours — require the
            # window to be nearly full to avoid self-matches.
            if len(meaningful) < MIN_LINES - 1:
                continue
            normalized = ''.join(meaningful)
            if len(normalized) < 40:
                continue
            # Skip windows that are mostly imports/comments/license noise —
            # those duplicate by design and drown real copy-paste.
            if sum(1 for l in meaningful if BOILERPLATE.match(l)) > len(meaningful) // 2:
                continue
            h = hashlib.md5(normalized.encode()).hexdigest()
            blocks[h].append((fpath, i + 1, '\n'.join(window)[:200]))
    return blocks


def merge_spans(blocks):
    """Collapse chains of overlapping duplicate windows into maximal spans.

    Window at lines N..N+4 and window at N+1..N+5 belong to the same physical
    duplicate; we only report the head of each chain, extended to full length.
    """
    dupes = {}
    for h, v in blocks.items():
        # Drop locations overlapping an earlier one in the same file — those
        # are the same physical lines matching themselves, not a duplicate.
        kept = []
        for f, l, preview in sorted(v):
            if any(f == kf and abs(l - kl) < MIN_LINES for kf, kl, _ in kept):
                continue
            kept.append((f, l, preview))
        if len(kept) > 1:
            dupes[h] = kept
    by_locations = {tuple(sorted((f, l) for f, l, _ in v)): h
                    for h, v in dupes.items()}

    spans = []
    for locs, h in by_locations.items():
        predecessor = tuple(sorted((f, l - 1) for f, l in locs))
        if predecessor in by_locations:
            continue  # covered by an earlier window in the same chain
        length = MIN_LINES
        cursor = locs
        while True:
            successor = tuple(sorted((f, l + 1) for f, l in cursor))
            if successor not in by_locations:
                break
            length += 1
            cursor = successor
        spans.append((locs, length, dupes[h][0][2]))
    return spans


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else '.'
    spans = merge_spans(collect_windows(root))

    if not spans:
        print("No significant duplicate blocks found.")
        return

    spans.sort(key=lambda s: -(len(s[0]) * s[1]))  # occurrences x length
    shown = spans[:MAX_GROUPS]
    for locs, length, preview in shown:
        print(f"\n--- Duplicate block: {length} lines, {len(locs)} occurrences ---")
        for fpath, line in locs[:MAX_LOCATIONS_PER_GROUP]:
            print(f"  {fpath}:{line}")
        if len(locs) > MAX_LOCATIONS_PER_GROUP:
            print(f"  ... and {len(locs) - MAX_LOCATIONS_PER_GROUP} more locations")
        print(f"  Preview: {preview[:150]}")
    if len(spans) > MAX_GROUPS:
        print(f"\n({len(spans) - MAX_GROUPS} smaller duplicate blocks not shown)")


if __name__ == '__main__':
    main()
