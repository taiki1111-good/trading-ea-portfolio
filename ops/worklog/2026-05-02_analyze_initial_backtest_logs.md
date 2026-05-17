# 2026-05-02 Analyze Initial Backtest Logs

## Summary
- Added `scripts/analyze_backtest_run_logs.py`.
- Analyzed existing run log only:
  - `logs/backtest_runs/usdjpy_m5_2024_0102_0109_initial/trade_logs.csv`
- Generated:
  - `logs/backtest_runs/usdjpy_m5_2024_0102_0109_initial/trade_log_analysis.md`
  - `logs/backtest_runs/usdjpy_m5_2024_0102_0109_initial/trade_log_analysis.csv`

## Scope
- This task is log analysis for pipeline behavior checks.
- No new backtest run, no period expansion, no runtime strategy changes.

## Notes
- Results are for initial structure/backtest verification only.
- Source run uses fixed `spread=0.2 pips` fallback.
- Commission/slippage/swap are not reflected.
- Profitability interpretation is out of scope.

## Key Findings
- `trade_count=34`
- `signal_type`: `long_entry=31`, `short_entry=3`
- `exit_reason`: `stop_loss=28`, `take_profit=6`
- fallback marker (`fallback heuristic structure was used`) appeared in all trades (`34/34`, `100%`).
- reason fields (`entry/signal/risk/filter`) had no missing values.

