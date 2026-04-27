# Changelog

All notable changes are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [0.0.3] — 2026-04-28

Production hardening: all 14 ralphi-identified issues resolved, 80+ new coverage tests, one real bug found and fixed in the process.

### Fixed

#### Critical

- **synthesis_prompt (all 3 locales)**: `signature` axis was missing from the LLM output JSON schema. The `"axes"` object had 6 keys — `signature` was silently omitted, so narrative synthesis always returned `null` for it. Added `"signature": "..." | null` and updated "Cross-reference all 6 axes" → "all 7 axes" in the oneliner instruction.
- **query.py**: `--scope`, `--tag`, `--tags` parameters were accepted by the CLI but never applied in the filter loop — every call returned unfiltered results regardless. Scope filter now excludes records where `obj["scope"] != scope`; tag filter matches `obj["axis"]`; tags filter accepts comma-separated axis list.

#### Warning

- **index.py session_id**: was hardcoded `""` for every indexed session. Now derived from the JSONL filename stem (`Path(jsonl_path).stem`), which matches the Claude Code session ID convention.
- **index.py content-as-list**: `message.content` can be a list of blocks in Claude Code format (`[{"type":"text","text":"..."}]`). Index now joins text blocks before truncating to 100 chars.
- **lexi SKILL (all 3 locales)**: steps referenced obsolete shell script names (`scan-transcripts.sh`, `extract-lexicon.sh`, `evidence-gather.sh`). Updated to `honne axis run lexicon` + `honne record claim` pattern, matching whoami step 4.
- **whoami SKILL (all 3 locales)**: frontmatter `description:` and H1 said "6-Axis" despite the implementation having 7 axes since v0.0.1. Updated to "7-Axis".
- **whoami SKILL step 3**: HITL rejection branch had no write path. Added explicit `honne record claim --type rejection` call on the "n" branch. Evolutions remain a structural TODO.
- **whoami SKILL preamble**: "Step 1 through Step 7" → "Step 1 through Step 6" (step count was wrong since the 0.0.2 restructure).
- **criteria-persona.md**: signature row was missing from the axis table. Added row 7 with ≥ 3 sessions threshold and description.

#### Coverage

- **precommit.py**: README claimed marketplace.json `source: "./"` was blocked by pre-commit, but the check was not implemented. Now validates staged `marketplace.json` files and rejects any plugin with a relative `source` value.
- **evidence.gather() max_ bug**: `break` in the inner message loop exited the message iteration but the outer session loop continued accumulating matches. Added outer-loop guard (`if len(evidence) >= max_: break`). Exposed by the new `test_max_respected` coverage test.

#### Round 2 (found during coverage test authoring)

- **scan.py since-filter**: `since` parameter with a datetime string (e.g. `"2025-06-01T00:00:00Z"`) was compared against file mtime date directly, potentially excluding same-day files. Now normalized to `since[:10]` before comparison.
- **scan.py known_shas guard**: empty string `""` was being added to `known_shas` when a session record had no `sha256` field. Added `if sha:` guard.
- **extract.py hash determinism**: `hash(first_10_lines)` for ritual/obsession key generation is PYTHONHASHSEED-sensitive — different process invocations could produce different hashes. Replaced with `int(hashlib.sha256(...).hexdigest(), 16) % (10**10)`.
- **extract.py obsession matched_sessions**: `matched_sessions` was incrementing for every session regardless of language detection result. Fixed to only add `sid` when a language (ko or en) is actually detected.
- **record.py ID collision**: claim ID hash used only `type + axis + claim` — identical claims from different run_ids or timestamps would collide. Now includes `run_id` and `created_at` in the hash input.
- **render.py quote_line**: `evidence_count` variable was computed but never used (dead code). More importantly, quote lines were not being rendered in the output report. Implemented `quote_line` template section rendering (up to 3 quotes per axis).
- **cli.py silent fallthrough**: unrecognized `command + subcommand` combinations fell through to `return 0` silently. Now prints an error to stderr and returns 1.

### Added

#### Tests (+80 tests, 353 total pytest)

