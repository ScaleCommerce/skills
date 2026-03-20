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

```bash
# Find exact duplicate blocks (5+ lines)
# This uses a simple but effective hash-based approach
python3 << 'PYEOF'
import hashlib, os, sys
from collections import defaultdict

def find_dupes(root, extensions, min_lines=5):
    """Find duplicate code blocks across files."""
    blocks = defaultdict(list)
    
    for dirpath, _, filenames in os.walk(root):
        # Skip common non-source dirs
        skip = ['node_modules', '.git', 'vendor', 'dist', '.nuxt', '.next', 
                '__pycache__', '.venv', 'build', 'coverage', '.output']
        if any(s in dirpath for s in skip):
            continue
        for fname in filenames:
            if not any(fname.endswith(ext) for ext in extensions):
                continue
            fpath = os.path.join(dirpath, fname)
            try:
                with open(fpath, 'r', errors='ignore') as f:
                    lines = f.readlines()
            except:
                continue
            # Sliding window of min_lines
            for i in range(len(lines) - min_lines + 1):
                block = lines[i:i + min_lines]
                # Normalize: strip whitespace for comparison
                normalized = ''.join(l.strip() for l in block if l.strip())
                if len(normalized) < 40:  # Skip trivial blocks
                    continue
                h = hashlib.md5(normalized.encode()).hexdigest()
                blocks[h].append((fpath, i + 1, ''.join(block).strip()[:200]))
    
    dupes = {k: v for k, v in blocks.items() if len(v) > 1}
    if not dupes:
        print("No significant duplicate blocks found.")
        return
    
    # Sort by number of occurrences
    for h, locations in sorted(dupes.items(), key=lambda x: -len(x[1]))[:15]:
        print(f"\n--- Duplicate block ({len(locations)} occurrences) ---")
        for fpath, line, preview in locations:
            print(f"  {fpath}:{line}")
        print(f"  Preview: {locations[0][2][:150]}...")

# Detect extensions from project
exts = []
for root, _, files in os.walk('.'):
    if any(s in root for s in ['node_modules', '.git', 'vendor']):
        continue
    for f in files:
        if f.endswith(('.ts', '.tsx', '.js', '.jsx', '.vue', '.svelte')):
            exts = ['.ts', '.tsx', '.js', '.jsx', '.vue', '.svelte']; break
        elif f.endswith(('.py',)):
            exts = ['.py']; break
        elif f.endswith(('.go',)):
            exts = ['.go']; break
        elif f.endswith(('.rs',)):
            exts = ['.rs']; break
        elif f.endswith(('.php',)):
            exts = ['.php']; break
    if exts:
        break

if not exts:
    exts = ['.ts', '.js', '.py', '.go', '.rs', '.php', '.rb', '.java']

find_dupes('.', exts)
PYEOF
```

#### Inconsistency Detection

