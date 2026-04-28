---
name: whoami
version: 0.0.3
description: >
  로컬 LLM 트랜스크립트에서 7축 자기관찰을 오케스트레이션합니다.
  자율 증거 수집 + LLM 합성 해설.
  Triggers: "who am I", "self profile", "profile me", "honne", "whoami self".
---

# honne — 7축 자기관찰

**호출 시 1단계부터 6단계까지 순서대로 즉시 실행합니다. 스킬을 설명하거나 사용자가 원하는 것을 묻지 않으십시오 — 호출 자체가 요청입니다. 1단계 질문으로 시작하십시오.**

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

**거절 기록**: 사용자가 후보 주장을 명시적으로 "n"으로 거절하면, 향후 3단계 필터에서 사용할 수 있도록 거절로 기록합니다:
```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" record claim \
  --type rejection --axis "$axis" --scope "$SCOPE" \
  --claim "$CANDIDATE" --run-id "$RUN_ID" \
  --out ".honne/assets/rejections.jsonl"
```

<!-- TODO(evolutions): evolutions.jsonl 교차 실행 diff 추적이 아직 구현되지 않았습니다. query --type evolution은 항상 []를 반환합니다. 구조적 변경이 필요합니다. -->

## 4단계: 축별 자율 기록

`axis list`의 각 축에 대해, 각 명령을 별도로 실행하세요 — 스크립트 파일로 번들링하거나 heredoc을 사용하지 마세요:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" axis run "$axis" \
  --locale "$LOCALE" --scan .honne/cache/scan.json > ".honne/cache/axis-${axis}.json"
```

```bash
python3 -c "import json,sys; d=json.load(open('.honne/cache/axis-${axis}.json')); sys.exit(0 if d.get('insufficient_evidence') else 1)"
```
exit 0이면 → 이 축을 건너뛰기 (근거 부족), 다음으로 진행.

```bash
python3 -c "import json; print(json.load(open('.honne/cache/axis-${axis}.json'))['candidate_claim'])"
```
stdout을 `CANDIDATE`로 캡처.

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" record claim \
  --type claim --axis "$axis" --scope "$SCOPE" \
  --claim "$CANDIDATE" --run-id "$RUN_ID" \
  --quotes-file ".honne/cache/axis-${axis}.json" \
  --out ".honne/assets/claims.jsonl"
```

**강제 규칙**: `/tmp`에 중간 데이터를 쓰지 마세요. `/tmp`에 쓰고 싶은 충동이 느껴지면 대신 `.honne/cache/`를 사용하세요. `/tmp`에 쓰는 것은 SKILL.md 계약 위반입니다 — 테스트 스위트가 이를 감지합니다.

**중요**: 각 `bash` 블록을 직접 셸 명령으로 실행하세요. `/tmp`에 쓰지 마세요, 셸 heredoc(`<< 'EOF'`)을 사용하지 마세요, 명령을 스크립트 파일로 번들링하지 마세요. 인라인 명령만 실행하세요.

## 5단계: LLM 해설 합성

Claude (당신의 정신 추론)를 호출하여 해설과 한줄평을 합성합니다:

(a) 합성 프롬프트 읽기: `Read "${CLAUDE_PLUGIN_ROOT}/skills/whoami/templates/synthesis_prompt.${LOCALE}.md"`

(b) 4단계에서 기록한 주장으로 USER_PAYLOAD를 구성합니다. 메모리에 있는 AXIS_JSON 출력을 사용하여 파일을 다시 읽지 않고 직접 JSON 객체로 구성하세요:

```
USER_PAYLOAD = {
  "locale": "<LOCALE>",
  "claims": {
    "<axis>": {"claim": "<CANDIDATE>", "evidence_count": <len(quotes)>} for each recorded axis,
    "<skipped_axis>": null for each axis that had insufficient evidence
  }
}
```

`python3 << 'PYEOF'`나 heredoc을 사용하지 마세요. 4단계에서 이미 알고 있는 출력으로 정신 맥락에서 조립하세요.

(c) 합성: 합성 프롬프트 시스템 지침을 자신에게 적용 + USER_PAYLOAD를 사용자 입력으로. STRICT JSON 응답 생성.

(d) 절대 경로를 먼저 확인하세요:
```bash
python3 -c "import os; print(os.path.join(os.getcwd(), '.honne/cache/narrative.json'))"
```
stdout을 `NARRATIVE_PATH`로 캡처. 그런 다음: JSON 응답을 확인된 경로에 `Write` 도구로 저장하세요. JSON 파싱 실패 또는 빈 응답이면 저장 스킵.

## 6단계: 페르소나 및 보고서 렌더링

```bash
date -u +%Y-%m-%dT%H:%M:%SZ
```
stdout을 `NOW`로 캡처.

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" render persona \
  --claims .honne/assets/claims.jsonl \
  --scope "$SCOPE" --locale "$LOCALE" --run-id "$RUN_ID" --now "$NOW" \
  --narrative .honne/cache/narrative.json \
  --out .honne/persona.json
```

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" render report \
  --persona .honne/persona.json --locale "$LOCALE" --out docs/honne.md
```

## 완료
`.honne/persona.json` 및 `docs/honne.md`에 저장된 파일을 보고합니다. `/honne:compare`를 사용하여 과거 관찰을 검토합니다.

다음 액션 제안을 사용자에게 출력합니다:

**다음 액션**
- `/honne:persona` — 이 프로필에서 두 페르소나(antipattern × signature) 생성
- `/honne:crush <주제>` — 두 페르소나 간 라이브 토론
