# 2026-05-15 Reason Category Dry-run Summary Adoption

## 1. 目的
- dry-run summary側 reason category 派生メトリクス実装を採用確定し、ops上で状態を閉じる。

## 2. 採用対象
- `scripts/summarize_csv_replay_dry_run.py` の最小追加実装。
- 対象ログ:
  - `near_live_decision_logs.csv`
- 対象列:
  - `filter_reason`
  - `risk_reason`（列が存在する場合）
- 追加メトリクス:
  - `risk_reason_category_counts`
  - `filter_reason_category_counts`
  - `risk_reason_primary_category_counts`
  - `filter_reason_primary_category_counts`
  - `risk_reason_unknown_count`
  - `filter_reason_unknown_count`

## 3. 採用理由
- 既存summary互換（削除・改名なし）を維持したまま、reason語彙の構造追跡を追加できる。
- dry-run health/status/warnings中心の責務を維持しつつ、診断補助として有効。
- `risk_reason` 列なしと値欠損を分離した仕様（列なしは集計対象外、列あり欠損はunknown）が明確である。
- `"none"` category 誤集計防止を実装・テストで固定できている。

## 4. 確認済み
- `pytest -q tests/unit/backtest/test_summarize_csv_replay_dry_run.py` -> 18 passed
- `pytest -q tests/unit/risk_filter` -> 38 passed
- `pytest -q tests/unit/backtest/test_analyze_backtest_run_logs.py` -> 2 passed
- `git diff --check` -> 問題なし

## 5. 非変更確認
- `near_live_summary.csv/.md` は未変更。
- `scripts/run_csv_replay_pipeline_dry_run.py` は未変更。
- `src/evaluator/` / `src/backtest/` / `src/risk_filter/` は未変更。
- 売買ロジック、`trade_ok` 判定、PipelineAdapter挙動は未変更。

## 6. 次タスク
- `src/evaluator/filter_analyzer.py` の category基準化判断へ進む。

## 7. 未解決点
- evaluator側 category基準化。
- 行単位派生列CSVの要否。
- canonical出力への段階移行。

## 8. 採用判断
- 採用可能 -> 採用済みとして確定。
