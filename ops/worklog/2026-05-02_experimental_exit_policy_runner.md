# 2026-05-02 Experimental Exit Policy Runner

## 目的
- BacktestRunner本体既定動作を変更せず、entry pipeline共通のまま exit policy を比較する実験runnerを追加。

## 実装
- `scripts/run_backtest_exit_experiment.py` を追加
- exit policy:
  - `fixed_sl_tp`
  - `simple_trailing_after_1R`
- 出力 trade_logs に以下を追加:
  - `exit_policy`
  - `trailing_activation_R`
  - `entry_time_mode`
  - `exit_reason`
  - `holding_bars`
  - `pnl`

## テスト
- `tests/unit/backtest/test_run_backtest_exit_experiment.py` を追加
- 確認項目:
  - fixed既定挙動維持
  - policy指定時のみtrailing適用
  - entryロジック共通
  - entryバーexitなし
  - long/short pnl符号

## ドキュメント
- `docs/17_backtest_design.md` に experimental exit policy 方針を追記

## 注意
- spread=0.2 pips fallback 前提
- 手数料・スリッページ・スワップ未反映
- 収益性評価ではなく構造検証
