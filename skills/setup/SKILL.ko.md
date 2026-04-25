---
name: setup
version: 0.0.2
description: >
  honne 권한을 위한 일회성 allowedTools 등록.
  Triggers: "setup honne", "configure permissions", "allowedTools", "/honne:setup".
---

# honne — 권한 설정

**호출되면 1단계부터 3단계까지 순서대로 즉시 실행하세요. 설명하거나 명확화를 요청하지 마세요 — 호출 자체가 요청입니다.**

## 1단계: 현재 상태 확인

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
        print(f'{p}: {len(honne)} honne 항목')
        for t in honne:
            print(f'  {t}')
    else:
        print(f'{p}: 없음')
"
```

## 2단계: allowedTools 조각 생성

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

결과를 보여주고 설명:
- `bash */scripts/honne *` — 모든 honne CLI 명령 (scan, axis run, record, render, persona check). 와일드카드 접두어로 어떤 설치 경로든 매칭.
- `bash */scripts/query-assets.sh *` — compare 스킬용 자산 쿼리
- `python3 -c *` — 인라인 체크 (staleness, JSON 추출, 경로 확인)
- `date -u *` — render용 UTC 타임스탬프
- `Write(.honne/**)` — `.honne/` 디렉토리 파일 쓰기 (cache, personas, assets)

## 3단계: 설정 적용

사용자에게 질문: "프로젝트 설정에 적용할까요? (yes / no / 경로만 표시)"

- **yes** → 실행:

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
print(f'{settings_path}에 저장됨')
print(f'{added}개 항목 추가 (총 {len(tools)}개 allowedTools)')
"
```

- **no** → 출력: "위 항목을 `~/.claude/settings.json` 또는 프로젝트 설정에 수동으로 복사하세요."
- **경로만 표시** → 프로젝트 설정 경로 출력.

**참고**: 프로젝트 수준 설정이 전역 설정보다 선호됩니다 — 이 리포지토리에만 권한을 범위 제한합니다.
