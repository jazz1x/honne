# honne

> Claude Code plugin — self-observation from LLM transcripts

![version](https://img.shields.io/badge/version-0.0.1-blue)
![license](https://img.shields.io/badge/license-MIT-green)
![claude-code](https://img.shields.io/badge/claude--code-plugin-purple)

**honne** (本音, "true voice") — a local, evidence-backed mirror of how you actually work with LLMs. Beneath the official persona (*tatemae*) surfaces what your transcripts quietly record: recurring vocabulary, rejected suggestions, session rituals, the patterns you never named.

Everything runs locally. No network calls, no analytics. Every claim is HITL-approved before it enters your persona file. Your data lives under `.honne/` as plain JSONL — portable, inspectable, deletable.

[한국어](./README.ko.md) · [日本語](./README.jp.md)

## Skills

| Skill | Command | Role |
|-------|---------|------|
| **whoami** | `/honne:whoami` | Main orchestrator. 6-axis persona with per-axis HITL approval. |
| **lexi** | `/honne:lexi` | Lexicon axis only (high-frequency vocabulary, code-switching, onomatopoeia). |
| **compare** | `/honne:compare` | Read-only retrospective. Reads accumulated assets and shows changes over time. No transcript re-scan, no LLM re-analysis. |

Each skill operates in its own orbit, connected only through **shared artifacts on disk** (`.honne/cache/`, `.honne/persona.json`, `.honne/assets/*.jsonl`).

```
 transcripts (~/.claude/projects/**/*.jsonl)
      │
      │  honne  ──→  persona.json + docs/honne.md  (6-axis snapshot)
      │                  │
      │                  ├── record-claim.sh  ──→  .honne/assets/*.jsonl (longitudinal)
      │                  │
      │  lexi   ──→  persona.json (axis 1 only)
      │
 SessionEnd hook ──→  .honne/cache/index.json  (passive transcript index, metadata only)
                              │
 compare (read-only)  ──→  query-assets.sh  ──→  docs/honne-compare.md  (diff of past claims)
```

## Prerequisites

honne requires `jq` plus one of `python3` or `ripgrep`. Install before using:

```bash
# macOS — python3 is preinstalled
brew install jq
# (optional backend) brew install ripgrep

# Linux (apt) — python3 is preinstalled on most distros
sudo apt install jq
# (optional backend) sudo apt install ripgrep
```

Verify: `command -v jq && { command -v python3 || command -v rg; }`. Without both of these, scripts exit with code 4.

**Backend selection**: scripts auto-detect `python3` first (preferred — native Unicode tokenization, single-pass redaction). If absent, they fall back to `ripgrep`. No configuration needed.

## Install

### 1. Register the marketplace

Inside a Claude Code session, run:

```
/plugin marketplace add https://github.com/jazz1x/honne.git
```

Expected output:

```
✓ Marketplace 'honne' added (1 plugin)
```

### 2. Install the plugin

```
/plugin install honne --scope user
```

Expected output:

```
✓ Installed honne@0.0.1 — 3 skills registered (whoami, lexi, compare)
```

Scope choice:

| Scope | Effect | When to use |
|-------|--------|-------------|
| `--scope user` *(recommended)* | Installs into `~/.claude/` — honne can read transcripts across **all projects** | Normal use. Self-observation benefits from cross-project history. |
| `--scope local` | Installs into the current project's `.claude/` only | Sandboxed trial, or when you intentionally want single-project scope. |

### 3. Verify

```
/plugin list
```

You should see `honne` in the list. If the three canonical slash commands below autocomplete, you're good:

```
/honne:whoami
/honne:lexi
/honne:compare
```

The `SessionEnd` hook is registered automatically — no extra configuration.

### 4. Uninstall

```
/plugin uninstall honne
/plugin marketplace remove honne
```

Your `.honne/` directory is **not** touched by uninstall — your assets persist. Delete them manually with `bash scripts/purge.sh --all` if you want a clean wipe.

---

## Quickstart

Once installed, try the fastest path end-to-end:

```
# Inside a Claude Code session, in any project
/honne:whoami
```

Sample flow (simplified):

```
user   > /honne:whoami

step 1 > Scan scope — repo (current project) or global (all projects)?
user   > global

step 2 > Indexing transcripts under ~/.claude/projects/… (127 files)
step 3 > Redacting secrets (12 patterns) → cache .honne/cache/scan.json
step 4 > Extracting 6 axes: lexicon, cadence, stance, ritual, antipattern, evolution
step 5 > HITL per axis — [y]es / [n]o / [e]dit

        axis 1 · lexicon   : "일단", "~해볼게", frequent code-switch en↔ko  → [y/n/e]?
user   > y

        ... (axes 2–6 similarly) ...

step 6 > Write persona snapshot + longitudinal claim assets?
user   > y

✓ Saved: .honne/persona.json
✓ Saved: docs/honne.md
✓ Appended: .honne/assets/claim.jsonl (6 entries)
```

After ≥ 2 runs, you can compare past profiles:

```
/honne:compare
```

This reads only what's already on disk — no transcript re-scan, no LLM re-analysis.

## Usage

### 1. First-time profile

```
User: "나는 누구" or /honne:whoami
→ honne asks: scan scope — repo or global?
→ scans transcripts → extracts 6 axes → HITL per-axis (y / n / edit)
→ writes .honne/persona.json + docs/honne.md
→ approved claims recorded as assets in .honne/assets/claim.jsonl
```

### 2. Single-axis

```
User: "내 말버릇만" or /honne:lexi
→ lexi scans transcripts → lexicon axis only → HITL
→ records claim/rejection asset for lexicon
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
| `.honne/persona.json` | Current 6-axis profile snapshot |
| `.honne/assets/claim.jsonl` | HITL-approved claims (longitudinal history) |
| `.honne/assets/rejection.jsonl` | HITL-rejected claims (signal of what doesn't fit) |
| `.honne/assets/evolution.jsonl` | Cross-run diff results (identical / evolved / reversed) |

**Privacy**:
- No network calls. Everything processes locally.
- Sensitive patterns (API keys, tokens, webhooks, emails, phone numbers, home paths, IPs, credit cards — 12 patterns total) are redacted before any quote storage. See `scripts/scan-transcripts.sh` §redact-secrets.
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
- [honne](https://github.com/jazz1x/honne) — evidence-backed self-observation (6-axis persona)
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
