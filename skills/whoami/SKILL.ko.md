---
name: whoami
version: 0.0.1
description: >
  로컬 LLM 트랜스크립트에서 6축 자기관찰을 오케스트레이션합니다.
  증거 기반 페르소나와 축별 HITL 승인.
  Triggers: "who am I", "self profile", "profile me", "honne", "whoami self".
---

# honne — 6축 자기관찰

## 1단계: 범위 HITL

사용자에게 물어봅시다: "스캔 범위 — `repo` (현재 프로젝트) 또는 `global` (모든 프로젝트)?"

`repo` 또는 `global`을 명시적으로 기다립니다. 모호한 답변 → 다시 묻습니다.

## 2단계: 트랜스크립트 스캔

실행합니다:
```bash
HONNE_ROOT="${CLAUDE_PLUGIN_ROOT}"
bash "$HONNE_ROOT/scripts/scan-transcripts.sh" \
  --scope "$SCOPE" --since "2020-01-01" \
  --cache ".honne/cache/scan.json" \
  --index-ref ".honne/cache/index.json" \
  --redact-secrets
```

exit 2 (트랜스크립트 없음) 시 → "충분한 데이터가 없습니다. 범위를 변경하시겠습니까?" 보고 → 종료합니다.

## 3단계: HITL 이전 거절 재구성 필터

각 축에 대해:
```bash
bash "$HONNE_ROOT/scripts/query-assets.sh" \
  --tag "<axis>" --type rejection --scope "$SCOPE" --out stdout
```

과거 거절을 메모리에 저장합니다 (주입하지 않음). HITL 주장 제시 전 "건너뛰기 후보" 필터로 사용합니다. 후보 주장 텍스트가 과거 거절과 크게 겹치면 재구성하거나 로그와 함께 건너뜁니다.

## 4단계: 축별 처리

[어휘, 반응, 워크플로우, 집착, 의식, 안티패턴]의 각 축에 대해:
- 통계 추출 (어휘 → extract-lexicon.sh; 집착 → detect-recurrence.sh; 기타 → 이 스킬 내 내부 로직)
- LLM 요약 (evidence-gather 출력 참조 필수)
- HITL: 인용과 함께 주장을 제시하고 (y / n / 수정)을 묻습니다. 모호함 → 다시 묻습니다.
- y → record-claim.sh --type claim ...
- n → record-claim.sh --type rejection ...
- edit → 수정된 텍스트 사용, record-claim.sh --type claim ...

## 5단계: .honne/persona.json 저장

architecture PRD §3.2 스키마. 승인된 축만.

## 6단계: docs/honne.md 렌더링

사람이 읽을 수 있는 보고서. 모든 주장에는 ≥ 1개의 인용이 있거나 [insufficient evidence]로 표시되어야 합니다.

금지된 문구 (호로스코프): "at times", "sometimes", "in certain situations", "때로는", "상황에 따라", "적절히".

## 7단계: 진화 연결 (2차+ 실행)

.honne/assets/claim.jsonl에 이 실행 전 항목이 있으면:
- query-assets.sh --tag <axis> --type claim --scope "$SCOPE" --until <this-run-ts>
- LLM 쌍 분류기: {past_claim, present_claim} → label ∈ {identical, evolved, reversed, unrelated} with confidence
- confidence < 0.7 → unrelated
- identical → 현재 주장 자산에 prior_id 설정, 새 진화 없음
- evolved / reversed → record-claim.sh --type evolution --prior-id <past> ...

## 완료

저장된 파일 보고 + 사용자에게 상기: "/honne:compare to review past."

## LLM Prompt Templates

### Pair classifier (Step 7)

When comparing past vs present claim within same axis:

```
System: You classify the relationship between two evidence-backed claims about the same user on the same axis.

Input:
  Axis: {axis}
  Past claim (recorded {past_ts}): "{past_claim}"
  Present claim (recorded {present_ts}): "{present_claim}"

Labels:
  - identical: same observation, different wording
  - evolved:   same axis, concrete content changed (vocabulary substitution OR frequency shift OR scope expansion)
  - reversed:  present observation contradicts past observation
  - unrelated: observations about different phenomena

Respond with JSON only:
  { "label": "<one-of-four>", "confidence": <0.0-1.0>, "rationale": "<one short sentence>" }

Rule: if confidence < 0.7, force label = "unrelated".
```

### Rejection overlap detector (Step 3)

When deciding whether to skip a candidate claim due to past rejection:

```
System: Decide whether the present candidate claim overlaps semantically with a past rejected claim (same user, same axis).

Input:
  Axis: {axis}
  Past rejection (recorded {past_ts}): "{past_rejection}"
  Present candidate: "{present_candidate}"

Respond with JSON only:
  { "overlap": true | false, "confidence": <0.0-1.0>, "rationale": "<one short sentence>" }

Rule: overlap=true only if confidence >= 0.7. Otherwise proceed with the present candidate as-is.
```

### Horoscope guard (Step 6)

Before writing a claim into docs/honne.md, self-check:

```
System: Does the following claim contain any horoscope-style hedge? (vague time qualifiers, vague universals, phrases like "sometimes", "at times", "generally", "in certain situations", or Korean "때로는"/"상황에 따라"/"적절히", or Japanese "時に"/"場合によって")

Input: "{claim_text}"

Respond JSON only:
  { "horoscope": true | false, "matched_phrase": "<str or empty>" }

If horoscope=true, the claim is rejected and the axis item is marked [insufficient evidence].
```
