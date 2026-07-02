#!/usr/bin/env python3
"""
Dependency health analysis: unused deps, lockfile integrity, unpinned versions,
audit integration, supply chain checks. Multi-ecosystem (npm, pip, go, cargo, composer).
"""
import os
import re
import glob
import json
import sys
import subprocess
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import iter_source_files, read_text

root = sys.argv[1] if len(sys.argv) > 1 else "."
issues = []  # (severity, message)


def add(severity, msg):
    issues.append((severity, msg))


# ---------------------------------------------------------------------------
# 1. DETECT ECOSYSTEM
# ---------------------------------------------------------------------------

ecosystems = []
pkg_json_path = os.path.join(root, "package.json")
requirements_path = os.path.join(root, "requirements.txt")
pyproject_path = os.path.join(root, "pyproject.toml")
pipfile_path = os.path.join(root, "Pipfile")
go_mod_path = os.path.join(root, "go.mod")
cargo_toml_path = os.path.join(root, "Cargo.toml")
composer_json_path = os.path.join(root, "composer.json")
gemfile_path = os.path.join(root, "Gemfile")

if os.path.exists(pkg_json_path):
    ecosystems.append("npm")
if os.path.exists(requirements_path) or os.path.exists(pyproject_path) or os.path.exists(pipfile_path):
    ecosystems.append("python")
if os.path.exists(go_mod_path):
    ecosystems.append("go")
if os.path.exists(cargo_toml_path):
    ecosystems.append("rust")
if os.path.exists(composer_json_path):
    ecosystems.append("php")
if os.path.exists(gemfile_path):
    ecosystems.append("ruby")


# ---------------------------------------------------------------------------
# 2. NPM / NODE CHECKS
# ---------------------------------------------------------------------------

# Specs that reference git repos, local paths, workspace links or tarballs are
# intentionally pinned/local — flagging them as "unpinned" is a false positive.
LOCAL_SPEC_PREFIXES = ("git+", "git:", "github:", "file:", "link:", "portal:",
                       "workspace:", "http://", "https://")


def collect_unpinned(deps_map, label=""):
    for name, ver in deps_map.items():
        ver = (ver or "").strip()
        if ver.lower().startswith(LOCAL_SPEC_PREFIXES) or ver.endswith((".tgz", ".tar.gz")):
            continue
        if ver in ("*", "latest"):
            add("high", f"Unpinned dependency (wildcard){label}: {name}@{ver}")
        elif ver.startswith(">=") and "<" not in ver:
            add("high", f"Unpinned dependency (unbounded range){label}: {name}@{ver}")


def find_workspace_packages(pkg):
    """Return workspace package.json paths for npm/yarn/pnpm monorepos."""
    patterns = []
    ws = pkg.get("workspaces")
    if isinstance(ws, dict):
        ws = ws.get("packages", [])
    if isinstance(ws, list):
        patterns.extend(p for p in ws if isinstance(p, str))
    pnpm_ws = read_text(os.path.join(root, "pnpm-workspace.yaml"))
    if pnpm_ws:
        for m in re.finditer(r"^\s*-\s*['\"]?([^'\"\s#]+)", pnpm_ws, re.M):
            patterns.append(m.group(1))
    found = []
    seen = set()
    for pat in patterns:
        if pat.startswith("!"):
            continue
        for d in glob.glob(os.path.join(root, pat)):
            pj = os.path.join(d, "package.json")
            if os.path.isdir(d) and os.path.exists(pj) and pj not in seen and "node_modules" not in pj:
                seen.add(pj)
                found.append(pj)
    return found


