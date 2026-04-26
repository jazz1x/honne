---
name: lexi
version: 0.0.2
description: >
  語彙軸スタンドアロン — 高頻度語彙、コード切り替え比率、オノマトペア抽出。
  Triggers: "my vocabulary", "lexicon", "word habits", "speech patterns".
---

# lexi — 語彙軸

スタンドアロン語彙抽出および分析。extract-lexicon.shを実行し、結果を提示し、軸ごとの主張を記録します。

## プロセス

1. スコープを要求 (repo/global)
2. scan-transcripts.shを実行
3. extract-lexicon.sh --input .honne/cache/scan.json --top 50 --min-sessions 2 を実行
4. LLMがevidence-gather.sh引用で上位用語を要約
5. HITL: サンプルとともに主張を提示し、(y/n/edit) を要求
6. 主張/拒否資産として記録
7. 過去の拒否をチェックして再提案を防止

**進捗モニタリング** — Monitor until-loop使用 (`sleep N && cat`禁止):
```bash
# ✓ Monitor: until [ -f ".honne/cache/lexicon.json" ]
```

stdout + .honne/assets/claim.jsonlに保存されたレポート
