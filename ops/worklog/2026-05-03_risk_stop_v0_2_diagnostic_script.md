# 2026-05-03 Risk/Stop v0.2 diagnostic script

## 実装内容
- `scripts/analyze_risk_stop_v2_trades.py` を追加。
- 既存 `trade_logs.csv` を後処理し、`daily_loss_stop` と `consecutive_loss_stop` の counterfactual を算出。
- 本体停止ロジックは実装せず、closed trade のみで仮想停止効果を評価。

## counterfactual仕様
- `daily_loss_stop`:
  - 同一UTC日で `daily_pips <= -threshold` 到達後、同日後続tradeを停止対象とみなす。
  - trigger trade自体は停止しない。
- `consecutive_loss_stop`:
  - 連敗数 `>= threshold` 到達後、同日後続tradeを停止対象とみなす。
  - trigger trade自体は停止しない。
  - UTC日が変わると連敗カウントと停止状態をリセット。
- 停止対象tradeから以下を算出:
  - `avoided_loss_pips`（負けを止めた分）
  - `missed_profit_pips`（勝ちを逃した分）
  - `net_counterfactual_effect_pips = avoided_loss_pips - missed_profit_pips`

## 出力
- `risk_stop_v2_trade_analysis.csv`
- `risk_stop_v2_summary.csv`
- `risk_stop_v2_summary.md`

## テスト結果
- `tests/unit/backtest/test_analyze_risk_stop_v2_trades.py` を追加。
- 処理順、pips換算、trigger/停止対象仕様、連敗リセット、複数閾値、必須列エラー、Markdown生成を検証。

## 未解決事項
- drawdown_stop / cooldown_after_loss の後続実装方針。
- cost-adjusted logs 併用時の評価方針。
- daily boundary を UTC以外へ拡張するか。
- lot sizing 導入後の再評価設計。

## 注意
- backtest再実行・Risk/Stop本体実装・BacktestRunner/PipelineAdapter変更・売買ロジック変更・lot sizing実装は未実施。
