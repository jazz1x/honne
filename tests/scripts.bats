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
  cp -R "$REPO_ROOT" "$CLAUDE_PROJECT_DIR/repo-copy"
  cd "$CLAUDE_PROJECT_DIR/repo-copy"
  run bash scripts/pre-commit.sh
  [ "$status" -eq 0 ]
  [[ "$output" =~ "Pre-commit passed" ]]
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
