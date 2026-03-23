---
name: code-review
description: "Analyze codebases for quality issues, security vulnerabilities, duplicate code, inconsistencies, and bad patterns. Use this skill whenever the user asks to review code quality, find code smells, detect duplicates, check for anti-patterns, audit a codebase, clean up code, find inconsistencies, run a security audit, check for vulnerabilities, or do any kind of static analysis or code health check. Also trigger when the user says things like 'review my code', 'find problems in my codebase', 'what should I refactor', 'is this code any good', 'check for bad patterns', 'find duplicate code', 'code audit', 'tech debt review', 'security review', 'check for vulnerabilities', 'is this code secure', or 'find security issues'. This skill should be used even for casual requests like 'take a look at my project and tell me what's wrong' or 'anything I should fix in here'. Works across all languages and frameworks."
---

# Code Review Skill

Perform a thorough, opinionated code review of a project or set of files. The goal is to find real problems that matter — not nitpick formatting or chase theoretical issues. Think like a senior dev doing a PR review of an entire codebase, with a security engineer looking over your shoulder.

## Philosophy

**Be useful, not exhaustive.** A review that lists 200 minor issues is worse than one that identifies the 10 things that actually matter. Prioritize by impact: bugs > security > architecture > maintainability > style.

**Be specific, not vague.** "This code could be better" helps nobody. "The retry logic in `api/client.ts:34` swallows errors silently — failed requests disappear without logging or propagation" is actionable.

**Show, don't just tell.** When suggesting improvements, include a brief code example of what the fix looks like. Don't rewrite everything — just enough to communicate the pattern.

**Security is not optional.** Every code review includes a security pass. You don't need to be asked specifically — vulnerabilities found early cost 100x less than those found in production.

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
- Whether this is a public-facing service (affects security severity)

This context shapes the entire review. A Vue SFC has different rules than a Go microservice.

### Step 2: Choose Your Review Scope

First, determine what to review. Check for uncommitted or recent changes:

```bash
# Changed files (staged + unstaged + untracked)
git status --short

# If on a feature branch, files changed vs main
git diff --name-only main...HEAD 2>/dev/null
```

#### Changed files exist → Focus review on the diff

This is the default mode. When there are changed files (uncommitted work, or a feature branch with commits ahead of main), **read all of them.** This is how real PR reviews work — review what changed, not the entire codebase. Read each changed file fully, understand the intent of the changes, and review for quality and security in the context of the surrounding code.

If a changed file touches auth, validation, or data handling, also read the related files it interacts with (the caller, the route that uses this handler, the model it queries) to understand the full picture.

Still run `check_deps.py` if package/dependency files changed, and `check_docs.py` if docs or project structure changed.

#### No changes (clean repo) or user asks for full/deep scan → Full codebase review

Count the source files to decide your approach:

```bash
find . -type f \( -name '*.ts' -o -name '*.js' -o -name '*.py' -o -name '*.go' -o -name '*.vue' -o -name '*.svelte' -o -name '*.php' -o -name '*.rb' -o -name '*.java' -o -name '*.rs' \) -not -path '*/node_modules/*' -not -path '*/.git/*' -not -path '*/vendor/*' -not -path '*/dist/*' -not -path '*/__pycache__/*' -not -path '*/.venv/*' -not -path '*/.nuxt/*' -not -path '*/.next/*' | wc -l
```

**~100 source files or fewer → Read the code directly.** Skip the scripts. You can read and understand the actual source files, which gives far better results than regex pattern matching. Read the key files (entry points, route handlers, models, auth logic, config) and review them with full context. You'll catch everything the scripts would — and more — because you understand what the code actually does, not just what it looks like.

Still run `check_deps.py` and `check_docs.py` — these do mechanical cross-referencing (imports vs declared deps, docs vs reality) that is tedious to do manually even on small projects.

**100+ source files → Scripts + targeted reading.** The scripts become valuable when you physically can't read every file. They scan hundreds of files in seconds and surface candidates for you to investigate deeper.

But remember: the scripts are **signal generators, not reviewers.** They match regex patterns and heuristics — they will produce false positives (flagging harmless code) and, critically, **false negatives** (missing vulnerabilities they have no pattern for). A project using an unusual ORM, a custom auth framework, or domain-specific security surfaces will have gaps the scripts can't see.

Your job as the reviewer is to:
1. Run the scripts to cast a wide net across all files
2. **Read the flagged locations in context** — dismiss false positives, confirm real issues
3. **Go beyond the scripts** — use your understanding of the codebase, data flow, and business logic to find issues no regex could catch (auth bypass via business logic, IDOR, race conditions, semantic bugs)

Think of it this way: the scripts are a metal detector. You're the archaeologist who decides what's actually treasure.

#### Available Scripts (for large codebases)

**Duplicate / Similar Code Detection** — Find exact duplicate blocks (5+ lines) using a hash-based approach. Auto-detects project language.

```bash
python3 <skill-path>/scripts/find_dupes.py
```

