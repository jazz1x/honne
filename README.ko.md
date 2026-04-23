# honne

> Claude Code 플러그인 — LLM 트랜스크립트로부터의 자기 관찰

![version](https://img.shields.io/badge/version-0.0.1-blue)
![license](https://img.shields.io/badge/license-MIT-green)
![claude-code](https://img.shields.io/badge/claude--code-plugin-purple)

**honne** (本音, "진짜 속마음") — 당신이 LLM 과 실제로 어떻게 일하는지를 로컬에서 증거 기반으로 비추는 거울입니다. 공식 페르소나(*tatemae*) 아래, 당신의 transcripts 가 조용히 기록해 둔 것들 — 반복 어휘, 거절한 제안, 세션 의식(儀式), 스스로도 이름 붙인 적 없던 패턴 — 을 드러냅니다.

모든 처리는 로컬에서 이뤄집니다. 네트워크 호출 없음, 분석 추적 없음. 주장은 자율적으로 기록되고 LLM 내러티브 합성으로 해설됩니다. 데이터는 `.honne/` 아래 평범한 JSONL 로 — 옮기기 쉽고, 들여다보기 쉽고, 지우기 쉽습니다.

[English](./README.md) · [日本語](./README.jp.md)

## 스킬

| 스킬 | 명령 | 역할 |
|------|------|------|
| **whoami** | `/honne:whoami` | 메인 오케스트레이터. 6축 페르소나 + 자율 증거 수집 + LLM 내러티브 합성. |
| **lexi** | `/honne:lexi` | 어휘(Lexicon) 축 단독 (고빈도 어휘, 코드스위칭 비율, 의성·의태어). |
| **compare** | `/honne:compare` | 읽기 전용 회고. 누적 자산을 읽어 시간축 변화를 제시. transcript 재스캔 / LLM 재분석 없음. |

각 스킬은 독립적으로 동작하며, **파일 기반 공유 산출물** (`.honne/cache/`, `.honne/persona.json`, `.honne/assets/*.jsonl`) 로만 연결됩니다.

```
 트랜스크립트 (~/.claude/projects/**/*.jsonl)
      │
      │  honne  ──→  .honne/persona.json + docs/honne.md  (6축 스냅샷)
      │                  │
      │                  ├── honne record claim  ──→  .honne/assets/*.jsonl (종단적 축적)
      │                  │
      │  lexi   ──→  .honne/persona.json (축 1번만)
      │
 SessionEnd 훅 ──→  .honne/cache/index.json  (메타데이터만, passive 인덱싱)
                              │
 compare (읽기 전용) ──→  honne query  ──→  docs/honne-compare.md  (과거 주장 diff)
```

## 필수 요구사항 (Prerequisites)

honne 는 **python3 ≥ 3.9** 만 필요합니다. 그 외 의존성 없음.

```bash
python3 --version   # 3.9 이상이어야 함
```

python3 가 없거나 3.9 미만이면 스크립트는 exit code 4 로 종료됩니다. `jq`, `ripgrep` 은 더 이상 필요하지 않습니다.

## 설치

### 1. 마켓플레이스 등록

Claude Code 세션 안에서 실행:

```
/plugin marketplace add https://github.com/jazz1x/honne.git
```

기대 출력:

```
✓ Marketplace 'honne' added (1 plugin)
```

### 2. 플러그인 설치

```
/plugin install honne --scope user
```

기대 출력:

```
✓ Installed honne@0.0.1 — 3 skills registered (whoami, lexi, compare)
```

스코프 선택:

| 스코프 | 효과 | 사용 시점 |
|--------|------|-----------|
| `--scope user` *(권장)* | `~/.claude/` 에 설치 — **모든 프로젝트**의 transcripts 스캔 가능 | 일반적인 사용. 자기 관찰은 프로젝트를 가로지르는 이력이 있을수록 풍부해집니다. |
| `--scope local` | 현재 프로젝트의 `.claude/` 에만 설치 | 시범 사용, 또는 의도적으로 단일 프로젝트 범위로 제한하고 싶을 때. |

### 3. 설치 확인

```
/plugin list
```

`honne` 이 리스트에 보여야 합니다. 아래 세 개의 본체 슬래시 명령이 자동완성되면 OK:

```
/honne:whoami
/honne:lexi
/honne:compare
```

`SessionEnd` 훅은 자동 등록 — 추가 설정 없음.

### 4. 삭제

```
/plugin uninstall honne
/plugin marketplace remove honne
```

`.honne/` 디렉터리는 삭제 명령에 **영향받지 않습니다** — 당신의 자산은 보존. 완전 제거를 원하면 `bash scripts/purge.sh --all` 로 수동 삭제.

---

## Quickstart

설치 후 가장 빠른 체험 경로:

```
# Claude Code 세션 안에서, 아무 프로젝트에서
/honne:whoami
```

샘플 흐름 (단순화):

```
user   > /honne:whoami

step 1 > 스캔 범위?  ← 화살표 키 메뉴 (repo / global)
         언어?       ← 화살표 키 메뉴 (ko / en / jp)
user   > [global, ko 선택]

step 2 > transcripts 스캔 ~/.claude/projects/… → .honne/cache/scan.json
         run_id 자동 생성; 민감 패턴(12종) + Claude Code 메타 가림

step 3 > 6축 자율 추출 [lexicon, reaction, workflow, obsession, ritual, antipattern]
           - axis run → 스캔 캐시에서 결정론적 시그널 추출
           - 거절 필터 적용 (과거 거절과 겹치는 후보 자동 스킵)
           - .honne/assets/claims.jsonl 에 자율 기록 (축별 확인 프롬프트 없음)

step 4 > LLM 내러티브 합성
           - synthesis_prompt.ko.md 를 매칭된 주장에 적용
           - 축별 해설 + 한줄평 → .honne/cache/narrative.json

step 5 > 페르소나 + 보고서 렌더링
✓ 저장: .honne/persona.json
✓ 저장: docs/honne.md
✓ append: .honne/assets/claims.jsonl
```

2회차 이상 실행되면 과거 프로필과 비교 가능:

```
/honne:compare
```

디스크에 있는 것만 읽습니다 — transcript 재스캔 없음, LLM 재분석 없음.

## 사용법

### 1. 최초 프로필 생성

```
사용자: "나는 누구" 또는 /honne:whoami
→ honne 가 범위(repo / global) + 언어(ko / en / jp) 확인
→ transcripts 스캔 → 6축 자율 추출 → 주장 기록
→ LLM 이 축별 해설 + 한줄평 합성
→ .honne/persona.json + docs/honne.md 렌더링
```

### 2. 단일 축

```
사용자: "내 말버릇만" 또는 /honne:lexi
→ lexi 가 transcripts 스캔 → lexicon 축만 → 자율 기록
→ lexicon 축 claim 자산 기록
```

### 3. 회고 (2회차 이상 실행 후)

```
사용자: "지난번이랑 비교" 또는 /honne:compare
→ compare 가 과거 claim + evolution 자산 로드 (read-only)
→ 축 × 시간 버킷으로 그룹핑
→ docs/honne-compare.md 렌더링 (identical / evolved / reversed / new)
```

### 4. 데이터 소거권

```bash
bash scripts/purge.sh --all           # .honne/ 전체 삭제
bash scripts/purge.sh --keep-assets   # cache 만 삭제, 종단적 자산 유지
```

두 명령 모두 확인을 위해 `DELETE` 입력이 필요합니다. 네트워크 개입 없음.

## 훅 (Hooks)

honne 는 설치 시 단일 훅을 자동 등록합니다. 별도 설정 불필요.

| 이벤트 | 트리거 | 동작 |
|--------|--------|------|
| `SessionEnd` | 세션 종료 | `scripts/index-session.sh` 실행 — 세션 메타 (id, 타임스탬프, sha256, 메시지 수) 를 `.honne/cache/index.json` 에 append. **LLM 호출 없음, 컨텍스트 주입 없음, 분석 없음.** Silent-fail. |

훅은 passive 인프라입니다 — transcript 인덱스를 최신 상태로 유지해 이후 `whoami` / `lexi` / `compare` 수동 실행을 가속합니다. 분석은 항상 사용자 주도.

## 당신의 데이터

모든 데이터는 현재 프로젝트 디렉터리의 `.honne/` 아래에 로컬로만 저장됩니다:

| 경로 | 용도 |
|------|------|
| `.honne/cache/scan.json` | transcript 스캔 캐시 (휘발성, TTL 24h) |
| `.honne/cache/index.json` | SessionEnd 훅 출력 — 메타만, 메시지 본문 없음 |
| `.honne/persona.json` | 현재 6축 프로필 스냅샷 |
| `.honne/assets/claims.jsonl` | 자율 기록 주장 (종단 이력) |
| `.honne/assets/rejection.jsonl` | 거절 주장 (부적합 시그널) |
| `.honne/assets/evolution.jsonl` | 회차 간 diff 결과 (identical / evolved / reversed) |

**프라이버시**:
- 네트워크 호출 없음. 모든 처리는 로컬.
- 민감 패턴 (API 키, 토큰, webhook, 이메일, 전화번호, 홈 경로, IP, 신용카드 — 총 12 패턴) 은 quote 저장 전 가림 처리됩니다. `scripts/honne_py/redact.py` 참조.
- 자산은 세션 컨텍스트에 **자동 주입되지 않습니다**. 사용자가 `compare` 를 명시 호출하거나 `query-assets.sh` 를 직접 실행할 때만 로드됩니다.
- `CLAUDE.md` 자동 주입은 영구 금지 (자기강화 루프 방어).

**Export**: `.honne/` 는 평범한 디렉터리입니다. `tar czf my-honne.tgz .honne/` 로 어디든 옮길 수 있습니다. 당신의 데이터, 당신이 관리.

## 워크트리 (Worktrees)

각 워크트리는 CWD 기반으로 독립된 `.honne/` 디렉터리를 가집니다. 페르소나 스냅샷과 종단 자산은 워크트리별로 완전히 격리 — 공유 상태 없음.

```
/project/.honne/                      ← 메인
/project/.claude/worktrees/A/.honne/  ← 워크트리 A (독립)
/other/path/worktree-B/.honne/        ← 워크트리 B (물리적 격리)
```

## 정직한 사용 고지 (Honest-use Notice)

honne 는 **트랜스크립트에 실제로 나타난 패턴** 을 드러냅니다. 그 패턴은 특정 맥락에서 LLM 과 어떻게 상호작용했는지에 대한 증거이지, 당신이 어떤 사람인지에 대한 판단이 아닙니다. 거절된 주장은 "당신이 실패했다" 가 아니라 "이 프레이밍이 이 데이터에 맞지 않았다" 를 의미합니다. antipattern 은 "당신이 잘못됐다" 가 아니라 "이런 것이 관찰되었다" 를 의미합니다.

출력 중 불편함을 주는 것이 있다면 삭제하세요 — `bash scripts/purge.sh --all`. 데이터는 로컬에만 존재하며, 네트워크 호출이나 분석 추적이 일절 없습니다.

**honne 는 작업 패턴의 거울이지, 정신 건강 도구가 아닙니다.** 정신적 안녕에 관한 우려가 있다면 전문가와 상담하세요.

## 네이밍

- **honne** (本音) — 공식 페르소나 아래의 진짜 목소리. 일본어 어원, *tatemae* (建前) 와 짝.
- **lexi** — lexicon + i (어휘 축 단독)
- **compare** — 과거와 현재를 비교하는 회고 (transcript 재스캔 없음)

## 트라이어드 (Triad)

honne 는 두 자매 플러그인 사이에 위치합니다 — 독립적으로 동작하며, 공유 산출물로만 연결됩니다:

```
harnish (make)  ──→  honne (know)  ──→  galmuri (keep)
   실행             자기 관찰             갈무리·정리
```

- [harnish](https://github.com/jazz1x/harnish) — 자율 구현 엔진
- [honne](https://github.com/jazz1x/honne) — 증거 기반 자기 관찰 (6축 페르소나)
- [galmuri](https://github.com/jazz1x/galmuri) — 컨텍스트 갈무리·정리·보관 (구 *hanashi*)

## 개발

clone 직후 한 번만 pre-commit 훅을 활성화:

```bash
git config core.hooksPath .githooks
```

훅 ([scripts/pre-commit.sh](scripts/pre-commit.sh)) 은 스테이징된 파일을 검증합니다: shell lint (`shellcheck` 또는 `bash -n` fallback), JSON 구문, `SKILL.md` frontmatter (`name` / `description` / SemVer `version`), 스크립트 실행 권한, `.claude-plugin/marketplace.json` 스키마 (`source: "."` 함정은 여기서 차단).

### 테스트 스위트

하이브리드 테스트 스위트 실행 (파이썬 helper 는 pytest, shell/매니페스트는 bats):

```bash
bash tests/run.sh
```

최초 1회 설치 — `brew install bats-core` (macOS) 또는 `apt install bats` (Linux). 모든 테스트는 임시 `HOME` 및 `CLAUDE_PROJECT_DIR` 샌드박스에서 실행되며, 실제 `~/.claude/` · `~/.honne/` 는 절대 건드리지 않습니다. 실수로 실제 HOME 에 착지하면 [tests/setup.bash](tests/setup.bash) 의 가드가 즉시 abort.

## Footnote

> *"판단하지 않고 비추는 거울은 드물다. 당신이 이미 쓴 것만 보여주는 거울이야말로 가장 정직한 종류다."*

honne 는 지어내지 않습니다 — 당신의 트랜스크립트가 이미 담고 있는 것만 드러냅니다. 쓰지 않은 말을 들려준다면, 우리가 잘못 만든 것입니다.

## 라이선스

MIT — [LICENSE](./LICENSE) 참조.
