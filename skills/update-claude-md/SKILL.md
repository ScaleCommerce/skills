---
name: update-claude-md
description: >
  Update or create CLAUDE.md files to reflect the current state of a project. Use this skill whenever
  the user asks to update CLAUDE.md, create CLAUDE.md, improve CLAUDE.md, sync CLAUDE.md, refresh
  project docs for AI agents, or says things like "update the project context", "make sure Claude
  knows about this project", "document the project for AI", or "the CLAUDE.md is outdated". Also
  trigger when the user finishes a significant refactor and says "update the docs" — CLAUDE.md is
  likely what they mean.
---

# Update CLAUDE.md

## Philosophy: Less Is More

CLAUDE.md is not documentation. It's a small, surgical file that steers agents away from mistakes
they'd otherwise make. Every line you add goes into context for every single token the agent
generates — biasing its behavior, costing time, and competing for attention with the actual task.

A recent study benchmarking context files across multiple LLMs found that developer-written
CLAUDE.md files only marginally improved task completion (+4% average), while auto-generated ones
actually hurt performance (-3% average). Both increased cost by over 20%. The takeaway isn't that
CLAUDE.md is useless — it's that most CLAUDE.md files contain the wrong things.

**The core principle:** If an agent can discover it by reading the codebase, it doesn't belong in
CLAUDE.md. These models are RL-trained to explore codebases aggressively — they read package.json,
grep for patterns, trace imports, check configs. They're genuinely good at this. Telling them what
they'd find anyway just wastes context and creates staleness risk.

### The Litmus Test

For every line, ask: **"Would removing this cause an agent to make a mistake or waste significant
time?"** If not, cut it.

### Context Pollution

Everything in CLAUDE.md biases the model. Mention TRPC once and the agent reaches for TRPC even
when it shouldn't. List a legacy directory and the agent puts new files there. It's the "don't
think about pink elephants" problem — mentioning anything makes the model think about it.

This means CLAUDE.md shouldn't just avoid irrelevant information. It should actively avoid
mentioning things you don't want the agent focused on, even if they're true.

## Before Reaching for CLAUDE.md

CLAUDE.md is a last resort, not a first step. When agents misbehave, work through this hierarchy:

1. **Fix the codebase** — If the agent puts files in the wrong place, maybe your structure is
   confusing. If it misuses a tool, maybe the tool's interface is unclear. Fix the root cause.
2. **Improve feedback loops** — Better type checks, unit tests, linting, and CI that the agent
   can run. Make it easy to do the right thing and hard to do the wrong thing.
3. **Use hooks** — Deterministic actions (run lint after edit, run tests before commit) belong
   in hooks, not prose instructions that the agent might ignore.
4. **Then update CLAUDE.md** — For the things that can't be fixed structurally. Conventions that
   break expectations, gotchas that have no code-level signal, workflow rules that aren't
   discoverable.

## What Belongs in CLAUDE.md

### Include (only if agents can't discover it themselves)

- **Behavioral corrections**: Things the agent consistently gets wrong despite having access to
  the code. "Always use `pnpm`, never `npm`" — only if the agent keeps reaching for npm.
- **Architecture decisions and their rationale**: Why you chose X over Y, especially when Y is
  the common default. The "why" isn't in the code.
- **Conventions that break expectations**: Patterns that differ from framework defaults. An agent
  reading a Nuxt project assumes Nuxt conventions — document where you diverge.
- **Gotchas that have burned the team**: Migration quirks, env var requirements, order-of-
  operations traps, silent failure modes. Things with no code-level signal.
- **Non-obvious commands**: Only commands the agent wouldn't find in package.json/Makefile/etc.
  `npm run dev` is obvious. `npm run dev:ssl -- --local-certs` is not.
- **Cross-cutting concerns**: Auth patterns, error handling strategy, logging conventions — things
  that affect many files but live in none.
- **Workflow rules**: Branch naming, PR process, deployment steps — but only team-specific ones.
- **Pointers to deeper docs**: "Read `docs/api-design.md` before touching the API layer" — not
  the docs themselves, just when to read them.

### Exclude (agents discover these on their own)

- **File listings and directory trees**: Agents run `ls`, `find`, and glob. They explore fast.
- **Detailed tech stack descriptions**: A brief stack line (e.g., "Nuxt 4 + NuxtUI + Convex") is
  fine — it helps agents pick the right docs and conventions fast. But don't list every dependency
  or explain what each one does.
- **Prop/API documentation**: Agents read source code and type definitions directly.
- **Code style rules**: If enforced by linters (ESLint/Prettier/Biome), don't duplicate in prose.
  Never send an agent to do a linter's job.
