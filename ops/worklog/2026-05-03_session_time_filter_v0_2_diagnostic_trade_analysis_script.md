# 2026-05-03 Session/Time Filter v0.2 diagnostic trade analysis script

## 実装内容
- `scripts/analyze_session_v2_diagnostic_trades.py` を新規追加。
- 入力:
  - `decision_logs.csv`
  - `trade_logs.csv`
- 突合:
  - `trade_logs.entry_time` と `decision_logs.timestamp` を UTC正規化して突合。
  - `decision_logs` 同一timestamp重複は最後の行を採用。
  - `trade_logs.pnl` を損益計算に使用。
- 出力:
  - `session_v2_trade_analysis.csv`
  - `session_v2_group_summary.csv`
  - `session_v2_group_summary.md`
- 集計グループ:
  - `session_label`
  - `hour_utc`
  - `day_of_week`
  - `session_risk_flag`
  - `is_low_liquidity_hour`
  - `is_tokyo_session`
  - `is_london_session`
  - `is_new_york_session`
  - `is_london_ny_overlap`
  - `session_policy`
- unmatched trade がある場合は Markdown summary に warning を出力。

## テスト結果（対象）
- join（entry_time/timestamp）・timezone差異吸収。
- session列のtrade analysis付与。
- group summary 指標（trade_count/total_pnl/average_pnl/win_rate）。
- unmatched warning。
- 必須列不足エラー。
- Markdown出力と注意書き。
- `session_label` / `hour_utc` / `day_of_week` / `session_risk_flag` 集計妥当性。

## 未解決事項
- 代表run（`oos2_202411_session_v2_diag_trailing_matched`）の実データ集計結果確認は未実施（ユーザー実行待ち）。
- `low_liquidity` のサンプル数が少ない場合の解釈方針（複数月確認）が必要。
- UTC固定近似ラベル（DST未補正）のまま本採用filter判断は行わない。
