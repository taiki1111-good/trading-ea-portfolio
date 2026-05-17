# 2026-05-02 temporal duplicate entry control

## 実施内容
- PipelineAdapterConfig に `max_entries_per_recent_third_candidate: int | None = None` を追加。
- PipelineAdapter に run 内状態として recent_third_timestamp ごとの entry 回数を保持する制御を追加。
- `max_entries_per_recent_third_candidate=1` で同一 candidate の2回目以降 entry を抑止。
- BacktestRunner 実行開始時に `entry_event_provider.reset_run_state()` を呼び出し、run 間の状態リークを防止。
- `scripts/run_backtest_on_m5_slice.py` に `--max-entries-per-recent-third-candidate` CLI を追加。
- `scripts/compare_temporal_lookback_runs.py` に dedup 設定列（notes由来）を追加。
- unit/integration テストを追加し、既定値維持・重複抑止・別timestamp許可・run間状態分離を確認。
- `docs/17_backtest_design.md` に temporal 再利用制御の方針を短く追記。

## 注意
- 本変更は構造検証目的であり、収益性最適化は目的外。
- spread=0.2 pips fallback 前提、手数料/スリッページ/スワップ未反映。
