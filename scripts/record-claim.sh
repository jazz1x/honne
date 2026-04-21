#!/usr/bin/env bash
set -euo pipefail

_log() { echo "[$1] $(basename "$0" .sh): $2" >&2; }

command -v jq >/dev/null 2>&1 || { _log error "jq missing"; exit 4; }

TYPE="" AXIS="" SCOPE="" CLAIM="" SUPPORT_COUNT=0 QUOTES_JSON="" QUOTES_FILE="" PRIOR_ID="" OUT=""
while [[ $# -gt 0 ]]; do
  case $1 in
    --type)           TYPE="$2"; shift 2;;
    --axis)           AXIS="$2"; shift 2;;
    --scope)          SCOPE="$2"; shift 2;;
    --claim)          CLAIM="$2"; shift 2;;
    --support-count)  SUPPORT_COUNT="$2"; shift 2;;
    --quotes-json)    QUOTES_JSON="$2"; shift 2;;
    --quotes-file)    QUOTES_FILE="$2"; shift 2;;
    --prior-id)       PRIOR_ID="$2"; shift 2;;
    --out)            OUT="$2"; shift 2;;
    *) _log error "unknown arg: $1"; exit 1;;
  esac
done

[[ -z "$TYPE" || -z "$AXIS" || -z "$SCOPE" || -z "$CLAIM" || -z "$OUT" ]] && \
  { _log error "required: --type --axis --scope --claim --out"; exit 1; }

QUOTES=""
if [[ -n "$QUOTES_FILE" && -f "$QUOTES_FILE" ]]; then
  QUOTES=$(cat "$QUOTES_FILE")
elif [[ -n "$QUOTES_JSON" ]]; then
  QUOTES="$QUOTES_JSON"
else
  QUOTES="[]"
fi

RECORD_ID="${TYPE}-$(date +%Y-%m-%d)-001"
RECORDED_AT=$(date -u +%FT%TZ)

mkdir -p "$(dirname "$OUT")"
TMP=$(mktemp)

ASSET=$(jq -n \
  --arg id "$RECORD_ID" \
  --arg t "$TYPE" \
  --arg ax "$AXIS" \
  --arg ra "$RECORDED_AT" \
  --arg sc "$SCOPE" \
  --arg cl "$CLAIM" \
  --argjson supp "$SUPPORT_COUNT" \
  --argjson q "$QUOTES" \
  --arg pi "${PRIOR_ID:-null}" \
  '{id: $id, type: $t, axis: $ax, recorded_at: $ra, scope: $sc, claim: $cl, support_count: $supp, quotes: $q, prior_id: ($pi | if . == "null" then null else . end), schema_version: 1}')

if [[ -f "$OUT" ]]; then
  cat "$OUT" >> "$TMP"
  echo "$ASSET" >> "$TMP"
  mv "$TMP" "$OUT"
else
  echo "$ASSET" > "$OUT"
  rm -f "$TMP"
fi

_log info "recorded $TYPE → $OUT"
exit 0
