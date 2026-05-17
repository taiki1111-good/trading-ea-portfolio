# Interview Pitch

本書は、`trading-ea` を面接・ポートフォリオ説明で話すための補助資料である。

本書は外部説明用の要約であり、Source of Truth ではない。正式な現状・契約・実装境界は `ops/CURRENT_TASKS.md`、`docs/03_architecture.md`、`docs/04_module_spec.md`、`docs/05_variable_spec.md`、`docs/10_interface_contract.md`、`docs/17_backtest_design.md` を優先する。

## 1. 30秒説明

このプロジェクトは、実運用EAや収益性確認済みシステムではなく、研究・検証用の自動売買EAフレームワークです。

売買ロジック単体ではなく、`Data -> HTFContext -> LTFStructure -> Signal -> RiskFilter -> Execution -> Logger -> Evaluator` という一方向フローに分け、判断理由や状態遷移をログから追跡できるように設計しています。実注文前に、dry-run、diagnostic comparison、shadow comparison を通じて、構造検証・ログ整合・no-real-order integrity を確認することを重視しています。

## 2. 1分説明

`trading-ea` は、研究・検証用の自動売買EAフレームワークです。目的は「儲かるEA」として見せることではなく、売買判断、リスク制御、実行、ログ、評価を責務ごとに分離し、判断過程を後から検証できる基盤を作ることです。

中心となる設計は、`Data -> HTFContext -> LTFStructure -> Signal -> RiskFilter -> Execution -> Logger -> Evaluator` の一方向フローです。BacktestRunner / PipelineAdapter を通じて時系列順に処理し、future leak を避けながら、dry-run とログ整合を確認します。

現時点では、Phase 9 CSV replay pipeline dry-run、Risk/Stop v0、PipelineAdapter planner chain 正式接続、HTF diagnostic comparison v0、Lot Sizing shadow comparison まで整理しています。ただし、実 broker / OANDA API / 実注文送信、収益性確認、lot sizing 本体接続、Session/SR/HTF の本体filter化は未実装です。

## 3. 3分説明

このプロジェクトでは、自動売買EAを単なる売買条件の集合としてではなく、検証可能なシステムとして設計しました。

まず、Data、HTFContext、LTFStructure、Signal、RiskFilter、Execution、Logger、Evaluator に責務を分けています。これにより、どの段階で何を判断したのか、どの理由で entry 候補になったのか、RiskFilter で何が通過・停止したのか、状態遷移やイベントがどのように起きたのかを、ログから追跡できるようにしています。

次に、BacktestRunner / PipelineAdapter を通じて、過去データを時系列順に流し、各時点で参照可能な情報だけを使う設計にしています。future leak を避けるため、現在バーより未来の情報を使わないことを docs と実装の両方で重視しています。

また、実注文や broker 接続へ進む前に、CSV replay pipeline dry-run によってログ整合、health 判定、no-real-order integrity を確認する方針を取っています。HTF は diagnostic comparison v0 として OFF / permissive / strict を比較し、本体filter採用前の診断に留めています。Lot Sizing も本体接続ではなく、fixed baseline と risk-based lot の違いを見る shadow comparison tool として扱っています。

このため、現時点の成果は収益性確認や実運用可能性ではなく、設計、責務分離、ログ追跡、検証手順、未実装範囲の明確化にあります。実 broker / OANDA API / 実注文送信、収益性確認、lot sizing 本体接続、Session/SR/HTF の本体filter化は未実装です。

## 4. 強調するポイント

- 売買ロジック単体ではなく、検証可能なフレームワークとして設計した。
- モジュール責務と I/O 契約を先に整理してから実装した。
- future leak を避ける時系列処理を重視した。
- dry-run と no-real-order integrity により、実注文前の構造検証を行った。
- decision / trade / state / event のログを分け、判断理由を追跡できるようにした。
- HTF や lot sizing は本体採用前に diagnostic / shadow comparison として比較した。
- 実装済み、未実装、future optional を分けて説明できるようにした。

## 5. 避ける説明

以下のような表現は使わない。

- 収益性確認済み
- 実運用可能
- 実注文対応済み
- broker接続済み
- OANDA API接続済み
- risk-based lot 本体接続済み
- HTF filter採用済み
- 完成済みEA
- 本番運用EA

## 6. よくある質問への答え方

### Q. 実際に利益は出ていますか？

このプロジェクトでは、収益性確認を主目的にはしていません。現時点では、売買判断・リスク制御・ログ・評価を分け、dry-run や diagnostic comparison によって構造検証を行う段階です。PnL や勝率を成果として主張する段階ではありません。

### Q. 実運用できますか？

できません。実 broker 接続、OANDA API 接続、実注文送信、実運用監視、通知、復旧フローは未実装です。現時点では研究・検証用EAフレームワークです。

### Q. 何が一番の成果ですか？

売買ロジックそのものよりも、システムを責務分離し、時系列処理、ログ追跡、dry-run、diagnostic comparison、shadow comparison を通じて、判断過程を後から説明できる形にした点です。

### Q. なぜ画像やグラフで収益を見せないのですか？

誤解を避けるためです。現時点では収益性確認済みではないため、PnL、win_rate、total_pnl を外部説明の中心にはしていません。代わりに、検証フロー、アーキテクチャ、ログ設計、未実装範囲を明示しています。

## 7. 参照導線

外部説明では、以下を主導線とする。

1. `README.md`
2. `docs/portfolio/portfolio_overview.md`
3. `docs/portfolio/architecture_for_portfolio.md`
4. `docs/portfolio/showcase_assets_plan.md`
5. `docs/portfolio/disclosure_policy.md`
6. `docs/portfolio/public_review_checklist.md`

`ops/worklog/` は詳細な作業履歴・設計判断履歴であり、最初の説明導線としては扱わない。