def check_npm():
    try:
        with open(pkg_json_path) as f:
            pkg = json.load(f)
    except Exception:
        return

    deps = pkg.get("dependencies", {})
    dev_deps = pkg.get("devDependencies", {})
    all_deps = {**deps, **dev_deps}

    # --- Unpinned versions (root + workspace packages) ---
    collect_unpinned(all_deps)

    # --- Monorepo / workspaces: audit + unused-dep checks below only cover
    # the root package, so tell the agent coverage is partial ---
    ws_pkgs = find_workspace_packages(pkg)
    if ws_pkgs:
        add("info", f"Monorepo detected: {len(ws_pkgs)} workspace packages — npm audit and unused-dep checks cover the root package only")
        for pj in ws_pkgs[:30]:
            try:
                with open(pj) as f:
                    ws_pkg = json.load(f)
            except Exception:
                continue
            ws_deps = {**ws_pkg.get("dependencies", {}), **ws_pkg.get("devDependencies", {})}
            collect_unpinned(ws_deps, label=f" in {os.path.relpath(pj, root)}")

    # --- Missing lockfile ---
    lockfiles = ["package-lock.json", "yarn.lock", "pnpm-lock.yaml", "bun.lockb"]
    has_lock = any(os.path.exists(os.path.join(root, lf)) for lf in lockfiles)
    if not has_lock:
        add("high", "No lockfile found — installs are non-deterministic and vulnerable to supply chain attacks")

    # --- Unused dependencies ---
    # Collect all imports/requires across source files
    imported = set()
    for fpath in iter_source_files(root, (".ts", ".tsx", ".js", ".jsx", ".vue", ".svelte", ".mjs", ".cjs")):
        content = read_text(fpath)
        if content is None:
            continue
        # ES imports: import ... from 'pkg'
        for m in re.finditer(r"""(?:import|from)\s+['"]([@a-zA-Z][^'"]*?)['"]""", content):
            pkg_name = m.group(1).split("/")[0]
            if pkg_name.startswith("@"):
                pkg_name = "/".join(m.group(1).split("/")[:2])
            imported.add(pkg_name)
        # require('pkg')
        for m in re.finditer(r"""require\s*\(\s*['"]([@a-zA-Z][^'"]*?)['"]""", content):
            pkg_name = m.group(1).split("/")[0]
            if pkg_name.startswith("@"):
                pkg_name = "/".join(m.group(1).split("/")[:2])
            imported.add(pkg_name)

    # Also check config files that reference deps (nuxt.config, vite.config, etc.)
    for config_name in ["nuxt.config.ts", "nuxt.config.js", "vite.config.ts", "vite.config.js",
                         "next.config.js", "next.config.mjs", "postcss.config.js", "tailwind.config.js",
                         "tailwind.config.ts", ".eslintrc.js", ".eslintrc.cjs", "jest.config.js",
                         "vitest.config.ts", "tsconfig.json", "babel.config.js"]:
        config_path = os.path.join(root, config_name)
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", errors="ignore") as f:
                    content = f.read()
                # Extract any package references
                for m in re.finditer(r"""['"]([@a-zA-Z][\w./-]*?)['"]""", content):
                    pkg_name = m.group(1).split("/")[0]
                    if pkg_name.startswith("@"):
                        pkg_name = "/".join(m.group(1).split("/")[:2])
                    imported.add(pkg_name)
            except Exception:
                pass

    # Check package.json scripts for CLI tools
    scripts = pkg.get("scripts", {})
    scripts_text = " ".join(scripts.values())
    for dep_name in all_deps:
        base = dep_name.split("/")[-1]
        if base in scripts_text:
            imported.add(dep_name)

    # Some deps are used implicitly (types, plugins, presets)
    implicit_prefixes = ("@types/", "@babel/", "@typescript-eslint/", "eslint-plugin-", "eslint-config-",
                         "prettier-plugin-", "@nuxtjs/", "@vueuse/", "typescript", "postcss", "autoprefixer")

    unused_deps = []
    for dep_name in deps:
        if dep_name in imported:
            continue
        if any(dep_name.startswith(p) for p in implicit_prefixes):
            continue
        unused_deps.append(dep_name)

    if unused_deps:
        add("medium", f"Possibly unused production dependencies: {', '.join(unused_deps[:8])}")
        if len(unused_deps) > 8:
            add("medium", f"  ... and {len(unused_deps) - 8} more")

    # --- npm audit (if available) ---
    try:
        result = subprocess.run(
            ["npm", "audit", "--json", "--omit=dev"],
            capture_output=True, text=True, timeout=30, cwd=root
        )
        if result.returncode != 0 and result.stdout:
            try:
                audit = json.loads(result.stdout)
                vuln_count = audit.get("metadata", {}).get("vulnerabilities", {})
                critical = vuln_count.get("critical", 0)
                high = vuln_count.get("high", 0)
                if critical or high:
                    add("critical", f"npm audit: {critical} critical, {high} high vulnerabilities — run `npm audit` for details")
                elif vuln_count.get("moderate", 0):
                    add("medium", f"npm audit: {vuln_count['moderate']} moderate vulnerabilities")
            except json.JSONDecodeError:
                pass
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # --- Postinstall scripts in dependencies (supply chain risk) ---
    node_modules = os.path.join(root, "node_modules")
    if os.path.isdir(node_modules):
        suspicious_scripts = []
        for dep_name in list(deps.keys())[:50]:  # Check production deps only, cap at 50
            dep_pkg = os.path.join(node_modules, dep_name, "package.json")
            if not os.path.exists(dep_pkg):
                continue
            try:
                with open(dep_pkg) as f:
                    dep_data = json.load(f)
                dep_scripts = dep_data.get("scripts", {})
                if any(s in dep_scripts for s in ("postinstall", "preinstall", "install")):
                    suspicious_scripts.append(dep_name)
            except Exception:
                continue
        if suspicious_scripts:
            add("medium", f"Dependencies with install scripts (supply chain surface): {', '.join(suspicious_scripts[:5])}")


