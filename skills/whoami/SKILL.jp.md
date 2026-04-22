---
name: whoami
version: 0.0.1
description: >
  ローカルLLMトランスクリプトから6軸自己観察をオーケストレートします。
  証拠に基づくペルソナと軸ごとのHITL承認。
  Triggers: "who am I", "self profile", "profile me", "honne", "whoami self".
---

# honne — 6軸自己観察

## ステップ1: スコープHITL

ユーザーに問い合わせます: "スキャンスコープ — `repo` (現在のプロジェクト) または `global` (すべてのプロジェクト)?"

明示的な `repo` または `global` を待ちます。曖昧な回答 → 再度質問します。

## ステップ2: トランスクリプトスキャン

実行します:
```bash
HONNE_ROOT="${CLAUDE_PLUGIN_ROOT}"
bash "$HONNE_ROOT/scripts/scan-transcripts.sh" \
  --scope "$SCOPE" --since "2020-01-01" \
  --cache ".honne/cache/scan.json" \
  --index-ref ".honne/cache/index.json" \
  --redact-secrets
```

exit 2 (トランスクリプトなし) の場合 → "十分なデータがありません。スコープを変更しますか?" を報告 → 終了します。

## ステップ3: HITL前の拒否リフレーム フィルター

各軸について:
```bash
bash "$HONNE_ROOT/scripts/query-assets.sh" \
  --tag "<axis>" --type rejection --scope "$SCOPE" --out stdout
```

過去の拒否をメモリに格納します (注入されません)。HITL主張を提示する前に「スキップ候補」フィルターとして使用します。候補主張テキストが過去の拒否と大きく重なる場合は、リフレーム またはログとともにスキップします。

## ステップ4: 軸ごとの処理

[語彙、反応、ワークフロー、執着、儀式、アンチパターン] の各軸に対して:
- 統計抽出 (語彙 → extract-lexicon.sh; 執着 → detect-recurrence.sh; その他 → このスキル内の内部ロジック)
- LLM要約 (evidence-gather出力への参照が必須)
- HITL: 引用付きで主張を提示し、(y / n / 編集) を尋ねます。曖昧 → 再度質問します。
- y → record-claim.sh --type claim ...
- n → record-claim.sh --type rejection ...
- edit → 編集されたテキストを使用、record-claim.sh --type claim ...

## ステップ5: .honne/persona.json を保存

architecture PRD §3.2スキーマ。承認された軸のみ。

## ステップ6: docs/honne.md をレンダリング

人間が読める報告書。すべての主張には ≥ 1個の引用が必要または [insufficient evidence] でマークされている必要があります。

禁止フレーズ (ホロスコープ): "at times", "sometimes", "in certain situations", "때로는", "상황에 따라", "적절히".

## ステップ7: 進化リンク (2回目以降の実行)

.honne/assets/claim.jsonlにこの実行前のエントリがある場合:
- query-assets.sh --tag <axis> --type claim --scope "$SCOPE" --until <this-run-ts>
- LLM ペア分類器: {past_claim, present_claim} → label ∈ {identical, evolved, reversed, unrelated} with confidence
- confidence < 0.7 → unrelated
- identical → 現在の主張資産にprior_idを設定、新しい進化なし
- evolved / reversed → record-claim.sh --type evolution --prior-id <past> ...

## 完了

保存されたファイルを報告 + ユーザーに注記: "/honne:compare to review past."

## LLM Prompt Templates

### Pair classifier (Step 7)

When comparing past vs present claim within same axis:

```
System: You classify the relationship between two evidence-backed claims about the same user on the same axis.

Input:
  Axis: {axis}
  Past claim (recorded {past_ts}): "{past_claim}"
  Present claim (recorded {present_ts}): "{present_claim}"

Labels:
  - identical: same observation, different wording
  - evolved:   same axis, concrete content changed (vocabulary substitution OR frequency shift OR scope expansion)
  - reversed:  present observation contradicts past observation
  - unrelated: observations about different phenomena

Respond with JSON only:
  { "label": "<one-of-four>", "confidence": <0.0-1.0>, "rationale": "<one short sentence>" }

Rule: if confidence < 0.7, force label = "unrelated".
```

### Rejection overlap detector (Step 3)

When deciding whether to skip a candidate claim due to past rejection:

```
System: Decide whether the present candidate claim overlaps semantically with a past rejected claim (same user, same axis).

Input:
  Axis: {axis}
  Past rejection (recorded {past_ts}): "{past_rejection}"
  Present candidate: "{present_candidate}"

Respond with JSON only:
  { "overlap": true | false, "confidence": <0.0-1.0>, "rationale": "<one short sentence>" }

Rule: overlap=true only if confidence >= 0.7. Otherwise proceed with the present candidate as-is.
```

### Horoscope guard (Step 6)

Before writing a claim into docs/honne.md, self-check:

```
System: Does the following claim contain any horoscope-style hedge? (vague time qualifiers, vague universals, phrases like "sometimes", "at times", "generally", "in certain situations", or Korean "때로는"/"상황에 따라"/"적절히", or Japanese "時に"/"場合によって")

Input: "{claim_text}"

Respond JSON only:
  { "horoscope": true | false, "matched_phrase": "<str or empty>" }

If horoscope=true, the claim is rejected and the axis item is marked [insufficient evidence].
```
