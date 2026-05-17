# 2026-05-02 Temporal Lookback Comparison

## Summary
- 同一1週間データで temporal lookback 3/5/10 を fallback OFF のまま比較。
- 各 run で `run_backtest_on_m5_slice.py` を実行し、`analyze_backtest_run_logs.py` で分析。
- 比較集約スクリプト `scripts/compare_temporal_lookback_runs.py` を追加し、CSV/MDを生成。

## Runs
- lb3: `usdjpy_m5_2024_0102_0109_temporal_lb3_no_fallback`
- lb5: `usdjpy_m5_2024_0102_0109_temporal_lb5_no_fallback`
- lb10: `usdjpy_m5_2024_0102_0109_temporal_lb10_no_fallback`

## Key Results
- lb3: trade_count=5, long/short=2/3, win_rate=60.0, total_pnl=0.0040000000000048885, avg_pnl=0.0008000000000009777
- lb5: trade_count=14, long/short=8/6, win_rate=42.857142857142854, total_pnl=0.004000000000013414, avg_pnl=0.00028571428571524385
- lb10: trade_count=29, long/short=18/11, win_rate=51.724137931034484, total_pnl=0.016000000000028082, avg_pnl=0.0005517241379320028
- structure_source は全runで `detector_chain_temporal` のみ
- fallback_used_rate は全runで 0.0%
- temporal reason count は trade_count と一致（lb3=5, lb5=14, lb10=29）

## Notes
- これは収益性評価ではない。
- spread=0.2 pips fallback 前提。
- 手数料・スリッページ・スワップ未反映。
- lookback比較は構造接続仕様の比較であり最適化確定ではない。
- 期間は1週間のみ。
