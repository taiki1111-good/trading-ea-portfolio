# 2026-05-17 HTF entry set diff summary (near_live diagnostic)

## 目的
- `scripts/run_htf_diagnostic_comparison.py` に、HTF OFF / permissive / strict の3条件で entry候補集合差分を比較できる最小summaryを追加する。
- 目的は near_live diagnostic comparison の説明可能性向上であり、収益性評価ではない。

## 実装方針（v0）
- entry候補集合の抽出条件: `entry_signal == True`。
- 比較キー: `timestamp + signal_type`。
- timestamp列は既存decision log列を優先し、`timestamp` を第一優先、欠損時のみ `log_time` をfallback使用。
- `htf_off` を基準集合として、permissive/strict との removed/added/intersection を件数で集計。

## 追加したsummary項目
- `entry_set_count`
- `entry_set_only_in_htf_off_count`
- `entry_set_only_in_condition_count`
- `entry_set_intersection_count`
- `entry_set_removed_vs_htf_off_count`
- `entry_set_added_vs_htf_off_count`

## 互換性
- 既存 `htf_diagnostic_comparison_summary.csv` / `.md` の既存項目は削除・改名しない。
- additive な列追加のみ実施。
- HTF filter本体のON化、売買判断、PnL集計、実注文関連には変更なし。

## 注意書き
- このentry集合差分は near_live diagnostic comparison 用であり、収益性評価ではない。
- PnL評価ではない。
- HTF filter本体採用ではない。
- `timestamp + signal_type` は v0比較キーであり、将来より厳密なキーへ拡張可能。
