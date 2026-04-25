---
name: setup
version: 0.0.2
description: >
  honne権限のための一回限りのallowedTools登録。
  Triggers: "setup honne", "configure permissions", "allowedTools", "/honne:setup".
---

# honne — 権限設定

**呼び出されたら、ステップ1からステップ3まで順番に実行してください。説明したり、明確化を求めたりしないでください — 呼び出し自体がリクエストです。**

## ステップ1: 現在の状態を検出

```bash
python3 -c "
import json, os, sys
paths = [
    os.path.expanduser('~/.claude/settings.json'),
    os.path.expanduser('~/.claude/projects/' + os.getcwd().replace('/', '-') + '/settings.json'),
]
for p in paths:
    if os.path.exists(p):
        d = json.load(open(p))
        tools = d.get('allowedTools', [])
        honne = [t for t in tools if 'honne' in t or '.honne' in t]
        print(f'{p}: {len(honne)} honneエントリ')
        for t in honne:
            print(f'  {t}')
    else:
        print(f'{p}: なし')
"
```

## ステップ2: allowedToolsフラグメントを生成

```bash
python3 -c "
import json
entries = [
    'Bash(bash */scripts/honne *)',
    'Bash(bash */scripts/query-assets.sh *)',
    'Bash(python3 -c *)',
    'Bash(date -u *)',
    'Write(.honne/**)',
]
print(json.dumps(entries, indent=2))
"
```

結果を表示して説明:
- `bash */scripts/honne *` — すべてのhonne CLIコマンド（scan、axis run、record、render、persona check）。ワイルドカードプレフィックスで任意のインストールパスにマッチ。
- `bash */scripts/query-assets.sh *` — compareスキル用のアセットクエリ
- `python3 -c *` — インラインチェック（staleness、JSON抽出、パス解決）
- `date -u *` — render用のUTCタイムスタンプ
- `Write(.honne/**)` — `.honne/`ディレクトリへのファイル書き込み（cache、personas、assets）

## ステップ3: 設定を適用

ユーザーに質問: "プロジェクト設定に適用しますか？ (yes / no / パスのみ表示)"

- **yes** → 実行:

```bash
python3 -c "
import json, os, sys
project_key = os.getcwd().replace('/', '-')
settings_path = os.path.expanduser(f'~/.claude/projects/{project_key}/settings.json')
os.makedirs(os.path.dirname(settings_path), exist_ok=True)
if os.path.exists(settings_path):
    settings = json.load(open(settings_path))
else:
    settings = {}
tools = settings.get('allowedTools', [])
new_entries = [
    'Bash(bash */scripts/honne *)',
    'Bash(bash */scripts/query-assets.sh *)',
    'Bash(python3 -c *)',
    'Bash(date -u *)',
    'Write(.honne/**)',
]
added = 0
for entry in new_entries:
    if entry not in tools:
        tools.append(entry)
        added += 1
settings['allowedTools'] = tools
with open(settings_path, 'w') as f:
    json.dump(settings, f, indent=2)
    f.write('\n')
print(f'{settings_path}に書き込み')
print(f'{added}エントリ追加（合計{len(tools)}個のallowedTools）')
"
```

- **no** → 出力: "上のエントリを `~/.claude/settings.json` またはプロジェクト設定に手動でコピーしてください。"
- **パスのみ表示** → プロジェクト設定パスを出力。

**注**: プロジェクトレベルの設定がグローバル設定より推奨されます — このリポジトリにのみ権限をスコープ制限します。
