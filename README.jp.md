# honne

> Claude Code プラグイン — LLM トランスクリプトからの自己観察

![version](https://img.shields.io/badge/version-0.0.2-blue)
![license](https://img.shields.io/badge/license-MIT-green)
![claude-code](https://img.shields.io/badge/claude--code-plugin-purple)

**honne** (本音) — あなたが LLM と実際にどう働いているかを、ローカルで証拠に基づいて映し出す鏡です。公式なペルソナ(*建前*)の下で、トランスクリプトが静かに記録していたもの — 繰り返される語彙、拒絶した提案、セッションの儀式、自分でも名付けたことのないパターン — を浮かび上がらせます。

すべての処理はローカルで完結します。ネットワーク呼び出しなし、解析トラッキングなし。主張は自律的に記録され、LLM ナラティブ合成で解説されます。データは `.honne/` 配下に平文の JSONL として — 持ち運びやすく、見やすく、削除しやすい形で保持されます。

[English](./README.md) · [한국어](./README.ko.md)

## スキル

| スキル | コマンド | 役割 |
|--------|----------|------|
| **whoami** | `/honne:whoami` | メインオーケストレーター。7 軸ペルソナ + 自律証拠収集 + LLM ナラティブ合成。 |
| **lexi** | `/honne:lexi` | 語彙 (Lexicon) 軸のみ (高頻度語彙、コードスイッチング比率、擬音語・擬態語)。 |
| **compare** | `/honne:compare` | 読み取り専用の振り返り。蓄積された資産を読み、経時的な変化を提示。transcript 再スキャン / LLM 再分析なし。 |
| **persona** | `/honne:persona` | アンチパターン & シグネチャ軸から 2 つの独立したペルソナを生成。`.md` ファイルとして `/honne:crush` で使用するために保存。 |
| **crush** | `/honne:crush` | 2 つのペルソナがトピックについてライブ討論。ペルソナファイルを読み、5 ターンのトランスクリプトと判決を生成。 |

各スキルは独立した軌道で動作し、**ファイルベースの共有成果物** (`.honne/cache/`, `.honne/persona.json`, `.honne/assets/*.jsonl`) でのみ接続されます。

```
 トランスクリプト (~/.claude/projects/**/*.jsonl)
      │
      │  honne  ──→  .honne/persona.json + docs/honne.md  (7 軸スナップショット)
      │                  │
      │                  ├── honne record claim  ──→  .honne/assets/*.jsonl (経時的蓄積)
      │                  │
      │  lexi   ──→  .honne/persona.json (軸 1 のみ)
      │
 SessionEnd フック ──→  .honne/cache/index.json  (メタデータのみ、受動的インデックス)
                              │
 compare (読み取り専用) ──→  honne query  ──→  docs/honne-compare.md  (過去主張の diff)
```

## 前提条件 (Prerequisites)

honne は **python3 ≥ 3.9** のみ必要です。他の依存関係はありません。

```bash
python3 --version   # 3.9 以上が必要
```

python3 がない、または 3.9 未満の場合、スクリプトは exit code 71 で終了します。

## インストール

### 1. マーケットプレイスを登録

Claude Code セッション内で実行:

```
/plugin marketplace add https://github.com/jazz1x/honne.git
```

期待される出力:

```
✓ Marketplace 'honne' added (1 plugin)
```

### 2. プラグインをインストール

```
/plugin install honne --scope user
```

期待される出力:

```
✓ Installed honne@0.0.2 — 5 skills registered (whoami, lexi, compare, persona, crush)
```

スコープの選択:

| スコープ | 効果 | 使う場面 |
|----------|------|----------|
| `--scope user` *(推奨)* | `~/.claude/` にインストール — **全プロジェクト**の transcripts を横断スキャン可能 | 通常利用。自己観察はプロジェクトを跨ぐ履歴があるほど豊かになります。 |
| `--scope local` | 現在のプロジェクトの `.claude/` のみにインストール | お試し利用、または意図的に単一プロジェクトに限定したい場合。 |

### 3. インストール確認

```
/plugin list
```

`honne` がリストに表示されていれば OK。以下の 3 つのスラッシュコマンドが補完できれば準備完了:

```
/honne:whoami
/honne:lexi
/honne:compare
/honne:persona
/honne:crush
```

> **Tip**: Claude Code を **auto mode** (`shift+tab` で切り替え) で実行するとスムーズです。honne スキルは多数の CLI コマンドを順次実行するため、auto mode が繰り返しの権限プロンプトを排除します。

`SessionEnd` フックは自動登録 — 追加設定不要。

### 4. アンインストール

```
/plugin uninstall honne
/plugin marketplace remove honne
```

`.honne/` ディレクトリはアンインストールで **変更されません** — 資産は保持されます。完全消去したい場合は `bash scripts/purge.sh --all` を手動実行してください。

---

## クイックスタート

インストール後、最速の一通り体験:

```
# Claude Code セッション内、任意のプロジェクトで
/honne:whoami
```

サンプルフロー (簡略化):

```
user   > /honne:whoami

step 1 > スキャン範囲?  ← 矢印キーメニュー (repo / global)
         言語?          ← 矢印キーメニュー (ko / en / jp)
user   > [global, jp を選択]

step 2 > transcripts をスキャン ~/.claude/projects/… → .honne/cache/scan.json
         run_id 自動生成; 機密パターン(12種) + Claude Code メタをマスク

step 3 > 7 軸を自律抽出 [lexicon, reaction, workflow, obsession, ritual, antipattern, signature]
           - axis run → スキャンキャッシュから決定論的シグナル抽出
           - 却下フィルタ適用 (過去の却下と重複する候補は自動スキップ)
           - .honne/assets/claims.jsonl に自律記録 (軸ごとの確認プロンプトなし)

step 4 > LLM ナラティブ合成
           - synthesis_prompt.jp.md をマッチした主張に適用
           - 軸ごとの解説 + 一行評 → .honne/cache/narrative.json

step 5 > ペルソナ + レポートをレンダリング
✓ 保存: .honne/persona.json
✓ 保存: docs/honne.md
✓ append: .honne/assets/claims.jsonl
```

2 回目以降の実行後は、過去のプロファイルと比較できます:

```
/honne:compare
```

ディスク上のものだけを読み込みます — transcript 再スキャンなし、LLM 再分析なし。

## 使い方

### 1. 初回プロフィール生成

```
ユーザー: "私は誰" または /honne:whoami
→ honne が範囲 (repo / global) + 言語 (ko / en / jp) を確認
→ transcripts をスキャン → 7 軸を自律抽出 → 主張を記録
→ LLM が軸ごとの解説 + 一行評を合成
→ .honne/persona.json + docs/honne.md をレンダリング
```

### 2. 単一軸

```
ユーザー: "口癖だけ" または /honne:lexi
→ lexi がトランスクリプトをスキャン → lexicon 軸のみ抽出 → 自律記録
```

### 3. 振り返り (2 回目以降の実行後)

```
ユーザー: "前回と比較" または /honne:compare
→ compare が過去の claim + evolution 資産をロード (read-only)
→ 軸 × 時間バケットでグループ化
→ docs/honne-compare.md をレンダリング (identical / evolved / reversed / new)
```

### 4. データ消去権

```bash
bash scripts/purge.sh --all           # .honne/ を完全削除
bash scripts/purge.sh --keep-assets   # cache のみ削除、経時的資産は保持
```

両コマンドとも確認のため `DELETE` の入力が必要です。ネットワーク関与なし。

## フック (Hooks)

honne はインストール時に単一のフックを自動登録します。追加設定不要。

| イベント | トリガー | 動作 |
|----------|----------|------|
| `SessionEnd` | セッション終了 | `scripts/index-session.sh` を実行 — セッションメタ (id, タイムスタンプ, sha256, メッセージ数) を `.honne/cache/index.json` に append。**LLM 呼び出しなし、コンテキスト注入なし、分析なし。** サイレント失敗。 |

フックは受動的インフラです — transcript インデックスを最新に保ち、その後の `whoami` / `lexi` / `compare` 手動実行を高速化します。分析は常にユーザー主導。

## あなたのデータ

すべてのデータは現在のプロジェクトディレクトリ内の `.honne/` 配下にローカルで保存されます:

| パス | 用途 |
|------|------|
| `.honne/cache/scan.json` | transcript スキャンキャッシュ (一時的、TTL 24h) |
| `.honne/cache/index.json` | SessionEnd フック出力 — メタのみ、メッセージ本文なし |
| `.honne/persona.json` | 現在の 7 軸プロフィールスナップショット |
| `.honne/assets/claims.jsonl` | 自律記録済み主張 (経時履歴) |
| `.honne/assets/rejection.jsonl` | 拒絶主張 (不適合シグナル) |
| `.honne/assets/evolution.jsonl` | 実行間の diff 結果 (identical / evolved / reversed) |

**プライバシー**:
- ネットワーク呼び出しなし。すべての処理はローカルで完結します。
- 機密パターン (API キー, トークン, webhook, メール, 電話番号, ホームパス, IP, クレジットカード — 全 18 パターン) は quote 保存前にマスク処理されます。`scripts/honne_py/redact.py` を参照。
- 資産はセッションコンテキストに **自動注入されません**。ユーザーが `compare` を明示的に呼び出すか、`query-assets.sh` を直接実行したときのみロードされます。
- `CLAUDE.md` への自動注入は恒久的に禁止 (自己強化ループ防止)。

**Export**: `.honne/` は通常のディレクトリです。`tar czf my-honne.tgz .honne/` でどこへでも持ち出せます。あなたのデータ、あなたの管理。

## Worktrees

各 worktree は CWD を基準に独立した `.honne/` ディレクトリを持ちます。ペルソナスナップショットと経時資産は worktree ごとに完全隔離 — 共有状態なし。

```
/project/.honne/                      ← メイン
/project/.claude/worktrees/A/.honne/  ← worktree A (独立)
/other/path/worktree-B/.honne/        ← worktree B (物理的分離)
```

## 誠実利用のお知らせ (Honest-use Notice)

honne は **トランスクリプトに実際に現れたパターン** を浮かび上がらせます。これらのパターンは、特定の文脈で LLM とどう相互作用したかの証拠であって、あなたがどのような人間かについての判断ではありません。拒絶された主張は「あなたが失敗した」ではなく「このフレーミングがこのデータに合わなかった」ことを意味します。antipattern は「あなたが間違っている」ではなく「このようなことが観察された」ことを意味します。

出力のいずれかが苦痛を与えるなら、削除してください — `bash scripts/purge.sh --all`。データはローカルにのみ存在し、ネットワーク呼び出しや解析トラッキングは一切ありません。

**honne は作業パターンの鏡であって、メンタルヘルスツールではありません。** 心の健康に関する懸念がある場合は、資格のある専門家にご相談ください。

## ネーミング

- **honne** (本音) — 公式ペルソナの下にある真の声。日本語起源、*建前* (たてまえ) と対。
- **lexi** — lexicon + i (語彙軸のみ)
- **compare** — 過去と現在を比較する振り返り (transcript 再スキャンなし)

## Triad

honne は 2 つの姉妹プラグインの間に位置します — 独立して動作し、共有成果物でのみ接続:

```
harnish (make)  ──→  honne (know)  ──→  galmuri (keep)
   実行              自己観察             整理・保管
```

- [harnish](https://github.com/jazz1x/harnish) — 自律実装エンジン
- [honne](https://github.com/jazz1x/honne) — 証拠ベースの自己観察 (7 軸ペルソナ)
- [galmuri](https://github.com/jazz1x/galmuri) — コンテキストを集め・整え・保つ (旧 *hanashi*)

## 開発

clone 後に一度だけ pre-commit フックを有効化:

```bash
git config core.hooksPath .githooks
```

フック ([scripts/pre-commit.sh](scripts/pre-commit.sh)) はステージ済みファイルを検証します: shell lint (`shellcheck` または `bash -n` フォールバック)、JSON 構文、`SKILL.md` frontmatter (`name` / `description` / SemVer `version`)、スクリプトの実行権限、`.claude-plugin/marketplace.json` スキーマ (`source: "."` の罠はここで遮断)。

### テストスイート

ハイブリッドテストスイート実行 (Python ヘルパーは pytest、shell/マニフェストは bats):

```bash
bash tests/run.sh
```

初回のみインストール — `brew install bats-core` (macOS) または `apt install bats` (Linux)。すべてのテストは一時的な `HOME` と `CLAUDE_PROJECT_DIR` サンドボックス内で実行され、実際の `~/.claude/` · `~/.honne/` には一切触れません。誤って実 HOME に着地した場合、[tests/setup.bash](tests/setup.bash) のガードが即座に abort します。

## Footnote

> *「判断せずに映す鏡は珍しい。あなたがすでに書いたものだけを映す鏡こそ、もっとも誠実な類だ。」*

honne は作りません — あなたのトランスクリプトがすでに含んでいるものだけを浮かび上がらせます。書いていない言葉を語るなら、作るべき道具を間違えたということです。

## ライセンス

MIT — [LICENSE](./LICENSE) を参照。
