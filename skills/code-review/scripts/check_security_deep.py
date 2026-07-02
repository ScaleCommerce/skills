#!/usr/bin/env python3
"""
Comprehensive security scanner: secrets, injection patterns, access control, insecure APIs.
Covers OWASP Top 10 2025, CWE/SANS Top 25, and common vulnerability patterns.

Precision matters more than recall here: every false positive the reviewing
agent has to dismiss erodes trust in the real findings. Structured token
patterns are case-sensitive, placeholder detection looks at the matched line
(not a broad context window), and .env findings consult .gitignore.
"""
import os
import re
import sys
import math
from collections import defaultdict

from common import iter_source_files, read_text, is_ignored_by_git

root = sys.argv[1] if len(sys.argv) > 1 else "."
issues = []  # (severity, category, message)

SOURCE_EXTS = {
    ".ts", ".tsx", ".js", ".jsx", ".vue", ".svelte",
    ".py", ".go", ".php", ".rb", ".java", ".rs", ".cs",
}
CONFIG_EXTS = {".env", ".yaml", ".yml", ".json", ".toml", ".xml", ".ini", ".cfg"}
ALL_EXTS = SOURCE_EXTS | CONFIG_EXTS


def walk_files(extensions=None):
    """Yield (filepath, content, lines) for matching files."""
    for fpath in iter_source_files(root, extensions or ALL_EXTS):
        content = read_text(fpath)
        if content is None:
            continue
        yield fpath, content, content.split("\n")


def add(severity, category, msg):
    issues.append((severity, category, msg))


def line_num(content, pos):
    return content[:pos].count("\n") + 1


def line_at(content, lines, pos):
    ln = line_num(content, pos)
    text = lines[ln - 1] if ln <= len(lines) else ""
    return ln, text


# ---------------------------------------------------------------------------
# 1. SECRET DETECTION
# ---------------------------------------------------------------------------

