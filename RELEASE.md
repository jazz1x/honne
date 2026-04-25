# honne v0.0.2

**Evidence-backed self-observation from your local LLM transcripts.**

honne reads the conversation history you've accumulated with Claude and extracts behavioral patterns — not from self-report, but from what's actually in the record. It runs locally, makes no network calls, and redacts sensitive data before storing anything.

---

## What's new in 0.0.2

### Split-persona pivot

`/honne:persona` now generates **two independent personas** (antipattern × signature) instead of a single merged verdict. Each persona has its own system prompt, name, and one-liner. A judge system prompt mediates between them.

### `/honne:crush` — Live debate

Stage a 5-turn debate between your two personas on any topic. Antipattern attacks, signature rebuts, judge delivers the verdict. Transcript is ephemeral — no files written.

### `/honne:setup` — Permission auto-configuration

One-time `allowedTools` registration. Detects current state, generates permission entries, optionally auto-applies to project settings. Eliminates excessive permission prompts during skill execution.

### Hardening

- All intermediate data writes to `.honne/cache/` — no `/tmp` usage
- `--quotes-file` replaces `--quotes-json` for shell-safe quote passing
- SKILL bash blocks restructured: every command starts with `bash`, `python3`, or `date` for `allowedTools` matchability
- `/honne:setup` generates portable wildcard patterns (`bash */scripts/honne *`) — no absolute paths, works on any machine
- Error paths produce diagnostic messages (missing scan, null personas, wrong quotes schema)
- No CLAUDE.md injection, no activation language in persona output

---

## 6 Skills

| Skill | Command | What it does |
|-------|---------|--------------|
| **whoami** | `/honne:whoami` | Full 7-axis profile. Autonomous after scope + locale selection. |
| **lexi** | `/honne:lexi` | Lexicon axis only. Faster, single-axis scan. |
| **compare** | `/honne:compare` | Read-only retrospective. Shows how patterns shift across runs. |
| **persona** | `/honne:persona` | Generates two personas from antipattern & signature axes. |
| **crush** | `/honne:crush` | Live debate between the two personas on any topic. |
| **setup** | `/honne:setup` | One-time `allowedTools` permission registration. |

---

## Privacy

Everything stays local under `.honne/` in your project directory. 12 sensitive patterns (API keys, tokens, emails, phone numbers, IPs, credit cards, home paths, and more) are redacted before any quote is stored. Assets are never auto-injected into session context. `CLAUDE.md` injection is permanently blocked.

---

## Infrastructure

- Zero external dependencies beyond python3 ≥ 3.9
- 266 unit tests (pytest) + e2e verification suite
- `SessionEnd` hook: passive transcript indexing — metadata only, no LLM, no context injection
- Pre-commit: shellcheck, JSON syntax, SKILL.md frontmatter validation
- 3 locales: ko / en / jp — all skills, all templates

---

## Install

```
/plugin marketplace add https://github.com/jazz1x/honne.git
/plugin install honne --scope user
```

After install, run `/honne:setup` to configure permissions and eliminate manual approval prompts.

---

## Data

Your `.honne/` directory is a plain directory. `tar czf my-honne.tgz .honne/` takes it anywhere. `bash scripts/purge.sh --all` wipes it cleanly. No sync, no telemetry, no analytics.
