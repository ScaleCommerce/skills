#!/usr/bin/env bash
# Update ScaleCommerce skills: pull this clone, then re-link.
#
#   ./update.sh
#
# Installed skills are symlinks into this clone, so the pull alone updates
# them. Re-running install.sh picks up skills that were added or removed.
set -euo pipefail

REPO="$(cd "$(dirname "$0")" && pwd -P)"
cd "$REPO"

before="$(git rev-parse HEAD)"
git pull --ff-only --quiet
after="$(git rev-parse HEAD)"

if [ "$before" = "$after" ]; then
  echo "Already up to date ($(git rev-parse --short HEAD))."
else
  echo "Updated $(git rev-parse --short "$before")..$(git rev-parse --short "$after"):"
  git log --format='  %h %s' "$before..$after" -- skills/
  echo
fi

"$REPO/install.sh"
