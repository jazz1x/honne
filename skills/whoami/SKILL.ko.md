---
name: whoami
version: 0.0.1
description: >
  로컬 LLM 트랜스크립트에서 6축 자기관찰을 오케스트레이션합니다.
  자율 증거 수집 + LLM 합성 해설.
  Triggers: "who am I", "self profile", "profile me", "honne", "whoami self".
---

# honne — 6축 자기관찰

**호출 시 1단계부터 7단계까지 순서대로 즉시 실행합니다. 스킬을 설명하거나 사용자가 원하는 것을 묻지 않으십시오 — 호출 자체가 요청입니다. 1단계 질문으로 시작하십시오.**

## 1단계: 범위 + 언어 HITL

`AskUserQuestion` 도구를 호출하여 한 번의 호출에 두 개의 질문을 포함합니다:

(a) 범위:
- `question`: "스캔 범위?"
- `options`: `[{"label":"repo","description":"현재 프로젝트만"},{"label":"global","description":"모든 프로젝트"}]`

(b) 언어:
- `question`: "언어?"
- `options`: `[{"label":"ko","description":"한국어"},{"label":"en","description":"English"},{"label":"jp","description":"日本語"}]`

두 답변에서 `SCOPE`와 `LOCALE`을 설정합니다. 일반 텍스트 Q&A를 사용하지 마십시오 — 화살표 키 선택만.

## 2단계: 스캔
실행: `bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" scan --scope "$SCOPE" --cache ".honne/cache/scan.json"`
결과에서 `RUN_ID` 캡처: `RUN_ID=$(python3 -c 'import json; print(json.load(open(".honne/cache/scan.json"))["run_id"])')`
0이 아닌 exit → stdout+stderr를 사용자에게 그대로 출력, 중지. Exit 코드를 해석하지 마십시오.

## 3단계: 거절 재구성 필터 (후보 건너뛰기)
각 축에 대해 `bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" query --base-dir ".honne" --tag "<axis>" --type rejection --scope "$SCOPE"`를 실행합니다.
4단계에서 각 축을 기록하기 전에 후보를 `bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" axis validate --text "$candidate" --locale "$LOCALE" --skip-if-overlaps "$rejection_text"`로 파이프합니다 — exit 3 = 겹침, 건너뛰고 "재구성됨"을 로그합니다. 모든 변수는 큰따옴표 인용 필수(공백·특수문자 안전). LLM 호출 없음.

## 4단계: 축별 자율 기록

`axis list`의 각 축에 대해:

```bash
AXIS_JSON=$(bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" axis run "$axis" \
  --locale "$LOCALE" --scan .honne/cache/scan.json)

# 근거 부족이면 건너뛰기
if echo "$AXIS_JSON" | python3 -c "import sys,json; sys.exit(0 if json.load(sys.stdin).get('insufficient_evidence') else 1)"; then
  continue
fi

# 후보 및 근거 추출
CANDIDATE=$(echo "$AXIS_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['candidate_claim'])")
QUOTES_JSON=$(echo "$AXIS_JSON" | python3 -c "import sys,json; print(json.dumps(json.load(sys.stdin)['quotes']))")

# 주장 기록
bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" record claim \
  --type claim --axis "$axis" --scope "$SCOPE" \
  --claim "$CANDIDATE" --run-id "$RUN_ID" \
  --quotes-json "$QUOTES_JSON" \
  --out ".honne/assets/claims.jsonl"
done
```

## 5단계: LLM 해설 합성

Claude (당신의 정신 추론)를 호출하여 해설과 한줄평을 합성합니다:

(a) 합성 프롬프트 읽기: `Read "${CLAUDE_PLUGIN_ROOT}/skills/whoami/templates/synthesis_prompt.${LOCALE}.md"`

(b) 일치하는 주장 추출:
```bash
USER_PAYLOAD=$(python3 -c "
import json
claims = [json.loads(l) for l in open('.honne/assets/claims.jsonl') if l.strip()]
matched = [c for c in claims if c.get('run_id')=='${RUN_ID}' and c.get('scope')=='${SCOPE}']
AXES = ['lexicon','reaction','workflow','obsession','ritual','antipattern']
payload = {'locale':'${LOCALE}','claims':{}}
for ax in AXES:
    found = [c for c in matched if c.get('axis')==ax]
    payload['claims'][ax] = {'claim': found[0]['claim'], 'evidence_count': len(found[0].get('quotes', []))} if found else None
print(json.dumps(payload, ensure_ascii=False))
")
```

(c) 합성: 합성 프롬프트 시스템 지침을 자신에게 적용 + USER_PAYLOAD를 사용자 입력으로. STRICT JSON 응답 생성.

(d) 결과 저장: JSON 응답을 `.honne/cache/narrative.json`에 `Write` 도구로 저장. JSON 파싱 실패 또는 빈 응답이면 저장 스킵 (narrative.json 미생성).

## 6단계: 페르소나 및 보고서 렌더링

```bash
NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ)
bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" render persona \
  --claims .honne/assets/claims.jsonl \
  --scope "$SCOPE" --locale "$LOCALE" --run-id "$RUN_ID" --now "$NOW" \
  --narrative .honne/cache/narrative.json \
  --out .honne/persona.json

bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" render report \
  --persona .honne/persona.json --locale "$LOCALE" --out docs/honne.md
```

## 완료
`.honne/persona.json` 및 `docs/honne.md`에 저장된 파일을 보고합니다. `/honne:compare`를 사용하여 과거 관찰을 검토합니다.

다음 액션 제안을 사용자에게 출력합니다:

**다음 액션 제안** *(해당 스킬들이 추가될 예정입니다.)*
- 이 형태로 나의 분신(페르소나) 구현해보기
- 토큰 절약을 위한 나의 습관 탐색해보기
