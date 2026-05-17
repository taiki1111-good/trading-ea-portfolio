# 2026-05-15 pipeline adapter planner chain adoption

## 判定
- PipelineAdapter planner chain正式接続を採用済みとする。

## 採用根拠
- `PipelineAdapter -> PositionSizer -> StopLossPlanner -> TakeProfitPlanner -> RiskAssembler` の本体経路接続が実装済み。
- fixed baseline 同値（trade_count / SLTP / decision trace主要列）維持を前提とした実装である。
- invalid `placeholder_account_balance` を含む invalid系で `trade_ok=false` を確認済み。
- テスト結果:
  - `tests/unit/risk_filter`: 29 passed
  - `tests/integration/test_signal_to_risk_filter.py`: 8 passed
  - `tests/unit/backtest/test_pipeline_adapter.py`: 56 passed
  - `pytest -q`: 421 passed

## 継続する非対応範囲
- lot sizing 本体実装
- `account_balance` 連動計算式
- `risk_per_trade`
- broker lot 制約厳密化
- OANDA/API 接続
- 実注文
- Session/SR/HTF filter本体化
- 収益性評価

## 次タスク
- `risk_reason` / `filter_reason` の管理語彙化（enum化要否）判断へ移行する。
