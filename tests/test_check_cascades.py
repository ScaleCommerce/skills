#!/usr/bin/env python3
"""Regression fixtures for code-review/scripts/check_cascades.py.

Run: python3 tests/test_check_cascades.py

The script resolves cascade declarations two ways — raw SQL via `REFERENCES`, and
ORM DSLs by matching the other end of the line against model names collected in a
first pass — and neither has an obvious right answer to eyeball. It was originally
verified by hand against four repos, which proved it worked *that day* and pinned
nothing.

Each case is a schema shape whose graph is known. Two of them are bugs the earlier
drafts had: `ON DELETE RESTRICT ON UPDATE CASCADE` counted as a delete cascade (a
Prisma migration is full of those, so a codebase with zero cascades reported
dozens), and a table declared in both camelCase and snake_case counted twice,
inflating every radius it appeared in.

Fixtures write real files because the script walks a directory; each gets its own
temp tree so a case can never see another's schema.
"""
import os
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "skills", "code-review", "scripts"))
import check_cascades as cc  # noqa: E402

FAILURES = []


def check(label, got, want):
    if got == want:
        print(f"  ok   {label}: {got}")
    else:
        print(f"  FAIL {label}: got {got!r}, want {want!r}")
        FAILURES.append(label)


def graph(files):
    """{parent: {children}} plus display names and unresolved lines, for a temp tree."""
    with tempfile.TemporaryDirectory() as tmp:
        for name, body in files.items():
            path = os.path.join(tmp, name)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as fh:
                fh.write(body)
        edges, display, _where, kinds, unresolved, _deletes, _n = cc.analyze(tmp)
        return {
            "edges": {p: set(c) for p, c in edges.items()},
            "display": dict(display),
            "kinds": dict(kinds),
            "unresolved": [u[2] for u in unresolved],
            "radius": {p: len(cc.closure(edges, p)) for p in edges},
        }


print("Raw SQL — REFERENCES plus the enclosing CREATE TABLE")
g = graph({"migrations/0001_init.sql": """
CREATE TABLE `statuses` (
  `id` text PRIMARY KEY NOT NULL
);
CREATE TABLE `cards` (
  `id` integer PRIMARY KEY NOT NULL,
  `status_id` text NOT NULL,
  FOREIGN KEY (`status_id`) REFERENCES `statuses`(`id`) ON DELETE CASCADE
);
"""})
check("sql edge", g["edges"], {"statuses": {"cards"}})
check("sql direction is fk-side", g["kinds"][("statuses", "cards")], "fk")

print("\nON UPDATE CASCADE is not a delete cascade — the bug that reported dozens of phantom edges")
g = graph({"migrations/0002_fks.sql": """
CREATE TABLE `Video` (
  `library_id` integer NOT NULL,
  CONSTRAINT `fk_lib` FOREIGN KEY (`library_id`) REFERENCES `Library`(`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_pkg` FOREIGN KEY (`package_id`) REFERENCES `Package`(`id`) ON DELETE SET NULL ON UPDATE CASCADE
);
"""})
check("no edges from ON UPDATE CASCADE", g["edges"], {})
check("and nothing left dangling as unresolved", g["unresolved"], [])

print("\nORM DSL — the other end resolves against names collected in pass one")
g = graph({"db/schema.ts": """
export const statuses = sqliteTable('statuses', {
  id: text('id').primaryKey()
})

export const cards = sqliteTable('cards', {
  id: integer('id').primaryKey(),
  statusId: text('status_id').notNull().references(() => statuses.id, { onDelete: 'cascade' })
})
"""})
check("drizzle edge", g["edges"], {"statuses": {"cards"}})

g = graph({"schema.prisma": """
model User {
  id    String @id
  posts Post[]
}

model Post {
  id       String @id
  authorId String
  author   User   @relation(fields: [authorId], references: [id], onDelete: Cascade)
}
"""})
check("prisma edge", g["edges"], {"user": {"post"}})

g = graph({"blog/models.py": """
class Author(models.Model):
    name = models.CharField(max_length=200)


class Book(models.Model):
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
"""})
check("django edge", g["edges"], {"author": {"book"}})

