---
name: lexi
version: 0.0.1
description: >
  어휘 축 독립형 — 고빈도 어휘, 코드 스위칭 비율, 의성어 추출.
  Triggers: "my vocabulary", "lexicon", "word habits", "speech patterns".
---

# lexi — 어휘 축

독립형 어휘 추출 및 분석. extract-lexicon.sh를 실행하고, 결과를 제시하며, 축별 주장을 기록합니다.

## 프로세스

1. 범위 요청 (repo/global)
2. scan-transcripts.sh 실행
3. extract-lexicon.sh --input .honne/cache/scan.json --top 50 --min-sessions 2 실행
4. LLM이 evidence-gather.sh 인용으로 상위 용어를 요약
5. HITL: 샘플과 함께 주장을 제시하고 (y/n/edit) 요청
6. 주장/거절 자산으로 기록
7. 과거 거절을 확인하여 재제안 방지

**진행 모니터링** — Monitor until-loop 사용 (`sleep N && cat` 금지):
```bash
# ✓ Monitor: until [ -f ".honne/cache/lexicon.json" ]
```

stdout + .honne/assets/claim.jsonl에 저장된 보고서
