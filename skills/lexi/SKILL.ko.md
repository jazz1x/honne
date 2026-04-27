---
name: lexi
version: 0.0.3
description: >
  어휘 축 독립형 — 고빈도 어휘, 코드 스위칭 비율, 의성어 추출.
  Triggers: "my vocabulary", "lexicon", "word habits", "speech patterns".
---

# lexi — 어휘 축

독립형 어휘 추출 및 분석. 통합 `honne` CLI를 사용하여 결과를 제시하고 주장을 기록합니다.

## 프로세스

1. 범위 요청 (repo/global). `SCOPE`와 `LOCALE` 변수 설정.
2. 스캔 실행: `bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" scan --base-dir ".honne" --scope "$SCOPE"`
3. 축 추출 실행: `bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" axis run lexicon --scan .honne/cache/scan.json --locale "$LOCALE"`
4. JSON 출력 확인 — `candidate_claim`, `quotes`, `insufficient_evidence` 필드 검토
5. HITL: 샘플 인용과 함께 후보 주장을 제시하고 (y/n/edit) 요청
   - **y**: 6단계로 이동
   - **n**: 거절 기록 — `bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" record claim --base-dir ".honne" --type rejection --axis lexicon --scope "$SCOPE" --text "$candidate"`; 완료
   - **edit**: 사용자가 수정된 텍스트 제공, 해당 텍스트를 주장으로 사용
6. 주장 기록: `bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" record claim --base-dir ".honne" --type claim --axis lexicon --scope "$SCOPE" --text "$claim"`
7. 과거 거절 확인하여 재제안 방지: `bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" query --base-dir ".honne" --type rejection --tag lexicon --scope "$SCOPE"`

**진행 모니터링** — Monitor until-loop 사용 (`sleep N && cat` 금지):
```bash
# ✓ Monitor: until [ -f ".honne/cache/.axis_lexicon.json" ]
```

stdout + .honne/assets/claims.jsonl에 저장된 보고서
