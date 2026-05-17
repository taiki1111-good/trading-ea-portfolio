# 2026-05-04 near-live dry-run v0.2 pipeline dry-run I/O contract design

## Summary
- Option A（別スクリプト分離）を採用前提として、`CSV replay pipeline dry-run` のI/O契約と追加ログ列候補を実装前に固定した。
- 今回は設計文書更新のみで、コード・テスト・売買ロジックは未変更。
- 現行skeletonは維持し、新規 `scripts/run_csv_replay_pipeline_dry_run.py` は次段階で最小実装する方針。

## New script proposal
- `scripts/run_csv_replay_pipeline_dry_run.py`（今回は未作成）

## Role definition
- CSV replay / warmup-replay split / data quality warning / gap classification は現行skeletonと同一責務で維持。
- replay bars のdecision/state処理では PipelineAdapter を呼ぶ。
- 実注文・デモ注文は行わず、paper-only/no-real-order 前提でログ出力する。

## Input contract (design freeze)
- CSV required columns:
  - `timestamp`, `open`, `high`, `low`, `close`
- CSV optional columns:
  - `volume`, `spread_pips`, `source`, `data_valid_flag`
- CLI baseline:
  - `--input-csv`, `--output-dir`, `--run-id`, `--warmup-start`, `--replay-start`, `--replay-end`, `--expected-timeframe-minutes`
- CLI additional candidates:
  - `--symbol`, `--timeframe`, `--pipeline-config`, `--max-bars`（or `--max-replay-bars`）
- 最小実装では追加引数を絞る。

## Output contract (design freeze)
- 既存出力を維持:
  - `near_live_decision_logs.csv`
  - `near_live_event_logs.csv`
  - `near_live_state_logs.csv`
  - `near_live_validation_warnings.csv`
  - `near_live_summary.csv`
  - `near_live_summary.md`
- 追加候補:
  - `near_live_pipeline_trace_logs.csv`（任意）

## Additional log fields candidates
- decision:
  - `pipeline_mode`, `pipeline_adapter_called`, `pipeline_adapter_status`
  - `pipeline_error_type`, `pipeline_error_message`
  - `htf_context_status`, `ltf_structure_status`, `signal_status`, `risk_filter_status`
  - `entry_signal`, `exit_signal`, `signal_type`, `signal_reason`, `trade_ok`, `filter_reason`
  - `lot`, `stop_loss`, `take_profit`
  - `paper_order_action`, `real_order_sent`, `broker_order_id`, `no_real_order_integrity_ok`
- state:
  - `pipeline_mode`, `pipeline_adapter_last_status`
  - `last_pipeline_error_type`, `last_pipeline_error_message`
  - `paper_position_state`, `real_order_sent`, `no_real_order_integrity_ok`
- event:
  - `pipeline_adapter_error`, `pipeline_adapter_skipped`
  - `no_real_order_integrity_violation`, `pipeline_output_schema_error`
- summary:
  - `pipeline_adapter_called_count`, `pipeline_adapter_error_count`
  - `entry_signal_true_count`, `exit_signal_true_count`, `trade_ok_true_count`
  - `paper_order_candidate_count`, `real_order_sent_count`
  - `no_real_order_integrity_violation_count`, `pipeline_dry_run_health_status`

## Integrity policy migration
- skeleton版は placeholder integrity（`entry_signal=False` 全行固定）を維持。
- pipeline版は placeholder integrity を使わず、`no_real_order_integrity` を使用。
- pipeline版期待値:
  - `real_order_sent=False`
  - `broker_order_id` 空欄
  - `paper_order_action` は `none` / `paper_candidate` のみ
  - broker/API送信副作用なし

## Go/No-Go candidates for pipeline dry-run
- `no_go_candidate`:
  - `real_order_sent_count > 0`
  - `no_real_order_integrity_violation_count > 0`
  - `pipeline_adapter_error_count` が一定以上
  - `decision_log_count != replay_bar_count`
- `investigate`:
  - pipeline error 少数
  - schema error
  - `ordinary_missing_bar_gap` / `unknown_gap`
- `warn`:
  - expected_weekend_gap only
  - `pipeline_adapter_error_count=0`
  - no-real-order integrity OK
- `pass`:
  - warningなし
  - `pipeline_adapter_error_count=0`
  - no-real-order integrity OK

## Pre-implementation checks
- PipelineAdapter 現在の入力契約確認（bars/windowの渡し方）
- `bars[:i+1]` 参照のみで future leak を防げるか
- HTF/LTF/Signal/RiskFilter の出力スキーマ確認
- 例外時方針（最小候補: event記録し、当該barは `pipeline_adapter_status=error` で継続）

## Out of scope in this step
- コード変更・テスト変更
- BacktestRunner / PipelineAdapter / Signal / RiskFilter / Execution 変更
- 売買ロジック変更
- OANDA/API接続、実注文、デモ注文
