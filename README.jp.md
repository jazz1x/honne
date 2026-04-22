# honne

> Claude Code プラグイン — LLM トランスクリプトからの自己観察

**honne** (本音) — あなたが LLM と実際にどう働いているかを、ローカルで証拠に基づいて映し出す鏡です。公式なペルソナ(*建前*)の下で、トランスクリプトが静かに記録していたもの — 繰り返される語彙、拒絶した提案、セッションの儀式、自分でも名付けたことのないパターン — を浮かび上がらせます。

[English](./README.md) · [한국어](./README.ko.md)

## 前提条件 (Prerequisites)

honne は `jq` と、`python3` または `ripgrep` のいずれかが必要です。使用前にインストールしてください:

```bash
# macOS — python3 はプリインストール済み
brew install jq
# (任意) brew install ripgrep

# Linux (apt) — python3 は多くのディストリで標準
sudo apt install jq
# (任意) sudo apt install ripgrep
```

確認: `command -v jq && { command -v python3 || command -v rg; }`. どちらもない場合、スクリプトは exit code 4 で終了します。

**バックエンド選択**: スクリプトは `python3` を優先的に自動検出します (ネイティブの Unicode トークナイズ + シングルパスのリダクションで高速)。なければ `ripgrep` へフォールバック。設定不要。

## インストール

### 1. マーケットプレイスを登録

Claude Code 内でこのリポジトリをプラグインマーケットプレイスとして登録:

```
/plugin marketplace add https://github.com/jazz1x/honne.git
```

成功時 `Marketplace "honne" added` が出力されます。

### 2. プラグインをインストール

```
/plugin install honne --scope user
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

`honne` がアクティブプラグインとして表示されていれば OK。`SessionEnd` フックは自動登録 — 追加設定不要。

### 4. 初回実行

```
/honne:honne
```

メインオーケストレーターに入ります。初回はスキャン範囲（現在の repo / グローバル）を尋ね、6 軸を HITL で巡回します。全体の流れは [使い方](#使い方) を参照。

## スキル

| スキル | コマンド | Alias | 役割 |
|--------|----------|-------|------|
| **honne** | `/honne:honne` | `/honne:me` | メインオーケストレーター。6 軸ペルソナ + 軸ごとの HITL 承認。 |
| **lexi** | `/honne:lexi` | `/honne:lex` | 語彙 (Lexicon) 軸のみ (高頻度語彙、コードスイッチング比率、擬音語・擬態語)。 |
| **compare** | `/honne:compare` | `/honne:back` | 読み取り専用の振り返り。蓄積された資産を読み、経時的な変化を提示。transcript 再スキャン / LLM 再分析なし。 |

各スキルは `honne:` 名前空間の後ろに自然に続く短い alias を 1 つだけ公開します — `/honne:me`, `/honne:lex`, `/honne:back`。本体名も alias も同じ本体スキルへ redirect。

各スキルは独立した軌道で動作し、**ファイルベースの共有成果物** (`.honne/cache/`, `.honne/persona.json`, `.honne/assets/*.jsonl`) でのみ接続されます。

```
 トランスクリプト (~/.claude/projects/**/*.jsonl)
      │
      │  honne  ──→  persona.json + docs/honne.md  (6 軸スナップショット)
      │                  │
      │                  ├── record-claim.sh  ──→  .honne/assets/*.jsonl (経時的蓄積)
      │                  │
      │  lexi   ──→  persona.json (軸 1 のみ)
      │
 SessionEnd フック ──→  .honne/cache/index.json  (メタデータのみ、受動的インデックス)
                              │
 compare (読み取り専用) ──→  query-assets.sh  ──→  docs/honne-compare.md  (過去主張の diff)
```

## 使い方

### 1. 初回プロフィール生成

```
ユーザー: "私は誰" または /honne:honne
→ honne が範囲を確認: repo / global?
→ transcripts をスキャン → 6 軸を抽出 → 軸ごとに HITL (y / n / edit)
→ .honne/persona.json + docs/honne.md を生成
→ 承認された主張は .honne/assets/claim.jsonl に資産として記録
```

### 2. 単一軸

```
ユーザー: "口癖だけ" または /honne:lexi
→ lexi が transcripts をスキャン → lexicon 軸のみ → HITL
→ lexicon 軸の claim/rejection 資産を記録
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

フックは受動的インフラです — transcript インデックスを最新に保ち、その後の `honne` / `lexi` / `compare` 手動実行を高速化します。分析は常にユーザー主導。

## あなたのデータ

すべてのデータは現在のプロジェクトディレクトリ内の `.honne/` 配下にローカルで保存されます:

| パス | 用途 |
|------|------|
| `.honne/cache/scan.json` | transcript スキャンキャッシュ (一時的、TTL 24h) |
| `.honne/cache/index.json` | SessionEnd フック出力 — メタのみ、メッセージ本文なし |
| `.honne/persona.json` | 現在の 6 軸プロフィールスナップショット |
| `.honne/assets/claim.jsonl` | HITL 承認済み主張 (経時履歴) |
| `.honne/assets/rejection.jsonl` | HITL 拒絶主張 (不適合シグナル) |
| `.honne/assets/evolution.jsonl` | 実行間の diff 結果 (identical / evolved / reversed) |

**プライバシー**:
- ネットワーク呼び出しなし。すべての処理はローカルで完結します。
- 機密パターン (API キー, トークン, webhook, メール, 電話番号, ホームパス, IP, クレジットカード — 全 12 パターン) は quote 保存前にマスク処理されます。`scripts/scan-transcripts.sh` §redact-secrets を参照。
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
- **me** — `honne` の alias。名前空間の後ろに続いて「honne me」と読める。
- **lex** — `lexi` の alias。「honne lex」— lexicon の短縮形。
- **back** — `compare` の alias。「honne back」— 過去の実行を振り返る。

## Triad

honne は 3 プラグインからなる軌道のひとつです:

- [harnish](https://github.com/jazz1x/harnish) — 自律実装エンジン (*作る*)
- [honne](https://github.com/jazz1x/honne) — transcripts からの自己観察 (*知る*)
- [galmuri](https://github.com/jazz1x/galmuri) — コンテキストを集め・整え・保つ (*保つ*)

## 開発

clone 後に一度だけ pre-commit フックを有効化:

```bash
git config core.hooksPath .githooks
```

フック ([scripts/pre-commit.sh](scripts/pre-commit.sh)) はステージ済みファイルを検証します: shell lint (`shellcheck` または `bash -n` フォールバック)、JSON 構文、`SKILL.md` frontmatter (`name` / `description` / SemVer `version`)、スクリプトの実行権限、`.claude-plugin/marketplace.json` スキーマ (`source: "."` の罠はここで遮断)。

## ライセンス

MIT
