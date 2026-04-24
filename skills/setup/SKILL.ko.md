---
name: setup
version: 0.0.2
description: >
  honne 권한을 위한 일회성 allowedTools 등록.
  Triggers: "setup honne", "configure permissions", "allowedTools", "/honne:setup".
---

# honne — 권한 설정

**호출되면 1단계와 2단계를 순서대로 즉시 실행하세요. 설명하거나 명확화를 요청하지 마세요 — 호출 자체가 요청입니다.**

## 1단계: 플러그인 경로 확인 후 allowedTools 조각 출력

실제 플러그인 설치 경로를 확인하고 조각을 출력하려면 다음 bash 블록을 실행하세요:

```bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT}"
cat <<EOF
다음 항목을 ~/.claude/settings.json의 "allowedTools" 배열에 추가하세요:

  "Bash(bash ${PLUGIN_ROOT}/scripts/honne *)",
  "Bash(bash \"${PLUGIN_ROOT}/scripts/honne\" *)",
  "Bash(python3 -c *)",
  "Bash(python3 ${PLUGIN_ROOT}/*)",
  "Write(.honne/**)"

allowedTools가 아직 없으면 최상위 배열로 생성하세요.
추가 후 다시 /honne:setup을 실행하여 확인하세요.
EOF
```

사용자에게 안내 사항:
- `Bash(bash ...)` 두 항목은 honne 스크립트의 인용부호 있는 호출과 없는 호출을 모두 커버합니다 (SKILL.md는 인용부호 버전 사용).
- `Write(.honne/**)`은 cache/assets 출력 시 파일 쓰기 프롬프트(리디렉션 `>` 포함)를 억제합니다.

## 2단계: 현재 구성 확인

다음 명령을 실행하여 현재 설정을 검사합니다:

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

결과 해석:
- **0개 항목**: "아직 설정되지 않았습니다. 위의 조각을 allowedTools에 붙여넣으세요."
- **≥1개 항목**: "설정됨. {N}개의 honne 항목이 등록되었습니다."

**참고**: 이 스킬은 구성 지침만 출력합니다 — `~/.claude/settings.json`에 쓰지 않습니다. 모든 변경은 당신이 제어합니다.
