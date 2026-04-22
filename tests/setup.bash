#!/usr/bin/env bash
# tests/setup.bash — shared sandboxing helpers for bats tests.
# load via:  load "$BATS_TEST_DIRNAME/setup.bash"
#
# Every test that touches the filesystem MUST call `honne_sandbox_setup` in
# setup() and `honne_sandbox_teardown` in teardown(). These swap HOME and
# CLAUDE_PROJECT_DIR to ephemeral temp directories so no test can reach the
# user's real ~/.claude/ or ~/.honne/.

set -euo pipefail

# Record the real HOME once, before any test swaps it.
: "${HONNE_TEST_REAL_HOME:=$HOME}"
export HONNE_TEST_REAL_HOME

# Resolve repo root from this file's own location — robust across bats /
# subshell / arbitrary cwd. setup.bash lives at <repo>/tests/setup.bash.
_honne_setup_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$_honne_setup_dir/.." && pwd)"
unset _honne_setup_dir
export REPO_ROOT
export CLAUDE_PLUGIN_ROOT="$REPO_ROOT"

honne_sandbox_setup() {
  HONNE_SANDBOX_HOME="$(mktemp -d -t honne-test-home-XXXXXX)"
  HONNE_SANDBOX_PROJECT="$(mktemp -d -t honne-test-proj-XXXXXX)"
  export HOME="$HONNE_SANDBOX_HOME"
  export CLAUDE_PROJECT_DIR="$HONNE_SANDBOX_PROJECT"
  mkdir -p "$HOME/.claude/projects/test-proj"
  honne_preflight_guard
}

honne_sandbox_teardown() {
  honne_preflight_guard
  [[ -n "${HONNE_SANDBOX_HOME:-}" && -d "$HONNE_SANDBOX_HOME" ]] && rm -rf "$HONNE_SANDBOX_HOME"
  [[ -n "${HONNE_SANDBOX_PROJECT:-}" && -d "$HONNE_SANDBOX_PROJECT" ]] && rm -rf "$HONNE_SANDBOX_PROJECT"
}

# Abort if HOME is the user's real home or outside an OS temp root.
honne_preflight_guard() {
  if [[ "$HOME" == "$HONNE_TEST_REAL_HOME" ]]; then
    echo "FATAL: test attempted to use real HOME ($HOME)" >&2
    exit 99
  fi
  case "$HOME" in
    /tmp/*|/var/folders/*|/private/var/folders/*|/private/tmp/*) ;;
    *)
      echo "FATAL: HOME not in an OS temp root: $HOME" >&2
      exit 99
      ;;
  esac
}

# Copy a fixture transcript into the sandbox HOME so scripts that glob
# ~/.claude/projects/**/*.jsonl find it.
honne_stage_transcript() {
  local fixture="$1"
  local dest="$HOME/.claude/projects/test-proj/$(basename "$fixture")"
  cp "$REPO_ROOT/tests/fixtures/transcripts/$fixture" "$dest"
  printf '%s\n' "$dest"
}
