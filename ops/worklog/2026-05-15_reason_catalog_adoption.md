# 2026-05-15 reason catalog adoption

## 1. 採用判断
- Reason Catalog 最小実装は採用済みとする。
- 採用理由:
  - `risk_reason` / `filter_reason` の管理語彙化を enum化なしで実現できている。
  - 既存ログ出力・売買ロジック・`trade_ok` 判定・PipelineAdapter挙動を維持している。
  - category/detail 互換境界（category保証、detail移行対象）が docs/ops に明記済み。

## 2. 採用時点で確認済み
- `reason_catalog.py` に文字列定数、`normalize_reason_category()`、`normalize_reason_categories()` を実装。
- `category_token[:detail]` 正規化、および `|` 連結reason の category list 化をテストで確認。
- legacy mapping 適用順序（raw prefix優先）を修正済み。

テスト結果（確認済み）:
- `pytest -q tests/unit/risk_filter` -> 38 passed
- `pytest -q tests/integration/test_signal_to_risk_filter.py` -> 8 passed
- `pytest -q tests/unit/backtest/test_pipeline_adapter.py` -> 56 passed
- `git diff --check` -> 問題なし

## 3. 未解決点（後続）
- Evaluator/分析スクリプト側への `normalize_reason_categories()` 適用。
- `all risk filters passed` から canonical 出力への段階移行計画。
- detail旧形式の廃止時期（移行完了タイミング）の判断。

## 4. 次タスク
- Evaluator/分析スクリプト側で category 抽出を前提にした集計経路の適用計画を整理する。

## 5. 非対応範囲（継続）
- lot sizing本体実装。
- OANDA/API接続。
- 実注文。
- 収益性評価。

