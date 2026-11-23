#!/usr/bin/env bash
# Install ScaleCommerce skills by symlinking them from this clone.
#
#   ./install.sh                     all skills
#   ./install.sh code-review ...     only the named ones
#
# Layout it produces (the same one `npx skills add -g` used, minus the copy):
#   ~/.agents/skills/<name>  -> <this repo>/skills/<name>     (Codex and others read here)
#   ~/.claude/skills/<name>  -> ../../.agents/skills/<name>   (Claude Code)
#
# Because everything is a symlink into the clone, `git pull` is the update;
# re-run this script only when a skill is added or removed.
set -euo pipefail

REPO="$(cd "$(dirname "$0")" && pwd -P)"
SRC="$REPO/skills"
AGENTS="$HOME/.agents/skills"
CLAUDE="$HOME/.claude/skills"
BACKUP="$HOME/.agents/skills-backup-$(date +%Y%m%d-%H%M%S)"

case "${1:-}" in
  -h|--help) sed -n '2,12p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
esac

if [ $# -gt 0 ]; then
  names=("$@")
else
  names=()
  for d in "$SRC"/*/; do
    [ -f "$d/SKILL.md" ] && names+=("$(basename "$d")")
  done
fi

mkdir -p "$AGENTS" "$CLAUDE"

for n in "${names[@]}"; do
  if [ ! -f "$SRC/$n/SKILL.md" ]; then
    echo "skip  $n: no such skill in $SRC" >&2
    continue
  fi

  # A real directory here is a copy left by `npx skills add`. Move it aside
  # rather than deleting it, in case it held local edits.
  if [ -e "$AGENTS/$n" ] && [ ! -L "$AGENTS/$n" ]; then
    mkdir -p "$BACKUP"
    mv "$AGENTS/$n" "$BACKUP/$n"
    echo "moved old copy of $n to $BACKUP/"
  fi
  if [ -e "$CLAUDE/$n" ] && [ ! -L "$CLAUDE/$n" ]; then
    mkdir -p "$BACKUP/claude"
    mv "$CLAUDE/$n" "$BACKUP/claude/$n"
    echo "moved old copy of $n to $BACKUP/claude/"
  fi

  ln -sfn "$SRC/$n" "$AGENTS/$n"
  ln -sfn "../../.agents/skills/$n" "$CLAUDE/$n"
  echo "ok    $n"
done

# Skills deleted from the repo leave dangling links behind; remove only those
# that point into this clone.
for link in "$AGENTS"/*; do
  if [ -L "$link" ] && [ ! -e "$link" ]; then
    case "$(readlink "$link")" in
      "$SRC"/*)
        n="$(basename "$link")"
        rm "$link"
        [ -L "$CLAUDE/$n" ] && [ ! -e "$CLAUDE/$n" ] && rm "$CLAUDE/$n"
        echo "removed $n (no longer in the repo)"
        ;;
    esac
  fi
done
