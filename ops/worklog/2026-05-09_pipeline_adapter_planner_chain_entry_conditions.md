# 2026-05-09 pipeline adapter planner chain entry conditions

## 目的
- Risk/Stop v0 採用済み最小実装を前提に、`PipelineAdapter` planner chain 正式接続の要否判断に必要な観点を docs/ops へ固定する。
- 今回は判断整理のみを対象とし、実装には着手しない。

## 現行暫定固定値経路の役割
- 現行 `PipelineAdapter` は `fixed_lot` / fixed SL distance / fixed TP distance を直接 `RiskAssembler` に渡す。
- この経路は Risk/Stop v0 契約（`trade_ok=true` には valid `lot` / `stop_loss` / `take_profit` 必須）を pipeline 上で安定維持するための暫定措置。
- `PositionSizer` / `StopLossPlanner` / `TakeProfitPlanner` の契約は unit/integration test で担保する。
- この状態は lot sizing 本体実装、収益性確認、実運用品質を意味しない。

## planner chain 正式接続の候補メリット
- Risk/Stop v0 の部品構成と `PipelineAdapter` 本体経路の一致度が上がる。
- `PositionSizer` / `StopLossPlanner` / `TakeProfitPlanner` の実装を pipeline 経路でも利用できる。
- 将来の lot sizing 本体や SL/TP 拡張への接続がしやすくなる。
- `docs/04` / `docs/10` と実装経路の整合が上がる。

## planner chain 正式接続のリスク
- Backtest/Pipeline の entry結果や `trade_ok` 件数が変化する可能性。
- 現行 config の fixed値項目と planner 入力の意味重複が起きる可能性。
- `PositionSizer placeholder` 前提の `account_balance` を `PipelineAdapter` がどう渡すか未固定。
- `entry_price_candidate` を `current_bar.close` として渡すか、別扱いにするか未固定。
- `fixed_sl_tp` baseline を壊す可能性。
- `tests/unit/backtest/test_pipeline_adapter.py` の期待値更新が必要になる可能性。

## 正式接続の着手条件
- 接続後も `fixed_sl_tp` baseline と同値の SL/TP 価格を representative fixture で確認できること。
- `PositionSizer placeholder` が `fixed_lot` を返せる `account_balance` 入力方針を固定済みであること。
- `entry_price_candidate=current_bar.close` などの受け渡し方針が固定済みであること。
- invalid `lot` / `stop_loss` / `take_profit` で `trade_ok=false` が pipeline decision trace に反映されること。
- `PipelineAdapter` の既存 decision trace / trade_logs / tests を壊さない移行方針があること。
- 接続前後で representative fixture 差分を比較できること。
- 接続後に targeted test と full `pytest` を実行すること。

## 正式接続時の非対応範囲
- lot sizing本体実装。
- `account_balance` 連動計算式。
- `risk_per_trade` 実装。
- broker lot制約厳密化。
- OANDA/API接続。
- 実注文。
- broker連携。
- Session/SR/HTF filter化。
- experimental exit 本採用。
- 株式拡張。
- 収益性評価。

## 接続時のテスト観点
- Planner chain経路でも fixed_lot / SL / TP が従来固定値経路と一致する正常系。
- invalid fixed_lot で `trade_ok=false`。
- invalid stop distance で `trade_ok=false`。
- invalid take profit distance で `trade_ok=false`。
- account_balance placeholder 入力不正で `trade_ok=false`。
- long/short の SL/TP 方向が正しい。
- decision trace に `risk_reason` / `filter_reason` が残る。
- representative fixture で既存挙動が意図せず変わらないことを確認する。
- full `pytest` を実行する。

## 今回実施したこと / 未実施
- 実施: docs/ops で判断観点、着手条件、非対応範囲、テスト観点を明文化。
- 未実施: `PipelineAdapter` planner chain 正式接続の実装、挙動変更、テスト変更。

## 残る未解決点
- planner chain 正式接続をいつ実施するか（Phase切り分けと優先順位）。
- `account_balance` placeholder 入力値を `PipelineAdapter` でどう固定するか。
- `entry_price_candidate` 受け渡しの命名・トレース方針をどこまで明文化するか。
- 接続時に `test_pipeline_adapter` の期待値差分をどこまで許容するか。