```bash
# Naming convention inconsistencies
python3 << 'PYEOF'
import os, re
from collections import Counter

issues = []

for dirpath, _, filenames in os.walk('.'):
    skip = ['node_modules', '.git', 'vendor', 'dist', '__pycache__', '.venv', '.nuxt', '.next']
    if any(s in dirpath for s in skip):
        continue
    for fname in filenames:
        if not any(fname.endswith(e) for e in ['.ts', '.tsx', '.js', '.jsx', '.vue', '.py', '.go', '.php']):
            continue
        fpath = os.path.join(dirpath, fname)
        try:
            with open(fpath, 'r', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
        except:
            continue
        
        # Check: mixed import styles (JS/TS)
        if fname.endswith(('.ts', '.tsx', '.js', '.jsx')):
            has_require = bool(re.search(r'\brequire\s*\(', content))
            has_import = bool(re.search(r'^import\s', content, re.MULTILINE))
            if has_require and has_import:
                issues.append(f"Mixed require/import: {fpath}")
        
        # Check: inconsistent string quotes (JS/TS)
        if fname.endswith(('.ts', '.tsx', '.js', '.jsx')):
            singles = len(re.findall(r"(?<!=)'[^']*'", content))
            doubles = len(re.findall(r'(?<!=)"[^"]*"', content))
            if singles > 5 and doubles > 5:
                ratio = min(singles, doubles) / max(singles, doubles)
                if ratio > 0.3:  # More than 30% mix
                    issues.append(f"Mixed quote styles ({singles} single, {doubles} double): {fpath}")

        # Check: console.log / print statements left in
        if fname.endswith(('.ts', '.tsx', '.js', '.jsx', '.vue')):
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped.startswith('console.log(') and not stripped.startswith('//'):
                    issues.append(f"console.log left in: {fpath}:{i+1}")
        if fname.endswith('.py'):
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped.startswith('print(') and not stripped.startswith('#'):
                    issues.append(f"print() left in: {fpath}:{i+1}")

        # Check: TODO/FIXME/HACK/XXX comments
        for i, line in enumerate(lines):
            if re.search(r'\b(TODO|FIXME|HACK|XXX)\b', line):
                issues.append(f"{re.search(r'(TODO|FIXME|HACK|XXX)', line).group()}: {fpath}:{i+1} — {line.strip()[:80]}")

        # Check: empty catch/except blocks
        if fname.endswith(('.ts', '.tsx', '.js', '.jsx')):
            for i, line in enumerate(lines):
                if re.search(r'catch\s*\([^)]*\)\s*\{\s*\}', content):
                    issues.append(f"Empty catch block: {fpath}")
                    break
        if fname.endswith('.py'):
            for i, line in enumerate(lines):
                if 'except' in line and i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if next_line == 'pass' or next_line == '...':
                        issues.append(f"Empty except/pass: {fpath}:{i+1}")

for issue in issues[:50]:
    print(issue)

if not issues:
    print("No major inconsistencies detected.")
else:
    print(f"\n({len(issues)} issues total)")
PYEOF
```

#### Large File / Complexity Check

```bash
# Find oversized files and functions
python3 << 'PYEOF'
import os, re

large_files = []
long_functions = []

for dirpath, _, filenames in os.walk('.'):
    skip = ['node_modules', '.git', 'vendor', 'dist', '__pycache__', '.venv', '.nuxt', '.next']
    if any(s in dirpath for s in skip):
        continue
    for fname in filenames:
        if not any(fname.endswith(e) for e in ['.ts', '.tsx', '.js', '.jsx', '.vue', '.py', '.go', '.php']):
            continue
        fpath = os.path.join(dirpath, fname)
        try:
            with open(fpath, 'r', errors='ignore') as f:
                lines = f.readlines()
        except:
            continue
        
        line_count = len(lines)
        if line_count > 300:
            large_files.append((fpath, line_count))
        
        # Detect long functions/methods
        func_start = None
        func_name = None
        depth = 0
        for i, line in enumerate(lines):
            # JS/TS function detection
            m = re.match(r'\s*(?:export\s+)?(?:async\s+)?(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=.*(?:=>|\bfunction\b))', line)
            if not m:
                m = re.match(r'\s*(?:async\s+)?(\w+)\s*\([^)]*\)\s*(?::\s*\w+)?\s*\{', line)
            if not m:
                # Python function detection
                m = re.match(r'\s*(?:async\s+)?def\s+(\w+)', line)
            
            if m:
                if func_start is not None and (i - func_start) > 50:
                    long_functions.append((fpath, func_name or "anonymous", func_start + 1, i - func_start))
                func_start = i
                func_name = m.group(1) or (m.group(2) if m.lastindex >= 2 else "anonymous")
        
        # Check last function
        if func_start is not None and (len(lines) - func_start) > 50:
            long_functions.append((fpath, func_name or "anonymous", func_start + 1, len(lines) - func_start))

if large_files:
    print("=== Large files (>300 lines) ===")
    for fpath, count in sorted(large_files, key=lambda x: -x[1]):
        print(f"  {count:>5} lines  {fpath}")

if long_functions:
    print("\n=== Long functions (>50 lines) ===")
    for fpath, name, start, length in sorted(long_functions, key=lambda x: -x[3])[:20]:
        print(f"  {length:>4} lines  {name}() at {fpath}:{start}")

if not large_files and not long_functions:
    print("No oversized files or functions found. Nice.")
PYEOF
```

