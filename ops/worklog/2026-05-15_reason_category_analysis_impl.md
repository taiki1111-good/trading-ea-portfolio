# 2026-05-15 reason category analysis impl

## 1. 目的
- analysis script 限定で `risk_reason` / `filter_reason` の category 集計を追加する。
- 既存ログ列や既存metricを壊さず、派生集計のみ追加する。

## 2. 実装内容
対象:
- `scripts/analyze_backtest_run_logs.py`

変更:
- `normalize_reason_categories()` を import。
- `_build_reason_category_metrics(rows)` を追加し、以下を算出:
  - `risk_reason_category_counts`
  - `filter_reason_category_counts`
  - `risk_reason_primary_category_counts`
  - `filter_reason_primary_category_counts`
  - `risk_reason_unknown_count`
  - `filter_reason_unknown_count`
- primary category は list 先頭、空なら `unknown`。
- 既存 `metrics` dict に上記を追加。
- `trade_log_analysis.md` に上記6項目を追記。
- 第1段階は summary metrics 追加に限定し、`risk_reason_categories` / `filter_reason_categories` の行単位派生列CSVは作成しない。
- 行単位派生列は後続候補として保持する。

非変更:
- `src/evaluator/` 本体未変更。
- `src/backtest/` 未変更。
- `src/risk_filter/` 未変更。
- 売買ロジック・`trade_ok` 判定・PipelineAdapter挙動未変更。
- 既存metric名の削除・改名なし。

## 3. 互換方針
- 既存CSV列（`risk_reason` / `filter_reason` / `decision_reason`）は置換しない。
- category正規化は分析時の派生集計として扱う。
- `exit_reason` 完全一致集計は現行維持。

## 4. テスト
追加テスト:
- `tests/unit/backtest/test_analyze_backtest_run_logs.py`
  - multi reason / legacy / detail / empty -> unknown を検証。

実行結果:
- `pytest -q tests/unit/risk_filter` -> 38 passed
- `pytest -q tests/integration/test_signal_to_risk_filter.py` -> 8 passed
- `pytest -q tests/unit/backtest/test_pipeline_adapter.py` -> 56 passed
- `pytest -q tests/unit/backtest/test_analyze_backtest_run_logs.py` -> 1 passed
- `git diff --check` -> 問題なし

## 5. 未解決点
- Evaluator本体（`src/evaluator/filter_analyzer.py`）への category基準化は後続。
- canonical出力への段階移行（`all risk filters passed` -> `all_risk_filters_passed`）は後続。
- detail旧形式の廃止時期は後続判断。

