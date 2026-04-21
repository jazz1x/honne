#!/usr/bin/env bash
# scripts/extract-lexicon.sh — lexicon axis extraction (axis 1)
# Exit: 0 success, 1 invalid args, 2 empty result, 4 tool missing
set -euo pipefail

_log() { echo "[$1] $(basename "$0" .sh): $2" >&2; }
_debug() { [[ "${HONNE_DEBUG:-0}" == "1" ]] && _log debug "$1" || :; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ---- Pre-flight ----
command -v jq >/dev/null 2>&1 || { _log error "jq missing (install: brew install jq)"; exit 4; }

# Tokenize backend: python3 primary, rg fallback
TOKEN_BACKEND=""
if command -v python3 >/dev/null 2>&1; then
  TOKEN_BACKEND="python3"
elif command -v rg >/dev/null 2>&1; then
  TOKEN_BACKEND="rg"
else
  _log error "need python3 or ripgrep (install: brew install python OR brew install ripgrep)"
  exit 4
fi
_debug "tokenize backend: $TOKEN_BACKEND"

# ---- Args ----
INPUT="" TOP=50 MIN_SESSIONS=2 OUT=""
while [[ $# -gt 0 ]]; do
  case $1 in
    --input)        INPUT="$2"; shift 2;;
    --top)          TOP="$2"; shift 2;;
    --min-sessions) MIN_SESSIONS="$2"; shift 2;;
    --out)          OUT="$2"; shift 2;;
    *) _log error "unknown arg: $1"; exit 1;;
  esac
done
[[ -z "$INPUT" || -z "$OUT" ]] && { _log error "required: --input --out"; exit 1; }
[[ ! -f "$INPUT" ]] && { _log error "input file not found: $INPUT"; exit 1; }

# ---- Tokenize + count ----
_tokens_from_stdin() {
  if [[ "$TOKEN_BACKEND" == "python3" ]]; then
    python3 "$SCRIPT_DIR/_tokenize.py"
  else
    rg --no-filename -o '[\p{L}\p{N}]+' | tr '[:upper:]' '[:lower:]'
  fi
}

# awk 단계에서 `count<TAB>term` 형식으로 정규화 → jq 에서 tab split
RESULT=$(jq -r '.sessions[].messages[] | select(.role=="user") | .text' "$INPUT" 2>/dev/null \
  | _tokens_from_stdin \
  | sort | uniq -c | sort -rn | head -"$TOP" \
  | awk -v min="$MIN_SESSIONS" '$1 >= min {printf "%d\t%s\n", $1, $2}' \
  | jq -Rs 'split("\n")
            | map(select(length > 0)
                  | split("\t") as [$count, $term]
                  | {term: $term, count: ($count | tonumber), session_count: ($count | tonumber), sample_quotes: []})')

mkdir -p "$(dirname "$OUT")"
printf '%s\n' "$RESULT" > "$OUT"

# empty result → exit 2 (convention)
COUNT=$(printf '%s' "$RESULT" | jq 'length')
if [[ "$COUNT" == "0" ]]; then
  _log info "no lexicon terms met --min-sessions threshold"
  exit 2
fi

_log info "extracted $COUNT terms → $OUT"
exit 0
