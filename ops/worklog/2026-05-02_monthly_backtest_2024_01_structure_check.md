# 2026-05-02 Monthly Backtest 2024-01 Structure Check

## 実施概要
- 対象期間 `2024-01-02` 〜 `2024-02-01`（UTC, end exclusive）で M1 DAT から M5 スライスを生成。
- 設定 `lookback=5 + max_entries_per_recent_third_candidate=1 + fallback OFF + max_holding_bars=10` で1か月BTを実行。
- `trade_logs` / `decision_logs` の構造検証分析を実施。
- `pytest -q` を実行し、既存テスト回帰なしを確認。

## 生成データ
- input: `data/raw/dukascopy/USDJPY/M1/dat_csv_candidates/DAT_MT_USDJPY_M1_2024.csv`
- output: `data/private/backtest_slices/USDJPY_M5_2024-01-02_2024-02-01.csv`
- spread fallback: `0.2 pips`（構造検証用途）

## Loader確認
- bar_count=6335
- start_time=2024-01-02T00:00:00+00:00
- end_time=2024-01-31T23:55:00+00:00
- invalid_ohlc_count=0

## BT結果（要約）
- run_id: `usdjpy_m5_2024_0102_0201_lb5_dedup1_no_fallback`
- trade_count=57
- total_pnl=-0.008999999999946337
- average_pnl=-0.00015789473684116383
- structure_source_counts(trade)=`{'detector_chain_temporal': 57}`
- fallback_used_rate=0.0%
- duplicate_recent_third_candidate_count=0
- max_entries_per_recent_third_candidate=1

## decision_logs要約
- decision_log_count=6270
- fail_stage_counts=`{'structure': 6194, 'direction_alignment': 6, 'none': 57, 'dedup': 13}`
- temporal_candidate_true_count=76
- temporal_candidate=false かつ recent_third_timestamp非空=0
- trade_ok_true_count=57（trade_count一致）

## 次タスク候補
- decision_logs schema validation を優先候補とし、その後複数月拡張または walk-forward runner 設計へ進む。
