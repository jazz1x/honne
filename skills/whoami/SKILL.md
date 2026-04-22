---
name: whoami
version: 0.0.1
description: >
  Orchestrate 6-axis self-observation from local LLM transcripts.
  Evidence-backed persona with per-axis HITL approval.
  Triggers: "who am I", "self profile", "profile me", "honne", "whoami self".
---

# honne — 6-Axis Self-Observation

## Step 1: Scope HITL

Ask user: "Scan scope — `repo` (current project) or `global` (all projects)?"

Wait for explicit `repo` or `global`. Ambiguous replies → re-ask.

## Step 2: Scan transcripts

Run:
```bash
HONNE_ROOT="${CLAUDE_PLUGIN_ROOT}"
bash "$HONNE_ROOT/scripts/scan-transcripts.sh" \
  --scope "$SCOPE" --since "2020-01-01" \
  --cache ".honne/cache/scan.json" \
  --index-ref ".honne/cache/index.json" \
  --redact-secrets
```

If exit 2 (no transcripts) → report "insufficient data. change scope?" → end.

## Step 3: Pre-HITL rejection reframe filter

For each axis:
```bash
bash "$HONNE_ROOT/scripts/query-assets.sh" \
  --tag "<axis>" --type rejection --scope "$SCOPE" --out stdout
```

Store past rejections in-memory (NOT injected). Use as "skip candidate" filter before presenting HITL claims. If a candidate claim text overlaps significantly with a past rejection, reframe or skip with a log.

## Step 4: Per-axis processing

For axis in [lexicon, reaction, workflow, obsession, ritual, antipattern]:
- Statistical extraction (lexicon → extract-lexicon.sh; obsession → detect-recurrence.sh; others → internal logic within this skill)
- LLM summary (must reference evidence-gather output)
- HITL: present claim with quotes, ask (y / n / edit). Ambiguous → re-ask.
- y → record-claim.sh --type claim ...
- n → record-claim.sh --type rejection ...
- edit → use edited text, record-claim.sh --type claim ...

## Step 5: Save .honne/persona.json

Schema per architecture PRD §3.2. Approved axes only.

## Step 6: Render docs/honne.md

Human-readable report. Every claim must have ≥ 1 quote or be marked [insufficient evidence].

Forbidden phrases (horoscope): "at times", "sometimes", "in certain situations", "때로는", "상황에 따라", "적절히".

## Step 7: Evolution link (2nd+ run)

If .honne/assets/claim.jsonl has entries from before this run:
- query-assets.sh --tag <axis> --type claim --scope "$SCOPE" --until <this-run-ts>
- LLM pair classifier: {past_claim, present_claim} → label ∈ {identical, evolved, reversed, unrelated} with confidence
- confidence < 0.7 → unrelated
- identical → set prior_id on current claim asset, no new evolution
- evolved / reversed → record-claim.sh --type evolution --prior-id <past> ...

## Completion

Report saved files + remind user: "/honne:compare to review past."

## LLM Prompt Templates

### Pair classifier (Step 7)

When comparing past vs present claim within same axis:

```
System: You classify the relationship between two evidence-backed claims about the same user on the same axis.

Input:
  Axis: {axis}
  Past claim (recorded {past_ts}): "{past_claim}"
  Present claim (recorded {present_ts}): "{present_claim}"

Labels:
  - identical: same observation, different wording
  - evolved:   same axis, concrete content changed (vocabulary substitution OR frequency shift OR scope expansion)
  - reversed:  present observation contradicts past observation
  - unrelated: observations about different phenomena

Respond with JSON only:
  { "label": "<one-of-four>", "confidence": <0.0-1.0>, "rationale": "<one short sentence>" }

Rule: if confidence < 0.7, force label = "unrelated".
```

### Rejection overlap detector (Step 3)

When deciding whether to skip a candidate claim due to past rejection:

```
System: Decide whether the present candidate claim overlaps semantically with a past rejected claim (same user, same axis).

Input:
  Axis: {axis}
  Past rejection (recorded {past_ts}): "{past_rejection}"
  Present candidate: "{present_candidate}"

Respond with JSON only:
  { "overlap": true | false, "confidence": <0.0-1.0>, "rationale": "<one short sentence>" }

Rule: overlap=true only if confidence >= 0.7. Otherwise proceed with the present candidate as-is.
```

### Horoscope guard (Step 6)

Before writing a claim into docs/honne.md, self-check:

```
System: Does the following claim contain any horoscope-style hedge? (vague time qualifiers, vague universals, phrases like "sometimes", "at times", "generally", "in certain situations", or Korean "때로는"/"상황에 따라"/"적절히", or Japanese "時に"/"場合によって")

Input: "{claim_text}"

Respond JSON only:
  { "horoscope": true | false, "matched_phrase": "<str or empty>" }

If horoscope=true, the claim is rejected and the axis item is marked [insufficient evidence].
```
