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
bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" persona check --persona .honne/persona.json
```

- Exit 66 → ユーザーへ通知: "`.honne/persona.json`が見つかりません。まず`/honne:whoami`を実行してペルソナを生成してください。" 停止。
- Exit 0 → 続行。

鮮度確認:

```bash
python3 -c "import json,datetime; d=json.load(open('.honne/persona.json')); ts=datetime.datetime.fromisoformat(d.get('generated_at','2000-01-01T00:00:00Z').replace('Z','+00:00')); print((datetime.datetime.now(datetime.timezone.utc)-ts).days)"
```
stdoutを`STALE_DAYS`としてキャプチャ。

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

`Read "${CLAUDE_PLUGIN_ROOT}/skills/persona/templates/persona_synthesis_prompt.${LOCALE}.md"`

(b) 合成プロンプトのシステム指示を自分自身に適用し、CONFLICT_PAYLOADをユーザー入力として使用します。STRICT JSON応答を生成します:

```json
{
  "conflict_present": true,
  "persona_antipattern": {
    "name": "...",
    "oneliner": "...",
    "system_prompt": "..."
  },
  "persona_signature": {
    "name": "...",
    "oneliner": "...",
    "system_prompt": "..."
  },
  "judge_system_prompt": "..."
}
```

分岐ルール（合成プロンプトテンプレートで適用）:
- `conflict_present = true`: 両軸が存在 → 二つの独立したペルソナ (アンチパターンとシグネチャ) + 審判者を生成。3つのフィールド **必須**。
- `conflict_present = false`、一方がnull: 不在のペルソナをnullに設定。`judge_system_prompt`はnull。
- `conflict_present = false`、両方ともnull: すべてのペルソナフィールドはnull。

制約: 各`system_prompt` ≤ 1000トークン。`judge_system_prompt` ≤ 500トークン。`name` ≤ 12字。`oneliner` ≤ 25語。

(c) 結果を保存: JSONを`{PWD}/.honne/cache/persona-synthesis.json`に`Write`ツールで保存します。JSONのパースに失敗するか応答が空の場合、保存をスキップし、生テキストと警告を出力します。

## ステップ5: ペルソナレンダリング

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/honne" render personas --persona .honne/persona.json --synthesis .honne/cache/persona-synthesis.json --locale "$LOCALE" --out-dir .honne/personas
```

ゼロ以外のexit → 生の合成フィールドを出力し、ファイルレンダリング失敗の警告を表示します。

ユーザーへ出力 — ステップ4(c)で保存した合成JSONの状態に応じてケースを選択します。

**ケースA — `conflict_present=true`** (二つのペルソナ + 審判者):

> ふたつのペルソナが生成されました:
> - `.honne/personas/antipattern.md` — {persona_antipattern.name}
> - `.honne/personas/signature.md` — {persona_signature.name}
> - `.honne/personas/judge.md` — 審判者
>
> ライブ討論を行うには `/honne:crush <テーマ>` を実行してください。

**ケースB — `conflict_present=false`、一方のペルソナのみ non-null**:

> ペルソナが1つだけ生成されました (反対軸が検出されませんでした):
> - `.honne/personas/{slot}.md` — {persona.name}
>
> `/honne:crush` ディベートには両軸が必要です。さらにセッションを収集し `/honne:whoami` を再実行してください。

`{slot}`は non-null ペルソナに応じて `antipattern` または `signature`。

**ケースC — `conflict_present=false`、両方とも null**:

> ペルソナは生成されませんでした (両軸とも検出されず)。セッションを追加収集し `/honne:whoami` を再実行してください。

**重要**: このスキルはファイルを生成するだけです。ペルソナが実行中・適用中・使用中と主張しないでください。ペルソナは独立した成果物です — ユーザーがライブディベートを望むときに `/honne:crush` を呼び出します。
