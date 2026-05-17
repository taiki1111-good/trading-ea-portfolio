# 2026-05-09 risk stop v0 minimal impl

## 目的
- docs/ops で固定した Risk/Stop v0 契約に沿って、`src/risk_filter` の最小実装と unit test を整える。

## 実装した対象
- `src/risk_filter/position_sizer.py`
- `src/risk_filter/stop_loss_planner.py`
- `src/risk_filter/take_profit_planner.py`
- `src/risk_filter/assembler.py`
- 関連テスト:
  - `tests/unit/risk_filter/test_position_sizer.py`
  - `tests/unit/risk_filter/test_stop_loss_planner.py`
  - `tests/unit/risk_filter/test_take_profit_planner.py`
  - `tests/unit/risk_filter/test_risk_assembler.py`
  - `tests/integration/test_signal_to_risk_filter.py`
  - 影響反映: `tests/unit/backtest/test_backtest_runner.py`, `tests/unit/backtest/test_pipeline_adapter.py`

## PositionSizer placeholder の内容
- `fixed_lot > 0` のとき `lot` を返す。
- `size_reason` に `placeholder_fixed_lot` を残す。
- `fixed_lot <= 0` または不正値のとき `lot=None`、`size_reason` に `invalid_lot` を残す。
- 本実装は placeholder であり、資金管理最適化は行っていない。

## lot sizing 本体を実装していないこと
- 非対応のまま維持:
  - `account_balance` 連動 sizing
  - `risk_per_trade`
  - 複利連動
  - broker lot 制約厳密化

## StopLossPlanner / TakeProfitPlanner
- 入力価格は `entry_price_candidate` 前提で扱う。
- StopLoss:
  - long: `entry_price_candidate - fixed_stop_distance`
  - short: `entry_price_candidate + fixed_stop_distance`
  - `fixed_stop_distance <= 0` は `stop_loss=None`、`invalid_stop_loss`
- TakeProfit:
  - long: `entry_price_candidate + fixed_take_profit_distance`
  - short: `entry_price_candidate - fixed_take_profit_distance`
  - `fixed_take_profit_distance <= 0` は `take_profit=None`、`invalid_take_profit`
- `fixed_sl_tp` baseline を維持し、experimental exit 本採用は行っていない。

## RiskAssembler の `trade_ok=true` 契約
- `trade_ok=true` を許容する条件:
  - `entry_signal=true`
  - entry 系 `signal_type`（long/short）
  - `event_risk_flag=false`
  - `spread_ok=true`
  - `limit_ok=true`
  - `lot` 有効値（`>0`）
  - `stop_loss` 有効値
  - `take_profit` 有効値
- 失敗時:
  - `risk_contract_invalid` / `invalid_lot` / `invalid_stop_loss` / `invalid_take_profit` などを理由に残す。
  - `risk_reason` または `filter_reason` が空にならない。
- 成功時:
  - `risk_reason` で `fixed_sl_tp` と `placeholder_fixed_lot` を追跡可能にした。

## テスト
- 追加・更新した観点:
  - PositionSizer placeholder 正常/異常
  - SL/TP 方向妥当性と invalid distance
  - RiskAssembler の `trade_ok` 契約（invalid lot/SL/TP, event/spread/limit fail）
  - integration の invalid lot fail 追加
- 実行結果:
  - `pytest -q tests/unit/risk_filter tests/integration/test_signal_to_risk_filter.py tests/unit/backtest/test_backtest_runner.py tests/unit/backtest/test_pipeline_adapter.py`
    - `88 passed`
  - `pytest -q`
    - `413 passed`

## 非対応範囲
- OANDA/API接続、実注文、demo口座接続、broker連携
- PipelineAdapter本体の売買判断変更
- BacktestRunner本体の戦略変更
- HTF/SR/Session/RiskStop/Halt filter化実装
- 株式拡張、Equity Adapter
- lot sizing本体実装
- account_balance連動、risk_per_trade、broker制約厳密化
- 収益性評価、最適化、ML/HMM/LSTM
- Triangle / Trap / reaction SR のmain導入
- experimental exit candidate の本採用

## 残る未解決点
- `risk_reason` / `filter_reason` の管理語彙化（enum化）タイミング。
- `entry_price_candidate` 命名統一の全体適用範囲。
- placeholder から lot sizing 本体への移行条件。
