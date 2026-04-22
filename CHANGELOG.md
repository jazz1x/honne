# Changelog

## 0.0.2 (2026-04-23)

Haiku 4.5 determinism — low-tier models complete `/honne:whoami` without hallucination or silent fallbacks.

- Single CLI wrapper `scripts/honne` — bundles PYTHONPATH, routes subcommands, emits coded stderr banners from `templates/errors.txt` on non-zero exit
- `honne axis run <name> --emit-hitl-block` — deterministic HITL text assembled from `templates/axes.{ko,en,jp}.md`; models echo verbatim, do not paraphrase
- `collect_quotes` contract — reuses `extract.py` per-axis `first_text`/`first_session_id`/`first_ts` (promoted in T6a), no LLM calls in quote selection
- `honne axis validate` — forbidden-phrase check + `--skip-if-overlaps` (exit 3) for Step 3 rejection reframe filter
- `scripts/honne doctor` — preflight for python3 / `.honne/` writability (exit codes 71 / 73)
- SKILL.md reduced 140 → ~70 lines; Step 1 scope+locale and Step 4 y/n/edit via AskUserQuestion (arrow-key menu)
- scan.py filter: meta-preamble (`<command-message>`, `<local-command-caveat>`, `Base directory for this skill`, `This session is being continued`) + assistant-leak heuristics
- `datetime.utcnow()` → `datetime.now(timezone.utc)` (Python 3.12 deprecation, 8 sites)
- `query.py` returns 0 on empty results when base_dir exists (was 2)
- Tests: `unit_axis_contract`, `unit_doctor`, `unit_templates`; golden HITL fixtures at `tests/fixtures/expected/axis_*.{ko,en,jp}.txt`
- Design: `docs/prd-honne-whoami-haiku-robustness.md` (architect), `docs/prd-honne-whoami-haiku-robustness-impl.md` (impl, 5 rev history in Appendix H)

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