#### Dependency / Security Quick Check

```bash
# Check for known risky patterns
python3 << 'PYEOF'
import os, re, json

issues = []

# Check package.json for problems
if os.path.exists('package.json'):
    with open('package.json') as f:
        pkg = json.load(f)
    
    deps = {**pkg.get('dependencies', {}), **pkg.get('devDependencies', {})}
    
    # Wildcard versions
    for name, ver in deps.items():
        if ver == '*' or ver == 'latest':
            issues.append(f"Unpinned dependency: {name}@{ver} — use a fixed version")
    
    # Missing lock file
    has_lock = os.path.exists('package-lock.json') or os.path.exists('yarn.lock') or os.path.exists('pnpm-lock.yaml')
    if not has_lock:
        issues.append("No lockfile found (package-lock.json / yarn.lock / pnpm-lock.yaml)")

# Check for hardcoded secrets/credentials
secret_patterns = [
    (r'(?:password|passwd|pwd)\s*[=:]\s*["\'][^"\']{4,}["\']', 'Possible hardcoded password'),
    (r'(?:api[_-]?key|apikey)\s*[=:]\s*["\'][^"\']{8,}["\']', 'Possible hardcoded API key'),
    (r'(?:secret|token)\s*[=:]\s*["\'][A-Za-z0-9+/=_-]{16,}["\']', 'Possible hardcoded secret/token'),
    (r'-----BEGIN (?:RSA |EC )?PRIVATE KEY-----', 'Private key in source code'),
]

for dirpath, _, filenames in os.walk('.'):
    skip = ['node_modules', '.git', 'vendor', 'dist', '__pycache__', '.venv']
    if any(s in dirpath for s in skip):
        continue
    for fname in filenames:
        if not any(fname.endswith(e) for e in ['.ts', '.js', '.py', '.go', '.php', '.env', '.yaml', '.yml', '.json', '.toml']):
            continue
        if fname.endswith('.lock') or fname.endswith('-lock.json') or fname == 'package-lock.json':
            continue
        fpath = os.path.join(dirpath, fname)
        try:
            with open(fpath, 'r', errors='ignore') as f:
                content = f.read()
        except:
            continue
        for pattern, label in secret_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for m in matches:
                line_num = content[:m.start()].count('\n') + 1
                # Skip common false positives
                if any(fp in m.group().lower() for fp in ['example', 'placeholder', 'your_', 'xxx', 'changeme', 'password123']):
                    continue
                issues.append(f"{label}: {fpath}:{line_num}")

for issue in issues[:30]:
    print(issue)

if not issues:
    print("No dependency or security issues detected.")
PYEOF
```

#### Documentation vs Code Consistency

Check if README.md, CLAUDE.md, and other docs actually match reality. This catches the silent rot where code evolves but docs don't — or docs describe an ideal that was never implemented.

