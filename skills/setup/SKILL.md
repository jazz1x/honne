---
name: setup
version: 0.0.2
description: >
  One-time allowedTools registration for honne permissions.
  Triggers: "setup honne", "configure permissions", "allowedTools", "/honne:setup".
---

# honne — Permission Setup

**When invoked, execute Step 1 through Step 3 in order immediately. Do not summarize or ask for clarification — invocation itself is the request.**

## Step 1: Detect Current State

```bash
python3 -c "
import json, os, sys
paths = [
    os.path.expanduser('~/.claude/settings.json'),
    os.path.expanduser('~/.claude/projects/' + os.getcwd().replace('/', '-') + '/settings.json'),
]
for p in paths:
    if os.path.exists(p):
        d = json.load(open(p))
        tools = d.get('allowedTools', [])
        honne = [t for t in tools if 'honne' in t or '.honne' in t]
        print(f'{p}: {len(honne)} honne entries')
        for t in honne:
            print(f'  {t}')
    else:
        print(f'{p}: not found')
"
```

## Step 2: Generate allowedTools Fragment

```bash
python3 -c "
import json
entries = [
    'Bash(bash */scripts/honne *)',
    'Bash(bash */scripts/query-assets.sh *)',
    'Bash(python3 -c *)',
    'Bash(date -u *)',
    'Write(.honne/**)',
]
print(json.dumps(entries, indent=2))
"
```

Present the result and explain:
- `bash */scripts/honne *` — all honne CLI commands (scan, axis run, record, render, persona check). Wildcard prefix matches any plugin install path.
- `bash */scripts/query-assets.sh *` — asset queries for compare skill
- `python3 -c *` — inline checks (staleness, JSON extraction, path resolution)
- `date -u *` — UTC timestamp for render
- `Write(.honne/**)` — file writes to `.honne/` directory (cache, personas, assets)

## Step 3: Apply Configuration

Ask user: "Apply these entries to your project settings? (yes / no / show path only)"

- **yes** → Run:

```bash
python3 -c "
import json, os, sys
project_key = os.getcwd().replace('/', '-')
settings_path = os.path.expanduser(f'~/.claude/projects/{project_key}/settings.json')
os.makedirs(os.path.dirname(settings_path), exist_ok=True)
if os.path.exists(settings_path):
    settings = json.load(open(settings_path))
else:
    settings = {}
tools = settings.get('allowedTools', [])
new_entries = [
    'Bash(bash */scripts/honne *)',
    'Bash(bash */scripts/query-assets.sh *)',
    'Bash(python3 -c *)',
    'Bash(date -u *)',
    'Write(.honne/**)',
]
added = 0
for entry in new_entries:
    if entry not in tools:
        tools.append(entry)
        added += 1
settings['allowedTools'] = tools
with open(settings_path, 'w') as f:
    json.dump(settings, f, indent=2)
    f.write('\n')
print(f'Written to {settings_path}')
print(f'{added} new entries added ({len(tools)} total allowedTools)')
"
```

- **no** → Output: "Copy the entries above into your `~/.claude/settings.json` or project settings manually."
- **show path only** → Output the project settings path.

**NOTE**: Project-level settings are preferred over global settings — they scope permissions to this repository only.
