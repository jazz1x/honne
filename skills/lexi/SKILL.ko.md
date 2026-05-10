---
name: lexi
version: 0.0.5
description: >
  어휘 축 독립형 — 고빈도 어휘, 코드 스위칭 비율, 의성어 추출.
  Triggers: "my vocabulary", "lexicon", "word habits", "speech patterns".
ssl:
  scheduling:
    anti_triggers:
      - "전체 7-axis 분석이 필요할 때 (whoami 사용)"
  structural:
    scenes:
      - "Step 1: HITL (범위 + 언어)"
      - "Step 2: 스캔"
      - "Step 3: 축 추출"
      - "Step 4: JSON 검토"
      - "Step 5: HITL 수락/거절/수정"
      - "Step 6: 주장 기록"
      - "Step 7: 과거 거절 확인"
    branches:
      - "Step 5: y → Step 6 주장 기록"
      - "Step 5: n → 거절 기록 후 종료"
      - "Step 5: edit → 사용자 수정 텍스트 → Step 6 주장 기록"
    resumable: false
  logical:
    tools: ["bash"]
    side_effects:
      reads:
        - ".honne/cache/scan.json"
      writes:
        - ".honne/assets/claims.jsonl  # append"
      deletes: []
      network: []
    idempotent: false
    rollback: ".honne/assets/claims.jsonl 의 마지막 lexicon 라인을 수동 제거."
---

# lexi — 어휘 축

독립형 어휘 추출 및 분석. 통합 `honne` CLI를 사용하여 결과를 제시하고 주장을 기록합니다.

## Step 1: HITL (범위 + 언어)

범위(repo/global)와 **언어**(ko/en/jp)를 모두 요청합니다. 응답에서 `SCOPE`와 `LOCALE` 변수를 설정합니다.

## Step 2: 스캔

`bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" scan --base-dir ".honne" --scope "$SCOPE"`

## Step 3: 축 추출

`bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" axis run lexicon --scan .honne/cache/scan.json --locale "$LOCALE"`

## Step 4: JSON 검토

JSON 출력 확인 — `candidate_claim`, `quotes`, `insufficient_evidence` 필드를 검토합니다.

## Step 5: HITL 수락/거절/수정

샘플 인용과 함께 후보 주장을 제시하고 (y/n/edit) 요청:
- **y**: Step 6으로 이동
- **n**: 거절 기록 — `bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" record claim --base-dir ".honne" --type rejection --axis lexicon --scope "$SCOPE" --text "$candidate"`; 완료
- **edit**: 사용자가 수정된 텍스트 제공, 해당 텍스트를 주장으로 사용

## Step 6: 주장 기록

`bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" record claim --base-dir ".honne" --type claim --axis lexicon --scope "$SCOPE" --text "$claim"`

## Step 7: 과거 거절 확인

재제안을 방지하기 위해: `bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" query --base-dir ".honne" --type rejection --tag lexicon --scope "$SCOPE"`

**진행 모니터링** — Monitor until-loop 사용 (`sleep N && cat` 금지):
```bash
# ✓ Monitor: until [ -f ".honne/cache/.axis_lexicon.json" ]
```

stdout + .honne/assets/claims.jsonl에 저장된 보고서
