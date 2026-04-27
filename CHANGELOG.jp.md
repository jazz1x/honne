# 変更ログ

## [0.0.3] — 2026-04-28

プロダクション強化: ralphi 検査で特定した 14 件の問題を全件解決。カバレッジテスト 80+ 件追加。テスト作成中に実際のバグ 1 件を発見・修正。

### 修正

#### 致命的 (Critical)

- **synthesis_prompt (3 ロケール全体)**: LLM 出力 JSON スキーマから `signature` 軸が欠落していた。`"axes"` オブジェクトが 6 キーのみで、ナラティブ合成時に signature の解説が常に `null` を返していた。`"signature": "..." | null` を追加、oneliner 指示の "6 軸を参照" → "7 軸" に修正。
- **query.py**: `--scope`, `--tag`, `--tags` パラメーターが CLI には存在したが、フィルタループで実際に適用されず常に全件返却していた。scope は `obj["scope"] != scope` で、tag は `obj["axis"]` で、tags はカンマ区切り軸リストでフィルタリング。

#### 警告 (Warning)

- **index.py session_id**: 全インデックスセッションで `""` がハードコードされていた。JSONL ファイル名の stem から実際のセッション ID を導出するよう修正。
- **index.py content-as-list**: Claude Code 形式では `message.content` がブロック配列になる場合がある。テキストブロックを結合後に 100 字で切り詰めるよう対応。
- **lexi SKILL (3 ロケール)**: 廃止済みシェルスクリプト名を参照していた。`honne axis run lexicon` + `honne record claim` パターンに更新。
- **whoami SKILL (3 ロケール)**: frontmatter と H1 が "6-Axis" のままだった (v0.0.1 から既に 7 軸実装)。"7-Axis" に修正。
- **whoami SKILL ステップ 3**: HITL 拒否分岐に記録パスがなかった。"n" 分岐に `honne record claim --type rejection` を追加。
- **whoami SKILL preamble**: "Step 1 〜 Step 7" と誤記 → "Step 1 〜 Step 6" に修正。
- **criteria-persona.md**: 軸テーブルに signature 行が欠落。7 行目を追加。

#### カバレッジ (Coverage)

- **precommit.py**: README では marketplace.json の `source: "./"` をプリコミットでブロックすると記載していたが、実装がなかった。実際に拒否するよう実装。
- **evidence.gather() max_ バグ**: 内部メッセージループの `break` はメッセージ反復のみ終了し、外部セッションループは継続して max_ 上限が事実上無効だった。外部ループにガードを追加。

#### ラウンド 2 (カバレッジテスト作成中に発見)

- **scan.py since フィルター**: datetime 文字列形式の `since` を日付と直接比較して当日ファイルが欠落する可能性があった。比較前に `since[:10]` に正規化。
- **scan.py known_shas ガード**: `sha256` フィールドのないレコードの空文字列が `known_shas` に追加されていた。`if sha:` ガードを追加。
- **extract.py ハッシュ決定論性**: `hash()` は PYTHONHASHSEED に依存。`hashlib.sha256` に置き換え。
- **extract.py obsession matched_sessions**: 言語検出結果に関わらず全セッションをカウントしていた。実際に検出された場合のみ追加するよう修正。
- **record.py ID 衝突**: クレーム ID ハッシュが `type + axis + claim` のみ使用。`run_id` + `created_at` を含めるよう修正。
- **render.py quote_line 未実装**: レポートに引用行がレンダリングされていなかった。軸ごとに最大 3 件の引用行をレンダリングする実装を追加。
- **cli.py サイレントフォールスルー**: 未認識コマンド組み合わせが `return 0` で抜けていた。stderr にエラー出力 + exit 1 に変更。

### 追加

#### テスト (+80 件、pytest 合計 353 件)

- `unit_scan_since_test.py`: since フィルター日付正規化 (3 件)
- `unit_core_modules_test.py`: `detect_recurrence`, `evidence`, `purge`, `io` 動作テスト (20 件)
- `unit_extractor_test.py`: reaction, workflow, ritual, obsession, antipattern 境界条件 (35 件)
- `unit_render_test.py` — `TestQuoteLineRendering`: 引用行レンダリング回帰防止 (5 件)
- `unit_summarize_test.py` — パラメタライズ行列 6×3=18 → 7×3=21 (signature 軸追加)
- `unit_query_filter_test.py`: scope / tag / tags / 複合フィルター (14 件)
- `e2e_pipeline_test.py`: scan → 7 軸抽出 → claim 記録 E2E (4 件)
- `e2e_query_filter.bats`: CLI scope/tag フィルター (bats 7 件)
- `e2e_doctor.bats`: `honne doctor` exit code、ディレクトリ生成、書き込み不可ガード (bats 3 件)
- `manifest.bats` 拡張: プリコミット相対パス拒否、レジストリ URL 許可 (bats 3 件追加)

### 変更

- `__version__` `0.0.2` → `0.0.3`
- `plugin.json` version `0.0.2` → `0.0.3`
- ゴールデンレンダーフィクスチャー再生成 (quote_line 反映)

---

## [0.0.2] — 2026-04-26

Split-persona ピボット: 2 つの独立したペルソナを別々に生成し、新スキル `/honne:crush` でライブ討論。

### 追加

- **persona**: `build_conflict_payload` — antipattern × signature 軸から conflict ペイロードを生成
- **persona 合成**: `persona_synthesis_prompt.{locale}.md` — 2 つの独立ペルソナ + 審判を生成
- **render personas**: `honne render personas` — `.honne/personas/` に 3 つの `.md` ファイルを生成
- **/honne:crush** スキル: 5 ターン討論、ファイル書き込みなし、エフェメラルトランスクリプト
- CLI: `honne render personas`, `honne persona check` 追加

### 変更

- **persona スキーマ破壊的変更**: 旧 `{verdict, ...}` → 新 `{conflict_present, persona_antipattern, persona_signature, judge_system_prompt}`
- `whoami` SKILL bash ブロック再構造化
- `crush`, `compare`, `lexi` SKILL: 変数削除・CLI 呼び出しへの統一

### 修正

- `record.py`: `Union` インポート欠落 (ランタイム NameError) を修正
- `axis.py`: スキャンファイルがない場合にエラーメッセージを出力
- `redact.py`: パターン 6 種追加 (Slack / GitHub PAT / GCP / PEM)
- `cli.py`: `--base-dir` 引数が `run_scan()` に実際に渡されるよう修正
- バージョン `0.0.1` → `0.0.2`

### 削除

- `persona_prompt.{locale}.md` テンプレート (→ `persona_render.md` に統合)
- `/honne:setup` スキル
- persona 出力の活性化指示文

---

## [0.0.1] — 2026-04-23

初回リリース — ローカル LLM トランスクリプトからの証拠ベース自己観察。

- コアスキル: `whoami` (6 軸ペルソナオーケストレーター)、`lexi` (語彙軸)、`compare` (資産比較、読み取り専用振り返り)
- SessionEnd フック: 受動的トランスクリプトインデックス、メタデータのみ
- `.honne/assets/*.jsonl` 資産レイヤー (claims / rejections / evolutions) — 明示クエリ専用
- ユーザー対面ドキュメント 3 ロケール (en / ko / jp)
