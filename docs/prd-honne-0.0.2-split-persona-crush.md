# honne 0.0.2 — Split-Persona Pivot + `/honne:crush` PRD

> Created: 2026-04-24
> Status: draft (supersedes `prd-honne-0.0.2-persona.md` persona sections)
> Estimated scale: Medium (2–3 days across 5 Haiku phases)

---

## §1 Problem Definition

### 1.1 Current State (As-Is, on branch `feat/0.0.2-persona-hardening`)

The shipped `/honne:persona` (commit `3a8edc6`) produces **one resolved persona** from the antipattern × signature conflict. It embeds a pre-recorded three-voice debate transcript inside `.honne/persona-prompt.md` and claims session activation via an activation directive.

Observed failure (real e2e run):
- The "debate" is a static block — the user cannot make the two sides fight about a new topic.
- "Activation" is text-only; subsequent turns do not actually embody the persona.
- The user's original intent was **two independent personas that clash on demand**, not one resolved character with a frozen fight attached.

### 1.2 Target State (To-Be)

`/honne:persona` generates **two separate personas** (and a neutral judge) as standalone system prompts on disk. A new skill `/honne:crush <topic>` loads those prompts and stages a live multi-round debate on any user-supplied topic.

```
persona.json ──→ synthesis LLM ──→ persona_antipattern.system_prompt
                              └──→ persona_signature.system_prompt
                              └──→ judge_system_prompt
                                        ↓
                         .honne/personas/{antipattern,signature,judge}.md

/honne:crush "주제"
   ↓
 Claude reads antipattern.md → attacks topic (round 1)
 Claude reads signature.md   → rebuts         (round 1)
 Claude reads antipattern.md → counters       (round 2)
 Claude reads signature.md   → closes         (round 2)
 Claude reads judge.md       → verdict
   ↓
 full transcript printed to user
```

### 1.3 Impact

Without this pivot:
- `/honne:persona` ships with a broken activation metaphor and a single static debate.
- User's "분신술" vision (two separable selves that can fight) remains unrealized.

With this pivot:
- Two persona files are first-class, portable artifacts (paste into any LLM).
- `/honne:crush` delivers the **live fight** — no pre-recording.
- Activation is removed from `/honne:persona`; it becomes generation-only, solving the "활성화가 안 된다" problem by not pretending to.

---

## §2 Design Decision

### Alternative A: Keep resolved persona + add `/honne:crush` that re-derives sides at runtime

- Each crush call re-extracts antipattern + signature from persona.json, spins up ephemeral role prompts.
- Pro: minimal change to existing persona flow.
- Con: debate prompts are recomputed every time; two identities never materialize as artifacts.

### Alternative B: Split personas at generation time, remove activation (SELECTED)

- `/honne:persona` outputs 2 or 3 persistent files under `.honne/personas/`.
- `/honne:crush` reads those files and switches system prompts mid-skill.
- Pro: two identities are concrete, paste-able artifacts. Matches user's mental model ("분신술로 둘이 된다").
- Pro: clean separation — generator vs. stager.
- Con: breaking schema change vs. current `persona-synthesis.json`. Requires rewrite of synthesis + render + SKILL + tests. CLI command `render persona-prompt` → `render personas` (breaking).
- Selected: zero users yet (0.0.2 unreleased), so breaking is free. The artifact model matches the user's explicit request.

**Validity condition**: revisit if users later want a "resolved persona" mode for pure embodiment without debate — could be added as `/honne:as <antipattern|signature>` in 0.0.3 without disturbing this structure.

---

## §3 Scope

Internal breaking changes only. No backward compatibility needed (0.0.2 never released). No feature flag. The general hardening items from `prd-honne-0.0.2-skill-hardening.md` (`--quotes-file`, setup skill, HARD RULE, path resolve) remain as-is — this PRD only pivots the persona subsystem.

Out of scope for this PRD:
- `/honne:as` single-embodiment mode (deferred to 0.0.3).
- Multi-round debate beyond 2 rounds + verdict.
- External API / web integration for debate hosting.

---

## §4 Implementation Spec

### 4.1 Affected Files

