# 2026-05-03 Halt diagnostic OOS-2 2024-11 initial result

## 1. 実行条件（記録）
- input-csv: `data/private/backtest_slices/USDJPY_M5_2024-11-01_2024-12-01.csv`
- decision-logs: `logs/backtest_runs/oos2_20241101_1201_htf_off_trailing/decision_logs.csv`
- trade-logs: `logs/backtest_runs/oos2_20241101_1201_htf_off_trailing/trade_logs.csv`
- `shock_m5_pips=20`
- `shock_m15_pips=35`
- `atr_window=14`
- `atr_median_window=50`
- `atr_ratio_threshold=2.0`
- `range_ratio_threshold=2.5`
- `cooldown_after_shock=60`
- `cooldown_after_volatility_spike=45`
- `instrument=USDJPY`
- `pip_size=0.01`

## 2. 初回結果
- halt_window_count=87
- total_halt_minutes=9215.0
- halted_entry_count=23
- halt_reason_counts=price_shock_halt:44|volatility_spike_halt:75
- avoided_loss_pips=0.10
- missed_profit_pips=16.87
- net_counterfactual_effect_pips=-16.77
- trade_count_reduction=23
- warning: decision_logs missing required columns and skipped: ['entry_time', 'signal_type']

## 3. 解釈
- 初期閾値では halt が広く効きすぎている可能性が高い。
- 停止対象の内訳は、負け回避より利益機会停止が大きい。
- `volatility_spike_halt` の発火数が多く、過剰停止の主因候補。

## 4. 判断
- 現時点では Phase 3 本体統合に進まない。
- まず Phase 2 内で停止要因を分解診断する。

## 5. 次タスク
1. `price_shock_halt` 単独診断。
2. `volatility_spike_halt` 単独診断。
3. halt_reason 別 halted entry 損益分解。
4. cooldown 時間の影響診断。
5. 分解診断後に Phase 3 統合可否を判断。

## 6. 注意
- これは構造診断であり、収益性確認ではない。
- 閾値は初期仮説であり、本採用値ではない。
- この記録では閾値変更・本体統合は実施していない。
