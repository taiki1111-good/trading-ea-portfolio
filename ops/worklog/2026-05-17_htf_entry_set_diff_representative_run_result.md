# 2026-05-17 htf entry set diff representative run result

## 実行目的
- `scripts/run_htf_diagnostic_comparison.py` に追加した entry集合差分summary（`timestamp + signal_type` 基準）の実出力を representative 入力で確認する。
- 本確認は near_live diagnostic comparison 用であり、HTF filter本体採用・ON化判断ではない。

## 使用入力（既存 representative と同一）
- `tests/fixtures/price_m5_h1_h4_base.csv`
- 期間:
  - `warmup_start=2024-01-01T00:00:00Z`
  - `replay_start=2024-01-01T01:00:00Z`
  - `replay_end=2024-01-01T04:00:00Z`
  - `expected-timeframe-minutes=5`

## 実行コマンド
```powershell
$env:PYTHONPATH='.'
python scripts/run_htf_diagnostic_comparison.py `
  --input-csv tests/fixtures/price_m5_h1_h4_base.csv `
  --output-dir tmp/htf_diagnostic_comparison_entry_set_rep_20260517 `
  --run-id htf_diag_cmp_entry_set_rep_20260517 `
  --warmup-start 2024-01-01T00:00:00Z `
  --replay-start 2024-01-01T01:00:00Z `
  --replay-end 2024-01-01T04:00:00Z `
  --expected-timeframe-minutes 5
```

## 出力先
- `tmp/htf_diagnostic_comparison_entry_set_rep_20260517/`
- 条件別:
  - `htf_off/near_live_decision_logs.csv`
  - `htf_permissive/near_live_decision_logs.csv`
  - `htf_strict/near_live_decision_logs.csv`
- 比較summary:
  - `htf_diagnostic_comparison_summary.csv`
  - `htf_diagnostic_comparison_summary.md`

## 新規entry集合差分summary（3条件）
- `htf_off`
  - `entry_set_count=34`
  - `entry_set_only_in_htf_off_count=0`
  - `entry_set_only_in_condition_count=0`
  - `entry_set_intersection_count=34`
  - `entry_set_removed_vs_htf_off_count=0`
  - `entry_set_added_vs_htf_off_count=0`
  - `htf_filter_rejected_count=0`
- `htf_permissive`
  - `entry_set_count=34`
  - `entry_set_only_in_htf_off_count=0`
  - `entry_set_only_in_condition_count=0`
  - `entry_set_intersection_count=34`
  - `entry_set_removed_vs_htf_off_count=0`
  - `entry_set_added_vs_htf_off_count=0`
  - `htf_filter_rejected_count=2`
- `htf_strict`
  - `entry_set_count=34`
  - `entry_set_only_in_htf_off_count=0`
  - `entry_set_only_in_condition_count=0`
  - `entry_set_intersection_count=34`
  - `entry_set_removed_vs_htf_off_count=0`
  - `entry_set_added_vs_htf_off_count=0`
  - `htf_filter_rejected_count=2`

## `htf_filter_rejected_count` との関係
- permissive / strict で `htf_filter_rejected_count` は非0（2）だが、`entry_set_removed_vs_htf_off_count` は0だった。
- このため、**entry_signal候補集合は同一だが、trade_ok/HTF rejection側で差が出ている可能性がある**。
- 今回の representative では `trade_ok_true_count` は3条件とも34で一致しており、entry集合差分が出ないケースを確認した。

## no-real-order 安全性確認
- 3条件すべてで:
  - `real_order_sent_count=0`
  - `no_real_order_integrity_violation_count=0`

## スコープ明記
- 本記録は entry集合差分の実出力確認のみ。
- PnL / win_rate / average_pnl / total_pnl / exit_reason counts は扱わない。
- 収益性評価ではない。
- HTF filter本体採用ではない。
