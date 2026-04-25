# honne 0.0.2 — /honne:persona + /honne:crush e2e Checklist

Manual verification checklist after split-persona pivot and hardening (PRD 0.0.2).

## `/honne:persona` — Generation Flow

- [ ] `/honne:persona` completes without errors
- [ ] `persona-synthesis.json` written to `.honne/cache/` (not `~/.claude/projects/`)
- [ ] `.honne/personas/` directory created with 3 files:
  - [ ] `antipattern.md` — contains persona name in `# ` header and system prompt
  - [ ] `signature.md` — contains persona name in `# ` header and system prompt
  - [ ] `judge.md` — contains judge system prompt
- [ ] Output does NOT claim activation ("활성화", "active", "embody", "from now on" absent)
- [ ] Output explicitly directs user to `/honne:crush`

## `/honne:crush` — Debate Flow

- [ ] `/honne:crush "test topic"` runs without errors
- [ ] Transcript produced with 5 turns + verdict:
  - [ ] Turn 1: `**[antipattern — {name}]**` attack on topic (2-3 sentences)
  - [ ] Turn 2: `**[signature — {name}]**` rebuttal (2-3 sentences)
  - [ ] Turn 3: `**[antipattern — {name}]**` counter-rebuttal (2-3 sentences)
  - [ ] Turn 4: `**[signature — {name}]**` closing argument (2-3 sentences)
  - [ ] Turn 5: `**[Verdict]**` judge verdict (2-3 sentences)
- [ ] No files created or modified (transcript ephemeral)
- [ ] Works with missing personas → clean error message "run /honne:persona first"

## Hardening

- [ ] No `/tmp` writes: all files go to `.honne/cache/` or `.honne/personas/`
- [ ] No CLAUDE.md injection
- [ ] `record claim --quotes-file` accepts file-based JSON (Korean + special chars safe)
- [ ] `/honne:setup` outputs `allowedTools` snippet for settings.json

## Integration

- [ ] Both skills work in same session without conflicts
- [ ] Personas generated in one session, used by crush in another session (artifacts persist)
