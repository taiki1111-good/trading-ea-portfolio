# 2026-05-02 temporal repro check next week

## 実施内容
- DAT年次CSVから 2024-01-09〜2024-01-16 のM5スライスを生成。
- PriceDataLoader で読込確認（bar_count/start/end/invalid_ohlc）。
- lookback=5 + fallback OFF + dedup=1 で BacktestRunner 実行。
- analyze_backtest_run_logs.py で集計を生成。
- 既存週（2024-01-02〜2024-01-09）との比較を compare_temporal_lookback_runs.py で実施。
- pytest を実行して既存テスト回帰なしを確認。

## 生成物
- data/private/backtest_slices/USDJPY_M5_2024-01-09_2024-01-16.csv
- logs/backtest_runs/usdjpy_m5_2024_0109_0116_temporal_lb5_dedup1_no_fallback/*
- logs/backtest_runs/temporal_lb5_dedup1_repro_0102_0116/*

## 注意
- 収益性評価ではなく構造検証。
- spread=0.2 pips fallback 前提。
- 手数料・スリッページ・スワップ未反映。
- 実 broker / OANDA API / 実注文送信は未実装。
