#!/usr/bin/env bats
# tests/scripts.bats — smoke + safety tests for honne shell scripts.
#
# All tests execute in a sandbox HOME / CWD. Real ~/.claude/ and ~/.honne/
# are never touched. purge.sh safety is a first-class concern here because
# it is the only irreversible script in the suite.

load "$BATS_TEST_DIRNAME/setup.bash"

setup() {
  honne_sandbox_setup
  cd "$CLAUDE_PROJECT_DIR"
}

teardown() {
  honne_sandbox_teardown
}

# ---------- argument validation ----------

@test "purge.sh exits 1 when no mode flag given" {
  mkdir -p .honne
  run bash "$REPO_ROOT/scripts/purge.sh"
  [ "$status" -eq 1 ]
  [[ "$output" =~ "required: --all or --keep-assets" ]]
}

@test "purge.sh exits 1 on unknown arg" {
  run bash "$REPO_ROOT/scripts/purge.sh" --bogus
  [ "$status" -eq 1 ]
}

@test "scan-transcripts.sh exits 1 on unknown arg" {
  run bash "$REPO_ROOT/scripts/scan-transcripts.sh" --nope
  [ "$status" -eq 1 ]
}

# ---------- purge safety ----------

@test "purge.sh exits 0 with 'Nothing to purge' when .honne missing" {
  run bash "$REPO_ROOT/scripts/purge.sh" --all --force
  [ "$status" -eq 0 ]
  [[ "$output" =~ "Nothing to purge" ]]
}

@test "purge.sh refuses to follow a symlink at .honne" {
  mkdir -p "$HOME/elsewhere"
  ln -s "$HOME/elsewhere" .honne
  run bash "$REPO_ROOT/scripts/purge.sh" --all --force
  [ "$status" -eq 1 ]
  [[ "$output" =~ "symlink" ]]
  # Real target must be untouched.
  [ -d "$HOME/elsewhere" ]
}

@test "purge.sh --all --force removes .honne/ tree" {
  mkdir -p .honne/cache .honne/assets
  echo '{}' > .honne/persona.json
  echo '{"claim":"a"}' > .honne/assets/claim.jsonl
  run bash "$REPO_ROOT/scripts/purge.sh" --all --force
  [ "$status" -eq 0 ]
  [ ! -d .honne ]
}

@test "purge.sh --keep-assets preserves longitudinal assets" {
  mkdir -p .honne/cache .honne/assets
  echo '{"claim":"keep"}' > .honne/assets/claim.jsonl
  echo '{"scan":"drop"}' > .honne/cache/scan.json
  run bash "$REPO_ROOT/scripts/purge.sh" --keep-assets --force
  [ "$status" -eq 0 ]
  [ ! -d .honne/cache ]
  [ -f .honne/assets/claim.jsonl ]
  grep -q "keep" .honne/assets/claim.jsonl
}

@test "purge.sh without --force cancels when user does not type DELETE" {
  mkdir -p .honne
  run bash -c "echo no | bash '$REPO_ROOT/scripts/purge.sh' --all"
  [ "$status" -eq 1 ]
  [ -d .honne ]
}

# ---------- pre-commit hook sanity ----------

@test "pre-commit hook runs cleanly on a worktree with no staged changes" {
  # Run in a throwaway git worktree so our real repo state is unaffected.
  # HONNE_SKIP_TESTS=1 prevents infinite recursion: pre-commit runs tests,
  # and this test runs pre-commit — without the gate, the inner pre-commit
  # would invoke tests/run.sh again.
  cp -R "$REPO_ROOT" "$CLAUDE_PROJECT_DIR/repo-copy"
  cd "$CLAUDE_PROJECT_DIR/repo-copy"
  HONNE_SKIP_TESTS=1 run bash scripts/pre-commit.sh
  [ "$status" -eq 0 ]
  [[ "$output" =~ "Pre-commit passed" ]]
}

# ---------- scan-transcripts.sh integration ----------

@test "scan-transcripts.sh extracts messages from Claude Code format transcripts" {
  mkdir -p "$HOME/.claude/projects"
  PROJ_SLUG=$(pwd | sed 's|/|-|g' | sed 's|^-||')
  PROJ_DIR="$HOME/.claude/projects/$PROJ_SLUG"
  mkdir -p "$PROJ_DIR"

  # Copy test fixture
  cp "$REPO_ROOT/tests/fixtures/transcripts/test-session-1.jsonl" "$PROJ_DIR/"

  # Scan with repo scope
  run bash "$REPO_ROOT/scripts/scan-transcripts.sh" \
    --scope repo --since "2020-01-01" --cache .honne/cache/scan.json

  [ "$status" -eq 0 ]
  [[ "$output" =~ "scanned 1 sessions" ]]

  # Validate output structure
  [ -f .honne/cache/scan.json ]
  MESSAGE_COUNT=$(jq '.sessions[0].messages | length' .honne/cache/scan.json)
  [[ "$MESSAGE_COUNT" -gt 0 ]]

  # Validate message fields exist
  jq '.sessions[0].messages[0] | has("role") and has("text") and has("ts")' .honne/cache/scan.json | grep -q "true"

  # Validate user messages have content
  USER_TEXT=$(jq -r '.sessions[0].messages[] | select(.role=="user") | .text' .honne/cache/scan.json | head -1)
  [[ -n "$USER_TEXT" ]]
}

# ---------- shim exit-code contracts ----------

@test "extract-lexicon.sh exits 1 on unknown arg" {
  run bash "$REPO_ROOT/scripts/extract-lexicon.sh" --bogus
  [ "$status" -eq 1 ]
}

@test "detect-recurrence.sh exits 1 on unknown arg" {
  run bash "$REPO_ROOT/scripts/detect-recurrence.sh" --bogus
  [ "$status" -eq 1 ]
}

@test "evidence-gather.sh exits 1 on unknown arg" {
  run bash "$REPO_ROOT/scripts/evidence-gather.sh" --bogus
  [ "$status" -eq 1 ]
}

@test "index-session.sh exits 1 on unknown arg" {
  run bash "$REPO_ROOT/scripts/index-session.sh" --bogus
  [ "$status" -eq 1 ]
}

@test "record-claim.sh exits 1 on unknown arg" {
  run bash "$REPO_ROOT/scripts/record-claim.sh" --bogus
  [ "$status" -eq 1 ]
}

@test "query-assets.sh exits 0 with empty result when .honne missing" {
  run bash "$REPO_ROOT/scripts/query-assets.sh" --type claim
  [ "$status" -eq 0 ]
  [ "$output" = "[]" ]
}

# ---------- sandbox self-check ----------

@test "sandbox preflight aborts if HOME is not in a temp root" {
  HOME="$HONNE_TEST_REAL_HOME" run bash -c "
    source '$REPO_ROOT/tests/setup.bash'
    honne_preflight_guard
  "
  [ "$status" -eq 99 ]
  [[ "$output" =~ "real HOME" ]]
}
