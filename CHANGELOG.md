# Changelog

## 0.1.0 (2026-04-22)

Python entrypoint refactor: single `python3 -m honne_py` entry replaces bash+jq orchestration.

- Unified CLI with subcommand dispatch (scan, extract, detect-recurrence, evidence, index, query, record, purge, precommit)
- Bash shims (≤4 lines) delegate to Python core
- JSONL streaming with time-based progress reporting
- 6-axis extraction: lexicon, obsession, reaction, workflow, ritual, antipattern
- Zero jq dependency; pure Python JSON
- Re-export shims maintain backward compatibility (_redact.py, _tokenize.py)

## 0.0.1 (2026-04-22)

Initial release.

- Core skills: `honne` (main orchestrator, 6-axis persona), `lexi` (lexicon axis), `compare` (asset diff, read-only retrospective).
- Aliases: `whoami` → `honne`, `diff` → `compare`.
- `SessionEnd` hook for passive transcript indexing.
- Asset layer at `.honne/assets/*.jsonl` (claim/rejection/evolution) with explicit-query-only access.
- Triplet i18n (en/ko/jp) for all user-facing docs.