# Structured tokens have a fixed format — matching them case-insensitively
# destroys their precision (AKIA keys are uppercase by definition).
# Tuple: (pattern, label, regex flags)
SECRET_PATTERNS = [
    # Cloud provider keys
    (r"\bAKIA[0-9A-Z]{16}\b", "AWS Access Key ID", 0),
    (r"(?:aws|AWS).{0,20}['\"][0-9a-zA-Z/+]{40}['\"]", "AWS Secret Access Key", 0),
    (r"\bAIza[0-9A-Za-z\-_]{35}\b", "Google API Key", 0),
    (r'"type"\s*:\s*"service_account"', "GCP Service Account JSON", 0),
    (r"AZURE[_-]?(?:STORAGE|SUBSCRIPTION|TENANT|CLIENT)[_-]?(?:KEY|ID|SECRET)\s*[=:]\s*['\"][^'\"]{8,}['\"]", "Azure credential", re.IGNORECASE),

    # SaaS tokens
    (r"\bghp_[a-zA-Z0-9]{36}\b", "GitHub Personal Access Token", 0),
    (r"\bgho_[a-zA-Z0-9]{36}\b", "GitHub OAuth Token", 0),
    (r"\bghu_[a-zA-Z0-9]{36}\b", "GitHub User-to-Server Token", 0),
    (r"\bghs_[a-zA-Z0-9]{36}\b", "GitHub Server-to-Server Token", 0),
    (r"\bgithub_pat_[a-zA-Z0-9]{22}_[a-zA-Z0-9]{59}\b", "GitHub Fine-Grained PAT", 0),
    (r"\bxox[bpras]-[a-zA-Z0-9\-]{10,}", "Slack Token", 0),
    (r"\bsk-[a-zA-Z0-9]{20}T3BlbkFJ[a-zA-Z0-9]{20}\b", "OpenAI API Key", 0),
    (r"\bsk-(?:proj|ant|api)-[a-zA-Z0-9\-_]{24,}", "API Secret Key (sk-proj/sk-ant)", 0),
    (r"\bsk_live_[a-zA-Z0-9]{24,}\b", "Stripe Live Secret Key", 0),
    (r"\brk_live_[a-zA-Z0-9]{24,}\b", "Stripe Restricted Key", 0),
    (r"\bsq0atp-[a-zA-Z0-9\-_]{22}\b", "Square Access Token", 0),
    (r"\bSG\.[a-zA-Z0-9\-_]{22}\.[a-zA-Z0-9\-_]{43}\b", "SendGrid API Key", 0),
    (r"\bkey-[a-f0-9]{32}\b", "Mailgun API Key", 0),
    (r"(?:twilio|TWILIO).{0,20}SK[a-f0-9]{32}", "Twilio API Key", 0),

    # Generic patterns — these need IGNORECASE and placeholder filtering
    (r"(?:password|passwd|pwd)\s*[=:]\s*[\"'][^\"']{4,}[\"']", "Possible hardcoded password", re.IGNORECASE),
    (r"(?:api[_-]?key|apikey)\s*[=:]\s*[\"'][^\"']{8,}[\"']", "Possible hardcoded API key", re.IGNORECASE),
    (r"(?:secret|token|auth)\s*[=:]\s*[\"'][A-Za-z0-9+/=_\-]{16,}[\"']", "Possible hardcoded secret/token", re.IGNORECASE),
    (r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY-----", "Private key in source code", 0),

    # JWT tokens (3 base64 segments separated by dots)
    (r"\beyJ[a-zA-Z0-9_-]{10,}\.eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}", "Hardcoded JWT token", 0),
]

# Values/lines that are clearly placeholders. Checked against the matched LINE,
# not a wide context window — "a real AWS key near an import statement" must
# still be reported.
PLACEHOLDER_HINTS = [
    "example", "placeholder", "your_", "your-", "xxx", "changeme",
    "password123", "dummy", "sample", "fake", "mock", "todo", "fixme",
    "<", "...",
]
# Lines that read the value from the environment are fine — but only for the
# generic patterns; a structured token literal is a finding regardless.
ENV_LOOKUP_HINTS = ["process.env", "os.environ", "os.getenv", "env(", "${", "getenv"]

GENERIC_LABELS = {"Possible hardcoded password", "Possible hardcoded API key",
                  "Possible hardcoded secret/token"}


def check_secrets():
    for fpath, content, lines in walk_files():
        rel = os.path.relpath(fpath, root)
        is_test_file = bool(re.search(r"(^|/)(tests?|__tests__|spec|fixtures?)(/|$)|\.(test|spec)\.",
                                      rel.replace(os.sep, "/")))
        for pattern, label, flags in SECRET_PATTERNS:
            for m in re.finditer(pattern, content, flags):
                ln, line_text = line_at(content, lines, m.start())
                lowered = line_text.lower()
                if any(fp in lowered for fp in PLACEHOLDER_HINTS):
                    continue
                if label in GENERIC_LABELS and any(h in line_text for h in ENV_LOOKUP_HINTS):
                    continue
                severity = "high" if (is_test_file or label in GENERIC_LABELS) else "critical"
                suffix = " (in test/fixture — verify it is not a real credential)" if is_test_file else ""
                add(severity, "secrets", f"{label}: {rel}:{ln}{suffix}")

        # Entropy-based detection for generic assignment patterns
        for m in re.finditer(
            r'(?:key|secret|token|password|credential|auth)[_\w]*\s*[=:]\s*["\']([A-Za-z0-9+/=_\-]{20,})["\']',
            content, re.IGNORECASE
        ):
            value = m.group(1)
            ln, line_text = line_at(content, lines, m.start())
            lowered = line_text.lower()
            if any(fp in lowered for fp in PLACEHOLDER_HINTS):
                continue
            if any(h in line_text for h in ENV_LOOKUP_HINTS):
                continue
            if _shannon_entropy(value) > 4.5:
                add("high", "secrets",
                    f"High-entropy secret (entropy={_shannon_entropy(value):.1f}): {rel}:{ln}")


def _shannon_entropy(s):
    if not s:
        return 0
    freq = defaultdict(int)
    for c in s:
        freq[c] += 1
    length = len(s)
    return -sum((count / length) * math.log2(count / length) for count in freq.values())


# ---------------------------------------------------------------------------
# 2. .env FILES
# ---------------------------------------------------------------------------

def check_env_files():
    """Flag .env files with real values — but only when they are NOT gitignored.
    A properly-ignored local .env is correct practice, not a finding."""
    # iter_source_files already excludes gitignored files inside a git repo,
    # so anything it yields here is tracked or would be committed.
    for fpath in iter_source_files(root, None):
        fname = os.path.basename(fpath)
        if not (fname == ".env" or (fname.startswith(".env.")
                and not fname.endswith((".example", ".sample", ".template")))):
            continue
        rel = os.path.relpath(fpath, root)
        if is_ignored_by_git(root, rel):
            continue
        content = read_text(fpath) or ""
        for line in content.splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                _, _, val = line.partition("=")
                val = val.strip().strip("\"'")
                if val and val.lower() not in ("", "changeme", "your_value_here", "true", "false"):
                    add("critical", "secrets",
                        f".env file with values is not gitignored: {rel} — add it to .gitignore and rotate any real credentials")
                    break  # one finding per file, keep checking other .env files


# ---------------------------------------------------------------------------
# 3. INJECTION PATTERNS
# ---------------------------------------------------------------------------

INJECTION_PATTERNS_JS = [
    # SQL injection
    (r"(?:query|execute|raw)\s*\(\s*[`'\"].*\$\{", "Potential SQL injection (template literal in query)"),
    (r"(?:query|execute|raw)\s*\(\s*['\"].*\+\s*(?:req\.|params\.|query\.|body\.)", "Potential SQL injection (string concat with user input)"),

    # XSS — skip assignments of a pure string literal (no interpolation).
    # (?m) so the $ anchors work per-line; the \s* must live INSIDE the
    # lookahead, otherwise the engine backtracks past it and the exclusion
    # never applies.
    (r"(?m)\.innerHTML\s*=(?!\s*(?:'[^'$]*'|\"[^\"$]*\"|`[^`$]*`)\s*;?\s*$)", "innerHTML assignment — potential XSS"),
    (r"dangerouslySetInnerHTML", "dangerouslySetInnerHTML — ensure input is sanitized"),
    (r"document\.write\s*\(", "document.write — potential XSS"),
    (r"v-html\s*=", "v-html directive — potential XSS if data is user-controlled"),

    # Command injection
    (r"(?:exec|execSync|spawn|spawnSync)\s*\(\s*(?:`.*\$\{|['\"].*\+)", "Potential command injection (user input in shell command)"),
    (r"child_process.*(?:req\.|params\.|query\.|body\.)", "User input flowing into child_process"),

    # Path traversal
    (r"(?:readFile|writeFile|createReadStream|unlink|readdir)\s*\([^)]*(?:req\.|params\.|query\.|body\.)", "Potential path traversal (user input in file operation)"),

    # SSRF / open redirect
    (r"(?:fetch|axios(?:\.\w+)?|got|request)\s*\(\s*(?:req\.|params\.|query\.|body\.)", "User input as outbound request URL — potential SSRF"),
    (r"res\.redirect\s*\(\s*(?:req\.|params\.|query\.|body\.)", "User input in redirect target — potential open redirect"),

    # Prototype pollution
    (r"Object\.assign\s*\(\s*\{\s*\}\s*,.*(?:req\.|params\.|body\.)", "Potential prototype pollution via Object.assign with user input"),
    (r"\[(?:req|params|query|body)\.[^\]]+\]\s*=", "Potential prototype pollution (dynamic property assignment from user input)"),

    # Code execution
    (r"new\s+Function\s*\(.*(?:req\.|params\.|body\.)", "Potential code injection via Function constructor"),
    (r"(?<![.\w])eval\s*\(", "eval() usage — avoid if possible, especially with dynamic input"),

    # JWT misconfiguration
    (r"algorithms?\s*:\s*\[[^\]]*['\"]none['\"]", "JWT 'none' algorithm accepted — signature bypass"),

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

    # Code execution. Lookbehind excludes method calls like model.eval() —
    # ubiquitous in ML code and unrelated to Python's builtin eval.
    (r"(?<![.\w])eval\s*\(", "eval() usage — avoid with dynamic input"),
    (r"(?<![.\w])exec\s*\(", "exec() usage — avoid with dynamic input"),
    (r"pickle\.loads?\s*\(", "pickle deserialization — unsafe with untrusted data"),
    (r"yaml\.load\s*\((?!.*Loader\s*=\s*yaml\.SafeLoader)", "yaml.load without SafeLoader — use yaml.safe_load"),
    (r"marshal\.loads?\s*\(", "marshal deserialization — unsafe with untrusted data"),

    # Path traversal
    (r"open\s*\(.*(?:request\.|args\.|form\.)", "Potential path traversal (user input in file open)"),

    # SSRF / open redirect
    (r"requests\.(?:get|post|put|delete|head)\s*\(\s*(?:request\.|args\.|form\.)", "User input as outbound request URL — potential SSRF"),
    (r"redirect\s*\(\s*request\.", "User input in redirect target — potential open redirect"),

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
    (r"mysql_query\s*\(", "mysql_query is deprecated and unsafe — use PDO with prepared statements"),
    (r"mysqli?_query\s*\(\s*\$\w+\s*,\s*[\"'].*\\\$", "Potential SQL injection (variable in query string)"),
    (r"(?<![\w$])eval\s*\(", "eval() usage — avoid with user input"),
    (r"(?:include|require)(?:_once)?\s*\(\s*\$", "Dynamic include/require — potential LFI/RFI"),
    (r"unserialize\s*\(", "unserialize — unsafe with untrusted data"),
    (r"shell_exec\s*\(|`[^`]*\$", "Shell execution — potential command injection"),
    (r"header\s*\(\s*['\"]Location:\s*['\"]?\s*\.\s*\$_(?:GET|POST|REQUEST)", "User input in redirect — potential open redirect"),
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
            for m in re.finditer(pattern, content, re.IGNORECASE):
                ln, line_text = line_at(content, lines, m.start())
                if line_text.strip().startswith(("//", "#", "*", "/*", "<!--")):
                    continue
                add("high", "injection", f"{label}: {rel}:{ln}")


# ---------------------------------------------------------------------------
# 4. ACCESS CONTROL & AUTH PATTERNS
# ---------------------------------------------------------------------------

def check_access_control():
    for fpath, content, lines in walk_files(SOURCE_EXTS | CONFIG_EXTS):
        rel = os.path.relpath(fpath, root)
        ext = os.path.splitext(fpath)[1]

        # Overly permissive CORS
        m = re.search(r"""(?:Access-Control-Allow-Origin|cors)\s*[=:(\[{]\s*['"]?\*""", content, re.IGNORECASE)
        if m:
            add("high", "access-control", f"CORS allows all origins (*): {rel}:{line_num(content, m.start())}")

        # Credentials with wildcard CORS
        if re.search(r"credentials\s*:\s*true", content, re.IGNORECASE) and re.search(r"origin\s*:\s*['\"]?\*", content, re.IGNORECASE):
            add("critical", "access-control", f"CORS with credentials:true and wildcard origin — credential theft risk: {rel}")

        # Missing CSRF protection — only meaningful for cookie/session auth.
        # Token-auth APIs (Authorization header) don't need CSRF tokens, so
        # require evidence of cookie/session use before flagging.
        if ext in (".ts", ".js") and re.search(r"app\.(post|put|patch|delete)\s*\(", content):
            uses_cookies = re.search(r"\b(?:cookie-session|express-session|cookieParser|res\.cookie)\b", content)
            if uses_cookies and not re.search(r"csrf|csurf|csrfToken|_csrf|sameSite", content, re.IGNORECASE):
                if any(x in rel.lower() for x in ["route", "controller", "handler", "api", "server"]):
                    add("medium", "access-control", f"Cookie/session-based state-changing routes without CSRF protection: {rel}")

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
                add("high", "access-control", f"{label}: {rel}:{line_num(content, m.start())}")


# ---------------------------------------------------------------------------
# 5. INSECURE CRYPTO & HASHING
# ---------------------------------------------------------------------------

SECURITY_CONTEXT_WORDS = ["token", "secret", "password", "key", "auth",
                          "session", "nonce", "salt", "csrf", "otp", "uuid"]


def _in_security_context(content, start, end):
    context = content[max(0, start - 200):end + 200].lower()
    return any(w in context for w in SECURITY_CONTEXT_WORDS)


def check_crypto():
    for fpath, content, lines in walk_files(SOURCE_EXTS):
        rel = os.path.relpath(fpath, root)
        for pattern, label, needs_context in [
            (r"createHash\s*\(\s*['\"](?:md5|sha1)['\"]", "Weak hash algorithm (MD5/SHA1) — use SHA-256+", False),
            (r"hashlib\.(?:md5|sha1)\s*\(", "Weak hash algorithm (MD5/SHA1) — use SHA-256+", False),
            (r"Math\.random\s*\(", "Math.random() for security-sensitive value — use crypto.randomUUID or crypto.getRandomValues", True),
            (r"random\.(?:random|randint|choice|randrange)\s*\(", "random module for security-sensitive value — use the secrets module", True),
            # Word boundaries: without them 'DES' matches SQL 'ORDER BY x DESC'.
            # Cipher names additionally require a crypto-ish context word.
            (r"\b(?:DES|3DES|RC4|RC2|Blowfish)\b", "Weak/deprecated cipher algorithm", True),
            (r"\bECB\b", "ECB mode — does not provide semantic security", True),
            (r"padding\s*=\s*(?:PKCS1v15|pkcs1)", "PKCS1v15 padding — use OAEP for RSA encryption", False),
        ]:
            for m in re.finditer(pattern, content):
                ln, line_text = line_at(content, lines, m.start())
                if line_text.strip().startswith(("//", "#", "*", "/*")):
                    continue
                if needs_context:
                    if pattern.startswith(r"\b"):  # cipher names: need crypto context
                        context = content[max(0, m.start() - 200):m.end() + 200].lower()
                        if not any(w in context for w in ["cipher", "crypt", "encrypt", "decrypt", "algorithm", "aes"]):
                            continue
                    elif not _in_security_context(content, m.start(), m.end()):
                        continue
                add("medium", "crypto", f"{label}: {rel}:{ln}")


# ---------------------------------------------------------------------------
# 6. INFORMATION DISCLOSURE
# ---------------------------------------------------------------------------

DEV_CONFIG_HINT = re.compile(r"(example|sample|template|\.dev|dev\.|local|test)", re.IGNORECASE)


def check_info_disclosure():
    for fpath, content, lines in walk_files(SOURCE_EXTS | {".env", ".ini", ".cfg", ".toml", ".yaml", ".yml"}):
        rel = os.path.relpath(fpath, root)
        for pattern, label in [
            (r"res\.(?:send|json|status)\s*\([^)]*(?:err\.stack|error\.stack|stackTrace)", "Stack trace sent in response — information disclosure"),
            (r"(?:message|detail|error)\s*:\s*(?:err|error)\.(?:message|stack)", "Error details sent to client — may leak internals"),
            (r"DEBUG\s*[=:]\s*(?:True|true|1|['\"]true['\"])", "Debug mode enabled — ensure this is dev-only"),
            (r"app\.use\s*\(\s*errorHandler\s*\(\s*\{\s*[^}]*debug\s*:\s*true", "Debug error handler enabled"),
        ]:
            # Debug flags in example/dev/test configs are expected, not findings.
            if "Debug mode" in label and DEV_CONFIG_HINT.search(rel):
                continue
            for m in re.finditer(pattern, content):
                add("medium", "info-disclosure", f"{label}: {rel}:{line_num(content, m.start())}")


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

    severity_order = {"critical": 0, "high": 1, "medium": 2}
    issues.sort(key=lambda x: (severity_order.get(x[0], 3), x[1]))

    current_cat = None
    for severity, category, msg in issues[:60]:
        if category != current_cat:
            current_cat = category
            print(f"\n=== {category.upper()} ===")
        print(f"  [{severity.upper()}] {msg}")

    total = len(issues)
    critical = sum(1 for s, _, _ in issues if s == "critical")
    high = sum(1 for s, _, _ in issues if s == "high")
    print(f"\n{total} security issues found ({critical} critical, {high} high)")
    if total > 60:
        print(f"  (showing first 60 of {total})")


if __name__ == "__main__":
    main()
