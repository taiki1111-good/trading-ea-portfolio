# 2026-05-03 Halt Diagnostic OOS-2 2024-11 分離診断結果

## 概要
- 対象: OOS-2 2024-11 OFF trailing
- 目的: `price_shock_halt` / `volatility_spike_halt` の分離診断結果を記録し、Phase 3 本体統合の Go/No-Go を明文化する。
- 注意: これは構造診断記録であり、収益性確認ではない。閾値本採用を意味しない。

## 実行条件（固定）
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

## 分離診断結果

| scenario | enabled_filters | halt_window_count | total_halt_minutes | halted_entry_count | halt_reason_counts | avoided_loss_pips | missed_profit_pips | net_counterfactual_effect_pips | trade_count_reduction |
| --- | --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: |
| combined | price_shock_halt + volatility_spike_halt | 87 | 9215.0 | 23 | price_shock_halt:44\|volatility_spike_halt:75 | 0.10 | 16.87 | -16.77 | 23 |
| price_shock only | price_shock_halt | 44 | 5495.0 | 11 | price_shock_halt:44 | 0.00 | 6.07 | -6.07 | 11 |
| volatility_spike only | volatility_spike_halt | 81 | 7040.0 | 17 | volatility_spike_halt:81 | 0.10 | 13.42 | -13.32 | 17 |

## 解釈
- 初期閾値では combined / price_shock only / volatility_spike only の全シナリオで `net_counterfactual_effect_pips` がマイナス。
- `price_shock_halt` 単独でも `missed_profit_pips` が優位で、利益機会停止が残る。
- `volatility_spike_halt` は発火数・停止時間・`missed_profit_pips` が大きく、過剰停止の主因候補。
- combined は停止窓重なりにより `total_halt_minutes` がさらに増える。

## 判断（Phase 3 Go/No-Go）
- **No-Go**: 初期閾値のままでは Phase 3 Halt/Risk integration に進まない。
- 閾値変更を即時実施せず、Phase 2 diagnostic scenario として比較設計を先行する。

## 次タスク
1. Phase 3 Go/No-Go 基準の定義。
2. cooldown 影響診断の設計。
3. `volatility_spike_halt` の過剰発火要因分析。
4. threshold/cooldown 候補比較を行う場合は Phase 2 diagnostic scenario として固定。
5. Phase 3 統合は保留。
