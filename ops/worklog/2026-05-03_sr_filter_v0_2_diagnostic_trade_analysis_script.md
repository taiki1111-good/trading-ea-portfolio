# 2026-05-03 SR Filter v0.2 diagnostic trade analysis script

## 実装内容
- `scripts/analyze_sr_v2_diagnostic_trades.py` を新規追加。
- 入力:
  - `decision_logs.csv`
  - `trade_logs.csv`
- 突合:
  - `trade_logs.entry_time` と `decision_logs.timestamp` を `pandas.to_datetime(..., utc=True)` でUTC正規化して突合。
  - `decision_logs` 側の同一timestamp重複は最後の行を採用。
  - `trade_logs.pnl` を損益集計に利用。
- 出力:
  - `sr_v2_trade_analysis.csv`
  - `sr_v2_group_summary.csv`
  - `sr_v2_group_summary.md`
- 集計グループ:
  - `sr_proximity_flag`
  - `sr_block_side`
  - `sr_data_valid_flag`
  - `sr_counterfactual_group`
  - `sr_policy`
  - `sr_window_bars`
- `unmatched trades` がある場合は Markdown summary に warning を出力。

## テスト
- `tests/unit/backtest/test_analyze_sr_v2_diagnostic_trades.py` を新規追加。
- 検証項目:
  - entry_time/timestamp 突合
  - timezone表記差異吸収
  - SR列付与
  - group summary 指標計算
  - unmatched warning
  - 必須列不足エラー
  - Markdown生成
  - `sr_proximity_flag` / `sr_block_side` 集計妥当性

## 制約確認
- backtest再実行なし。
- SR filterをentry制御に使っていない。
- 売買ロジック変更なし。
- HTF v2 filter化なし。
- 閾値の本採用扱いなし。

## 未解決事項
- 代表run（`oos2_202411_sr_v2_diag_trailing_matched`）での実データ集計結果確認は未実施（ユーザー実行待ち）。
- `sr_proximity_flag=True` 群の解釈（悪化要因か利益源か）は出力確認後に判断。
