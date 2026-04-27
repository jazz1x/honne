---
name: lexi
version: 0.0.3
description: >
  Lexicon axis standalone — extract high-frequency vocabulary, code-switching ratio, onomatopoeia.
  Triggers: "my vocabulary", "lexicon", "word habits", "speech patterns".
---

# lexi — Lexicon Axis

Standalone lexicon extraction and analysis. Uses the unified `honne` CLI, presents findings, records claims.

## Process

1. Ask for scope (repo/global). Set `SCOPE` and `LOCALE` variables.
2. Run scan: `bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" scan --base-dir ".honne" --scope "$SCOPE"`
3. Run axis extraction: `bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" axis run lexicon --scan .honne/cache/scan.json --locale "$LOCALE"`
4. Read JSON output — review `candidate_claim`, `quotes`, `insufficient_evidence` fields
5. HITL: present candidate claim with sample quotes, ask (y/n/edit)
   - **y**: proceed to step 6
   - **n**: record rejection — `bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" record claim --base-dir ".honne" --type rejection --axis lexicon --scope "$SCOPE" --text "$candidate"`; skip to done
   - **edit**: user provides revised text, use as claim
6. Record claim: `bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" record claim --base-dir ".honne" --type claim --axis lexicon --scope "$SCOPE" --text "$claim"`
7. Check past rejections to avoid re-proposing: `bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" query --base-dir ".honne" --type rejection --tag lexicon --scope "$SCOPE"`

**Progress monitoring** — use Monitor until-loop (never `sleep N && cat`):
```bash
# ✓ Monitor: until [ -f ".honne/cache/.axis_lexicon.json" ]
```

Report saved to stdout + .honne/assets/claims.jsonl
