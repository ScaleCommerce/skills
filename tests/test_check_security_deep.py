#!/usr/bin/env python3
"""Regression fixtures for code-review/scripts/check_security_deep.py — Symfony/Doctrine/Twig.

Run: python3 tests/test_check_security_deep.py
Against another copy of the script (e.g. the pre-fix one, as a counter-check):
    SECURITY_SCRIPT=/path/to/check_security_deep.py python3 tests/test_check_security_deep.py

The scanner's PHP patterns targeted pre-framework PHP (`mysql_query`, `$_GET`,
`shell_exec`), so on a Symfony codebase it found nothing — and then printed
"No security issues detected.", a clearance from an instrument that never touched
the subject. Cases A1–A4 are the four shapes it missed (brief 282, 17.11.2026);
each was confirmed missed by running the script, not by reading it. The
non-matches are the parameterised forms of the same calls: a scanner that flags
those buries the real ones, which is the failure the docstring of the script
warns about.

The script reads `sys.argv` at module level and keeps its findings in a global
list, so it is run as a subprocess against a temp tree per case rather than
imported. That also tests what a reviewer actually sees: the printed report.
"""
import os
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.environ.get("SECURITY_SCRIPT") or os.path.join(
    REPO, "skills", "code-review", "scripts", "check_security_deep.py")

FAILURES = []


def check(label, ok, detail=""):
    if ok:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}" + (f"\n         {detail}" if detail else ""))
        FAILURES.append(label)


def scan(files):
    """Printed report for a temp tree holding `files` ({relpath: body})."""
    with tempfile.TemporaryDirectory() as tmp:
        for name, body in files.items():
            path = os.path.join(tmp, name)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as fh:
                fh.write(body)
        result = subprocess.run([sys.executable, SCRIPT, tmp],
                                capture_output=True, text=True, timeout=60)
        return result.returncode, result.stdout + result.stderr


def finding_lines(out):
    return [l for l in out.splitlines() if l.lstrip().startswith("[")]


def hit(out, where, severity=None):
    """True if some finding line names `where` (and has `severity`, if given)."""
    for line in finding_lines(out):
        if where in line and (severity is None or f"[{severity.upper()}]" in line):
            return True
    return False


def php(body):
    return "<?php\n\nclass Fixture\n{\n    public function run()\n    {\n" + body + "\n    }\n}\n"


# ---------------------------------------------------------------------------
# Must be reported — A1–A4 from brief 282 §0, all missed by 6e6d6ba.
# The call sits on line 7 of every PHP fixture (php() adds six lines above it).
# ---------------------------------------------------------------------------
print("A1 — DBAL concatenation with a request value (real SQL injection) → high")
_, out = scan({"src/A1.php": php(
    '        $conn->executeQuery("SELECT * FROM x WHERE id = " . $request->query->get("id"));')})
check("A1 reported as high at src/A1.php:7", hit(out, "A1.php:7", "high"), out)

print("A2 — DQL concatenation, no visible request source → medium")
_, out = scan({"src/A2.php": php(
    "        $em->createQuery('SELECT u FROM User u WHERE u.name = ' . $name);")})
check("A2 reported as medium at src/A2.php:7", hit(out, "A2.php:7", "medium"), out)

print("A3 — DBAL interpolation in a double-quoted string → medium")
_, out = scan({"src/A3.php": php(
    '        $rows = $conn->fetchAllAssociative("SELECT id, templateData FROM {$table}");')})
check("A3 reported as medium at src/A3.php:7", hit(out, "A3.php:7", "medium"), out)

print("A4 — |raw in a .twig template → reported")
_, out = scan({"templates/a4.html.twig": "<div>\n  {{ block.text|raw }}\n</div>\n"})
check("A4 reported for a4.html.twig", hit(out, "a4.html.twig"), out)

# ---------------------------------------------------------------------------
# Must NOT be reported — the parameterised forms of the same calls (brief 282 §2.1).
# Without these the scanner is free to flag every query in a Symfony app.
# ---------------------------------------------------------------------------
NON_HITS = {
    "src/N1.php": php("        $conn->executeQuery('SELECT * FROM x WHERE id = :id', ['id' => $id]);"),
    "src/N2.php": php("        $em->createQuery('SELECT u FROM User u WHERE u.name = :name')->setParameter('name', $name);"),
    "src/N3.php": php("        $qb->select('u')->from(User::class, 'u')\n"
                      "            ->where('u.id = :id')\n"
                      "            ->andWhere($qb->expr()->eq('u.active', ':active'))\n"
                      "            ->setParameter('id', $id)->setParameter('active', true);"),
    # The concatenation is in the *parameters*, not the SQL — shape taken from
    # sulu-scale.sc MoveTreeNestingCommand.php:176 minus its table interpolation.
    "src/N4.php": php("        $conn->fetchOne('SELECT id FROM t WHERE data LIKE ? LIMIT 1', ['%' . $uuid . '%']);"),
    "templates/n5.html.twig": "<p>{{ text }}</p>\n<p>{{ text|e('html') }}</p>\n",
    "templates/n6.html.twig": "{# {{ block.text|raw }} — disabled #}\n"
                              "{#\n   multi-line comment: {{ legacy|raw }}\n#}\n<p>{{ text }}</p>\n",
}
print("Non-matches — parameterised queries, escaped output, |raw inside {# … #}")
_, out = scan(NON_HITS)
for name in NON_HITS:
    base = os.path.basename(name)
    check(f"{base} not reported", not hit(out, base),
          "\n         ".join(l for l in finding_lines(out) if base in l))

# ---------------------------------------------------------------------------
# Output (brief 282 §2.3–2.4). New behaviour, so these are also red on 6e6d6ba.
# ---------------------------------------------------------------------------
print("Twig findings are summarised per file, not one line per |raw")
_, out = scan({"templates/many.html.twig": "".join(f"<p>{{{{ f{i}|raw }}}}</p>\n" for i in range(7))
               + "{% autoescape false %}{{ x }}{% endautoescape %}\n"})
lines = [l for l in finding_lines(out) if "many.html.twig" in l]
check("exactly one finding line for many.html.twig", len(lines) == 1, "\n         ".join(lines) or out)
check("it counts 7× |raw", bool(lines) and "7× |raw" in lines[0], lines[0] if lines else out)
check("it counts the autoescape block", bool(lines) and "autoescape false" in lines[0], lines[0] if lines else out)

print("An empty result is not printed as a clearance, and says what was scanned")
code, out = scan({"src/Clean.php": php("        return 1;"), "templates/clean.html.twig": "{{ x }}\n"})
check("exit code stays 0", code == 0, out)
check("no 'No security issues detected.'", "No security issues detected" not in out, out)
check("coverage names .php with its file count", ".php: 1" in out, out)
check("coverage names .twig with its file count", ".twig: 1" in out, out)

print("File types the scanner cannot read are named as not covered")
_, out = scan({"src/App.kt": "fun main() {}\n", "src/ok.py": "x = 1\n"})
check("a .kt file is reported as not covered", "not covered" in out and ".kt" in out, out)

print("A capped report still totals every category")
many = {f"src/M{i}.php": php('        $conn->fetchOne("SELECT 1 FROM {$t}");') for i in range(70)}
many["templates/t.html.twig"] = "{{ a|raw }}\n"
_, out = scan(many)
check("injection total is 70 even though only 60 lines are shown", "injection: 70" in out, out[-600:])
check("the twig category is totalled although it was cut off", "template-xss: 1" in out, out[-600:])

print()
if FAILURES:
    print(f"{len(FAILURES)} failing: {', '.join(FAILURES)}")
    sys.exit(1)
print("all ok")
