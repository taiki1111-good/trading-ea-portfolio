# Interview Pitch

本書は外部説明用の要約であり、Source of Truth ではない。正式な現状・契約・実装境界は `ops/CURRENT_TASKS.md`、`docs/03_architecture.md`、`docs/04_module_spec.md`、`docs/05_variable_spec.md`、`docs/10_interface_contract.md`、`docs/17_backtest_design.md` を優先する。

## 1. 30秒説明
このリポジトリは、設計・検証・説明可能性を重視した研究/検証用EAフレームワークです。

売買ロジック単体ではなく、Data から Evaluator までの責務分離、future leak 防止、判断理由ログ、dry-run（実注文を行わない検証実行）を中心に設計しています。現時点では、実際の取引システムとの接続や注文送信機能は実装していません。

## 2. 1分説明
このプロジェクトでは、自動売買EAを一つの大きな条件式として作るのではなく、`Data -> HTFContext -> LTFStructure -> Signal -> RiskFilter -> Execution -> Logger -> Evaluator` の一方向フローへ分解しています。

BacktestRunner / PipelineAdapter / CSV replay dry-run を使い、時系列上の構造検証、ログ整合、no-real-order integrity（実注文が発生していないことの整合確認）を確認します。HTF diagnostic comparison（採用前の診断比較）や lot sizing shadow comparison（本体挙動に影響させない比較）も、本体採用前に影響範囲を切り分けるための仕組みとして整理しています。

このため、面接では「収益性」よりも、責務分離、検証設計、ログ追跡、未実装範囲を分けて説明できる点を中心に話します。

## 3. 強調する技術要素
- モジュール責務と I/O 契約を先に整理していること
- 現在バーまでの情報だけを使い、future leak を避ける設計にしていること
- `decision_logs` / `trade_logs` / `state_logs` / `event_logs` を分け、判断理由と状態遷移を追えること
- main と experiments を分け、新しい仮説を本体へ直接混ぜないこと
- dry-run、diagnostic comparison、shadow comparison を使い、実装済み・検証済み・未実装を分けて確認していること

## 4. 明確に伝える未実装範囲
- 実際の取引システムとの接続
- 注文送信機能
- 収益性の確認
- lot sizing 本体接続
- Session / SR / HTF の本体filter化
- 株式対応の実装・検証

## 5. 面接での短い回答例
「このプロジェクトは、運用向けの完成EAではなく、EAを安全に検証するための研究用フレームワークです。Data、Signal、RiskFilter、Execution、Logger、Evaluator を分け、判断理由と状態遷移をログで追えるようにしています。CSV replay dry-run では注文送信を行わず、ログ整合と no-real-order integrity を確認します。HTF や lot sizing は本体採用前の診断比較として扱い、収益性や運用準備完了は主張していません。」