- `unit_scan_since_test.py`: since-filter date normalization (3 tests — same date included, datetime string normalized, future date excludes)
- `unit_core_modules_test.py`: behavioral tests for `detect_recurrence`, `evidence`, `purge`, `io` (20 tests)
- `unit_extractor_test.py`: boundary conditions for all 5 previously-untested extractors — reaction, workflow, ritual, obsession, antipattern (35 tests)
- `unit_render_test.py` — `TestQuoteLineRendering`: quote text appears, max 3 capped, empty quotes handled, session ID field, all 3 locales (5 tests)
- `unit_summarize_test.py` — parametrized matrix expanded from 6×3=18 to 7×3=21 (added signature axis)
- `unit_query_filter_test.py`: scope / tag / tags / combined filter correctness (14 tests)
- `e2e_pipeline_test.py`: scan → 7-axis extract → record claim end-to-end (4 tests)
- `e2e_query_filter.bats`: CLI scope/tag/combined filter correctness (7 bats tests)
- `e2e_doctor.bats`: `honne doctor` exit code, directory creation, non-writable guard (3 bats tests)
- `manifest.bats` extended: pre-commit rejects relative `source`, accepts registry URL (3 new bats tests)

### Changed

- `__version__` bumped `0.0.2` → `0.0.3`
- `plugin.json` version bumped `0.0.2` → `0.0.3`
- Golden render fixtures (`tests/fixtures/render/case_*/expected_honne.md`) regenerated to include quote lines

---

## [0.0.2] — 2026-04-26

Split-persona pivot: two independent personas generated separately, then debated live via new `/honne:crush` skill.

### Added

#### persona — Split-persona generation (no activation)

- **Conflict payload builder** (`persona_prompt.build_conflict_payload`): extracts antipattern + signature axes from persona.json with supporting context; returns `conflict_present` flag
- **Split-persona synthesis** (SKILL step 4): `persona_synthesis_prompt.{locale}.md` templates generate two separate personas + judge from conflict payload. Synthesis JSON schema: `{conflict_present, persona_antipattern, persona_signature, judge_system_prompt}` (one or both personas can be null).
- **Render personas** (`honne render personas`): writes three `.md` files to `.honne/personas/` — `antipattern.md`, `signature.md`, `judge.md`. Each file contains system prompt under `# ` name header.
- **No activation** (SKILL step 5): outputs are portable artifacts only. Persona skill no longer claims session activation. User redirected to `/honne:crush` for live debate.

#### crush — Live persona debate skill

- **`/honne:crush <topic>`**: 6-step flow — validate personas exist → load all 3 files → stage 5-turn debate (antipattern attack → signature rebuttal → antipattern counter → signature closing → judge verdict) → output transcript
- **No file writes**: transcript is ephemeral, displayed only in current session
- **Role switching**: each turn applies the corresponding persona's system prompt mentally, enforcing extreme viewpoints without compromise
- **Extensible for new topics**: users can run `/honne:crush` multiple times on different topics without regenerating personas

#### Templates (3 locales: ko / en / jp)

- `persona_synthesis_prompt.{locale}.md` — LLM synthesis template for split-persona generation (antipattern ≤1000 tokens, signature ≤1000 tokens, judge ≤500 tokens)
- `persona_render.md` — locale-agnostic template for persona file output: `# {name}`, `> {oneliner}`, `---`, `{system_prompt}`

#### Skills

- `persona` (ko / en / jp): 5-step flow — locale HITL → persona.json validation → conflict payload → LLM synthesis → render personas (generation-only, no activation)
- `crush` (ko / en / jp): 6-step debate orchestrator — topic input → persona validation → live 5-turn transcript with judge
- `setup` skill removed — `allowedTools` auto-configuration did not effectively reduce permission prompts; auto mode recommended instead

#### CLI

- `honne render personas` — render `.honne/personas/` directory from synthesis.json + persona.json
- `honne persona check` — existence check for `.honne/persona.json`

#### Tests

