# 2026-05-02 Decision Logs Schema Validation

## 実施内容
- `CsvSchemaValidator` を拡張し、backtest `decision_logs` 向けに以下を追加:
  - 必須列チェック（docs/10 4.9 の最小列案と整合）
  - `fail_stage` / `structure_source` の許容値検証
  - temporal metadata 整合検証（`temporal_candidate` 条件）
- `CsvSchemaValidator.validate_backtest_log_consistency(trade_logs, decision_logs)` を追加:
  - `trade_ok=true` 件数と trade 件数の一致
  - fallback OFF run で `heuristic_fallback` 混入検出
  - 未知 `structure_source` 検出
- `scripts/analyze_decision_logs.py` に schema/consistency 結果出力を追加。
- unit/integration テストを追加・更新。
- docs/10, docs/17, CURRENT_TASKS を更新。

## 検証
- 対象 run:
  - `logs/backtest_runs/usdjpy_m5_2024_0102_0201_lb5_dedup1_no_fallback/decision_logs.csv`
  - `logs/backtest_runs/usdjpy_m5_2024_0102_0201_lb5_dedup1_no_fallback/trade_logs.csv`
- `analyze_decision_logs.py` の schema/consistency 出力が `valid=True` になることを確認。
- `pytest -q` 実行。

## 注意
- 売買ロジック（BacktestRunner / PipelineAdapter のエントリー判定）は未変更。
- 本作業は構造検証向けログ品質改善であり、収益性評価ではない。
