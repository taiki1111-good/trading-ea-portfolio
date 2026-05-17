# 2026-05-03 near-live dry-run v0.2 CSV replay 1day result

## 1. 目的
- Phase 9 CSV replay dry-run skeleton を代表M5 sliceでローカル実行し、時刻整合性・ログ完全性を確認する。
- 本記録は実行結果記録のみであり、コード変更やロジック変更は行わない。

## 2. 使用データ
- 入力CSV:
  - `data/private/backtest_slices/USDJPY_M5_2024-01-02_2024-01-09.csv`
- 列:
  - `timestamp, open, high, low, close, spread, volume`
- 前提:
  - `spread=0.2 pips fixed fallback`
  - 構造確認・dry-run skeleton確認用途
  - 運用近似スプレッド検証・収益性確認用途ではない

## 3. 実行コマンド
```powershell
$env:PYTHONPATH='.'
python scripts/run_csv_replay_dry_run.py `
  --input-csv data/private/backtest_slices/USDJPY_M5_2024-01-02_2024-01-09.csv `
  --output-dir outputs/near_live/csv_replay/2024-01-03_1day `
  --run-id near_live_csv_replay_usdjpy_m5_2024_01_03_1day `
  --warmup-start 2024-01-02T00:00:00Z `
  --replay-start 2024-01-03T00:00:00Z `
  --replay-end 2024-01-04T00:00:00Z `
  --expected-timeframe-minutes 5
```

## 4. 結果
- `run_id=near_live_csv_replay_usdjpy_m5_2024_01_03_1day`
- `mode=csv_replay`
- `warmup_bar_count=288`
- `replay_bar_count=288`
- `warning_count=0`
- `duplicate_bar_count=0`
- `data_gap_count=0`
- `out_of_order_count=0`
- `decision_log_count=288`

## 5. ログ整合確認
- decision logs first timestamp:
  - `2024-01-03T00:00:00+00:00`
- decision logs last timestamp:
  - `2024-01-03T23:55:00+00:00`
- placeholder整合:
  - `entry_signal=False`
  - `exit_signal=False`
  - `trade_ok=False`
  - `paper_order_action=none`
  - `decision_reason=csv_replay_skeleton:no_signal_no_trade`

## 6. 解釈
- 1日分 replay で、最小skeletonとしての時刻整合・ログ完全性は確認できた。
- warning 0件は当該slice/期間での入力品質記録として扱う。
- これは収益性確認ではない。

## 7. 注意
- 本記録は実行結果記録のみ。
- コード変更・売買ロジック変更・PipelineAdapter接続・OANDA/API接続・実注文/デモ注文は未実施。