- `unit_persona_prompt_test.py`: rewritten for `render_personas` (both personas, one absent, both null, missing synthesis/persona, missing template, invalid locale)
- `unit_crush_skill_test.py`: contract tests for crush SKILL (file existence, step structure, persona file references, no file writes)
- `tests/fixtures/persona/synthesis_*.json`: new fixtures for split-persona schema (full, no antipattern, no axes)
- `unit_skill_contract_test.py`: updated assertions for new Step 4 schema

#### Docs

- `docs/e2e-persona.md`: rewritten checklist for `/honne:persona` generation flow + `/honne:crush` debate flow (no activation checks)

### Changed

- **persona schema breaking change**: old `{verdict, character_oneliner, debate, ...}` → new `{conflict_present, persona_antipattern, persona_signature, judge_system_prompt}`
- `scripts/honne_py/persona_prompt.py`: deleted `render_persona_prompt` + `_load_persona_prompt_template`; kept `build_conflict_payload`, added `render_personas`
- `scripts/honne_py/cli.py`: removed `render persona-prompt` subparser; added `render personas` + `persona check` subparsers
- `skills/persona/SKILL.md` (+ ko / jp): Step 4-5 rewritten for new schema; Step 2 now uses `persona check`; Step 5 output no longer claims activation
- Documentation: README.md / README.ko.md / README.jp.md updated for version 0.0.2, persona redesign, crush + setup skills
- `skills/whoami/SKILL.md` (+ ko / jp): bash blocks restructured — variable assignments removed, stdout capture pattern adopted for `allowedTools` matchability; version bumped to 0.0.2
- `skills/crush/SKILL.md` (+ ko / jp): raw bash file checks replaced with `honne persona check` CLI calls
- `skills/compare/SKILL.md` (+ ko / jp): `HONNE_ROOT` variable removed; direct `${CLAUDE_PLUGIN_ROOT}` usage
- `persona_render.md`: consolidated from 3 identical locale-specific templates to single file
- `skills/whoami/SKILL.md` (+ ko / jp): "coming soon" placeholder replaced with concrete `/honne:persona` + `/honne:crush` next action links

### Fixed

- `scripts/honne_py/__init__.py`: version bumped `0.0.1` → `0.0.2`
- `scripts/honne_py/record.py`: added missing `Union` import (runtime NameError on `Union[Path, str]` type hint)
- `scripts/honne_py/record.py`: `--quotes-file` with wrong-schema JSON now warns instead of silent empty fallback
- `scripts/honne_py/axis.py`: `axis run` with missing scan file now prints error message (was silent exit 66)
- `scripts/honne_py/persona_prompt.py`: `render personas` with both personas null now warns (was silent empty directory)
- `scripts/honne_py/persona_prompt.py`: removed dead code (unused persona JSON load in `render_personas`)
- Unused imports cleaned across 8 Python modules (`extract.py`, `detect_recurrence.py`, `evidence.py`, `index.py`, `query.py`, `record.py`, `persona_prompt.py`)
- Cross-locale parity: `lexi` and `compare` ko/jp SKILL files aligned with en (missing bash blocks added)
- `unit_cli_contract_test.py`: added CLI contract tests for `render personas` and `persona check` (0.0.2 commands)
- `unit_persona_prompt_test.py`: added `TestPersonaCheckCLI` (exit 0/66 tests)
- `scripts/honne_py/cli.py`: `--base-dir` argument now forwarded to `run_scan()` (was silently dropped)
- `scripts/honne_py/record.py`: `--quotes-json` with malformed JSON now returns exit 1 with error message (was unhandled exception)
- `scripts/honne_py/doctor.py`: `OSError` on `.honne/` mkdir now prints diagnostic (was silent exit 73)
- `scripts/honne_py/purge.py`: `--keep-assets` now checks children for symlinks before `rmtree`
- `scripts/honne_py/redact.py`: added 6 redaction patterns — Slack API tokens (`xoxb-`/`xoxp-`), GitHub fine-grained PATs (`github_pat_`), GCP API keys (`AIza`), PEM private key blocks
- `scripts/honne_py/io.py`, `scan.py`, `render.py`, `purge.py`, `axis.py`: additional unused imports and dead code removed
- `compare` and `lexi` SKILL versions bumped `0.0.1` → `0.0.2` (all 3 locales each)
- Documentation: redaction pattern count updated 12 → 18 across README × 3, RELEASE.md

