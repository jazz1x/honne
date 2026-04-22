#!/usr/bin/env bash
# scripts/decline-fixtures.sh — human-only HITL rejection (TTY guard)
set -e
if [ "${HONNE_HUMAN_APPROVE:-}" != "1" ] && [ ! -t 0 ]; then
  echo "decline-fixtures: require TTY or HONNE_HUMAN_APPROVE=1 (human-only)" >&2
  exit 10
fi
[ -d tests/fixtures/expected.pending ] || { echo "no pending"; exit 1; }
if [ -t 0 ]; then
  read -r -p "Decline all pending fixtures? (yes/no): " ans
  [ "$ans" = "yes" ] || { echo "aborted"; exit 2; }
fi
rm -rf tests/fixtures/expected.pending
rm -f .honne/impl-gate.lock
echo "declined"
