#!/usr/bin/env bash
# scripts/pre-commit.sh — shim → python3 -m honne_py precommit "$@"
command -v python3 >/dev/null || { echo "python3 required" >&2; exit 4; }
PYTHONPATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd):${PYTHONPATH:-}" exec python3 -m honne_py precommit "$@"
