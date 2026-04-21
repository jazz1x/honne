#!/usr/bin/env bash
set -euo pipefail

_log() { echo "[$1] $(basename "$0" .sh): $2" >&2; }

command -v jq >/dev/null 2>&1 || { _log error "jq missing"; exit 4; }

INPUT="" MIN_SESSIONS=3 OUT=""
while [[ $# -gt 0 ]]; do
  case $1 in
    --input)       INPUT="$2"; shift 2;;
    --min-sessions) MIN_SESSIONS="$2"; shift 2;;
    --out)         OUT="$2"; shift 2;;
    *) _log error "unknown arg: $1"; exit 1;;
  esac
done
[[ -z "$INPUT" || -z "$OUT" ]] && { _log error "required: --input --out"; exit 1; }
[[ ! -f "$INPUT" ]] && { _log error "input file not found: $INPUT"; exit 1; }

RESULT=$(jq -r '.sessions[] | {id: .session_id, text: .messages | map(.text) | join(" ")}' "$INPUT" | \
  jq -s 'map(select(.text | length > 0))' | jq -c '[.[] | {session_id: .id, ngrams: (.text | split(" ") | combinations(3) | map(join(" ")))}] | group_by(.session_id) | map({concept: .[0].ngrams[0], sessions: map(.session_id), count: (. | length)}) | select(.count >= '"$MIN_SESSIONS"')' 2>/dev/null || echo "[]")

mkdir -p "$(dirname "$OUT")"
echo "$RESULT" > "$OUT"
_log info "detected recurrence → $OUT"
exit 0