print("\nTransitive radius — the number that exists in no single file")
g = graph({"migrations/0003_chain.sql": """
CREATE TABLE `projects` (`id` text PRIMARY KEY);
CREATE TABLE `cards` (
  `project_id` text,
  FOREIGN KEY (`project_id`) REFERENCES `projects`(`id`) ON DELETE CASCADE
);
CREATE TABLE `comments` (
  `card_id` integer,
  FOREIGN KEY (`card_id`) REFERENCES `cards`(`id`) ON DELETE CASCADE
);
"""})
check("chain edges", g["edges"], {"projects": {"cards"}, "cards": {"comments"}})
check("projects radius counts the grandchild", g["radius"]["projects"], 2)
check("cards radius", g["radius"]["cards"], 1)

print("\nOne table, two naming conventions — must not count twice")
g = graph({
    "db/schema.ts": """
export const users = sqliteTable('users', { id: text('id').primaryKey() })

export const myTasksCollapsed = sqliteTable('my_tasks_collapsed', {
  userId: text('user_id').references(() => users.id, { onDelete: 'cascade' })
})
""",
    "db/migrations/0004.sql": """
CREATE TABLE `my_tasks_collapsed` (
  `user_id` text,
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
);
""",
})
check("same table folded to one node", g["edges"], {"users": {"mytaskscollapsed"}})
check("radius is 1, not 2", g["radius"]["users"], 1)
check("displayed with the database's spelling", g["display"]["mytaskscollapsed"], "my_tasks_collapsed")

print("\nA declaration whose ends cannot be named is reported, never dropped")
g = graph({"db/orphan.sql": """
ALTER TABLE something ADD CONSTRAINT fk FOREIGN KEY (x_id) ON DELETE CASCADE;
"""})
check("no invented edge", g["edges"], {})
check("surfaced as unresolved", len(g["unresolved"]), 1)

print("\nAssociation-side declaration — the declaring class is the PARENT")
g = graph({"app/models.rb": """
class Post < ApplicationRecord
  has_many :comments, dependent: :destroy
end

class Comment < ApplicationRecord
  belongs_to :post
end
"""})
# `class Comment` against `has_many :comments` needs case and one plural `s` folded,
# or the direction rule below is unreachable and every Rails model lands unresolved.
check("rails edge", g["edges"], {"post": {"comment"}})
check("direction is association-side", g["kinds"][("post", "comment")], "association")
check("nothing unresolved", g["unresolved"], [])

print("\nProse about a cascade is not a cascade")
g = graph({
    "src/Listener.php": """
class ZoneConfigSyncSubscriber
{
    public function onFlush(): void
    {
        // Zones are SQL-cascade-removed by ON DELETE CASCADE when an
        // Organization is deleted — Doctrine never fires per-zone events.
    }
}
""",
    "src/Doc.php": """
class Notes
{
    /**
     * LoadBalancerOrigin.origin_server_id is ON DELETE CASCADE — deleting
     * an origin server takes its rows with it.
     */
}
""",
    "db/notes.sql": """
-- user_id is ON DELETE CASCADE, deliberately
CREATE TABLE `plain` (`id` text PRIMARY KEY);
""",
})
check("comments produce no edges", g["edges"], {})
check("and are not reported as unresolved", g["unresolved"], [])

print("\nBut a PHP 8 attribute is not a comment, even though it starts with #")
g = graph({"src/Entity/Certificate.php": """
class Certificate
{
    #[ORM\\OneToMany(mappedBy: 'certificate', targetEntity: CertificateSan::class, cascade: ['persist', 'remove'], orphanRemoval: true)]
    private Collection $sans;
}

class CertificateSan
{
}
"""})
# Skipping `#` wholesale deleted every Doctrine association in a Symfony codebase
# while the map still looked plausible — 12 edges, silently.
check("doctrine attribute edge", g["edges"], {"certificate": {"certificatesan"}})

print("\nA class named CascadeDelete is a name, not a cascade")
g = graph({"src/CascadeDeleteCommand.php": """
class CascadeDeleteCommand extends DeleteCommand
{
}
"""})
check("no edge from a class name", g["edges"], {})
check("not reported as unresolved either", g["unresolved"], [])

print()
if FAILURES:
    print(f"{len(FAILURES)} failing: {', '.join(FAILURES)}")
    sys.exit(1)
print("all cascade fixtures pass")
