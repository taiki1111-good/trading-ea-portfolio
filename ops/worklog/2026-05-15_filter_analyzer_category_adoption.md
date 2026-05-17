# 2026-05-15 FilterAnalyzer Category Adoption

## 1. 目的
- `FilterAnalyzer.analyze_by_category()` 実装を採用確定し、Reason Category 系フェーズを第1段階完了として閉じる。

## 2. 採用対象
- `src/evaluator/filter_analyzer.py` の `analyze_by_category(logs)`。
- 既存 `FilterAnalyzer.analyze()` は完全一致bucketとして維持。
- `analyze_by_category()` は `normalize_reason_categories()` を利用。
- `|` 連結reasonは複数categoryへ加算。
- `None` / 空白 / 欠損は `unknown`。
- `"None"` -> `"none"` 誤集計を防止。
- 既存戻り値型互換を維持（`tuple[Dict[str, FilterStatsResult], List[str]]`）。

## 3. 採用理由
- 既存互換を壊さずに category分析を本体Evaluatorへ段階導入できる。
- scripts側（analysis/dry-run summary）で先行した category集計と責務整合が取れる。
- 完全一致分析とcategory分析を併存でき、将来移行の判断材料を保持できる。

## 4. 確認済み
- `pytest -q tests/unit/evaluator/test_filter_analyzer.py` -> 3 passed
- `git diff --check` -> 問題なし

## 5. 非変更確認
- 売買ロジック、`trade_ok`、PipelineAdapter挙動は未変更。
- `scripts/run_csv_replay_pipeline_dry_run.py` は未変更。
- 既存 `FilterAnalyzer.analyze()` のシグネチャ・挙動・warningは未変更。

## 6. フェーズ整理
- Reason Category 系は第1段階完了とする。
- 完了範囲:
  - Reason Catalog 最小実装採用
  - `scripts/analyze_backtest_run_logs.py` 採用
  - `scripts/summarize_csv_replay_dry_run.py` 採用
  - `FilterAnalyzer.analyze_by_category()` 採用

## 7. 次タスク
- lot sizing本体フェーズを独立させるか判断する（優先）。

## 8. 未解決点（後続保持）
- 行単位派生列CSVの要否。
- canonical出力への段階移行。
- detail旧形式の廃止時期。

## 9. 採用判断
- 採用可能 -> 採用済みとして確定。
