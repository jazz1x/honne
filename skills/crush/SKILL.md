---
name: crush
version: 0.0.2
description: >
  Stage a live debate between your persona's antipattern and signature voices on a topic.
  Triggers: "crush", "debate personas", "personas fight", "/honne:crush".
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
A=0; S=0; J=0
[ -f .honne/personas/antipattern.md ] && A=1
[ -f .honne/personas/signature.md ] && S=1
[ -f .honne/personas/judge.md ] && J=1
echo "a=$A s=$S j=$J"
```

Branch on the result:

- **All three present (`a=1 s=1 j=1`)** → proceed to Step 3.
- **Nothing present (`a=0 s=0 j=0`)** → tell user: "No personas found. Run `/honne:persona` first to generate them." Stop.
- **Partial (`a+s+j` ∈ {1,2})** → tell user: "Debate requires both antipattern and signature personas plus a judge. Your persona has only one axis represented. Collect more sessions and re-run `/honne:whoami` + `/honne:persona` to generate a full set." Stop.

## Step 3: Load Personas

Read all three files into your mental context:
- `.honne/personas/antipattern.md` → extract system prompt and `name` from `# ` header
- `.honne/personas/signature.md` → extract system prompt and `name`
- `.honne/personas/judge.md` → extract system prompt

Extract the `name` from each by reading the first `# Name` line after the header.

## Step 4: Round 1 — Antipattern Attacks

Apply `.honne/personas/antipattern.md` system prompt mentally.

Produce a 2-3 sentence attack on TOPIC from the antipattern perspective.

Label output: `**[antipattern — {name}]**` followed by the attack.

## Step 5: Round 1 + Round 2 — Signature & Counter

Apply `.honne/personas/signature.md` system prompt.

Produce a 2-3 sentence rebuttal to antipattern's attack.

Label: `**[signature — {name}]**` followed by the rebuttal.

Then, back to antipattern perspective: 2-3 sentence counter-rebuttal.

Label: `**[antipattern — {name}]**` followed by the counter.

Then, back to signature perspective: 2-3 sentence closing argument.

Label: `**[signature — {name}]**` followed by the closing.

## Step 6: Judge's Verdict

Apply `.honne/personas/judge.md` system prompt.

Produce a 2-3 sentence verdict: which approach is more situationally appropriate, and why.

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
