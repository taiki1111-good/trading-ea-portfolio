# 2026-05-03 near-live / dry-run v0.2 CSV replay skeleton

## 1. 実装内容
- `scripts/run_csv_replay_dry_run.py` を新規追加。
- CSV replay dry-run skeleton として、UTC正規化・warmup/replay分離・逐次replay処理・warning検知・ログ出力を実装。
- 初期判定は placeholder（`entry_signal=False` / `exit_signal=False` / `trade_ok=False` / `paper_order_action=none`）。
- 実注文/OANDA/API接続/デモ注文/売買ロジック変更は未実装のまま維持。

## 2. 入力仕様
- CLI:
  - `--input-csv`
  - `--output-dir`
  - `--run-id`
  - `--warmup-start`
  - `--replay-start`
  - `--replay-end`
  - `--expected-timeframe-minutes`（default: 5）
- 必須列:
  - `timestamp`
  - `open`
  - `high`
  - `low`
  - `close`
- 任意列:
  - `volume`
  - `spread_pips`
  - `source`
  - `data_valid_flag`

## 3. 出力仕様
- `near_live_decision_logs.csv`
- `near_live_event_logs.csv`
- `near_live_state_logs.csv`
- `near_live_validation_warnings.csv`
- `near_live_summary.csv`
- `near_live_summary.md`

## 4. warning検知
- duplicate timestamp 検知。
- out-of-order timestamp（CSV原順）検知。
- expected timeframeとの差分による data gap 検知。
- warningは `near_live_validation_warnings.csv` と `near_live_event_logs.csv` に記録。

## 5. テスト結果
- `tests/unit/backtest/test_run_csv_replay_dry_run.py` を追加。
- 検証観点:
  - CLI引数parse
  - UTC正規化
  - warmup/replay分離
  - replay barsのみdecision logs出力
  - duplicate/data gap/out-of-order warning検知
  - decision_reason非空
  - summary csv/md出力
  - 必須列不足エラー

## 6. 未解決事項
- PipelineAdapterへの接続タイミングと責務境界。
- paper position管理粒度。
- exit判定再現の導入範囲。
- warning重大度ルールの細分化。
- dry-run summary の Validation Framework 取り込み仕様詳細。

## 7. 注意
- 本実装はCSV replay dry-run skeletonであり、収益性確認ではない。
