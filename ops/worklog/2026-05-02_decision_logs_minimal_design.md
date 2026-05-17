# 2026-05-02 decision logs minimal design

## 実施内容
- docs/17 に decision_logs 最小方針を追記。
- docs/10 に backtest decision_logs の最小列案を追記。
- BacktestRunner / PipelineAdapter に最小 decision trace を実装し、decision_logs を出力可能化。
- run_backtest_on_m5_slice.py で decision_logs.csv 出力を追加（trade_logs仕様は維持）。
- CURRENT_TASKS を更新し、別週再現性確認を完了扱い、次タスクを decision_logs/no-entry 診断へ更新。
- unit/integration テストに decision trace / decision_logs 非空確認を追加。

## 注意
- 売買ロジックは変更していない。
- 収益性評価は目的外。
- 実 broker/OANDA API/実注文送信は未実装。
