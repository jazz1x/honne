# Changelog

All notable changes are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

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
- `report.{locale}.md` — report sections: header, axis_block, quote_line, insufficient_block, footer, next_actions
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

- Hybrid test suite: 188 unit tests (pytest) + bats integration; sandboxed HOME guard prevents touching real `~/.claude/`
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