| File | Change | Notes |
|------|--------|-------|
| `scripts/honne_py/persona_prompt.py` | Rewrite | Keep `build_conflict_payload`. Delete `render_persona_prompt` + `_load_persona_prompt_template`. Add `render_personas`. |
| `scripts/honne_py/cli.py` | Modify | Remove `render persona-prompt` subcommand. Add `render personas` + `persona check`. |
| `skills/persona/templates/persona_synthesis_prompt.{ko,en,jp}.md` | Rewrite | New output schema (split personas + judge). |
| `skills/persona/templates/persona_prompt.{ko,en,jp}.md` | Delete | No longer used — replaced by `persona_render.{locale}.md`. |
| `skills/persona/templates/persona_render.{ko,en,jp}.md` | Add | Single compact template per locale — `{name}` / `{oneliner}` / `{system_prompt}`. |
| `skills/persona/SKILL.{md,ko.md,jp.md}` | Rewrite Step 4–5 | New schema in Step 4. Step 5 is generate-only, no activation. |
| `skills/crush/SKILL.{md,ko.md,jp.md}` | Add | New skill, 6-step flow. |
| `tests/unit_persona_prompt_test.py` | Rewrite | Drop old `TestRenderPersonaPrompt`. Add `TestRenderPersonas`. |
| `tests/fixtures/persona/synthesis_full.json` | Rewrite | New schema. |
| `tests/fixtures/persona/synthesis_no_antipattern.json` | Add | `persona_antipattern=null`, `conflict_present=false`. |
| `tests/fixtures/persona/synthesis_no_axes.json` | Add | Both null. |
| `tests/unit_persona_skill_test.py` | Update | Assertions for new Step 4 schema + Step 5 render cmd. |
| `tests/unit_crush_skill_test.py` | Add | Contract tests for `/honne:crush`. |
| `tests/unit_skill_contract_test.py` | Update | `test_skill_step4_has_quotes_file_arg` unchanged; any persona step assertions updated. |
| `CHANGELOG.md` | Update 0.0.2 | Remove debate/activation wording; add split-persona + crush. |
| `README.md` / `README.ko.md` / `README.jp.md` | Update | persona row description; add crush row. |
| `docs/e2e-persona.md` | Update | Drop activation check; add personas/ + crush transcript checks. |

### 4.2 Synthesis JSON Schema (output of LLM in persona Step 4)

```json
{
  "conflict_present": true,
  "persona_antipattern": {
    "name": "과잉명세형",
    "oneliner": "나는 overspec 255회의 장본인이다",
    "system_prompt": "당신은 과잉명세형 인물입니다. ... ≤1000 tokens"
  },
  "persona_signature": {
    "name": "정밀타격형",
    "oneliner": "나는 targeted_request 573회의 정확도다",
    "system_prompt": "당신은 정밀타격형 인물입니다. ..."
  },
  "judge_system_prompt": "당신은 두 인격의 주장을 듣고 판결하는 심판자입니다. ... ≤500 tokens"
}
```

Required fields:
- Always: `conflict_present: bool`
- When `conflict_present=true`: all three of `persona_antipattern`, `persona_signature`, `judge_system_prompt` required (non-null).
- When `conflict_present=false`:
  - At most one of `persona_antipattern` / `persona_signature` is non-null.
  - `judge_system_prompt` is null or omitted.

Each persona block:
- `name`: ≤12 chars (ko/jp) or ≤25 chars (en). Archetype label in 1st person.
- `oneliner`: ≤25 words, 1st person ("나는 ...", "I am ...", "私は...").
- `system_prompt`: ≤1000 tokens, 1st person character prompt. No synthesis language ("하지만", "however"). Pure extremism of that one axis.

Two personas are **never merged**. They are two separate voices throughout.

### 4.3 Python: `render_personas`

Signature:
```python
def render_personas(
    synthesis_path: Union[Path, str],
    persona_path: Union[Path, str],
    locale: str,
    out_dir: Union[Path, str],
) -> int:
    """Render .honne/personas/{antipattern,signature,judge}.md from synthesis.

    Exit codes:
      0: success
      2: template error (missing locale template)
      66: missing/malformed synthesis or persona.json
    """
```

