# 2026-05-02 Exit Strategy Observation From MTF Charts

## 背景
Q1 backtest の MTFチャート（H4/H1 reference + M5 execution）を目視確認したところ、entry後の一時逆行または小さな損切りの後に、トレンド方向へ進行するケースが確認された。

## 観察メモ
- 現行 backtest exit は固定 `stop_loss` / 固定 `take_profit` / `max_holding_bars` に寄っている。
- そのため、トレンド継続・崩壊の構造判定を使わず、早期撤退となる可能性がある。
- この観察は構造検証段階の知見であり、収益性確認済みを意味しない。

## 今回の対応（文書化のみ）
- `docs/17_backtest_design.md` に future exit experiments を追記。
  - `fixed_sl_tp_exit`（比較基準として維持）
  - `trend_break_exit`
  - `hybrid_exit`
  - `time_based_exit`（単独主exitにしない比較候補）
- `docs/04_module_spec.md` に、Backtest初期exitは固定方式であり trend-break exit は将来実験候補である旨を追記。
- `ops/CURRENT_TASKS.md` に発展課題を追加。
  - exit strategy experiments
  - trend-break exit
  - hybrid exit
  - swing-based trailing stop

## 制約の維持
- 売買ロジック変更なし。
- `BacktestRunner` / `PipelineAdapter` / `ExitRuleEngine` 実装変更なし。
- 実 broker / OANDA API / 実注文送信は未実装のまま。
- spread=0.2 pips fallback、手数料・スリッページ・スワップ未反映の前提を維持。
