# 2026-05-15 lot sizing v1 isolated calculator adoption

## 目的
- `Lot Sizing v1` isolated calculator 実装を採用確定し、ops上の状態を閉じる。
- 今回はコード変更を行わず、採用判断の記録のみを行う。

## 採用判断
- 採用可能とする。
- 採用対象:
  - `src/risk_filter/lot_sizing_calculator.py`
  - `tests/unit/risk_filter/test_lot_sizing_calculator.py`

## 採用根拠
- isolated calculator として formula / rounding / clamp / invalid 条件が unit test で固定されている。
- `PipelineAdapter` / `BacktestRunner` / `PositionSizer` 本線には未接続である。
- `fixed_lot` baseline は維持されている。
- PnL / trade_count に影響する経路は変更していない。

## 確認結果
- `pytest -q tests/unit/risk_filter/test_lot_sizing_calculator.py` -> `13 passed`
- `pytest -q tests/unit/risk_filter` -> `51 passed`
- `git diff --check` -> 問題なし

## 非接続範囲（継続）
- `PipelineAdapter` へ接続しない
- `BacktestRunner` へ接続しない
- `PositionSizer` 置換しない
- 売買ロジックを変更しない

## 未解決点（後続）
- `PipelineAdapter` / `PositionSizer` 本線へ接続するか
- Decimal化または整数step換算の要否
- broker別 lot 制約の厳密化
- `pip_value_per_lot` の通貨ペア別自動計算
- 実運用 / OANDA / API 接続は後続

## 次タスク
- `Lot Sizing v1` を `PipelineAdapter` / `PositionSizer` 本線へ接続するかの判断（Go/No-Go）へ進む。
