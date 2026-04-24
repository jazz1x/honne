# Changelog

All notable changes are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [0.0.2] — 2026-04-24

Persona system prompt activation: conflict synthesis between antipattern and signature axes.

### Added

#### persona — In-session persona activation from conflict synthesis

- **Conflict payload builder** (`persona_prompt.build_conflict_payload`): extracts antipattern + signature axes from persona.json with supporting context; returns `conflict_present` flag
- **Three-voice debate synthesis** (SKILL step 4): `persona_synthesis_prompt.{locale}.md` templates stage antipattern vs. signature as prosecutor / defender / judge. Synthesis JSON now requires `debate: {antipattern_voice, signature_voice, resolution}` when `conflict_present=true`.
- **Render with debate + activation directive** (`honne render persona-prompt`): `.honne/persona-prompt.md` includes the inner clash transcript + an explicit "stay in character" directive for the LLM reading the file
- **Session-scoped activation** (SKILL step 5): outputs character_oneliner + verdict + debate summary + system_prompt, then the skill self-applies the activation directive as its final statement. CLAUDE.md injection remains prohibited — activation works via (a) the rendered directive visible in context, (b) the final self-statement.

#### Templates (3 locales: ko / en / jp)

- `persona_synthesis_prompt.{locale}.md` — LLM synthesis template enforcing three-voice debate format (antipattern prosecutor / signature defender / judge resolution)
- `persona_prompt.{locale}.md` — report template for `.honne/persona-prompt.md` (character_oneliner, verdict, signature, antipattern, **debate**, system_prompt, **activation_directive** sections)

#### Skills

- `persona` (ko / en / jp): 5-step flow — locale HITL → persona.json validation → conflict payload → LLM synthesis → render + activation

#### CLI

- `honne render persona-prompt` — render persona-prompt.md from synthesis.json + persona.json with locale selection

#### setup — One-time allowedTools permission registration

- `setup` skill (ko / en / jp): 2-step flow — output `allowedTools` fragment → inspect current `~/.claude/settings.json` state. Read-only; never mutates user settings.

#### SKILL hardening (whoami execution fixes from 0.0.1 e2e log)

- **File-based quotes passing** (`record claim --quotes-file <path>`): eliminates shell arg injection failure for Korean / special-character quote sets. `--quotes-json` preserved for backward compat.
- **Intermediate file contract** (SKILL step 4): each axis output written to `.honne/cache/axis-{name}.json`; `/tmp` writes prohibited as testable HARD RULE.
- **Absolute path resolution** (SKILL step 5): narrative Write path resolved via `python3 os.getcwd()` before Write tool invocation. Eliminates `{PWD}` placeholder ambiguity that caused writes to `~/.claude/projects/*/`.
- **Synthesis JSON validation** (`render persona-prompt`): required keys `{verdict, character_oneliner, system_prompt, conflict_present}` checked fail-fast (exit 66) on missing key.
- **`build_conflict_payload` contract**: `conflict_present: bool` added to return dict (True only when both antipattern + signature non-null).

#### Tests

- `unit_persona_prompt_test.py`: build_conflict_payload and render_persona_prompt tests (both axes, one/both absent, both null, missing files, invalid locale)
- `unit_persona_skill_test.py`: SKILL contract tests (all 3 locale files, no heredocs, required keys, templates, plugin.json registration, whoami /tmp prohibition)
- `tests/fixtures/persona/persona_no_axes.json`: fixture for both-axes-null (portrait mode) branch
- `unit_skill_contract_test.py`: `test_skill_step4_has_quotes_file_arg` updated to reflect 0.0.2 file-based passing contract

#### Docs

- `docs/e2e-persona.md`: manual smoke checklist for post-implementation verification

### Changed

- `.claude-plugin/plugin.json`: version bumped to 0.0.2; persona + setup skills registered
- `scripts/honne_py/record.py`: `quotes_file` parameter added; accepts axis JSON (`{quotes: [...]}`) or flat array
- `scripts/honne_py/cli.py`: `--quotes-file` wired into `record claim` subparser
- `scripts/honne_py/purge.py`: `--keep-assets` loop handles `cache/` deletion (including `axis-*.json`) via `rmtree`
- `skills/whoami/SKILL.md` (+ ko / jp): Step 4 rewritten for file-based quotes; Step 5 abs-path resolve
- Documentation: README.md / README.ko.md / README.jp.md updated with /honne:persona skill table entry

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
