# Presentation Notes

## 1. この文書の目的
この文書は、外部向け説明やポートフォリオ用の要点を整理するためのメモである。プロジェクトの構成、現状、テスト、ログ・再現性、未実装項目を短く説明できる形にまとめる。

本書は外部説明用の要約であり、Source of Truth ではない。現在状況は `ops/CURRENT_TASKS.md`、設計契約は `docs/03_architecture.md`、`docs/04_module_spec.md`、`docs/05_variable_spec.md`、`docs/10_interface_contract.md`、`docs/17_backtest_design.md` を優先する。

## 2. このプロジェクトで示せること
- 研究・検証用EAフレームワークとしての責務分離設計
- `Data -> HTFContext -> LTFStructure -> Signal -> RiskFilter -> Execution -> Logger -> Evaluator` の一方向フロー
- BacktestRunner / PipelineAdapter による構造検証
- CSV replay pipeline dry-run による near-live 風のログ整合確認
- `decision_logs` / `trade_logs` / `state_logs` / `event_logs` を分けるログ設計
- future leak 防止を前提にした時系列駆動
- main ロジックと experiments の分離
- Risk/Stop v0 による `trade_ok`、`lot`、`stop_loss`、`take_profit`、理由文字列の契約確認

## 3. 現在の到達点
現時点では、`ops/CURRENT_TASKS.md` に従い以下の段階として扱う。

- Phase 9 CSV replay pipeline dry-run minimal completion reached (Option A)
- Risk/Stop v0 minimal implementation adopted
- 主要モジュールの一方向フローを実装済み
- BacktestRunner / PipelineAdapter を使った構造検証を実施済み
- CSV replay pipeline dry-run の representative run を確認済み
- weekday representative run で `dry_run_health_status=pass` を確認済み
- weekend expected gap representative run で `dry_run_health_status=pass` / `pipeline_health_ok` を確認済み
- no real order integrity を含む最小 health 判定を実装済み
- Risk/Stop v0 review follow-up 後の記録として targeted `92 passed`、full `420 passed`
- `PipelineAdapter` planner chain 正式接続を採用済み（fixed baseline 同値維持目的）
- HTF diagnostic comparison v0 を完了（3条件比較、candidate/accepted/rejected 集合の診断）
- lot sizing shadow comparison を diagnostic / shadow comparison tool として採用済み

注意:
- 上記の `pass` は dry-run health / ログ整合確認であり、収益性や実運用品質を意味しない。
- 実 broker / OANDA API / 実注文送信は未実装。
- 収益性確認済みではない。
- lot sizing 本体は未実装であり、`PositionSizer` は placeholder。
- lot sizing の risk-based lot は本線接続していない（comparison-only）。
- Session v2 は diagnostic_only 継続、Session/SR/HTF の本体filter化は未実装。

## 4. モジュール分割と責務分離
- `src/data/`: 価格データやイベントデータの入力処理
- `src/htf_context/`: 上位足環境の認識と整理
- `src/ltf_structure/`: 執行足の構造認識
- `src/signal/`: HTF と LTF を統合して売買候補を生成
- `src/risk_filter/`: 取引可否、停止条件、lot/SL/TP の判断
- `src/execution/`: 注文実行と状態管理（現状は dry-run / skeleton 中心）
- `src/logger/`: 判定理由、状態遷移、注文結果を記録
- `src/evaluator/`: 成績評価と改善対象整理
- `src/persistence/`: CSV persistence skeleton を中心としたログ永続化
- `src/backtest/`: BacktestRunner / PipelineAdapter による構造検証

## 5. テスト・検証で説明できること
- 単体テスト: Data / Signal / RiskFilter などの部品契約確認
- 結合テスト: Signal -> RiskFilter、BacktestRunner / PipelineAdapter の接続確認
- E2E 最小統合テスト: Data から Evaluator までの接続確認
- CSV replay dry-run: replay bar と decision log の整合確認
- no real order integrity: dry-run 中に実注文送信がないことの確認
- weekday / weekend expected gap: 通常代表期間と weekend gap を含む代表期間の health 判定確認

## 6. ログ・再現性設計
- `run_id` 単位でログを分離する方針
- `decision_logs.csv` / `trade_logs.csv` / `state_logs.csv` / `event_logs.csv` の責務分離
- 判断理由を `*_reason` として追跡し、後から構造検証しやすくする方針
- `dry_run_health_status` と `status_reason` により、ログ整合や no real order integrity を要約する方針
- future leak 防止のため、各時点で参照可能なバーを現在時点までに限定する方針

## 7. まだ未実装の範囲
- 実 broker API / OANDA API 連携
- 実注文送信と約定確認の本格実装
- lot sizing 本体（`account_balance` / `risk_per_trade` / broker lot 制約厳密化）
- Session / SR / HTF の本体 filter 化
- 株式対応の実装・検証
- 収益性確認、パラメータ最適化、実運用監視・通知・復旧フロー

## 8. 面接で説明する場合の短い説明文
このプロジェクトは、実運用EAではなく、研究・検証用の自動売買EAフレームワークです。Data から Evaluator までを一方向フローに分け、BacktestRunner / PipelineAdapter と CSV replay dry-run で、売買判断・リスク判定・ログ出力が時系列上で破綻なく接続されるかを検証しています。

現時点では Phase 9 として CSV replay pipeline dry-run の representative run を確認し、`dry_run_health_status=pass`、no real order integrity、weekday/weekend expected gap の代表確認まで到達しています。また Risk/Stop v0（`PositionSizer` placeholder 維持）、PipelineAdapter planner chain 正式接続、HTF diagnostic comparison v0、lot sizing shadow comparison（comparison-only）まで整備しています。ただし、収益性確認、実注文、OANDA/API 接続、lot sizing 本体接続、Session/SR/HTF の本体filter化は未実装です。
