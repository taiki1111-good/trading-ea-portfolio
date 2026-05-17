# 2026-05-15 Reason Category Analysis Adoption

## 1. 目的
- `scripts/analyze_backtest_run_logs.py` の Reason category 集計実装（analysis script 第1段階）を採用確定し、ops上で状態を閉じる。

## 2. 採用対象
- `normalize_reason_categories()` を利用した summary metrics 追加。
- 対象列:
  - `risk_reason`
  - `filter_reason`
- 追加メトリクス:
  - `risk_reason_category_counts`
  - `filter_reason_category_counts`
  - `risk_reason_primary_category_counts`
  - `filter_reason_primary_category_counts`
  - `risk_reason_unknown_count`
  - `filter_reason_unknown_count`

## 3. 採用理由
- 既存ログ列を置換せず、派生メトリクス追加に限定しているため影響範囲が小さい。
- 既存metric名の削除・改名を伴わず、後方互換を維持している。
- `None` / 空白 / 欠損を unknown 扱いに統一し、`"none"` category の誤集計を防止できる。
- reason語彙を category 軸で集計可能にし、後続の Evaluator/dry-run summary 適用検討の前提を満たす。

## 4. 確認済みテスト
- `pytest -q tests/unit/backtest/test_analyze_backtest_run_logs.py` -> 2 passed
- `pytest -q tests/unit/risk_filter` -> 38 passed
- `git diff --check` -> 問題なし

## 5. 未解決点（後続判断）
- dry-run summary側への reason category 適用判断。
- `src/evaluator/filter_analyzer.py` の category基準化判断。
- 行単位派生列CSVの要否。
- canonical出力への段階移行方針。

## 6. 次タスク
- 推奨A: dry-run summary側への reason category 適用要否を先に判断する。
  - 理由: Evaluator本体より影響範囲が小さく、段階導入しやすい。
- B: `src/evaluator/filter_analyzer.py` の category基準化要否を判断する。

## 7. 採用判断
- 採用可能 -> 採用済みとして確定。
