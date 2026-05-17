# 2026-05-16 lot sizing v1 shadow comparison representative run result

## 実行目的
- 既存の representative run 手順（comparison-only / diagnostic-only）が実運用できることを、1回のスモーク実行で確認する。
- 新機能追加、本線接続、収益性評価は行わない。

## 使用入力
- `tmp/phase9_pipeline_rep_20260509/near_live/near_live_decision_logs.csv`
- 補足:
  - 入力CSVに `stop_loss_distance_pips` 列がないため、CLI fallback を使用。

## 実行コマンド
```powershell
$env:PYTHONPATH='.'
python scripts/compare_lot_sizing_shadow.py `
  --input-csv tmp/phase9_pipeline_rep_20260509/near_live/near_live_decision_logs.csv `
  --output-dir tmp/lot_sizing_shadow_rep_20260516 `
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
- `tmp/lot_sizing_shadow_rep_20260516/`

## summary要点
- `row_count`: `36`
- `valid_risk_lot_count`: `36`
- `invalid_risk_lot_count`: `0`
- `clamped_count`: `0`
- `below_min_count`: `0`
- `invalid_input_count`: `0`
- `average_lot_size_diff`: `-0.050000000000000024`
- `average_lot_size_ratio`: `0.5`
- `risk_based_lot_reason_counts`: `{'lot_sizing_v1_applied': 36}`

## Git管理外にした生成物
- `tmp/lot_sizing_shadow_rep_20260516/lot_sizing_shadow_rows.csv`
- `tmp/lot_sizing_shadow_rep_20260516/lot_sizing_shadow_summary.csv`
- `tmp/lot_sizing_shadow_rep_20260516/lot_sizing_shadow_summary.md`

## 非影響確認
- 本実行は `scripts/compare_lot_sizing_shadow.py` の offline comparison のみ。
- `PipelineAdapter` / `BacktestRunner` / `PositionSizer` / Execution path は未変更。
- PnL / trade_count / entry / exit / `trade_ok` への影響はない。

## 次に進む判断
- representative run 手順は運用可能（1回実行で確認）。
- 次タスクは Session / SR / HTF filter化の優先順位整理へ進む。
