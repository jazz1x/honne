# criteria-persona.md

> Reference for honne main skill's per-axis reasoning.

## Axes

| # | Axis | Source | Gate | Nature |
|---|---|---|---|---|
| 1 | Lexicon | extract-lexicon.sh | ≥ 3 sessions | Behavioral vocabulary patterns |
| 2 | Reaction | internal (short affirmations/doubts) | ≥ 5 occurrences | Dispositional response tendency |
| 3 | Workflow | internal N-gram sequences | ≥ 2 sessions recurring | Cross-session behavioral flow |
| 4 | Obsession | detect-recurrence.sh | ≥ 3 sessions | Topic recurrence frequency |
| 5 | Ritual | internal (session boundary patterns) | ≥ 3 sessions | Dispositional session habits |
| 6 | Antipattern | internal (rejection language) | ≥ 3 sessions | Rejected framing patterns |
| 7 | Signature | internal (decisive close + targeted request patterns) | ≥ 3 sessions | Characteristic closing and precision patterns |

## Horoscope defenses

Claims MUST NOT contain:
- Time qualifiers without condition: "sometimes", "at times", "in certain situations"
- Vague universals: "often", "generally", "usually" without frequency anchor
- Korean: "때로는", "상황에 따라", "적절히"
- Japanese: "時に", "場合によって"

Every claim requires ≥ 1 quote. No quote → `[insufficient evidence]` and axis item skipped.

## Claim wording guidelines

Observed patterns are **evidentiary, not evaluative**. The `claim` field MUST describe what was observed, not what that implies about the user as a person.

Claims must anchor in **session count** (number of distinct sessions where the pattern occurred) or occurrence count — never in dispositional generalizations. The JSON field `session_count` (snake_case) carries the value; the phrase "session count" is the natural-language anchor in prose and in this document.

### Examples

✅ Good:  
- "Uses 'actually' 10+ times across sessions (lexicon)"  
- "Repeats structure 'let me check first' in workflow queries (workflow)"  
- "Asks about performance 3+ times in same month (obsession)"

❌ Bad (evaluative):  
- "Is actually very careful" (evaluative + assumes intent)  
- "Gets obsessed with details" (judgment, not observation)  
- "Lacks attention to edge cases" (inference from pattern, not pattern itself)  
- "Always rushes through reviews" (horoscope: "always")

## Schema

```jsonc
{
  "session_id": "unique-string",
  "started_at": "2026-04-22T10:30:00Z",
  "scope": "repo | global",
  "axes": {
    "lexicon": { 
      "claim": "...", 
      "support_count": N,    // number of supporting instances
      "session_count": M,    // number of sessions where observed
      "quotes": [...]        // evidence samples
    },
    "reaction": { "claim": "...", "support_count": N, "session_count": M, "quotes": [...] },
    // ... other axes
  },
  "recorded_at": "2026-04-22T11:00:00Z"
}
```
