#!/usr/bin/env python3
"""Shared file discovery for the code-review scripts.

Two goals:
1. Respect what the project itself considers source code. Inside a git repo we
   use `git ls-files` so .gitignore rules apply automatically (this is what
   keeps a properly-ignored local .env or build output from being scanned).
2. Never flood the caller. Minified bundles, sourcemaps, generated files and
   huge blobs produce noise, not review findings, so they are filtered here
   once instead of in every script.
"""
import os
import subprocess

# Exact directory names to prune when walking outside a git repo.
# Matched per path component, not by substring — a folder named
# "distribution" or "builder" must NOT be skipped.
SKIP_DIRS = {
    'node_modules', '.git', 'vendor', 'dist', 'build', 'out', 'coverage',
    '.nuxt', '.next', '.output', '.svelte-kit', '__pycache__', '.venv',
    'venv', '.tox', '.terraform', 'target', 'Pods', '.idea', '.vscode',
    'bower_components', '.cache',
}

# Generated / minified artifacts that waste scan time even when tracked in git.
SKIP_SUFFIXES = ('.min.js', '.min.css', '.map', '.lock', '.snap')
SKIP_BASENAMES = {'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml',
                  'composer.lock', 'Cargo.lock', 'poetry.lock', 'uv.lock',
                  'Gemfile.lock'}

MAX_FILE_BYTES = 1_000_000  # files larger than this are almost never hand-written


def _git_files(root):
    """Tracked + untracked-but-not-ignored files, or None if not a git repo."""
    try:
        result = subprocess.run(
            ['git', '-C', root, 'ls-files', '-z', '--cached', '--others',
             '--exclude-standard'],
            capture_output=True, timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return [os.path.join(root, p.decode('utf-8', 'replace'))
            for p in result.stdout.split(b'\0') if p]


def _walk_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fname in filenames:
            yield os.path.join(dirpath, fname)


def _wanted(path, extensions):
    base = os.path.basename(path)
    if base in SKIP_BASENAMES or base.endswith(SKIP_SUFFIXES):
        return False
    if '.generated.' in base or base.endswith('.d.ts'):
        return False
    if extensions is not None and not any(base.endswith(e) for e in extensions):
        return False
    # Even inside a git repo, prune vendored trees that projects sometimes commit.
    parts = path.split(os.sep)
    if any(p in SKIP_DIRS for p in parts):
        return False
    try:
        if os.path.getsize(path) > MAX_FILE_BYTES:
            return False
    except OSError:
        return False
    return True


def iter_source_files(root='.', extensions=None):
    """Yield project source file paths, honouring .gitignore when possible.

    extensions: iterable of suffixes ('.py', '.ts', ...) or None for all files.
    """
    files = _git_files(root)
    if files is None:
        files = _walk_files(root)
    for path in files:
        if os.path.isfile(path) and _wanted(path, extensions):
            yield path


def read_text(path):
    """Read a file as text, tolerating odd encodings. Returns None on failure."""
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except OSError:
        return None


def is_ignored_by_git(root, relpath):
    """True if git confirms the path is ignored (e.g. a local .env). False when
    unknown, so callers must treat False as 'not proven ignored'."""
    try:
        result = subprocess.run(
            ['git', '-C', root, 'check-ignore', '-q', relpath],
            capture_output=True, timeout=10,
        )
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False
