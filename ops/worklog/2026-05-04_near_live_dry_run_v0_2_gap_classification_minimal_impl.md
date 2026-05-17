# 2026-05-04 near-live dry-run v0.2 gap classification minimal implementation

## Summary
- Phase 9 CSV replay dry-run skeleton に、`data_gap` 向け gap classification の最小実装を追加した。
- 既存の warning検知・ファイル名・summary主要countは維持した。
- 本変更は運用整合性の診断改善であり、収益性確認ではない。

## Implementation
- 対象:
  - `scripts/run_csv_replay_dry_run.py`
  - `tests/unit/backtest/test_run_csv_replay_dry_run.py`
- `data_gap` warning時に追加する最小列:
  - `gap_class`
  - `expected_gap_flag`
  - `gap_duration`
  - `previous_timestamp`
  - `current_timestamp`
  - `gap_reason`
  - `gap_action`
  - `gap_requires_investigation`
- 分類:
  - `expected_weekend_gap`
  - `ordinary_missing_bar_gap`
  - `unknown_gap`（fallback）
- 既存warning互換:
  - `duplicate_timestamp` / `out_of_order_timestamp` は維持。
  - 上記warningでは gap分類列は空欄デフォルト。
- summary拡張:
  - `expected_weekend_gap_count`
  - `ordinary_missing_bar_gap_count`
  - `unknown_gap_count`
  - 既存 `warning_count` / `data_gap_count` / `duplicate_bar_count` / `out_of_order_count` は維持。

## Test cases
- weekend gap classification test:
  - `2024-01-05T16:55:00Z -> 2024-01-07T17:05:00Z`
  - `gap_class=expected_weekend_gap`
  - `expected_gap_flag=True`
  - `gap_requires_investigation=False`
- ordinary missing bar gap classification test:
  - 平日 `00:00 -> 00:20`
  - `gap_class=ordinary_missing_bar_gap`
  - `expected_gap_flag=False`
  - `gap_requires_investigation=True`
- 既存の duplicate/out_of_order/data_gap 検知テストは維持。

## Scope exclusions
- BacktestRunner / PipelineAdapter / Signal / RiskFilter / Execution の変更なし。
- 売買ロジック変更なし。
- HTF/SR/Session/RiskStop/Halt のfilter化なし。
- OANDA/API接続なし。
- 実注文・デモ注文なし。
- 祝日/メンテナンスカレンダー未導入（将来候補）。

## Next steps
1. 代表M5 sliceでユーザー実行により再確認。
2. `expected_market_closure_gap` / `unexpected_market_hours_gap` の導入要否判断。
3. dry-run summary の Validation Framework 接続方式を設計。
