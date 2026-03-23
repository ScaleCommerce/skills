#!/usr/bin/env python3
"""
Comprehensive security scanner: secrets, injection patterns, access control, insecure APIs.
Covers OWASP Top 10 2025, CWE/SANS Top 25, and common vulnerability patterns.
"""
import os
import re
import sys
import math
from collections import defaultdict

root = sys.argv[1] if len(sys.argv) > 1 else "."
issues = []  # (severity, category, message)

SKIP_DIRS = {
    "node_modules", ".git", "vendor", "dist", "__pycache__", ".venv",
    ".nuxt", ".next", ".output", "build", "coverage", ".tox", "venv",
}
SOURCE_EXTS = {
    ".ts", ".tsx", ".js", ".jsx", ".vue", ".svelte",
    ".py", ".go", ".php", ".rb", ".java", ".rs", ".cs",
}
CONFIG_EXTS = {".env", ".yaml", ".yml", ".json", ".toml", ".xml", ".ini", ".cfg"}
ALL_EXTS = SOURCE_EXTS | CONFIG_EXTS


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def walk_files(extensions=None):
    """Yield (filepath, content, lines) for matching files."""
    exts = extensions or ALL_EXTS
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fname in filenames:
            if not any(fname.endswith(e) for e in exts):
                continue
            # Skip lockfiles and minified bundles
            if fname.endswith((".lock", "-lock.json", ".min.js", ".min.css")):
                continue
            fpath = os.path.join(dirpath, fname)
            try:
                with open(fpath, "r", errors="ignore") as f:
                    content = f.read()
            except Exception:
                continue
            yield fpath, content, content.split("\n")


def add(severity, category, msg):
    issues.append((severity, category, msg))


def line_num(content, pos):
    return content[:pos].count("\n") + 1


# ---------------------------------------------------------------------------
# 1. SECRET DETECTION (expanded patterns)
# ---------------------------------------------------------------------------

