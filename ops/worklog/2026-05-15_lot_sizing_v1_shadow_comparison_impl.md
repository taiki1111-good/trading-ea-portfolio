# 2026-05-15 lot sizing v1 shadow comparison impl

## 目的
- `Lot Sizing v1 shadow mode v0` として、専用 offline comparison script を実装する。
- 既存ログへ後付けで `LotSizingCalculator` を適用し、`fixed_lot` との差分観測を行う。

## 実装内容
- 追加:
  - `scripts/compare_lot_sizing_shadow.py`
  - `tests/unit/backtest/test_compare_lot_sizing_shadow.py`

## 入力仕様（CLI）
- `--input-csv`
- `--output-dir`
- `--fixed-lot`
- `--account-balance`
- `--risk-per-trade`
- `--pip-value-per-lot`
- `--lot-step`
- `--min-lot`
- `--max-lot`
- `--rounding-mode`
- `--stop-loss-distance-pips`（fallback）

`stop_loss_distance_pips` 取得:
- CSV列 `stop_loss_distance_pips` があれば優先利用
- 列がなければ `--stop-loss-distance-pips` を利用
- 両方なければエラー

## 出力仕様
- 行単位:
  - `lot_sizing_shadow_rows.csv`
  - 列:
    - `row_index`
    - `fixed_lot`
    - `account_balance`
    - `risk_per_trade`
    - `stop_loss_distance_pips`
    - `pip_value_per_lot`
    - `risk_based_raw_lot`
    - `risk_based_rounded_lot`
    - `risk_based_effective_lot`
    - `risk_based_lot_sizing_reason`
    - `risk_based_clamped_flag`
    - `risk_lot_valid_flag`
    - `lot_size_diff`
    - `lot_size_ratio`
- summary:
  - `lot_sizing_shadow_summary.csv`
  - `lot_sizing_shadow_summary.md`
  - metrics:
    - `row_count`
    - `valid_risk_lot_count`
    - `invalid_risk_lot_count`
    - `clamped_count`
    - `below_min_count`
    - `invalid_input_count`
    - `average_lot_size_diff`
    - `average_lot_size_ratio`
    - `max_lot_size_diff`
    - `min_lot_size_diff`
    - `risk_based_lot_reason_counts`

## 非影響保証
- 入力CSVを書き換えない
- `PipelineAdapter` 変更なし
- `BacktestRunner` 変更なし
- `PositionSizer` 変更なし
- PnL / trade_count / entry / exit / `trade_ok` / Execution path への影響なし
- diagnostic / comparison-only として実施

## テスト結果
- `pytest -q tests/unit/backtest/test_compare_lot_sizing_shadow.py` -> `9 passed`
- `pytest -q tests/unit/risk_filter/test_lot_sizing_calculator.py` -> `13 passed`

## 未解決点
- `account_balance` / `risk_per_trade` / `pip_value_per_lot` の供給経路を run metadata 化するか
- `risk_based_lot_reason_counts` を canonical形式へ段階移行するか
- shadow mode v1（PipelineAdapter内shadow計算）へ進むかは後続判断
