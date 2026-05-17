# 2026-05-02 Run Backtest on M5 Slice

## Summary
- Added `scripts/run_backtest_on_m5_slice.py`.
- Ran `BacktestRunner + PipelineAdapter` on generated M5 slice:
  - `data/private/backtest_slices/USDJPY_M5_2024-01-02_2024-01-09.csv`
- Persisted run outputs under:
  - `logs/backtest_runs/usdjpy_m5_2024_0102_0109_initial/`

## Scope
- Executed minimal backtest flow only:
  - `PriceDataLoader.load_from_csv(..., timeframe="M5")`
  - `PipelineAdapter`
  - `BacktestRunner.run(...)`
  - summary/trade log/evaluator result output
- Not in scope:
  - real broker or OANDA API
  - real order sending
  - walk-forward, ML, optimization
  - profitability claim

## Script Behavior
- CLI args:
  - `--input-csv`
  - `--run-id`
  - `--output-dir`
  - `--max-holding-bars`
- Writes:
  - `trade_logs.csv` (when trade exists)
  - `backtest_summary.csv`
  - `backtest_summary.md`
  - `evaluator_result.txt`
- If `trade_count=0`:
  - no error
  - summary note records that no qualifying entry occurred under current conditions

## Verification
- `CsvLogWriter` used for trade log persistence.
- `CsvLogReader + CsvSchemaValidator("trade_logs")` executed when logs exist.
- Confirmed required reason/PnL fields exist in `trade_logs.csv`:
  - `entry_reason`
  - `signal_reason`
  - `risk_reason`
  - `filter_reason`
  - `exit_reason`
  - `pnl`
  - `realized_pnl`

## Important Note
- This run uses data with fixed `spread=0.2 pips` fallback.
- This is acceptable for initial structure checks / research backtest baseline.
- This is not operation-like approximation and must not be treated as production-grade execution realism.

