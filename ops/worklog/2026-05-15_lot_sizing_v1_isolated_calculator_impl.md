# 2026-05-15 lot sizing v1 isolated calculator impl

## 目的
- `Lot Sizing v1` として isolated calculator を実装する。
- 本線（`PipelineAdapter` / `BacktestRunner` / `PositionSizer`）には接続しない。

## 実装内容
- 追加:
  - `src/risk_filter/lot_sizing_calculator.py`
  - `LotSizingV1Config`
  - `LotSizingV1Result`
  - `LotSizingCalculator.calculate(...)`
- 追加:
  - `tests/unit/risk_filter/test_lot_sizing_calculator.py`

## 固定した挙動
- formula:
  - `raw_lot = account_balance * risk_per_trade / (stop_loss_distance_pips * pip_value_per_lot)`
- rounding:
  - `floor` のみ対応
  - `rounding_mode != "floor"` は invalid
  - `rounded_lot = floor(raw_lot / lot_step) * lot_step`
- clamp:
  - `rounded_lot > max_lot` は `lot=max_lot`, `clamped_flag=True`
  - `rounded_lot < min_lot` は invalid（引き上げしない）
- step整合:
  - `min_lot` / `max_lot` は `lot_step` 整合必須
  - 不整合は invalid
- reason形式:
  - `category_token[:detail]`
  - success: `lot_sizing_v1_applied`
  - clamp: `lot_sizing_v1_applied:max_lot_clamped`
  - invalid: `invalid_lot_sizing_input: <detail>`

## 非接続範囲（維持）
- `PipelineAdapter` 接続なし
- `BacktestRunner` 接続なし
- `PositionSizer` 置換なし
- `src/backtest/` 未変更
- `src/evaluator/` 未変更
- 売買ロジック未変更
- trade_count / PnL 影響経路未変更

## テスト
- `pytest -q tests/unit/risk_filter/test_lot_sizing_calculator.py`
- `pytest -q tests/unit/risk_filter`
- `git diff --check`

## 未解決点
- `LotSizingCalculator` を既存 `PositionSizer` / planner chain に接続するかは後続判断。
- 通貨ペア別 `pip_value_per_lot` 自動計算は未対応。
- broker別 lot 制約厳密化は未対応。
