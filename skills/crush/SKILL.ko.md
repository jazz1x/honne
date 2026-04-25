---
name: crush
version: 0.0.2
description: >
  두 인격(비효율 vs 강점)이 주제를 두고 벌이는 라이브 토론.
  Triggers: "crush", "debate personas", "personas fight", "/honne:crush".
---

# honne — 인격 토론 (실시간)

**호출 시 1단계부터 6단계까지 순서대로 즉시 실행합니다. 스킬 인자가 제공되면 토론 주제로 사용하고, 그렇지 않으면 묻습니다.**

## 1단계: 주제 획득

`skill_args`가 비어있지 않으면: `TOPIC = skill_args를 공백으로 연결`

그 외: 일반 텍스트 질문: "두 인격이 토론할 주제는?"

응답에서 `TOPIC`을 설정합니다.

## 2단계: 인격 검증

존재하는 인격 파일 개수를 셉니다:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" persona check --persona .honne/personas/antipattern.md
```
```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" persona check --persona .honne/personas/signature.md
```
```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" persona check --persona .honne/personas/judge.md
```

각 exit 0 (존재) 또는 exit 66 (미존재). 조합 결과에 따라 분기:

- **세 개 모두 exit 0** → 3단계 진행.
- **세 개 모두 exit 66** → 사용자에게 알림: "인격이 없습니다. 먼저 `/honne:persona`를 실행해 생성하세요." 중지.
- **혼합** → 사용자에게 알림: "토론은 antipattern·signature 인격과 심판자가 모두 필요합니다. 현재 인격은 한 축만 검출되었습니다. 세션을 더 수집한 뒤 `/honne:whoami` + `/honne:persona`를 재실행하세요." 중지.

## 3단계: 인격 로드

정신적 컨텍스트에 세 파일을 모두 읽습니다:
- `.honne/personas/antipattern.md` → 시스템 프롬프트 및 `# ` 헤더에서 `name` 추출
- `.honne/personas/signature.md` → 시스템 프롬프트 및 `name` 추출
- `.honne/personas/judge.md` → 시스템 프롬프트 추출

헤더 후 첫 `# Name` 라인을 읽어 각 `name`을 추출합니다.

## 4단계: 1라운드 — 비효율 공격

`.honne/personas/antipattern.md` 시스템 프롬프트를 정신적으로 적용합니다.

TOPIC에 대해 비효율 관점에서 2~3문장의 공격을 생성합니다.

출력 레이블: `**[비효율 — {name}]**` 그 후 공격.

## 5단계: 1라운드 + 2라운드 — 강점 & 반박

`.honne/personas/signature.md` 시스템 프롬프트를 적용합니다.

비효율의 공격에 대한 2~3문장의 반박을 생성합니다.

레이블: `**[강점 — {name}]**` 그 후 반박.

그 다음, 비효율 관점으로 돌아가: 2~3문장의 재반박.

레이블: `**[비효율 — {name}]**` 그 후 재반박.

그 다음, 강점 관점으로 돌아가: 2~3문장의 최종 주장.

레이블: `**[강점 — {name}]**` 그 후 최종 주장.

## 6단계: 심판자의 판결

`.honne/personas/judge.md` 시스템 프롬프트를 적용합니다.

2~3문장의 판결을 생성합니다: 어떤 접근이 상황적으로 더 적절하며, 그 이유는 무엇인지.

레이블: `**[판결]**` 그 후 판결.

---

## 출력 형식

이 마크다운 구조로 전체 대본을 출력합니다:

```markdown
**주제**: {TOPIC}

**[비효율 — {name}]**
{1라운드 공격}

**[강점 — {name}]**
{1라운드 반박}

**[비효율 — {name}]**
{2라운드 재반박}

**[강점 — {name}]**
{2라운드 최종}

**[판결]**
{심판자 판결}
```

파일 쓰기 없음. 대본은 임시 — 현재 세션에서만 표시됩니다.
