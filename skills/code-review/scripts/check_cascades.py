#!/usr/bin/env python3
"""Map cascading deletes: which parent row takes which child rows with it.

This prints a *map*, never findings. Every edge here may be perfectly intended —
an order taking its line items is correct. What the map gives you is the thing no
single file states: the **transitive radius** of one delete, assembled from
declarations spread across a schema file and dozens of migrations. Reviewing the
edges is your job; measured across eight real codebases, agents find cascade
declarations unaided but almost never follow the chain past the first hop.

Two deliberately generic resolvers, so this does not become a per-ORM parser:

  1. Raw SQL — `REFERENCES parent` on the cascade line, plus the nearest enclosing
     `CREATE TABLE` / `ALTER TABLE` / `Schema::create` for the child. Covers Drizzle,
     Laravel, Rails structure.sql, Flyway, Alembic and hand-written migrations.
  2. ORM DSLs — pass one collects every model/table declaration name in the project,
     pass two resolves the other end of a cascade line to whichever *collected name*
     appears on it. No ORM syntax knowledge: this resolved 26/26 Drizzle relations,
     and works the same way for Prisma, Django, TypeORM and Doctrine.

Direction comes from one bit, because there are two families rather than N ORMs:
a foreign-key-side declaration (`references`, `foreign key`, `belongs_to`,
`ManyToOne`) makes the enclosing block the *child*; an association-side one
(`has_many`, `OneToMany`, `relationship`) makes it the *parent*.

Two details that sound minor and are not. **A name is matched across case and one
plural `s`** (`same_table`), because an association-side declaration names its
target the way the language does — Rails pairs `class Comment` with `has_many
:comments`, and without the fold the direction rule above is unreachable for every
Rails model. And **whole-line comments are skipped**, because a codebase that
documents its cascades in prose otherwise gets an edge per sentence: a subscriber,
a processor and a test case all appeared in one map as parent tables.

Reported as-is, deliberately:
  - lines whose two ends could not be resolved (printed raw — a recall failure you
    can see beats one you cannot),
  - `possible triggers`, which are unverified string matches and wrong often enough
    that you must open the file before believing one,
  - and the fact that finding nothing is not an all-clear.

Usage: python3 check_cascades.py [root]
"""
import os
import re
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import iter_source_files, read_text  # noqa: E402

EXTS = ('.sql', '.prisma', '.ts', '.js', '.mjs', '.py', '.go', '.php', '.rb',
        '.java', '.kt', '.cs', '.rs', '.xml', '.yaml', '.yml')

# The cascade must be BOUND to deletion. `ON DELETE SET NULL ON UPDATE CASCADE`
# is not a delete cascade, and Prisma migrations are full of exactly that — a
# same-line "cascade near delete" test reports a whole file of false edges.
CASCADE_DELETE = re.compile(
    r"on[\s_]*delete\w*[\s:=(\[{,]*['\"]?(?:models\.|DeleteBehavior\.)?cascade"
    r"|cascade[\s_]*on[\s_]*delete"
    r"|cascade\w*[\s.:=(\[{,]*['\"]?(?:delete|remove)"
    r"|dependent\s*:\s*:(?:destroy|delete_all)"
    r"|cascade\s*=\s*[\"']?(?:all|remove)"
    r"|orphan[_ ]?removal\s*[:=]\s*true"
    r"|delete[-_]orphan", re.I)

# `class CascadeDeleteCommand` is a name, not a cascade.
DECLARATION = re.compile(
    r"^\s*(?:(?:final|abstract|public|private|internal|export|default)\s+)*"
    r"(?:class|interface|trait|enum|struct|function|def|func)\b", re.I)

# Prose about a cascade is not a cascade. Well-commented codebases explain their
# cascades in exactly these words — "// LoadBalancerOrigin.origin_server_id is ON
# DELETE CASCADE — deleting…" — and each such line produced an edge out of whatever
# class enclosed it, so a subscriber, a processor and a test case all appeared in
# the map as parent tables. Only whole-line comments are skipped: a trailing comment
# sits on a line whose code is the declaration anyway.
# `#(?!\[)` because a PHP 8 attribute opens with `#[`, and that is exactly how
# Doctrine declares a cascade: `#[ORM\OneToMany(..., cascade: ['remove'])]`.
# Treating those as comments silently deleted every association-side edge in a
# Symfony codebase — 12 of them — while the map still looked plausible.
COMMENT_LINE = re.compile(r"^\s*(?://|#(?!\[)|--|\*/?|/\*)")

