# 2026-05-03 Risk/Stop v0.2 diagnostic result

## 対象run
- `run_id`: `oos2_202411_session_v2_diag_trailing_matched`
- `trade_count`: `64`
- `total_pnl`: `0.29010000000004366`

## 実行結果（後処理counterfactual）
- `consecutive_loss_stop threshold=2`
  - `stopped_trade_count=2`
  - `avoided_loss_pips=0.0`
  - `missed_profit_pips=0.75`
  - `net_counterfactual_effect_pips=-0.75`
  - `avoided_loss_pnl=0.0`
  - `missed_profit_pnl=0.0075`
  - `net_counterfactual_effect_pnl=-0.0075`
  - `trigger_count=1`

- `consecutive_loss_stop threshold=3`
  - `stopped_trade_count=0`
  - `avoided_loss_pips=0.0`
  - `missed_profit_pips=0.0`
  - `net_counterfactual_effect_pips=0.0`
  - `trigger_count=0`

- `daily_loss_stop threshold=20/30/50`
  - 全て `stopped_trade_count=0`
  - 全て `trigger_count=0`

## 解釈
- `daily_loss_stop` は代表月で発動なしのため、採用判断は保留。
- `consecutive_loss_stop=2` は1回発動したが、回避損失がなく逸失利益のみ発生し `net` はマイナス。
- `consecutive_loss_stop=3` は発動なしで判断保留。
- 今回の代表月では Risk/Stop 本体統合の根拠は得られていない。
- ただし、Risk/Stop が不要という意味ではなく、良好月では停止条件が効きにくい可能性を示す。

## 統合保留判断
- `daily_loss_stop` / `consecutive_loss_stop` の本体統合は保留。
- Risk/Stop は引き続き diagnostic/counterfactual layer として継続。
- 悪化月・連敗月・高DD月で複数月確認後に再判断する。

## 未解決事項
- 悪化月サンプルでの再現性確認。
- `drawdown_stop` / `cooldown_after_loss` の後続実装順序。
- Phase 8 Validation framework へ先行するかの判断。
- lot sizing未導入状態での評価限界の扱い。

## 注意
- これは既存trade_logsの後処理診断であり、収益性確認ではない。
- backtest再実行・Risk/Stop本体実装・売買ロジック変更・閾値変更は未実施。
