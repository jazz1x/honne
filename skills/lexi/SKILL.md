---
name: lexi
version: 0.0.4
description: >
  Lexicon axis standalone — extract high-frequency vocabulary, code-switching ratio, onomatopoeia.
  Triggers: "my vocabulary", "lexicon", "word habits", "speech patterns".
ssl:
  scheduling:
    anti_triggers:
      - "전체 7-axis 분석이 필요할 때 (whoami 사용)"
  structural:
    scenes:
      - "Step 1: HITL (scope + locale)"
      - "Step 2: Scan"
      - "Step 3: Axis extract"
      - "Step 4: Review JSON"
      - "Step 5: HITL accept/reject/edit"
      - "Step 6: Record claim"
      - "Step 7: Check past rejections"
    branches:
      - "Step 5: y → Step 6 record claim"
      - "Step 5: n → record rejection, halt"
      - "Step 5: edit → user-revised text → Step 6 record claim"
    resumable: false
  logical:
    tools: ["bash"]
    side_effects:
      reads:
        - ".honne/cache/scan.json"
      writes:
        - ".honne/assets/claims.jsonl  # append"
      deletes: []
      network: []
    idempotent: false
    rollback: ".honne/assets/claims.jsonl 의 마지막 lexicon 라인을 수동 제거."
---

# lexi — Lexicon Axis

Standalone lexicon extraction and analysis. Uses the unified `honne` CLI, presents findings, records claims.

## Step 1: HITL (scope + locale)

Ask for scope (repo/global) AND locale (ko/en/jp). Set `SCOPE` and `LOCALE` variables from the replies.

## Step 2: Scan

`bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" scan --base-dir ".honne" --scope "$SCOPE"`

## Step 3: Axis extract

`bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" axis run lexicon --scan .honne/cache/scan.json --locale "$LOCALE"`

## Step 4: Review JSON

Read JSON output — review `candidate_claim`, `quotes`, `insufficient_evidence` fields.

## Step 5: HITL accept/reject/edit

Present candidate claim with sample quotes, ask (y/n/edit):
- **y**: proceed to Step 6
- **n**: record rejection — `bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" record claim --base-dir ".honne" --type rejection --axis lexicon --scope "$SCOPE" --text "$candidate"`; skip to done
- **edit**: user provides revised text, use as claim

## Step 6: Record claim

`bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" record claim --base-dir ".honne" --type claim --axis lexicon --scope "$SCOPE" --text "$claim"`

## Step 7: Check past rejections

Avoid re-proposing: `bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" query --base-dir ".honne" --type rejection --tag lexicon --scope "$SCOPE"`

**Progress monitoring** — use Monitor until-loop (never `sleep N && cat`):
```bash
# ✓ Monitor: until [ -f ".honne/cache/.axis_lexicon.json" ]
```

Report saved to stdout + .honne/assets/claims.jsonl
