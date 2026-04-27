# honne v0.0.3

**Evidence-backed self-observation from your local LLM transcripts.**

honne reads the conversation history you've accumulated with Claude and extracts behavioral patterns — not from self-report, but from what's actually in the record. It runs locally, makes no network calls, and redacts sensitive data before storing anything.

---

## What's new in 0.0.3

### Production hardening

Fourteen issues identified by static + dynamic inspection resolved. One real bug discovered and fixed during coverage test authoring.

**Critical fixes**
- `signature` axis was silently absent from the LLM synthesis prompt schema (all 3 locales). Narrative synthesis now covers all 7 axes.
- `query --scope / --tag / --tags` parameters were accepted but never applied. Filtering now works correctly.

**Bug fixes**
- `evidence.gather()`: `max_` limit was applied to the inner message loop only — the outer session loop continued accumulating matches. Fixed with an outer-loop guard.
- `scan.py`: `since` parameter with a datetime string could incorrectly exclude same-day files. Now normalized to date-only before comparison.
- `extract.py`: `hash()` for ritual/obsession key generation is PYTHONHASHSEED-sensitive. Replaced with deterministic `hashlib.sha256`.
- `record.py`: claim IDs could collide between runs. Hash now includes `run_id` + `created_at`.
- `render.py`: quote lines were not rendered in the output report. Implemented `quote_line` template section (up to 3 per axis).
- `index.py`: session ID was hardcoded `""`. Now derived from the JSONL filename stem.

**Correctness fixes**
- `whoami` SKILL: "6-Axis" label updated to "7-Axis" in frontmatter and H1 (all 3 locales).
- `lexi` SKILL: obsolete shell script references replaced with `honne axis run lexicon` + `honne record claim` pattern.
- `whoami` SKILL step 3: HITL rejection branch now writes `honne record claim --type rejection`.
- `precommit.py`: marketplace.json relative-source block was documented but not implemented. Now actually rejects.
- `cli.py`: unrecognized command combinations now print an error and exit 1 (was silent exit 0).

### Test coverage (+80 tests)

353 pytest + 38 bats — all passing.

New test files:
- `unit_scan_since_test.py` — since-filter date normalization
- `unit_core_modules_test.py` — `detect_recurrence`, `evidence`, `purge`, `io` behavioral tests
- `unit_extractor_test.py` — boundary conditions for all 5 previously-untested extractors
- `unit_render_test.py` (extended) — `TestQuoteLineRendering` quote regression guard
- `e2e_pipeline_test.py` — scan → 7-axis extract → claim record end-to-end
- `e2e_query_filter.bats` / `e2e_doctor.bats` — CLI filter and doctor tests

---

## 5 Skills

| Skill | Command | What it does |
|-------|---------|--------------|
| **whoami** | `/honne:whoami` | Full 7-axis profile. Autonomous after scope + locale selection. |
| **lexi** | `/honne:lexi` | Lexicon axis only. Faster, single-axis scan. |
| **compare** | `/honne:compare` | Read-only retrospective. Shows how patterns shift across runs. |
| **persona** | `/honne:persona` | Generates two personas from antipattern & signature axes. |
| **crush** | `/honne:crush` | Live debate between the two personas on any topic. |

---

## Privacy

Everything stays local under `.honne/` in your project directory. 18 sensitive patterns (API keys, tokens, emails, phone numbers, IPs, credit cards, home paths, and more) are redacted before any quote is stored. Assets are never auto-injected into session context. `CLAUDE.md` injection is permanently blocked.

---

## Infrastructure

- Zero external dependencies beyond python3 ≥ 3.9
- 353 pytest + 38 bats — all sandboxed, real `~/.claude/` never touched
- `SessionEnd` hook: passive transcript indexing — metadata only, no LLM, no context injection
- Pre-commit: shellcheck, JSON syntax, SKILL.md frontmatter, marketplace.json relative-source block
- 3 locales: ko / en / jp — all skills, all templates

---

## Install

```
/plugin marketplace add https://github.com/jazz1x/honne.git
/plugin install honne --scope user
```

Run Claude Code in **auto mode** (`shift+tab` to cycle) for the smoothest experience — honne skills invoke many sequential CLI commands.

---

## Data

Your `.honne/` directory is a plain directory. `tar czf my-honne.tgz .honne/` takes it anywhere. `bash scripts/purge.sh --all` wipes it cleanly. No sync, no telemetry, no analytics.
