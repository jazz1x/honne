---
name: whoami
version: 0.0.5
description: >
  ローカルLLMトランスクリプトから7軸の自己観察を編成します。
  自律的な証拠収集 + LLM合成ナラティブ。
  Triggers: "who am I", "self profile", "profile me", "honne whoami", "whoami self".
ssl:
  scheduling:
    anti_triggers:
      - "`.honne/persona.json` がすでに新鮮で新しい transcript がないとき (compare を使用)"
      - "単一 axis のみ必要な場合 (lexi を使用)"
  structural:
    scenes:
      - "Step 1: 範囲+言語 HITL"
      - "Step 2: スキャン"
      - "Step 3: 却下再フレーミングフィルタ"
      - "Step 4: 軸ごとの自律的な記録"
      - "Step 5: LLMナラティブ合成"
      - "Step 6: ペルソナとレポートのレンダリング"
    branches:
      - "Step 2: scan exit non-zero → stdout+stderr をそのまま出力後に停止"
      - "Step 3: validate exit 3 (overlap) → 軸 skip + 'reframed' ログ"
      - "Step 4: insufficient_evidence true → 軸 skip、次へ進行"
      - "ユーザーが候補に 'n' で応答 → 拒否を記録"
    resumable: true
  logical:
    tools: ["AskUserQuestion", "bash", "python3", "Read", "Write"]
    side_effects:
      reads:
        - ".honne/cache/scan.json"
        - ".honne/cache/axis-${axis}.json"
      writes:
        - ".honne/cache/scan.json  # overwrite"
        - ".honne/cache/axis-${axis}.json  # overwrite"
        - ".honne/assets/claims.jsonl  # append"
        - ".honne/assets/rejections.jsonl  # append"
        - ".honne/cache/narrative.json  # overwrite"
        - ".honne/persona.json  # overwrite"
        - "docs/honne.md  # overwrite"
      deletes: []
      network: []
    idempotent: false
    rollback: ".honne/assets/*.jsonl の最後の RUN_ID 行を jq/grep で手動削除。.honne/ と docs/honne.md は .gitignore 対象のため git checkout 不可 — 実行前に cp -r .honne .honne.bak 推奨。"
---

# honne — 7軸自己観察

**呼び出されたら、ステップ1からステップ6まで順番に実行してください。スキルを説明したり、ユーザーが何を望むかを尋ねたりしないでください — 呼び出し自体がリクエストです。ステップ1の質問から始めてください。**

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

**却下の記録**: ユーザーが候補主張を明示的に「n」で拒否した場合、ステップ3フィルターで将来使用できるよう却下として記録します:
```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" record claim \
  --type rejection --axis "$axis" --scope "$SCOPE" \
  --claim "$CANDIDATE" --run-id "$RUN_ID" \
  --out ".honne/assets/rejections.jsonl"
```

<!-- TODO(evolutions): evolutions.jsonlのクロスラン差分追跡はまだ実装されていません。query --type evolutionは常に[]を返します。構造的変更が必要です。 -->

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

**強制ルール** — 実行制約 (テストスイートが強制):
- 各 `bash` ブロックは直接シェルコマンドとして実行 — heredoc (`<< 'EOF'`)・スクリプトファイル・コマンドバンドリング禁止。
- 中間データを `/tmp` に書き込まない — `.honne/cache/` を使用。`/tmp` への書き込みは SKILL.md 契約違反。

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

**次のアクション**
- `/honne:persona` — このプロファイルから2つのペルソナ（antipattern × signature）を生成
- `/honne:crush <トピック>` — 2つのペルソナ間のライブディベート
