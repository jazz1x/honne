#!/usr/bin/env bash
# scripts/start-impl.sh — T0 wrapper (see Appendix F)
set -e
ORIG_BRANCH=$(git branch --show-current)
mkdir -p .honne
echo "$ORIG_BRANCH" > .honne/orig-branch

if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "uncommitted changes in $ORIG_BRANCH — commit or stash first" >&2
  exit 1
fi

if git show-ref --quiet refs/heads/feat/haiku-determinism; then
  echo "branch feat/haiku-determinism already exists" >&2
  exit 1
fi

git switch -c feat/haiku-determinism
