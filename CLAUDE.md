# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repo Is

A collection of AI coding skills for the ScaleCommerce team, installed via [npx skills](https://github.com/vercel-labs/skills). Skills give AI coding assistants specialized knowledge and workflows. They work across 40+ AI agents (Claude Code, Cursor, Copilot, etc.).

## Repository Structure

```
skills/
├── code-review/
│   ├── SKILL.md                — Automated code quality analysis
│   └── scripts/                — Dupe detection, inconsistency, complexity, security, doc-drift checks
├── frontend-design/
│   └── SKILL.md                — UI design (from anthropics/skills)
├── landing-page-guide/
│   └── SKILL.md                — Conversion-focused landing pages (Nuxt4 + NuxtUI)
└── nano-banana/
    ├── SKILL.md                — Image generation & editing via OpenRouter API
    └── scripts/nb.py           — CLI: generate, edit, balance, stats
```

Each skill is a single `SKILL.md` file with YAML frontmatter (`name`, `description`) followed by markdown instructions.

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

## Conventions

- Skills are self-contained: one folder with a `SKILL.md` file, plus optional `scripts/` for bundled CLIs/tools.
- The README.md lists all skills with descriptions and "Use it when" guidance — update it when adding/removing skills.
- Skills that depend on external APIs (e.g., nano-banana needs `OPENROUTER_API_KEY`) must document the required env vars.
