---
name: compare
version: 0.0.1
description: >
  Asset-only retrospective. No transcript re-scan, no LLM re-analysis, no HITL.
  Triggers: "compare", "review past", "what changed", "self retrospective".
---

# compare — Read-only Retrospective

## Step 1: Scope HITL (one-shot)

Ask: "Retrospective scope — `repo` or `global`?"

## Step 2: Assets presence check

If .honne/assets/ absent or empty:
  Print "No assets yet. Run honne first." and exit 0.

## Step 3: Load claims + evolutions

```bash
HONNE_ROOT="${CLAUDE_PLUGIN_ROOT}"
bash "$HONNE_ROOT/scripts/query-assets.sh" \
  --tag "<axis>" --scope "$SCOPE" --type claim --out stdout
bash "$HONNE_ROOT/scripts/query-assets.sh" \
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

## Step 6: No writes

This skill MUST NOT write to .honne/assets/ or .honne/persona.json.
Verify (test): stat -c %Y on assets/*.jsonl before/after unchanged.
