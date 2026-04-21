#!/usr/bin/env bash
set -euo pipefail

_log() { echo "[$1] $(basename "$0" .sh): $2" >&2; }

command -v jq >/dev/null 2>&1 || { _log error "jq missing"; exit 4; }

TAGS="" TYPES="" SCOPE="" SINCE="" UNTIL="" OUT="stdout" BASE_DIR=".honne"
while [[ $# -gt 0 ]]; do
  case $1 in
    --tag)        TAGS="$2"; shift 2;;
    --tags)       TAGS="$2"; shift 2;;
    --type)       TYPES="$2"; shift 2;;
    --types)      TYPES="$2"; shift 2;;
    --scope)      SCOPE="$2"; shift 2;;
    --since)      SINCE="$2"; shift 2;;
    --until)      UNTIL="$2"; shift 2;;
    --out)        OUT="$2"; shift 2;;
    --base-dir)   BASE_DIR="$2"; shift 2;;
    *) _log error "unknown arg: $1"; exit 1;;
  esac
done

ASSET_DIR="$BASE_DIR/assets"
[[ ! -d "$ASSET_DIR" ]] && { echo "[]"; exit 2; }

RESULT="[]"
for f in "$ASSET_DIR"/*.jsonl; do
  [[ ! -f "$f" ]] && continue
  while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    OBJ=$(echo "$line" | jq -c '.' 2>/dev/null) || { _log warn "malformed line"; continue; }

    # Apply filters
    MATCH=1
    [[ -n "$TAGS" ]] && ! echo "$OBJ" | jq -e --arg ax "$TAGS" '.axis == $ax' >/dev/null 2>&1 && MATCH=0
    [[ -n "$SCOPE" ]] && ! echo "$OBJ" | jq -e --arg sc "$SCOPE" '.scope == $sc' >/dev/null 2>&1 && MATCH=0
    [[ -n "$SINCE" ]] && ! echo "$OBJ" | jq -e --arg s "$SINCE" '.recorded_at >= $s' >/dev/null 2>&1 && MATCH=0
    [[ -n "$UNTIL" ]] && ! echo "$OBJ" | jq -e --arg u "$UNTIL" '.recorded_at <= $u' >/dev/null 2>&1 && MATCH=0

    [[ "$MATCH" -eq 1 ]] && RESULT=$(echo "$RESULT" | jq --argjson o "$OBJ" '. + [$o]')
  done < "$f"
done

if [[ "$OUT" == "stdout" ]]; then
  echo "$RESULT"
else
  mkdir -p "$(dirname "$OUT")"
  echo "$RESULT" > "$OUT"
  _log info "queried assets → $OUT"
fi

[[ $(echo "$RESULT" | jq 'length') -eq 0 ]] && exit 2
exit 0
