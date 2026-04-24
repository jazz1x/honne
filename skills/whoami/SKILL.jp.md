---
name: whoami
version: 0.0.1
description: >
  ローカルLLMトランスクリプトから6軸の自己観察を編成します。
  自律的な証拠収集 + LLM合成ナラティブ。
  Triggers: "who am I", "self profile", "profile me", "honne", "whoami self".
---

# honne — 6軸自己観察

**呼び出されたら、ステップ1からステップ7まで順番に実行してください。スキルを説明したり、ユーザーが何を望むかを尋ねたりしないでください — 呼び出し自体がリクエストです。ステップ1の質問から始めてください。**

## ステップ1: 範囲 + 言語HITL

`AskUserQuestion`ツールを呼び出して、1回の呼び出しに2つの質問を含めます:

(a) 範囲:
- `question`: "スキャン範囲?"
- `options`: `[{"label":"repo","description":"現在のプロジェクトのみ"},{"label":"global","description":"すべてのプロジェクト"}]`

(b) 言語:
- `question`: "言語?"
- `options`: `[{"label":"ko","description":"한국어"},{"label":"en","description":"English"},{"label":"jp","description":"日本語"}]`

2つの回答から `SCOPE` と `LOCALE` を設定します。プレーンテキストQAを使用しないでください — 矢印キー選択のみ。

## ステップ2: スキャン
実行: `bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" scan --scope "$SCOPE" --cache ".honne/cache/scan.json"`
結果から `RUN_ID` をキャプチャ: `RUN_ID=$(python3 -c 'import json; print(json.load(open(".honne/cache/scan.json"))["run_id"])')`
ゼロ以外の終了 → stdout+stderrをユーザーに正確に出力、停止。終了コードを解釈しないでください。

## ステップ3: 却下の再フレーミングフィルタ (候補をスキップ)
各軸について、`bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" query --base-dir ".honne" --tag "<axis>" --type rejection --scope "$SCOPE"`を実行します。
ステップ4で各軸を記録する前に、候補を `bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" axis validate --text "$candidate" --locale "$LOCALE" --skip-if-overlaps "$rejection_text"` にパイプします — exit 3 = 重複、スキップして「再フレーミング」をログします。すべての変数は大きなダブルクォートで引用する必要があります(空白・特殊文字の安全性)。LLM呼び出しなし。

## ステップ4: 軸ごとの自律的な記録

`axis list` の各軸について:

```bash
AXIS_JSON=$(bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" axis run "$axis" \
  --locale "$LOCALE" --scan .honne/cache/scan.json)

# 根拠が不十分な場合はスキップ
if echo "$AXIS_JSON" | python3 -c "import sys,json; sys.exit(0 if json.load(sys.stdin).get('insufficient_evidence') else 1)"; then
  continue
fi

# 候補と根拠を抽出
CANDIDATE=$(echo "$AXIS_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['candidate_claim'])")
QUOTES_JSON=$(echo "$AXIS_JSON" | python3 -c "import sys,json; print(json.dumps(json.load(sys.stdin)['quotes']))")

# 主張を記録
bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" record claim \
  --type claim --axis "$axis" --scope "$SCOPE" \
  --claim "$CANDIDATE" --run-id "$RUN_ID" \
  --quotes-json "$QUOTES_JSON" \
  --out ".honne/assets/claims.jsonl"
done
```

## ステップ5: LLMナラティブ合成

Claude (あなた自身の精神的推論) を呼び出して、説明と一行評を合成します:

(a) 合成プロンプトを読む: `Read "${CLAUDE_PLUGIN_ROOT}/skills/whoami/templates/synthesis_prompt.${LOCALE}.md"`

(b) マッチした主張を抽出:
```bash
USER_PAYLOAD=$(python3 -c "
import json
claims = [json.loads(l) for l in open('.honne/assets/claims.jsonl') if l.strip()]
matched = [c for c in claims if c.get('run_id')=='${RUN_ID}' and c.get('scope')=='${SCOPE}']
AXES = ['lexicon','reaction','workflow','obsession','ritual','antipattern']
payload = {'locale':'${LOCALE}','claims':{}}
for ax in AXES:
    found = [c for c in matched if c.get('axis')==ax]
    payload['claims'][ax] = {'claim': found[0]['claim'], 'evidence_count': len(found[0].get('quotes', []))} if found else None
print(json.dumps(payload, ensure_ascii=False))
")
```

(c) 合成: 合成プロンプトシステム指示を自身に適用 + USER_PAYLOADをユーザー入力として。STRICT JSON応答を生成。

(d) 結果を保存: JSON応答を `.honne/cache/narrative.json` に `Write` ツールで保存。JSON解析失敗または空の応答の場合、保存をスキップ (narrative.jsonが生成されない)。

## ステップ6: ペルソナとレポートをレンダリング

```bash
NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ)
bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" render persona \
  --claims .honne/assets/claims.jsonl \
  --scope "$SCOPE" --locale "$LOCALE" --run-id "$RUN_ID" --now "$NOW" \
  --narrative .honne/cache/narrative.json \
  --out .honne/persona.json

bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" render report \
  --persona .honne/persona.json --locale "$LOCALE" --out docs/honne.md
```

## 完了
`.honne/persona.json` と `docs/honne.md` に保存されたファイルを報告します。 `/honne:compare` を使用して過去の観察を確認します。

次のアクション提案をユーザーに出力します：

**次のアクション提案**
- このパターンを基に自分の分身（ペルソナ）を実装してみる
- 効率的なトークン使用のための分析ガイド

*(これらの機能はまもなく登場します。)*