TABLE_BLOCK = re.compile(
    r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[`\"\[]?(\w+)"
    r"|ALTER\s+TABLE\s+[`\"\[]?(\w+)"
    r"|Schema::(?:create|table)\(\s*['\"](\w+)", re.I)

# Model/table names, for the ORM-DSL resolver. Kept deliberately loose: any
# declaration that introduces a name a relation could point at.
MODEL_NAME = re.compile(
    r"^\s*export\s+(?:const|default|class)\s+(\w+)"
    r"|^\s*model\s+(\w+)\s*\{"
    r"|^\s*(?:(?:final|abstract|public)\s+)*class\s+(\w+)"
    r"|^\s*(\w+)\s*=\s*(?:sqliteTable|pgTable|mysqlTable)\s*\(", re.I)

REFERENCES = re.compile(r"REFERENCES\s+[`\"\[]?(\w+)", re.I)
FK_SIDE = re.compile(r"references|foreign[\s_]*key|foreignid|constrained|belongs_to"
                     r"|many[\s_]*to[\s_]*one|@ORM\\ManyToOne", re.I)
DESTROY = re.compile(r"\bdelete\b|\bdestroy\b|\bremove\b|\bdrop\b", re.I)
TESTISH = re.compile(r"(^|/)(tests?|spec|__tests__|fixtures?|e2e|cypress)(/|$)"
                     r"|\.(test|spec)\.", re.I)
HANDLERISH = re.compile(r"(^|/)(api|routes?|controllers?|handlers?|services?|actions?"
                        r"|commands?|repositor\w+)(/|$)", re.I)


def schemaish(rel):
    return bool(re.search(r"migrat|schema", rel, re.I)) or rel.endswith(('.sql', '.prisma'))


def norm(name):
    """Identity for a table across naming conventions.

    A schema-first ORM declares the same constraint twice — `myTasksCollapsed` in
    schema.ts and `my_tasks_collapsed` in the migration it generated — and counting
    both doubles every radius. Case and underscores are the whole difference, so
    folding them makes one table one node.

    What this does NOT fold is an entity name against its table name
    (Doctrine's `Certificate` vs `certificates`): singular/plural stemming would
    merge tables that are genuinely different. Those show up as two nodes, which at
    least tells you the cascade is declared at both layers.
    """
    return name.replace('_', '').lower()


def same_table(a, b):
    """Whether two spellings name one table.

    `norm` folds case and underscores; one trailing `s` on either side covers the
    singular-class / plural-association split that an association-side declaration
    depends on. Rails writes `class Comment` and then `has_many :comments`, so
    without this the direction rule below is unreachable for every Rails model and
    the declaration lands in `unresolved`. Stemming further would start merging
    tables that are genuinely different, which is why `norm` itself refuses to.
    """
    a, b = norm(a), norm(b)
    return a == b or a == b + 's' or a + 's' == b


def loose_name(text, names, block):
    """A collected model name that some identifier on `text` refers to.

    Tried only after an exact word match fails, so a schema that spells its
    relations exactly is never subject to the looser comparison.
    """
    for token in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", text):
        for name in names:
            if name != block and same_table(name, token):
                return name
    return None


def analyze(root):
    """Resolve every cascade declaration under `root` into a parent -> child graph.

    Returns (edges, display, where, kinds, unresolved, deletes, file_count). Separated from
    the printing below so the resolvers can be tested against known schemas
    instead of by eyeballing a report — see tests/test_check_cascades.py.
    """
    files = [f for f in iter_source_files(root, EXTS)]

    # Pass 1: collect names, so the ORM resolver has a vocabulary to match against.
    names, contents = set(), {}
    for path in files:
        text = read_text(path)
        if text is None:
            continue
        rel = os.path.relpath(path, root)
        contents[rel] = text.split('\n')
        for line in contents[rel]:
            m = MODEL_NAME.match(line)
            if m:
                names.add(next(g for g in m.groups() if g))

    # Pass 2: resolve each cascade declaration into a parent -> child edge.
    edges = defaultdict(set)          # parent -> {child}, both normalised
    where, kinds = {}, {}             # (parent, child) -> "file:line" / declaration style
    display = {}                      # normalised name -> the spelling worth printing
    unresolved, deletes = [], []

    for rel, lines in contents.items():
        for i, text in enumerate(lines, 1):
            if DESTROY.search(text) and not schemaish(rel):
                deletes.append((rel, i, text.strip()[:110]))
            if (not CASCADE_DELETE.search(text) or DECLARATION.match(text)
                    or COMMENT_LINE.match(text)):
                continue

            block = None
            for j in range(i - 1, max(-1, i - 400), -1):
                m = TABLE_BLOCK.search(lines[j]) or MODEL_NAME.match(lines[j])
                if m:
                    block = next(g for g in m.groups() if g)
                    break

            ref = REFERENCES.search(text)
            other = ref.group(1) if ref else next(
                (n for n in names if n != block and re.search(rf"\b{re.escape(n)}\b", text)), None)
            if other is None and not ref:
                other = loose_name(text, names, block)

            if block and other:
                # FK side: the block declaring the column is the child. Association
                # side (has_many / OneToMany): the block IS the parent.
                p_raw, c_raw = (other, block) if (ref or FK_SIDE.search(text)) else (block, other)
                parent, child = norm(p_raw), norm(c_raw)
                # Print the spelling the database uses: prefer snake_case when the
                # same table was declared under two conventions.
                for key, raw in ((parent, p_raw), (child, c_raw)):
                    if key not in display or ('_' in raw and '_' not in display[key]):
                        display[key] = raw
                edges[parent].add(child)
                key = (parent, child)
                # Prefer a schema file over a migration: migrations are history, and a
                # later one may have changed the constraint the older one declares.
                if key not in where or (schemaish(where[key][0]) and not schemaish(rel)):
                    where[key] = (rel, i)
                    kinds[key] = 'fk' if (ref or FK_SIDE.search(text)) else 'association'
            else:
                unresolved.append((rel, i, text.strip()[:120]))

    return edges, display, where, kinds, unresolved, deletes, len(contents)


def closure(edges, start):
    """Every table reachable from `start` — the blast radius of deleting one row."""
    seen, stack = set(), [start]
    while stack:
        for child in edges.get(stack.pop(), ()):
            if child not in seen:
                seen.add(child)
                stack.append(child)
    return seen


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else '.'
    edges, display, where, kinds, unresolved, deletes, file_count = analyze(root)

    total = sum(len(v) for v in edges.values())
    print(f"CASCADE MAP — {total} delete-cascade edge(s) across {len(edges)} parent table(s), "
          f"from {file_count} files")
    print("Every edge may be intended. This is a map to review, not a list of findings.\n")

    if not total:
        print("No delete-cascade declarations resolved.\n"
              "  That is NOT an all-clear. Three ways a cascade hides from this scan:\n"
              "   - a document store (Mongo, Firestore) has no cascade syntax at all — child\n"
              "     cleanup there is application code, or missing, so read the delete handlers;\n"
              "   - a framework's own cascades live in vendor/, excluded here but not from your\n"
              "     users' data;\n"
              "   - `ON DELETE RESTRICT`/`SET NULL` block or orphan instead of cascading, which\n"
              "     moves the risk to leftover rows and files rather than removing it.")

    def shown(name):
        return display.get(name, name)

    for parent in sorted(edges, key=lambda p: (-len(closure(edges, p)), p)):
        full, direct = closure(edges, parent), edges[parent]
        indirect = sorted(shown(c) for c in full - direct)
        print(f"  {shown(parent)}  ->  {len(full)} table(s)")
        for child in sorted(direct):
            rel, line = where[(parent, child)]
            print(f"      {shown(child):<28} {rel}:{line}"
                  + ("  [association-side; verify direction]"
                     if kinds[(parent, child)] == 'association' else ""))
        if indirect:
            print(f"      via them: {', '.join(indirect)}")

        # Unverified, and wrong often enough to say so: a string match on the parent
        # name near a destruction verb. Open the file before believing one.
        pat = re.compile(rf"\b{re.escape(parent)}s?\b", re.I)
        hits = sorted((d for d in deletes if pat.search(d[2])),
                      key=lambda d: (bool(TESTISH.search(d[0])),
                                     not HANDLERISH.search(d[0]), len(d[0])))
        for rel, line, snippet in hits[:2]:
            print(f"      possible trigger (unverified): {rel}:{line}  {snippet}")
        print()

    if unresolved:
        print(f"UNRESOLVED — {len(unresolved)} cascade declaration(s) whose two ends this scan "
              f"could not name. Read them by hand; they are edges too:")
        for rel, line, text in unresolved[:25]:
            print(f"  {rel}:{line}  {text}")
        if len(unresolved) > 25:
            print(f"  ... and {len(unresolved) - 25} more")


if __name__ == '__main__':
    main()
