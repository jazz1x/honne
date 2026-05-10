---
name: compare
version: 0.0.5
description: >
  Asset-only retrospective. No transcript re-scan, no LLM re-analysis, no HITL.
  Triggers: "compare", "review past", "what changed", "self retrospective".
ssl:
  scheduling:
    anti_triggers:
      - ".honne/assets/ 미생성 또는 비어있을 때 (whoami 먼저 실행)"
  structural:
    scenes:
      - "Step 1: Scope HITL"
      - "Step 2: Assets presence check"
      - "Step 3: Load claims+evolutions"
      - "Step 4: Time-bucket grouping"
      - "Step 5: Render docs/honne-compare.md"
      - "Step 6: Asset immutability check"
    branches:
      - "Step 2: assets dir absent or empty → print 'No assets yet' + exit 0"
      - "Step 5: user requested 'summarize' → cite-bound LLM pass (otherwise pure render)"
    resumable: false
  logical:
    tools: ["bash"]
    side_effects:
      reads:
        - ".honne/assets/*.jsonl"
      writes:
        - "docs/honne-compare.md  # overwrite"
      deletes: []
      network: []
    idempotent: false  # summarize branch invokes non-deterministic LLM
    rollback: "docs/honne-compare.md 는 .gitignore 대상 — 실행 전 cp 백업 또는 출력 검증 후 수동 삭제."
---

# compare — Read-only Retrospective

## Step 1: Scope HITL (one-shot)

Ask: "Retrospective scope — `repo` or `global`?"

## Step 2: Assets presence check

If .honne/assets/ absent or empty:
  Print "No assets yet. Run honne first." and exit 0.

## Step 3: Load claims + evolutions

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/query-assets.sh" \
  --tag "<axis>" --scope "$SCOPE" --type claim --out stdout
```

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/query-assets.sh" \
  --type evolution --scope "$SCOPE" --out stdout
```

**Async wait pattern** — use Monitor until-loop, not `sleep N && cat`:
```bash
# ✓ Monitor: until [ -f ".honne/assets/claim.jsonl" ]
```

## Step 4: Time-bucket grouping

Group by axis × recorded_at bucket (YYYY-MM granularity for MVP).

## Step 5: Render docs/honne-compare.md (+ stdout)

Format per architecture PRD §4.2 compare Step 6.
No LLM unless the user asked for "summarize" — and even then, only cite-bound.

## Step 6: Asset immutability check

This skill MUST NOT write to .honne/assets/ or .honne/persona.json.
Verify (test): stat -c %Y on assets/*.jsonl before/after unchanged.