SECRET_PATTERNS = [
    # Cloud provider keys
    (r"AKIA[0-9A-Z]{16}", "AWS Access Key ID"),
    (r"(?:aws).{0,20}['\"][0-9a-zA-Z/+]{40}['\"]", "AWS Secret Access Key"),
    (r"AIza[0-9A-Za-z\-_]{35}", "Google API Key"),
    (r'"type"\s*:\s*"service_account"', "GCP Service Account JSON"),
    (r"AZURE[_-]?(?:STORAGE|SUBSCRIPTION|TENANT|CLIENT)[_-]?(?:KEY|ID|SECRET)\s*[=:]\s*['\"][^'\"]{8,}['\"]", "Azure credential"),

    # SaaS tokens
    (r"ghp_[a-zA-Z0-9]{36}", "GitHub Personal Access Token"),
    (r"gho_[a-zA-Z0-9]{36}", "GitHub OAuth Token"),
    (r"ghu_[a-zA-Z0-9]{36}", "GitHub User-to-Server Token"),
    (r"ghs_[a-zA-Z0-9]{36}", "GitHub Server-to-Server Token"),
    (r"github_pat_[a-zA-Z0-9]{22}_[a-zA-Z0-9]{59}", "GitHub Fine-Grained PAT"),
    (r"xox[bpras]-[a-zA-Z0-9\-]{10,}", "Slack Token"),
    (r"sk-[a-zA-Z0-9]{20}T3BlbkFJ[a-zA-Z0-9]{20}", "OpenAI API Key"),
    (r"sk-(?:proj-|ant-)?[a-zA-Z0-9\-_]{20,}", "API Secret Key (sk-*)"),
    (r"sk_live_[a-zA-Z0-9]{24,}", "Stripe Live Secret Key"),
    (r"rk_live_[a-zA-Z0-9]{24,}", "Stripe Restricted Key"),
    (r"sq0atp-[a-zA-Z0-9\-_]{22}", "Square Access Token"),
    (r"SG\.[a-zA-Z0-9\-_]{22}\.[a-zA-Z0-9\-_]{43}", "SendGrid API Key"),
    (r"key-[a-zA-Z0-9]{32}", "Mailgun API Key"),
    (r"(?:twilio|TWILIO).{0,20}SK[a-f0-9]{32}", "Twilio API Key"),

    # Generic patterns
    (r"(?:password|passwd|pwd)\s*[=:]\s*[\"'][^\"']{4,}[\"']", "Possible hardcoded password"),
    (r"(?:api[_-]?key|apikey)\s*[=:]\s*[\"'][^\"']{8,}[\"']", "Possible hardcoded API key"),
    (r"(?:secret|token|auth)\s*[=:]\s*[\"'][A-Za-z0-9+/=_\-]{16,}[\"']", "Possible hardcoded secret/token"),
    (r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY-----", "Private key in source code"),
    (r"-----BEGIN CERTIFICATE-----", "Certificate in source code"),

    # JWT tokens (3 base64 segments separated by dots)
    (r"eyJ[a-zA-Z0-9_-]{10,}\.eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}", "Hardcoded JWT token"),
]

# Common false positives to skip
FALSE_POSITIVE_HINTS = [
    "example", "placeholder", "your_", "xxx", "changeme", "password123",
    "test", "dummy", "sample", "fake", "mock", "todo", "fixme",
    "process.env", "os.environ", "os.getenv", "env(", "${",
    "import ", "require(", "from ",
]


def check_secrets():
    for fpath, content, lines in walk_files():
        rel = os.path.relpath(fpath, root)
        for pattern, label in SECRET_PATTERNS:
            for m in re.finditer(pattern, content, re.IGNORECASE):
                matched = m.group()
                context = content[max(0, m.start() - 80):m.end() + 40].lower()
                # Skip false positives
                if any(fp in context for fp in FALSE_POSITIVE_HINTS):
                    continue
                ln = line_num(content, m.start())
                add("critical", "secrets", f"{label}: {rel}:{ln}")

        # Entropy-based detection for generic assignment patterns
        # Look for variable assignments with high-entropy string values
        for m in re.finditer(
            r'(?:key|secret|token|password|credential|auth)[_\w]*\s*[=:]\s*["\']([A-Za-z0-9+/=_\-]{20,})["\']',
            content, re.IGNORECASE
        ):
            value = m.group(1)
            context = content[max(0, m.start() - 60):m.end() + 20].lower()
            if any(fp in context for fp in FALSE_POSITIVE_HINTS):
                continue
            entropy = _shannon_entropy(value)
            if entropy > 4.5:
                ln = line_num(content, m.start())
                add("critical", "secrets", f"High-entropy secret (entropy={entropy:.1f}): {rel}:{ln}")


def _shannon_entropy(s):
    """Calculate Shannon entropy of a string."""
    if not s:
        return 0
    freq = defaultdict(int)
    for c in s:
        freq[c] += 1
    length = len(s)
    return -sum((count / length) * math.log2(count / length) for count in freq.values())


# ---------------------------------------------------------------------------
# 2. .env FILES COMMITTED
# ---------------------------------------------------------------------------

def check_env_files():
    """Flag .env files that exist in the repo (should be gitignored)."""
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fname in filenames:
            if fname == ".env" or (fname.startswith(".env.") and not fname.endswith(".example") and not fname.endswith(".sample") and not fname.endswith(".template")):
                fpath = os.path.relpath(os.path.join(dirpath, fname), root)
                # Check if it contains actual values (not just variable names)
                try:
                    with open(os.path.join(dirpath, fname), "r", errors="ignore") as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith("#") and "=" in line:
                                key, _, val = line.partition("=")
                                val = val.strip().strip("\"'")
                                if val and val not in ("", "changeme", "your_value_here"):
                                    add("critical", "secrets", f".env file with values present: {fpath} — should be gitignored")
                                    return
                except Exception:
                    pass


# ---------------------------------------------------------------------------
# 3. INJECTION PATTERNS
# ---------------------------------------------------------------------------

INJECTION_PATTERNS_JS = [
    # SQL injection
    (r"(?:query|execute|raw)\s*\(\s*[`'\"].*\$\{", "Potential SQL injection (template literal in query)"),
    (r"(?:query|execute|raw)\s*\(\s*['\"].*\+\s*(?:req\.|params\.|query\.|body\.)", "Potential SQL injection (string concat with user input)"),

    # XSS
    (r"\.innerHTML\s*=\s*(?!['\"]\s*$)", "innerHTML assignment — potential XSS"),
    (r"dangerouslySetInnerHTML", "dangerouslySetInnerHTML — ensure input is sanitized"),
    (r"document\.write\s*\(", "document.write — potential XSS"),
    (r"v-html\s*=", "v-html directive — potential XSS if data is user-controlled"),

    # Command injection
    (r"(?:exec|execSync|spawn|spawnSync)\s*\(\s*(?:`.*\$\{|['\"].*\+)", "Potential command injection (user input in shell command)"),
    (r"child_process.*(?:req\.|params\.|query\.|body\.)", "User input flowing into child_process"),

    # Path traversal
    (r"(?:readFile|writeFile|createReadStream|unlink|readdir)\s*\([^)]*(?:req\.|params\.|query\.|body\.)", "Potential path traversal (user input in file operation)"),
    (r"\.\.\/", None),  # tracked separately below

    # Prototype pollution
    (r"Object\.assign\s*\(\s*\{\s*\}\s*,.*(?:req\.|params\.|body\.)", "Potential prototype pollution via Object.assign with user input"),
    (r"\[(?:req|params|query|body)\.[^\]]+\]\s*=", "Potential prototype pollution (dynamic property assignment from user input)"),

    # Template injection
    (r"new\s+Function\s*\(.*(?:req\.|params\.|body\.)", "Potential template injection via Function constructor"),

    # Eval
    (r"\beval\s*\(", "eval() usage — avoid if possible, especially with dynamic input"),

    # Regex DoS
    (r"new\s+RegExp\s*\(.*(?:req\.|params\.|query\.|body\.)", "User input in RegExp constructor — potential ReDoS"),
]

INJECTION_PATTERNS_PY = [
    # SQL injection
    (r"(?:execute|raw)\s*\(\s*f['\"]", "Potential SQL injection (f-string in query)"),
    (r"(?:execute|raw)\s*\(\s*['\"].*%\s", "Potential SQL injection (% formatting in query)"),
    (r"(?:execute|raw)\s*\(\s*['\"].*\.format\(", "Potential SQL injection (.format in query)"),

    # Command injection
    (r"os\.system\s*\(", "os.system() — use subprocess with shell=False instead"),
    (r"subprocess.*shell\s*=\s*True", "subprocess with shell=True — potential command injection"),
    (r"os\.popen\s*\(", "os.popen() — use subprocess with shell=False instead"),

    # Code execution
    (r"\beval\s*\(", "eval() usage — avoid with dynamic input"),
    (r"\bexec\s*\(", "exec() usage — avoid with dynamic input"),
    (r"pickle\.loads?\s*\(", "pickle deserialization — unsafe with untrusted data"),
    (r"yaml\.load\s*\((?!.*Loader\s*=\s*yaml\.SafeLoader)", "yaml.load without SafeLoader — use yaml.safe_load"),
    (r"marshal\.loads?\s*\(", "marshal deserialization — unsafe with untrusted data"),

    # Path traversal
    (r"open\s*\(.*(?:request\.|args\.|form\.)", "Potential path traversal (user input in file open)"),

    # Template injection (Jinja2, etc.)
    (r"Template\s*\(.*(?:request\.|args\.|form\.)", "Potential server-side template injection"),
    (r"render_template_string\s*\(", "render_template_string — potential SSTI if input is user-controlled"),

    # Insecure deserialization
    (r"jsonpickle\.decode\s*\(", "jsonpickle deserialization — unsafe with untrusted data"),
]

INJECTION_PATTERNS_GO = [
    (r"fmt\.Sprintf\s*\(.*(?:SELECT|INSERT|UPDATE|DELETE)", "Potential SQL injection (Sprintf in query)"),
    (r"exec\.Command\s*\(.*\+", "Potential command injection (string concat in exec.Command)"),
    (r"template\.HTML\s*\(", "template.HTML — bypasses HTML escaping"),
]

INJECTION_PATTERNS_PHP = [
    (r"\$_(?:GET|POST|REQUEST|COOKIE)\s*\[", None),  # tracked for context
    (r"mysql_query\s*\(", "mysql_query is deprecated and unsafe — use PDO with prepared statements"),
    (r"mysqli?_query\s*\(\s*\$\w+\s*,\s*[\"'].*\\\$", "Potential SQL injection (variable in query string)"),
    (r"\beval\s*\(", "eval() usage — avoid with user input"),
    (r"(?:include|require)(?:_once)?\s*\(\s*\$", "Dynamic include/require — potential LFI/RFI"),
    (r"unserialize\s*\(", "unserialize — unsafe with untrusted data"),
    (r"shell_exec\s*\(|`[^`]*\$", "Shell execution — potential command injection"),
]


def check_injections():
    for fpath, content, lines in walk_files(SOURCE_EXTS):
        rel = os.path.relpath(fpath, root)
        ext = os.path.splitext(fpath)[1]

        patterns = []
        if ext in (".ts", ".tsx", ".js", ".jsx", ".vue", ".svelte"):
            patterns = INJECTION_PATTERNS_JS
        elif ext == ".py":
            patterns = INJECTION_PATTERNS_PY
        elif ext == ".go":
            patterns = INJECTION_PATTERNS_GO
        elif ext == ".php":
            patterns = INJECTION_PATTERNS_PHP

        for pattern, label in patterns:
            if label is None:
                continue
            for m in re.finditer(pattern, content, re.IGNORECASE):
                ln = line_num(content, m.start())
                # Skip comments
                line_text = lines[ln - 1].strip() if ln <= len(lines) else ""
                if line_text.startswith(("//", "#", "*", "/*", "<!--")):
                    continue
                add("high", "injection", f"{label}: {rel}:{ln}")


# ---------------------------------------------------------------------------
# 4. ACCESS CONTROL & AUTH PATTERNS
# ---------------------------------------------------------------------------

def check_access_control():
    """Look for missing auth patterns, CORS misconfig, CSRF issues."""
    for fpath, content, lines in walk_files(SOURCE_EXTS | CONFIG_EXTS):
        rel = os.path.relpath(fpath, root)
        ext = os.path.splitext(fpath)[1]

        # Overly permissive CORS
        if re.search(r"""(?:Access-Control-Allow-Origin|cors)\s*[=:(\[{]\s*['"]?\*['"]?""", content, re.IGNORECASE):
            ln = line_num(content, re.search(r"(?:Access-Control-Allow-Origin|cors)\s*[=:(\[{]\s*['\"]?\*", content, re.IGNORECASE).start())
            add("high", "access-control", f"CORS allows all origins (*): {rel}:{ln}")

        # Credentials with wildcard CORS
        if re.search(r"credentials\s*:\s*true", content, re.IGNORECASE) and re.search(r"origin\s*:\s*['\"]?\*", content, re.IGNORECASE):
            add("critical", "access-control", f"CORS with credentials:true and wildcard origin — credential theft risk: {rel}")

        # Missing CSRF protection (Express/Connect)
        if ext in (".ts", ".js") and re.search(r"app\.(post|put|patch|delete)\s*\(", content):
            if not re.search(r"csrf|csurf|csrfToken|_csrf", content, re.IGNORECASE):
                # Only flag route files, not utility modules
                if any(x in rel.lower() for x in ["route", "controller", "handler", "api", "server"]):
                    add("medium", "access-control", f"State-changing routes without CSRF protection: {rel}")

        # Disabled security features
        for pattern, label in [
            (r"helmet\s*\(\s*\{\s*[^}]*(?:contentSecurityPolicy|frameguard|hsts)\s*:\s*false", "Security header explicitly disabled"),
            (r"X-Frame-Options.*(?:ALLOWALL|disabled)", "X-Frame-Options disabled — clickjacking risk"),
            (r"(?:verify|check|validate)(?:SSL|Certificate|TLS)\s*[=:]\s*false", "SSL/TLS verification disabled"),
            (r"rejectUnauthorized\s*:\s*false", "TLS certificate verification disabled"),
            (r"NODE_TLS_REJECT_UNAUTHORIZED\s*=\s*['\"]?0", "TLS certificate verification disabled via env"),
            (r"InsecureSkipVerify\s*:\s*true", "Go TLS verification disabled"),
            (r"verify\s*=\s*False", "Python SSL verification disabled"),
        ]:
            for m in re.finditer(pattern, content, re.IGNORECASE):
                ln = line_num(content, m.start())
                add("high", "access-control", f"{label}: {rel}:{ln}")


# ---------------------------------------------------------------------------
# 5. INSECURE CRYPTO & HASHING
# ---------------------------------------------------------------------------

def check_crypto():
    for fpath, content, lines in walk_files(SOURCE_EXTS):
        rel = os.path.relpath(fpath, root)
        for pattern, label in [
            (r"createHash\s*\(\s*['\"](?:md5|sha1)['\"]", "Weak hash algorithm (MD5/SHA1) — use SHA-256+"),
            (r"hashlib\.(?:md5|sha1)\s*\(", "Weak hash algorithm (MD5/SHA1) — use SHA-256+"),
            (r"Math\.random\s*\(", "Math.random() for security-sensitive context — use crypto.randomUUID or crypto.getRandomValues"),
            (r"random\.random\s*\(|random\.randint\s*\(", "random module is not cryptographically secure — use secrets module"),
            (r"DES|Blowfish|RC4|RC2", "Weak/deprecated cipher algorithm"),
            (r"ECB", "ECB mode — does not provide semantic security"),
            (r"padding\s*=\s*(?:PKCS1v15|pkcs1)", "PKCS1v15 padding — use OAEP for RSA encryption"),
        ]:
            for m in re.finditer(pattern, content):
                ln = line_num(content, m.start())
                line_text = lines[ln - 1].strip() if ln <= len(lines) else ""
                if line_text.startswith(("//", "#", "*", "/*")):
                    continue
                # Math.random is only a concern in security context
                if "Math.random" in pattern:
                    # Check surrounding context for security-related usage
                    context = content[max(0, m.start() - 200):m.end() + 200].lower()
                    if not any(w in context for w in ["token", "secret", "password", "key", "auth", "session", "nonce", "salt", "hash", "random id", "uuid"]):
                        continue
                add("medium", "crypto", f"{label}: {rel}:{ln}")


# ---------------------------------------------------------------------------
# 6. INFORMATION DISCLOSURE
# ---------------------------------------------------------------------------

def check_info_disclosure():
    for fpath, content, lines in walk_files(SOURCE_EXTS):
        rel = os.path.relpath(fpath, root)
        for pattern, label in [
            # Stack traces sent to client
            (r"res\.(?:send|json|status)\s*\([^)]*(?:err\.stack|error\.stack|stackTrace)", "Stack trace sent in response — information disclosure"),
            (r"(?:message|detail|error)\s*:\s*(?:err|error)\.(?:message|stack)", "Error details sent to client — may leak internals"),
            # Debug mode in production config
            (r"DEBUG\s*[=:]\s*(?:True|true|1|['\"]true['\"])", "Debug mode enabled — ensure this is dev-only"),
            # Verbose error pages
            (r"app\.use\s*\(\s*errorHandler\s*\(\s*\{\s*[^}]*debug\s*:\s*true", "Debug error handler enabled"),
        ]:
            for m in re.finditer(pattern, content):
                ln = line_num(content, m.start())
                add("medium", "info-disclosure", f"{label}: {rel}:{ln}")


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    check_secrets()
    check_env_files()
    check_injections()
    check_access_control()
    check_crypto()
    check_info_disclosure()

    if not issues:
        print("No security issues detected.")
        return

    # Group and sort by severity
    severity_order = {"critical": 0, "high": 1, "medium": 2}
    issues.sort(key=lambda x: (severity_order.get(x[0], 3), x[1]))

    current_cat = None
    for severity, category, msg in issues[:60]:
        if category != current_cat:
            current_cat = category
            print(f"\n=== {category.upper()} ===")
        severity_tag = {"critical": "CRITICAL", "high": "HIGH", "medium": "MEDIUM"}.get(severity, severity)
        print(f"  [{severity_tag}] {msg}")

    total = len(issues)
    critical = sum(1 for s, _, _ in issues if s == "critical")
    high = sum(1 for s, _, _ in issues if s == "high")
    print(f"\n{total} security issues found ({critical} critical, {high} high)")
    if total > 60:
        print(f"  (showing first 60 of {total})")


if __name__ == "__main__":
    main()
