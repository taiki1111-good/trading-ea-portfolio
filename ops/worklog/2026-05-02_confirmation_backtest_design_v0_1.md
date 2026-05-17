# 2026-05-02 Confirmation Backtest Design v0.1

## 目的
- Candidate Freeze v0.1 の次工程として、確認用バックテスト設計を明文化する。
- 本工程は収益性確認ではなく、候補を次段階に残す価値の確認を目的とする。

## 前提
- Q1/Q2 は探索・構造検証に使用済み期間として扱い、確認用評価から分離する。
- spread=0.2 pips fallback、手数料・スリッページ・スワップ未反映。
- 実 broker / OANDA API / 実注文送信は未実装。
- 確認用期間の結果を見ても、その場でルール変更しない。
- 変更が必要な場合は Candidate Freeze v0.2 として別管理する。
- 重いbacktestはユーザーがローカルPowerShellで実行する。

## OOS定義
- OOS-1（第一確認期間）: `2024-07-01` 〜 `2024-10-01`
- OOS-2（第二確認候補）: `2024-10-01` 〜 `2025-01-01`
- 実行順序: まず OOS-1 のみ実行する。

## 比較条件（4条件）
1. OFF + `fixed_sl_tp`
2. OFF + `simple_trailing_after_1R`
3. permissive + `fixed_sl_tp`
4. permissive + `simple_trailing_after_1R`

## 判定観点（合否基準）
- `simple_trailing_after_1R` が `fixed_sl_tp` より安定しているか
- permissive + trailing が OFF + trailing を上回るか、少なくとも大きく悪化しないか
- 月別偏りが強すぎないか
- `trade_count` が少なすぎないか
- schema validation / consistency が valid か
- entry集合差分、`neutral_passed_count`、`shifted_5min_count` を確認する
- 結果が悪い場合は即修正せず、v0.1棄却またはv0.2再設計候補として記録する

## 対象外（v0.1確認用BT主軸から除外）
- strict（Q2でOFF一致、将来の仕様比較候補として保持）
- H4 / support-resistance / H1&H4 aligned / H4 bias + H1 context
- 追加exit改造（swing-based trailing / trend-break exit）

## ローカル実行テンプレート（実行はユーザー側）
```powershell
$env:PYTHONPATH='.'

python scripts/run_backtest_exit_experiment.py --input-csv <oos1_m5_slice_csv> --run-id <oos1_off_fixed> --output-dir <out_off_fixed> --max-holding-bars 50 --exit-policy fixed_sl_tp --entry-time-mode m5_close --third-candidate-lookback-bars 5 --max-entries-per-recent-third-candidate 1 --disable-heuristic-fallback --start 2024-07-01 --end 2024-10-01
python scripts/run_backtest_exit_experiment.py --input-csv <oos1_m5_slice_csv> --run-id <oos1_off_trailing> --output-dir <out_off_trailing> --max-holding-bars 50 --exit-policy simple_trailing_after_1R --entry-time-mode m5_close --third-candidate-lookback-bars 5 --max-entries-per-recent-third-candidate 1 --disable-heuristic-fallback --start 2024-07-01 --end 2024-10-01
python scripts/run_backtest_exit_experiment.py --input-csv <oos1_m5_slice_csv> --run-id <oos1_perm_fixed> --output-dir <out_perm_fixed> --max-holding-bars 50 --exit-policy fixed_sl_tp --entry-time-mode m5_close --third-candidate-lookback-bars 5 --max-entries-per-recent-third-candidate 1 --disable-heuristic-fallback --htf-filter-enabled --htf-neutral-policy permissive --start 2024-07-01 --end 2024-10-01
python scripts/run_backtest_exit_experiment.py --input-csv <oos1_m5_slice_csv> --run-id <oos1_perm_trailing> --output-dir <out_perm_trailing> --max-holding-bars 50 --exit-policy simple_trailing_after_1R --entry-time-mode m5_close --third-candidate-lookback-bars 5 --max-entries-per-recent-third-candidate 1 --disable-heuristic-fallback --htf-filter-enabled --htf-neutral-policy permissive --start 2024-07-01 --end 2024-10-01
```