# ---------------------------------------------------------------------------
# 3. PYTHON CHECKS
# ---------------------------------------------------------------------------

def check_python():
    # --- Lockfile ---
    has_lock = any(os.path.exists(os.path.join(root, f)) for f in [
        "poetry.lock", "Pipfile.lock", "requirements.lock", "pdm.lock", "uv.lock"
    ])
    if not has_lock and os.path.exists(requirements_path):
        # Check if requirements.txt has pinned versions
        try:
            with open(requirements_path) as f:
                lines = [l.strip() for l in f if l.strip() and not l.startswith("#") and not l.startswith("-")]
            # git+/file:/-e/URL/"pkg @ url" specs are intentionally pinned or local
            unpinned = [l for l in lines
                        if "==" not in l and " @ " not in l
                        and not l.startswith(("git+", "file:", "http://", "https://", "-e", "./", "../"))]
            if unpinned:
                add("high", f"No Python lockfile and {len(unpinned)} unpinned deps in requirements.txt: {', '.join(unpinned[:5])}")
        except Exception:
            pass
    elif not has_lock and os.path.exists(pyproject_path):
        add("medium", "No Python lockfile (poetry.lock, pdm.lock, etc.) — consider pinning dependencies")

    # --- pip audit (if available) ---
    # Only ever audit an explicit project manifest. Running bare `pip-audit`
    # would audit the agent's own Python environment, not the project.
    if not os.path.exists(requirements_path):
        if os.path.exists(pyproject_path) and "dependencies" in (read_text(pyproject_path) or ""):
            add("info", "pip-audit skipped: no requirements.txt (pyproject.toml deps present — audit manually with `pip-audit .`)")
        else:
            add("info", "pip-audit skipped: no auditable Python manifest (requirements.txt) found")
        return

    try:
        result = subprocess.run(
            ["pip-audit", "--format=json", "-r", requirements_path],
            capture_output=True, text=True, timeout=60, cwd=root
        )
        if result.stdout:
            try:
                vulns = json.loads(result.stdout)
                if isinstance(vulns, dict):  # newer pip-audit wraps results
                    vulns = [d for d in vulns.get("dependencies", []) if d.get("vulns")]
                if isinstance(vulns, list) and vulns:
                    fixable = [v for v in vulns
                               if v.get("fix_versions") or any(x.get("fix_versions") for x in v.get("vulns", []))]
                    add("high", f"pip-audit: {len(vulns)} vulnerable packages ({len(fixable)} fixable) — run `pip-audit -r requirements.txt` for details")
            except json.JSONDecodeError:
                pass
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass


# ---------------------------------------------------------------------------
# 4. GO CHECKS
# ---------------------------------------------------------------------------

def check_go():
    if not os.path.exists(go_mod_path):
        return
    # Check for go.sum
    if not os.path.exists(os.path.join(root, "go.sum")):
        add("high", "No go.sum file — dependency checksums not verified")

    # govulncheck (if available)
    try:
        result = subprocess.run(
            ["govulncheck", "-json", "./..."],
            capture_output=True, text=True, timeout=60, cwd=root
        )
        if "Vulnerability" in (result.stdout or ""):
            add("high", "govulncheck found vulnerabilities — run `govulncheck ./...` for details")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass


# ---------------------------------------------------------------------------
# 5. RUST / PHP / RUBY CHECKS
# ---------------------------------------------------------------------------

def check_rust():
    if not os.path.exists(os.path.join(root, "Cargo.lock")):
        add("high", "No Cargo.lock — builds are non-deterministic (commit the lockfile)")
    try:
        result = subprocess.run(
            ["cargo", "audit", "--json"],
            capture_output=True, text=True, timeout=60, cwd=root
        )
        if result.stdout:
            try:
                report = json.loads(result.stdout)
                count = report.get("vulnerabilities", {}).get("count", 0)
                if count:
                    add("critical", f"cargo audit: {count} vulnerable crates — run `cargo audit` for details")
            except json.JSONDecodeError:
                pass
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass


