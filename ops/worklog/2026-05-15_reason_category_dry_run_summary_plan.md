# 2026-05-15 Reason Category Dry-run Summary Plan

## 1. 目的
- dry-run summary側に reason category 正規化を適用すべきか判断し、実装前方針を固定する。
- 今回は実装コードを変更せず、適用要否・対象列・互換方針・実装範囲のみを確定する。

## 2. 現状確認
- `scripts/summarize_csv_replay_dry_run.py` は health/status/warnings 中心の二次summary。
- 現時点で reason category 集計は未実装。
- `scripts/run_csv_replay_pipeline_dry_run.py` の `near_live_decision_logs.csv` には `filter_reason` / `signal_reason` / `decision_reason` がある。
- `risk_reason` は現行 near-live decision logs の標準列ではない。

## 3. 判断結果
- 判断候補A/B/Cのうち **Aを採用**。
- ただし最小実装に限定し、`summarize_csv_replay_dry_run.py` の派生メトリクス追加だけを次フェーズ対象にする。

## 4. 方針（実装前固定）
- 変更対象:
  - `scripts/summarize_csv_replay_dry_run.py`
- 非変更対象:
  - `scripts/run_csv_replay_pipeline_dry_run.py`（ログ生成形式は変更しない）
  - `src/evaluator/`
  - `src/backtest/`
  - `src/risk_filter/`

## 5. 集計対象列
- 主対象（category 集計）:
  - `risk_reason`（列が存在する場合のみ）
  - `filter_reason`
- 対象外（自由文として維持）:
  - `decision_reason`
  - `signal_reason`

## 6. 互換ポリシー
- 既存 `near_live_summary.csv/.md` の既存項目は削除・改名しない。
- 既存 `dry_run_period_summary.csv/.md` の既存項目は削除・改名しない。
- 既存列置換は行わず、派生メトリクス追加のみ。
- `None` / 空白 / 欠損は unknown 扱い。
- `"none"` category の誤集計を防止する。
- 共通helper化は急がず、`normalize_reason_categories()` 利用に留める。

## 7. 追加メトリクス案（次フェーズ）
- `risk_reason_category_counts`
- `filter_reason_category_counts`
- `risk_reason_primary_category_counts`
- `filter_reason_primary_category_counts`
- `risk_reason_unknown_count`
- `filter_reason_unknown_count`

補足:
- `risk_reason` 列が存在しない run では unknown として集計、または 0件扱いのどちらかを実装時に固定する。

## 8. 未解決点
- 行単位派生列CSVの要否。
- `src/evaluator/filter_analyzer.py` の category基準化判断。
- canonical出力への段階移行判断。
