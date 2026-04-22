# honne

> Claude Code plugin — self-observation from LLM transcripts

**honne** (本音, "true voice") — a local, evidence-backed mirror of how you actually work with LLMs. Beneath the official persona (*tatemae*) surfaces what your transcripts quietly record: recurring vocabulary, rejected suggestions, session rituals, the patterns you never named.

[한국어](./README.ko.md) · [日本語](./README.jp.md)

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

Run Claude Code, then:

```
/plugin marketplace add https://github.com/jazz1x/honne.git
/plugin install honne --scope user
```

User scope is recommended — it enables global transcript scanning across all projects. Local scope (project-only) is supported but limits self-observation to a single project.

## Skills

| Skill | Command | Aliases | Role |
|-------|---------|---------|------|
| **honne** | `/honne:honne` | `/honne:whoami` · `/honne:hon-me` | Main orchestrator. 6-axis persona with per-axis HITL approval. |
| **lexi** | `/honne:lexi` | — | Lexicon axis only (high-frequency vocabulary, code-switching, onomatopoeia). |
| **compare** | `/honne:compare` | `/honne:diff` · `/honne:hon-back` | Read-only retrospective. Reads accumulated assets and shows changes over time. No transcript re-scan, no LLM re-analysis. |

Aliases come in two flavors: **semantic** (`whoami`, `diff`) for Unix-familiar entry points, and **brand-prefixed** (`hon-me`, `hon-back`) for harnish-style family visibility in the marketplace listing. Both redirect to the same core skill.

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

## Usage

### 1. First-time profile

```
User: "나는 누구" or /honne:honne
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

The hook is passive infrastructure — it keeps the transcript index warm so later manual invocations of `honne` / `lexi` / `compare` run faster. Analysis is always user-initiated.

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
- **whoami** / **hon-me** — aliases for `honne`. `whoami` is Unix-familiar; `hon-me` follows harnish's `har-*` brand prefix convention.
- **diff** / **hon-back** — aliases for `compare`. `diff` is the universal term; `hon-back` reads as "honne, look back".

## Triad

honne is one orbit of a three-plugin set:

- [harnish](https://github.com/jazz1x/harnish) — autonomous implementation engine (*makes*)
- [honne](https://github.com/jazz1x/honne) — self-observation from transcripts (*knows*)
- [galmuri](https://github.com/jazz1x/galmuri) — gather, organize, and keep context (*keeps*)

## License

MIT
