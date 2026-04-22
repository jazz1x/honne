#!/usr/bin/env bash
# scripts/scan-transcripts.sh — shim → python3 -m honne_py scan "$@"
command -v python3 >/dev/null || { echo "python3 required" >&2; exit 4; }
PYTHONPATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd):${PYTHONPATH:-}" exec python3 -m honne_py scan "$@"
