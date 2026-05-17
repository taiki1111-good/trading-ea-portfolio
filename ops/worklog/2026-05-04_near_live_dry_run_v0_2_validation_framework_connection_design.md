# 2026-05-04 near-live dry-run v0.2 validation framework connection design

## Summary
- Phase 9 CSV replay dry-run summary を、Phase 8 Validation Framework v0.2 の period summary / diagnostic summary に接続する設計方針を文書化した。
- 本設計は収益性評価ではなく、operational readiness / dry-run health 評価として扱う。
- 今回は文書更新のみであり、コード変更・テスト変更は実施していない。

## Purpose
- `near_live_summary.csv` / `near_live_validation_warnings.csv` の既存出力を、Validation Framework側で再利用できる評価観点に整理する。
- dry-run特有の整合性（ログ完全性・placeholder整合・時刻整合・warning分類）を status 化する。

## Connection targets
- primary:
  - `near_live_summary.csv`
  - `near_live_validation_warnings.csv`
- optional future references:
  - `near_live_decision_logs.csv`
  - `near_live_state_logs.csv`
  - `near_live_event_logs.csv`

## Validation categories
1. log completeness
   - `decision_log_count == replay_bar_count` を必須候補。
   - `state_log_count == replay_bar_count` は将来候補。
   - warning/event logs 出力欠落を許容しない。
2. data quality warning summary
   - `warning_count`
   - `duplicate_bar_count`
   - `out_of_order_count`
   - `data_gap_count`
   - `expected_weekend_gap_count`
   - `ordinary_missing_bar_gap_count`
   - `unknown_gap_count`
3. dry-run placeholder integrity
   - `entry_signal=False`
   - `exit_signal=False`
   - `trade_ok=False`
   - `paper_order_action=none`
   - `paper_position_state=flat`
4. time consistency
   - UTC timestamp 基準。
   - warmup/replay split 整合。
   - `replay_start <= timestamp < replay_end`。
   - previous/current timestamp 順序整合。

## dry-run health status proposal
- `status=pass`
- `status=warn`
- `status=investigate`
- `status=no_go_candidate`

初期判定案:
- `pass`
  - `warning_count=0`
  - log completeness OK
  - placeholder integrity OK
- `warn`
  - `expected_weekend_gap` のみ
  - log completeness OK
  - placeholder integrity OK
- `investigate`
  - `ordinary_missing_bar_gap` / `unknown_gap` あり
  - duplicate/out_of_order あり
- `no_go_candidate`
  - `decision_log_count != replay_bar_count`
  - UTC/time order破綻
  - placeholder integrity破綻
  - unexplained gaps 多発

## Go / No-Go candidate rules
- duplicate/out_of_order は高優先調査。
- ordinary_missing_bar_gap / unknown_gap は調査対象。
- expected_weekend_gap 単独は No-Go にしない。
- `decision_log_count != replay_bar_count` は No-Go候補。
- placeholder integrity 破綻は No-Go候補。

## Output candidates (design only)
- `dry_run_period_summary.csv`
- `dry_run_period_summary.md`
- `dry_run_warning_summary.csv`
- `dry_run_health_check.csv`

## Out of scope (this work)
- `scripts/run_csv_replay_dry_run.py` 変更なし。
- tests 変更なし。
- BacktestRunner / PipelineAdapter 変更なし。
- Signal / RiskFilter / Execution 変更なし。
- 売買ロジック変更なし。
- OANDA/API接続なし、実注文・デモ注文なし。

## Next step candidates
1. 本設計の文書レビュー。
2. dry-run summary 変換（period/warning/health）最小実装の要否判断。
3. 必要時のみ後処理スクリプトで接続し、PipelineAdapter責務とは分離維持。