Behavior:
1. Load + validate synthesis JSON:
   - `conflict_present` key present.
   - If `conflict_present=true`: `persona_antipattern`, `persona_signature`, `judge_system_prompt` present AND non-null.
   - Each present persona dict: `{"name", "oneliner", "system_prompt"}` all present.
   - Any violation → exit 66 with specific error.
2. Load persona.json; not-exists → exit 66.
3. Load template `skills/persona/templates/persona_render.<locale>.md`; missing → exit 2.
4. `out_dir.mkdir(parents=True, exist_ok=True)`.
5. For each non-null persona block:
   - Render template with `{name}`, `{oneliner}`, `{system_prompt}` placeholders.
   - Write to `out_dir/antipattern.md` or `out_dir/signature.md`.
6. If `judge_system_prompt` is non-null:
   - Write the string **as-is** (no template wrap) to `out_dir/judge.md`.
7. Return 0.

### 4.4 Render Template (`persona_render.{locale}.md`)

Single body per locale — no sections, just a template string:

```markdown
# {name}

> {oneliner}

---

{system_prompt}
```

No locale-specific prose in the template body. (Identical across ko/en/jp.) The reason we still keep 3 files is to preserve the locale-directory convention and allow future locale-specific polish.

### 4.5 CLI Changes (cli.py)

Remove:
```python
persona_prompt_p = render_sub.add_parser("persona-prompt")
# ... all related args and dispatch
```

Add:
```python
personas_p = render_sub.add_parser("personas")
personas_p.add_argument("--synthesis", required=True)
personas_p.add_argument("--persona", required=True)
personas_p.add_argument("--locale", required=True, choices=["ko", "en", "jp"])
personas_p.add_argument("--out-dir", required=True)
```

Also add a top-level `persona` subcommand for existence checks (replaces `--check-only`):
```python
persona_parser = subparsers.add_parser("persona", help="persona utilities")
persona_sub = persona_parser.add_subparsers(dest="subcommand")
persona_check = persona_sub.add_parser("check")
persona_check.add_argument("--persona", required=True)
```

Dispatch:
```python
elif args.command == "persona" and args.subcommand == "check":
    from pathlib import Path
    return 0 if Path(args.persona).exists() else 66

elif args.command == "render" and args.subcommand == "personas":
    from .persona_prompt import render_personas
    return render_personas(
        synthesis_path=args.synthesis,
        persona_path=args.persona,
        locale=args.locale,
        out_dir=args.out_dir,
    )
```

### 4.6 `/honne:persona` Step 4 + Step 5 Rewrite

Step 4 (b) expected JSON block changes to match §4.2 schema. Drop all `verdict` / `character_oneliner` / `debate` / `conflict_present=true with debate` language.

Step 4 (c) unchanged — write synthesis to `.honne/cache/persona-synthesis.json` via absolute-path-resolved Write.

Step 5 replaces entirely:

```bash
HONNE_BIN=$(python3 -c "import os; print(os.path.join(os.environ.get('CLAUDE_PLUGIN_ROOT',''), 'scripts/honne'))")
bash "$HONNE_BIN" render personas \
  --synthesis .honne/cache/persona-synthesis.json \
  --persona .honne/persona.json \
  --locale "$LOCALE" \
  --out-dir .honne/personas
```

Note: `${CLAUDE_PLUGIN_ROOT}` must be resolved at runtime via `python3 os.environ` before use in bash; bare shell variable expansion is unreliable in SKILL bash blocks (established in setup-skill hardening).

Non-zero exit → output raw synthesis + warning.

Then tell the user (locale-translated per SKILL locale):

**ko:**
> 두 인격이 생성되었습니다:
> - `.honne/personas/antipattern.md` — {persona_antipattern.name}
> - `.honne/personas/signature.md` — {persona_signature.name}
> - `.honne/personas/judge.md` — 심판자
>
> 두 인격을 붙이려면 `/honne:crush <주제>`를 실행하세요.

**en:**
> Two personas generated:
> - `.honne/personas/antipattern.md` — {persona_antipattern.name}
> - `.honne/personas/signature.md` — {persona_signature.name}
> - `.honne/personas/judge.md` — judge
>
> Run `/honne:crush <topic>` to stage a live debate.

