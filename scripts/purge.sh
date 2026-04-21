#!/usr/bin/env bash
set -euo pipefail

_log() { echo "[$1] $(basename "$0" .sh): $2" >&2; }

MODE="" FORCE=0
while [[ $# -gt 0 ]]; do
  case $1 in
    --all)          MODE="all"; shift;;
    --keep-assets)  MODE="keep-assets"; shift;;
    --force)        FORCE=1; shift;;
    *) _log error "unknown arg: $1"; exit 1;;
  esac
done

[[ -z "$MODE" ]] && { _log error "required: --all or --keep-assets"; exit 1; }
[[ ! -d ".honne" ]] && { echo "Nothing to purge."; exit 0; }

# Check symlink
[[ -L ".honne" ]] && { _log error ".honne is a symlink — refusing to follow"; exit 1; }

if [[ "$FORCE" -eq 0 ]]; then
  echo "This will delete:"
  [[ "$MODE" == "all" ]] && echo "  .honne/cache/ (scan cache, session index)"
  [[ "$MODE" == "all" ]] && echo "  .honne/persona.json (current profile snapshot)"
  [[ "$MODE" == "all" ]] && echo "  .honne/assets/*.jsonl (longitudinal claims/rejections/evolution)"
  [[ "$MODE" == "keep-assets" ]] && echo "  .honne/cache/ (scan cache, session index)"
  read -p "Type DELETE to confirm: " CONFIRM
  [[ "$CONFIRM" != "DELETE" ]] && { _log info "purge: cancelled"; exit 1; }
fi

BEFORE=$(find .honne -type f | wc -l || echo 0)
BYTES=$(du -sh .honne 2>/dev/null | cut -f1 || echo "0")

if [[ "$MODE" == "all" ]]; then
  rm -rf .honne
else
  rm -rf .honne/cache
fi

echo "Purged $BEFORE files ($BYTES)."
exit 0
