# 2026-05-17 htf accepted/rejected entry set representative run result

## 実行目的
- `scripts/run_htf_diagnostic_comparison.py` に追加した candidate / accepted / htf_rejected entry set summary の実出力を representative 入力で確認する。
- 本確認は near_live diagnostic comparison の説明可能性確認であり、HTF filter本体採用・ON化判断ではない。

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
  --output-dir tmp/htf_diagnostic_comparison_acc_rej_rep_20260517 `
  --run-id htf_diag_cmp_acc_rej_rep_20260517 `
  --warmup-start 2024-01-01T00:00:00Z `
  --replay-start 2024-01-01T01:00:00Z `
  --replay-end 2024-01-01T04:00:00Z `
  --expected-timeframe-minutes 5
```

## 出力先
- `tmp/htf_diagnostic_comparison_acc_rej_rep_20260517/`
- 条件別:
  - `htf_off/near_live_decision_logs.csv`
  - `htf_permissive/near_live_decision_logs.csv`
  - `htf_strict/near_live_decision_logs.csv`
- 比較summary:
  - `htf_diagnostic_comparison_summary.csv`
  - `htf_diagnostic_comparison_summary.md`

## 3条件のsummary要点
- 共通:
  - `replay_bar_count=36`
  - `decision_log_count=36`
  - `entry_signal_true_count=34`
  - `trade_ok_true_count=34`
  - `real_order_sent_count=0`
  - `no_real_order_integrity_violation_count=0`
- `htf_off`:
  - `htf_filter_rejected_count=0`
  - candidate:
    - `entry_set_count=34`
    - `entry_set_removed_vs_htf_off_count=0`
    - `entry_set_added_vs_htf_off_count=0`
  - accepted:
    - `accepted_entry_set_count=34`
    - `accepted_entry_set_removed_vs_htf_off_count=0`
    - `accepted_entry_set_added_vs_htf_off_count=0`
  - htf_rejected:
    - `htf_rejected_entry_set_count=0`
    - `htf_rejected_entry_set_vs_htf_off_added_count=0`
    - `htf_rejected_entry_set_vs_htf_off_intersection_count=0`
- `htf_permissive`:
  - `htf_filter_rejected_count=2`
  - candidate:
    - `entry_set_count=34`
    - `entry_set_removed_vs_htf_off_count=0`
    - `entry_set_added_vs_htf_off_count=0`
  - accepted:
    - `accepted_entry_set_count=34`
    - `accepted_entry_set_removed_vs_htf_off_count=0`
    - `accepted_entry_set_added_vs_htf_off_count=0`
  - htf_rejected:
    - `htf_rejected_entry_set_count=0`
    - `htf_rejected_entry_set_vs_htf_off_added_count=0`
    - `htf_rejected_entry_set_vs_htf_off_intersection_count=0`
- `htf_strict`:
  - `htf_filter_rejected_count=2`
  - candidate:
    - `entry_set_count=34`
    - `entry_set_removed_vs_htf_off_count=0`
    - `entry_set_added_vs_htf_off_count=0`
  - accepted:
    - `accepted_entry_set_count=34`
    - `accepted_entry_set_removed_vs_htf_off_count=0`
    - `accepted_entry_set_added_vs_htf_off_count=0`
  - htf_rejected:
    - `htf_rejected_entry_set_count=0`
    - `htf_rejected_entry_set_vs_htf_off_added_count=0`
    - `htf_rejected_entry_set_vs_htf_off_intersection_count=0`

## candidate / accepted / htf_rejected の差分関係
- candidate set（`entry_signal==True`）は3条件で同一だった。
- accepted set（`entry_signal==True && trade_ok==True`）も3条件で同一だった。
- htf_rejected set（`entry_signal==True && htf_filter_rejected==True`）は3条件とも0件だった。

## `htf_filter_rejected_count` との整合性
- permissive/strict で `htf_filter_rejected_count=2` に対し、`htf_rejected_entry_set_count=0`。
- 現行定義では `htf_rejected_entry_set` は `entry_signal==True` を必要とするため、`entry_signal==False` の行で発生したHTF rejectionは集合に入らない。
- このため、`htf_filter_rejected_count` と `htf_rejected_entry_set_count` は一致を保証しない。

## `htf_filter_rejected` 列不在時の fallback
- 今回の集計では `htf_filter_rejected` 列が無い場合、既存方針どおり `htf_filter_enabled && !htf_direction_aligned` を proxy として使用する。

## 解釈
- candidate entry set が同一のため、今回データでは HTF は候補生成ではなく後段判定側に影響している可能性がある。
- accepted entry set が変わらず、かつ htf_rejected entry set も0だったため、少なくとも本runでは HTF rejection が `entry_signal==True` な集合にも `trade_ok` 集合にも反映していない可能性がある。
- これは収益性評価ではない。
- HTF filter採用判断ではない。
