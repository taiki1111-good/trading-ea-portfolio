# 2026-05-15 FilterAnalyzer Category Implementation

## 1. 目的
- `src/evaluator/filter_analyzer.py` に category集計用 `analyze_by_category(logs)` を追加する。
- 既存 `analyze()` のシグネチャ・挙動・warning互換は維持する。

## 2. 実装内容
- `FilterAnalyzer.analyze_by_category(logs)` を追加。
- `normalize_reason_categories()` を利用して category集計。
- `filter_reason` が `|` 連結の場合、複数categoryへそれぞれ加算。
- `None` / 空白 / 欠損は `unknown` へ加算。
- `"None"` が `"none"` category へ誤変換されないよう、category正規化前に空文字扱い。

## 3. 互換方針
- 既存 `FilterAnalyzer.analyze()` は未変更。
- 既存 `FilterStatsResult.filter_reason` は bucket key として維持。
- 既存完全一致集計と category集計を併存。

## 4. テスト
- 既存の `analyze()` 完全一致bucketテストを維持。
- `analyze_by_category()` の追加テストで以下を固定:
  - legacy `"all risk filters passed"` の canonical化
  - `risk_contract_invalid | invalid_lot` の複数category加算
  - 欠損/空白/None の unknown化
  - `"none"` category 非出現

## 5. 未解決点
- category集計結果を Evaluatorのどの公開出力へ載せるかは後続判断。
- canonical出力への段階移行タイミングは後続判断。
