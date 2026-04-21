# Changelog

## 0.0.1 (2026-04-22)

Initial release.

- Core skills: `honne` (main orchestrator, 6-axis persona), `lexi` (lexicon axis), `compare` (asset diff, read-only retrospective).
- Aliases: `whoami` → `honne`, `diff` → `compare`.
- `SessionEnd` hook for passive transcript indexing.
- Asset layer at `.honne/assets/*.jsonl` (claim/rejection/evolution) with explicit-query-only access.
- Triplet i18n (en/ko/jp) for all user-facing docs.
