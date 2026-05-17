# 2026-05-04 near-live dry-run v0.2 placeholder integrity summary check

## Summary
- `scripts/summarize_csv_replay_dry_run.py` に placeholder integrity 詳細判定を最小追加した。
- `near_live_decision_logs.csv` は任意入力とし、存在時のみ判定する。
- 判定は Phase 9 csv_replay skeleton 用の整合監査であり、収益性確認ではない。

## Updated files
- `scripts/summarize_csv_replay_dry_run.py`
- `tests/unit/backtest/test_summarize_csv_replay_dry_run.py`
- `docs/17_backtest_design.md`
- `ops/CURRENT_TASKS.md`

## Added period summary fields
- `placeholder_integrity_checked`
- `placeholder_integrity_ok`
- `placeholder_violation_count`
- `entry_signal_true_count`
- `exit_signal_true_count`
- `trade_ok_true_count`
- `paper_order_action_non_none_count`
- `paper_position_state_non_flat_count`

## Placeholder integrity rule
期待値（全行）:
- `entry_signal=False`
- `exit_signal=False`
- `trade_ok=False`
- `paper_order_action=none`
- `paper_position_state=flat`

`near_live_decision_logs.csv` がない場合:
- `placeholder_integrity_checked=False`
- `placeholder_integrity_ok=not_checked`
- placeholder未確認のみでは No-Go にしない。

## Health decision priority
1. `decision_log_count != replay_bar_count`
   - `dry_run_health_status=no_go_candidate`
   - `status_reason=decision_log_count_mismatch`
2. `placeholder_integrity_checked=True` かつ `placeholder_integrity_ok=False`
   - `dry_run_health_status=no_go_candidate`
   - `status_reason=placeholder_integrity_violation`
3. duplicate / out_of_order / ordinary_missing / unknown
   - `dry_run_health_status=investigate`
4. expected_weekend_gap only
   - `dry_run_health_status=warn`
5. warningなし、log completeness OK、placeholder OKまたは未確認
   - `dry_run_health_status=pass`

## Tests
- `tests/unit/backtest/test_summarize_csv_replay_dry_run.py` に以下を追加:
  1. decision_logs が期待値どおり（checked=True, ok=True）
  2. `entry_signal=True` 1件（no_go_candidate）
  3. `paper_order_action != none` 1件（no_go_candidate）
  4. decision_logs なし（checked=False, ok=not_checked）
