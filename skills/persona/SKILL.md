---
name: persona
version: 0.0.2
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
bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" render persona-prompt --check-only --persona .honne/persona.json --locale "$LOCALE"
```

- Exit 66 → tell user: "`.honne/persona.json` not found. Please run `/honne:whoami` first to generate your persona." Stop.
- Exit 0 → proceed.

Check staleness:

```bash
STALE_DAYS=$(python3 -c "import json,datetime; d=json.load(open('.honne/persona.json')); ts=datetime.datetime.fromisoformat(d.get('generated_at','2000-01-01T00:00:00Z').replace('Z','+00:00')); print((datetime.datetime.now(datetime.timezone.utc)-ts).days)")
```

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

```bash
Read "${CLAUDE_PLUGIN_ROOT}/skills/persona/templates/persona_synthesis_prompt.${LOCALE}.md"
```

(b) Apply the synthesis prompt system instructions to yourself, with CONFLICT_PAYLOAD as the user input. Produce a STRICT JSON response:

```json
{
  "verdict": "...",
  "character_oneliner": "...",
  "system_prompt": "...",
  "conflict_present": true,
  "debate": {
    "antipattern_voice": "...",
    "signature_voice": "...",
    "resolution": "..."
  }
}
```

Branch rules (enforced by synthesis prompt template):
- `conflict_present = true`: both axes present → stage antipattern vs. signature as a three-voice debate (prosecutor / defender / judge). `debate` field is REQUIRED.
- `conflict_present = false`, one axis null: dominant-trait portrait, label absent side as "not yet observed". `debate` may be null or omitted.
- `conflict_present = false`, both axes null: portrait from supporting 5 axes only. `debate` may be null or omitted.

Constraints: `system_prompt` ≤ 1500 tokens. `character_oneliner` ≤ 20 words. Each `debate` voice is 2–3 sentences, declarative only.

(c) Save result: `Write` the JSON to `{PWD}/.honne/cache/persona-synthesis.json`. If JSON parse fails or response is empty, skip saving and output raw text with a warning.

## Step 5: Render and Activate

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" render persona-prompt --persona .honne/persona.json --synthesis .honne/cache/persona-synthesis.json --locale "$LOCALE" --out .honne/persona-prompt.md
```

Non-zero exit → output the raw synthesis fields with a warning that file render failed.

Output to user:

**Character**: `character_oneliner`

**Verdict**: `verdict`

**The Inner Clash** (only when `conflict_present = true`):
- **antipattern side**: `debate.antipattern_voice`
- **signature side**: `debate.signature_voice`
- **verdict**: `debate.resolution`

**Your persona system prompt**:

```
[system_prompt]
```

Tell the user: "This persona is active for the current session. The full system prompt + activation directive have been saved to `.honne/persona-prompt.md` — paste it into any future session or LLM to restore this persona."

Then, as the final line of your output, self-apply the activation directive by stating:

> **From this message forward, I will respond as the person described above until you say "drop persona" or "reset persona".**

**IMPORTANT**: Do not write to CLAUDE.md. Persona activation is in-session only — achieved by (1) the activation_directive section rendered into `.honne/persona-prompt.md` (visible in context), and (2) the final self-statement above. After this skill ends, subsequent turns in the same session should embody the persona.
