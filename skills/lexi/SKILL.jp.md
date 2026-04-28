---
name: lexi
version: 0.0.3
description: >
  語彙軸スタンドアロン — 高頻度語彙、コード切り替え比率、オノマトペア抽出。
  Triggers: "my vocabulary", "lexicon", "word habits", "speech patterns".
---

# lexi — 語彙軸

スタンドアロン語彙抽出および分析。統合`honne` CLIを使用して結果を提示し、主張を記録します。

## プロセス

1. スコープを要求 (repo/global)。`SCOPE`と`LOCALE`変数を設定。
2. スキャン実行: `bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" scan --base-dir ".honne" --scope "$SCOPE"`
3. 軸抽出実行: `bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" axis run lexicon --scan .honne/cache/scan.json --locale "$LOCALE"`
4. JSON出力を確認 — `candidate_claim`、`quotes`、`insufficient_evidence`フィールドをレビュー
5. HITL: サンプル引用とともに候補主張を提示し、(y/n/edit) を要求
   - **y**: ステップ6へ
   - **n**: 拒否を記録 — `bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" record claim --base-dir ".honne" --type rejection --axis lexicon --scope "$SCOPE" --text "$candidate"`; 完了
   - **edit**: ユーザーが修正テキストを提供、そのテキストを主張として使用
6. 主張を記録: `bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" record claim --base-dir ".honne" --type claim --axis lexicon --scope "$SCOPE" --text "$claim"`
7. 過去の拒否をチェックして再提案を防止: `bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" query --base-dir ".honne" --type rejection --tag lexicon --scope "$SCOPE"`

**進捗モニタリング** — Monitor until-loop使用 (`sleep N && cat`禁止):
```bash
# ✓ Monitor: until [ -f ".honne/cache/.axis_lexicon.json" ]
```

stdout + .honne/assets/claims.jsonlに保存されたレポート
