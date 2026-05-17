# Trading EA

## 概要
モジュール分割と段階的テストを前提として、自動売買EAを設計・実装する個人プロジェクトです。
本リポジトリは研究・検証用EAフレームワークであり、実運用EA、収益性確認済みシステム、broker接続済みシステムではありません。

## このプロジェクトで示すこと
- 売買ロジック単体ではなく、責務分離・ログ設計・dry-run・diagnostic comparison・shadow comparison を通じて、判断過程を説明可能にする設計
- `Data` から `Evaluator` までの一方向フロー
- 実注文より前に、構造検証・ログ整合・no-real-order integrity を確認する進め方

## まず見るべき文書
- 概要: `README.md`
- 外部説明: `docs/portfolio/portfolio_overview.md`
- アーキテクチャ: `docs/portfolio/architecture_for_portfolio.md`
- 公開時の注意: `docs/portfolio/disclosure_policy.md`
- 公開前チェック: `docs/portfolio/public_review_checklist.md`
- 見せ方計画: `docs/portfolio/showcase_assets_plan.md`
- 詳細な設計・作業履歴: `docs/` と `ops/worklog/`（外部向け主導線ではない）

## 簡易フロー
```text
Data
  -> HTFContext
  -> LTFStructure
  -> Signal
  -> RiskFilter
  -> Execution
  -> Logger
  -> Evaluator
```

## 現在の段階
主要モジュール（Data -> HTFContext -> LTFStructure -> Signal -> RiskFilter -> Execution -> Logger -> Evaluator）を一周実装し、dry-run / diagnostic / shadow comparison を通じて、判断過程の説明可能性を重視した分析・検証基盤として整備を進めています。

### 実装済み・到達点
- `Data` から `Evaluator` までの一方向フローを実装
- `tests/integration/test_end_to_end_minimal_pipeline.py` による E2E 最小統合テストを完了
- `Execution` は dry-run skeleton として設計されており、実 broker / OANDA API / 実注文送信は未実装
- `src/persistence/` に CSV persistence skeleton を実装し、Logger -> Persistence -> Evaluator の接続確認を行っている
- main 初期版は `third_wave_break` のみ、本体に `triangle_break` は `experiments` 扱いで分離
- `BacktestRunner` / `PipelineAdapter` で構造検証を継続
- `PipelineAdapter` は planner chain（`PositionSizer` / `StopLossPlanner` / `TakeProfitPlanner` / `RiskAssembler`）へ正式接続済み（fixed baseline 同値維持目的）
- `Risk/Stop v0` 最小実装を採用済み（`PositionSizer` は placeholder）
- `HTF diagnostic comparison v0` を完了（OFF/permissive/strict の比較 + candidate/accepted/rejected 集合の診断）
- `Lot Sizing shadow comparison` を diagnostic / shadow comparison tool として採用済み
- CSV replay pipeline dry-run の representative run を完了し、no-real-order 整合を確認

### 注意・未実装
- 上記は設計・検証基盤としての到達点であり、収益性確認済みを意味しない。
- lot sizing 本体接続（risk-based lot の本線採用）は未実装。
- `PositionSizer` は placeholder であり、lot sizing 本体ではない。
- HTF は diagnostic comparison v0 であり、本体filter採用ではない。
- `Lot Sizing shadow comparison` は diagnostic / shadow comparison tool であり、本体接続ではない。
- Session v2 は diagnostic_only であり、entry を止めない。
- Session / SR / HTF の本体filter化は未実装（Session v2 は diagnostic_only）。
- 検証詳細や前提条件は `docs/09_presentation_notes.md` と `docs/17_backtest_design.md` を参照。

## 設計文書
- `docs/01_overview.md`
- `docs/02_requirements.md`
- `docs/03_architecture.md`
- `docs/04_module_spec.md`
- `docs/05_variable_spec.md`
- `docs/06_state_spec.md`
- `docs/07_test_plan.md`
- `docs/08_development_plan.md`
- `docs/09_presentation_notes.md`
- `docs/10_interface_contract.md`
- `docs/11_data_source_policy.md`
- `docs/12_project_kpi.md`
- `docs/13_project_management.md`
- `docs/14_traceability_matrix.md`
- `docs/15_non_functional_requirements.md`
- `docs/16_operation_design.md`
- `docs/17_backtest_design.md`
- `docs/18_asset_class_extension_policy.md`
- `docs/19_strategy_extension_policy.md`

## Portfolio Docs
- [portfolio_overview.md](docs/portfolio/portfolio_overview.md)
- [architecture_for_portfolio.md](docs/portfolio/architecture_for_portfolio.md)
- [disclosure_policy.md](docs/portfolio/disclosure_policy.md)
- [public_review_checklist.md](docs/portfolio/public_review_checklist.md)
- [showcase_assets_plan.md](docs/portfolio/showcase_assets_plan.md)
- `docs/portfolio/` は README から辿る外部説明用の要約です。
- `portfolio/` は作業用の説明下書き・補助資料です。
- `ops/worklog/` は詳細な作業履歴・設計判断履歴（古い検討や途中経過を含む）です。
- 外部向けの主導線は README と `docs/portfolio/*` を優先してください。
- worklog内の個別runや数値は、収益性確認や実運用可能性を意味しません。
- Source of Truth は `ops/CURRENT_TASKS.md` と `docs/` を優先します。

## 開発方針
- 設計を先に確定する
- 上流モジュールから順に実装する
- 各段階でテストを挟む
- 実装と並行してポートフォリオ資料も整備する