- **Standard language idioms**: Agents already know Python/JS/Go conventions.
- **Implementation details**: If it's in the code, it's in the code.
- **Frequently changing info**: Git log and blame are authoritative.
- **Generic advice**: "Write clean code", "add tests" — agents already try to do this.
- **Anything produced by `/init`**: Auto-generated CLAUDE.md files are almost always noise.
  They contain things the model already found in order to write the file.

## Update Process

### 1. Assess Current State

If a CLAUDE.md exists, audit it ruthlessly:

| Criterion | Check |
|-----------|-------|
| **Necessity** | Could an agent figure this out from the code? Remove it. |
| **Accuracy** | Does it reference files, functions, or patterns that still exist? Verify. |
| **Bias risk** | Does it mention legacy tech or deprecated patterns that might mislead? |
| **Conciseness** | Is there anything verbose, obvious, or duplicated from tooling? |
| **Actionability** | Are instructions specific enough to follow without guessing? |

**The nuclear audit**: Delete the entire file, run the agent on a real task, and see what it
struggles with. What it handles fine on its own didn't need to be there. What it gets wrong is
what your CLAUDE.md should address. This is the most reliable way to figure out what actually
belongs.

### 2. Gather Context

Explore the codebase to understand its current state — but remember, you're gathering context
to identify what the agent would NOT easily discover, not to summarize what's there:

- Read config files (package.json, tsconfig, etc.) to understand what's already discoverable
- Check CI/CD config, linter config, test setup — these are self-documenting
- Read recent commit messages for active work patterns and team conventions
- Look for existing gotchas, workarounds, or non-obvious patterns in the code
- Check for nested CLAUDE.md files that might need updating too

### 3. Draft or Revise

**Target length**: 30-100 lines. Under 150 is acceptable for complex projects. Over 150 means
you're almost certainly including things agents can infer. Many simple projects need only 20-30
lines.

**Recommended structure** (adapt to the project — skip sections that don't apply):

```markdown
# CLAUDE.md

## About This File
CLAUDE.md is agent guidance — decisions, conventions, and gotchas that can't be inferred from
reading code. Keep it minimal: every line competes for the agent's attention and biases its
behavior. Don't add file listings, tech stack descriptions, or anything agents discover by
exploring the source. If an agent can find it in the code, it doesn't belong here.
When updating, ask for each line: "Would removing this cause an agent to make a mistake?"

## Project Overview
[1-2 lines: what this is, who it's for, core stack (e.g., "Nuxt 4 + NuxtUI + Convex")]

## Commands
[Only non-obvious ones. Skip `dev`, `build`, `test` if they're standard.]

## Conventions
[Where this project diverges from framework/language defaults]

## Gotchas
[Things that have burned the team — silent failures, ordering traps, env requirements]
```

The "About This File" section is a self-enforcing guard. It reminds both humans and future
agents to keep the file lean during updates. Always include it.

### 4. Validate

Before finalizing:

- **The discovery test**: For each line, pretend you're an agent with no CLAUDE.md. Could you
  figure this out in under 60 seconds by reading the code? If yes, delete the line.
- **The bias test**: Does any line mention something you DON'T want the agent focused on?
  Even mentioning legacy tech to say "don't use it" makes the agent think about it. Instead,
  make the preferred approach prominent and leave the legacy stuff unmentioned.
- **The staleness test**: Will this line become wrong when someone changes the code without
  updating CLAUDE.md? If it's likely to go stale, it probably belongs in the code instead.
- **The length test**: If over 100 lines, seriously reconsider what's earning its keep.

## Progressive Disclosure

For complex projects, keep the root CLAUDE.md minimal and use nested files for domain-specific
guidance that only loads when agents enter those directories:

```
project/
├── CLAUDE.md                    # 30-60 lines: the essentials
├── src/
│   ├── api/
│   │   └── CLAUDE.md            # API-specific conventions (only loaded when working here)
│   └── db/
│       └── CLAUDE.md            # Migration gotchas, query patterns
└── docs/
    └── architecture.md          # Deep reference (root CLAUDE.md points here)
```

## Common Mistakes

- **Summarizing the codebase**: The most common mistake. Agents explore code faster than they
  read your summary. And your summary will go stale.
- **Running `/init` and shipping it**: Auto-generated files contain exactly what the agent already
  found. By definition, this is the least useful information you could include.
- **Mentioning things to avoid them**: "Don't use the old auth middleware" makes the agent think
  about the old auth middleware. Just don't mention it. Make the new one easy to find.
- **Adding back what you pruned**: If you removed file listings, don't re-add them as
  "architecture overview". The principle stays.
- **Documenting the fix, not the gotcha**: "We fixed the auth bug in v2.3" is useless.
  "Auth tokens expire silently after 24h — always check `token.isValid()` before API calls"
  is useful.
- **Never updating it**: A stale CLAUDE.md is worse than no CLAUDE.md. Models will confidently
  follow outdated instructions, placing files in wrong locations, using deprecated patterns,
  and referencing things that no longer exist.
