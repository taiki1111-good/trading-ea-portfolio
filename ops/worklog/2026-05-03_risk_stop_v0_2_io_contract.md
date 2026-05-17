# 2026-05-03 Risk/Stop v0.2 I/O Contract & Diagnostic Policy

## 目的
- Phase 7 Risk/Stop v0.2 の実装前段階として I/O 契約と診断ポリシーを固定する。
- 対象は entry選別ではなく、EA全体の損失拡大抑制・破滅回避・停止/再開管理。
- 今回は設計契約固定のみで、本体停止ロジック実装は行わない。

## 入力
- `trade_logs.csv`（必須）
- optional `decision_logs.csv`
- optional cost-adjusted trade logs
- risk_stop config

## 出力（diagnostic候補）
- `trade_id`, `entry_time`, `exit_time`, `trade_date_utc`
- `pnl`, `pnl_pips`
- `cumulative_pnl`, `cumulative_pips`
- `daily_pnl`, `daily_pips`, `daily_trade_count`
- `equity_peak`, `drawdown`, `drawdown_pips`
- `consecutive_loss_count`
- `would_daily_loss_stop_trigger`
- `would_consecutive_loss_stop_trigger`
- `would_drawdown_stop_trigger`
- `would_cooldown_trigger`
- `risk_stop_reason`
- `avoided_loss_pnl`, `missed_profit_pnl`, `net_counterfactual_effect_pnl`

## 初期評価単位
- `trade_logs` 後処理で評価。
- closed trades のみ対象。
- open position 強制決済は初期対象外。
- 停止は「新規entry停止」を仮想評価。

## 損益単位
- 初期sourceは `pnl`（price unit）。
- USDJPYは補助的に pips 換算（`pip_size=0.01`）。
- R基準・金額基準・lot sizing は後続候補。
- pips / R / 金額を混同しない。

## daily boundary 方針
- 初期は UTC date を daily boundary とする。
- JST / NY close は後続候補。
- broker/OANDA時間との整合は未解決事項として保持。

## counterfactual方針
- stop発動以降（同日または cooldown 期間中）の新規entryを止めた仮想ケースを評価。
- 避けた負けを `avoided_loss`、逃した勝ちを `missed_profit` として算出。
- `net_counterfactual_effect = avoided_loss - missed_profit` を評価軸とする。
- 代表月単独で本採用判断はしない。

## 未解決事項
- pips / R / 金額の最終基準。
- lot sizing導入タイミング。
- daily boundary（UTC/JST/NY close）の最終選定。
- open position 強制決済の扱い。
- stop後の再開条件。
- cost-adjusted logs 利用有無。
- swap/commission/slippage反映後の再評価要否。

## 注意
- backtest再実行・Risk/Stop本体実装・BacktestRunner/PipelineAdapter変更・売買ロジック変更・lot sizing実装・閾値確定は未実施。
