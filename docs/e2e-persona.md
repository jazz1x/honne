# honne 0.0.2 — /honne:persona e2e Smoke Checklist

Manual verification checklist after implementing hardening fixes (PRD 0.0.2).

## Test Items

- [ ] `/honne:persona` runs without /tmp writes (check `.honne/cache/` only)
- [ ] `persona-synthesis.json` written to `{CWD}/.honne/cache/` (not `~/.claude/projects/`)
- [ ] Korean persona claim in `persona.json` → `record claim --quotes-file` succeeds (no exit 1)
- [ ] `/honne:whoami` full run: `axis-{name}.json` files appear in `.honne/cache/`, no ARG_MAX crash
- [ ] Permission count: after `/honne:setup` allowedTools configured, whoami runs with ≤3 prompts
