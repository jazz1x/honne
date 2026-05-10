---
name: whoami
version: 0.0.5
description: >
  Orchestrate 7-axis self-observation from local LLM transcripts.
  Autonomous evidence gathering + LLM-synthesized narrative.
  Triggers: "who am I", "self profile", "profile me", "honne whoami", "whoami self".
ssl:
  scheduling:
    anti_triggers:
      - "`.honne/persona.json` 이 이미 신선하고 새 transcript 가 없을 때 (compare 사용)"
      - "단일 axis 만 필요한 경우 (lexi 사용)"
  structural:
    scenes:
      - "Step 1: Scope+Locale HITL"
      - "Step 2: Scan"
      - "Step 3: Rejection reframe filter"
      - "Step 4: Per-axis autonomous record"
      - "Step 5: LLM narrative synthesis"
      - "Step 6: Render persona and report"
    branches:
      - "Step 2: scan exit non-zero → output stdout+stderr verbatim, halt"
      - "Step 3: validate exit 3 (overlap) → skip axis + log 'reframed'"
      - "Step 4: insufficient_evidence true → skip axis, continue"
      - "User responds 'n' on candidate → record rejection"
    resumable: true
  logical:
    tools: ["AskUserQuestion", "bash", "python3", "Read", "Write"]
    side_effects:
      reads:
        - ".honne/cache/scan.json"
        - ".honne/cache/axis-${axis}.json"
      writes:
        - ".honne/cache/scan.json  # overwrite"
        - ".honne/cache/axis-${axis}.json  # overwrite"
        - ".honne/assets/claims.jsonl  # append"
        - ".honne/assets/rejections.jsonl  # append"
        - ".honne/cache/narrative.json  # overwrite"
        - ".honne/persona.json  # overwrite"
        - "docs/honne.md  # overwrite"
      deletes: []
      network: []
    idempotent: false
    rollback: ".honne/assets/*.jsonl 의 마지막 RUN_ID 라인을 jq/grep 으로 수동 제거. .honne/ 와 docs/honne.md 는 .gitignore 대상이므로 git checkout 불가 — 실행 전 cp -r .honne .honne.bak 권장."
---

# honne — 7-Axis Self-Observation

**When invoked, execute Step 1 through Step 6 in order immediately. Do not summarize the skill or ask what the user wants — invocation itself is the request. Start by asking the Step 1 question.**

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

**Recording rejections**: If the user explicitly says "n" or rejects a candidate claim for any axis, record it as a rejection so Step 3 can filter it in future runs:
```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" record claim \
  --type rejection --axis "$axis" --scope "$SCOPE" \
  --claim "$CANDIDATE" --run-id "$RUN_ID" \
  --out ".honne/assets/rejections.jsonl"
```

<!-- TODO(evolutions): evolutions.jsonl cross-run diff tracking is not yet implemented. query --type evolution always returns []. Structural change required. -->


## Step 4: Per-axis autonomous record

For each axis from `axis list`, run each command separately — do NOT bundle into a script file or use heredocs:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" axis run "$axis" \
  --locale "$LOCALE" --scan .honne/cache/scan.json > ".honne/cache/axis-${axis}.json"
```

```bash
python3 -c "import json,sys; d=json.load(open('.honne/cache/axis-${axis}.json')); sys.exit(0 if d.get('insufficient_evidence') else 1)"
```
If exit 0 → skip this axis (insufficient evidence), continue to next.

```bash
python3 -c "import json; print(json.load(open('.honne/cache/axis-${axis}.json'))['candidate_claim'])"
```
Capture stdout as `CANDIDATE`.

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" record claim \
  --type claim --axis "$axis" --scope "$SCOPE" \
  --claim "$CANDIDATE" --run-id "$RUN_ID" \
  --quotes-file ".honne/cache/axis-${axis}.json" \
  --out ".honne/assets/claims.jsonl"
```

**HARD RULE** — execution constraints (test suite enforces):
- Each `bash` block runs as a direct shell command — no heredocs (`<< 'EOF'`), no script files, no command bundling.
- No intermediate writes to `/tmp` — use `.honne/cache/` instead. Writing to `/tmp` is a SKILL.md contract violation.

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

(d) Resolve the absolute path first:
```bash
python3 -c "import os; print(os.path.join(os.getcwd(), '.honne/cache/narrative.json'))"
```
Capture stdout as `NARRATIVE_PATH`. Then: `Write` the JSON response to the resolved path. If JSON parse fails or response is empty, skip saving.

## Step 6: Render persona and report

```bash
date -u +%Y-%m-%dT%H:%M:%SZ
```
Capture stdout as `NOW`.

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" render persona \
  --claims .honne/assets/claims.jsonl \
  --scope "$SCOPE" --locale "$LOCALE" --run-id "$RUN_ID" --now "$NOW" \
  --narrative .honne/cache/narrative.json \
  --out .honne/persona.json
```

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" render report \
  --persona .honne/persona.json --locale "$LOCALE" --out docs/honne.md
```

## Completion
Report saved files to `.honne/persona.json` and `docs/honne.md`. Use `/honne:compare` to review past observations.

Output the following next action suggestions to the user:

**Next actions**
- `/honne:persona` — generate two personas (antipattern × signature) from this profile
- `/honne:crush <topic>` — stage a live debate between the two personas
