# 2026-05-15 pipeline adapter planner chain impl

## 目的
- `PipelineAdapter` の暫定 fixed 値直結経路を、Risk/Stop v0 の planner chain 構成（`PositionSizer` / `StopLossPlanner` / `TakeProfitPlanner` / `RiskAssembler`）へ接続し、docs/ops で固定した方針と実装経路を一致させる。
- 機能強化ではなく、fixed baseline 同値維持（trade_count / SLTP / decision trace主要列）を目的とする。

## 実装内容
- `src/backtest/pipeline_adapter.py`
  - planner chain 呼び出しを追加:
    - `PositionSizer.size(...)`
    - `StopLossPlanner.plan(...)`
    - `TakeProfitPlanner.plan(...)`
    - `RiskAssembler.assemble(...)`
  - 旧 direct fixed 経路（`_build_fixed_risk_prices` + `lot=self._config.fixed_lot` 直渡し）を置換。
  - `entry_price_candidate=current_bar.close` を使用。
  - `PipelineAdapterConfig` に `placeholder_account_balance: float = 1000.0` を追加し、placeholder valid 判定を通す固定値入力を明示化。
  - `sub_reasons` に planner chain の理由（size/SL/TP）を連結して追跡性を維持。
- `tests/unit/backtest/test_pipeline_adapter.py`
  - invalid `placeholder_account_balance`（`0.0`）時に `entry_event is None` / `fail_stage=risk_filter` / `trade_ok=False` を確認するテストを追加。

## baseline 同値観点の確認
- 既存の pipeline adapter テスト（long/short 正常系）で以下を維持:
  - `stop_loss == close +/- stop_loss_distance`
  - `take_profit == close +/- take_profit_distance`
  - `direction` と SL/TP 方向の整合。
- `fail_stage` / `trade_ok` を含む decision trace 主要列の既存検証が通過。
- invalid 系（fixed_lot / stop distance / take profit distance / account_balance）で `trade_ok=false` の契約を維持。

## テスト
- targeted:
  - `pytest -q tests/unit/risk_filter` -> `29 passed`
  - `pytest -q tests/integration/test_signal_to_risk_filter.py` -> `8 passed`
  - `pytest -q tests/unit/backtest/test_pipeline_adapter.py` -> `56 passed`
  - 合計 `93 passed`
- full:
  - `pytest -q` -> `421 passed`

## 非対応範囲（維持）
- lot sizing 本体実装
- `account_balance` 連動計算式
- `risk_per_trade`
- broker lot 制約厳密化
- OANDA/API 接続
- 実注文
- Session/SR/HTF filter 本体化
- 収益性評価

## 未解決点
- 実装は完了したため、次は cross-file review（docs/code/tests/ops）で採用確定または追加修正判断を行う。
