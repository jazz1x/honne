---
name: lexi
version: 0.0.2
description: >
  Lexicon axis standalone — extract high-frequency vocabulary, code-switching ratio, onomatopoeia.
  Triggers: "my vocabulary", "lexicon", "word habits", "speech patterns".
---

# lexi — Lexicon Axis

Standalone lexicon extraction and analysis. Runs extract-lexicon.sh, presents findings, records claims per axis.

## Process

1. Ask for scope (repo/global)
2. Run scan-transcripts.sh
3. Run extract-lexicon.sh --input .honne/cache/scan.json --top 50 --min-sessions 2
4. LLM summarizes top terms with evidence-gather.sh quotes
5. HITL: present claim with samples, ask (y/n/edit)
6. Record as claim/rejection asset
7. Check past rejections to avoid re-proposing

**Progress monitoring** — use Monitor until-loop (never `sleep N && cat`):
```bash
# ✓ Monitor: until [ -f ".honne/cache/lexicon.json" ]
```

Report saved to stdout + .honne/assets/claim.jsonl
