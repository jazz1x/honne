---
name: whoami
version: 0.0.2
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

`axis list` の各軸について、各コマンドを個別に実行します — スクリプトファイルにバンドルしたり、heredocを使用したりしないでください:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" axis run "$axis" \
  --locale "$LOCALE" --scan .honne/cache/scan.json > ".honne/cache/axis-${axis}.json"
```

```bash
python3 -c "import json,sys; d=json.load(open('.honne/cache/axis-${axis}.json')); sys.exit(0 if d.get('insufficient_evidence') else 1)"
```
終了 0 の場合 → この軸をスキップ (根拠不足)、次へ進む。

```bash
python3 -c "import json; print(json.load(open('.honne/cache/axis-${axis}.json'))['candidate_claim'])"
```
stdoutを`CANDIDATE`としてキャプチャ。

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" record claim \
  --type claim --axis "$axis" --scope "$SCOPE" \
  --claim "$CANDIDATE" --run-id "$RUN_ID" \
  --quotes-file ".honne/cache/axis-${axis}.json" \
  --out ".honne/assets/claims.jsonl"
```

**強制ルール**: `/tmp` に中間データを書き込まないでください。`/tmp` に書き込みたい衝動に駆られた場合は、代わりに `.honne/cache/` を使用してください。`/tmp` への書き込みは SKILL.md 契約違反です — テストスイートがこれをキャッチします。

**重要**: 各 `bash` ブロックを直接シェルコマンドとして実行します。`/tmp` に書き込まないでください、シェル heredoc (`<< 'EOF'`) を使用しないでください、コマンドをスクリプトファイルにバンドルしないでください。インラインコマンドのみを実行してください。

## ステップ5: LLMナラティブ合成

Claude (あなた自身の精神的推論) を呼び出して、説明と一行評を合成します:

(a) 合成プロンプトを読む: `Read "${CLAUDE_PLUGIN_ROOT}/skills/whoami/templates/synthesis_prompt.${LOCALE}.md"`

(b) ステップ4で記録した主張からUSER_PAYLOADを構築します。メモリ内のAXIS_JSON出力を使用し、ファイルを再読み込みせずに直接JSONオブジェクトとして構成します:

```
USER_PAYLOAD = {
  "locale": "<LOCALE>",
  "claims": {
    "<axis>": {"claim": "<CANDIDATE>", "evidence_count": <len(quotes)>} for each recorded axis,
    "<skipped_axis>": null for each axis that had insufficient evidence
  }
}
```

`python3 << 'PYEOF'` やheredocを使用しないでください。ステップ4で既知の出力から精神的コンテキストで組み立てます。

(c) 合成: 合成プロンプトシステム指示を自身に適用 + USER_PAYLOADをユーザー入力として。STRICT JSON応答を生成。

(d) 絶対パスを最初に解決します:
```bash
python3 -c "import os; print(os.path.join(os.getcwd(), '.honne/cache/narrative.json'))"
```
stdoutを`NARRATIVE_PATH`としてキャプチャ。その後: JSON応答を解決されたパスに `Write` ツールで保存します。JSON解析失敗または空の応答の場合、保存をスキップ。

## ステップ6: ペルソナとレポートをレンダリング

```bash
date -u +%Y-%m-%dT%H:%M:%SZ
```
stdoutを`NOW`としてキャプチャ。

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" render persona \
  --claims .honne/assets/claims.jsonl \
  --scope "$SCOPE" --locale "$LOCALE" --run-id "$RUN_ID" --now "$NOW" \
  --narrative .honne/cache/narrative.json \
  --out .honne/persona.json
```

```bash
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
