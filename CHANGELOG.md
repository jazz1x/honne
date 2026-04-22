# Changelog

## 0.0.1 (unreleased)

Initial pre-release. First tag will be `v0.0.1`.

### Skills & orchestration
- Core skills: `honne:whoami` (main orchestrator, 6-axis persona), `honne:lexi` (lexicon axis only), `honne:compare` (asset diff, read-only retrospective)
- `SessionEnd` hook for passive transcript indexing
- Asset layer at `.honne/assets/*.jsonl` (claim / rejection / evolution) with explicit-query-only access

### Python core
- Single `python3 -m honne_py` entry (scan / extract / detect-recurrence / evidence / index / query / record / purge / precommit / **axis** / **doctor**)
- 6-axis extraction: lexicon, reaction, workflow, obsession, ritual, antipattern
- Zero `jq` dependency; pure Python JSON
- `datetime.now(timezone.utc)` throughout (Python 3.12 compatible)

### Haiku-safe determinism (`honne:whoami`)
- Single bash wrapper `scripts/honne` — bundles PYTHONPATH, routes subcommands, emits coded stderr banners from `templates/errors.txt` on non-zero exit
- `honne axis run <name> --emit-hitl-block` — deterministic HITL text assembled from `skills/whoami/templates/axes.{ko,en,jp}.md`; models echo verbatim
- `collect_quotes` contract — reuses `extract.py` per-axis `first_text`/`first_session_id`/`first_ts`; no LLM calls in quote selection
- `honne axis validate` — forbidden-phrase check + `--skip-if-overlaps` (exit 3) for rejection reframe filter
- `scripts/honne doctor` — preflight for python3 / `.honne/` writability (exit codes 71 / 73)
- `scan.py` filter: meta-preamble (`<command-message>`, `<local-command-caveat>`, `Base directory for this skill`, `This session is being continued`) + assistant-leak heuristics
- SKILL.md condensed to ~70 lines; Step 1 (scope + locale) and Step 4 (y/n/edit) via `AskUserQuestion` arrow-key menu

### Backward-compatible shims
- Eight existing `.sh` shims (`scan-transcripts`, `evidence-gather`, `extract-lexicon`, `detect-recurrence`, `query-assets`, `record-claim`, `index-session`, `purge`) now redirect to the wrapper; snapshot test (`tests/snapshot_shim_compat.sh`) guards stdout/stderr byte-equality

### Tests
- `pytest` + `bats` runners via `tests/run.sh`
- Contract tests: `unit_axis_contract`, `unit_doctor`, `unit_templates`, plus existing `unit_scan_*`, `unit_tokenize`, `unit_redact`
- Golden HITL fixtures at `tests/fixtures/expected/axis_*.{ko,en,jp}.txt`

### Docs
- Triplet i18n (en / ko / jp) for README and CHANGELOG
