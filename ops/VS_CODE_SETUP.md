# VS Code セットアップ手順

## 1. 目的
本書は、`trading-ea` の VS Code 環境を人間と AI agent の両方で再現しやすくするための運用文書である。

## 2. 基本方針
- 拡張機能は基本的に PC ごとに導入が必要である
- ただし、Settings Sync を使うと同一アカウント間で拡張・設定を同期しやすい
- `.vscode/settings.json` は workspace 固有設定である
- `.vscode/extensions.json` は推奨拡張を明示するためのファイルである
- Remote 環境（SSH/Dev Container/WSL 等）では、接続先側で別途拡張確認が必要になる場合がある

## 3. 推奨拡張（この repo）
以下は `.vscode/extensions.json` で推奨している拡張。

- `shd101wyy.markdown-preview-enhanced`
- `yzhang.markdown-all-in-one`
- `bierner.markdown-mermaid`
- `eamodio.gitlens`
- `usernamehw.errorlens`
- `Gruntfuggly.todo-tree`
- `ms-python.python`
- `ryanluker.vscode-coverage-gutters`
- `redhat.vscode-yaml`
- `ms-toolsai.jupyter`
- `hediet.vscode-drawio`

## 4. テスト運用（Python）
- 本 repo の VS Code テスト運用は pytest 前提とする
- VS Code の Testing ビューを使い、`tests/` を対象に実行する
- workspace 設定は `.vscode/settings.json` を正とする

## 5. 手順（最小）
1. VS Code で repo を開く
2. `extensions.json` の推奨拡張を導入する
3. `settings.json` の workspace 設定が反映されていることを確認する
4. Testing ビューで pytest 検出・実行を確認する
5. Remote 利用時は接続先でも同様に拡張状態を確認する

## 6. AI agent 向け注意
- AI agent は実装前に本書を読むこと
- 実装前に `AGENT_INDEX.md`、`REPO_MAP.md`、`docs/00_how_to_continue.md` を確認すること
- Source of Truth は `docs/02` から `docs/08` を優先すること

## 7. 関連ファイル
- `AGENT_INDEX.md`
- `REPO_MAP.md`
- `docs/02_requirements.md`
- `docs/03_architecture.md`
- `docs/04_module_spec.md`
- `docs/05_variable_spec.md`
- `docs/06_state_spec.md`
- `docs/07_test_plan.md`
- `docs/08_development_plan.md`
- `.vscode/settings.json`
- `.vscode/extensions.json`
