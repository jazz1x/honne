---
name: crush
version: 0.0.5
description: >
  Stage a live debate between your persona's antipattern and signature voices on a topic.
  Triggers: "crush", "debate personas", "personas fight", "/honne:crush".
ssl:
  scheduling:
    anti_triggers:
      - ".honne/personas/{antipattern,signature,judge}.md 모두 부재 시 (persona 먼저 실행)"
  structural:
    scenes:
      - "Step 1: Get Topic"
      - "Step 2: Validate Personas"
      - "Step 3: Load Personas"
      - "Step 4: Round 1 — Antipattern Attacks"
      - "Step 5: Round 1+2 — Signature & Counter"
      - "Step 6: Judge's Verdict"
    branches:
      - "Step 1: skill_args empty → ask plain-text question"
      - "Step 2: all 3 exit 0 → proceed"
      - "Step 2: all 3 exit 66 → halt with persona suggestion"
      - "Step 2: mixed → halt with whoami+persona suggestion"
    resumable: false
  logical:
    tools: ["bash", "Read"]
    side_effects:
      reads:
        - ".honne/personas/*.md"
      writes: []
      deletes: []
      network: []
    idempotent: true
    rollback: null
---

# honne — Personas Debate (Live)

**When invoked, execute Step 1 through Step 6 in order immediately. If skill arguments are provided, use them as the topic; otherwise ask for one.**

## Step 1: Get Topic

If `skill_args` are non-empty: `TOPIC = skill_args joined with spaces`

Else: Ask plain-text question: "What topic do you want the two personas to debate?"

Set `TOPIC` from the reply.

## Step 2: Validate Personas

Count which persona files exist:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" persona check --persona .honne/personas/antipattern.md
```
```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" persona check --persona .honne/personas/signature.md
```
```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" persona check --persona .honne/personas/judge.md
```

Each returns exit 0 (exists) or exit 66 (missing). Branch on the combined result:

- **All three exit 0** → proceed to Step 3.
- **All three exit 66** → tell user: "No personas found. Run `/honne:persona` first to generate them." Stop.
- **Mixed** → tell user: "Debate requires both antipattern and signature personas plus a judge. Your persona has only one axis represented. Collect more sessions and re-run `/honne:whoami` + `/honne:persona` to generate a full set." Stop.

## Step 3: Load Personas

Read all three files into your mental context:
- `.honne/personas/antipattern.md` → extract system prompt and `name` from `# ` header
- `.honne/personas/signature.md` → extract system prompt and `name`
- `.honne/personas/judge.md` → extract system prompt

Extract the `name` from each by reading the first `# Name` line after the header.

## Step 4–5: Debate (4 turns)

For each turn: apply the named persona's system prompt mentally, produce 2-3 sentences, prefix with the label.

| # | Persona | Stance        | Label                          |
|---|---------|---------------|--------------------------------|
| 1 | antipattern | open attack on TOPIC          | `**[antipattern — {name}]**` |
| 2 | signature   | rebuttal to turn 1            | `**[signature — {name}]**`   |
| 3 | antipattern | counter-rebuttal to turn 2    | `**[antipattern — {name}]**` |
| 4 | signature   | closing argument              | `**[signature — {name}]**`   |

## Step 6: Judge's Verdict

Apply `.honne/personas/judge.md` system prompt. Produce a 2-3 sentence verdict: which approach is more situationally appropriate, and why.

Label: `**[Verdict]**` followed by the verdict.

---

## Output Format

Output the full transcript in this markdown structure:

```markdown
**Topic**: {TOPIC}

**[antipattern — {name}]**
{round 1 attack}

**[signature — {name}]**
{round 1 rebuttal}

**[antipattern — {name}]**
{round 2 counter}

**[signature — {name}]**
{round 2 closing}

**[Verdict]**
{judge verdict}
```

No file writes. The transcript is ephemeral — displayed only to the current session.
