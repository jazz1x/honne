#!/usr/bin/env bats
# tests/e2e_doctor.bats — E2E: honne doctor health check

load "$BATS_TEST_DIRNAME/setup.bash"

setup() {
  honne_sandbox_setup
}

teardown() {
  honne_sandbox_teardown
}

@test "honne doctor exits 0 in a writable environment" {
  cd "$HONNE_SANDBOX_PROJECT"
  run bash "$REPO_ROOT/scripts/honne" doctor
  [ "$status" -eq 0 ]
}

@test "honne doctor creates .honne/ directory if missing" {
  cd "$HONNE_SANDBOX_PROJECT"
  [ ! -d ".honne" ]
  run bash "$REPO_ROOT/scripts/honne" doctor
  [ "$status" -eq 0 ]
  [ -d ".honne" ]
}

@test "honne doctor exits non-zero when .honne/ is not writable" {
  cd "$HONNE_SANDBOX_PROJECT"
  mkdir -p .honne
  chmod 444 .honne

  run bash "$REPO_ROOT/scripts/honne" doctor
  chmod 755 .honne
  [ "$status" -ne 0 ]
}
