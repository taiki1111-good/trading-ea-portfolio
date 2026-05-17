# 2026-05-03 near-live / dry-run v0.2 I/O Contract

## 1. 目的
- Phase 9 near-live / dry-run v0.2 実装前段階として、I/O契約と診断ポリシーを固定する。
- 実注文なしで、逐次bar処理時の判断・ログ整合性・時刻整合性・追跡可能性を確認する。
- 今回は設計契約の明文化のみを対象とし、dry-run本体実装は行わない。

## 2. 重要前提
- 実 broker / OANDA API / 実注文送信は未実装。
- デモ注文も送らない。
- 収益性確認済みではない。
- HTF/SR/Session/RiskStop は本体filter化せず、diagnostic/explanation/counterfactual layer として継続する。

## 3. 入力（初期方針）
- 初期優先は CSV replay input。
- OANDA stream/API は後続候補。
- 基本単位は M5 bars。
- `warmup bars` と `live/replay bars` を分離。
- 未確定barは使用しない。
- timestamp は UTC aware 必須。

### 3.1 入力列候補（CSV replay）
- `timestamp`
- `open`
- `high`
- `low`
- `close`
- `volume`
- `spread_pips`（optional）
- `source`
- `data_valid_flag`（optional）

## 4. dry-run mode 候補
- `csv_replay`
- `pseudo_stream`
- `oanda_dry_run_future`
- 初期設計対象は `csv_replay` のみ。

## 5. 状態管理候補
- `current_timestamp`
- `last_processed_timestamp`
- `warmup_ready_flag`
- `data_gap_flag`
- `duplicate_bar_flag`
- `out_of_order_flag`
- `paper_position_state`
- `pending_signal_state`
- `risk_stop_state`
- `halt_state`

## 6. 出力ログ候補
- `near_live_decision_logs.csv`
- `near_live_signal_logs.csv`
- `near_live_event_logs.csv`
- `near_live_state_logs.csv`
- `near_live_risk_logs.csv`
- `near_live_validation_warnings.csv`

### 6.1 near_live_decision_logs.csv 列候補
- `timestamp`
- `mode`
- `input_bar_status`
- `data_valid_flag`
- `warmup_ready_flag`
- `entry_signal`
- `exit_signal`
- `signal_type`
- `trade_ok`
- `decision_reason`
- `htf_v2_* fields`
- `sr_v2_* fields`
- `session_v2_* fields`
- `risk_stop_state`
- `halt_state`
- `paper_order_action`
- `paper_position_state`
- `warning_flags`

### 6.2 near_live_event_logs.csv 列候補
- `timestamp`
- `event_type`
- `severity`
- `message`
- `source`
- `recovery_action`
- `resolved_flag`

## 7. Diagnostic Policy
- 実注文しない。
- 約定したと断定しない。
- `paper_order_action` は仮想判断。
- backtest 完全一致は要求しない。
- 差分は、入力範囲・warmup・未確定bar・時刻境界・ログ列差分として説明する。
- ログ欠損・時刻不整合は No-Go 候補。

## 8. Go/No-Go 方針
- timestamp 重複・欠損・逆順を検知できない場合は No-Go。
- `decision_reason` が空欄になる場合は No-Go。
- warning 多発は No-Go。
- paper decision が追跡不能なら No-Go。
- OANDA/API 接続は csv_replay dry-run 安定後に検討。
- 実注文接続はさらに後段。

## 9. Validation Framework との接続
- dry-run summary を将来 validation input 化する。
- near_live logs を `validation_v0_2_summary` へ変換可能にする。
- validation `period_type` 候補に `dry_run_period` / `near_live_observed` を将来追加する。
- dry-run は収益性確認ではなく、運用整合性確認である。

## 10. 未解決事項
- csv_replay runner を新規scriptにするか、既存runnerを使うか。
- paper position 管理の粒度。
- exit 判定をどこまで再現するか。
- spread/slippage/swap を dry-run で扱うか。
- warnings の重大度定義。
- dry-run ログ保存場所。
- OANDA 接続の導入条件。
- near-live から demo order へ進む条件。

## 11. 注意
- 本記録は I/O 契約固定であり、OANDA/API接続・実注文・デモ注文・dry-run本体実装・Runner変更・売買ロジック変更・閾値変更を含まない。
