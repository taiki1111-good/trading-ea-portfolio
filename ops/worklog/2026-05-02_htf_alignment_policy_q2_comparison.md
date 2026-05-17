# 2026-05-02 HTF Alignment Policy Q2 Comparison

## 概要
- 対象: Q2（2024-04/05/06）HTF alignment policy comparison
- 比較軸:
  - OFF / permissive / strict
  - fixed_sl_tp / simple_trailing_after_1R
- 位置づけ: 構造検証（収益性確認ではない）
- 前提:
  - spread=0.2 pips fallback
  - 手数料・スリッページ・スワップ未反映
  - 実 broker / OANDA API / 実注文送信は未実装
  - HTF v1 は H1 only + direction alignment only
  - `simple_trailing_after_1R` は experimental exit candidate（本採用ではない）

## Q2比較結果（ユーザー実行結果の整理）
| month | OFF fixed | OFF trailing | permissive fixed | permissive trailing | strict fixed | strict trailing |
|---|---:|---:|---:|---:|---:|---:|
| 2024-04 trade_count | 80 | 80 | 84 | 84 | 80 | 80 |
| 2024-04 total_pnl | -0.0260 | 0.0621 | -0.0210 | 0.0689 | -0.0260 | 0.0621 |
| 2024-05 trade_count | 72 | 72 | 76 | 76 | 72 | 72 |
| 2024-05 total_pnl | -0.0270 | 0.0870 | -0.0280 | 0.0962 | -0.0270 | 0.0870 |
| 2024-06 trade_count | 59 | 59 | 62 | 62 | 59 | 59 |
| 2024-06 total_pnl | -0.0140 | 0.0582 | -0.0110 | 0.0634 | -0.0140 | 0.0582 |

## 観察
- Q2の4月・5月・6月すべてで strict は OFF と一致。
- permissive は全月で trade_count を増やした（neutral 通過 policy）。
- permissive + trailing は全月で OFF/strict + trailing を上回った。
- permissive + fixed は 2024-05 で OFF/strict より悪化し、単独採用判断は不可。
- 以上は構造検証上の比較結果であり、本採用判断や収益性確認ではない。

## 集計手順（entry集合差分）
- 重い backtest 実行は行わず、既存 run ディレクトリの `trade_logs.csv` / `decision_logs.csv` から差分集計する。
- 推奨スクリプト:
  - `scripts/compare_htf_alignment_policy_runs.py`
- 最低限の出力列:
  - `base_run_id`
  - `compare_run_id`
  - `base_trade_count`
  - `compare_trade_count`
  - `common_count`
  - `compare_only_count`
  - `base_only_count`
  - `shifted_5min_count`
  - `neutral_passed_count`
  - `neutral_rejected_count`
  - `total_pnl_diff`
  - `notes`

### 実行例
```powershell
$env:PYTHONPATH='.'
python scripts/compare_htf_alignment_policy_runs.py `
  --base-run-dir logs/backtest_runs/<q2_month_off_trailing_run> `
  --compare-run-dir logs/backtest_runs/<q2_month_permissive_trailing_run> `
  --compare-run-dir logs/backtest_runs/<q2_month_strict_trailing_run> `
  --output-csv logs/backtest_runs/<comparison_dir>/entry_set_diff_q2_trailing.csv `
  --output-md logs/backtest_runs/<comparison_dir>/entry_set_diff_q2_trailing.md
```

## neutral count 集計定義（更新）
- `neutral_passed_count`:
  - `htf_filter_enabled=True`
  - `htf_bias=neutral`
  - `htf_neutral_policy=permissive`
  - `htf_direction_aligned=True`
  - `entry_signal=True` または `trade_ok=True`
- `neutral_rejected_count`:
  - `htf_filter_enabled=True`
  - `htf_bias=neutral`
  - `htf_neutral_policy=strict`
  - `htf_direction_aligned=False`
  - `fail_stage` / `decision_reason` / `htf_filter_reason` から HTF rejection を追跡できる行
- 注記: `decision_reason` の `neutral_passed` / `neutral_rejected` 固定文字列には依存しない。

## Q2既存ログの再集計コマンド例（backtest再実行なし）
```powershell
$env:PYTHONPATH='.'
python scripts/compare_htf_alignment_policy_runs.py `
  --base-run-dir logs/backtest_runs/<2024-04_off_trailing_run> `
  --compare-run-dir logs/backtest_runs/<2024-04_permissive_trailing_run> `
  --compare-run-dir logs/backtest_runs/<2024-04_strict_trailing_run> `
  --output-csv logs/backtest_runs/<comparison_dir>/entry_set_diff_2024-04_trailing.csv `
  --output-md logs/backtest_runs/<comparison_dir>/entry_set_diff_2024-04_trailing.md

python scripts/compare_htf_alignment_policy_runs.py `
  --base-run-dir logs/backtest_runs/<2024-05_off_trailing_run> `
  --compare-run-dir logs/backtest_runs/<2024-05_permissive_trailing_run> `
  --compare-run-dir logs/backtest_runs/<2024-05_strict_trailing_run> `
  --output-csv logs/backtest_runs/<comparison_dir>/entry_set_diff_2024-05_trailing.csv `
  --output-md logs/backtest_runs/<comparison_dir>/entry_set_diff_2024-05_trailing.md

python scripts/compare_htf_alignment_policy_runs.py `
  --base-run-dir logs/backtest_runs/<2024-06_off_trailing_run> `
  --compare-run-dir logs/backtest_runs/<2024-06_permissive_trailing_run> `
  --compare-run-dir logs/backtest_runs/<2024-06_strict_trailing_run> `
  --output-csv logs/backtest_runs/<comparison_dir>/entry_set_diff_2024-06_trailing.csv `
  --output-md logs/backtest_runs/<comparison_dir>/entry_set_diff_2024-06_trailing.md
```
