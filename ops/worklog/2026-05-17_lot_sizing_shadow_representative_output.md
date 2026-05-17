# 2026-05-17 lot sizing shadow representative output

## 実行目的
- 採用済みの `compare_lot_sizing_shadow.py`（diagnostic / shadow comparison tool）が、代表入力で出力できることを1回記録する。
- 本記録は本体接続や収益性評価ではなく、運用可能性の確認である。

## 入力
- `tmp/phase9_pipeline_rep_20260509/near_live/near_live_decision_logs.csv`
- 補足:
  - 入力CSVに `stop_loss_distance_pips` 列がないため、CLI fallback（`--stop-loss-distance-pips 20`）を使用。

## 実行コマンド
```powershell
$env:PYTHONPATH='.'
python scripts/compare_lot_sizing_shadow.py `
  --input-csv tmp/phase9_pipeline_rep_20260509/near_live/near_live_decision_logs.csv `
  --output-dir tmp/lot_sizing_shadow_rep_20260517 `
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

## 出力先
- `tmp/lot_sizing_shadow_rep_20260517/`

## 出力ファイル
- `lot_sizing_shadow_rows.csv`
- `lot_sizing_shadow_summary.csv`
- `lot_sizing_shadow_summary.md`

## summary要点
- `row_count=36`
- `valid_risk_lot_count=36`
- `invalid_risk_lot_count=0`
- `clamped_count=0`
- `below_min_count=0`
- `invalid_input_count=0`
- `average_lot_size_diff=-0.050000000000000024`
- `average_lot_size_ratio=0.5`
- `risk_based_lot_reason_counts={'lot_sizing_v1_applied': 36}`

## row-level確認（先頭行）
- `risk_lot_valid_flag=True`
- `lot_size_diff=-0.05`
- `lot_size_ratio=0.5`

## 位置づけ
- 本実行は diagnostic / shadow comparison tool の representative output 記録。
- lot sizing 本体接続ではない。
- `PositionSizer` placeholder 維持。
- `PipelineAdapter` / `BacktestRunner` / `RiskAssembler` / `PositionSizer` の本線挙動は変更していない。
- `PnL` / `trade_count` / `trade_ok` / `entry` / `exit` に影響しない。
- 収益性評価ではない。

## 補足
- `fixed_lot <= 0` 時の diff/ratio 空欄仕様は既存 unit test で固定済みであり、本runではその境界ケースは実施していない。
