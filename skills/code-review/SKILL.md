---
name: code-review
description: "Analyze codebases for quality issues, duplicate code, inconsistencies, and bad patterns. Use this skill whenever the user asks to review code quality, find code smells, detect duplicates, check for anti-patterns, audit a codebase, clean up code, find inconsistencies, or do any kind of static analysis or code health check. Also trigger when the user says things like 'review my code', 'find problems in my codebase', 'what should I refactor', 'is this code any good', 'check for bad patterns', 'find duplicate code', 'code audit', or 'tech debt review'. This skill should be used even for casual requests like 'take a look at my project and tell me what's wrong' or 'anything I should fix in here'. Works across all languages and frameworks."
---

# Code Review Skill

Perform a thorough, opinionated code review of a project or set of files. The goal is to find real problems that matter — not nitpick formatting or chase theoretical issues. Think like a senior dev doing a PR review of an entire codebase.

## Philosophy

**Be useful, not exhaustive.** A review that lists 200 minor issues is worse than one that identifies the 10 things that actually matter. Prioritize by impact: bugs > security > architecture > maintainability > style.

**Be specific, not vague.** "This code could be better" helps nobody. "The retry logic in `api/client.ts:34` swallows errors silently — failed requests disappear without logging or propagation" is actionable.

**Show, don't just tell.** When suggesting improvements, include a brief code example of what the fix looks like. Don't rewrite everything — just enough to communicate the pattern.

## Review Process

### Step 1: Understand the Project

Before reviewing anything, get the lay of the land:

```bash
# Project structure (2 levels deep)
find . -type f -not -path '*/node_modules/*' -not -path '*/.git/*' -not -path '*/vendor/*' -not -path '*/.nuxt/*' -not -path '*/.next/*' -not -path '*/dist/*' -not -path '*/__pycache__/*' -not -path '*/.venv/*' | head -100

# Package/dependency info
cat package.json 2>/dev/null || cat requirements.txt 2>/dev/null || cat go.mod 2>/dev/null || cat Cargo.toml 2>/dev/null || echo "No standard package file found"

# Config files that reveal patterns
ls -la *.config.* .eslintrc* .prettierrc* tsconfig* pyproject.toml setup.cfg 2>/dev/null
```

Determine:
- Language(s) and framework(s)
- Project type (API, frontend, CLI, library, full-stack)
- Existing linting/formatting setup
- Test infrastructure (or lack thereof)

This context shapes the entire review. A Vue SFC has different rules than a Go microservice.

### Step 2: Automated Scanning

Run language-appropriate scans to gather data. Don't just read files manually — use tools to find patterns at scale.

#### Duplicate / Similar Code Detection

Find exact duplicate blocks (5+ lines) using a hash-based approach. Auto-detects project language.

```bash
python3 <skill-path>/scripts/find_dupes.py
```

#### Inconsistency Detection

Checks for mixed import styles, inconsistent quotes, leftover console.log/print, TODO/FIXME comments, and empty catch/except blocks.

```bash
python3 <skill-path>/scripts/find_inconsistencies.py
```

#### Large File / Complexity Check

Finds files over 300 lines and functions over 50 lines.

```bash
python3 <skill-path>/scripts/find_complexity.py
```

#### Dependency / Security Quick Check

Checks for unpinned dependencies, missing lockfiles, and hardcoded secrets/credentials.

```bash
python3 <skill-path>/scripts/check_security.py
```

#### Documentation vs Code Consistency

Check if README.md, CLAUDE.md, and other docs actually match reality. This catches the silent rot where code evolves but docs don't — or docs describe an ideal that was never implemented.

```bash
python3 <skill-path>/scripts/check_docs.py
```

### Step 3: Manual Review

After the automated scans, read the actual source files — especially the ones flagged by the scans. Focus on:

