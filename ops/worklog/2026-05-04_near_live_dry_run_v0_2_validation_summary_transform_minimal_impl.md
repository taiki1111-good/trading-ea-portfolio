# 2026-05-04 near-live dry-run v0.2 validation summary transform minimal implementation

## Summary
- `near_live_summary.csv` / `near_live_validation_warnings.csv` を Validation Framework 接続用に変換する最小スクリプトを実装した。
- 出力は `dry_run_period_summary.csv` / `dry_run_period_summary.md` / `dry_run_warning_summary.csv` の3点。
- 収益性評価ではなく、operational readiness / dry-run health の要約を目的とする。

## Implemented files
- `scripts/summarize_csv_replay_dry_run.py`
- `tests/unit/backtest/test_summarize_csv_replay_dry_run.py`

## Implemented behavior
- 入力:
  - 必須: `near_live_summary.csv`, `near_live_validation_warnings.csv`
  - 任意: `near_live_decision_logs.csv`, `near_live_state_logs.csv`, `near_live_event_logs.csv`（今回は未使用）
- health判定:
  1. `no_go_candidate`: `decision_log_count != replay_bar_count`
  2. `investigate`: duplicate / out_of_order / ordinary_missing_bar_gap / unknown_gap のいずれか
  3. `warn`: warningあり かつ `expected_weekend_gap` のみ
  4. `pass`: warningなし かつ log completeness OK
- warning summary:
  - `warning_type` / `gap_class` / `expected_gap_flag` / `gap_requires_investigation` の別count

## Notes
- placeholder integrity（`entry_signal=False` 等）の詳細判定は今回未実装。
- 将来候補として `near_live_decision_logs.csv` を参照する追加監査を保持。
- BacktestRunner / PipelineAdapter / 売買ロジックは未変更。
- OANDA/API接続、実注文、デモ注文は未実施。

## Representative M5 run result (2026-05-04)
実行コマンド:
- `python scripts/summarize_csv_replay_dry_run.py --input-dir outputs/near_live/csv_replay/2024-01-03_to_2024-01-09_gap_classified --output-dir outputs/near_live/csv_replay/2024-01-03_to_2024-01-09_gap_classified_summary`

実行結果:
- `run_id=near_live_csv_replay_usdjpy_m5_2024_01_03_to_2024_01_09_gap_classified`
- `dry_run_health_status=warn`
- `status_reason=expected_weekend_gap_only`

`dry_run_period_summary.csv` 確認値:
- `replay_bar_count=1151`
- `decision_log_count=1151`
- `warning_count=1`
- `duplicate_bar_count=0`
- `out_of_order_count=0`
- `data_gap_count=1`
- `expected_weekend_gap_count=1`
- `ordinary_missing_bar_gap_count=0`
- `unknown_gap_count=0`
- `log_completeness_ok=True`
- `data_quality_status=warn`

`dry_run_warning_summary.csv` 確認値:
- `warning_type=data_gap: 1`
- `gap_class=expected_weekend_gap: 1`
- `expected_gap_flag=true: 1`
- `gap_requires_investigation=false: 1`

解釈:
- 今回のwarningは `expected_weekend_gap` のみであり、初期ルールに従い `warn` 判定となった。
- 収益性確認ではなく、dry-run運用整合性の要約結果として記録する。

## Recording update (2026-05-04)
- 上記 Representative M5 結果を以下へ反映:
  - `docs/17_backtest_design.md`（Phase 9記録セクション追記）
  - `ops/CURRENT_TASKS.md`（次タスク更新）
