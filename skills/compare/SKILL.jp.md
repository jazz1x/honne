---
name: compare
version: 0.0.1
description: >
  資産のみの振り返り。トランスクリプト再スキャン、LLM再分析、HITL なし。
  Triggers: "compare", "review past", "what changed", "self retrospective".
---

# compare — 読み取り専用振り返り

## ステップ1: スコープHITL (ワンショット)

聞きます: "振り返りスコープ — `repo` または `global`?"

## ステップ2: 資産の存在確認

.honne/assets/ が存在しないまたは空の場合:
  "No assets yet. Run honne first." を出力してexit 0 します。

## ステップ3: 主張 + 進化をロード

```bash
HONNE_ROOT="${CLAUDE_PLUGIN_ROOT}"
bash "$HONNE_ROOT/scripts/query-assets.sh" \
  --tag "<axis>" --scope "$SCOPE" --type claim --out stdout
bash "$HONNE_ROOT/scripts/query-assets.sh" \
  --type evolution --scope "$SCOPE" --out stdout
```

## ステップ4: 時間バケットグループ化

軸 × recorded_at バケットでグループ化 (MVPの場合はYYYY-MM粒度)。

## ステップ5: docs/honne-compare.md をレンダリング (+ stdout)

architecture PRD §4.2 compare Step 6 に従ってフォーマットします。
ユーザーが「要約」を要求しない限り LLM なし — その場合でも引用制限のみ。

## ステップ6: 書き込みなし

このスキルは .honne/assets/ または .honne/persona.json に決して書き込むことはできません。
検証 (テスト): assets/*.jsonl の stat -c %Y before/after 変更なし。