**jp:**
> ふたつのペルソナが生成されました:
> - `.honne/personas/antipattern.md` — {persona_antipattern.name}
> - `.honne/personas/signature.md` — {persona_signature.name}
> - `.honne/personas/judge.md` — 審判者
>
> ライブ討論を行うには `/honne:crush <テーマ>` を実行してください。

**Do not output an activation directive. Do not claim the persona is active. This skill is generate-only.**

Step 2 check command changes from `render persona-prompt --check-only` to `persona check`:
```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" persona check --persona .honne/persona.json
```

### 4.7 `/honne:crush` Skill

Full 6-step flow. Accepts skill arguments as topic text.

Frontmatter:
```yaml
---
name: crush
version: 0.0.2
description: >
  Stage a live debate between your persona's antipattern and signature voices on a topic.
  Triggers: "crush", "debate personas", "personas fight", "/honne:crush".
---
```

Step 1 — Topic:
- If skill arguments are non-empty → `TOPIC = args joined with spaces`.
- Else: ask plain-text question "토론 주제는? (예: '이 PR 머지해야 할까?')". Reply becomes TOPIC.

Step 2 — Validate personas:
- Existence check for all three files under `.honne/personas/`.
- Any missing → tell user "먼저 `/honne:persona`를 실행해 인격을 생성하세요." Stop.

Step 3 — Round 1 (antipattern):
- Read `.honne/personas/antipattern.md`.
- Apply it as the current system prompt mentally.
- Produce a 2–3 sentence attack on TOPIC.
- Label output `**[antipattern — {name}]**` where `{name}` is parsed from the `# ` header of the file.

Step 4 — Round 1 (signature):
- Read `.honne/personas/signature.md`. Apply. Rebut antipattern's attack in 2–3 sentences.
- Label `**[signature — {name}]**`.

Step 5 — Round 2:
- Back to antipattern.md: counter-rebuttal 2–3 sentences.
- Back to signature.md: closing argument 2–3 sentences.

Step 6 — Judge:
- Read `.honne/personas/judge.md`. Apply. Deliver 2–3 sentence verdict.
- Label `**[판결]**` (ko) / `**[Verdict]**` (en) / `**[判決]**` (jp).

Output format:
```markdown
**주제**: {TOPIC}

**[antipattern — {name}]**
{round 1 attack}

**[signature — {name}]**
{round 1 rebuttal}

**[antipattern — {name}]**
{round 2 counter}

**[signature — {name}]**
{round 2 closing}

**[판결]**
{verdict}
```

No file writes. Transcript is ephemeral.

### 4.8 Test Fixtures

`synthesis_full.json` (both personas + judge):
```json
{
  "conflict_present": true,
  "persona_antipattern": {
    "name": "과잉명세형",
    "oneliner": "나는 overspec 255회의 장본인이다",
    "system_prompt": "당신은 과잉명세형 인물입니다. 모든 문제는 사양의 완전성으로 해결된다고 믿습니다."
  },
  "persona_signature": {
    "name": "정밀타격형",
    "oneliner": "나는 targeted_request 573회의 정확도다",
    "system_prompt": "당신은 정밀타격형 인물입니다. 첫 화살로 명중시키지 못하면 무의미하다고 믿습니다."
  },
  "judge_system_prompt": "당신은 두 인격의 주장을 듣고 판결하는 심판자입니다."
}
```

`synthesis_no_antipattern.json`:
```json
{
  "conflict_present": false,
  "persona_antipattern": null,
  "persona_signature": {
    "name": "정밀타격형",
    "oneliner": "나는 targeted_request 573회의 정확도다",
    "system_prompt": "당신은 정밀타격형 인물입니다."
  },
  "judge_system_prompt": null
}
```

`synthesis_no_axes.json`:
```json
{
  "conflict_present": false,
  "persona_antipattern": null,
  "persona_signature": null,
  "judge_system_prompt": null
}
```

---

## §5 Success Criteria

