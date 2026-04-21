#!/usr/bin/env bash
set -euo pipefail

_log() { echo "[$1] $(basename "$0" .sh): $2" >&2; }

command -v jq >/dev/null 2>&1 || { _log error "jq missing"; exit 4; }

INPUT="" CLAIM="" MAX=5 OUT="stdout"
while [[ $# -gt 0 ]]; do
  case $1 in
    --input)  INPUT="$2"; shift 2;;
    --claim)  CLAIM="$2"; shift 2;;
    --max)    MAX="$2"; shift 2;;
    --out)    OUT="$2"; shift 2;;
    *) _log error "unknown arg: $1"; exit 1;;
  esac
done
[[ -z "$INPUT" || -z "$CLAIM" ]] && { _log error "required: --input --claim"; exit 1; }
[[ ! -f "$INPUT" ]] && { _log error "input file not found: $INPUT"; exit 1; }

RESULT=$(jq -r '.sessions[] | {session_id, messages: .messages[]}' "$INPUT" | \
  jq -s 'map(select(.messages.text | contains("'"$CLAIM"'")))' | \
  jq -c 'map({session_id: .session_id, ts: .messages.ts, text: .messages.text}) | sort_by(.ts) | reverse | .[0:'"$MAX"']' 2>/dev/null || echo "[]")

if [[ "$OUT" == "stdout" ]]; then
  echo "$RESULT"
else
  mkdir -p "$(dirname "$OUT")"
  echo "$RESULT" > "$OUT"
  _log info "gathered evidence → $OUT"
fi
exit 0
