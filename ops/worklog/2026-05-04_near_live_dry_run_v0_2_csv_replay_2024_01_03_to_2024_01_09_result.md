# 2026-05-04 near-live dry-run v0.2 CSV replay multi-day result

## 1. 目的
- Phase 9 CSV replay dry-run skeleton の初回実データ確認として、1day結果に加えて複数日 replay 結果を記録する。
- weekend / market closure gap の取り扱い方針を明文化する。
- 本記録は記録更新のみであり、コード変更は行わない。

## 2. 再確認（1day）
- 対象: `2024-01-03T00:00:00Z` 〜 `2024-01-04T00:00:00Z`
- 結果: `warning_count=0`
- 解釈: 1day replay は正常完了。

## 3. 複数日 replay 実行
```powershell
$env:PYTHONPATH='.'
python scripts/run_csv_replay_dry_run.py `
  --input-csv data/private/backtest_slices/USDJPY_M5_2024-01-02_2024-01-09.csv `
  --output-dir outputs/near_live/csv_replay/2024-01-03_to_2024-01-09 `
  --run-id near_live_csv_replay_usdjpy_m5_2024_01_03_to_2024_01_09 `
  --warmup-start 2024-01-02T00:00:00Z `
  --replay-start 2024-01-03T00:00:00Z `
  --replay-end 2024-01-09T00:00:00Z `
  --expected-timeframe-minutes 5
```

## 4. 複数日 replay 結果
- `run_id=near_live_csv_replay_usdjpy_m5_2024_01_03_to_2024_01_09`
- `mode=csv_replay`
- `warmup_bar_count=288`
- `replay_bar_count=1151`
- `warning_count=1`
- `duplicate_bar_count=0`
- `data_gap_count=1`
- `out_of_order_count=0`
- `decision_log_count=1151`

## 5. warning 詳細
- `timestamp=2024-01-07T17:05:00+00:00`
- `warning_type=data_gap`
- `message=data gap detected: expected 0 days 00:05:00, got 2 days 00:10:00`

## 6. 取り扱い方針（現時点）
- 当該warningは通常欠損と即断せず、`weekend / market closure gap` 候補として扱う。
- 現時点では dry-run skeleton を No-Go 判定しない。
- ただし、休場説明と整合しない data_gap が多発する場合は No-Go 候補として再評価する。

## 7. 注意
- 本記録は実行結果の記録と運用方針の明文化のみ。
- コード変更、売買ロジック変更、PipelineAdapter接続、OANDA/API接続、実注文/デモ注文は未実施。
- 収益性確認ではない。