#### Inconsistency Detection

Checks for mixed import styles, inconsistent quotes, leftover console.log/print, TODO/FIXME comments, and empty catch/except blocks.

```bash
python3 <skill-path>/scripts/find_inconsistencies.py
```

#### Complexity Analysis

Finds files over 300 lines, functions over 50 lines, and measures cyclomatic complexity (NIST threshold: 10), cognitive complexity (SonarQube threshold: 15), excessive parameters (>5), and deep nesting (>4 levels).

```bash
python3 <skill-path>/scripts/find_complexity.py
```

#### Security Scan

Comprehensive security analysis covering secrets detection (AWS/GCP/GitHub/Slack/Stripe keys, entropy-based detection), injection patterns (SQL/XSS/command/template injection, path traversal, prototype pollution), access control issues (CORS misconfiguration, missing CSRF, disabled TLS verification), weak cryptography, and information disclosure.

```bash
python3 <skill-path>/scripts/check_security_deep.py
```

#### Dependency Health

Multi-ecosystem dependency analysis: unused dependencies, lockfile integrity, unpinned versions, `npm audit`/`pip-audit` integration, GitHub Actions supply chain checks.

```bash
python3 <skill-path>/scripts/check_deps.py
```

#### Documentation vs Code Consistency

Check if README.md, CLAUDE.md, and other docs actually match reality. This catches the silent rot where code evolves but docs don't — or docs describe an ideal that was never implemented.

```bash
python3 <skill-path>/scripts/check_docs.py
```

### Step 3: Deep Security Review (Agent-Driven)

This is where you earn your keep. The scripts found pattern matches — now you read the actual code and think like an attacker. The most dangerous vulnerabilities are the ones no regex can catch: logic flaws, missing authorization checks on specific routes, race conditions between concurrent operations, or data flowing from user input through three function calls before hitting an unsafe sink.

For each area below, **read the relevant source files** and trace how data moves through the system. Don't just grep — follow the code paths.

