#!/usr/bin/env python3
"""WCAG contrast ratio between two colours. Zero dependencies.

Contrast is computed, never eyeballed: "looks fine" shipped a 2.50:1 tag label
and a 1.71:1 status dot in the codebase this skill was distilled from. The
thresholds that matter:

  4.5:1  normal text (AA) — including small bold labels; the large-text
         exemption starts at 18.7px bold / 24px regular
  3.0:1  large text, and graphical objects / UI components (borders you must
         see, status dots, icons that carry meaning)

Accepts hex (#rgb, #rrggbb) and oklch(L C H) / oklch(L% C H) — the latter so
token declarations can be checked straight out of a stylesheet.

Usage:
  python3 contrast.py '#334155' '#ffffff'
  python3 contrast.py 'oklch(21% 0.006 285.885)' '#a1a1aa'
"""

import math
import re
import sys


def oklch_to_rgb(L: float, C: float, H: float):
    a, b = C * math.cos(math.radians(H)), C * math.sin(math.radians(H))
    l_ = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m_ = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s_ = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
    lin = (
        4.0767416621 * l_ - 3.3077115913 * m_ + 0.2309699292 * s_,
        -1.2684380046 * l_ + 2.6097574011 * m_ - 0.3413193965 * s_,
        -0.0041960863 * l_ - 0.7034186147 * m_ + 1.7076147010 * s_,
    )
    gamma = lambda v: 12.92 * v if v <= 0.0031308 else 1.055 * v ** (1 / 2.4) - 0.055
    return tuple(min(1.0, max(0.0, gamma(v))) for v in lin)


def parse(colour: str):
    colour = colour.strip()
    m = re.match(r'oklch\(\s*([\d.]+)(%?)\s+([\d.]+)\s+([\d.]+)', colour)
    if m:
        L = float(m.group(1)) / (100 if m.group(2) else 1)
        return oklch_to_rgb(L, float(m.group(3)), float(m.group(4)))
    hexval = colour.lstrip('#')
    if len(hexval) == 3:
        hexval = ''.join(c * 2 for c in hexval)
    if re.fullmatch(r'[0-9a-fA-F]{6}', hexval):
        return tuple(int(hexval[i:i + 2], 16) / 255 for i in (0, 2, 4))
    raise ValueError(f'cannot parse colour: {colour!r}')


def luminance(rgb) -> float:
    lin = lambda v: v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(v) for v in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def main() -> None:
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    a, b = parse(sys.argv[1]), parse(sys.argv[2])
    la, lb = luminance(a), luminance(b)
    ratio = (max(la, lb) + 0.05) / (min(la, lb) + 0.05)

    verdict = lambda ok: 'PASS' if ok else 'FAIL'
    print(f'{sys.argv[1]}  vs  {sys.argv[2]}')
    print(f'contrast ratio: {ratio:.2f}:1')
    print(f'  normal text (AA, 4.5:1):        {verdict(ratio >= 4.5)}')
    print(f'  large text / graphics (3.0:1):  {verdict(ratio >= 3.0)}')
    print(f'  normal text (AAA, 7.0:1):       {verdict(ratio >= 7.0)}')


if __name__ == '__main__':
    main()
