#!/usr/bin/env bash
set -euo pipefail
trap 'exit 0' ERR

_sha256() {
  if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1"
  else shasum -a 256 "$1"
  fi
}

JSONL="" OUT=""
while [[ $# -gt 0 ]]; do
  case $1 in
    --jsonl) JSONL="$2"; shift 2;;
    --out)   OUT="$2"; shift 2;;
    *) shift;;
  esac
done

[[ -f "$JSONL" ]] || exit 0
[[ -z "$OUT" ]] && exit 0

SESSION_ID=$(jq -r '.sessionId // empty' < "$JSONL" 2>/dev/null | head -1) || exit 0
[[ -z "$SESSION_ID" ]] && exit 0

SHA=$(_sha256 "$JSONL" | cut -d' ' -f1)

# Idempotent check
if [[ -f "$OUT" ]]; then
  if jq -e --arg s "$SHA" '.sessions[] | select(.sha256 == $s)' "$OUT" > /dev/null 2>&1; then
    exit 0
  fi
fi

STARTED=$(jq -r '.ts // empty' < "$JSONL" 2>/dev/null | head -1 || echo "")
ENDED=$(tail -1 "$JSONL" 2>/dev/null | jq -r '.ts // empty' 2>/dev/null || echo "")
MSG_COUNT=$(wc -l < "$JSONL" 2>/dev/null || echo "0")
PROJECT_PATH=$(jq -r '.cwd // empty' < "$JSONL" 2>/dev/null | head -1 || echo "")

mkdir -p "$(dirname "$OUT")"
TMP=$(mktemp)

if [[ -f "$OUT" ]]; then
  jq --arg id "$SESSION_ID" --arg pp "$PROJECT_PATH" --arg sa "$STARTED" \
     --arg ea "$ENDED" --argjson mc "$MSG_COUNT" --arg sh "$SHA" \
    '.sessions += [{session_id: $id, project_path: $pp, started_at: $sa, ended_at: $ea, message_count: $mc, sha256: $sh}]' \
    "$OUT" > "$TMP" 2>/dev/null || { rm -f "$TMP"; exit 0; }
else
  jq -n --arg id "$SESSION_ID" --arg pp "$PROJECT_PATH" --arg sa "$STARTED" \
     --arg ea "$ENDED" --argjson mc "$MSG_COUNT" --arg sh "$SHA" \
    '{version: 1, sessions: [{session_id: $id, project_path: $pp, started_at: $sa, ended_at: $ea, message_count: $mc, sha256: $sh}]}' \
    > "$TMP" 2>/dev/null || { rm -f "$TMP"; exit 0; }
fi

mv "$TMP" "$OUT" 2>/dev/null || exit 0
exit 0
