# 2026-05-02 Backtest Fallback Control

## Summary
- Added fallback control to `PipelineAdapterConfig`:
  - `allow_heuristic_fallback: bool = True`
- Added fallback tracing fields and propagated across backtest flow:
  - `fallback_used`
  - `structure_source`
- Added `entry_time` / `exit_time` to persisted `trade_logs`.
- Updated run/analyze scripts for fallback ON/OFF execution and richer log analysis.

## Scope
- Focus is pipeline behavior visibility and fallback dependency check.
- No broker/OANDA integration.
- No period expansion, optimization, or profitability claim.

## Implemented Changes
- `src/backtest/pipeline_adapter.py`
  - fallback allow/disable switch
  - structure source tagging (`detector_chain`, `heuristic_fallback`)
- `src/backtest/backtest_runner.py`
  - `EntryEvent` extended with fallback metadata
  - fallback metadata propagation into position/trade/log
- `src/backtest/types.py`
  - `BacktestPosition` / `BacktestTrade` include fallback metadata
- `src/backtest/backtest_logger_adapter.py`
  - outputs `entry_time`, `exit_time`, `fallback_used`, `structure_source`
- `scripts/run_backtest_on_m5_slice.py`
  - new flags:
    - `--allow-heuristic-fallback`
    - `--disable-heuristic-fallback`
  - writes empty `trade_logs.csv` header when trade_count=0
  - summary note for no-fallback/no-entry case
- `scripts/analyze_backtest_run_logs.py`
  - added:
    - fallback_used count/rate
    - structure_source counts
    - entry/exit daily counts and hourly counts (when available)

## Validation
- Target tests passed:
  - `tests/unit/backtest/test_pipeline_adapter.py`
  - `tests/integration/test_backtest_pipeline_adapter_integration.py`
  - `tests/unit/backtest/test_backtest_runner.py`
- Result: `9 passed`

## Run Results
- Fallback ON:
  - `trade_count=34`
  - `structure_source_counts={'heuristic_fallback': 34}`
  - `fallback_used_rate=100%`
- Fallback OFF:
  - `trade_count=0`
  - detector-chain-only entry did not fire in this period
  - summary note recorded accordingly

## Important Note
- These outputs are for initial backtest/structure verification only.
- Source data uses `spread=0.2 pips` fallback and excludes fee/slippage/swap realism.
- Not for profitability evaluation.

