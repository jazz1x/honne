---
name: persona
version: 0.0.3
description: >
  antipattern × signature 축의 갈등 합성.
  관찰된 패턴으로부터 작동하는 페르소나 프롬프트를 생성합니다.
  Triggers: "persona", "activate persona", "who am I as Claude", "honne persona".
---

# honne — 페르소나 합성

**호출 시 1단계부터 5단계까지 순서대로 즉시 실행합니다. 스킬을 설명하거나 사용자가 원하는 것을 묻지 마십시오 — 호출 자체가 요청입니다. 1단계 질문으로 시작하십시오.**

## 1단계: 언어 HITL

`AskUserQuestion` 도구를 호출합니다:

- `question`: "언어?"
- `options`: `[{"label":"ko","description":"한국어"},{"label":"en","description":"English"},{"label":"jp","description":"日本語"}]`

답변에서 `LOCALE`을 설정합니다. 일반 텍스트 Q&A를 사용하지 마십시오 — 화살표 키 선택만.

## 2단계: 로드 및 유효성 검증

persona.json 존재 여부를 확인합니다:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" persona check --persona .honne/persona.json
```

- Exit 66 → 사용자에게 알림: "`.honne/persona.json`이 없습니다. 먼저 `/honne:whoami`를 실행하여 페르소나를 생성하세요." 중지.
- Exit 0 → 계속.

신선도 확인:

```bash
python3 -c "import json,datetime; d=json.load(open('.honne/persona.json')); ts=datetime.datetime.fromisoformat(d.get('generated_at','2000-01-01T00:00:00Z').replace('Z','+00:00')); print((datetime.datetime.now(datetime.timezone.utc)-ts).days)"
```
stdout을 `STALE_DAYS`로 캡처.

`STALE_DAYS`가 7을 초과하면 (`HONNE_PERSONA_STALE_DAYS` 환경변수로 재정의 가능): "persona.json이 {STALE_DAYS}일 전에 마지막으로 업데이트되었습니다. `/honne:whoami` 재실행을 고려하세요."라고 경고합니다. 그 후 계속.

## 3단계: 갈등 페이로드 구성

`.honne/persona.json`을 정신적 컨텍스트에서 읽습니다. CONFLICT_PAYLOAD를 파일 쓰기나 heredoc 없이 JSON 오브젝트로 구성합니다:

```
CONFLICT_PAYLOAD = {
  "locale": "<LOCALE>",
  "antipattern": {
    "claim": "<axes.antipattern.claim>",
    "explanation": "<axes.antipattern.explanation>",
    "evidence_strength": <axes.antipattern.evidence_strength>
  }  — antipattern 축이 없거나 claim이 null이면 null,
  "signature": {
    "claim": "<axes.signature.claim>",
    "explanation": "<axes.signature.explanation>",
    "evidence_strength": <axes.signature.evidence_strength>
  }  — signature 축이 없거나 claim이 null이면 null,
  "supporting_axes": {
    "<axis>": {"claim": "...", "explanation": "...", "evidence_strength": <val>}
    나머지 5개 축 각각: lexicon, reaction, workflow, obsession, ritual
  }
}
```

`python3 << 'EOF'` 또는 heredoc을 사용하지 마십시오. 방금 읽은 persona.json 데이터에서 정신적 컨텍스트로 페이로드를 조립합니다.

## 4단계: LLM 합성

(a) 합성 프롬프트 읽기:

`Read "${CLAUDE_PLUGIN_ROOT}/skills/persona/templates/persona_synthesis_prompt.${LOCALE}.md"`

(b) 합성 프롬프트 시스템 지침을 자신에게 적용하고, CONFLICT_PAYLOAD를 사용자 입력으로 사용합니다. STRICT JSON 응답을 생성합니다:

```json
{
  "conflict_present": true,
  "persona_antipattern": {
    "name": "...",
    "oneliner": "...",
    "system_prompt": "..."
  },
  "persona_signature": {
    "name": "...",
    "oneliner": "...",
    "system_prompt": "..."
  },
  "judge_system_prompt": "..."
}
```

분기 규칙 (합성 프롬프트 템플릿에서 적용):
- `conflict_present = true`: 양쪽 축 모두 존재 → 두 개의 분리된 페르소나 (antipattern과 signature) + 심판자를 생성. 세 필드 모두 **필수**.
- `conflict_present = false`, 한쪽 null: 없는 페르소나를 null로 설정. `judge_system_prompt`는 null.
- `conflict_present = false`, 양쪽 모두 null: 모든 페르소나 필드는 null.

제약: 각 `system_prompt` ≤ 1000 tokens. `judge_system_prompt` ≤ 500 tokens. `name` ≤ 12자. `oneliner` ≤ 25단어.

(c) 결과 저장: JSON을 `{PWD}/.honne/cache/persona-synthesis.json`에 `Write` 도구로 저장합니다. JSON 파싱 실패 또는 빈 응답이면 저장 건너뛰고 원시 텍스트와 경고를 출력합니다.

## 5단계: 페르소나 렌더링

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" render personas --persona .honne/persona.json --synthesis .honne/cache/persona-synthesis.json --locale "$LOCALE" --out-dir .honne/personas
```

0이 아닌 exit → 원시 합성 필드를 출력하고 파일 렌더링 실패 경고를 표시합니다.

사용자에게 출력 — 4단계(c)에서 저장한 합성 JSON 상태에 따라 케이스를 선택합니다.

**케이스 A — `conflict_present=true`** (두 인격 + 심판자):

> 두 인격이 생성되었습니다:
> - `.honne/personas/antipattern.md` — {persona_antipattern.name}
> - `.honne/personas/signature.md` — {persona_signature.name}
> - `.honne/personas/judge.md` — 심판자
>
> 두 인격을 붙이려면 `/honne:crush <주제>`를 실행하세요.

**케이스 B — `conflict_present=false`, 한쪽 인격만 non-null**:

> 하나의 인격만 생성되었습니다 (반대 축이 감지되지 않음):
> - `.honne/personas/{slot}.md` — {persona.name}
>
> `/honne:crush` 토론은 두 축이 모두 필요합니다. 더 많은 세션을 수집한 뒤 `/honne:whoami`를 재실행하세요.

`{slot}`은 non-null 인격에 따라 `antipattern` 또는 `signature`.

**케이스 C — `conflict_present=false`, 양쪽 모두 null**:

> 인격이 생성되지 않았습니다 (두 축 모두 감지되지 않음). 세션을 더 수집한 뒤 `/honne:whoami`를 재실행하세요.

**중요**: 이 스킬은 파일만 생성합니다. 페르소나가 실행 중·적용 중·사용 중이라고 주장하지 마십시오. 페르소나는 독립적인 산물입니다 — 사용자가 실시간 토론을 원할 때 `/honne:crush`를 호출합니다.
