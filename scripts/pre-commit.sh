#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
ERRORS=0

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

pass() { echo -e "  ${GREEN}✓${NC} $1"; }
fail() { echo -e "  ${RED}✗${NC} $1"; ERRORS=$((ERRORS + 1)); }
warn() { echo -e "  ${YELLOW}!${NC} $1"; }

STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM)

# --- 1. Shell lint (shellcheck, fallback to bash -n) ---
echo "Shell lint"
SH_FILES=$(echo "$STAGED_FILES" | grep -E '\.(sh|bash)$' || true)
if [ -n "$SH_FILES" ]; then
  if command -v shellcheck &>/dev/null; then
    for f in $SH_FILES; do
      if shellcheck -S warning "$REPO_ROOT/$f" 2>/dev/null; then
        pass "$f (shellcheck)"
      else
        fail "$f"
      fi
    done
  else
    warn "shellcheck not installed — falling back to bash -n (brew install shellcheck)"
    for f in $SH_FILES; do
      if bash -n "$REPO_ROOT/$f" 2>/dev/null; then
        pass "$f (bash -n)"
      else
        fail "$f — syntax error"
      fi
    done
  fi
else
  pass "no shell (.sh/.bash) files staged"
fi

# --- 2. JSON syntax ---
echo "JSON syntax"
JSON_FILES=$(echo "$STAGED_FILES" | grep '\.json$' || true)
if [ -n "$JSON_FILES" ]; then
  for f in $JSON_FILES; do
    if python3 -m json.tool "$REPO_ROOT/$f" >/dev/null 2>&1; then
      pass "$f"
    else
      fail "$f — invalid JSON"
    fi
  done
else
  pass "no .json files staged"
fi

# --- 3. SKILL.md frontmatter ---
echo "SKILL.md frontmatter"
SKILL_FILES=$(echo "$STAGED_FILES" | grep 'SKILL\.md$' || true)
if [ -n "$SKILL_FILES" ]; then
  for f in $SKILL_FILES; do
    filepath="$REPO_ROOT/$f"
    if ! head -1 "$filepath" | grep -q '^---$'; then
      fail "$f — missing frontmatter"
      continue
    fi
    fm=$(awk '/^---$/{c++; next} c==1{print} c==2{exit}' "$filepath")
    has_name=$(echo "$fm" | grep -c '^name:' || true)
    has_desc=$(echo "$fm" | grep -c '^description:' || true)
    has_version=$(echo "$fm" | grep -c '^version:' || true)
    if [ "$has_name" -eq 0 ]; then
      fail "$f — missing 'name' in frontmatter"
    elif [ "$has_desc" -eq 0 ]; then
      fail "$f — missing 'description' in frontmatter"
    elif [ "$has_version" -eq 0 ]; then
      fail "$f — missing 'version' in frontmatter"
    else
      version_val=$(echo "$fm" | grep '^version:' | sed 's/^version:[[:space:]]*//')
      if echo "$version_val" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+$'; then
        pass "$f (v$version_val)"
      else
        fail "$f — invalid version format '$version_val' (expected X.Y.Z)"
      fi
    fi
  done
else
  pass "no SKILL.md files staged"
fi

# --- 4. Script executable permission (*.sh only; .bash is sourced, .bats run by bats) ---
echo "Script permissions"
EXEC_FILES=$(echo "$STAGED_FILES" | grep '\.sh$' || true)
if [ -n "$EXEC_FILES" ]; then
  for f in $EXEC_FILES; do
    if [ -x "$REPO_ROOT/$f" ]; then
      pass "$f"
    else
      fail "$f — not executable (chmod +x)"
    fi
  done
else
  pass "no .sh files staged"
fi

# --- 5. marketplace.json schema (honne-specific guard) ---
echo "Marketplace schema"
MP_FILE=".claude-plugin/marketplace.json"
if echo "$STAGED_FILES" | grep -qx "$MP_FILE"; then
  filepath="$REPO_ROOT/$MP_FILE"
  if python3 -m json.tool "$filepath" >/dev/null 2>&1; then
    # plugins[].source must start with "./" (local) or be a valid git/github object.
    # We reject the common "." footgun that silently breaks /plugin marketplace add.
    bad=$(python3 -c '
import json, sys
d = json.load(open(sys.argv[1]))
bad = []
for i, p in enumerate(d.get("plugins", [])):
    src = p.get("source")
    if isinstance(src, str):
        if src == "." or src == "./":
            if src == ".":
                bad.append(f"plugins[{i}].source == \".\" (must be \"./\")")
        elif not src.startswith("./"):
            bad.append(f"plugins[{i}].source relative path must start with \"./\" — got {src!r}")
    elif src is None:
        bad.append(f"plugins[{i}].source is missing")
print("\n".join(bad))
' "$filepath")
    if [ -n "$bad" ]; then
      while IFS= read -r line; do fail "$MP_FILE — $line"; done <<< "$bad"
    else
      pass "$MP_FILE"
    fi

    # Referenced skill directories must exist for source "./"
    python3 -c '
import json, os, sys
d = json.load(open(sys.argv[1]))
root = sys.argv[2]
for i, p in enumerate(d.get("plugins", [])):
    if p.get("source") == "./":
        plugin_json = os.path.join(root, ".claude-plugin", "plugin.json")
        if not os.path.isfile(plugin_json):
            print(f"plugins[{i}] source=./ but .claude-plugin/plugin.json missing")
' "$filepath" "$REPO_ROOT" | while IFS= read -r line; do
      [ -n "$line" ] && fail "$MP_FILE — $line"
    done
  else
    : # JSON syntax error already reported in step 2
  fi
else
  pass "marketplace.json not staged"
fi

# --- 6. Test suite (run only if scripts/tests are staged) ---
echo "Test suite"
TEST_TRIGGER=$(echo "$STAGED_FILES" | grep -E '^(scripts/|tests/)' || true)
if [ -n "$TEST_TRIGGER" ]; then
  if [ "${HONNE_SKIP_TESTS:-0}" = "1" ]; then
    warn "HONNE_SKIP_TESTS=1 — skipping test suite (manual override)"
  elif [ -x "$REPO_ROOT/tests/run.sh" ]; then
    if bash "$REPO_ROOT/tests/run.sh" >/tmp/honne-pre-commit-tests.log 2>&1; then
      pass "pytest + bats (see /tmp/honne-pre-commit-tests.log)"
    else
      fail "test suite failed — see /tmp/honne-pre-commit-tests.log"
      tail -20 /tmp/honne-pre-commit-tests.log >&2
    fi
  else
    warn "tests/run.sh missing — skipping"
  fi
else
  pass "no scripts/ or tests/ changes staged — test run skipped"
fi

echo ""
if [ "$ERRORS" -gt 0 ]; then
  echo -e "${RED}Pre-commit failed: $ERRORS error(s)${NC}"
  exit 1
else
  echo -e "${GREEN}Pre-commit passed${NC}"
  exit 0
fi
