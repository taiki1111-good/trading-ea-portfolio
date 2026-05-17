# 2026-05-04 near-live dry-run v0.2 pipeline dry-run minimal implementation

## Summary
- Option A 方針に基づき、`scripts/run_csv_replay_pipeline_dry_run.py` を新規追加した。
- 既存 `run_csv_replay_dry_run.py` は維持し、PipelineAdapter 接続版を別スクリプトとして分離した。
- 目的は収益性評価ではなく、CSV replay から `PipelineAdapter` を安全に呼び、no-real-order 制約を維持した near-live 風ログ生成である。

## Implemented files
- `scripts/run_csv_replay_pipeline_dry_run.py`
- `tests/unit/backtest/test_run_csv_replay_pipeline_dry_run.py`
- `docs/17_backtest_design.md`
- `ops/CURRENT_TASKS.md`

## Implemented behavior
- CSV replay / warmup-replay split / gap warning は既存方針を踏襲。
- `CSV row -> PriceBar` 変換を追加:
  - `spread_pips` 優先、次に `spread`、なければ `0.0`
  - `volume` 未指定時 `0.0`
  - timestamp UTC正規化
- replay bar ごとに `window=bars[:i+1]`、`current_index=len(window)-1` で `PipelineAdapter` を呼ぶ。
- 例外時は run を止めず、`pipeline_adapter_status=error` と `pipeline_adapter_error` event を記録して継続。
- `EntryEvent` は実注文ではなく `paper_candidate` として扱う。

## no_real_order_integrity
- `real_order_sent=False` を固定出力。
- `broker_order_id=""` を固定出力。
- `paper_order_action` は `none` / `paper_candidate` のみ。
- `no_real_order_integrity_violation_count` を summary で集計。

## Output files
- `near_live_decision_logs.csv`
- `near_live_event_logs.csv`
- `near_live_state_logs.csv`
- `near_live_validation_warnings.csv`
- `near_live_summary.csv`
- `near_live_summary.md`

## Tests
- `tests/unit/backtest/test_run_csv_replay_pipeline_dry_run.py` を追加。
- 変換、正常呼び出し、EntryEvent、例外継続、integrity、出力ファイル生成を確認。
