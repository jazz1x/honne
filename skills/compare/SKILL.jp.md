---
name: compare
version: 0.0.4
description: >
  資産のみの振り返り。トランスクリプト再スキャン、LLM再分析、HITL なし。
  Triggers: "compare", "review past", "what changed", "self retrospective".
ssl:
  scheduling:
    anti_triggers:
      - ".honne/assets/ が未生成または空のとき (whoami を先に実行)"
  structural:
    scenes:
      - "Step 1: スコープ HITL"
      - "Step 2: 資産の存在確認"
      - "Step 3: 主張+進化のロード"
      - "Step 4: 時間バケットグループ化"
      - "Step 5: docs/honne-compare.md レンダリング"
      - "Step 6: 資産不変性チェック"
    branches:
      - "Step 2: 資産ディレクトリ不在/空 → 'No assets yet' 出力 + exit 0"
      - "Step 5: ユーザーが「summarize」要求 → 引用限定 LLM パス (それ以外は純粋レンダ)"
    resumable: false
  logical:
    tools: ["bash"]
    side_effects:
      reads:
        - ".honne/assets/*.jsonl"
      writes:
        - "docs/honne-compare.md  # overwrite"
      deletes: []
      network: []
    idempotent: false  # summarize 分岐で非決定的 LLM 呼び出し
    rollback: "docs/honne-compare.md は .gitignore 対象 — 実行前に cp バックアップまたは出力検証後に手動削除。"
---

# compare — 読み取り専用振り返り

## ステップ1: スコープHITL (ワンショット)

聞きます: "振り返りスコープ — `repo` または `global`?"

## ステップ2: 資産の存在確認

.honne/assets/ が存在しないまたは空の場合:
  "No assets yet. Run honne first." を出力してexit 0 します。

## ステップ3: 主張 + 進化をロード

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/query-assets.sh" \
  --tag "<axis>" --scope "$SCOPE" --type claim --out stdout
```

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/query-assets.sh" \
  --type evolution --scope "$SCOPE" --out stdout
```

**非同期待機パターン** — Monitor until-loop使用、`sleep N && cat`禁止:
```bash
# ✓ Monitor: until [ -f ".honne/assets/claim.jsonl" ]
```

## ステップ4: 時間バケットグループ化

軸 × recorded_at バケットでグループ化 (MVPの場合はYYYY-MM粒度)。

## ステップ5: docs/honne-compare.md をレンダリング (+ stdout)

architecture PRD §4.2 compare Step 6 に従ってフォーマットします。
ユーザーが「要約」を要求しない限り LLM なし — その場合でも引用制限のみ。

## ステップ6: 資産不変性チェック

このスキルは .honne/assets/ または .honne/persona.json に決して書き込むことはできません。
検証 (テスト): assets/*.jsonl の stat -c %Y before/after 変更なし。
