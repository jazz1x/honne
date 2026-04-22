#!/usr/bin/env bash
# scripts/scan-transcripts.sh
# Exit: 0 success, 1 invalid args, 2 empty result, 4 tool missing
set -euo pipefail

# ---- Helpers ----
_log() { echo "[$1] $(basename "$0" .sh): $2" >&2; }
_debug() { [[ "${HONNE_DEBUG:-0}" == "1" ]] && _log debug "$1" || :; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ---- Pre-flight ----
command -v jq >/dev/null 2>&1 || { _log error "jq missing (install: brew install jq)"; exit 4; }

# Redact backend: python3 primary, rg fallback. Cached per process.
REDACT_BACKEND=""
if command -v python3 >/dev/null 2>&1; then
  REDACT_BACKEND="python3"
elif command -v rg >/dev/null 2>&1; then
  REDACT_BACKEND="rg"
else
  _log error "need python3 or ripgrep (install: brew install python OR brew install ripgrep)"
  exit 4
fi
_debug "redact backend: $REDACT_BACKEND"

# ---- Arg parsing ----
SCOPE="" SINCE="" CACHE="" INDEX_REF="" REDACT=1
while [[ $# -gt 0 ]]; do
  case $1 in
    --scope)      SCOPE="$2"; shift 2;;
    --since)      SINCE="$2"; shift 2;;
    --cache)      CACHE="$2"; shift 2;;
    --index-ref)  INDEX_REF="$2"; shift 2;;
    --redact-secrets)    REDACT=1; shift;;
    --no-redact-secrets) REDACT=0; shift;;
    *) _log error "unknown arg: $1"; exit 1;;
  esac
done
[[ -z "$SCOPE" || -z "$SINCE" || -z "$CACHE" ]] && { _log error "required: --scope --since --cache"; exit 1; }
[[ "$SCOPE" != "global" && "$SCOPE" != "repo" ]] && { _log error "scope must be global|repo"; exit 1; }

# ---- Scope → path resolution ----
if [[ "$SCOPE" == "global" ]]; then
  SEARCH_DIR="$HOME/.claude/projects"
else
  SLUG=$(pwd | sed 's|/|-|g' | sed 's|^-||')
  SEARCH_DIR="$HOME/.claude/projects/$SLUG"
  if [[ ! -d "$SEARCH_DIR" ]] || [[ -z "$(ls -A "$SEARCH_DIR" 2>/dev/null)" ]]; then
    _log warn "repo scope: no transcripts found at $SEARCH_DIR"
    exit 2
  fi
fi

# ---- Index ref (idempotent skip) ----
KNOWN_SHAS=""
if [[ -n "$INDEX_REF" && -f "$INDEX_REF" ]]; then
  KNOWN_SHAS=$(jq -r '.sessions[].sha256' "$INDEX_REF" 2>/dev/null | tr '\n' '|' | sed 's/|$//')
fi

# ---- Redact helper (python3 primary + rg fallback) ----
_redact() {
  local text="$1"
  [[ "$REDACT" == "0" ]] && { printf '%s' "$text"; return; }
  if [[ "$REDACT_BACKEND" == "python3" ]]; then
    printf '%s' "$text" | python3 "$SCRIPT_DIR/_redact.py"
  else
    # rg fallback: 12-pattern passthru chain (BSD/GNU sed 회피용)
    printf '%s\n' "$text" | rg --passthru --no-filename \
      -e '(sk-|pk_)[a-zA-Z0-9_-]{20,}' --replace '[REDACTED:api-key]' | rg --passthru \
      -e 'AKIA[0-9A-Z]{16}' --replace '[REDACTED:aws]' | rg --passthru \
      -e 'gh[pso]_[a-zA-Z0-9]{36,}' --replace '[REDACTED:gh]' | rg --passthru \
      -e 'ey[JK][A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}' --replace '[REDACTED:jwt]' | rg --passthru \
      -e 'https://hooks\.slack\.com/services/[A-Z0-9/]+' --replace '[REDACTED:slack-webhook]' | rg --passthru \
      -e 'https://discord(app)?\.com/api/webhooks/[0-9]+/[A-Za-z0-9_-]+' --replace '[REDACTED:discord-webhook]' | rg --passthru \
      -e 'Bearer [A-Za-z0-9_\-\.=:]+' --replace '[REDACTED:bearer]' | rg --passthru \
      -e '([?&](token|api_key|apikey|key|secret|password)=)[^&\s]+' --replace '$1[REDACTED]' | rg --passthru \
      -e '/Users/[^/[:space:]]+/' --replace '/Users/[REDACTED]/' | rg --passthru \
      -e '/home/[^/[:space:]]+/' --replace '/home/[REDACTED]/' | rg --passthru \
      -e '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}' --replace '[REDACTED:email]' | rg --passthru \
      -e '01[0-9]-?[0-9]{3,4}-?[0-9]{4}' --replace '[REDACTED:phone]' | rg --passthru \
      -e '(?:[0-9]{1,3}\.){3}[0-9]{1,3}' --replace '[REDACTED:ipv4]' | rg --passthru \
      -e '[0-9]{4}[\s-]?[0-9]{4}[\s-]?[0-9]{4}[\s-]?[0-9]{4}' --replace '[REDACTED:card]'
  fi
}

