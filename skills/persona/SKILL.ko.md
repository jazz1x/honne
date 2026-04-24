---
name: persona
version: 0.0.2
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
bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" render persona-prompt --check-only --persona .honne/persona.json --locale "$LOCALE"
```

- Exit 66 → 사용자에게 알림: "`.honne/persona.json`이 없습니다. 먼저 `/honne:whoami`를 실행하여 페르소나를 생성하세요." 중지.
- Exit 0 → 계속.

신선도 확인:

```bash
STALE_DAYS=$(python3 -c "import json,datetime; d=json.load(open('.honne/persona.json')); ts=datetime.datetime.fromisoformat(d.get('generated_at','2000-01-01T00:00:00Z').replace('Z','+00:00')); print((datetime.datetime.now(datetime.timezone.utc)-ts).days)")
```

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

```bash
Read "${CLAUDE_PLUGIN_ROOT}/skills/persona/templates/persona_synthesis_prompt.${LOCALE}.md"
```

(b) 합성 프롬프트 시스템 지침을 자신에게 적용하고, CONFLICT_PAYLOAD를 사용자 입력으로 사용합니다. STRICT JSON 응답을 생성합니다:

```json
{
  "verdict": "...",
  "character_oneliner": "...",
  "system_prompt": "...",
  "conflict_present": true,
  "debate": {
    "antipattern_voice": "...",
    "signature_voice": "...",
    "resolution": "..."
  }
}
```

분기 규칙 (합성 프롬프트 템플릿에서 적용):
- `conflict_present = true`: 양쪽 축 모두 존재 → antipattern vs. signature를 3자 토론 (검사 / 변호 / 판결)으로 무대화. `debate` 필드 **필수**.
- `conflict_present = false`, 한쪽 null: 지배적 특성 포트레이트, 없는 쪽을 "아직 관찰되지 않음"으로 표시. `debate`는 null 또는 생략.
- `conflict_present = false`, 양쪽 모두 null: 지원 5개 축만으로 포트레이트. `debate`는 null 또는 생략.

제약: `system_prompt` ≤ 1500 tokens. `character_oneliner` ≤ 20단어. 각 `debate` voice는 2~3문장, 평서문만.

(c) 결과 저장: JSON을 `{PWD}/.honne/cache/persona-synthesis.json`에 `Write` 도구로 저장합니다. JSON 파싱 실패 또는 빈 응답이면 저장 건너뛰고 원시 텍스트와 경고를 출력합니다.

## 5단계: 렌더링 및 활성화

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" render persona-prompt --persona .honne/persona.json --synthesis .honne/cache/persona-synthesis.json --locale "$LOCALE" --out .honne/persona-prompt.md
```

0이 아닌 exit → 원시 합성 필드를 출력하고 파일 렌더링 실패 경고를 표시합니다.

사용자에게 출력합니다:

**캐릭터**: `character_oneliner`

**판정**: `verdict`

**내면의 충돌** (`conflict_present = true`일 때만):
- **antipattern 측**: `debate.antipattern_voice`
- **signature 측**: `debate.signature_voice`
- **판결**: `debate.resolution`

**페르소나 시스템 프롬프트**:

```
[system_prompt]
```

사용자에게 알립니다: "이 페르소나는 현재 세션에서 활성화되어 있습니다. 시스템 프롬프트 + 활성화 지시는 `.honne/persona-prompt.md`에 저장되었습니다 — 향후 세션이나 다른 LLM에서 이 페르소나를 복원하려면 붙여넣기 하세요."

그 후 출력의 마지막 줄로, 활성화 지시를 자기 자신에게 적용하여 다음을 선언합니다:

> **이 메시지부터 "페르소나 해제" 또는 "reset persona"라고 말씀하시기 전까지, 저는 위 인물로 응답합니다.**

**중요**: CLAUDE.md에 쓰지 마십시오. 페르소나 활성화는 세션 내에서만 — (1) `.honne/persona-prompt.md`에 렌더링된 activation_directive 섹션 (컨텍스트에 노출) + (2) 위의 최종 자기 선언으로 달성됩니다. 이 스킬이 끝난 후, 같은 세션의 이후 턴은 페르소나를 체현해야 합니다.