| Criterion | Condition |
|-----------|-----------|
| Two persona files generated | `/honne:persona` writes `antipattern.md` + `signature.md` (+ `judge.md` when `conflict_present=true`) under `.honne/personas/` |
| Single-axis portrait | When only one axis is present, exactly 1 file written; `judge.md` absent |
| No activation claim | `/honne:persona` output does not contain "활성화", "active", "embody", "from now on" in any locale |
| Live debate reachable | `/honne:crush <topic>` produces a 5-turn labeled transcript ending with judge verdict |
| Crush is file-write-free | No files created or modified during `/honne:crush` execution |
| Unit tests green | `pytest tests/ -q` exits 0 with no skips |

---

## §6 Test Criteria

### Run
```bash
python3 -m pytest tests/ -q
```
Target: all tests pass after rewrite. No skips introduced.

### Unit (new / rewritten)

| Test | Expected |
|------|----------|
| `TestBuildConflictPayload` (existing) | unchanged — all pass |
| `TestRenderPersonas::test_render_both_personas` | fixture `synthesis_full.json` → 3 files written to out_dir |
| `TestRenderPersonas::test_render_antipattern_only` | `synthesis_no_antipattern.json` with swap → only `signature.md` |
| `TestRenderPersonas::test_render_signature_only` | mirror case |
| `TestRenderPersonas::test_render_both_null` | `synthesis_no_axes.json` → 0 files, exit 0 (nothing to render but not an error) |
| `TestRenderPersonas::test_missing_conflict_present_key` | exit 66 |
| `TestRenderPersonas::test_conflict_true_missing_persona_block` | `conflict_present=true` but `persona_antipattern=null` → exit 66 |
| `TestRenderPersonas::test_persona_block_missing_name` | missing `name` subfield → exit 66 |
| `TestCrushSkillExists` | 3 locale files, `name=crush`, `version=0.0.2` |
| `TestCrushStepStructure` | Steps 1–6 present in each locale |
| `TestCrushReadsPersonas` | bash blocks reference `.honne/personas/{antipattern,signature,judge}.md` |
| `TestCrushNoFileWrites` | no Write tool invocations or `>` redirects in crush SKILL bash blocks |

### E2E (manual, docs/e2e-persona.md)

- `/honne:persona` → `.honne/personas/` has 3 files (or 2 or 1 depending on conflict_present)
- `/honne:persona` output does NOT contain "활성화" or "activation"
- `/honne:crush "이 PR 머지해야 할까?"` produces a 5-turn transcript + verdict, all labeled correctly
- `/honne:crush` without argument prompts for topic via plain text, then proceeds
- `/honne:crush` with missing personas → clean "run /honne:persona first" message, no stack trace

---

## §7 Guardrails

> **HARD** = blocking; implementation must not ship if violated. **SOFT** = advisory; violating risks quality but does not block.

1. **[HARD] Two personas must never merge in the synthesis output.** Any `system_prompt` that contains both axes' claims (e.g. "you are X but also Y") is a violation. Synthesis templates explicitly forbid this.

2. **[HARD] `/honne:persona` has zero activation language.** No "active", "embody", "from now on respond as". Enforcement: grep in `unit_persona_skill_test.py` for those strings in persona SKILL.md bodies, must return 0 matches.

3. **[HARD] `/honne:crush` writes to no file.** Transcript is ephemeral. Enforced by test (no Write, no `> path` redirect in crush SKILL bash blocks).

4. **[HARD] `name` header is load-bearing.** `/honne:crush` parses `# {name}` from persona files for its transcript labels. Render template must always emit `# {name}` as the first content line.

5. **[SOFT] Two personas are loaded at crush time only.** Never embedded inline in crush SKILL.md. This keeps personas portable and lets users edit `.honne/personas/*.md` between runs.

6. **[SOFT] Judge prompt is neutral.** The synthesis template must not bias the judge toward either axis. Judge is "두 입장을 듣고 현 상황에서 누가 옳은지 판결" — no prefabricated conclusion.

7. **[SOFT] CLI renaming is hard-break.** `render persona-prompt` removed, `render personas` added. Acceptable because 0.0.2 is unreleased. If this PRD is implemented after 0.0.2 ships, this guardrail inverts — keep both commands + deprecation path.
