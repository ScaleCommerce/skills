---
name: ui-overhaul
description: "Audit and consolidate a web app's UI: measure visual drift (hardcoded colors, ad-hoc font sizes, duplicated spacing literals, hand-maintained dark-mode twins, N spellings of one component, hand-rolled copies of the UI library's own button/input re-typed inline, inconsistent action-row order and alignment, inconsistent or doubled focus rings and hover states, controls styled for the mouse but not the keyboard), establish a semantic design-token layer, migrate the markup to it, unify duplicated UI into shared primitives, and run hierarchy and polish passes per surface. Also audits the project's own design rules (CLAUDE.md / AGENTS.md) and guard tests in both directions — too strict (rules that veto design ideas) or too loose (rules that sound binding but catch nothing). Use this skill whenever the user wants to clean up, unify, or systematize an app's UI, design, or styling — phrases like 'make the design consistent', 'the UI is a mess', 'every screen looks different', 'clean up the frontend', 'extract a design system', 'design tokens', 'dark mode is painful to maintain', 'UI audit', 'consolidate components', 'make it look professional', 'polish pass', 'the focus ring looks wrong', or 'hover behaves differently on every screen' — and when they ask whether their design rules or guard tests have gone too far or aren't pulling their weight. Also trigger when a restyle or redesign request reveals organic growth (many one-off styles) rather than one bad screen. Works best on Tailwind projects; includes guidance for plain CSS."
---

# UI Overhaul Skill

Take a UI that grew organically and consolidate it into one that reads as designed — the way a senior design engineer would: audit first, decide from measurements, build the vocabulary before migrating to it, and record every decision where the next person will read it. The goal is a genuinely beautiful, coherent app, not compliance: every rule below exists to *free* design effort from maintenance drag, and any rule that starts blocking good design ideas is being misapplied (see "Consolidation must not freeze the design").

## Philosophy

**Measure, then move.** Every claim in the audit and every decision in the execution carries a number, a file reference, or a screenshot. "The type scale is inconsistent" persuades nobody; "726 inline font sizes spanning 19 distinct values, 9 of them half-pixel nudges" makes the case, defines done, and lets you rerun the scan after each phase to prove progress. The bundled scanner produces these numbers; your job is to read the flagged sites and turn counts into findings.

**The second file is the defect.** A one-off literal (`min-h-[26px]` on one component) is a measurement of that component and is fine. The same literal spelled in two files is shared vocabulary kept in two places — the next retune will find one of them. This single test separates "leave it" from "name it": don't force every value into a token, and don't leave any duplicated value out.

**Hand-maintained dark mode is the loudest smell.** Every `bg-white dark:bg-zinc-900` pair is two numbers someone keeps in sync forever, and the dark half silently rots. The fix is never per-call-site discipline — it's a semantic token layer where dark mode is decided once, after which the raw utility becomes unnecessary rather than forbidden.

**Contrast is computed, not eyeballed.** "Looks fine" has shipped 2.50:1 text and 1.71:1 status dots. Check real foreground/background pairs with `contrast.py` — especially small grey text, user-chosen/stored colors, and everything in dark mode. Text owes 4.5:1; graphical objects that carry meaning (dots, borders you must see, icons) owe 3:1.

**Saturation is a budget.** Chrome — navigation, borders, headers, buttons at rest — stays neutral; the saturated pixels carry data (status, identity, priority, warnings). When everything is colored, color says nothing. This is what makes a dense tool read as an instrument panel instead of a circus.

**Record mechanisms, not verdicts.** When you decide something (and especially when you *reject* something), write down the checkable reason where the next reader will look — in the component, next to the token, in the commit. "A full-width rule crosses the avatar gutter" is a mechanism a future redesign can test its idea against; "no lines between comments" is a verdict that bans things nobody evaluated. Scope every rejection to its premise.

## Process

### Phase 0 — Audit and report (always first; stop for approval before executing)

