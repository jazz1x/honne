#!/usr/bin/env bash
command -v python3 >/dev/null || { echo "python3 required" >&2; exit 4; }
exec "$(dirname "${BASH_SOURCE[0]}")/honne" detect-recurrence "$@"
