---
name: compare
version: 0.0.3
description: >
  자산 전용 회고. 트랜스크립트 재스캔, LLM 재분석, HITL 없음.
  Triggers: "compare", "review past", "what changed", "self retrospective".
---

# compare — 읽기 전용 회고

## 1단계: 범위 HITL (일회성)

물어봅니다: "회고 범위 — `repo` 또는 `global`?"

## 2단계: 자산 존재 확인

.honne/assets/ 부재 또는 비어있으면:
  "No assets yet. Run honne first." 출력 및 exit 0.

## 3단계: 주장 + 진화 로드

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/query-assets.sh" \
  --tag "<axis>" --scope "$SCOPE" --type claim --out stdout
```

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/query-assets.sh" \
  --type evolution --scope "$SCOPE" --out stdout
```

**비동기 대기 패턴** — Monitor until-loop 사용, `sleep N && cat` 금지:
```bash
# ✓ Monitor: until [ -f ".honne/assets/claim.jsonl" ]
```

## 4단계: 시간 버킷 그룹화

축 × recorded_at 버킷으로 그룹화 (MVP의 경우 YYYY-MM 세분성).

## 5단계: docs/honne-compare.md 렌더링 (+ stdout)

architecture PRD §4.2 compare Step 6에 따라 형식화합니다.
사용자가 "요약"을 요청하지 않는 한 LLM 없음 — 심지어 그때도 인용 제한만.

## 6단계: 쓰기 없음

이 스킬은 .honne/assets/ 또는 .honne/persona.json에 절대 쓸 수 없습니다.
검증 (테스트): assets/*.jsonl의 stat -c %Y before/after 변경되지 않음.
