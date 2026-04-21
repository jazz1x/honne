# Validates scan-transcripts.sh output structure
# Usage: jq -e --slurpfile schema tests/schemas/scan-schema.jq '.' < scan.json | jq -f scan-schema.jq

# Top-level structure
(type == "object") and
(.scope | type == "string" and ("global", "repo" | IN(.scope))) and
(.scanned_at | type == "string") and
(.sessions | type == "array") and

# Each session
(.sessions | map(
  (type == "object") and
  (.session_id | type == "string") and
  (.project_path | type == "string") and
  (.started_at | type == "string") and
  (.messages | type == "array") and
  (.sha256 | type == "string") and

  # Each message
  (.messages | map(
    (type == "object") and
    (.role | type == "string" and ("user", "assistant" | IN(.role))) and
    (.text | type == "string") and
    (.ts | type == "string")
  ) | all)
) | all)
