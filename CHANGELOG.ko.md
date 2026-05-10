# 변경 로그

## [0.0.5] — 2026-05-10

5개 스킬 전체에 SSL audit 결과 반영. v0.0.4 가 SSL 계약을 frontmatter 로 끌어올렸다면, v0.0.5 는 정적 audit 가 발견한 누락을 메웁니다 — `tools` 와 `branches` 가 모든 스킬에서 비어있었고, 두 스킬은 트리거 substring 충돌이 있었으며, `compare` 는 `idempotent` 가 잘못 선언되어 있었습니다. 본문 산문에서 자기 반복되는 부분도 정리했습니다 — 정보 손실 0.

### 추가

- `ssl.logical.tools` 를 15 개 SKILL 파일 전체 (5 스킬 × 3 로케일) 에 선언. 각 스킬이 실제 호출하는 도구 (`bash`, `python3`, `Read`, `Write`, `AskUserQuestion`) 를 반영. v0.0.4 에서는 모든 스킬에 누락되어 있던 항목.
- `ssl.structural.branches` 를 15 개 SKILL 파일 전체에 선언. 본문 산문에 묻혀 있던 분기 조건 (예: `whoami` Step 4 의 `insufficient_evidence → skip`, `persona` Step 4 의 `conflict_present` 3-way, `crush` Step 2 의 `all-0/all-66/mixed`) 을 1급 선언으로 격상.
- `.gitignore`: `.galmuri/` 추가 (audit 리포트는 로컬 진단물이며 소스가 아님).

### 변경

- **`whoami` 본문 — `HARD RULE` + `IMPORTANT` 통합**: 인접한 두 블록이 같은 `/tmp` · heredoc 제약을 다른 표현으로 두 번 말하던 것을 단일 불릿 리스트로 통합 (로케일별).
- **트리거 substring 충돌 해소** (Scheduling layer):
  - `whoami` 트리거 `"honne"` → `"honne whoami"` — 단독 `"honne"` 가 `persona` 의 `"honne persona"` 및 `crush` 의 `"/honne:crush"` 와 substring 매치.
  - `persona` 트리거에서 `"who am I as Claude"` 제거 (`whoami` 의 `"who am I"` 와 substring 충돌); 해소 사실을 `anti_trigger` 로 명시.
- **`compare` — `idempotent: true` → `false`**: `summarize` 분기에서 비결정적 LLM 호출이 발생하므로 이전 선언이 부정확했음. rollback 문자열은 이미 올바른 상태.
- 5개 스킬 모두 `version: 0.0.4` → `0.0.5` (3 로케일).
- `plugin.json` 버전 `0.0.4` → `0.0.5`.
- `scripts/honne_py/__init__.py` `__version__` → `0.0.5`.
- README 배지 및 welcome 라인 0.0.5 로 갱신 (en / ko / jp).

### 수정

- `compare` 의 idempotency 선언이 실제 동작과 일치 (위 변경 항목 참조). 이전에는 `idempotent: true` 를 신뢰하는 감사 도구가 `summarize` 분기에서 안전한 재실행을 오인할 수 있었음.

---

## [0.0.4] — 2026-05-07

모든 스킬에 SSL frontmatter 컨벤션을 적용했습니다. v0.0.3 스킬을 감사한 결과 scheduling 트리거, structural 단계 경계, logical 부작용이 본문 산문 안에 묻혀 있어 — 사람은 읽을 수 있어도 정적 검사는 불가능한 상태였습니다. v0.0.4는 이 계약들을 YAML frontmatter 로 끌어올려, 본문을 읽지 않고도 리뷰어(혹은 향후 도구)가 검사할 수 있도록 했습니다.

### 추가

- `docs/conventions/ssl-frontmatter.md` — 정식 SSL (Scheduling–Structural–Logical) 스키마, 6단계 마이그레이션 가이드, 안티패턴 카탈로그. 영문 단일본 (내부 계약 문서이며 user-facing 문서인 README/CHANGELOG 만 트라이링구얼 유지). Schank & Abelson 스크립트 이론과 arXiv:2604.24026 을 참고합니다.
- 기존 5개 스킬에 `ssl:` frontmatter 블록을 추가했습니다. `scheduling.anti_triggers`, `structural.scenes` + `resumable`, `logical.side_effects` + `idempotent` + `rollback` 을 선언합니다. `.ko.md` / `.jp.md` 로케일에도 동일하게 미러링 (총 15개 SKILL 파일).
- `tests/manifest.bats` 게이트: 모든 SKILL 파일(ko/jp 포함)이 `ssl:` 블록과 6개 필수 키 (`ssl:`, `scheduling:`, `structural:`, `logical:`, `side_effects:`, `idempotent:`) 를 선언함을 검증합니다. 신규 스킬은 컨벤션을 회귀시킬 수 없습니다.

