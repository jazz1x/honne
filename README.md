# honne

> Claude Code plugin — self-observation from LLM transcripts

![version](https://img.shields.io/badge/version-0.0.3-blue)
![license](https://img.shields.io/badge/license-MIT-green)
![claude-code](https://img.shields.io/badge/claude--code-plugin-purple)

**honne** (本音, "true voice") — a local, evidence-backed mirror of how you actually work with LLMs. Beneath the official persona (*tatemae*), honne surfaces what your transcripts quietly record: recurring vocabulary, rejected suggestions, session rituals, the patterns you never named.

Everything runs locally. No network calls, no analytics. Claims are extracted and recorded autonomously; narrative explanations are synthesized via LLM in a single dedicated step. Your data lives under `.honne/` as plain JSONL — portable, inspectable, deletable.

[한국어](./README.ko.md) · [日本語](./README.jp.md)

## Skills

| Skill | Command | Role |
|-------|---------|------|
| **whoami** | `/honne:whoami` | Main orchestrator. 7-axis persona with autonomous evidence gathering and LLM narrative synthesis. |
| **lexi** | `/honne:lexi` | Lexicon axis only (high-frequency vocabulary, code-switching, onomatopoeia). |
| **compare** | `/honne:compare` | Read-only retrospective. Reads accumulated assets and shows changes over time. No transcript re-scan, no LLM re-analysis. |
| **persona** | `/honne:persona` | Generates two independent personas from antipattern & signature axes. Outputs standalone `.md` files for use with `/honne:crush`. |
| **crush** | `/honne:crush` | Stages a live debate between the two personas on any topic. Reads persona files and produces a 5-turn transcript with judge verdict. |

Each skill operates in its own orbit, connected only through **shared artifacts on disk** (`.honne/cache/`, `.honne/persona.json`, `.honne/assets/*.jsonl`).

```
 transcripts (~/.claude/projects/**/*.jsonl)
      │
      │  honne  ──→  .honne/persona.json + docs/honne.md  (7-axis snapshot)
      │                  │
      │                  ├── honne record claim  ──→  .honne/assets/*.jsonl (longitudinal)
      │                  │
      │  lexi   ──→  .honne/persona.json (axis 1 only)
      │
 SessionEnd hook ──→  .honne/cache/index.json  (passive transcript index, metadata only)
                              │
 compare (read-only)  ──→  honne query  ──→  docs/honne-compare.md  (diff of past claims)
```

## Prerequisites

honne requires **python3 ≥ 3.9**. No other dependencies.

```bash
python3 --version   # must be 3.9+
```

Scripts exit with code 71 if python3 is missing or below 3.9.

## Install

### Option 1 — `npx skills add` (recommended)

Works with Claude Code, Cursor, Codex, Windsurf, and other skills.sh-compatible agents.

```bash
npx skills add jazz1x/honne                  # install into ./.claude/skills/ (project)
npx skills add jazz1x/honne -g               # install into ~/.claude/skills/ (global, recommended for honne)
npx skills add jazz1x/honne --list           # list skills before installing
npx skills add jazz1x/honne --skill whoami   # install a single skill
```

Expected output:

```
✓ Installed jazz1x/honne — 5 skills (whoami, lexi, compare, persona, crush)
```

Global install (`-g`) is recommended — honne reads transcripts across all projects, so cross-project history makes self-observation richer.

### Option 2 — Claude Code native plugin

#### 1. Register the marketplace

Inside a Claude Code session, run:

```
/plugin marketplace add https://github.com/jazz1x/honne.git
```

Expected output:

```
✓ Marketplace 'honne' added (1 plugin)
```

#### 2. Install the plugin

```
/plugin install honne --scope user
```

Expected output:

```
✓ Installed honne@0.0.3 — 5 skills registered (whoami, lexi, compare, persona, crush)
```

Scope options:

| Scope | Effect | When to use |
|-------|--------|-------------|
| `--scope user` *(recommended)* | Installs into `~/.claude/` — honne can read transcripts across **all projects** | Normal use. Self-observation benefits from cross-project history. |
| `--scope local` | Installs into the current project's `.claude/` only | Sandboxed trial, or when you intentionally want single-project scope. |

#### 3. Verify

```
/plugin list
```

You should see `honne` in the list. If the slash commands below autocomplete, you're good:

```
/honne:whoami
/honne:lexi
/honne:compare
/honne:persona
/honne:crush
```

> **Tip**: Run Claude Code in **auto mode** (`shift+tab` to cycle) for the smoothest experience. honne skills invoke many sequential CLI commands — auto mode eliminates repeated permission prompts.

The `SessionEnd` hook is registered automatically — no extra configuration.

#### 4. Uninstall

```
/plugin uninstall honne
/plugin marketplace remove honne
```

Your `.honne/` directory is **not** touched by uninstall — your assets persist. Delete them manually with `bash scripts/purge.sh --all` if you want a clean wipe.

---

## Quickstart

Once installed, start with:

```
# Inside a Claude Code session, in any project
/honne:whoami
```

Sample flow (simplified):

```
user   > /honne:whoami

step 1 > Scan scope?     ← arrow-key menu (repo / global)
         Locale?         ← arrow-key menu (ko / en / jp)
user   > [selects global, en]

step 2 > scan transcripts under ~/.claude/projects/… → .honne/cache/scan.json
         run_id auto-generated; secrets + Claude Code meta filtered during scan

step 3 > per-axis autonomous extraction [lexicon, reaction, workflow, obsession, ritual, antipattern, signature]
           - axis run → deterministic signal extraction from scan cache
           - rejection filter applied (overlapping past rejections skipped)
           - claims recorded to .honne/assets/claims.jsonl (no per-axis prompt)

step 4 > LLM narrative synthesis
           - synthesis_prompt.en.md applied to matched claims
           - per-axis explanations + oneliner → .honne/cache/narrative.json

step 5 > render persona + report
✓ Saved: .honne/persona.json
✓ Saved: docs/honne.md
✓ Appended: .honne/assets/claims.jsonl
```

Axis claims come from deterministic signal functions, not from model generation. Narrative synthesis in step 4 is the only LLM call in the entire flow.

After 2 or more runs, compare past profiles:

```
/honne:compare
```

This reads only what's already on disk — no transcript re-scan, no LLM re-analysis.

## Usage

### 1. First-time profile

```
User: "who am I" or /honne:whoami
→ honne asks: scan scope (repo / global) + locale (ko / en / jp)
→ scans transcripts → extracts 7 axes autonomously → records claims
→ LLM synthesizes per-axis explanations + overall oneliner
→ renders .honne/persona.json + docs/honne.md
```

### 2. Single-axis

```
User: "내 말버릇만" or /honne:lexi
→ lexi scans transcripts → lexicon axis only → records claim autonomously
→ records claim asset for lexicon
```

### 3. Retrospective (after ≥ 2 runs)

```
User: "지난번이랑 비교" or /honne:compare
→ compare loads past claims + evolution assets (read-only)
→ groups by axis × time bucket
→ renders docs/honne-compare.md (identical / evolved / reversed / new)
```

### 4. Deletion (right to erasure)

```bash
bash scripts/purge.sh --all           # delete .honne/ entirely
bash scripts/purge.sh --keep-assets   # delete cache only, keep longitudinal claims
```

Both commands require typing `DELETE` to confirm. No network involvement.

## Hooks

honne registers a single hook, automatically on install. No configuration needed.

| Event | Trigger | What it does |
|-------|---------|--------------|
| `SessionEnd` | Session closes | Runs `scripts/index-session.sh` — appends session metadata (id, timestamps, sha256, message count) to `.honne/cache/index.json`. **No LLM call, no context injection, no analysis.** Silent-fail. |

The hook is passive infrastructure — it keeps the transcript index warm so later manual invocations of `whoami` / `lexi` / `compare` run faster. Analysis is always user-initiated.

## Your data

Everything stays local under `.honne/` in your current project directory:

| Path | Purpose |
|------|---------|
| `.honne/cache/scan.json` | Transcript scan cache (ephemeral, TTL 24h) |
| `.honne/cache/index.json` | SessionEnd hook output — metadata only, no message bodies |
| `.honne/persona.json` | Current 7-axis profile snapshot |
| `.honne/assets/claims.jsonl` | Autonomously recorded claims (longitudinal history) |
| `.honne/assets/rejection.jsonl` | Rejected claims (signal of what doesn't fit) |
| `.honne/assets/evolution.jsonl` | Cross-run diff results (identical / evolved / reversed) |

**Privacy**:
- No network calls. Everything processes locally.
- Sensitive patterns (API keys, tokens, webhooks, emails, phone numbers, home paths, IPs, credit cards — 18 patterns total) are redacted before any quote storage. See `scripts/honne_py/redact.py`.
- Assets are **never auto-injected** into session context. They load only when you explicitly invoke `compare` or call `query-assets.sh`.
- `CLAUDE.md` auto-injection is permanently prohibited (prevents self-reinforcement loop).

**Export**: `.honne/` is a plain directory. `tar czf my-honne.tgz .honne/` takes it anywhere. Your data, your move.

## Worktrees

Each worktree gets its own `.honne/` directory based on CWD. Persona snapshots and longitudinal assets are fully isolated per worktree — no shared state.

```
/project/.honne/                      ← main tree
/project/.claude/worktrees/A/.honne/  ← worktree A (independent)
/other/path/worktree-B/.honne/        ← worktree B (physical separation)
```

## Honest-use Notice

honne surfaces patterns **visible in your transcripts**. Those patterns are evidence of how you interacted with an LLM in specific contexts — they are not judgments of who you are as a person. A rejected claim means "this framing didn't fit this data", not "you failed". An antipattern means "this was observed", not "this is wrong about you".

If any output causes distress, delete it — `bash scripts/purge.sh --all`. Your data stays local; no network calls, no analytics.

**honne is a mirror for work patterns, not a mental-health tool.** For concerns about well-being, consult a qualified professional.

## Naming

- **honne** (本音) — the real voice under the official persona. Japanese origin, paired with *tatemae* (建前).
- **lexi** — lexicon + i (vocabulary axis only)
- **compare** — retrospective diff, past vs present (no transcript re-scan)

## Triad

honne sits between two sibling plugins — independent, connected by shared artifacts only:

```
harnish (make)  ──→  honne (know)  ──→  galmuri (keep)
  execution         reflection          refinement
```

- [harnish](https://github.com/jazz1x/harnish) — autonomous implementation engine
- [honne](https://github.com/jazz1x/honne) — evidence-backed self-observation (7-axis persona)
- [galmuri](https://github.com/jazz1x/galmuri) — gather, organize, and keep context (formerly *hanashi*)

## Development

Enable the repo's pre-commit hook once per clone:

```bash
git config core.hooksPath .githooks
```

The hook ([scripts/pre-commit.sh](scripts/pre-commit.sh)) validates staged files: shell lint (`shellcheck` or `bash -n` fallback), JSON syntax, `SKILL.md` frontmatter (`name` / `description` / SemVer `version`), script executable bits, and `.claude-plugin/marketplace.json` schema (the `source: "."` footgun is blocked here).

### Test suite

Run the hybrid test suite (pytest for Python helpers, bats for shell scripts + manifest schema):

```bash
bash tests/run.sh
```

Install requirements once — `brew install bats-core` (macOS) or `apt install bats` (Linux). Every test executes inside an ephemeral sandbox `HOME` and `CLAUDE_PROJECT_DIR`; real `~/.claude/` and `~/.honne/` are never touched. See [tests/setup.bash](tests/setup.bash) for the guard that aborts if a test somehow lands on the real home.

## Footnote

> *"A mirror that reflects without judging is rare. One that shows only what you already wrote is the most honest kind."*

honne never invents — it only surfaces what your transcripts already contain. If it tells you something you didn't say, we built the wrong tool.

## License

MIT — See [LICENSE](./LICENSE).
