# 2026-05-16 htf diagnostic comparison representative run result

## 実行目的
- `scripts/run_htf_diagnostic_comparison.py` の最小runnerで、`htf_off` / `htf_permissive` / `htf_strict` の3条件比較が representative 入力で再現可能に実行できることを確認する。
- 本確認は diagnostic comparison の運用確認であり、本体HTF filter採用判断ではない。

## 使用入力
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
  --output-dir tmp/htf_diagnostic_comparison_rep_20260516 `
  --run-id htf_diag_cmp_rep_20260516 `
  --warmup-start 2024-01-01T00:00:00Z `
  --replay-start 2024-01-01T01:00:00Z `
  --replay-end 2024-01-01T04:00:00Z `
  --expected-timeframe-minutes 5
```

## 出力先
- `tmp/htf_diagnostic_comparison_rep_20260516/`
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
  - `decision_log_count=36`（3条件とも整合）
  - `entry_signal_true_count=34`
  - `trade_ok_true_count=34`
  - `htf_direction_aligned_count=34`
  - `htf_against_entry_count=2`
  - `neutral_passed_count=0`
  - `neutral_rejected_count=1`
- 条件差分:
  - `htf_off`:
    - `htf_filter_enabled=False`
    - `htf_filter_rejected_count=0`
  - `htf_permissive`:
    - `htf_filter_enabled=True`
    - `htf_neutral_policy=permissive`
    - `htf_filter_rejected_count=2`
  - `htf_strict`:
    - `htf_filter_enabled=True`
    - `htf_neutral_policy=strict`
    - `htf_filter_rejected_count=2`
- `htf_filter_rejected_by_reason` は文字列reason countsとして出力されることを確認した。

## no-real-order 安全性確認
- 3条件すべてで:
  - `real_order_sent_count=0`
  - `no_real_order_integrity_violation_count=0`

## `htf_against_entry_count` の v0 定義限界
- 本runでは v0 の保守的仮集計として、`htf_direction_aligned == False` 件数を `htf_against_entry_count` に使用。
- 厳密な entry集合差分（`timestamp + signal_type` など）に基づく定義ではない。

## PnL系非対応（今回）
- `win_rate` / `average_pnl` / `total_pnl` / `exit_reason counts` は near_live単体で扱わない。
- 本結果は収益性評価ではなく、HTF条件差分の構造比較用記録。

## 生成物のGit管理
- 出力は `tmp/` 配下に生成し、Git管理外のまま運用。

## 次に進む判断
- 次フェーズは `entry集合差分（timestamp + signal_type）` の追加設計要否判断へ進む。
