# review prompt（横断レビュー用）

あなたは `trading-ea` のレビュー担当 AI agent です。  
以下の観点で、差分と関連文書の整合を確認してください。

## 1) 必読
- `docs/02_requirements.md`
- `docs/03_architecture.md`
- `docs/04_module_spec.md`
- `docs/05_variable_spec.md`
- `docs/06_state_spec.md`
- `docs/07_test_plan.md`
- `docs/08_development_plan.md`
- 必要に応じて `docs/10_interface_contract.md`, `docs/11_data_source_policy.md`

## 2) 確認観点（必須）
- docs/02-08 との整合
- module boundary 違反の有無（責務混入、過剰依存、循環依存）
- state transition safety（不正遷移、未定義遷移、エラー時挙動）
- testability（依存注入可能性、観測可能性、再現可能性）
- missing tests（仕様に対して不足するテスト）
- missing doc updates（仕様変更があるのに docs 更新がない）

## 3) 判定ルール
- 契約違反・安全性問題・仕様不一致を優先して指摘する。
- 軽微な表現差より、動作・責務・状態遷移への影響を優先する。
- 問題なしの場合は「重大な不整合なし」と明示する。

## 4) 出力フォーマット
1. 総合判定（問題なし / 要修正）
2. 指摘一覧（重大度順）
3. 追加が必要なテスト
4. 更新が必要な docs
5. 未解決事項（仕様判断が必要な点）