1. **Scan for drift:**
   ```bash
   python3 <skill-path>/scripts/scan_ui_drift.py <src-dir>          # human-readable
   python3 <skill-path>/scripts/scan_ui_drift.py <src-dir> --json   # full site lists
   ```
   This measures: raw palette utilities bypassing tokens, hand-maintained dark twins, arbitrary values duplicated across files, the inline font-size ladder, tracking values, raw shadows, hex colors in CSS; then interactive state — the spellings of each hover/focus property, sites that opt out of the focus system, and transitions that name only colors while a state also moves a shadow or transform; and finally what the markup *is* rather than how it looks: control geometry spelled inline (grouped by signature, so two files sharing one surface as a component spelled twice), controls styled for the mouse only, and shared primitives with almost no call sites. Read the flagged sites before reporting — counts are signal, not verdicts.

   **A quiet scan is a finding, not a pass.** The value checks can all read zero on a codebase that is still substantially hand-built — every color a token, every size on the ladder — because a hand-rolled copy of your button library is made *entirely of correct utilities*, and a footer that rebuilds your own save bar is made of entirely correct components. Duplication hides one layer above wherever you last looked: values → controls → composites. The last three sections chase it up that ladder, and steps 3–5 below carry it further than any regex can.

2. **Read the foundation:** the main stylesheet, Tailwind/theme config, and the component library's theme config (e.g. `app.config.ts` for Nuxt UI). Is there a token layer at all? Is it used? Does the component library's dark theme collapse distinct tokens onto identical values? (Nuxt UI's dark defaults map `bg-muted`, `bg-elevated`, and `border` to one color — borders drawn in the surface's own color are invisible, and `hover:bg-elevated` on `bg-muted` is a 0-delta hover. Check with `getComputedStyle`, not by reading the docs.)

3. **Inventory the idioms.** Start from the scan's control-geometry clusters — those are the ones a grep would have to be lucky to find — then count spellings for the idioms it cannot see: section labels (how many combinations of size/weight/uppercase/tracking say "this is a section"?), page headers, empty states, avatars, field rows, menus. Five spellings of one idiom is one component waiting to exist.

   **Take the action row seriously — it is the most-repeated composite in most apps and the one nobody names.** Every modal footer, every inline editor commit, every delete confirmation is the same object: a primary, a way out, sometimes a destructive escape and a status line. It drifts on four axes that no value scan can see, so check each one explicitly across *every* such row before concluding anything:
   - **Order of the pair** — is the primary first or last? Expect to find both, and expect the split to be principled rather than random: a right-aligned dialog footer and a left-aligned row under a text field can honestly disagree, because the primary belongs at the row's *terminal end* and that end mirrors with the alignment. Establish which rule the codebase is already following before imposing one; most have converged further than they look.
   - **Alignment** — a row that commits a *field* aligns to that field's edge; a row that commits a *surface* aligns to the surface's closing corner. Two alignments is not automatically drift.
   - **Where the keyboard hint lives** — on the button it fires, or floating at the far end of the row? Inconsistency here is almost always the age of each call site rather than a decision, including whether the hint hides on small screens.
   - **Whether the primary carries an icon** — and whether that icon says anything the label does not. "Create + plus" adds the fact that a new thing appears; "Save + check" is a picture of the word next to it.

   **Then connect what you found to what the project ships.** A geometry cluster plus the theme config you read in step 2 answers two questions at once that neither answers alone: *which* component the cluster should have been (compare the cluster's padding and text step against the library's size ramp — an exact match means it was re-typed by hand), and what a guard against the recurrence should read. Have the guard derive that ramp from the installed library at test time rather than restating the numbers, so a version bump moves the guard with it. Watch for the theme having already been tuned to match the hand-rolls: that means the consolidation was done once and only the originals were left behind, and the migration is mechanical.