#### Authentication & Authorization
- Are all endpoints that should require auth actually protected? Look for route handlers without auth middleware.
- Is authorization granular enough? (A user shouldn't be able to access another user's data just by changing an ID in the URL — this is IDOR, the #1 API vulnerability.)
- Are JWTs validated properly (signature, expiry, issuer)?
- Is session management secure (HttpOnly cookies, secure flag, reasonable expiry)?

#### Input Validation at Trust Boundaries
- Are API endpoints validating and sanitizing input? (Not just type-checking — length limits, allowed characters, range checks)
- Is file upload restricted by type, size, and stored outside the webroot?
- Are database queries parameterized everywhere, or did someone slip in a string concat?
- Is user input ever reflected back without encoding?

#### Data Protection
- Are sensitive fields (passwords, tokens, PII) excluded from API responses and logs?
- Is data encrypted at rest where required?
- Are error messages safe? (No stack traces, internal paths, or DB schema leaked to clients)
- Are rate limits in place for auth endpoints and expensive operations?

#### Supply Chain (OWASP 2025 #3)
- Are dependencies reasonably current? (Median dependency is 278 days behind — anything >1 year is a flag)
- Do lockfiles have integrity hashes?
- Are CI/CD actions pinned to SHA hashes, not mutable tags?

### Step 4: Deep Quality Review (Agent-Driven)

Read the actual source files — start with the ones flagged by the scans, but don't stop there. The scripts only know about patterns they were programmed to find. You understand code semantics: you can spot a function that claims to validate input but actually doesn't, a "cache" that grows forever, or an API that returns unbounded result sets. Focus on:

#### Documentation Truthfulness
- Does the README describe the project as it actually is, or as someone wished it was 6 months ago?
- Does CLAUDE.md (if present) accurately reflect the project structure, conventions, and commands? Claude Code trusts this file — lies here cause compounding errors.
- Are install/setup instructions actually runnable? (Missing steps, wrong commands, outdated deps)
- Do documented API endpoints match actual route files?
- Are env vars documented that no longer exist, or used in code but missing from docs?
- Is the described architecture still accurate or has it drifted?

#### Architecture & Structure
- Is there a clear separation of concerns or is business logic tangled with presentation/infrastructure?
- Are there circular dependencies? (check imports — if A imports B and B imports A, that's a design issue)
- Is the project structure predictable — could a new dev find things without a guide?
- Are there god files/classes that do too many things?
- Are there exported functions/components that nothing imports? (dead code at module boundaries)

#### Error Handling
- Are errors caught and handled meaningfully, or swallowed?
- Is there consistent error handling (do some endpoints return errors differently than others)?
- Are there missing error cases (what happens when the DB is down, the API times out, the file doesn't exist)?
- Do error paths clean up resources? (missing `finally` blocks, unclosed connections/streams/file handles)

#### Resource Management
- Are database connections, file handles, and network sockets properly closed?
- Are there potential memory leaks? (growing caches without eviction, event listener accumulation, unbounded arrays)
- Are expensive operations (DB queries, API calls) happening in loops when they could be batched?
- Is there pagination for endpoints that return lists? (unbounded queries are a production time bomb)

#### Logging & Observability
- Can you trace a request through the system? (correlation IDs, structured logging)
- Are error paths logged, or do failures happen silently?
- Is sensitive data being logged? (PII, tokens, passwords in log output)
- Are log levels used consistently? (errors logged as warnings, or worse, as info)

#### Data & State
- Is mutable state well-contained or scattered?
- Are there race conditions in concurrent code?
- Are database transactions used where multiple writes need to be atomic?

#### Naming & Readability
- Can you understand what a function does from its name?
- Are there misleading names (function called `getUser` that also modifies state)?
- Are abbreviations consistent (is it `req`/`res` everywhere or `request`/`response` in some places)?

#### Test Coverage Gaps
- Are there complex functions (high cyclomatic complexity from the scan) with no corresponding test file?
- Do existing tests only cover happy paths? (look for absence of error case tests, edge cases, boundary conditions)
- Are there integration tests for API endpoints, or only unit tests?
- Are tests actually testing behavior, or just asserting that mocks were called?

#### Framework-Specific Patterns
Check for anti-patterns specific to the detected framework:

**Vue/Nuxt**: Mutating props, missing keys on v-for, reactive state in wrong scope, giant components, watchers that could be computed
**React/Next**: Stale closures, missing deps in useEffect, prop drilling instead of context, unnecessary re-renders, missing error boundaries
**Express/Fastify**: Missing async error handling, middleware order issues, missing input validation, no rate limiting
**Django/Flask**: N+1 queries, raw SQL without parameterization, missing CSRF protection, debug mode in production settings
**Go**: Unchecked errors, goroutine leaks, missing context propagation, defer in loops

#### Beyond the Scripts: What Only You Can Find

The scripts can't detect these — but you can by reading the code with understanding:

- **Logic bugs**: A discount calculation that applies twice, a pagination offset that skips the first item, a permission check that uses OR where it should use AND
- **Semantic mismatches**: A function named `validateEmail` that only checks for `@` but not domain, a "delete" endpoint that soft-deletes but the "list" endpoint doesn't filter deleted records
- **Missing business logic**: An e-commerce checkout with no stock validation, a rate limiter that resets on server restart, a password reset flow with no expiry
- **Data flow vulnerabilities**: User input that passes through 3 clean-looking functions before reaching an unsafe sink — no single line looks dangerous, but the chain is
- **Implicit coupling**: Two modules that work because they both assume the same database state, but nothing enforces this — a change to one will silently break the other
- **Framework misuse specific to this project**: Not generic anti-patterns (those are above), but ways this particular codebase misuses its own abstractions

When you find something the scripts missed, that's the highest-value part of your review. Call it out clearly.

### Step 5: Write the Report

Structure the report by severity, not by file. Group related issues together.

#### Report Format

```markdown
# Code Review: [project name]

## Summary
[2-3 sentences: overall health, biggest concern, one positive thing]

## Critical Issues
[Bugs, security vulnerabilities, data loss risks. Things that need fixing NOW.]

## Security Findings
[Injection risks, auth gaps, secret exposure, supply chain issues. Grouped by OWASP category where applicable. Include severity (Critical/High/Medium) for each finding.]

## Architecture Concerns
[Structural problems that will get worse over time. Refactoring candidates.]

## Documentation Drift
[Mismatches between README/CLAUDE.md and actual code. Dead instructions, phantom files, outdated setup steps. This section matters because wrong docs are worse than no docs — they actively mislead.]

## Code Quality
[Duplicates, inconsistencies, complexity hotspots, bad patterns. Cleanup work.]

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
- **For security findings, include the attack scenario.** "An attacker could..." makes the risk concrete and helps the developer understand urgency

### Step 6: Present Results

Save the report as a markdown file and present it to the user. If a CODE_REVIEW.md already exists, create a new one with todays date in the name. If the user asked about a specific concern (e.g., "find duplicates"), lead with that section.

After presenting, offer to:
1. Deep-dive into any specific issue
2. Generate fix suggestions for the critical issues
3. Create a prioritized refactoring plan
4. Run a focused security audit on a specific area
5. Review specific files in more detail

## Edge Cases

- **Monorepo**: Ask which package/app to review, or review the one the user is most likely working in based on context
- **Very large codebase (500+ files)**: Focus on the most important directories (src/, app/, server/) and sample rather than scanning everything
- **Generated code**: Skip files that are clearly auto-generated (migrations, lockfiles, compiled output, .d.ts files)
- **No clear entry point**: Start with the most-imported files — they're the backbone of the project
- **Security-only review**: If the user specifically asks for a security audit, skip Steps 2's quality scans (dupes, inconsistencies) and focus entirely on Steps 2's security/deps scans + Step 3's manual security review. Use a streamlined report format focused on findings by OWASP category.
