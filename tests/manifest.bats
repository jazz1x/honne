#!/usr/bin/env bats
# tests/manifest.bats — plugin/marketplace/hooks manifest schema checks.
#
# These are read-only tests of files already in the repo. No sandboxing
# needed because nothing writes to disk — we only parse JSON.

load "$BATS_TEST_DIRNAME/setup.bash"

@test "plugin.json is valid JSON" {
  run python3 -m json.tool "$REPO_ROOT/.claude-plugin/plugin.json"
  [ "$status" -eq 0 ]
}

@test "plugin.json has required fields" {
  run python3 -c "
import json
d = json.load(open('$REPO_ROOT/.claude-plugin/plugin.json'))
for k in ('name', 'version', 'description', 'skills'):
    assert k in d, f'missing: {k}'
"
  [ "$status" -eq 0 ]
}

@test "plugin.json does not carry the unsupported 'hooks' field" {
  run python3 -c "
import json
d = json.load(open('$REPO_ROOT/.claude-plugin/plugin.json'))
assert 'hooks' not in d, 'hooks field must be absent — auto-discovered from hooks/hooks.json'
"
  [ "$status" -eq 0 ]
}

@test "plugin.json version is SemVer" {
  run python3 -c "
import json, re
v = json.load(open('$REPO_ROOT/.claude-plugin/plugin.json'))['version']
assert re.fullmatch(r'\d+\.\d+\.\d+', v), f'not SemVer: {v}'
"
  [ "$status" -eq 0 ]
}

@test "marketplace.json is valid JSON" {
  run python3 -m json.tool "$REPO_ROOT/.claude-plugin/marketplace.json"
  [ "$status" -eq 0 ]
}

@test "marketplace.json plugins[].source starts with './'" {
  run python3 -c "
import json
d = json.load(open('$REPO_ROOT/.claude-plugin/marketplace.json'))
for i, p in enumerate(d['plugins']):
    s = p.get('source')
    assert isinstance(s, str) and s.startswith('./'), f'plugins[{i}].source invalid: {s!r}'
"
  [ "$status" -eq 0 ]
}

@test "hooks/hooks.json is valid JSON with 'hooks' root key" {
  run python3 -c "
import json
d = json.load(open('$REPO_ROOT/hooks/hooks.json'))
assert 'hooks' in d, 'root key hooks missing'
assert 'SessionEnd' in d['hooks'], 'SessionEnd event missing'
"
  [ "$status" -eq 0 ]
}

@test "every skill directory has a SKILL.md with valid frontmatter" {
  run python3 -c "
import os, re
root = '$REPO_ROOT/skills'
bad = []
for name in sorted(os.listdir(root)):
    path = os.path.join(root, name, 'SKILL.md')
    if not os.path.isfile(path):
        bad.append(f'{name}: missing SKILL.md'); continue
    head = open(path).read(2000)
    if not head.startswith('---\n'):
        bad.append(f'{name}: no frontmatter'); continue
    fm = head.split('---\n', 2)[1]
    for k in ('name:', 'version:', 'description:'):
        if k not in fm:
            bad.append(f'{name}: missing {k}')
    m = re.search(r'^version:\s*(\S+)', fm, re.M)
    if m and not re.fullmatch(r'\d+\.\d+\.\d+', m.group(1)):
        bad.append(f'{name}: version not SemVer ({m.group(1)})')
assert not bad, bad
"
  [ "$status" -eq 0 ]
}