4. **Inventory the states, the same way.** Hover, focus, active and disabled drift exactly like colors do — N spellings of one thing, maintained per call site — and nothing in a static reading of the markup shows it. Three questions, in this order:
   - **Where is each state declared, and which layer wins?** This is the one that hides. A global rule that is unlayered or `!important` overrides every component's own decision *and every opt-out written against it without the same weight* — so those opt-outs are dead code that still reads as deliberate, and the component's considered choice never renders. Check with `getComputedStyle` on a real focused element, not by reading the rules. Symptoms: two concentric focus rings (the library's own plus the global one), a component that sets `focus:outline-none` on purpose and gets a ring anyway, a `border-radius` in a global focus rule *mutating the element* so round controls square off.
   - **How many spellings does one state have on one kind of object?** Two different hovers for two kinds of card is drift; a card and a menu item legitimately differ. Group by object, not by file.
   - **Which interactive things have no state at all?** The scan now counts two buckets — controls declaring a hover and no focus, and controls declaring neither — but a count is where this starts, not where it ends: a global stylesheet rule or an ancestor `focus-within` shell may cover any of them, and that is invisible to a per-element check. Read the global focus rule first, then tab through a real form rather than one field. **A zero in the opt-out count means nobody fought the focus system, not that everything reached it** — those two numbers answer different questions and an app can score 0 on the first while most of its controls have no marker at all.
   - **Absence is not automatically a defect, and this is where a keyboard-first reading pays.** A control reached only by pointer or by a shortcut — a board driven by arrow keys, a palette opened with ⌘K — may be entirely right to carry no focus marker, and painting all of them is busywork that also dilutes the marker where it matters. The question is not "is there a ring" but "does anything in this app invite a keyboard to land here": a tab-order flow, a component deliberately converted from a `<div>` so it could be reached, a documented shortcut. Where a rule bans per-element focus styling to keep focus stated once, check that the rule's own markup-side guard covers *controls* and not only text fields — otherwise it forbids the local fix without ever checking that the global one arrived.

5. **Look at it.** Open the running app (browser tools) in both color modes at realistic data density. Screenshot the main surfaces. Note: invisible borders, 0-delta hovers, hierarchy failures (can you tell a title from its metadata at arm's length?), and any element that lights up on hover but does nothing when clicked.

6. **Spot-check contrast** with `contrast.py` on the real pairs found in steps 2–5.

7. **Audit the rule system itself** — CLAUDE.md / AGENTS.md design sections, guard tests, custom lint rules (see "Auditing the rule system" below). The drift scan is the cross-check in both directions: a loud scan under strict-sounding rules means the rules aren't actually enforced; a quiet scan plus a history of design work stalling against green tests means they're a cage.

8. **Write the report** (format below) and stop for approval of the phased plan. On explicit "just fix it" instructions, present the summary numbers and proceed.

### Phase 1 — The token layer

Build the vocabulary *before* migrating anything to it. Never the reverse: migrating to tokens that don't exist yet produces a second generation of literals.

- **Semantic surfaces and text**, not palette names: `bg-default/muted/elevated/accented`, `text-default/muted/dimmed/highlighted`, `border-default/accented` (or your library's equivalents). Each name is a *role*; dark mode is decided once per role, here.
- **Repair the dark ramp first** if the audit found collapsed steps — every migrated call site inherits the fix for free, and per-call-site workarounds ("use the emphasis border so it's visible") spend emphasis on being merely visible.
- **Type scale: count, then close.** Take the audit's distinct-sizes list and collapse it to ~5–7 named steps, each with a job written beside it ("13px — the workhorse; 12px — labels and metadata"). Tune line-height per step: large type on inherited 1.5 leading is what makes headlines read as scaled-up body text. If the app has genuine display moments (a stat readout, a wordmark), declare a separate display tier with its own tracking rather than letting sites reach past the ladder onto untuned defaults.
- **Elevation as a ramp**: 2–4 shadow tokens defined once per color mode (black-alpha shadows vanish on dark surfaces). Radius as containment depth: small inside a surface, medium for a surface, large for a container of surfaces.
- **Shared geometry**: every duplicated arbitrary value from the audit becomes a named token (`--spacing-column`, `--spacing-row`); one-offs stay literals.
- Every scale is a closed set **with its reasoning written next to the declarations** — the stylesheet is where the measurements live.

### Phase 2 — Migration

Mechanical, batched by family, and free of design changes:

- Raw palette → semantic tokens. Inline font sizes → named steps. Raw shadows → the ramp. Duplicated literals → their new tokens.
- **Migration is not a retune.** If a value should *change* while migrating, that's a design decision — record it separately with its reason. Mixing the two makes both unreviewable.
- Verify each batch with the project's cheapest sufficient check (lint / build); rerun the drift scan after the sweep and quote the delta.
- **Legitimate exceptions are named, with reasons, not silently skipped.** A brand moment (auth page, error page, logo) may keep expressive one-off color — as a written-down exception, so the next person knows it's deliberate.

### Phase 3 — Consolidate primitives

- **One component per idiom — but a different shape is not another spelling.** For each multi-spelling idiom from the audit: build (or adopt) one primitive, migrate every call site, and let the consolidation *reveal* the drift — five section-label spellings at four letter-spacings only become "these are the same thing" once they're one component. Consolidate first, retune second. The counterpart to "the second file is the defect" applies here: before collapsing a set, separate the members that differ by *history* from the ones that differ by *shape*. A field that reads as text until you click it, or that sits chrome-less inside a row because its container draws the boundary, is not a boxed input spelled differently — forcing it into the library component means stripping that component's ring, padding and radius back off, and the plain element was the simpler thing all along. Consolidate the historical half; document where the line falls and why.
- **Prefer the component library's own primitives** before hand-rolling — check what it actually ships (empty states, user rows, keyboard hints, dashboard shells) before building a private version.
- **Finish the migration, or the primitive is worse than nothing.** The scan's adoption list is the check: a shared primitive with one or two call sites, in a codebase where ten files rebuild its shape inline, is a consolidation that was designed and then abandoned. It costs more than never building it — the codebase now carries both the component and every hand-rolled copy, and the component's existence makes the copies *look* like deliberate exceptions. Migrate every call site in the same pass, and where one genuinely cannot adopt it, that reason goes in the primitive's own docstring.
- **"It changes nothing the user sees" is not a reason to skip a migration — it is what a correct one looks like.** Phases 1–3 are defined by producing no visual change; that is the property that makes them safe to run standalone, and quoting it as a cost is how a consolidation pass talks itself out of its own job. If you *do* defer, the honest reasons are risk (a large diff across surfaces you cannot verify), sequencing (it belongs after another change), or scope (the user approved something narrower) — name whichever it is, in those words, in the place the next reader will look. A deferral recorded as "no user-visible outcome" reads to that reader as a decision that the work was pointless, and they will not revisit it.
- **User-chosen / stored colors** (tags, statuses, avatars) need a correction recipe, not raw application: set the *lightness* in CSS and keep the user's hue (`oklch(from var(--swatch) L c h)`). Mixing toward black/white cannot fix a dark stored hex — the output lightness depends on the input's. One recipe, verified with `contrast.py` across the actual offered palette, in both modes.
- Derived identity color (avatar tints from names) beats N identical grey discs on any surface where several people appear.

### Phase 4 — Surface passes

With the vocabulary in place, polish each key surface (main view, detail view/panel, lists, navigation) one at a time:

- **One focal point per surface**; type size/weight express the hierarchy; everything aligns to a shared inset.
- **Honest affordances**: only interactive things light up on hover. Compute the hover delta — a sub-1% lightness change is a rendering fault, not a hover state.
- **One treatment per kind of object, states included.** Correctness is not enough: two hovers that are both honest, both visible and different is still drift, and it is the kind a static scan cannot see. Settle it by asking what the treatment *spends* rather than which looks nicer — a hover that tints the border and title with the brand color spends saturation on a pointer position, which the saturation budget reserves for data; one that lifts and steps the border a neutral notch spends motion instead, and can also answer the click with an `:active` press. Whichever wins, apply it to every member of the class in the same pass and grep for the stragglers — a create-tile or an empty slot may legitimately keep its own highlight, as a written-down exception.
- **Empty states are invitations**: the affordance to add the first item, not a sentence reporting absence. A heading over a void is worse than no heading.
- **Metadata is quieter than content**: a byline smaller than the text it introduces; timestamps behind tooltips carrying the exact moment; action buttons quiet at rest, reachable by keyboard (`focus-within`).
- Density is a feature in a work tool — tighten toward the data, not toward whitespace for its own sake.
- **Record each surface's decisions in the component** as mechanisms with measurements, including the alternatives tried and *why* they failed.

### Phase 5 — Verify like a user

Automated checks generally cannot see the client. Load the app: both color modes, realistic data, keyboard navigation, the browser console. Rerun the drift scan and the contrast checks; quote before/after numbers in the summary.

## Report format (Phase 0 output)

```markdown
# UI Audit: [project]

## Summary
[2–3 sentences: overall coherence, the biggest maintenance drag, one thing done well]

## The numbers
[Drift table: raw palette count, dark twins, duplicated literals, distinct font
sizes, raw shadows — each with the worst offenders]

## Contrast failures
[Measured pairs under threshold, with ratios and where they appear]

## Idiom inventory
[N spellings of X → one component; the concrete spellings found. Include the
control-geometry clusters, each with the library component it duplicates (or
"none — this is genuinely bespoke"), and the action row on its four axes:
order, alignment, hint placement, icon on the primary]

## State drift
[Per state: where it is declared and which layer wins; spellings per kind of
object; focus opt-outs and how many of them the cascade makes dead; controls
with a hover and no focus, separated into "no keyboard path reaches this" and
"reachable and unmarked" — only the second is a defect]

## Dark mode debt
[Collapsed token steps, hand-maintained twins, invisible borders/hovers]

## Rule system health
[Verdict per rule source (CLAUDE.md/AGENTS.md sections, each guard test): sound /
too strict / too loose — with the specific signal, and the rewrite or deletion
each failing rule owes]

## Proposed token layer
[Sketch: surface/text roles, the collapsed type scale with jobs, elevation ramp,
geometry tokens — with the audit numbers that justify each]

## Phased plan
[Phases 1–4 scoped to this codebase, each with rough size and what "done" measures]
```

## Auditing the rule system

A project's design rules (CLAUDE.md / AGENTS.md), guard tests, and custom lint rules are part of the UI: they decide what the next design session is allowed to try. Both failure directions are real, both have shipped, and each has checkable signals — judge rules by these, not by tone.

**Too strict — the rules veto design ideas.** Signals:

- **Verdict language without a mechanism**: "no gradients", "never use X", "rejected then and still rejected". A conclusion generalizes past its evidence and bans devices nobody evaluated; the mechanism form ("a full-width rule crosses the avatar gutter") bans exactly one thing and tells a future design how to check whether its idea escapes.
- **Guards that pin tuning, not decisions**: a test asserting `text-dimmed` exactly (which grey is tuning) instead of "low priority renders neutral" (the decision). Every retune becomes a test edit, and test edits feel forbidden.
- **Guards that fail on subtraction**: assertions that some decoration, token usage, or literal *must exist*. A design pass that legitimately removes the thing fails CI for making the app cleaner.
- **No amendment path**: exemption lists exist but nothing says extending them is legitimate — so a failing guard reads as a veto and the idea gets abandoned. This can kill a whole design session while every individual rule looks reasonable.
- **Rules broader than the codebase's own practice**: a ban the app already violates in shipped, deliberate code (e.g. "no gradients" while gradient masks fade every scroll edge). Ambiguity taxes every future decision.

**Too loose — the rules sound binding but catch nothing.** Signals:

- **Prose without enforcement**: strict-sounding rules while the drift scan is loud. A rule nothing checks is a wish; per-call-site discipline ("remember to use the visible border on recessed surfaces") is a tax that always eventually goes unpaid.
- **Allowlists narrower than the defect**: a guard matching four grey families while the codebase paints in twelve, or four variant prefixes while `focus-visible:` walks past. Verify by testing a known offender against the guard's actual pattern — a green test over live violations is worse than no test.
- **Guards that restate the value they police**: asserting the stylesheet contains the number someone just set recomputes nothing and can't fail when it matters. The guard must re-derive the property (contrast from the declared lightness, the token from the declaration) so retuning is checked, not mirrored.
- **Confident claims with nothing behind them**: comments or docs asserting "verified", "computed", "guaranteed" where no test exists — check two or three by hand; one false claim means none can be trusted.
- **One rule, several records, updated in one**: the same rule in CLAUDE.md, a comment, and a test, saying different things.

**The four-condition test** for any single rule: it (1) names a mechanism, not a conclusion; (2) is enforced by something that *recomputes* the property rather than restating the value; (3) carries a measurement, a file reference, or a test; (4) is applied everywhere it is recorded. Failing all four → delete it, don't soften it. Failing some → rewrite to pass.

**Remedies.** Too strict: rewrite verdicts as mechanisms scoped to their premises, give every guard a named exemption list, and state the amendment workflow *in the rules document itself* ("a failing guard asks for a reason, not a retreat"). Too loose: don't write more prose — encode the two or three highest-value invariants as recomputing guards (contrast, raw palette, cross-file duplication) and leave taste to the surface passes.

## Consolidation must not freeze the design

The audit section above describes how to *detect* an over- or under-constrained rule system; this is how to avoid writing one. Lessons paid for the hard way — a consolidation pass that overshoots turns into a cage that blocks the next good idea:

- **Build the amendment path in from the start.** Every convention you introduce gets its exemption list and a sentence in the rules document saying a failing guard asks for a written reason, not a retreat. Every rejection you record gets its mechanism and its premise, so the next redesign knows when it's re-opened.
- **Don't gold-plate the rulebook.** Meta-work (rules, guards, docs about the system) serves the pixels. If successive commits produce no visible change, return to a surface.
- **Closed scales need a pressure valve.** A display moment, a brand gradient, an expressive empty state — deliberate exceptions, written down, are what keep the system from flattening the app into beige. An instrument panel still has one signature interaction where it's allowed to be theatrical.

## Plain-CSS codebases (no Tailwind)

Same phases, different mechanics: the scanner's CSS checks (hex colors, font sizes, letter-spacing, shadows) still apply; grep additionally for `rgb(`/`rgba(`/`hsl(` literals. The token layer is custom properties on `:root` with a `.dark`/`prefers-color-scheme` override block; migration replaces literals with `var(--…)`. The second-file test, the contrast thresholds, and the surface passes are unchanged.

## Edge cases

- **Small project (< ~30 components):** skip the scanner, read everything; the phases still apply but may compress into two passes (tokens+migration, consolidation+polish).
- **A design system already exists but is drifting:** the audit becomes "where does the markup reach around it, and why" — often the system is missing a token people needed (that's a finding), not just discipline.
- **Component library with themable tokens (Nuxt UI, shadcn, etc.):** override at the library's theme layer so its internals inherit the fix; never fork components to restyle them.
- **Mid-feature-freeze / hotfix culture:** phases 1–2 are safe to run standalone (zero visual change when done right — that's verifiable: screenshot before/after); phases 3–4 change pixels and need product buy-in.
- **User asks for a redesign of one screen, but the audit shows systemic drift:** do the screen — using tokens if they exist — and report the systemic findings separately rather than holding the screen hostage to the overhaul.
