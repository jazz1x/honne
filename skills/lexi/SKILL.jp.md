---
name: lexi
version: 0.0.4
description: >
  語彙軸スタンドアロン — 高頻度語彙、コード切り替え比率、オノマトペア抽出。
  Triggers: "my vocabulary", "lexicon", "word habits", "speech patterns".
ssl:
  scheduling:
    anti_triggers:
      - "完全な 7-axis 分析が必要な場合 (whoami を使用)"
  structural:
    scenes:
      - "Step 1: HITL (スコープ + 言語)"
      - "Step 2: スキャン"
      - "Step 3: 軸抽出"
      - "Step 4: JSON レビュー"
      - "Step 5: HITL 受諾/拒否/編集"
      - "Step 6: 主張記録"
      - "Step 7: 過去の拒否確認"
    branches:
      - "Step 5: y → Step 6 主張記録"
      - "Step 5: n → 拒否記録後に終了"
      - "Step 5: edit → ユーザー修正テキスト → Step 6 主張記録"
    resumable: false
  logical:
    tools: ["bash"]
    side_effects:
      reads:
        - ".honne/cache/scan.json"
      writes:
        - ".honne/assets/claims.jsonl  # append"
      deletes: []
      network: []
    idempotent: false
    rollback: ".honne/assets/claims.jsonl の最後の lexicon 行を手動削除。"
---

# lexi — 語彙軸

スタンドアロン語彙抽出および分析。統合`honne` CLIを使用して結果を提示し、主張を記録します。

## Step 1: HITL (スコープ + 言語)

スコープ(repo/global)と**言語**(ko/en/jp)の両方を要求します。返答から `SCOPE` と `LOCALE` 変数を設定します。

## Step 2: スキャン

`bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" scan --base-dir ".honne" --scope "$SCOPE"`

## Step 3: 軸抽出

`bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" axis run lexicon --scan .honne/cache/scan.json --locale "$LOCALE"`

## Step 4: JSON レビュー

JSON出力を確認 — `candidate_claim`、`quotes`、`insufficient_evidence` フィールドをレビューします。

## Step 5: HITL 受諾/拒否/編集

サンプル引用とともに候補主張を提示し、(y/n/edit) を要求:
- **y**: Step 6 へ
- **n**: 拒否を記録 — `bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" record claim --base-dir ".honne" --type rejection --axis lexicon --scope "$SCOPE" --text "$candidate"`; 完了
- **edit**: ユーザーが修正テキストを提供、そのテキストを主張として使用

## Step 6: 主張記録

`bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" record claim --base-dir ".honne" --type claim --axis lexicon --scope "$SCOPE" --text "$claim"`

## Step 7: 過去の拒否確認

再提案を防止するため: `bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" query --base-dir ".honne" --type rejection --tag lexicon --scope "$SCOPE"`

**進捗モニタリング** — Monitor until-loop使用 (`sleep N && cat`禁止):
```bash
# ✓ Monitor: until [ -f ".honne/cache/.axis_lexicon.json" ]
```

stdout + .honne/assets/claims.jsonlに保存されたレポート