### 변경

- **`compare` 스킬 본문**: Step 6 헤더를 `No writes` → `Asset immutability check` 로 변경했습니다. 기존 명칭은 전역 no-writes 를 시사했지만 Step 5 에서 `docs/honne-compare.md` 를 실제로 작성하므로, 보호 대상이 `.honne/assets/` 와 `.honne/persona.json` 에 한정된다는 점을 명확히 했습니다.
- **`lexi` 스킬 본문**: 단일 7항목 번호 리스트 구조를 명시적인 `## Step 1:` … `## Step 7:` 헤더로 재구조화했습니다. Step 1 에서 scope 와 locale 을 함께 묻도록 변경했습니다 (기존에는 scope 만 물으면서 `LOCALE` 을 이후 단계에서 마치 수집된 것처럼 사용하던 침묵 계약 위반을 감사가 적발).
- 기존 5개 스킬의 `version` 을 3개 로케일 모두 `0.0.3` → `0.0.4` 로 올렸습니다.
- `plugin.json` version `0.0.3` → `0.0.4`.
- `scripts/honne_py/__init__.py` `__version__` 을 `0.0.4` 로 갱신.
- README 배지와 welcome 라인 0.0.4 반영 (en / ko / jp).

### 수정 (선언 보강 — 동작 변경 아님)

- **record-claim append-only 동작 명시화**: `record-claim` 이 `claims.jsonl` / `rejections.jsonl` 을 mode `"a"` 로 열고 `claim_id` 에 `created_at` 을 포함해 dedup 이 절대 트리거되지 않는 동작이 그동안 문서화되지 않았습니다. 이제 frontmatter 에 `idempotent: false` 로 선언하고 구체적인 rollback 절차를 명시했습니다 (`whoami`, `lexi`).
- **gitignore 인지 rollback 문자열**: `.honne/`, `docs/honne.md`, `docs/honne-compare.md` 가 모두 `.gitignore` 대상이므로 `git checkout` 을 권하는 rollback 조언은 사실상 무효였습니다. rollback 문자열은 호출 전 `cp` 백업을 권장하도록 수정했습니다.

### 방법론 노트

감사는 반복적으로 진행되었습니다. 1차 패스에서 부작용·멱등성·롤백 경로에 대한 사실 주장을 정리했고, 2차 자기 검수 패스에서 1차의 결함 4건을 — 가장 큰 것은 `.gitignore` 대상 경로에 대한 `git checkout` 롤백 권고 — 적발했습니다. 정정된 결과를 v0.0.4 frontmatter 로 적용하고, 컨벤션을 `docs/conventions/ssl-frontmatter.md` 에 정리하고, 향후 회귀를 막는 `manifest.bats` 게이트를 추가했습니다. 신규 런타임 도구 없음, 신규 스킬 없음, 신규 CLI 표면 없음 — 컨벤션과 정적 게이트만.

---

## [0.0.3] — 2026-04-28

프로덕션 하드닝: ralphi 검수로 발견한 14개 이슈 전량 해결, 신규 커버리지 테스트 80+ 추가, 테스트 작성 과정에서 실제 버그 1건 발견·수정.

### 수정

#### 치명적 오류 (Critical)

- **synthesis_prompt (3개 로케일 전체)**: LLM 출력 JSON 스키마에서 `signature` 축이 누락되어 있었습니다. `"axes"` 오브젝트가 6개 키만 갖고 있어 내러티브 합성 시 signature 해설이 항상 `null`로 반환되었습니다. `"signature": "..." | null` 추가, oneliner 지침의 "6개 축 교차 참조" → "7개 축"으로 수정.
- **query.py**: `--scope`, `--tag`, `--tags` 파라미터가 CLI에는 존재했지만 필터 루프에서 실제로 적용되지 않아 항상 전체 결과를 반환했습니다. scope는 `obj["scope"] != scope`로, tag는 `obj["axis"]`로, tags는 쉼표 구분 축 목록으로 필터링.

