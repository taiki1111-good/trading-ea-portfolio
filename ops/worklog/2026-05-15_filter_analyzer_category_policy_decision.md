# 2026-05-15 FilterAnalyzer Category Policy Decision

## 1. 目的
- `src/evaluator/filter_analyzer.py` を category基準化するか判断し、実装前方針を固定する。
- 今回はコード未変更で、互換方針と次実装方式を確定する。

## 2. 現状確認
- `FilterAnalyzer.analyze(logs)` は `filter_reason` の完全一致文字列でbucket化している。
- 欠損時は `"unknown"` に寄せ、warningを返す。
- `FilterStatsResult.filter_reason` は bucket key と同義で扱われている。
- 既存テスト・統合テストで完全一致キー（例: `"spread_too_high"`）が前提になっている。
- `src/backtest/backtest_runner.py` は `filter_stats={}` を直接渡しており、`FilterAnalyzer` は主に evaluator統合経路/テストで利用される。

## 3. 判断結果
- Aを採用する。
- 既存 `analyze()` は維持し、category分析は別メソッド（例: `analyze_by_category()`）を追加する。

## 4. 採用理由
- 既存互換を壊しにくい（既存キーと既存warningを維持可能）。
- 完全一致分析とcategory分析を併存できる。
- scripts側で先行した category 集計との整合確認がしやすい。
- 既存分析を急に置換しないため、段階移行リスクを下げられる。

## 5. 固定ポリシー（実装時）
- 既存 `analyze()` の挙動は変更しない。
- category分析は `normalize_reason_categories()` を使用する。
- `|` 連結reasonは複数categoryへそれぞれ加算する。
- primary categoryのみへの圧縮は Evaluator本体の第1段階では行わない。
- `None` / 空白 / 欠損は unknown 扱い。
- `"None"` が `"none"` category として誤集計されないよう正規化前に空文字化する。

## 6. 未採用案
- B（`analyze(..., category_mode=...)`）:
  - 既存シグネチャ変更により呼び出し側影響の見通しが増えるため今回は不採用。
- C（既存 `analyze()` をcategory置換）:
  - 既存互換を壊すため不採用。
- D（Evaluator本体見送り）:
  - scripts側との整合フェーズを進めるため今回は不採用。

## 7. 未解決点
- 行単位派生列CSVの要否。
- canonical出力への段階移行時期。
- category分析結果の公開先（既存 `filter_stats` と別枠か）を実装時に最終固定。
