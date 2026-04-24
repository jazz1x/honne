---
name: setup
version: 0.0.2
description: >
  honne権限のための一回限りのallowedTools登録。
  Triggers: "setup honne", "configure permissions", "allowedTools", "/honne:setup".
---

# honne — 権限設定

**呼び出されたら、ステップ1とステップ2を順番に実行してください。説明したり、明確化を求めたりしないでください — 呼び出し自体がリクエストです。**

## ステップ1: プラグインルートを解決し allowedTools フラグメントを出力

実際のプラグインインストールパスを解決してフラグメントを出力するには、次の bash ブロックを実行します:

```bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT}"
cat <<EOF
次のエントリを ~/.claude/settings.json の "allowedTools" 配列に追加してください:

  "Bash(bash ${PLUGIN_ROOT}/scripts/honne *)",
  "Bash(bash \"${PLUGIN_ROOT}/scripts/honne\" *)",
  "Bash(python3 -c *)",
  "Bash(python3 ${PLUGIN_ROOT}/*)",
  "Write(.honne/**)"

allowedTools がまだない場合は、トップレベル配列として作成してください。
追加後、/honne:setup を再度実行して確認してください。
EOF
```

ユーザーへの注意:
- 2つの `Bash(bash ...)` エントリは honne スクリプトの引用符ありと引用符なし両方の呼び出しをカバーします (SKILL.md は引用符版を使用)。
- `Write(.honne/**)` は cache/assets 出力時のファイル書き込みプロンプト(`>` リダイレクト含む)を抑制します。

## ステップ2: 現在の構成を確認

現在の設定を検査するために次のコマンドを実行します:

```bash
python3 -c "
import json, os
p = os.path.expanduser('~/.claude/settings.json')
if not os.path.exists(p):
    print('settings.json not found')
    exit(1)
d = json.load(open(p))
tools = d.get('allowedTools', [])
honne = [t for t in tools if 'honne' in t or '.honne' in t]
print(f'honne entries: {len(honne)}')
for t in honne:
    print(' ', t)
"
```

結果の解釈:
- **0項目**: "まだ設定されていません。上のフラグメントをallowedToolsに貼り付けてください。"
- **≥1項目**: "設定済み。{N}個のhonneエントリが登録されています。"

**注**: このスキルは構成指示のみを出力します — `~/.claude/settings.json` に書き込みません。すべての変更はあなたが制御します。
