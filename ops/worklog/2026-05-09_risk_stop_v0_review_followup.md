# 2026-05-09 risk stop v0 review followup

## 目的
- `/review` 指摘に対して、採用前の小修正（契約整合・テスト補強・docs/ops明記）を行う。
- 大きな再設計や本体売買ロジック変更は行わない。

## 対応内容
### 1) PositionSizer の account_balance 前提チェック
- `src/risk_filter/position_sizer.py` を更新。
- `fixed_lot > 0` かつ `account_balance > 0` の両方を満たす場合のみ `lot` を返す。
- 以下は `lot=None` とし、`size_reason` に `invalid_lot` を残す:
  - `account_balance <= 0`
  - `account_balance` が `None` / `bool` / `NaN` / `inf` / 非数
  - `fixed_lot` が `None` / `bool` / `NaN` / `inf` / `<=0` / 非数
- 本対応は placeholder の前提条件チェックであり、lot sizing 本体実装ではない。

### 2) RiskAssembler の不正値テスト補強
- `tests/unit/risk_filter/test_risk_assembler.py` に以下を追加:
  - `lot=float("nan")` / `lot=float("inf")` / `lot=True` で `trade_ok=false` + `invalid_lot`
  - `stop_loss=float("nan")` / `stop_loss=True` で `trade_ok=false` + `invalid_stop_loss`
  - `take_profit=float("inf")` / `take_profit=True` で `trade_ok=false` + `invalid_take_profit`
  - `signal_type="exit"` かつ `entry_signal=True` で `trade_ok=false` + `risk_contract_invalid`
- `_is_valid_positive_number` 実装変更は不要（既存ロジックで拒否可能）。

### 3) integration テスト補強
- `tests/integration/test_signal_to_risk_filter.py` に
  - `signal_type="exit"` かつ `entry_signal=True` の拒否ケースを追加。

### 4) PipelineAdapter 暫定固定値経路の明記
- `docs/10_interface_contract.md` に `4.5.2` を追加。
- `docs/17_backtest_design.md` に `6.116` を追加。
- 明記内容:
  - 現時点の `PipelineAdapter` は planner chain 未接続。
  - `fixed_lot` / fixed SL distance / fixed TP distance を `RiskAssembler` に渡す暫定固定値経路を維持。
  - これは Risk/Stop v0 契約検証と pipeline 安定性維持のための暫定措置。
  - planner chain 正式接続は後続判断。
  - lot sizing 本体実装・収益性確認・実運用品質を意味しない。

## 非対応（維持）
- PipelineAdapter への planner chain 正式接続。
- BacktestRunner / Signal / Execution 本体変更。
- lot sizing 本体実装（`account_balance`連動計算式、`risk_per_trade`、複利、broker lot制約厳密化）。
- OANDA/API接続、実注文、demo口座接続、broker連携。
- HTF/SR/Session/RiskStop/Halt filter化、株式拡張。

## 残る未解決点
- planner chain を PipelineAdapter 本体へ正式接続するかの判断時期。
- `risk_reason` / `filter_reason` の語彙管理（enum化）タイミング。
- placeholder から lot sizing 本体への移行条件。