# ---- Collect session files ----
SESSIONS_JSON="[]"
FOUND=0
while IFS= read -r -d '' JSONL; do
  # sha256 skip (idempotent)
  if command -v sha256sum >/dev/null 2>&1; then
    SHA=$(sha256sum "$JSONL" | cut -d' ' -f1)
  else
    SHA=$(shasum -a 256 "$JSONL" | cut -d' ' -f1)
  fi
  if [[ -n "$KNOWN_SHAS" ]] && echo "|$KNOWN_SHAS|" | grep -q "|$SHA|"; then
    _debug "skip known sha: $SHA"
    continue
  fi

  # since filter
  if [[ -n "$SINCE" ]]; then
    FILE_DATE=$(date -r "$JSONL" +%Y-%m-%d 2>/dev/null || stat -f %Sm -t %Y-%m-%d "$JSONL")
    [[ "$FILE_DATE" < "$SINCE" ]] && continue
  fi

  # Meta + message parsing
  SID=$(head -1 "$JSONL" | jq -r '.sessionId // empty' 2>/dev/null) || { _log warn "parse fail: $JSONL"; continue; }
  [[ -z "$SID" ]] && continue

  CWD=$(head -1 "$JSONL" | jq -r '.cwd // empty' 2>/dev/null || echo "")
  STARTED=$(head -1 "$JSONL" | jq -r '.ts // empty' 2>/dev/null || echo "")

  MESSAGES_JSON="[]"
  LINE_NUM=0
  while IFS= read -r LINE; do
    LINE_NUM=$((LINE_NUM + 1))
    MSG=$(echo "$LINE" | jq -c '
      select(.message.role != null) |
      {
        role: .message.role,
        text: (
          if (.message.content | type) == "string" then .message.content
          elif (.message.content | type) == "array" then
            [.message.content[]? | select(.type == "text") | .text] | join("\n")
          else "" end
        ),
        ts: (.timestamp // "")
      } |
      select(.text != "" and .text != null)
    ' 2>/dev/null) || {
      _log warn "$SID: parse failed line $LINE_NUM"
      continue
    }
    [[ -z "$MSG" ]] && continue
    # redact
    TEXT=$(echo "$MSG" | jq -r '.text')
    REDACTED_TEXT=$(_redact "$TEXT")
    MSG=$(echo "$MSG" | jq --arg t "$REDACTED_TEXT" '.text = $t')
    MESSAGES_JSON=$(echo "$MESSAGES_JSON" | jq --argjson m "$MSG" '. + [$m]')
  done < "$JSONL"

  SESSION_OBJ=$(jq -n \
    --arg sid "$SID" --arg pp "$CWD" --arg sa "$STARTED" \
    --argjson msgs "$MESSAGES_JSON" \
    '{session_id: $sid, project_path: $pp, started_at: $sa, messages: $msgs, sha256: "'$SHA'"}')
  SESSIONS_JSON=$(echo "$SESSIONS_JSON" | jq --argjson s "$SESSION_OBJ" '. + [$s]')
  FOUND=$((FOUND + 1))
done < <(find "$SEARCH_DIR" -type f -name '*.jsonl' -print0 2>/dev/null)

if [[ "$FOUND" -eq 0 ]]; then
  _log info "no transcripts matched"
  exit 2
fi

# ---- Atomic write ----
mkdir -p "$(dirname "$CACHE")"
TMP=$(mktemp)
jq -n --arg scope "$SCOPE" --arg ts "$(date -u +%FT%TZ)" --argjson sess "$SESSIONS_JSON" \
  '{scope: $scope, scanned_at: $ts, sessions: $sess}' > "$TMP"
mv "$TMP" "$CACHE"
_log info "scanned $FOUND sessions → $CACHE"
exit 0
