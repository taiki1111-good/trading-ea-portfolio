# 2026-05-15 Reason Category Dry-run Summary Implementation

## 1. 目的
- `scripts/summarize_csv_replay_dry_run.py` に reason category 派生メトリクスを最小追加し、dry-run summary 側の第1段階実装を完了する。

## 2. 実装内容
- `normalize_reason_categories()` を利用して `near_live_decision_logs.csv` の reason を category 集計する処理を追加した。
- 追加メトリクス:
  - `risk_reason_category_counts`
  - `filter_reason_category_counts`
  - `risk_reason_primary_category_counts`
  - `filter_reason_primary_category_counts`
  - `risk_reason_unknown_count`
  - `filter_reason_unknown_count`
- 出力反映:
  - `dry_run_period_summary.csv`
  - `dry_run_period_summary.md`

## 3. 互換方針
- 既存 `dry_run_period_summary` の既存項目は削除・改名しない。
- 既存 `near_live_summary.csv/.md` は変更しない。
- `scripts/run_csv_replay_pipeline_dry_run.py` のログ生成形式は変更しない。

## 4. missing-column / unknown 方針
- `filter_reason`:
  - 列あり + 値欠損（None/空白/欠損） -> unknown
- `risk_reason`:
  - 列あり + 値欠損（None/空白/欠損） -> unknown
  - 列なし -> 集計対象外（counts空、unknown_count=0）
- `"None"` -> `"none"` の誤category化は防止する（正規化前に空文字化）。

## 5. テスト
- `tests/unit/backtest/test_summarize_csv_replay_dry_run.py` に以下を追加:
  - `filter_reason` の canonical category 集計
  - 複合reason（`risk_contract_invalid | invalid_lot`）の category/primary 集計
  - `risk_reason` 複合reasonの集計
  - 列あり欠損時の unknown 集計
  - `"none"` 非出現
  - `risk_reason` 列なし時の counts空 / unknown_count=0

## 6. 未解決点
- `analyze_backtest_run_logs.py` との共通helper化は未実施（今回は最小実装優先）。
- `src/evaluator/filter_analyzer.py` 側の category基準化判断は後続。
- 行単位派生列CSVの要否判断は後続。
- canonical出力への段階移行判断は後続。
