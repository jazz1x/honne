# 변경 로그

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
