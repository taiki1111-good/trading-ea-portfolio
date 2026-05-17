# 2026-05-02 Temporal Third Break Connection

## Summary
- `PipelineAdapter` に detector chain の時系列接続経路 `detector_chain_temporal` を追加。
- same-bar `StructureAssembler` 不成立時に、breakout 現在バーと過去Nバーの `wave_phase=third` を接続して `third_wave_break` 候補化。
- `fallback_used` は heuristic fallback のときのみ true を維持。temporal は false。
- `structure_source` を `detector_chain / detector_chain_temporal / heuristic_fallback` で区別。
- `run_backtest_on_m5_slice.py` に temporal 設定CLIを追加。
- `diagnose_ltf_detector_chain_on_m5_slice.py` に temporal 集計指標を追加。

## Docs
- `docs/17_backtest_design.md` に時系列接続方針を追記。
  - third候補は数バー後breakoutと接続しうる
  - 判定は常に bars[:i+1] のみ（future leak禁止）
  - lookback設定化、初期候補5 bars
  - fallback heuristic ではなく detector_chain_temporal
  - 収益性評価ではなく構造検証目的

## Config / Behavior
- `PipelineAdapterConfig` 追加:
  - `third_candidate_lookback_bars: int = 5`
  - `allow_temporal_third_break: bool = True`
- temporal 条件:
  - same-bar structure_candidate=false
  - current breakout_flag=true
  - 過去Nバー以内に wave_phase=third
  - recent third direction == breakout_direction

## Validation
- `pytest -q tests/unit/backtest/test_pipeline_adapter.py tests/integration/test_backtest_pipeline_adapter_integration.py` -> 9 passed
- `pytest -q` -> 189 passed

## Runs
- Diagnose:
  - `python scripts/diagnose_ltf_detector_chain_on_m5_slice.py --input-csv data/private/backtest_slices/USDJPY_M5_2024-01-02_2024-01-09.csv --output-dir logs/backtest_runs/usdjpy_m5_2024_0102_0109_detector_diagnosis_wave_breakout_overlap`
- Backtest (fallback OFF / temporal ON):
  - `python scripts/run_backtest_on_m5_slice.py --input-csv data/private/backtest_slices/USDJPY_M5_2024-01-02_2024-01-09.csv --run-id usdjpy_m5_2024_0102_0109_temporal_no_fallback --output-dir logs/backtest_runs/usdjpy_m5_2024_0102_0109_temporal_no_fallback --max-holding-bars 10 --disable-heuristic-fallback --third-candidate-lookback-bars 5`
- Analyze:
  - `python scripts/analyze_backtest_run_logs.py --trade-logs logs/backtest_runs/usdjpy_m5_2024_0102_0109_temporal_no_fallback/trade_logs.csv --output-dir logs/backtest_runs/usdjpy_m5_2024_0102_0109_temporal_no_fallback/analysis`

## Key Results
- Diagnose temporal metrics:
  - temporal_third_break_candidate_count_3=27
  - temporal_third_break_candidate_count_5=49
  - temporal_third_break_candidate_count_10=93
  - temporal_direction_match_count_3=5
  - temporal_direction_match_count_5=15
  - temporal_direction_match_count_10=36
- Backtest fallback OFF / temporal ON:
  - trade_count=14
  - structure_source_counts={'detector_chain_temporal': 14}
  - fallback_used_rate=0.0%
  - signal_type_counts={'long_entry': 8, 'short_entry': 6}
  - exit_reason_counts={'stop_loss': 8, 'take_profit': 6}
