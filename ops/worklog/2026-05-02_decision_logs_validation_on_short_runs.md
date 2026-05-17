# 2026-05-02 decision logs validation on short runs

## 実施内容
- fallback OFF / lookback=5 / dedup=1 設定で2期間（2024-01-02〜01-09, 2024-01-09〜01-16）を decision_logs 検証用 run_id で再実行。
- trade_logs.csv と decision_logs.csv の同時出力を確認。
- decision_logs 分析用に scripts/analyze_decision_logs.py を追加。
- decision_log_count, fail_stage, entry_signal, trade_ok, structure_source, temporal_candidate, decision_reason 等を集計。
- trade_count と decision_logs の trade_ok true count の対応を確認。
- pytest で回帰確認。

## 注意
- 収益性評価ではなく構造検証。
- spread=0.2 pips fallback 前提。
- 手数料・スリッページ・スワップ未反映。
- 実 broker / OANDA API / 実注文送信は未実装。
