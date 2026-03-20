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

Build high-converting landing pages with proven conversion psychology and layout patterns. Based on testing 300+ pages, this skill guides the AI through the full workflow — from strategy (customer awareness stages, message match, psychology principles) to code (Nuxt4 + NuxtUI) to deployment. Includes mobile optimization, A/B testing priorities, page speed checklists, and AI-generated visuals via OpenRouter.

**Use it when:** Creating landing pages, squeeze pages, lead gen pages, optimizing conversion rates, writing landing page copy, or A/B testing page elements.

### code-review

Thorough, opinionated code review that finds real problems — not formatting nits. Runs automated scans (duplicate detection, inconsistency checks, complexity analysis, security patterns, documentation drift) then does a manual architecture and quality review. Produces a prioritized report grouped by severity: critical issues, architecture concerns, documentation drift, code quality, and what's actually done well.

**Use it when:** Reviewing a codebase, auditing code quality, finding duplicates, checking for anti-patterns, hunting tech debt, or any "take a look at my code and tell me what's wrong" request.

**Works with:** All languages and frameworks.

### nano-banana

Generate images using the OpenRouter API with the Nano Banana model (Gemini 2.5 Flash Image). Handles the full flow: crafting a detailed prompt from a brief description, calling the API, decoding the base64 response, saving the PNG, and displaying it — all in one step.

**Use it when:** You need AI-generated images — product mockups, hero visuals, illustrations, or any "make me a picture of..." request.

**Requires:** `OPENROUTER_API_KEY` environment variable.

## Contributing

Add a new skill by creating a folder under `skills/` with a `SKILL.md` file:

```
skills/
├── code-review/
│   └── SKILL.md
├── landing-page-guide/
│   └── SKILL.md
├── nano-banana/
│   └── SKILL.md
└── your-new-skill/
    └── SKILL.md
```

See the [Skills documentation](https://github.com/vercel-labs/skills) for the SKILL.md format.