```bash
python3 << 'PYEOF'
import os, re, json
from pathlib import Path

issues = []
root = '.'

# Collect docs
docs = {}
for name in ['README.md', 'readme.md', 'CLAUDE.md', 'claude.md', 'CONTRIBUTING.md', 'docs/README.md']:
    path = os.path.join(root, name)
    if os.path.exists(path):
        with open(path, 'r', errors='ignore') as f:
            docs[name] = f.read()

if not docs:
    print("No README.md or CLAUDE.md found — nothing to cross-check.")
    import sys; sys.exit(0)

# Gather project facts
# 1. Actual scripts/commands from package.json
pkg_scripts = {}
pkg_deps = {}
if os.path.exists('package.json'):
    with open('package.json') as f:
        try:
            pkg = json.load(f)
            pkg_scripts = pkg.get('scripts', {})
            pkg_deps = {**pkg.get('dependencies', {}), **pkg.get('devDependencies', {})}
        except:
            pass

# 2. Actual files and directories that exist
existing_paths = set()
for dirpath, dirnames, filenames in os.walk(root):
    skip = {'node_modules', '.git', 'vendor', 'dist', '__pycache__', '.venv', '.nuxt', '.next', '.output'}
    dirnames[:] = [d for d in dirnames if d not in skip]
    for fname in filenames:
        rel = os.path.relpath(os.path.join(dirpath, fname), root)
        existing_paths.add(rel)
    for dname in dirnames:
        rel = os.path.relpath(os.path.join(dirpath, dname), root)
        existing_paths.add(rel)

# 3. Actual API routes (Nuxt/Next/Express patterns)
actual_routes = set()
for p in existing_paths:
    # Nuxt server routes
    m = re.match(r'server/(?:api|routes)/(.+)\.(get|post|put|delete|patch)\.[tj]s', p)
    if m:
        route = m.group(1).replace('[', ':').replace(']', '')
        actual_routes.add(f"{m.group(2).upper()} /api/{route}")
    # Next.js API routes
    m = re.match(r'(?:app|pages)/api/(.+)/route\.[tj]s', p)
    if m:
        actual_routes.add(f"/api/{m.group(1)}")

# 4. Actual env vars used in code
used_env_vars = set()
for dirpath, dirnames, filenames in os.walk(root):
    skip = {'node_modules', '.git', 'vendor', 'dist', '__pycache__', '.venv'}
    dirnames[:] = [d for d in dirnames if d not in skip]
    for fname in filenames:
        if not any(fname.endswith(e) for e in ['.ts', '.js', '.vue', '.py', '.go', '.env.example']):
            continue
        fpath = os.path.join(dirpath, fname)
        try:
            with open(fpath, 'r', errors='ignore') as f:
                content = f.read()
        except:
            continue
        # process.env.X, os.environ['X'], os.Getenv("X")
        used_env_vars.update(re.findall(r'process\.env\.([A-Z_][A-Z0-9_]*)', content))
        used_env_vars.update(re.findall(r'os\.environ(?:\.get)?\s*\[\s*["\']([A-Z_][A-Z0-9_]*)', content))
        used_env_vars.update(re.findall(r'os\.Getenv\s*\(\s*["\']([A-Z_][A-Z0-9_]*)', content))

# Now cross-check each doc
for doc_name, content in docs.items():
    print(f"\n--- Checking {doc_name} ---")
    doc_issues = []

    # Check: npm/yarn/pnpm commands mentioned that don't exist in scripts
    if pkg_scripts:
        for m in re.finditer(r'(?:npm run|yarn|pnpm(?:\s+run)?)\s+([a-zA-Z0-9:_-]+)', content):
            script = m.group(1)
            if script not in pkg_scripts and script not in ('install', 'init', 'start', 'test', 'build', 'dev', 'ci', 'npx'):
                doc_issues.append(f"References script '{script}' but package.json has no such script. Available: {', '.join(pkg_scripts.keys()) or 'none'}")

    # Check: file paths mentioned that don't exist
    # Match paths like src/foo/bar.ts, ./config/something.yml, server/api/users.ts
    path_pattern = r'(?:`|"|\'|\s)((?:\./)?(?:[a-zA-Z0-9_-]+/)+[a-zA-Z0-9_.-]+\.[a-zA-Z]{1,5})(?:`|"|\'|\s|$)'
    for m in re.finditer(path_pattern, content):
        mentioned_path = m.group(1).lstrip('./')
        # Skip URLs, common examples, and glob patterns
        if any(x in mentioned_path for x in ['http', 'example', '*', '{', 'your-', 'my-']):
            continue
        if mentioned_path not in existing_paths:
            # Check if directory part exists at least
            parent = str(Path(mentioned_path).parent)
            if parent != '.' and parent not in existing_paths:
                doc_issues.append(f"References path '{mentioned_path}' — neither file nor directory exists")
            elif mentioned_path.count('/') > 0:  # Only flag specific paths, not ambiguous ones
                doc_issues.append(f"References file '{mentioned_path}' — file not found")

    # Check: tech stack / dependency claims
    tech_mentions = {
        'typescript': lambda: any(os.path.exists(f) for f in ['tsconfig.json', 'tsconfig.app.json']),
        'tailwind': lambda: 'tailwindcss' in pkg_deps or os.path.exists('tailwind.config.js') or os.path.exists('tailwind.config.ts'),
        'prisma': lambda: 'prisma' in pkg_deps or '@prisma/client' in pkg_deps,
        'drizzle': lambda: 'drizzle-orm' in pkg_deps,
        'docker': lambda: os.path.exists('Dockerfile') or os.path.exists('docker-compose.yml') or os.path.exists('docker-compose.yaml'),
        'redis': lambda: any(k for k in pkg_deps if 'redis' in k.lower()) or any('redis' in p for p in existing_paths),
        'postgres': lambda: any(k for k in pkg_deps if 'pg' in k.lower() or 'postgres' in k.lower()),
        'mongodb': lambda: any(k for k in pkg_deps if 'mongo' in k.lower()),
        'sqlite': lambda: any(k for k in pkg_deps if 'sqlite' in k.lower() or 'better-sqlite' in k.lower()),
    }
    content_lower = content.lower()
    for tech, check_fn in tech_mentions.items():
        # Only flag if doc says "we use X" / "built with X" / "requires X" style language
        usage_patterns = [
            rf'(?:uses?|built with|requires?|powered by|running)\s+{tech}',
            rf'{tech}\s+(?:is |for )',
        ]
        mentioned = any(re.search(p, content_lower) for p in usage_patterns)
        if not mentioned:
            # Also check if it appears in a tech stack list / badges
            mentioned = bool(re.search(rf'[-*]\s*.*{tech}', content_lower))
        if mentioned and not check_fn():
            doc_issues.append(f"Mentions {tech} but no corresponding dependency or config file found")

    # Check: env vars documented but not used (or used but not documented)
    doc_env_vars = set(re.findall(r'[`"\']?([A-Z][A-Z0-9_]{2,})[`"\']?\s*[-=:]', content))
    # Filter out common words that look like env vars
    noise = {'THE', 'AND', 'FOR', 'NOT', 'YOU', 'ALL', 'THIS', 'WITH', 'FROM', 'API', 'URL', 
             'GET', 'POST', 'PUT', 'DELETE', 'NOTE', 'TODO', 'MIT', 'NPM', 'CLI'}
    doc_env_vars -= noise
    
    if doc_env_vars and used_env_vars:
        documented_not_used = doc_env_vars - used_env_vars
        used_not_documented = used_env_vars - doc_env_vars
        # Only flag env-var-looking names (at least one underscore or common prefix)
        documented_not_used = {v for v in documented_not_used if '_' in v or v.startswith(('NUXT_', 'NEXT_', 'VITE_', 'DATABASE_', 'AUTH_'))}
        used_not_documented = {v for v in used_not_documented if '_' in v}
        for var in list(documented_not_used)[:5]:
            doc_issues.append(f"Documents env var {var} but it's not referenced in code")
        for var in list(used_not_documented)[:5]:
            doc_issues.append(f"Code uses env var {var} but it's not documented in {doc_name}")

    if doc_issues:
        for issue in doc_issues:
            print(f"  ⚠ {issue}")
    else:
        print(f"  ✓ No inconsistencies found between {doc_name} and code")

    issues.extend(doc_issues)

if not issues:
    print("\nDocs and code appear to be in sync. ✓")
else:
    print(f"\n{len(issues)} documentation inconsistencies found.")
PYEOF
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
