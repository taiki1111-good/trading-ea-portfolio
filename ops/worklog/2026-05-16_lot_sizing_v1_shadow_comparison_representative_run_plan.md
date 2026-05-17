# 2026-05-16 lot sizing v1 shadow comparison representative run plan

## 目的
- `Lot Sizing v1 shadow comparison v0`（Go採用済み）について、comparison-only / diagnostic-only の代表実行手順を固定する。
- 本記録は運用手順・比較観点・Git管理方針の明文化に限定し、実装変更は行わない。
- 収益性評価は目的外とし、構造診断と接続判断材料の整備を目的とする。

## representative run で使う入力候補
- 候補1（最小確認）:
  - 小さな `trade_logs.csv` または `decision_logs.csv`（`stop_loss_distance_pips` 列あり）
- 候補2（fallback確認）:
  - `stop_loss_distance_pips` 列なしCSV + `--stop-loss-distance-pips` 指定
- 候補3（invalid/clamp観測）:
  - `risk_per_trade` / `max_lot` / `min_lot` を調整し、`below_min` / `max_lot_clamped` を意図的に含める入力

注意:
- `stop_loss_distance_pips` は「CSV列優先、なければCLI fallback、両方欠損時エラー」の契約を維持する。
- 本手順では `PipelineAdapter` / `BacktestRunner` / `PositionSizer` / Execution path へ接続しない。

## 実行コマンド例
```powershell
$env:PYTHONPATH='.'
python scripts/compare_lot_sizing_shadow.py `
  --input-csv tmp/shadow_rep_input/trade_logs.csv `
  --output-dir tmp/lot_sizing_shadow_rep_20260516 `
  --fixed-lot 0.1 `
  --account-balance 1000 `
  --risk-per-trade 0.01 `
  --pip-value-per-lot 10 `
  --lot-step 0.01 `
  --min-lot 0.01 `
  --max-lot 2.0 `
  --rounding-mode floor
```

fallback例（CSVに `stop_loss_distance_pips` 列がない場合）:
```powershell
$env:PYTHONPATH='.'
python scripts/compare_lot_sizing_shadow.py `
  --input-csv tmp/shadow_rep_input/decision_logs_without_sl.csv `
  --output-dir tmp/lot_sizing_shadow_rep_20260516_fallback `
  --fixed-lot 0.1 `
  --account-balance 1000 `
  --risk-per-trade 0.01 `
  --pip-value-per-lot 10 `
  --lot-step 0.01 `
  --min-lot 0.01 `
  --max-lot 2.0 `
  --rounding-mode floor `
  --stop-loss-distance-pips 20
```

## 出力先例
- `tmp/lot_sizing_shadow_rep_20260516/`
- `tmp/lot_sizing_shadow_rep_20260516_fallback/`

## 確認対象ファイル
- `lot_sizing_shadow_rows.csv`
- `lot_sizing_shadow_summary.csv`
- `lot_sizing_shadow_summary.md`

## 最低限見る summary 項目
- `row_count`
- `valid_risk_lot_count`
- `invalid_risk_lot_count`
- `clamped_count`
- `below_min_count`
- `invalid_input_count`
- `average_lot_size_diff`
- `average_lot_size_ratio`
- `risk_based_lot_reason_counts`

## 比較観点（軽量運用）
- valid/invalid の比率が急変していないか。
- `below_min_count` / `clamped_count` の偏りがないか。
- `risk_based_lot_reason_counts` に想定外の invalid reason が増えていないか。
- `average_lot_size_diff` / `average_lot_size_ratio` の大きな変動がないか。

## Git管理方針
- representative run の出力CSV/MD（`lot_sizing_shadow_rows.csv` / `lot_sizing_shadow_summary.csv` / `lot_sizing_shadow_summary.md`）は原則 Git 管理外とする。
- 生成物は `tmp/` 配下などの一時出力として扱い、レビュー時は必要な要点のみ worklog に記録する。

## 将来拡張メモ
- 小さいfixture由来の expected sample は、将来 `tests/fixtures/` + unit test へ昇格できる余地を残す。
- ただし本段階では comparison-only 運用手順の固定を優先し、canonical出力化や legacy detail 削除は行わない。

## 非影響の再確認
- 本手順は運用記録のみであり、`PipelineAdapter` / `BacktestRunner` / `PositionSizer` / Execution path の挙動を変更しない。
- PnL / trade_count / entry / exit / `trade_ok` へ影響しない。
