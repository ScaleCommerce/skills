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

Anthropic's official frontend-design skill, extended with additional best practices — guides the AI to create distinctive, production-grade interfaces that avoid generic "AI slop" aesthetics. Works in two passes: first a compact design plan (palette, type roles, layout, one signature element), self-critiqued against known AI-default looks, then implementation with a quality floor (responsive, keyboard focus, reduced motion). Includes UX-writing guidance so the copy doesn't give the page away either.

**Use it when:** Building any web UI — components, pages, dashboards, landing pages, or styling/beautifying existing interfaces.

**Origin:** [anthropics/claude-code frontend-design plugin](https://github.com/anthropics/claude-code/tree/main/plugins/frontend-design), merged with our additions (component-vocabulary consistency, Tailwind palette replacement, banned AI-copy register). Included here so the team gets it automatically.

### code-review

Thorough, opinionated code review that finds real problems — not formatting nits. Runs automated scans (duplicate detection, inconsistency checks, complexity analysis, security patterns, documentation drift) then does a manual architecture and quality review. Produces a prioritized report grouped by severity: critical issues, architecture concerns, documentation drift, code quality, and what's actually done well.

**Use it when:** Reviewing a codebase, auditing code quality, finding duplicates, checking for anti-patterns, hunting tech debt, or any "take a look at my code and tell me what's wrong" request.

**Works with:** All languages and frameworks.

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
├── update-claude-md/
│   └── SKILL.md
└── your-new-skill/
    └── SKILL.md
```

See the [Skills documentation](https://github.com/vercel-labs/skills) for the SKILL.md format.
