# 2026-05-02 Temporal Metadata And Duplicate Analysis

## Summary
- temporal third_wave_break 成立時のメタデータを EntryEvent -> BacktestPosition -> BacktestTrade -> trade_logs へ伝播。
- 追加メタデータ:
  - recent_third_timestamp
  - recent_third_direction
  - temporal_lag_bars
  - temporal_lookback_bars
  - breakout_direction
- temporal 経路以外では空値/Noneを許容。

## Analysis Enhancements
- `scripts/analyze_backtest_run_logs.py` に追加:
  - recent_third_timestamp ごとの entry_count
  - recent_third_timestamp ごとの long/short count
  - temporal_lag_bars 分布
  - temporal_lag_bars min/max/average
  - temporal_lookback_bars 別 trade_count
  - duplicate_recent_third_candidate_count
  - max_entries_per_recent_third_candidate
  - entry_time 日別・時間帯別
- `scripts/compare_temporal_lookback_runs.py` に追加:
  - duplicate_recent_third_candidate_count
  - max_entries_per_recent_third_candidate
  - average_temporal_lag_bars
  - max_temporal_lag_bars
  - temporal_lag_bars_distribution

## Runs (fallback OFF)
- lb3 meta
- lb5 meta
- lb10 meta

## Key Comparison (meta runs)
- lb3: trade_count=5, duplicate_recent_third_candidate_count=0, max_entries_per_recent_third_candidate=1, avg_lag=1.6, max_lag=2
- lb5: trade_count=14, duplicate_recent_third_candidate_count=2, max_entries_per_recent_third_candidate=2, avg_lag=2.7857142857142856, max_lag=4
- lb10: trade_count=29, duplicate_recent_third_candidate_count=7, max_entries_per_recent_third_candidate=4, avg_lag=5.206896551724138, max_lag=9

## Notes
- 本結果は収益性評価ではない。
- spread=0.2 pips fallback 前提。
- 手数料・スリッページ・スワップ未反映。
- lookback比較は構造接続仕様の挙動比較。
