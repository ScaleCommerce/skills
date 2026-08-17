# ScaleCommerce Skills

A collection of AI coding skills shared across the ScaleCommerce team. These skills give AI coding assistants (Claude Code, Cursor, Copilot, and others) specialized knowledge and workflows that we've refined through real project work — so the AI gets it right the first time instead of guessing.

Skills are installed via [npx skills](https://github.com/vercel-labs/skills) and work across 40+ AI coding agents.

## Installation

```bash
# Install all ScaleCommerce skills
npx skills add scalecommerce/skills

# Install globally (available in all projects)
npx skills add scalecommerce/skills -g

# Install a specific skill only
npx skills add scalecommerce/skills -s landing-page-guide
```

## Updating

```bash
# Check for updates
npx skills check

# Pull latest versions
npx skills update
```

## Skills in this collection

### landing-page-guide

Build high-converting landing pages with proven conversion psychology and layout patterns. Guides the AI through a six-phase workflow — strategy inputs (awareness stages, message match, offer), layout blueprint, copy rules, build (Nuxt 4 + Nuxt UI v4, form handling, GDPR/double-opt-in compliance for EU/DACH), visuals via OpenRouter, and an end-to-end launch checklist. Includes Core Web Vitals targets, mobile optimization, A/B testing priorities, and lead quality scoring. Cross-references the frontend-design and nuxt-ui skills.

**Use it when:** Creating landing pages, squeeze pages, lead gen pages, optimizing conversion rates, writing landing page copy, or A/B testing page elements.

### frontend-design

Anthropic's official frontend-design skill, extended with additional best practices — guides the AI to create distinctive, production-grade interfaces that avoid generic "AI slop" aesthetics. Starts by looking for the design system the project already has, so new UI extends it instead of inventing a second visual language. Then works in two passes: a compact design plan (palette, type roles, layout, one signature element), self-critiqued against a checklist of current AI-design tells, then implementation with a real quality floor (responsive breakpoints, contrast ratios, focus states, reduced motion). Adds typographic mechanics, a check that the fonts it names can actually be loaded, and UX-writing guidance so the copy doesn't give the page away either.

**Use it when:** Building any web UI — components, pages, dashboards, landing pages, or styling/beautifying existing interfaces.

**Origin:** [anthropics/skills frontend-design](https://github.com/anthropics/skills/tree/main/skills/frontend-design) (Apache 2.0), merged with our additions (codebase-first design-system detection, typographic mechanics, component-vocabulary consistency, Tailwind palette replacement, AI-tells checklist, accessibility floor, banned AI-copy register). Included here so the team gets it automatically.

### code-review

Thorough, opinionated code review that finds real problems — not formatting nits. Runs automated scans (duplicate detection, inconsistency checks, complexity analysis, security patterns, documentation drift) then does a manual architecture and quality review. Produces a prioritized report grouped by severity: critical issues, architecture concerns, documentation drift, code quality, and what's actually done well.

One pass no scanner covers: tracing every destructive operation to its real **blast radius**. A cascade delete is declared as one word in the schema and fires from a handler that shows no sign of it, so the confirmation dialog, the API description and the function name can all describe the smaller act truthfully while the call destroys records nobody named. The bundled cascade mapper assembles the `parent → child` graph and each root's transitive reach (`organizations → 23 tables`) from raw SQL and ORM declarations alike — a number that exists in no single file — and the skill then asks the questions a list of cascades doesn't answer: is this one crossing from a label into the content filed under it, and does the confirmation say what actually dies.

**Use it when:** Reviewing a codebase, auditing code quality, finding duplicates, checking for anti-patterns, hunting tech debt, or any "take a look at my code and tell me what's wrong" request.

**Works with:** All languages and frameworks.

### ui-overhaul

Audit and consolidate a web app's UI that grew organically. Bundled scanners measure the drift first — hardcoded colors, hand-maintained dark-mode twins (`bg-white dark:bg-zinc-900` pairs), spacing literals duplicated across files, ad-hoc font-size ladders — then the skill works in phases: establish a semantic design-token layer, migrate the markup to it, unify N spellings of one idiom into shared primitives, and run hierarchy/polish passes per surface. Every decision carries a measurement; contrast is computed with the included WCAG checker, not eyeballed. Also audits the project's own design rules (CLAUDE.md / AGENTS.md) and guard tests in both directions — too strict (rules that veto design ideas) or too loose (rules that sound binding but catch nothing).

A UI drifts in its **states** as well as at rest, and nothing in a static reading of the markup shows it, so the scanner measures those too: how many spellings each hover/focus property has, how many sites opt out of the focus system, and transitions that name only colors while a state also moves a shadow or a transform (so that half snaps instead of easing). The skill's first question about any state is which cascade layer declares it — a global rule that is unlayered or `!important` overrides every component's own decision *and* every opt-out written against it without the same weight, which is how a codebase ends up with two focus rings per input and forty opt-outs that are dead code but still read as deliberate.

**Use it when:** Cleaning up inconsistent UI or styling, extracting design tokens from hardcoded values, "the UI is a mess" / "every screen looks different" requests, painful dark-mode maintenance, consolidating duplicate components, focus rings or hover states that look wrong or differ per screen, or checking whether a project's design rules and guard tests help or hurt.

**Works with:** Tailwind projects first-class (any framework); includes plain-CSS guidance.

### nano-banana

Generate and edit images using the OpenRouter API with the Nano Banana model (Gemini 3.1 Flash Image). Includes a Python CLI (`scripts/nb.py`) that handles the full flow — prompt enrichment, API calls, base64 decoding, and file output — in a single command. Supports text-to-image generation, image editing (background removal, style transfer, element changes), batch variations, aspect ratios, and resolution control.

**Use it when:** You need AI-generated images — product mockups, hero visuals, illustrations, image editing, or any "make me a picture of..." / "edit this image..." request.

**Requires:** `OPENROUTER_API_KEY` environment variable.

### update-claude-md

Keep CLAUDE.md files useful, lean, and current. Guides the AI through a structured update process — assess the current file, explore the codebase, then draft or revise with a focus on tribal knowledge (architecture decisions, conventions, gotchas) rather than code-level details agents can discover themselves. Includes a self-enforcing "About This File" section that prevents bloat during future updates.

**Use it when:** Creating, updating, or improving CLAUDE.md files, syncing project context for AI agents, or after a significant refactor when the project docs need refreshing.

## Contributing

Add a new skill by creating a folder under `skills/` with a `SKILL.md` file:

```
skills/
├── code-review/
│   ├── SKILL.md
│   └── scripts/        # Automated analysis tools
├── frontend-design/
│   └── SKILL.md
├── landing-page-guide/
│   └── SKILL.md
├── nano-banana/
│   ├── SKILL.md
│   └── scripts/        # CLI wrapper (nb.py)
├── ui-overhaul/
│   ├── SKILL.md
│   └── scripts/        # UI drift scanner, WCAG contrast checker
├── update-claude-md/
│   └── SKILL.md
└── your-new-skill/
    └── SKILL.md
```

See the [Skills documentation](https://github.com/vercel-labs/skills) for the SKILL.md format.
