# honne v0.0.1

**Evidence-backed self-observation from your local LLM transcripts.**

honne reads the conversation history you've accumulated with Claude and extracts behavioral patterns — not from self-report, but from what's actually in the record. It runs locally, makes no network calls, and redacts sensitive data before storing anything.

---

## What it does

Invoke `/honne:whoami` in any Claude Code session. honne asks two questions — scan scope and locale — then runs autonomously: it scans your transcripts, extracts signals across 7 axes, generates a claim per axis, and synthesizes per-axis explanations plus a one-liner. The result lands in `.honne/persona.json` and `docs/honne.md`.

---

## 7 Axes

| Axis | What it finds |
|------|---------------|
| **lexicon** | High-frequency vocabulary, code-switching ratio, onomatopoeia |
| **reaction** | Emotional register, frustration signals, enthusiasm markers |
| **workflow** | Recurring task sequences and delegation patterns |
| **obsession** | Topics and concerns that surface repeatedly across sessions |
| **ritual** | Habitual openers, closers, and structural tics |
| **antipattern** | Inefficiency signals — over-specification, repeated corrections |
| **signature** | Positive behavioral patterns — decisive closures, precise file-level requests |

`signature` is the positive counterpart to `antipattern`: instead of flagging what's inefficient, it surfaces what consistently works.

---

## Skills

- **`/honne:whoami`** — Full 7-axis profile. Autonomous after initial scope + locale selection.
- **`/honne:lexi`** — Lexicon axis only. Faster, single-axis scan.
- **`/honne:compare`** — Read-only retrospective. Loads accumulated claims and shows how your patterns have shifted across runs. No re-scan, no LLM call.

---

## Privacy

Everything stays local under `.honne/` in your project directory. 12 sensitive patterns (API keys, tokens, emails, phone numbers, IPs, credit cards, home paths, and more) are redacted before any quote is stored. Assets are never auto-injected into session context — they load only when you explicitly invoke `compare` or run a query. `CLAUDE.md` injection is permanently blocked to prevent self-reinforcement loops.

---

## Infrastructure

- Zero external dependencies beyond python3 ≥ 3.9
- 206 unit tests (pytest) + bats integration suite
- `SessionEnd` hook: passive transcript indexing — metadata only, no LLM, no context injection
- Sandboxed test HOME: test suite never touches `~/.claude/`
- Pre-commit: shellcheck, JSON syntax, SKILL.md frontmatter validation, executable bits

---

## Install

```
/plugin marketplace add https://github.com/jazz1x/honne.git
/plugin install honne --scope user
```

---

## Data

Your `.honne/` directory is a plain directory. `tar czf my-honne.tgz .honne/` takes it anywhere. `bash scripts/purge.sh --all` wipes it cleanly. No sync, no telemetry, no analytics.
