# 2026-05-02 M1 Exit Replay Rule Comparison

## 実施目的
- M1 replay で `simple_trailing_after_1R` 単体結果のみでは判断できないため、
  baseline / trailing variants を同一条件で比較する。

## 実施内容
- 同条件で4ルールを実行
  - `baseline_fixed_exit`
  - `simple_trailing_after_1R`
  - `simple_trailing_after_1R_conservative`
  - `simple_trailing_after_1R_next_bar_activation`
- 追加スクリプト:
  - `scripts/compare_m1_exit_replay_results.py`
- 比較出力:
  - `m1_exit_replay_comparison.csv`
  - `m1_exit_replay_comparison.md`

## 共通条件
- M1 DAT: `data/raw/dukascopy/USDJPY/M1/dat_csv_candidates/DAT_MT_USDJPY_M1_2024.csv`
- trade logs: `logs/backtest_runs/usdjpy_m5_2024_0102_0401_lb5_dedup1_no_fallback/trade_logs.csv`
- `max_holding_minutes=50`
- `spread_pips=0.2`

## 注意
- spread=0.2 pips fallback 前提
- 手数料・スリッページ・スワップ未反映
- 収益性評価ではなく構造検証