def check_php():
    if not os.path.exists(os.path.join(root, "composer.lock")):
        add("high", "No composer.lock — installs are non-deterministic (commit the lockfile)")
        return
    try:
        result = subprocess.run(
            ["composer", "audit", "--format=json", "--no-interaction"],
            capture_output=True, text=True, timeout=60, cwd=root
        )
        if result.stdout:
            try:
                report = json.loads(result.stdout)
                advisories = report.get("advisories") or {}
                if advisories:
                    add("critical", f"composer audit: {len(advisories)} packages with security advisories — run `composer audit` for details")
            except json.JSONDecodeError:
                pass
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass


def check_ruby():
    if not os.path.exists(os.path.join(root, "Gemfile.lock")):
        add("high", "No Gemfile.lock — installs are non-deterministic (commit the lockfile)")
        return
    try:
        result = subprocess.run(
            ["bundle", "audit", "check"],
            capture_output=True, text=True, timeout=60, cwd=root
        )
        out = (result.stdout or "") + (result.stderr or "")
        if result.returncode != 0 and "Vulnerabilities found" in out:
            count = len(re.findall(r"^Name:", out, re.M))
            add("critical", f"bundle audit: {count or 'multiple'} vulnerable gems — run `bundle audit` for details")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass


# ---------------------------------------------------------------------------
# 6. GITHUB ACTIONS / CI SUPPLY CHAIN
# ---------------------------------------------------------------------------

def check_ci_supply_chain():
    """Check for unpinned GitHub Actions (should use SHA hashes, not tags)."""
    workflows_dir = os.path.join(root, ".github", "workflows")
    if not os.path.isdir(workflows_dir):
        return

    first_party_files = set()   # workflows pinning official actions by tag (low risk)
    third_party = []            # (relpath, line, action@ref) — real supply chain surface
    for fname in os.listdir(workflows_dir):
        if not fname.endswith((".yml", ".yaml")):
            continue
        fpath = os.path.join(workflows_dir, fname)
        try:
            with open(fpath, "r", errors="ignore") as f:
                lines = f.read().splitlines()
        except Exception:
            continue
        relpath = f".github/workflows/{fname}"
        for lineno, line in enumerate(lines, 1):
            # Find uses: owner/repo@ref where ref is not a full SHA
            for m in re.finditer(r"uses:\s*([a-zA-Z0-9_-]+/[a-zA-Z0-9_.-]+)@([^\s#]+)", line):
                action, ref = m.group(1), m.group(2)
                if re.match(r"^[a-f0-9]{40}$", ref):  # full SHA — pinned
                    continue
                owner = action.split("/")[0].lower()
                if owner in ("actions", "github"):
                    first_party_files.add(relpath)
                else:
                    third_party.append((relpath, lineno, f"{action}@{ref}"))

    if third_party:
        unique = list(dict.fromkeys(third_party))
        for relpath, lineno, spec in unique[:6]:
            add("medium", f"Third-party GitHub Action pinned by tag/branch (pin to SHA): {spec} at {relpath}:{lineno}")
        if len(unique) > 6:
            add("medium", f"  ... and {len(unique) - 6} more third-party actions pinned by tag/branch")
    if first_party_files:
        add("info", f"{len(first_party_files)} workflow(s) pin official actions/* or github/* by tag rather than SHA (low risk)")


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    if not ecosystems:
        print("No recognized package manager found (package.json, requirements.txt, go.mod, etc.)")
        return

    print(f"Detected ecosystems: {', '.join(ecosystems)}")

    if "npm" in ecosystems:
        check_npm()
    if "python" in ecosystems:
        check_python()
    if "go" in ecosystems:
        check_go()
    if "rust" in ecosystems:
        check_rust()
    if "php" in ecosystems:
        check_php()
    if "ruby" in ecosystems:
        check_ruby()

    check_ci_supply_chain()

    if not issues:
        print("No dependency health issues found.")
        return

    severity_order = {"critical": 0, "high": 1, "medium": 2, "info": 3}
    issues.sort(key=lambda x: severity_order.get(x[0], 4))

    for severity, msg in issues[:40]:
        tag = {"critical": "CRITICAL", "high": "HIGH", "medium": "MEDIUM", "info": "INFO"}.get(severity, severity)
        print(f"  [{tag}] {msg}")

    total = len(issues)
    print(f"\n{total} dependency issues found.")


if __name__ == "__main__":
    main()
