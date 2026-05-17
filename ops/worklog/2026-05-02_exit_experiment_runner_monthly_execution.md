# 2026-05-02 Exit Experiment Runner Monthly Execution

## 目的
- experimental exit runner の Q1 安定実行に向けて、進捗表示・期間分割・比較集計を追加。

## 変更
- `scripts/run_backtest_exit_experiment.py`
  - progress表示（total/processed/timestamp/trade_count/elapsed）
  - `--start` / `--end` 期間フィルタ
  - `run_metadata.json` 出力
  - `--partial-save-every-bars` による `partial_trade_logs.csv` 任意保存
- `scripts/compare_exit_experiment_runs.py` を追加
  - 複数run directoryを比較して `exit_experiment_comparison.csv/.md` を生成
- `docs/17_backtest_design.md` に月別分割運用と役割差分を追記

## 実行方針
- Q1一括前に月別（01/02/03）で fixed_sl_tp / simple_trailing_after_1R を比較

## 注意
- spread=0.2 pips fallback 前提
- 手数料・スリッページ・スワップ未反映
- 収益性評価ではなく構造検証