### Removed

- `persona_prompt.{locale}.md` templates (replaced by `persona_render.md`)
- `persona_render.{ko,en,jp}.md` (3 identical files → 1 locale-agnostic template)
- Activation directive output from `/honne:persona` skill (no longer in-session embodiment claim)
- `/honne:setup` skill (3 locales) — `allowedTools` auto-configuration was ineffective; auto mode recommended instead
- "coming soon" placeholder from `/honne:whoami` completion output

---

## [0.0.1] — 2026-04-23

Initial release of **honne** — evidence-backed self-observation from local LLM transcripts.

### Added

#### whoami — 6-axis autonomous persona pipeline

- **Scan** (`honne scan`): transcript ingestion with run_id auto-generation, secrets redaction (12 patterns + Claude Code internal payloads), session timestamp normalization
- **Extract** (`honne extract`): deterministic signal extraction for 6 axes — lexicon, reaction, workflow, obsession, ritual, antipattern
- **Summarize**: axis-specific claim summarization from signal data with locale-aware formatting
- **Axis run** (`honne axis run`): per-axis candidate generation with rejection-overlap filter (`axis validate --skip-if-overlaps`)
- **Record** (`honne record claim`): JSONL claim persistence with run_id, scope, axis, quotes
- **Query** (`honne query`): asset read with type/since/until filters; graceful empty on missing workspace
- **Render persona** (`honne render persona`): persona.json generation from claims + optional narrative injection
- **Render report** (`honne render report`): docs/honne.md generation from persona.json via locale templates
- **LLM narrative synthesis** (SKILL step 5): per-axis explanations + oneliner via synthesis_prompt templates; saved to `.honne/cache/narrative.json`
- **Doctor** (`honne doctor`): preflight check for python3 version and `.honne/` writability

#### Templates (3 locales: ko / en / jp)

- `axes.{locale}.md` — axis labels, HITL questions, report headers, summary_template keys
- `report.{locale}.md` — report sections: header, axis_block, quote_line, insufficient_block, footer
- `synthesis_prompt.{locale}.md` — system + user prompt for LLM narrative synthesis
- `errors.txt` — TSV error catalogue (exit codes 2, 66, 71, 73 × 3 locales)
- `forbidden.json` — hallucination guard phrases per locale

#### CLI (`scripts/honne`)

- Unified Python entry: `scan`, `extract`, `axis`, `record`, `query`, `render`, `purge`, `doctor`, `precommit`
- All subcommands wired through `honne_py/cli.py`; zero `jq` / `ripgrep` dependency

#### Skills

- `whoami` (ko / en / jp): fully autonomous 6-step flow — scope+locale HITL → scan → rejection filter → per-axis autonomous record → LLM synthesis → render
- `lexi`: lexicon axis only (high-frequency vocabulary, code-switching, onomatopoeia)
- `compare`: read-only retrospective diff of accumulated assets

#### Infrastructure

- Hybrid test suite: 206 unit tests (pytest) + bats integration; sandboxed HOME guard prevents touching real `~/.claude/`
- Pre-commit hook: shellcheck, JSON syntax, SKILL.md frontmatter validation, executable bits
- SessionEnd hook: passive transcript index (metadata only, no LLM, no context injection)
- Asset layer at `.honne/assets/*.jsonl` (claims / rejections / evolutions) — explicit-query-only access

### Changed

- Skill renamed: `/honne:honne` → `/honne:whoami`
- whoami execution model: per-axis arrow-key HITL removed; fully autonomous after initial scope+locale selection
- Tokenizer: min length 3, alpha-only, stopword filter (EN/KO/JP function words and particles)
- `claim.jsonl` → `claims.jsonl`

### Fixed

- `scan.py`: JSONL header field `ts` → `timestamp` (Claude Code transcript format alignment)
- `pre-commit.sh`: PYTHONPATH now points to `scripts/`, not `.githooks/`
- `collect_quotes`: blank quote texts filtered before deduplication
- `summarize_workflow`: uses `summary_template.item_sep` from template instead of hardcoded `" → "`
