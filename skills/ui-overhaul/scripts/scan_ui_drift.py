#!/usr/bin/env python3
"""Scan a codebase for UI drift: the measurements a UI consolidation pass runs on.

Zero dependencies. Scans markup (.vue/.jsx/.tsx/.svelte/.astro/.html) and .css
for the kinds of drift that accumulate in a Tailwind codebase:

  1. Raw palette utilities (bg-zinc-500, text-red-400) — colours that dodge the
     semantic token layer, so dark mode is maintained by hand.
  2. Hand-maintained dark twins (bg-white dark:bg-zinc-900 on one line) — the
     strongest signal, each one is a value someone has to keep in sync forever.
  3. Arbitrary values (w-[280px], tracking-[0.08em]) grouped by spelling —
     a value repeated across 2+ files is shared vocabulary wanting a token.
  4. Inline font sizes (text-[13px], font-size: 13px) — the size ladder that
     grew instead of being decided.
  5. Raw shadow steps and hex colours in CSS — per-mode values with no token.
  6. Interactive state: how many spellings of hover/focus there are, how many
     sites opt out of the focus system, and transitions that name only colours
     while a state also moves a shadow or a transform (so that half snaps).
  7. Control geometry spelled inline — a native element wearing padding plus a
     text step or a radius, grouped by that signature. Two files sharing one is
     a component spelled twice, very often the UI library's own button.
  8. Controls styled for the mouse only (a hover, no focus) and controls with no
     state at all — the absence that check 6 structurally cannot see.

Counts are signal, not verdicts: read the flagged sites before acting on them.

Checks 1-5 all measure appearance *at rest*. Check 6 exists because a UI drifts
just as hard in its states, and none of the others can see it: a codebase can
scan clean while every input draws two focus rings, half the opt-outs written
against a global rule are dead code, and one kind of card has two hovers.

Checks 7-8 measure what the markup *is* rather than what it looks like, which
is the axis the others structurally miss. A codebase can score zero on 1-6 —
every colour a token, every size on the ladder, no opt-outs — while shipping a
dozen hand-rolled copies of its own button component, because each individual
utility in them is already correct. Check 8 is the same blind spot from the
other side: check 6 counts who fought the focus rule and reports 0 for an app
where nothing reached it in the first place.

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

# ── Interactive state ──────────────────────────────────────────────────────────
STATE_VARIANTS = r'(?:group-|peer-)?(?:hover|focus|focus-visible|focus-within|active)'
# A state that paints: grouped by the property it moves, so the report can say
# "N spellings of hover-border" the way it says "N distinct font sizes".
STATE_PAINT = re.compile(
    r'\b(' + STATE_VARIANTS + r'):(?:before:|after:)?'
    r'(border|ring|outline|shadow|bg|text|opacity|translate|scale)([\w./\[\]-]*)'
)
# Opting out of the focus system. Counted separately because the number is the
# whole finding: it measures how many places fought the global rule — and a
# `!`-flagged one means the global rule was strong enough to need overriding.
#
# `outline-*` counts bare, because an outline is only ever visible on focus.
# `ring-0` does not: at rest it is how a component says "no ring", and only a
# state prefix or a `!` makes it a focus opt-out. Counting it bare reports every
# ghost-variant button as a suppressor.
FOCUS_SUPPRESSOR = re.compile(
    r'\b(?:(?:' + STATE_VARIANTS + r':)(outline-none!?|ring-0!?|outline-hidden)'
    r'|(outline-none!?|outline-hidden)|(ring-0!))\b'
)
# `transition-colors` moves colour/background/border/fill/stroke and nothing
# else. Pair it with a state that also moves a shadow or a transform and that
# half of the transition snaps on instead of easing.
TRANSITION_COLORS = re.compile(r'\btransition-colors\b')
NON_COLOUR_STATE = re.compile(
    r'\b' + STATE_VARIANTS + r':(shadow-|translate-|scale-|rotate-|opacity-)'
)

# ── Control geometry ───────────────────────────────────────────────────────────
# The second-file test applied to *components* rather than to single values.
#
# A native element carrying padding plus a text step or a radius is a control
# wearing a control's geometry inline. One is a measurement of one component and
# is fine. The same geometry in a second file is a component someone has spelled
# twice — and if the project ships a UI library, it is very often that library's
# button re-typed by hand, which is invisible to every check above because each
# individual utility is already a legitimate token.
#
# Deliberately framework-agnostic: no list of library prefixes to maintain, and
# it works the same on a plain-CSS-plus-Tailwind app with no library at all.
# Which component a cluster *should* become is a question for the theme config
# (Phase 0 step 2), not for this regex.
NATIVE_CONTROL = re.compile(r'<(button|a|input|select|textarea)\b([^>]*?)>', re.S)
CLASS_ATTR = re.compile(r'class(?:Name)?="([^"]*)"')
GEOM_PAD = re.compile(r'^p[xy]?-')
GEOM_TEXT = re.compile(r'^text-(?:xs|sm|base|lg|xl|\dxl|2xs|\[)')
GEOM_RADIUS = re.compile(r'^rounded')
GEOM_WEIGHT = re.compile(r'^font-(?:medium|semibold|bold)')
# Any state paint the element declares for itself, split by which state it is.
OWN_HOVER = re.compile(r'\b(?:group-)?hover:(?:border|ring|outline|shadow|bg|text|opacity|translate|scale)')
OWN_FOCUS = re.compile(r'\bfocus(?:-visible|-within)?:(?:border|ring|outline|shadow|bg|text|opacity)')

# ── Primitive adoption ─────────────────────────────────────────────────────────
# The layer above control geometry, and invisible to it: a footer that assembles
# <Button variant="ghost">Cancel</Button> next to <Button>Save</Button> is made
# entirely of *correct* library components, so every check above passes while a
# dozen files reproduce the same composite by hand.
#
# What that looks like from the outside is a primitive nobody calls. A component
# with one or two consumers is not automatically wrong — it may be new, or
# genuinely niche — but when the codebase also has ten places rebuilding its
# shape inline, it was built and abandoned, and the migration was the half that
# never happened.
#
# Scoped to *shared primitives*, not to every component. A feature component with
# one consumer is the normal case — `KanbanBoard` is used by the board page and
# nowhere else, and that is healthy. Only a component that exists to be reused
# says anything by going unused, so the check reads the directory the project
# already put them in.
PRIMITIVE_DIRS = {'ui', 'primitives', 'common', 'shared', 'base', 'core', 'elements'}
COMPONENT_EXT = {'.vue', '.jsx', '.tsx', '.svelte'}


def component_tags(rel_path: str):
    """The tag names a component file might be referenced by.

    `Foo.tsx` → `Foo`. Nuxt also auto-imports by directory path, so
    `components/ui/SaveBar.vue` is `<UiSaveBar>` as well as `<SaveBar>` — both are
    tried and the higher count wins, which keeps the check honest on plain Vue,
    React and Svelte without knowing which it is looking at.
    """
    parts = rel_path.replace('\\', '/').split('/')
    stem = os.path.splitext(parts[-1])[0]
    names = {stem}
    dirs = [p for p in parts[:-1] if p not in ('src', 'app', 'components')]
    if dirs:
        names.add(''.join(d[:1].upper() + d[1:] for d in dirs) + stem)
    return names


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
    state_paint = defaultdict(lambda: defaultdict(int))  # property -> utility -> count
    focus_optouts = []          # (file, line_no, utility)
    snapped = []                # (file, line_no, [properties that snap])
    control_geom = defaultdict(lambda: defaultdict(list))  # signature -> file -> [lines]
    mouse_only = []             # (file, line_no, tag) — hover declared, focus not
    stateless = []              # (file, line_no, tag) — neither declared
    component_files = []        # rel paths that define a component
    tags_used = {}              # file -> {PascalCase tags it references}
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
            for m in STATE_PAINT.finditer(line):
                state_paint[m.group(2)][m.group(0)] += 1
            for m in FOCUS_SUPPRESSOR.finditer(line):
                focus_optouts.append((rel, i, m.group(1) or m.group(2) or m.group(3)))

        if is_markup:
            tags_used[rel] = set(re.findall(r'<([A-Z][A-Za-z0-9_]*)', text))
            segments = set(os.path.dirname(rel).replace('\\', '/').split('/'))
            if os.path.splitext(rel)[1] in COMPONENT_EXT and (segments & PRIMITIVE_DIRS):
                component_files.append(rel)

        # Native interactive elements, whole-tag rather than per line: an opening
        # tag wraps across lines as often as not, and both checks below need the
        # element's *complete* class attribute to be right about it.
        if is_markup:
            for m in NATIVE_CONTROL.finditer(text):
                tag, attrs = m.group(1), m.group(2)
                cm = CLASS_ATTR.search(attrs)
                if not cm:
                    continue
                toks = cm.group(1).split()
                line = text[:m.start()].count('\n') + 1

                pad = sorted(t for t in toks if GEOM_PAD.match(t))
                text_step = sorted(t for t in toks if GEOM_TEXT.match(t))
                radius = sorted(t for t in toks if GEOM_RADIUS.match(t))
                weight = sorted(t for t in toks if GEOM_WEIGHT.match(t))
                # Padding alone is a layout wrapper; padding plus a text step or a
                # radius is something shaped like a control.
                if pad and (text_step or radius):
                    sig = ' '.join(pad + radius + text_step + weight)
                    control_geom[sig][rel].append(line)

                attr = cm.group(1)
                if tag != 'a' and not OWN_FOCUS.search(attr):
                    (mouse_only if OWN_HOVER.search(attr) else stateless).append(
                        (rel, line, tag))

        # Per class attribute rather than per line: a class string often wraps,
        # and `transition-colors` and the state it fails to cover land on
        # different lines when it does.
        for m in re.finditer(r'class(?:Name)?=["\']([\s\S]*?)["\']', text):
            attr = m.group(1)
            if not TRANSITION_COLORS.search(attr):
                continue
            missed = sorted({g.rstrip('-') for g in NON_COLOUR_STATE.findall(attr)})
            if missed:
                snapped.append((rel, text[:m.start()].count('\n') + 1, missed))

    shared_arbitrary = {u: files for u, files in arbitrary.items() if len(files) > 1}
    shared_geom = {s: files for s, files in control_geom.items() if len(files) > 1}

    adoption = {}
    for comp in component_files:
        names = component_tags(comp)
        adoption[comp] = sum(
            1 for f, used in tags_used.items() if f != comp and (used & names))

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
            'state_treatments': {
                prop: dict(utils) for prop, utils in state_paint.items()},
            'focus_optouts': [
                {'file': f, 'line': l, 'utility': u} for f, l, u in focus_optouts],
            'snapped_transitions': [
                {'file': f, 'line': l, 'properties': p} for f, l, p in snapped],
            'shared_control_geometry': {
                s: dict(files) for s, files in shared_geom.items()},
            'one_off_control_geometry': sorted(
                s for s, files in control_geom.items() if len(files) == 1),
            'mouse_only_controls': [
                {'file': f, 'line': l, 'tag': t} for f, l, t in mouse_only],
            'stateless_controls': [
                {'file': f, 'line': l, 'tag': t} for f, l, t in stateless],
            'component_adoption': dict(sorted(adoption.items(), key=lambda x: x[1])),
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
    total_state = sum(sum(u.values()) for u in state_paint.values())
    print(f'INTERACTIVE STATE: {total_state} painted state sites, '
          f'{sum(len(u) for u in state_paint.values())} distinct spellings')
    print('The same ladder as font sizes, one property at a time. Two spellings')
    print('of one property on one kind of object is drift, not variety — ask what')
    print('object each belongs to before collapsing them.')
    for prop, utils in sorted(state_paint.items(), key=lambda x: -len(x[1])):
        if len(utils) < 2:
            continue
        top = sorted(utils.items(), key=lambda x: -x[1])[:4]
        print(f'  {prop:9} {len(utils):3} distinct  '
              + ', '.join(f'{u} ({n})' for u, n in top)
              + (' …' if len(utils) > 4 else ''))

    print()
    print(f'FOCUS OPT-OUTS: {len(focus_optouts)} sites across '
          f'{len({f for f, _, _ in focus_optouts})} files')
    print('Each fought a global focus rule. Check which layer that rule sits in')
    print('before trusting them: an unlayered or !important global beats a plain')
    print('utility whatever its specificity, so opt-outs written without the same')
    print('weight are dead code that still reads as deliberate.')
    for f, l, u in focus_optouts[:10]:
        print(f'  {f}:{l}  {u}')
    if len(focus_optouts) > 10:
        print(f'  … and {len(focus_optouts) - 10} more')

    print()
    print(f'SNAPPED TRANSITIONS: {len(snapped)} sites declare `transition-colors`')
    print('while a state also moves a shadow or a transform — that half jumps.')
    for f, l, props in snapped[:10]:
        print(f'  {f}:{l}  also moves {", ".join(props)}')
    if len(snapped) > 10:
        print(f'  … and {len(snapped) - 10} more')

    print()
    geom_sites = sum(len(l) for files in shared_geom.values() for l in files.values())
    print(f'CONTROL GEOMETRY SPELLED INLINE: {len(control_geom)} distinct signatures, '
          f'{len(shared_geom)} in 2+ files ({geom_sites} sites)')
    print('A native element wearing padding plus a text step or a radius is a')
    print('control. One is a measurement of one component; the same geometry in a')
    print('second file is a component spelled twice — and where the project ships a')
    print('UI library it is usually that library\'s button re-typed by hand, which')
    print('every check above misses because each utility is individually fine.')
    print('Read the sites: a popover menu row and a full-bleed list cell wear this')
    print('shape honestly and are not buttons. Then compare a real cluster against')
    print('the library theme you read in Phase 0 — that comparison names both the')
    print('component to migrate to and the ramp a guard should read rather than')
    print('restate.')
    for s, files in sorted(shared_geom.items(),
                           key=lambda x: -sum(len(l) for l in x[1].values())):
        n = sum(len(l) for l in files.values())
        print(f'  {n:3} sites / {len(files):2} files   {s}')
        for f, lines in sorted(files.items())[:4]:
            print(f'        {f}:{",".join(str(x) for x in lines)}')
        if len(files) > 4:
            print(f'        … and {len(files) - 4} more files')
    one_off_geom = sum(1 for files in control_geom.values() if len(files) == 1)
    print(f'  ({one_off_geom} one-off signatures not listed — those may stay inline)')

    print()
    print(f'CONTROLS STYLED FOR THE MOUSE ONLY: {len(mouse_only)} declare a hover '
          f'and no focus')
    print(f'CONTROLS WITH NO STATE AT ALL: {len(stateless)}')
    print('The counterpart to the opt-out count above, and the one it cannot see:')
    print('that number measures who *fought* a focus rule, this one measures who')
    print('never reached it. Neither is a verdict. A global stylesheet rule or an')
    print('ancestor `focus-within` shell may cover any of these — check which,')
    print('before styling anything. And a control reached only by pointer or by')
    print('shortcut may be right to have no focus marker at all; the question is')
    print('whether anything in the app invites a keyboard to land on it.')
    by_file = defaultdict(int)
    for f, _, _ in mouse_only + stateless:
        by_file[f] += 1
    for f, n in sorted(by_file.items(), key=lambda x: -x[1])[:10]:
        print(f'  {n:4}  {f}')
    if len(by_file) > 10:
        print(f'  … and {len(by_file) - 10} more files (use --json for all)')

    print()
    low = sorted((n, f) for f, n in adoption.items() if n <= 2)
    if not adoption:
        print('PRIMITIVE ADOPTION: no shared-primitive directory found')
        print(f'Looked for: {", ".join(sorted(PRIMITIVE_DIRS))}. If this project keeps')
        print('its reusable components somewhere else, count call sites by hand — the')
        print('finding below is worth the grep either way.')
    else:
        print(f'PRIMITIVE ADOPTION: {len(low)} of {len(adoption)} shared primitives '
              f'have 2 or fewer call sites')
    print('The layer above control geometry, and invisible to it: a footer built')
    print('from two *correct* library buttons passes every check in this report,')
    print('so a dozen files can rebuild one composite by hand while the component')
    print('written to end that sits unused. From outside, that looks like a')
    print('primitive nobody calls.')
    print('A low count is a question, not a verdict — a primitive can be new, or')
    print('genuinely niche, or reached through a wrapper. Ask the follow-up: how')
    print('many places rebuild its shape without it? One consumer against ten')
    print('rebuilds is a migration that never happened, and Phase 3 owes it.')
    for n, f in low:
        print(f'  {n:4}  {f}')

    print()
    print('=' * 72)
    print('These numbers are the audit baseline: quote them in the report, and')
    print('rerun after each phase — the deltas are the progress record.')


if __name__ == '__main__':
    main()