#### 경고 (Warning)

- **index.py session_id**: 모든 인덱스 세션에 `""` 하드코딩. JSONL 파일명 stem(`Path(jsonl_path).stem`)에서 실제 세션 ID를 파생하도록 수정.
- **index.py content-as-list**: Claude Code 형식에서 `message.content`가 블록 배열(`[{"type":"text","text":"..."}]`)일 수 있음. 텍스트 블록을 병합한 후 100자 자름.
- **lexi SKILL (3개 로케일)**: 단계별 지시에서 삭제된 셸 스크립트명(`scan-transcripts.sh` 등) 참조. `honne axis run lexicon` + `honne record claim` 패턴으로 업데이트.
- **whoami SKILL (3개 로케일)**: frontmatter와 H1에 "6-Axis" 표기가 남아 있었음 (v0.0.1부터 이미 7축 구현). "7-Axis"로 수정.
- **whoami SKILL 3단계**: HITL 거절 분기에 기록 경로가 없었음. "n" 분기에 `honne record claim --type rejection` 추가. evolutions는 구조적 TODO로 유지.
- **whoami SKILL preamble**: "Step 1 ~ Step 7"로 잘못 표기 → "Step 1 ~ Step 6"으로 수정 (0.0.2 구조 재편 이후 스텝 수가 맞지 않았음).
- **criteria-persona.md**: 축 테이블에 signature 행 누락. 7번 행 추가 (≥ 3 세션 임계값, 설명 포함).

#### 커버리지 (Coverage)

- **precommit.py**: README에서 marketplace.json `source: "./"` 차단을 주장했지만 실제 구현이 없었음. 이제 staged 파일 검증 시 상대 경로 `source` 값을 가진 플러그인을 실제로 거부.
- **evidence.gather() max_ 버그**: 내부 메시지 루프의 `break`가 메시지 반복만 중단하고 외부 세션 루프는 계속 실행되어 max_ 제한이 사실상 무효였음. 외부 루프에 가드 추가.

#### 라운드 2 (커버리지 테스트 작성 중 발견)

- **scan.py since 필터**: datetime 문자열 형식의 `since`(`"2025-06-01T00:00:00Z"`)를 파일 mtime 날짜와 직접 비교해 같은 날 파일이 누락될 수 있었음. 비교 전 `since[:10]`으로 정규화.
- **scan.py known_shas 가드**: `sha256` 필드 없는 세션 레코드의 빈 문자열 `""`이 `known_shas`에 추가되었음. `if sha:` 가드 추가.
- **extract.py 해시 결정론성**: `hash(first_10_lines)`는 PYTHONHASHSEED에 따라 달라짐. `hashlib.sha256`로 교체.
- **extract.py obsession matched_sessions**: 언어 감지 여부와 무관하게 모든 세션을 카운트했음. 언어 실제 감지 시에만 추가.
- **record.py ID 충돌**: 주장 ID 해시가 `type + axis + claim`만 사용 — 동일 주장이 다른 run_id에서 충돌 가능. `run_id` + `created_at` 포함.
- **render.py quote_line 미구현**: 보고서에 인용문이 렌더링되지 않았음. 축당 최대 3개 `quote_line` 렌더링 구현.
- **cli.py 침묵 폴스루**: 미인식 커맨드 조합이 `return 0`으로 조용히 빠져나가던 것을 stderr 오류 출력 + exit 1로 변경.

### 추가

#### 테스트 (+80개, pytest 총 353개)

- `unit_scan_since_test.py`: since 필터 날짜 정규화 (3개)
- `unit_core_modules_test.py`: `detect_recurrence`, `evidence`, `purge`, `io` 동작 테스트 (20개)
- `unit_extractor_test.py`: reaction, workflow, ritual, obsession, antipattern 경계 조건 (35개)
- `unit_render_test.py` — `TestQuoteLineRendering`: 인용문 렌더링 회귀 방지 (5개)
- `unit_summarize_test.py` — parametrize 행렬 6×3=18 → 7×3=21 (signature 축 추가)
- `unit_query_filter_test.py`: scope / tag / tags / 복합 필터 (14개)
- `e2e_pipeline_test.py`: scan → 7축 추출 → claim 기록 E2E (4개)
- `e2e_query_filter.bats`: CLI scope/tag 필터 (7개 bats)
- `e2e_doctor.bats`: `honne doctor` exit code, 디렉터리 생성, 쓰기 불가 가드 (3개 bats)
- `manifest.bats` 확장: pre-commit 상대 경로 거부, 레지스트리 URL 허용 (bats 3개 추가)

