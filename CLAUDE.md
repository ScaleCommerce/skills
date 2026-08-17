# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repo Is

A collection of AI coding skills for the ScaleCommerce team, installed via [npx skills](https://github.com/vercel-labs/skills). Skills give AI coding assistants specialized knowledge and workflows. They work across 40+ AI agents (Claude Code, Cursor, Copilot, etc.).

## Repository Structure

```
skills/
├── code-review/
│   ├── SKILL.md                — Automated code quality analysis
│   ├── scripts/                — Dupe detection, inconsistency, complexity, security, doc-drift, cascade map
│   └── evals/                  — Test prompts + assertions for the review behaviours (see Evaluating Skill Changes)
├── frontend-design/
│   └── SKILL.md                — UI design (fork of anthropics/claude-code plugin, see Updating Skills)
├── landing-page-guide/
│   └── SKILL.md                — Conversion-focused landing pages (Nuxt4 + NuxtUI)
├── nano-banana/
│   ├── SKILL.md                — Image generation & editing via OpenRouter API
│   └── scripts/nb.py           — CLI: generate, edit, balance, stats
├── ui-overhaul/
│   ├── SKILL.md                — UI drift audit & consolidation into a design-token system
│   └── scripts/                — Drift scanner (scan_ui_drift.py), WCAG contrast checker (contrast.py)
└── update-claude-md/
    └── SKILL.md                — Structured CLAUDE.md creation & maintenance

tests/                          — Fixtures for the bundled scripts (see Testing the Scripts)
.github/workflows/tests.yml     — Runs those fixtures, plus every scanner, on push
```

Each skill is a single `SKILL.md` file with YAML frontmatter (`name`, `description`) followed by markdown instructions.

## Testing the Scripts

`tests/` holds plain python scripts that exit non-zero on failure — no runner, no dependencies, nothing to install:

```bash
python3 tests/test_find_complexity.py    # one file
for t in tests/test_*.py; do python3 "$t"; done   # all of them, as CI does
```

**It sits outside `skills/` deliberately.** Everything under a skill folder is packaged and installed by `npx skills add`, and end users have no reason to carry test files — `evals/` escapes that only because the packager excludes it by name.

**What belongs here is a script's *output*, not a skill's prose.** A skill is instructions to a model and gets measured by running it (see Evaluating Skill Changes); a script has right answers and gets measured by asserting them. `test_find_complexity.py` is the model to copy: each case is a number that script actually got wrong, with the real answer verified by reading the file, and a comment saying what the wrong number was. Fixtures are inline strings so they never depend on a codebase that might change under them.

**Add a case whenever a review has to debunk something the tooling said.** That is the signal the numbers are not trustworthy, and it is how `find_complexity.py` came to report a 16-line function as 444 lines for as long as it did — the wrongness was visible in every report and nothing captured it.

`check_cascades.py` still has no fixtures; its resolvers were verified by hand against four repos, which is not repeatable. That is the next gap to close.

**CI conventions the workflow depends on:** a script named `check_*`, `find_*` or `scan_*` takes a repo path as `argv[1]` and prints a report, so CI can point it at this repo to prove it runs. Scripts with their own argument shape (`nb.py`'s subcommands, `contrast.py`'s colour pairs) must not use those prefixes, or CI will invoke them wrongly.

## Adding a New Skill

Create `skills/<skill-name>/SKILL.md` with this structure:

```markdown
---
name: <skill-name>
description: <trigger description — when should an AI agent activate this skill>
---

<skill instructions in markdown>
```

The `description` field in frontmatter is critical — it controls when AI agents trigger the skill. Write it as a detailed activation prompt, not a summary.

## Local Development Workflow

To test skills you're editing, install them globally from the local repo path. This symlinks into `~/.claude/skills/` (and other agent dirs under `~/`) so Claude Code picks them up across all projects:

```bash
# Install/update all skills globally from local repo
npx skills add . -g --all

# Install/update a specific skill globally
npx skills add . -g -s <skill-name>
```

`add` overwrites previous installs, so re-run the same command after switching from the GitHub version to your local checkout. By default skills are symlinked, so edits to your repo are reflected immediately without reinstalling.

## End-User Install Commands

```bash
# Install all skills from GitHub
npx skills add scalecommerce/skills

# Install globally
npx skills add scalecommerce/skills -g

# Install a single skill
npx skills add scalecommerce/skills -s <skill-name>

# Check for updates / pull latest
npx skills check
npx skills update
```

## Updating Skills

When asked to update or improve a skill, always edit the local SKILL.md in this repo — this is the development version. Users will later install it via `npx skills add scalecommerce/skills`. Use the `/skill-creator` skill for creating, modifying, and testing skills.

**Note that `~/.agents/skills/<name>/` is a real directory copy, not a symlink to this repo** — so the installed skill an agent actually loads can lag your edits by however long it has been since the last `npx skills add . -g`. Verify which version you are testing (`grep` for a phrase you just wrote) before concluding a change had no effect.

### Evaluating Skill Changes

Referenced by the `evals/` directories above. A skill change is a behavioural change, so measure it against the previous version rather than reasoning about it — snapshot the old skill, run both on the same prompts, and compare.

**Use at least three runs per configuration, and credit only differences that are consistent within a configuration.** This is the rule that cost the most to learn: a single-run A/B on `code-review` appeared to show the new section displacing a security finding, and three repeats showed that same finding appearing in only 1 of 3 *identical baseline* runs. Reviews of a real codebase reliably surface their top findings and vary in the tail, so any single-run difference in the tail is noise wearing the costume of a result. The effect that turned out to be real showed 3/3 against 0/3.

Two more things worth knowing before you spend the tokens:

- **Ask agents to return findings as text, not to write report files** — the Write tool refuses agent-authored reports, and eight runs each discovered that the hard way. Extract their final message from the transcript instead.
- **Prompts that cap the output ("the 5 most serious problems") manufacture displacement**, since a new finding must push another out. Leave the count open when the question is whether a change *adds* anything.

A bundled script is different: it has a right answer, so it gets fixtures rather than eval runs — see Testing the Scripts.

### Skills Forked from Upstream

`frontend-design` is a fork of Anthropic's skill (Apache 2.0). Upstream lives in two places that carry byte-identical copies — https://github.com/anthropics/skills/tree/main/skills/frontend-design (canonical) and https://github.com/anthropics/claude-code/tree/main/plugins/frontend-design/skills/frontend-design (plugin mirror, lags the canonical repo by days). Upstream rewrites this skill periodically, so when syncing, fetch the upstream SKILL.md, **merge** it with our additions, and never overwrite the local copy wholesale. Diffing by hand is the whole job — our copy is roughly twice upstream's length and every extra paragraph is deliberate.

Our additions on top of upstream: the codebase-first section (find the design system the project already has before inventing one), concrete typographic mechanics plus a loadable-font reality check, component-vocabulary consistency, Tailwind replace-don't-extend palette guidance, a checkable list of current AI-design tells, imagery guidance, an accessibility floor with actual numbers, modern-CSS pointers, persisting the token plan so the second screen inherits it, the banned AI-copy register, and a pushier trigger description. Upstream's own material is otherwise kept intact, including its voice.

Two upstream lines are deliberately dropped as redundant: its standalone "consider written content carefully" pointer (the Writing section covers it) and its `LICENSE.txt` reference (we cite the upstream URL in frontmatter instead, since we don't vendor the file).

Last synced: August 2026 — upstream unchanged since its 2026-06-09 rewrite (`anthropics/skills` 2235be7), verified against both locations.

## Conventions

- Skills are self-contained: one folder with a `SKILL.md` file, plus optional `scripts/` for bundled CLIs/tools.
- The README.md lists all skills with descriptions and "Use it when" guidance — update it when adding/removing skills.
- Skills that depend on external APIs (e.g., nano-banana needs `OPENROUTER_API_KEY`) must document the required env vars.
