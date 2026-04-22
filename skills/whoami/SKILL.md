---
name: whoami
version: 0.0.2
description: >
  Orchestrate 6-axis self-observation from local LLM transcripts.
  Evidence-backed persona with per-axis HITL approval.
  Triggers: "who am I", "self profile", "profile me", "honne", "whoami self".
---

# honne — 6-Axis Self-Observation

**When invoked, execute Step 1 through Step 7 in order immediately. Do not summarize the skill or ask what the user wants — invocation itself is the request. Start by asking the Step 1 question.**

## Step 1: Scope + Locale HITL

Invoke `AskUserQuestion` tool with two questions in a single call:

(a) Scope:
- `question`: "Scan scope?"
- `options`: `[{"label":"repo","description":"current project only"},{"label":"global","description":"all projects"}]`

(b) Locale:
- `question`: "Locale?"
- `options`: `[{"label":"ko","description":"한국어"},{"label":"en","description":"English"},{"label":"jp","description":"日本語"}]`

Set `SCOPE` and `LOCALE` from the two replies. Do not use plain-text Q&A — arrow-key selection only.

## Step 2: Scan
Run: `bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" scan --scope "$SCOPE" --cache ".honne/cache/scan.json"`
Non-zero exit → output stdout+stderr verbatim to user, stop. Do not interpret exit codes.

## Step 3: Rejection reframe filter (skip candidate)
For each axis, run: `bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" query --base-dir ".honne" --tag "<axis>" --type rejection --scope "$SCOPE"`
Before Step 4's HITL for each axis, pipe the candidate through `bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" axis validate --text "$candidate" --locale "$LOCALE" --skip-if-overlaps "$rejection_text"` — exit 3 = overlap, skip HITL and log "reframed". 모든 변수는 큰따옴표 인용 필수(공백·특수문자 안전). LLM 호출 없음.

## Step 4: Per-axis HITL

For each axis from `axis list`:

(a) Run `bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" axis run "$axis" --locale "$LOCALE" --scan .honne/cache/scan.json --emit-hitl-block`. Capture stdout as `$block`.

(b) **Output `$block` to the user EXACTLY as received. Do not paraphrase, shorten, translate, or prepend labels like "Respond:". Do not re-render in your own words. Echo only.** If `$block` shows `[insufficient evidence]`, skip (c) and proceed to next axis.

(c) Invoke `AskUserQuestion` tool with:
- `question`: "Accept this claim?"
- `options`: `[{"label":"y","description":"accept"},{"label":"n","description":"reject"},{"label":"edit","description":"rephrase"}]`

(d) Handle reply:
- `y` → run:
  ```
  bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" record claim \
    --type claim --axis "$axis" --scope "$SCOPE" \
    --claim "$candidate" --out ".honne/assets/claims.jsonl"
  ```
  `$candidate` is the `candidate` field from `axis run` JSON mode (run without `--emit-hitl-block` to get JSON).
- `n` → same command but `--type rejection` and `--out ".honne/assets/rejections.jsonl"`, `--claim "$candidate"`.
- `edit` → ask user for replacement text `$edited`, validate via `bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" axis validate --text "$edited" --locale "$LOCALE"`. Exit 0 → record as claim with `--claim "$edited"`. Non-zero → show user the stderr and re-ask for edit.

## Step 5: Save persona
Approved axes only → `.honne/persona.json`.

## Step 6: Render docs/honne.md
Quotes required per claim (axis run already guarantees). No model paraphrase.

## Step 7: Evolution link (2nd+ run)
`honne query --tag <axis> --type claim --scope "$SCOPE" --until <ts>` → pair classifier (LLM, external to axis.py).

## Completion
Report saved files. "/honne:compare to review past."
