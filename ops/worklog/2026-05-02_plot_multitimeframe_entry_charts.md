# 2026-05-02 Plot Multi-Timeframe Entry Charts

## 目的
Q1 backtest の entry timing とトレンド認識を目視確認するため、M5 実行パネルに加えて M5 から再構成した H1/H4 を参考表示するマルチタイムフレーム可視化スクリプトを追加した。

## 実施内容
- `scripts/plot_backtest_entries_multitimeframe.py` を新規追加。
- 入力引数を実装。
  - `--price-csv`
  - `--trade-logs`
  - `--output-dir`
  - `--before-bars`
  - `--after-bars`
  - `--max-charts`
  - `--trade-index` (optional)
- M5 から H1/H4 を再集約（visual reference only）。
  - open: first
  - high: max
  - low: min
  - close: last
  - volume: sum
  - spread: last
- 1トレード1画像で 3 段パネル表示。
  - H4 reference panel
  - H1 reference panel
  - M5 execution panel
- 各パネルで以下を描画。
  - entry_time
  - exit_time
  - recent_third_timestamp
  - long_entry / short_entry の区別
- M5 execution panel のみ以下を追加表示。
  - stop_loss
  - take_profit
- title 注記に以下を必ず表示。
  - `H1/H4 are visual references only; current backtest decision used M5-derived pipeline window.`
  - signal_type, entry_time, exit_reason, pnl, temporal_lag_bars, structure_source
- 出力を以下で保存。
  - `mtf_chart_0001.png` ...
  - `mtf_chart_index.csv`
- `mtf_chart_index.csv` に以下列を出力。
  - chart_file
  - trade_index
  - signal_type
  - entry_time
  - exit_time
  - recent_third_timestamp
  - temporal_lag_bars
  - exit_reason
  - pnl
  - structure_source
  - note_visual_reference_only

## 実行確認
- コマンド:
  - `$env:PYTHONPATH='.'`
  - `python scripts/plot_backtest_entries_multitimeframe.py --price-csv data/private/backtest_slices/USDJPY_M5_2024-01-02_2024-04-01.csv --trade-logs logs/backtest_runs/usdjpy_m5_2024_0102_0401_lb5_dedup1_no_fallback/trade_logs.csv --output-dir logs/backtest_runs/usdjpy_m5_2024_0102_0401_lb5_dedup1_no_fallback/mtf_charts --before-bars 40 --after-bars 20 --max-charts 30`
- 生成:
  - PNG 30枚
  - index 30行

## テスト
- `$env:PYTHONPATH='.'`
- `pytest -q`
- 結果: `207 passed`

## 影響範囲
- 売買ロジック変更なし
- `BacktestRunner` / `PipelineAdapter` 変更なし
- 実 broker / OANDA API / 実注文送信の実装なし
