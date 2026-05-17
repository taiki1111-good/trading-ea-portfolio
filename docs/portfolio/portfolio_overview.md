# Portfolio Overview

本書は外部説明用の要約であり、Source of Truth ではない。正式な現状・契約・実装境界は `ops/CURRENT_TASKS.md`、`docs/03_architecture.md`、`docs/04_module_spec.md`、`docs/05_variable_spec.md`、`docs/10_interface_contract.md`、`docs/17_backtest_design.md` を優先する。

## 1. プロジェクト概要
`trading-ea` は、設計・検証・説明可能性を重視した研究/検証用の自動売買EAフレームワークである。

目的は、売買ロジックそのものを強調することではなく、責務分離、ログ、再現性、検証手順を自然に説明できる形へ整理することである。現時点では、実際の取引システムとの接続や注文送信機能は実装していない。

## 2. 開発目的
- 裁量的な判断をモジュール責務へ分解する。
- `Data -> HTFContext -> LTFStructure -> Signal -> RiskFilter -> Execution -> Logger -> Evaluator` の一方向フローを構築する。
- backtest / dry-run（実注文を行わない検証実行）/ experiments を分離して、検証結果の意味を混同しない。
- 判断理由と状態遷移をログから追跡できるようにする。
- 将来の追加仮説を main ロジックへ直接混ぜず、experiments で比較できる形にする。

## 3. 現在の到達点
- Phase 9 CSV replay pipeline dry-run minimal completion reached (Option A)
- Risk/Stop v0 minimal implementation adopted
- PipelineAdapter planner chain 正式接続済み（fixed baseline 同値維持目的）
- BacktestRunner / PipelineAdapter による構造検証を実施
- CSV replay pipeline dry-run の representative run を確認
- weekday representative run で `dry_run_health_status=pass` を確認
- weekend expected gap representative run で `dry_run_health_status=pass` / `pipeline_health_ok` を確認
- no-real-order integrity（実注文が発生していないことの整合確認）を含む health 判定を確認
- HTF diagnostic comparison v0（上位足フィルター候補を本体採用前に比較する診断）を完了
- Lot Sizing shadow comparison（本体のロット決定を変えずに固定lotとrisk-based lotを比較する仕組み）を採用
- targeted `92 passed`、full `420 passed` が `ops/CURRENT_TASKS.md` に記録済み

## 4. 技術的に示せること
- モジュール分割と I/O 契約を先に整理してから実装する進め方
- 時系列処理で future leak を防ぐ設計
- BacktestRunner と PipelineAdapter を使った構造検証
- dry-run における no-real-order integrity の確認
- 判断理由をログに残す追跡可能性
- main と experiments を分離した研究用設計
- Risk/Stop v0 における `trade_ok` と SL/TP/lot 契約の最小確認

## 5. 実装済み範囲
- Data から Evaluator までの一方向フロー
- BacktestRunner / PipelineAdapter の構造検証用接続
- CSV persistence skeleton
- CSV replay pipeline dry-run の最小 health 判定
- Risk/Stop v0 の最小実装
- `PositionSizer` placeholder
- PipelineAdapter planner chain 正式接続（fixed baseline 同値維持）
- HTF diagnostic comparison v0（OFF/permissive/strict の比較 + candidate/accepted/rejected 診断）
- lot sizing shadow comparison（comparison-only）
- `decision_logs` / `trade_logs` / `state_logs` / `event_logs` の分離方針

## 6. 未実装範囲
- 実際の取引システムとの接続
- 注文送信機能
- 収益性の確認
- lot sizing 本体
- `account_balance` / `risk_per_trade` / 取引単位制約の厳密化
- Session / SR / HTF の本体 filter 化
- Session v2 の本体filter化（現状は diagnostic_only）
- 株式対応の実装・検証
- 実運用監視、通知、復旧フロー

## 7. 検証フロー
```text
Data / Price CSV
  -> BacktestRunner / PipelineAdapter
  -> Signal / RiskFilter
  -> Execution dry-run
  -> Logger / Persistence
  -> Evaluator / Summary

diagnostic / integrity checks (side tracks):
  - CSV replay pipeline dry-run
  - HTF diagnostic comparison v0
  - Lot Sizing shadow comparison
  - no-real-order integrity check
```

- dry-run は、実注文を行わない検証実行である。
- diagnostic comparison は、採用前に条件差分を診断する比較である。
- shadow comparison は、本体挙動へ影響させずに候補値を比較する仕組みである。
- no-real-order integrity は、実注文が発生していないことの整合確認である。
- HTF は diagnostic comparison v0 であり、本体filter採用ではない。
- Lot Sizing は shadow comparison tool であり、本体接続ではない。
- dry-run health の `pass` は、収益性や実運用品質を意味しない。

## 8. テスト・検証の概要
- unit test で下位部品の契約を確認する。
- integration test でモジュール間接続を確認する。
- BacktestRunner / PipelineAdapter で時系列上の構造検証を行う。
- CSV replay dry-run で near-live 風のログ整合を確認する。
- no-real-order integrity により、dry-run 中に注文送信がないことを確認する。
- `pass` は dry-run health の結果であり、収益性や実運用品質を意味しない。

## 9. 面接での説明例
このリポジトリは、研究・検証用の自動売買EAフレームワークです。売買ロジック単体ではなく、Data から Evaluator までの責務分離、future leak 防止、ログ追跡、backtest / dry-run の検証手順を中心に設計しています。

現時点では Phase 9 として CSV replay pipeline dry-run の representative run を確認し、Risk/Stop v0 として `trade_ok`、lot、SL/TP、理由ログの最小契約を実装・テストしています。加えて、PipelineAdapter planner chain 正式接続（fixed baseline 同値維持目的）、HTF diagnostic comparison v0、lot sizing shadow comparison（comparison-only）まで整備しています。ただし、注文送信、実際の取引システムとの接続、lot sizing 本体接続、Session/SR/HTF の本体filter化、収益性確認は未実装です。
