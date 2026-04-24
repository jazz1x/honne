---
name: persona
version: 0.0.2
description: >
  アンチパターン × シグネチャ軸の葛藤合成。
  観測されたパターンから機能するペルソナプロンプトを生成します。
  Triggers: "persona", "activate persona", "who am I as Claude", "honne persona".
---

# honne — ペルソナ合成

**呼び出されたら、ステップ1からステップ5まで順番に実行してください。スキルを説明したり、ユーザーが何を望むかを尋ねたりしないでください — 呼び出し自体がリクエストです。ステップ1の質問から始めてください。**

## ステップ1: 言語HITL

`AskUserQuestion`ツールを呼び出します:

- `question`: "言語?"
- `options`: `[{"label":"ko","description":"한국어"},{"label":"en","description":"English"},{"label":"jp","description":"日本語"}]`

返答から`LOCALE`を設定します。プレーンテキストのQ&Aは使用しないでください — 矢印キー選択のみ。

## ステップ2: ロードと検証

persona.jsonの存在確認:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" render persona-prompt --check-only --persona .honne/persona.json --locale "$LOCALE"
```

- Exit 66 → ユーザーへ通知: "`.honne/persona.json`が見つかりません。まず`/honne:whoami`を実行してペルソナを生成してください。" 停止。
- Exit 0 → 続行。

鮮度確認:

```bash
STALE_DAYS=$(python3 -c "import json,datetime; d=json.load(open('.honne/persona.json')); ts=datetime.datetime.fromisoformat(d.get('generated_at','2000-01-01T00:00:00Z').replace('Z','+00:00')); print((datetime.datetime.now(datetime.timezone.utc)-ts).days)")
```

`STALE_DAYS`が7を超える場合（`HONNE_PERSONA_STALE_DAYS`環境変数で上書き可能）: "persona.jsonは{STALE_DAYS}日前に最後に更新されました。`/honne:whoami`の再実行を検討してください。"と警告します。その後続行。

## ステップ3: 葛藤ペイロード構築

`.honne/persona.json`をメンタルコンテキストで読み取ります。ファイル書き込みやheredocを使わずにCONFLICT_PAYLOADをJSONオブジェクトとして構築します:

```
CONFLICT_PAYLOAD = {
  "locale": "<LOCALE>",
  "antipattern": {
    "claim": "<axes.antipattern.claim>",
    "explanation": "<axes.antipattern.explanation>",
    "evidence_strength": <axes.antipattern.evidence_strength>
  }  — antipattern軸が存在しないかclaimがnullの場合はnull,
  "signature": {
    "claim": "<axes.signature.claim>",
    "explanation": "<axes.signature.explanation>",
    "evidence_strength": <axes.signature.evidence_strength>
  }  — signature軸が存在しないかclaimがnullの場合はnull,
  "supporting_axes": {
    "<axis>": {"claim": "...", "explanation": "...", "evidence_strength": <val>}
    残り5つの各軸: lexicon, reaction, workflow, obsession, ritual
  }
}
```

`python3 << 'EOF'`またはheredocは使用しないでください。読み取ったpersona.jsonデータからメンタルコンテキストでペイロードを組み立てます。

## ステップ4: LLM合成

(a) 合成プロンプトを読む:

```bash
Read "${CLAUDE_PLUGIN_ROOT}/skills/persona/templates/persona_synthesis_prompt.${LOCALE}.md"
```

(b) 合成プロンプトのシステム指示を自分自身に適用し、CONFLICT_PAYLOADをユーザー入力として使用します。STRICT JSON応答を生成します:

```json
{
  "verdict": "...",
  "character_oneliner": "...",
  "system_prompt": "...",
  "conflict_present": true,
  "debate": {
    "antipattern_voice": "...",
    "signature_voice": "...",
    "resolution": "..."
  }
}
```

`conflict_present = true` の場合、`debate` フィールドは **必須** です (antipattern 側 / signature 側 / 判決の 3 者討論)。

分岐ルール（合成プロンプトテンプレートで適用）:
- `conflict_present = true`: 両軸が存在 → アンチパターン対シグネチャの緊張をフレーミング → verdict + 解決
- `conflict_present = false`、一方がnull: 支配的な特性のポートレート、存在しない側を「未観測」として表示
- `conflict_present = false`、両方ともnull: サポーティング5軸のみでポートレート、葛藤フレーミングなし

制約: `system_prompt` ≤ 1500トークン。`character_oneliner` ≤ 20語。

(c) 結果を保存: JSONを`{PWD}/.honne/cache/persona-synthesis.json`に`Write`ツールで保存します。JSONのパースに失敗するか応答が空の場合、保存をスキップし、生テキストと警告を出力します。

## ステップ5: レンダリングと活性化

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" render persona-prompt --persona .honne/persona.json --synthesis .honne/cache/persona-synthesis.json --locale "$LOCALE" --out .honne/persona-prompt.md
```

ゼロ以外のexit → 生の合成フィールドを出力し、ファイルレンダリング失敗の警告を表示します。

ユーザーへ出力します:

**キャラクター**: `character_oneliner`

**判定**: `verdict`

**内なる衝突** (`conflict_present = true` の場合のみ):
- **antipattern 側**: `debate.antipattern_voice`
- **signature 側**: `debate.signature_voice`
- **判決**: `debate.resolution`

**ペルソナシステムプロンプト**:

```
[system_prompt]
```

ユーザーへ通知します: "このペルソナは現在のセッションでアクティブです。システムプロンプト + アクティベーション指示は `.honne/persona-prompt.md` に保存されました — 将来のセッションや他の LLM で復元するには貼り付けてください。"

その後、出力の最後の行として、アクティベーション指示を自己に適用し次のように宣言します:

> **このメッセージ以降、「ペルソナ解除」または "reset persona" と言われるまで、上記の人物として応答します。**

**重要**: CLAUDE.md には書き込まないでください。ペルソナの活性化はセッション内でのみ — (1) `.honne/persona-prompt.md` にレンダリングされた activation_directive セクション (コンテキストに露出) + (2) 上の最終自己宣言で達成されます。このスキルが終了した後、同じセッションの以降のターンではペルソナを体現してください。
