# 2026-05-04 near-live dry-run v0.2 pipeline adapter contract audit

## Summary
- `run_csv_replay_pipeline_dry_run.py` 実装前に、既存 `PipelineAdapter` の入力/出力契約を監査した。
- 監査結果として、`csv replay pipeline dry-run` からの呼び出しは「条件付きで安全に可能（Go）」と判断した。
- ただし実装前に `CSV -> PriceBar translator` と `safe call wrapper` の最小仕様固定が必要。

## Audited files
- `src/backtest/pipeline_adapter.py`
- `src/backtest/backtest_runner.py`
- `src/data/types.py`
- `src/backtest/types.py`
- `tests/unit/backtest/test_pipeline_adapter.py`
- `tests/integration/test_end_to_end_minimal_pipeline.py`
- `docs/10_interface_contract.md`
- `docs/04_module_spec.md`
- `docs/17_backtest_design.md`

## Interface findings
- 公開呼び出しは `PipelineAdapter.__call__(current_index, window)`。
- 入力は `List[PriceBar]` 前提で DataFrame 直入力ではない。
- `current_index == len(window)-1` 制約があり、future bar 混入時は `ValueError`。
- 戻り値は `Optional[EntryEvent]`、追加診断は `get_last_decision_trace()` で取得する。

## Future leak and side-effect findings
- `window` が `bars[:i+1]` であれば future leak を避けられる設計。
- HTF集約は completed bar 限定ロジックを持つ。
- `PipelineAdapter` は Execution/broker/API を直接呼ばず、実注文副作用を持たない。
- `real_order_sent` / `broker_order_id` は runner側固定列として保証する設計が妥当。

## Required wrapper before implementation
- `csv row -> PriceBar` 変換（UTC正規化、spread/volume補完）
- 1barごと `window=bars[:i+1]` での adapter 呼び出し
- 例外捕捉して `pipeline_adapter_status=error` をログに残し継続する層
- `EntryEvent + decision_trace` を near-live decision/state/event schema に写像する mapper

## Decision
- 次段で `run_csv_replay_pipeline_dry_run.py` 最小実装検討へ進行可能。
- ただし translator / mapper / error handling の最小仕様固定を先行条件とする。

## Out of scope in this step
- コード変更・テスト変更
- BacktestRunner / PipelineAdapter / Signal / RiskFilter / Execution 変更
- 売買ロジック変更
- OANDA/API接続、実注文、デモ注文
