# 2026-05-02 M1 Exit Replay for Trailing Validation

## 実施内容
- `scripts/replay_counterfactual_exits_m1.py` を追加
- M5 `trade_logs` の entry 固定で、M1バーを使った exit 再評価を実装
- 対応 rule:
  - `baseline_fixed_exit`
  - `simple_trailing_after_1R`
  - `simple_trailing_after_1R_conservative`
  - `simple_trailing_after_1R_next_bar_activation`
- position-aware 制約（保有中の次entry skip）を実装
- entryと同じM1バーでexitしない制約を維持
- `max_holding_minutes` による制限を実装
- 出力:
  - `m1_exit_replay_trades.csv`
  - `m1_exit_replay_summary.csv`
  - `m1_exit_replay_summary.md`

## ドキュメント更新
- `docs/17_backtest_design.md` に M1 replay の位置づけを追記

## テスト
- `tests/unit/backtest/test_replay_counterfactual_exits_m1.py` を追加
- 検証項目:
  - M1 DAT最小読み込み
  - entry同一M1バーexit禁止
  - 保有中entry skip
  - max_holding_minutes 制限
  - long/short pnl符号
  - trailing rule のM1動作
  - 不正/欠損DATのエラー

## 注意
- spread=0.2 pips fallback 前提
- 手数料/スリッページ/スワップ未反映
- 収益性評価ではなく構造検証
