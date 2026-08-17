#!/usr/bin/env python3
"""Regression fixtures for code-review/scripts/find_complexity.py span measurement.

Run: python3 tests/test_find_complexity.py

Every case here is a wrong number this script actually reported. The span heuristic
used to end a function at the next *declaration*, which meant a function followed by
anything that isn't one — a Vue template, top-level `watch()` calls, module-level
code — absorbed all of it. A reviewer then has to debunk the tool, and one did:
`handleKeydown()` was reported at 444 lines when it is 16.

Fixtures are inline so this stays runnable anywhere, with no dependency on the
codebases where the numbers were first found wrong. It sits outside `skills/` on
purpose: everything under a skill folder is packaged by `npx skills add`, and end
users have no reason to install a test file.
"""
import sys
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "skills", "code-review", "scripts"))
import find_complexity as fc  # noqa: E402

FAILURES = []


def check(label, got, want):
    if got == want:
        print(f"  ok   {label}: {got}")
    else:
        print(f"  FAIL {label}: got {got}, want {want}")
        FAILURES.append(label)


def spans(source, ext=".ts", language="js"):
    """{name: (start, end, line_count)} for a source string."""
    lines = source.splitlines(keepends=True)
    if ext in (".vue", ".svelte"):
        lines = fc.vue_script_lines(lines)
    funcs = (fc.extract_functions_py(lines, "fixture" + ext) if language == "py"
             else fc.extract_functions_braces(lines, "fixture" + ext, language))
    return {f.name: (f.start_line, f.end_line, f.line_count) for f in funcs}


# 1. A Vue SFC: the last function in <script setup> must not claim the template.
VUE = '''<script setup lang="ts">
const props = defineProps<{ open: boolean }>()

function handleKeydown(e: KeyboardEvent) {
  if (!e.metaKey) return
  submit()
}

watch(() => props.open, (isOpen) => {
  if (isOpen) reset()
})
</script>

<template>
  <div v-if="props.open" class="panel">
    <button v-for="n in 10" :key="n" @click="handleKeydown">
      {{ n }}
    </button>
  </div>
</template>

<style scoped>
.panel { display: flex; }
</style>
'''
print("Vue SFC — function must stop at its own closing brace, not run to EOF")
v = spans(VUE, ".vue")
check("handleKeydown span", v["handleKeydown"], (4, 7, 4))

# 2. An expression-bodied arrow closes on its own line: no braces ever open, so
#    brace-only tracking handed it everything up to the next declaration.
ARROWS = '''const isReady = computed(() => a && b)

const label = 'unrelated top-level code'
const other = [1, 2, 3]

function later() {
  return 1
}
'''
print("\nExpression-bodied arrow — one line, not everything up to `later`")
a = spans(ARROWS)
check("isReady span", a["isReady"], (1, 1, 1))
check("later span", a["later"], (6, 8, 3))

# 3. Python: a nested helper ends where the body dedents, not at the next sibling def.
PY = '''import os


def outer(items):
    def specific(group):
        props = [p for p in group]
        return len(props) >= 2

    total = 0
    for g in items:
        total += 1
    return total


def sibling():
    pass


main()
'''
print("\nPython nested def — ends at the dedent, not at the next sibling def")
p = spans(PY, ".py", "py")
check("specific span", p["specific"], (5, 7, 3))
check("outer span", p["outer"], (4, 12, 9))
check("sibling span", p["sibling"], (15, 16, 2))

# 4. A regex literal's closing slash is not a line comment. `\/` + `/` looks like
#    `//`, and stripping from there deleted the `)` that balances the call, so a
#    six-line function measured 98 lines because nothing ever closed it.
REGEX_LITERAL = r'''function markup(file) {
  return read(file)
    .replace(/\/\*[\s\S]*?\*\//g, blank)
    .replace(/^\s*\/\/.*$/gm, blank)
}

const AFTER = 'top-level code that must not be absorbed'
'''
print("\nRegex literal — its closing slash must not read as a comment")
r = spans(REGEX_LITERAL)
check("markup span", r["markup"], (1, 5, 5))

# 5. Guard the metrics too: complexity must come from the real body. Before the fix
#    a Vue handler's CC included branches from the template it had swallowed.
print("\nComplexity is computed from the real body only")
lines = VUE.splitlines(keepends=True)
funcs = fc.extract_functions_braces(fc.vue_script_lines(lines), "fixture.vue", "js")
handler = next(f for f in funcs if f.name == "handleKeydown")
check("handleKeydown cyclomatic", handler.cyclomatic, 2)  # base 1 + one `if`

print()
if FAILURES:
    print(f"{len(FAILURES)} failing: {', '.join(FAILURES)}")
    sys.exit(1)
print("all span fixtures pass")
