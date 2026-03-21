#!/usr/bin/env python3
"""Check if README.md, CLAUDE.md, and other docs actually match the codebase reality."""
import os, re, json, sys
from pathlib import Path

root = sys.argv[1] if len(sys.argv) > 1 else '.'
issues = []

# Collect docs
docs = {}
for name in ['README.md', 'readme.md', 'CLAUDE.md', 'claude.md', 'CONTRIBUTING.md', 'docs/README.md']:
    path = os.path.join(root, name)
    if os.path.exists(path):
        with open(path, 'r', errors='ignore') as f:
            docs[name] = f.read()

if not docs:
    print("No README.md or CLAUDE.md found — nothing to cross-check.")
    sys.exit(0)

# Gather project facts
# 1. Actual scripts/commands from package.json
pkg_scripts = {}
pkg_deps = {}
pkg_path = os.path.join(root, 'package.json')
if os.path.exists(pkg_path):
    with open(pkg_path) as f:
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
        'typescript': lambda: any(os.path.exists(os.path.join(root, f)) for f in ['tsconfig.json', 'tsconfig.app.json']),
        'tailwind': lambda: 'tailwindcss' in pkg_deps or os.path.exists(os.path.join(root, 'tailwind.config.js')) or os.path.exists(os.path.join(root, 'tailwind.config.ts')),
        'prisma': lambda: 'prisma' in pkg_deps or '@prisma/client' in pkg_deps,
        'drizzle': lambda: 'drizzle-orm' in pkg_deps,
        'docker': lambda: os.path.exists(os.path.join(root, 'Dockerfile')) or os.path.exists(os.path.join(root, 'docker-compose.yml')) or os.path.exists(os.path.join(root, 'docker-compose.yaml')),
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
