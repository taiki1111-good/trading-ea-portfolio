# 2026-05-02 Position-aware Counterfactual Exit Replay

## 目的
独立counterfactual exit analysis（trade独立）に対して、position保有中の後続entry抑止を含む position-aware replay を追加し、構造検証を行った。

## 実装
- `scripts/replay_counterfactual_exits_position_aware.py` を追加。
- 対応rule:
  - `baseline_fixed_exit`
  - `simple_trailing_after_1R`
- 処理:
  - `trade_logs` の entry候補を entry_time 昇順で処理
  - positionなし時のみ entry accepted
  - position保有中の候補は `skipped_due_to_open_position`
  - accepted trade は rule に応じて exit再計算
  - 同時保有なしを検証

## 出力
- `position_aware_counterfactual_trades.csv`
- `position_aware_counterfactual_summary.csv`
- `position_aware_counterfactual_summary.md`

## docs更新
- `docs/17_backtest_design.md` に 6.6 節を追記。
- 独立counterfactual（局所exit評価）と position-aware replay（同時保有抑止含む）を別分析として明記。
- ただし後追いであり正式BacktestRunner統合ではないことを明記。

## テスト
- `tests/unit/backtest/test_replay_counterfactual_exits_position_aware.py` を追加。
  - 保有中entry skip
  - exit後entry accept
  - accepted+skipped件数整合
  - position overlapなし
  - baseline件数整合
  - trailingでbaseline以上のskipが起こり得ること

## 実行
- `$env:PYTHONPATH='.'; pytest -q`
- `$env:PYTHONPATH='.'; python scripts/replay_counterfactual_exits_position_aware.py --price-csv data/private/backtest_slices/USDJPY_M5_2024-01-02_2024-04-01.csv --trade-logs logs/backtest_runs/usdjpy_m5_2024_0102_0401_lb5_dedup1_no_fallback/trade_logs.csv --output-dir logs/backtest_runs/usdjpy_m5_2024_0102_0401_lb5_dedup1_no_fallback/counterfactual_exit_position_aware --rule simple_trailing_after_1R --max-holding-bars 6`

## 結果
- `pytest -q`: `224 passed`
- 今回データでは `simple_trailing_after_1R` の position-aware replay は skip 0件（独立分析と同値）。
- ただしスクリプト/テスト上は skip発生ケースを検証できる状態にした。

## 注意
- 収益性評価ではなく構造検証。
- spread=0.2 pips fallback、手数料・スリッページ・スワップ未反映。
- 売買ロジック本体、BacktestRunner / PipelineAdapter / ExitRuleEngine は未変更。
