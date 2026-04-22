#!/usr/bin/env bash
# tests/run.sh — run the full honne test suite (pytest + bats).
# Both runners must pass for this script to exit 0.
set -euo pipefail

# impl-gate check — abort if pending human approval
if [ -f .honne/impl-gate.lock ]; then
  cat .honne/impl-gate.lock >&2
  echo "tests skipped: impl-gate.lock present" >&2
  exit 100
fi

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

fail() { echo -e "${RED}✗ $1${NC}" >&2; exit 1; }
pass() { echo -e "${GREEN}✓ $1${NC}"; }

echo "==> pytest (python helpers)"
if command -v pytest >/dev/null 2>&1; then
  pytest tests/ -q
elif command -v python3 >/dev/null 2>&1; then
  python3 -m pytest tests/ -q
else
  fail "python3/pytest not found"
fi
pass "pytest"

echo ""
echo "==> bats (shell + manifest)"
if ! command -v bats >/dev/null 2>&1; then
  fail "bats not installed — brew install bats-core (macOS) / apt install bats (linux)"
fi
bats tests/
pass "bats"

echo ""
pass "all tests passed"
