---
name: persona
version: 0.0.3
description: >
  Conflict synthesis from antipattern × signature axes.
  Generates a working persona prompt from your observed patterns.
  Triggers: "persona", "activate persona", "who am I as Claude", "honne persona".
---

# honne — Persona Synthesis

**When invoked, execute Step 1 through Step 5 in order immediately. Do not summarize the skill or ask what the user wants — invocation itself is the request. Start by asking the Step 1 question.**

## Step 1: Locale HITL

Invoke `AskUserQuestion` tool:

- `question`: "Locale?"
- `options`: `[{"label":"ko","description":"한국어"},{"label":"en","description":"English"},{"label":"jp","description":"日本語"}]`

Set `LOCALE` from the reply. Do not use plain-text Q&A — arrow-key selection only.

## Step 2: Load and Validate

Check that persona.json exists:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" persona check --persona .honne/persona.json
```

- Exit 66 → tell user: "`.honne/persona.json` not found. Please run `/honne:whoami` first to generate your persona." Stop.
- Exit 0 → proceed.

Check staleness:

```bash
python3 -c "import json,datetime; d=json.load(open('.honne/persona.json')); ts=datetime.datetime.fromisoformat(d.get('generated_at','2000-01-01T00:00:00Z').replace('Z','+00:00')); print((datetime.datetime.now(datetime.timezone.utc)-ts).days)"
```
Capture stdout as `STALE_DAYS`.

If `STALE_DAYS` exceeds 7 (or the value of `HONNE_PERSONA_STALE_DAYS` if set): warn "persona.json last updated {STALE_DAYS} days ago — consider re-running `/honne:whoami`." Then continue.

## Step 3: Build Conflict Payload

Read `.honne/persona.json` in your mental context. Construct CONFLICT_PAYLOAD as a JSON object without writing to any file or using heredocs:

```
CONFLICT_PAYLOAD = {
  "locale": "<LOCALE>",
  "antipattern": {
    "claim": "<axes.antipattern.claim>",
    "explanation": "<axes.antipattern.explanation>",
    "evidence_strength": <axes.antipattern.evidence_strength>
  }  — or null if antipattern axis is absent or claim is null,
  "signature": {
    "claim": "<axes.signature.claim>",
    "explanation": "<axes.signature.explanation>",
    "evidence_strength": <axes.signature.evidence_strength>
  }  — or null if signature axis is absent or claim is null,
  "supporting_axes": {
    "<axis>": {"claim": "...", "explanation": "...", "evidence_strength": <val>}
    for each of the 5 remaining axes: lexicon, reaction, workflow, obsession, ritual
  }
}
```

Do NOT use `python3 << 'EOF'` or any heredoc. Assemble the payload in your mental context from the persona.json data you just read.

## Step 4: LLM Synthesis

(a) Read synthesis prompt:

`Read "${CLAUDE_PLUGIN_ROOT}/skills/persona/templates/persona_synthesis_prompt.${LOCALE}.md"`

(b) Apply the synthesis prompt system instructions to yourself, with CONFLICT_PAYLOAD as the user input. Produce a STRICT JSON response:

```json
{
  "conflict_present": true,
  "persona_antipattern": {
    "name": "...",
    "oneliner": "...",
    "system_prompt": "..."
  },
  "persona_signature": {
    "name": "...",
    "oneliner": "...",
    "system_prompt": "..."
  },
  "judge_system_prompt": "..."
}
```

Branch rules (enforced by synthesis prompt template):
- `conflict_present = true`: both axes present → generate two separate personas (antipattern and signature) + judge. All three fields REQUIRED.
- `conflict_present = false`, one axis null: set absent persona to null. `judge_system_prompt` is null.
- `conflict_present = false`, both axes null: all persona fields are null.

Constraints: each `system_prompt` ≤ 1000 tokens. `judge_system_prompt` ≤ 500 tokens. `name` ≤ 12 chars. `oneliner` ≤ 25 words.

(c) Save result: `Write` the JSON to `{PWD}/.honne/cache/persona-synthesis.json`. If JSON parse fails or response is empty, skip saving and output raw text with a warning.

## Step 5: Render Personas

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" render personas --persona .honne/persona.json --synthesis .honne/cache/persona-synthesis.json --locale "$LOCALE" --out-dir .honne/personas
```

Non-zero exit → output the raw synthesis fields with a warning that file render failed.

Output to user — choose the template matching the synthesis JSON state you saved in Step 4(c). Use `LOCALE` (ko/en/jp).

**Case A — `conflict_present=true`** (both personas + judge):

- ko: `두 인격이 생성되었습니다:\n- .honne/personas/antipattern.md — {persona_antipattern.name}\n- .honne/personas/signature.md — {persona_signature.name}\n- .honne/personas/judge.md — 심판자\n\n두 인격을 붙이려면 /honne:crush <주제>를 실행하세요.`
- en: `Two personas generated:\n- .honne/personas/antipattern.md — {persona_antipattern.name}\n- .honne/personas/signature.md — {persona_signature.name}\n- .honne/personas/judge.md — judge\n\nRun /honne:crush <topic> to stage a live debate.`
- jp: `ふたつのペルソナが生成されました:\n- .honne/personas/antipattern.md — {persona_antipattern.name}\n- .honne/personas/signature.md — {persona_signature.name}\n- .honne/personas/judge.md — 審判者\n\nライブ討論を行うには /honne:crush <テーマ> を実行してください。`

**Case B — `conflict_present=false`, exactly one persona non-null**:

- ko: `하나의 인격만 생성되었습니다 (반대 축이 감지되지 않음):\n- .honne/personas/{slot}.md — {persona.name}\n\n/honne:crush 토론은 두 축이 모두 필요합니다. 더 많은 세션을 수집한 뒤 /honne:whoami를 재실행하세요.`
- en: `Only one persona generated (opposite axis not detected):\n- .honne/personas/{slot}.md — {persona.name}\n\n/honne:crush debate requires both axes. Collect more sessions and re-run /honne:whoami.`
- jp: `ペルソナが1つだけ生成されました (反対軸が検出されませんでした):\n- .honne/personas/{slot}.md — {persona.name}\n\n/honne:crush ディベートには両軸が必要です。さらにセッションを収集し /honne:whoami を再実行してください。`

Where `{slot}` is `antipattern` or `signature` depending on which is non-null.

**Case C — `conflict_present=false`, both personas null**:

- ko: `인격이 생성되지 않았습니다 (두 축 모두 감지되지 않음). 세션을 더 수집한 뒤 /honne:whoami를 재실행하세요.`
- en: `No personas generated (neither axis detected). Collect more sessions and re-run /honne:whoami.`
- jp: `ペルソナは生成されませんでした (両軸とも検出されず)。セッションを追加収集し /honne:whoami を再実行してください。`

**IMPORTANT**: This skill only generates files. Do not claim the persona is running, applied, or in use. Personas are independent artifacts — users invoke `/honne:crush` for live debate.
