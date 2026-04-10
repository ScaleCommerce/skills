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

The most valuable CLAUDE.md content is knowledge that exists only in developers' heads — the gap
between "what code can tell you" and "what successful team members know."

### Categories of Invisible Knowledge

- **Behavioral corrections**: Things the agent consistently gets wrong despite having access to
  the code. "Always use `pnpm`, never `npm`" — only if the agent keeps reaching for npm.
- **Architecture decisions and their rationale**: Why you chose X over Y, especially when Y is
  the common default. The "why" isn't in the code.
- **Conventions that break expectations**: Patterns that differ from framework defaults. An agent
  reading a Nuxt project assumes Nuxt conventions — document where you diverge.
- **External service quirks**: API behaviors that aren't obvious from the SDK. "Stripe webhook
  needs raw body, not parsed JSON." "The geocoding API returns 200 with an error field instead
  of 4xx." "Rate limited to 100 req/min — we batch calls."
- **Deployment constraints**: Platform limits that shape code decisions. "Vercel serverless
  times out at 60s." "Edge functions can't use Node fs." "Always test with `--turbo` locally
  because CI uses Turborepo."
- **Business domain context**: What the app does in human terms. Domain-specific terminology
  ("a 'folio' is a customer's portfolio"), business rules not enforced in code ("users can only
  have one active subscription"), state transitions ("orders go pending → paid → shipped, never
  backwards").
- **Cross-service dependencies**: "This service consumes events from the billing service." "The
  mobile app expects API v1 to remain stable." Things that break other systems if changed.
- **Security boundaries and trust assumptions**: "User input is sanitized in API middleware —
  downstream code assumes clean data." "Never store PII outside the users table." "Auth tokens
  use RS256, not HS256."
- **Environment quirks**: "CI runs Ubuntu but local dev is macOS — path case sensitivity differs."
  "Test DB is on port 5433, not 5432." "Redis in staging is Upstash REST, not a socket."
- **Gotchas that have burned the team**: Migration quirks, order-of-operations traps, silent
  failure modes. Things with no code-level signal.
- **Non-obvious commands**: Only commands the agent wouldn't find in package.json/Makefile/etc.
- **Pointers to deeper docs**: "Read `docs/api-design.md` before touching the API layer" — not
  the docs themselves, just when to read them.

### What to Exclude (agents discover these on their own)

- **File listings and directory trees**: Agents run `ls`, `find`, and glob. They explore fast.
- **Detailed tech stack descriptions**: A brief stack line (e.g., "Nuxt 4 + NuxtUI + Convex") is
  fine — it helps agents pick the right docs and conventions fast. But don't list every dependency.
- **Prop/API documentation**: Agents read source code and type definitions directly.
- **Code style rules**: If enforced by linters (ESLint/Prettier/Biome), don't duplicate in prose.
- **Standard language idioms**: Agents already know Python/JS/Go conventions.
- **Implementation details**: If it's in the code, it's in the code.
- **Frequently changing info**: Git log and blame are authoritative.
- **Generic advice**: "Write clean code", "add tests" — agents already try to do this.
- **Anything produced by `/init`**: Auto-generated CLAUDE.md files are almost always noise.

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
| **Completeness** | Is invisible knowledge missing? (see step 3 below) |

### 2. Gather Context

Explore the codebase to understand what's already discoverable (so you don't duplicate it):

- Read config files (package.json, tsconfig, etc.) — this is what agents will find on their own
- Check CI/CD config, linter config, test setup — these are self-documenting
- Read recent commit messages for active work patterns and team conventions
- Check for nested CLAUDE.md files that might need updating too

### 3. Hunt for Missing Knowledge

This is the critical step most CLAUDE.md updates miss. Don't just audit what's there — actively
investigate what's NOT there but should be.

**Mine the codebase for signals:**

- **Git hotspots**: Run `git log --oneline -50` and look for files fixed repeatedly — these
  often signal gotchas worth documenting.
- **TODO/FIXME/HACK comments**: These are developers flagging pain points. Scan for them and
  evaluate whether they reveal gotchas an agent should know about.
- **CI config**: Look for non-obvious steps — custom scripts, environment setup, platform-specific
  workarounds. These often reveal deployment constraints.
- **Dockerfile / deployment configs**: Platform constraints (memory limits, timeouts, OS
  differences) that shape what code is valid.
- **.env.example**: Variables with unclear purposes or non-obvious requirements.
- **Error handling patterns**: Are errors handled consistently? Is there a project-wide strategy
  (Result types, error boundaries, Sentry integration) that new code should follow?

**Ask the developer targeted questions:**

Don't just silently write the file. Prompt the user to surface head-knowledge with specific
questions like:

- "Are there external services with undocumented quirks or rate limits I should note?"
- "Any deployment platform constraints (timeouts, memory limits, OS differences)?"
- "Domain terms or business rules that aren't obvious from the code?"
- "Areas of the codebase that are particularly fragile or surprising to work in?"
- "Team workflow rules — branching strategy, review requirements, deploy process?"
- "Known gotchas that have tripped people up before?"

Skip questions where you already found the answer in the code. Focus on the gaps. Not every
project needs all of these — use judgment based on what you found in steps 1-2.

### 4. Draft or Revise

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

Not every project needs every section. A simple project might only have Overview + Conventions.
A complex one might add sections for domain context, deployment constraints, or security
boundaries — but only if that knowledge is genuinely invisible from the code.

### 5. Validate

Before finalizing:

- **The discovery test**: For each line, pretend you're an agent with no CLAUDE.md. Could you
  figure this out in under 60 seconds by reading the code? If yes, delete the line.
- **The bias test**: Does any line mention something you DON'T want the agent focused on?
  Even mentioning legacy tech to say "don't use it" makes the agent think about it. Instead,
  make the preferred approach prominent and leave the legacy stuff unmentioned.
- **The staleness test**: Will this line become wrong when someone changes the code without
  updating CLAUDE.md? If it's likely to go stale, it probably belongs in the code instead.
- **The gap test**: Review the "Categories of Invisible Knowledge" above. Is there important
  head-knowledge in any of those categories that you haven't captured?
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
- **Only auditing, never adding**: A CLAUDE.md that's been pruned to perfection but is missing
  critical domain knowledge or deployment constraints is still failing. Pruning and discovering
  are both essential.
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

## Maintenance

With every model release, try deleting sections and see if the agent still performs well.
Models keep getting better at codebase exploration — what needed documenting 6 months ago
might be redundant today. The best CLAUDE.md files shrink over time.

When you notice an agent struggling with something, don't immediately add it to CLAUDE.md.
First ask: can I fix the codebase so the agent wouldn't struggle? Better tests, clearer
structure, improved naming? Only reach for CLAUDE.md when the structural fix isn't feasible.