#### Documentation Truthfulness
- Does the README describe the project as it actually is, or as someone wished it was 6 months ago?
- Does CLAUDE.md (if present) accurately reflect the project structure, conventions, and commands? Claude Code trusts this file — lies here cause compounding errors.
- Are install/setup instructions actually runnable? (Missing steps, wrong commands, outdated deps)
- Do documented API endpoints match actual route files?
- Are env vars documented that no longer exist, or used in code but missing from docs?
- Is the described architecture still accurate or has it drifted?

#### Architecture & Structure
- Is there a clear separation of concerns or is business logic tangled with presentation/infrastructure?
- Are there circular dependencies?
- Is the project structure predictable — could a new dev find things without a guide?
- Are there god files/classes that do too many things?

#### Error Handling
- Are errors caught and handled meaningfully, or swallowed?
- Is there consistent error handling (do some endpoints return errors differently than others)?
- Are there missing error cases (what happens when the DB is down, the API times out, the file doesn't exist)?

#### Data & State
- Is mutable state well-contained or scattered?
- Are there race conditions in concurrent code?
- Is input validated at trust boundaries (API endpoints, form handlers)?
- SQL injection, XSS, or other injection risks?

#### Naming & Readability
- Can you understand what a function does from its name?
- Are there misleading names (function called `getUser` that also modifies state)?
- Are abbreviations consistent (is it `req`/`res` everywhere or `request`/`response` in some places)?

#### Framework-Specific Patterns
Check for anti-patterns specific to the detected framework:

**Vue/Nuxt**: Mutating props, missing keys on v-for, reactive state in wrong scope, giant components
**React/Next**: Stale closures, missing deps in useEffect, prop drilling instead of context, unnecessary re-renders
**Express/Fastify**: Missing async error handling, middleware order issues, missing input validation
**Django/Flask**: N+1 queries, raw SQL without parameterization, missing CSRF protection
**Go**: Unchecked errors, goroutine leaks, missing context propagation

### Step 4: Write the Report

Structure the report by severity, not by file. Group related issues together.

#### Report Format

```markdown
# Code Review: [project name]

## Summary
[2-3 sentences: overall health, biggest concern, one positive thing]

## Critical Issues
[Bugs, security vulnerabilities, data loss risks. Things that need fixing NOW.]

## Architecture Concerns
[Structural problems that will get worse over time. Refactoring candidates.]

## Documentation Drift
[Mismatches between README/CLAUDE.md and actual code. Dead instructions, phantom files, outdated setup steps. This section matters because wrong docs are worse than no docs — they actively mislead.]

## Code Quality
[Duplicates, inconsistencies, bad patterns. Cleanup work.]

## Minor Issues
[Style nits, small improvements. Nice-to-have.]

## What's Good
[Seriously — call out things that are done well. Reviews that are all negative are demoralizing and usually wrong.]
```

#### Rules for Writing Findings

- **Always include the file path and line number.** `server/api/users.ts:45` not "in the users API"
- **Explain why it matters.** "This will crash in production when..." not just "this is wrong"
- **Show a fix when possible.** A 3-line code snippet is worth more than a paragraph of explanation
- **Group related issues.** If the same pattern appears in 5 files, say it once and list the locations — don't write it 5 times
- **Be honest about severity.** Not everything is critical. If something is a mild preference, say so.
- **Avoid false authority.** If you're not sure something is actually a problem, say "this might be an issue" rather than stating it as fact

### Step 5: Present Results

Save the report as a markdown file and present it to the user. If a CODE_REVIEW.md already exists, create a new one with todays date in the name. If the user asked about a specific concern (e.g., "find duplicates"), lead with that section.

After presenting, offer to:
1. Deep-dive into any specific issue
2. Generate fix suggestions for the critical issues
3. Create a prioritized refactoring plan
4. Review specific files in more detail

## Edge Cases

- **Monorepo**: Ask which package/app to review, or review the one the user is most likely working in based on context
- **Very large codebase (500+ files)**: Focus on the most important directories (src/, app/, server/) and sample rather than scanning everything
- **Generated code**: Skip files that are clearly auto-generated (migrations, lockfiles, compiled output, .d.ts files)
- **No clear entry point**: Start with the most-imported files — they're the backbone of the project
