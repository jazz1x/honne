---
name: whoami
version: 0.0.1
description: >
  Orchestrate 6-axis self-observation from local LLM transcripts.
  Autonomous evidence gathering + LLM-synthesized narrative.
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
Capture `RUN_ID` from result: `RUN_ID=$(python3 -c 'import json; print(json.load(open(".honne/cache/scan.json"))["run_id"])')`
Non-zero exit → output stdout+stderr verbatim to user, stop. Do not interpret exit codes.

## Step 3: Rejection reframe filter (skip candidate)
For each axis, run: `bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" query --base-dir ".honne" --tag "<axis>" --type rejection --scope "$SCOPE"`
Before Step 4 records each axis, pipe the candidate through `bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" axis validate --text "$candidate" --locale "$LOCALE" --skip-if-overlaps "$rejection_text"` — exit 3 = overlap, skip and log "reframed". 모든 변수는 큰따옴표 인용 필수(공백·특수문자 안전). LLM 호출 없음.

## Step 4: Per-axis autonomous record

For each axis from `axis list`, run each command separately — do NOT bundle into a script file or use heredocs:

```bash
AXIS_JSON=$(bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" axis run "$axis" \
  --locale "$LOCALE" --scan .honne/cache/scan.json)
```

```bash
echo "$AXIS_JSON" | python3 -c "import sys,json; sys.exit(0 if json.load(sys.stdin).get('insufficient_evidence') else 1)"
```
If exit 0 → skip this axis (insufficient evidence), continue to next.

```bash
CANDIDATE=$(echo "$AXIS_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['candidate_claim'])")
QUOTES_JSON=$(echo "$AXIS_JSON" | python3 -c "import sys,json; print(json.dumps(json.load(sys.stdin)['quotes']))")
```

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" record claim \
  --type claim --axis "$axis" --scope "$SCOPE" \
  --claim "$CANDIDATE" --run-id "$RUN_ID" \
  --quotes-json "$QUOTES_JSON" \
  --out ".honne/assets/claims.jsonl"
```

**IMPORTANT**: Execute each `bash` block as a direct shell command. Do NOT write to `/tmp`, do NOT use shell heredocs (`<< 'EOF'`), do NOT bundle commands into a script file. Run inline commands only.

## Step 5: LLM narrative synthesis

Invoke Claude (your own mental reasoning) to synthesize explanations and a one-liner:

(a) Read synthesis prompt: `Read "${CLAUDE_PLUGIN_ROOT}/skills/whoami/templates/synthesis_prompt.${LOCALE}.md"`

(b) Build USER_PAYLOAD from the claims recorded in Step 4. You already have the AXIS_JSON outputs in memory — construct the payload directly as a JSON object without re-reading files:

```
USER_PAYLOAD = {
  "locale": "<LOCALE>",
  "claims": {
    "<axis>": {"claim": "<CANDIDATE>", "evidence_count": <len(quotes)>} for each recorded axis,
    "<skipped_axis>": null for each axis that had insufficient evidence
  }
}
```

Do NOT use `python3 << 'PYEOF'` or any heredoc to build this payload. Assemble it in your mental context from the Step 4 outputs already known.

(c) Synthesize: Apply synthesis_prompt system instructions to yourself + USER_PAYLOAD as user input. Produce STRICT JSON response.

(d) Save result: `Write` the JSON response to `{PWD}/.honne/cache/narrative.json` (absolute path required). If JSON parse fails or response is empty, skip saving (narrative.json remains absent).

## Step 6: Render persona and report

```bash
NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ)
bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" render persona \
  --claims .honne/assets/claims.jsonl \
  --scope "$SCOPE" --locale "$LOCALE" --run-id "$RUN_ID" --now "$NOW" \
  --narrative .honne/cache/narrative.json \
  --out .honne/persona.json

bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" render report \
  --persona .honne/persona.json --locale "$LOCALE" --out docs/honne.md
```

## Completion
Report saved files to `.honne/persona.json` and `docs/honne.md`. Use `/honne:compare` to review past observations.

Output the following next action suggestions to the user:

**다음 액션 제안**
- 이 형태로 나의 분신(페르소나) 구현해보기
- 효율적인 토큰 사용을 위한 분석 가이드

*(these features are coming soon.)*
