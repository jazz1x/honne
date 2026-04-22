# honne

> Claude Code 플러그인 — LLM 트랜스크립트로부터의 자기 관찰

**honne** (本音, "진짜 속마음") — 당신이 LLM 과 실제로 어떻게 일하는지를 로컬에서 증거 기반으로 비추는 거울입니다. 공식 페르소나(*tatemae*) 아래, 당신의 transcripts 가 조용히 기록해 둔 것들 — 반복 어휘, 거절한 제안, 세션 의식(儀式), 스스로도 이름 붙인 적 없던 패턴 — 을 드러냅니다.

[English](./README.md) · [日本語](./README.jp.md)

## 필수 요구사항 (Prerequisites)

honne 는 `jq` 와 `python3` 또는 `ripgrep` 둘 중 하나가 필요합니다. 사용 전에 설치해 주세요:

```bash
# macOS — python3 는 이미 설치되어 있음
brew install jq
# (선택) brew install ripgrep

# Linux (apt) — python3 는 대부분 기본 설치되어 있음
sudo apt install jq
# (선택) sudo apt install ripgrep
```

확인: `command -v jq && { command -v python3 || command -v rg; }`. 둘 다 없으면 스크립트는 exit code 4 로 종료됩니다.

**백엔드 선택**: 스크립트는 자동으로 `python3` 을 우선 감지합니다 (네이티브 유니코드 토크나이징 + 단일 pass 리댁션으로 성능 우수). 없으면 `ripgrep` 으로 fallback. 별도 설정 불필요.

## 설치

### 1. 마켓플레이스 등록

Claude Code 안에서 이 저장소를 플러그인 마켓플레이스로 등록:

```
/plugin marketplace add https://github.com/jazz1x/honne.git
```

성공 시 `Marketplace "honne" added` 출력.

### 2. 플러그인 설치

```
/plugin install honne --scope user
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

`honne` 이 활성 플러그인으로 보여야 합니다. `SessionEnd` 훅은 자동 등록 — 추가 설정 없음.

### 4. 첫 실행

```
/honne:honne
```

메인 오케스트레이터 진입. 첫 호출 시 스캔 범위(현재 repo / 전역)를 묻고, 6 개 축을 HITL 로 순회합니다. 전체 흐름은 [사용법](#사용법) 참조.

## 스킬

| 스킬 | 명령 | Alias | 역할 |
|------|------|-------|------|
| **honne** | `/honne:honne` | `/honne:whoami` · `/honne:hon-me` | 메인 오케스트레이터. 6축 페르소나 + 축별 HITL 승인. |
| **lexi** | `/honne:lexi` | `/honne:hon-word` | 어휘(Lexicon) 축 단독 (고빈도 어휘, 코드스위칭 비율, 의성·의태어). |
| **compare** | `/honne:compare` | `/honne:diff` · `/honne:hon-back` | 읽기 전용 회고. 누적 자산을 읽어 시간축 변화를 제시. transcript 재스캔 / LLM 재분석 없음. |

Alias 는 두 갈래: **의미적** (`whoami`, `diff`) — Unix 친숙한 진입점. **brand prefix** (`hon-me`, `hon-back`) — harnish `har-*` 스타일로 마켓플레이스에서 honne 계열 시각적 그룹핑. 양쪽 모두 동일 본체로 redirect.

각 스킬은 독립적으로 동작하며, **파일 기반 공유 산출물** (`.honne/cache/`, `.honne/persona.json`, `.honne/assets/*.jsonl`) 로만 연결됩니다.

```
 트랜스크립트 (~/.claude/projects/**/*.jsonl)
      │
      │  honne  ──→  persona.json + docs/honne.md  (6축 스냅샷)
      │                  │
      │                  ├── record-claim.sh  ──→  .honne/assets/*.jsonl (종단적 축적)
      │                  │
      │  lexi   ──→  persona.json (축 1번만)
      │
 SessionEnd 훅 ──→  .honne/cache/index.json  (메타데이터만, passive 인덱싱)
                              │
 compare (읽기 전용) ──→  query-assets.sh  ──→  docs/honne-compare.md  (과거 주장 diff)
```

## 사용법

### 1. 최초 프로필 생성

```
사용자: "나는 누구" 또는 /honne:honne
→ honne 가 범위 확인: repo / global?
→ transcripts 스캔 → 6축 추출 → 축별 HITL (y / n / edit)
→ .honne/persona.json + docs/honne.md 생성
→ 승인된 주장은 .honne/assets/claim.jsonl 에 자산으로 기록
```

### 2. 단일 축

```
사용자: "내 말버릇만" 또는 /honne:lexi
→ lexi 가 transcripts 스캔 → lexicon 축만 → HITL
→ lexicon 축 claim/rejection 자산 기록
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

훅은 passive 인프라입니다 — transcript 인덱스를 최신 상태로 유지해 이후 `honne` / `lexi` / `compare` 수동 실행을 가속합니다. 분석은 항상 사용자 주도.

## 당신의 데이터

모든 데이터는 현재 프로젝트 디렉터리의 `.honne/` 아래에 로컬로만 저장됩니다:

| 경로 | 용도 |
|------|------|
| `.honne/cache/scan.json` | transcript 스캔 캐시 (휘발성, TTL 24h) |
| `.honne/cache/index.json` | SessionEnd 훅 출력 — 메타만, 메시지 본문 없음 |
| `.honne/persona.json` | 현재 6축 프로필 스냅샷 |
| `.honne/assets/claim.jsonl` | HITL 승인 주장 (종단 이력) |
| `.honne/assets/rejection.jsonl` | HITL 거절 주장 (부적합 시그널) |
| `.honne/assets/evolution.jsonl` | 회차 간 diff 결과 (identical / evolved / reversed) |

**프라이버시**:
- 네트워크 호출 없음. 모든 처리는 로컬.
- 민감 패턴 (API 키, 토큰, webhook, 이메일, 전화번호, 홈 경로, IP, 신용카드 — 총 12 패턴) 은 quote 저장 전 가림 처리됩니다. `scripts/scan-transcripts.sh` §redact-secrets 참조.
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
- **whoami** / **hon-me** — `honne` 의 alias. `whoami` 는 Unix 친숙. `hon-me` 는 harnish `har-*` brand prefix 규약 대응.
- **hon-word** — `lexi` 의 alias. brand prefix 변형; "honne, 내 말" 로 읽힘.
- **diff** / **hon-back** — `compare` 의 alias. `diff` 는 범용어, `hon-back` 은 "honne, 되돌아보기" 로 읽힘.

## 트라이어드 (Triad)

honne 는 세 플러그인으로 이루어진 궤도의 한 축입니다:

- [harnish](https://github.com/jazz1x/harnish) — 자율 구현 엔진 (*만든다*)
- [honne](https://github.com/jazz1x/honne) — transcripts 로부터의 자기 관찰 (*안다*)
- [galmuri](https://github.com/jazz1x/galmuri) — 컨텍스트 갈무리·정리·보관 (*간직한다*)

## 개발

clone 직후 한 번만 pre-commit 훅을 활성화:

```bash
git config core.hooksPath .githooks
```

훅 ([scripts/pre-commit.sh](scripts/pre-commit.sh)) 은 스테이징된 파일을 검증합니다: shell lint (`shellcheck` 또는 `bash -n` fallback), JSON 구문, `SKILL.md` frontmatter (`name` / `description` / SemVer `version`), 스크립트 실행 권한, `.claude-plugin/marketplace.json` 스키마 (`source: "."` 함정은 여기서 차단).

## 라이선스

MIT
