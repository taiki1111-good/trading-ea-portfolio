# 2026-05-15 pipeline adapter planner chain decision

## 目的
- `PipelineAdapter` planner chain 正式接続を次フェーズで実装するかを判断し、実装前の採用判断・限定スコープ・Go/No-Go 条件を固定する。
- 今回は docs/ops 整理のみを対象とし、実装コード・テストコードの変更は行わない。

## 現状確認（コード実体）
- `src/backtest/pipeline_adapter.py` は現時点で以下の暫定固定値経路を使用している。
  - `entry_price=current_bar.close` を基準に `_build_fixed_risk_prices()` で fixed SL/TP 価格を生成。
  - `RiskAssembler.assemble(...)` に `lot=self._config.fixed_lot` と fixed SL/TP を直接渡す。
  - `PositionSizer` / `StopLossPlanner` / `TakeProfitPlanner` は pipeline 本体経路で未接続。
- `src/risk_filter/position_sizer.py`
  - placeholder 実装として `account_balance>0` かつ `fixed_lot>0` のとき fixed lot を返す。
  - 不正値（bool/NaN/inf/<=0 等）は `lot=None` / `invalid_lot`。
- `src/risk_filter/stop_loss_planner.py`
  - `entry_price_candidate` と `fixed_stop_distance` で SL を算出。
  - long: `entry_price_candidate - distance` / short: `entry_price_candidate + distance`。
- `src/risk_filter/take_profit_planner.py`
  - `entry_price_candidate` と `fixed_take_profit_distance` で TP を算出。
  - long: `entry_price_candidate + distance` / short: `entry_price_candidate - distance`。
- `src/risk_filter/assembler.py`
  - `trade_ok=true` には valid `lot/stop_loss/take_profit` を必須化。
  - invalid `lot` / SL / TP では `trade_ok=false` とし `risk_reason` / `filter_reason` を返す。

## 判断
- 採用判断: **A. planner chain正式接続を次フェーズで実装する**。

## 判断理由
- docs で固定済みの Risk/Stop v0 部品境界（PositionSizer / SL Planner / TP Planner / RiskAssembler）と、`PipelineAdapter` 本体経路の不一致を解消する価値が高い。
- 現行は fixed 値直結で動作安定しているため、同値維持条件を先に固定すれば、低リスクで接続できる。
- lot sizing 本体を実装せず placeholder 維持でも、接続整合性・契約追跡性（decision trace / risk_reason / filter_reason）を改善できる。

## 次フェーズ実装スコープ（限定）
- `PipelineAdapter` から以下を直列接続する。
  - `PositionSizer`
  - `StopLossPlanner`
  - `TakeProfitPlanner`
  - `RiskAssembler`
- ただし結果は従来 baseline と一致させる。
  - `fixed_lot` / fixed SL distance / fixed TP distance を維持。
  - `PositionSizer` は placeholder のまま。
  - `account_balance` は placeholder valid 判定を通す固定値（例: `1000.0`）を渡す。
  - `entry_price_candidate` は `current_bar.close` を使用。
  - long/short の SL/TP 方向は現行固定経路と同一。
  - decision trace / `risk_reason` / `filter_reason` を壊さない。

## 非対応範囲（同時実装しない）
- lot sizing 本体実装。
- `account_balance` 連動計算式。
- `risk_per_trade` 実装。
- broker lot 制約厳密化。
- OANDA/API 接続。
- 実注文送信。
- Session/SR/HTF filter 本体化。
- 収益性評価。

## Go/No-Go 条件（実装着手前固定）
- Go 条件:
  1. representative fixture で接続前後の `trade_count` が不変。
  2. fixed baseline の SL/TP 価格が接続前後で一致。
  3. decision trace 主要列（少なくとも `trade_ok`, `fail_stage`, `decision_reason`, `risk_reason`, `filter_reason` 文脈）が壊れない。
  4. invalid `fixed_lot` / invalid stop distance / invalid take profit distance / invalid `account_balance` で `trade_ok=false` が確認できる。
  5. targeted pytest 実行後に full `pytest` 実行を前提とする。
- No-Go 条件:
  - 上記 1〜4 のいずれか不成立。
  - baseline 同値維持のために非対応範囲（lot sizing本体等）へ踏み込む必要が出た場合。

## 今回実施 / 未実施
- 実施:
  - docs/ops で採用判断（A）と実装前固定方針を明文化。
- 未実施:
  - `PipelineAdapter` 実装変更。
  - テストコード更新。
  - pytest 実行。
