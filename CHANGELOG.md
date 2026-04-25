# Changelog

All notable changes are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [0.0.2] — 2026-04-24

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
- `setup` (ko / en / jp): 3-step permission configurator — detect current state → generate allowedTools entries → auto-apply to project settings

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
- `skills/setup/SKILL.md` (+ ko / jp): `allowedTools` patterns changed from absolute `CLAUDE_PLUGIN_ROOT` paths to portable wildcard globs (`bash */scripts/honne *`); `CLAUDE_PLUGIN_ROOT` dependency removed from setup flow
- `skills/setup/SKILL.md` (+ ko / jp): project key derivation fixed — removed erroneous `.lstrip('-')` that broke settings path resolution

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

### Removed

- `persona_prompt.{locale}.md` templates (replaced by `persona_render.md`)
- `persona_render.{ko,en,jp}.md` (3 identical files → 1 locale-agnostic template)
- Activation directive output from `/honne:persona` skill (no longer in-session embodiment claim)

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
