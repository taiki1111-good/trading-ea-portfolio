# 2026-05-02 Q2 exit experiment out-of-sample check

## 目的
- Q1で実施した experimental exit comparison（fixed_sl_tp vs simple_trailing_after_1R）を、同一条件のまま Q2（2024-04-01〜2024-07-01）で再確認する。

## 実施内容
1. M5スライス生成
- 入力: `data/raw/dukascopy/USDJPY/M1/dat_csv_candidates/DAT_MT_USDJPY_M1_2024.csv`
- 出力: `data/private/backtest_slices/USDJPY_M5_2024-04-01_2024-07-01.csv`
- 条件: `spread-pips=0.2`

2. Loader確認
- `bar_count=18720`
- `start_time=2024-04-01T00:00:00+00:00`
- `end_time=2024-06-30T23:55:00+00:00`
- `invalid_ohlc_count=0`

3. M5 experimental exit（月別）
- 共通条件:
  - `--disable-heuristic-fallback`
  - `--third-candidate-lookback-bars 5`
  - `--max-entries-per-recent-third-candidate 1`
  - `--entry-time-mode m5_close`
  - `--max-holding-bars 50`
- 対象:
  - 2024-04-01〜2024-05-01
  - 2024-05-01〜2024-06-01
  - 2024-06-01〜2024-07-01
- 比較:
  - `fixed_sl_tp`
  - `simple_trailing_after_1R`

4. M5比較出力
- `logs/backtest_runs/usdjpy_m5_2024_q2_exit_experiment_comparison/exit_experiment_comparison.csv`
- `logs/backtest_runs/usdjpy_m5_2024_q2_exit_experiment_comparison/exit_experiment_comparison.md`

5. M1 replay（Q2全体、entry固定）
- fixed側Q2 trade_logs（4月+5月+6月）を結合し、entry候補として利用。
- 条件:
  - `entry_time_mode=m5_close`
  - `entry_timeframe_minutes=5`
  - `max_holding_minutes=50`
  - `spread_pips=0.2`
- ルール:
  - `baseline_fixed_exit`
  - `simple_trailing_after_1R`
  - `simple_trailing_after_1R_conservative`
  - `simple_trailing_after_1R_next_bar_activation`
- 比較出力:
  - `logs/backtest_runs/usdjpy_m5_2024_q2_m1_exit_replay_comparison/m1_exit_replay_comparison.csv`
  - `logs/backtest_runs/usdjpy_m5_2024_q2_m1_exit_replay_comparison/m1_exit_replay_comparison.md`

## メモ
- 本作業は構造検証であり、収益性確認ではない。
- 前提は `spread=0.2 pips fallback`、`手数料/スリッページ/スワップ未反映`。
- BacktestRunner / PipelineAdapter / ExitRuleEngine の既定動作、売買ロジック本体、exit policy追加は未変更。
