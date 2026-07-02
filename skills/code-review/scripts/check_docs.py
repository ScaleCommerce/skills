#!/usr/bin/env python3
"""Check if README.md, CLAUDE.md, and other docs actually match the codebase reality."""
import os, re, json, sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import iter_source_files, read_text

root = sys.argv[1] if len(sys.argv) > 1 else '.'
issues = []

# Collect docs (dedupe by inode — case-insensitive filesystems would otherwise
# report README.md and readme.md as two separate docs)
docs = {}
_seen_doc_files = set()
for name in ['README.md', 'readme.md', 'CLAUDE.md', 'claude.md', 'CONTRIBUTING.md', 'docs/README.md']:
    path = os.path.join(root, name)
    if os.path.exists(path):
        try:
            st = os.stat(path)
            key = (st.st_dev, st.st_ino)
        except OSError:
            continue
        if key in _seen_doc_files:
            continue
        text = read_text(path)
        if text is not None:
            _seen_doc_files.add(key)
            docs[name] = text

# Also scan a top-level docs/ directory (cap at 10 files)
docs_dir = os.path.join(root, 'docs')
if os.path.isdir(docs_dir):
    try:
        md_files = sorted(f for f in os.listdir(docs_dir) if f.endswith('.md'))
    except OSError:
        md_files = []
    for fname in md_files[:10]:
        name = f'docs/{fname}'
        if name in docs:
            continue
        path = os.path.join(docs_dir, fname)
        try:
            st = os.stat(path)
            key = (st.st_dev, st.st_ino)
        except OSError:
            continue
        if key in _seen_doc_files:
            continue
        text = read_text(path)
        if text is not None:
            _seen_doc_files.add(key)
            docs[name] = text

if not docs:
    print("No README.md or CLAUDE.md found — nothing to cross-check.")
    sys.exit(0)

# Gather project facts
# 1. Actual scripts/commands from package.json
pkg_scripts = {}
pkg_deps = {}
pkg_path = os.path.join(root, 'package.json')
if os.path.exists(pkg_path):
    try:
        with open(pkg_path) as f:
            pkg = json.load(f)
        pkg_scripts = pkg.get('scripts', {})
        pkg_deps = {**pkg.get('dependencies', {}), **pkg.get('devDependencies', {})}
    except (OSError, json.JSONDecodeError):
        pass

# 2. Actual files and directories that exist (git-aware via common.py)
existing_paths = set()
for fpath in iter_source_files(root):
    rel = os.path.relpath(fpath, root)
    existing_paths.add(rel)
    parent = os.path.dirname(rel)
    while parent:
        existing_paths.add(parent)
        parent = os.path.dirname(parent)

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
for fpath in iter_source_files(root, ('.ts', '.js', '.vue', '.py', '.go', '.env.example')):
    content = read_text(fpath)
    if content is None:
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
    # Code blocks introduced with "create"/"add"/"example" etc. describe files
    # the reader is meant to create — their paths are illustrative, not claims.
    illustrative_intro = re.compile(r'\b(create|add|generate|example|scaffold|template|new file)\w*\b', re.I)
    code_blocks = []  # (start, end, is_illustrative)
    for cb in re.finditer(r'```.*?```', content, re.S):
        intro = content[max(0, cb.start() - 300):cb.start()]
        code_blocks.append((cb.start(), cb.end(), bool(illustrative_intro.search(intro))))

    placeholder_markers = ('http', 'example', '*', '{', '}', '<', '>', 'your-', 'my-', 'foo', 'placeholder')
    seen_paths = set()
    path_pattern = r'(?:`|"|\'|\s)((?:\./)?(?:[a-zA-Z0-9_-]+/)+[a-zA-Z0-9_.-]+\.[a-zA-Z]{1,5})(?:`|"|\'|\s|$)'
    for m in re.finditer(path_pattern, content):
        mentioned_path = m.group(1).lstrip('./')
        # Skip URLs, placeholders, and glob patterns
        if any(x in mentioned_path.lower() for x in placeholder_markers):
            continue
        if mentioned_path in seen_paths:
            continue
        # Skip paths inside code blocks that were introduced as illustrative
        if any(s <= m.start(1) < e and ill for s, e, ill in code_blocks):
            continue
        if mentioned_path in existing_paths or os.path.exists(os.path.join(root, mentioned_path)):
            continue
        # Only flag when the parent directory actually exists — if the whole
        # tree is absent, the doc is almost certainly showing an example layout.
        parent = str(Path(mentioned_path).parent)
        if parent == '.' or not os.path.isdir(os.path.join(root, parent)):
            continue
        seen_paths.add(mentioned_path)
        doc_issues.append(f"References file '{mentioned_path}' — file not found (directory {parent}/ exists)")

    # Check: tech stack / dependency claims.
    # Exact package-name matching — substring matching ('pg' in name) would
    # match unrelated deps like 'pg-boss'... or worse, anything containing "pg".
    def has_dep(*names):
        wanted = set(names)
        return any(k.lower() in wanted for k in pkg_deps)

    tech_mentions = {
        'typescript': lambda: any(os.path.exists(os.path.join(root, f)) for f in ['tsconfig.json', 'tsconfig.app.json']),
        'tailwind': lambda: 'tailwindcss' in pkg_deps or os.path.exists(os.path.join(root, 'tailwind.config.js')) or os.path.exists(os.path.join(root, 'tailwind.config.ts')),
        'prisma': lambda: 'prisma' in pkg_deps or '@prisma/client' in pkg_deps,
        'drizzle': lambda: 'drizzle-orm' in pkg_deps,
        'docker': lambda: os.path.exists(os.path.join(root, 'Dockerfile')) or os.path.exists(os.path.join(root, 'docker-compose.yml')) or os.path.exists(os.path.join(root, 'docker-compose.yaml')),
        'redis': lambda: has_dep('redis', 'ioredis', '@upstash/redis', 'redis-om', 'connect-redis') or any('redis' in p for p in existing_paths),
        'postgres': lambda: has_dep('pg', 'postgres', 'postgresql', 'pg-promise', 'pg-native', 'slonik', '@vercel/postgres', '@neondatabase/serverless', 'psycopg2', 'psycopg2-binary', 'psycopg', 'asyncpg'),
        'mongodb': lambda: has_dep('mongodb', 'mongoose', '@nestjs/mongoose', 'pymongo', 'motor'),
        'sqlite': lambda: has_dep('sqlite', 'sqlite3', 'better-sqlite3', '@libsql/client', 'aiosqlite'),
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
             'URI', 'GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'NOTE', 'TODO', 'FIXME',
             'WARNING', 'IMPORTANT', 'ERROR', 'INFO', 'DEBUG', 'MIT', 'NPM', 'CLI', 'SDK',
             'IDE', 'REST', 'CRUD', 'JSON', 'HTML', 'CSS', 'XML', 'YAML', 'YML', 'TOML',
             'SQL', 'HTTP', 'HTTPS', 'README', 'LICENSE', 'CHANGELOG', 'FAQ', 'USAGE',
             'GITHUB', 'TRUE', 'FALSE', 'NULL', 'NONE'}
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
            print(f"  [WARN] {issue}")
    else:
        print(f"  [OK] No inconsistencies found between {doc_name} and code")

    issues.extend(doc_issues)

if not issues:
    print("\n[OK] Docs and code appear to be in sync.")
else:
    print(f"\n{len(issues)} documentation inconsistencies found.")
