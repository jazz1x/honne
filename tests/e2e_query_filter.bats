#!/usr/bin/env bats
# tests/e2e_query_filter.bats — E2E: query scope/tag filter verification

load "$BATS_TEST_DIRNAME/setup.bash"

setup() {
  honne_sandbox_setup
  HONNE_BASE="$HONNE_SANDBOX_HOME/.honne"
  mkdir -p "$HONNE_BASE/assets"

  # Write mixed claims.jsonl fixture
  cat > "$HONNE_BASE/assets/claims.jsonl" <<'JSONL'
{"id":"c1","axis":"lexicon","scope":"repo","type":"claim","created_at":"2025-01-01T00:00:00Z"}
{"id":"c2","axis":"reaction","scope":"repo","type":"claim","created_at":"2025-01-02T00:00:00Z"}
{"id":"c3","axis":"lexicon","scope":"global","type":"claim","created_at":"2025-01-03T00:00:00Z"}
{"id":"c4","axis":"workflow","scope":"repo","type":"claim","created_at":"2025-01-04T00:00:00Z"}
JSONL

  # Write mixed rejections.jsonl fixture
  cat > "$HONNE_BASE/assets/rejections.jsonl" <<'JSONL'
{"id":"r1","axis":"lexicon","scope":"repo","type":"rejection","created_at":"2025-02-01T00:00:00Z"}
{"id":"r2","axis":"obsession","scope":"global","type":"rejection","created_at":"2025-02-02T00:00:00Z"}
JSONL
}

teardown() {
  honne_sandbox_teardown
}

# --- scope filter ---

@test "query --scope repo returns only repo-scoped records" {
  run bash "$REPO_ROOT/scripts/honne" query \
    --base-dir "$HONNE_BASE" \
    --type claim \
    --scope repo

  [ "$status" -eq 0 ]
  count=$(echo "$output" | python3 -c "import json,sys; print(len(json.load(sys.stdin)))")
  [ "$count" -eq 3 ]
}

@test "query --scope global returns only global-scoped records" {
  run bash "$REPO_ROOT/scripts/honne" query \
    --base-dir "$HONNE_BASE" \
    --type claim \
    --scope global

  [ "$status" -eq 0 ]
  count=$(echo "$output" | python3 -c "import json,sys; print(len(json.load(sys.stdin)))")
  [ "$count" -eq 1 ]
}

@test "query without --scope returns all records" {
  run bash "$REPO_ROOT/scripts/honne" query \
    --base-dir "$HONNE_BASE" \
    --type claim

  [ "$status" -eq 0 ]
  count=$(echo "$output" | python3 -c "import json,sys; print(len(json.load(sys.stdin)))")
  [ "$count" -eq 4 ]
}

# --- tag filter ---

@test "query --tag lexicon returns only lexicon axis records" {
  run bash "$REPO_ROOT/scripts/honne" query \
    --base-dir "$HONNE_BASE" \
    --type claim \
    --tag lexicon

  [ "$status" -eq 0 ]
  count=$(echo "$output" | python3 -c "import json,sys; print(len(json.load(sys.stdin)))")
  [ "$count" -eq 2 ]
}

@test "query --scope repo --tag lexicon returns only matching record" {
  run bash "$REPO_ROOT/scripts/honne" query \
    --base-dir "$HONNE_BASE" \
    --type claim \
    --scope repo \
    --tag lexicon

  [ "$status" -eq 0 ]
  count=$(echo "$output" | python3 -c "import json,sys; print(len(json.load(sys.stdin)))")
  [ "$count" -eq 1 ]
  id=$(echo "$output" | python3 -c "import json,sys; print(json.load(sys.stdin)[0]['id'])")
  [ "$id" = "c1" ]
}

# --- rejection type + scope/tag ---

@test "query --type rejection --scope repo --tag lexicon returns r1 only" {
  run bash "$REPO_ROOT/scripts/honne" query \
    --base-dir "$HONNE_BASE" \
    --type rejection \
    --scope repo \
    --tag lexicon

  [ "$status" -eq 0 ]
  count=$(echo "$output" | python3 -c "import json,sys; print(len(json.load(sys.stdin)))")
  [ "$count" -eq 1 ]
  id=$(echo "$output" | python3 -c "import json,sys; print(json.load(sys.stdin)[0]['id'])")
  [ "$id" = "r1" ]
}

@test "query --type rejection --scope repo --tag obsession returns empty (no match)" {
  run bash "$REPO_ROOT/scripts/honne" query \
    --base-dir "$HONNE_BASE" \
    --type rejection \
    --scope repo \
    --tag obsession

  [ "$status" -eq 0 ]
  output_trimmed=$(echo "$output" | tr -d ' \n')
  [ "$output_trimmed" = "[]" ]
}
