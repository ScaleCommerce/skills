#!/usr/bin/env python3
"""Check for known risky patterns: unpinned deps, missing lockfiles, hardcoded secrets."""
import os, re, json, sys

root = sys.argv[1] if len(sys.argv) > 1 else '.'
issues = []

# Check package.json for problems
pkg_path = os.path.join(root, 'package.json')
if os.path.exists(pkg_path):
    with open(pkg_path) as f:
        pkg = json.load(f)

    deps = {**pkg.get('dependencies', {}), **pkg.get('devDependencies', {})}

    # Wildcard versions
    for name, ver in deps.items():
        if ver == '*' or ver == 'latest':
            issues.append(f"Unpinned dependency: {name}@{ver} — use a fixed version")

    # Missing lock file
    has_lock = (os.path.exists(os.path.join(root, 'package-lock.json'))
                or os.path.exists(os.path.join(root, 'yarn.lock'))
                or os.path.exists(os.path.join(root, 'pnpm-lock.yaml')))
    if not has_lock:
        issues.append("No lockfile found (package-lock.json / yarn.lock / pnpm-lock.yaml)")

# Check for hardcoded secrets/credentials
secret_patterns = [
    (r'(?:password|passwd|pwd)\s*[=:]\s*["\'][^"\']{4,}["\']', 'Possible hardcoded password'),
    (r'(?:api[_-]?key|apikey)\s*[=:]\s*["\'][^"\']{8,}["\']', 'Possible hardcoded API key'),
    (r'(?:secret|token)\s*[=:]\s*["\'][A-Za-z0-9+/=_-]{16,}["\']', 'Possible hardcoded secret/token'),
    (r'-----BEGIN (?:RSA |EC )?PRIVATE KEY-----', 'Private key in source code'),
]

for dirpath, _, filenames in os.walk(root):
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
