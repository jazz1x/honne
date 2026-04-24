---
name: setup
version: 0.0.2
description: >
  One-time allowedTools registration for honne permissions.
  Triggers: "setup honne", "configure permissions", "allowedTools", "/honne:setup".
---

# honne — Permission Setup

**When invoked, execute Step 1 and Step 2 in order immediately. Do not summarize or ask for clarification — invocation itself is the request.**

## Step 1: Resolve Plugin Root and Output allowedTools Fragment

Run this bash block to resolve the actual plugin install path and emit the fragment:

```bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT}"
cat <<EOF
Add the following entries to your ~/.claude/settings.json under "allowedTools":

  "Bash(bash ${PLUGIN_ROOT}/scripts/honne *)",
  "Bash(bash \"${PLUGIN_ROOT}/scripts/honne\" *)",
  "Bash(python3 -c *)",
  "Bash(python3 ${PLUGIN_ROOT}/*)",
  "Write(.honne/**)"

If allowedTools does not exist yet, create it as a top-level array.
Run /honne:setup again after adding to verify.
EOF
```

Note to the user:
- The two `Bash(bash ...)` entries cover both unquoted and quoted invocations of the honne script (SKILL.md uses the quoted form).
- `Write(.honne/**)` suppresses file-write prompts for cache/assets outputs (including `>` redirections).

## Step 2: Check Current Configuration

Run the following command to inspect the current settings:

```bash
python3 -c "
import json, os
p = os.path.expanduser('~/.claude/settings.json')
if not os.path.exists(p):
    print('settings.json not found')
    exit(1)
d = json.load(open(p))
tools = d.get('allowedTools', [])
honne = [t for t in tools if 'honne' in t or '.honne' in t]
print(f'honne entries: {len(honne)}')
for t in honne:
    print(' ', t)
"
```

Interpret the result:
- **0 entries**: "Not yet configured. Paste the fragment above into allowedTools."
- **≥1 entries**: "Configured. {N} honne entries registered."

**NOTE**: This skill outputs configuration instructions only — it does NOT write to `~/.claude/settings.json`. You control all mutations.