### 변경

- `__version__` `0.0.2` → `0.0.3`
- `plugin.json` version `0.0.2` → `0.0.3`
- 골든 렌더 픽스처 (`tests/fixtures/render/case_*/expected_honne.md`) 재생성 (quote_line 반영)

---

## [0.0.2] — 2026-04-26

Split-persona 피벗: 두 개의 독립 페르소나를 따로 생성하고, 신규 `/honne:crush` 스킬로 라이브 토론.

### 추가

- **persona**: `build_conflict_payload` — antipattern × signature 축으로 갈등 페이로드 생성 (conflict_present 플래그 포함)
- **persona 합성**: `persona_synthesis_prompt.{locale}.md` — 두 개의 독립 페르소나 + 심판 생성. 출력 스키마: `{conflict_present, persona_antipattern, persona_signature, judge_system_prompt}`
- **render personas**: `honne render personas` — `.honne/personas/`에 antipattern.md / signature.md / judge.md 생성
- **/honne:crush** 스킬: 5턴 토론 (antipattern 공격 → signature 반박 → antipattern 반격 → signature 마무리 → 심판 판결). 파일 쓰기 없음, 에페머럴 트랜스크립트.
- 템플릿: `persona_synthesis_prompt.{locale}.md`, `persona_render.md` (3 로케일)
- CLI: `honne render personas`, `honne persona check` 추가

### 변경

- **persona 스키마 파괴적 변경**: 기존 `{verdict, character_oneliner, debate, ...}` → 신규 `{conflict_present, persona_antipattern, persona_signature, judge_system_prompt}`
- `whoami` SKILL bash 블록 재구조화 (stdout 캡처 패턴, `allowedTools` 매칭성 향상)
- `crush` SKILL: raw bash 파일 체크 → `honne persona check` CLI 호출로 교체
- `compare`, `lexi` SKILL: `HONNE_ROOT` 변수 제거, `${CLAUDE_PLUGIN_ROOT}` 직접 사용

### 수정

- `record.py`: `Union` 임포트 누락(런타임 NameError) 수정
- `record.py`: `--quotes-file`에 잘못된 스키마 JSON 전달 시 경고(기존: 침묵 빈 fallback)
- `axis.py`: 스캔 파일 없을 때 오류 메시지 출력(기존: 침묵 exit 66)
- `redact.py`: 패턴 6종 추가 — Slack API 토큰, GitHub fine-grained PAT, GCP API 키, PEM 개인키 블록
- `doctor.py`: `.honne/` mkdir OSError 시 진단 메시지 출력(기존: 침묵)
- `purge.py`: `--keep-assets` 시 symlink 자식 검사 후 rmtree
- `cli.py`: `--base-dir` 인수가 `run_scan()`에 실제로 전달되도록 수정(기존: 침묵 무시)
- 버전 `0.0.1` → `0.0.2`

### 제거

- `persona_prompt.{locale}.md` 템플릿 (→ `persona_render.md`로 통합)
- `/honne:setup` 스킬 (allowedTools 자동 설정 비효율 → auto mode 권장)
- persona 출력의 활성화 지시문 제거 (in-session 구현 주장 삭제)

---

## [0.0.1] — 2026-04-23

초기 릴리스 — 로컬 LLM 트랜스크립트로부터의 증거 기반 자기 관찰.

- 코어 스킬: `whoami` (6축 페르소나 오케스트레이터), `lexi` (어휘 축), `compare` (자산 비교, 읽기 전용 회고)
- 세션 종료 훅(`SessionEnd`): 수동 트랜스크립트 인덱싱, 메타데이터만
- `.honne/assets/*.jsonl` 자산 레이어 (claims / rejections / evolutions) — 명시 쿼리 전용
- 사용자 대면 문서 3개 로케일 (en / ko / jp)
