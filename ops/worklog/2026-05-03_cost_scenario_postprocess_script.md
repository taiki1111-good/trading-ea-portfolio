# 2026-05-03 cost scenario postprocess script

## 実装内容
- `scripts/apply_cost_scenarios_to_m1_replay.py` を追加。
- 対象入力: `m1_exit_replay_trades.csv`。
- `accepted_entry=True` かつ `m1_replay_pnl` 有効行のみを集計対象にし、後処理で以下を算出:
  - `gross_pnl`, `gross_pips`
  - `additional_spread_pips`, `slippage_pips_round_turn`, `commission_pips_round_turn`, `total_cost_pips`
  - `net_pips`, `net_pnl`
  - scenario metadata（`cost_scenario_name`, `spread_already_included`, `swap_mode`）
- 出力:
  - `cost_adjusted_trades.csv`
  - `cost_adjusted_summary.csv`
  - `cost_adjusted_summary.md`

## テスト
- `tests/unit/backtest/test_apply_cost_scenarios_to_m1_replay.py` を追加。
- 検証項目:
  1. USDJPY pip換算（`1 pip = 0.01`）
  2. cost控除後の `net_pips` / `net_pnl`
  3. `accepted_entry=False` の集計除外
  4. `spread_already_included=true` で追加spread 0.0 のとき二重計上しない
  5. summary gross/net 集計
  6. 必須列不足時の明確なエラー

## 未解決事項
- swap は v0.1 では `none` / `note_only` で実控除なし。実額控除モデルは未実装。
- `spread_already_included` の運用は scenario 設計依存であり、入力runごとの前提管理が必要。
- representative logs に対する scenario パラメータ（slippage/commission/additional spread）の標準セットは今後決定する。
