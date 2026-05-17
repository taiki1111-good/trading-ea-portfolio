# 2026-05-17 htf accepted/rejected entry set diff summary impl

## 目的
- HTF diagnostic comparison runner で、candidate entry（候補生成）と accepted/rejected（通過判定/HTF rejection）を分離して説明可能にする。
- 収益性評価ではなく near_live diagnostic comparison の可観測性向上を目的とする。

## 実装内容
- 既存 `entry_signal == True` の `entry_set_*` は維持（candidate entry set として扱う）。
- 新規 `accepted_entry_set`（v0）を追加:
  - 定義: `entry_signal == True AND trade_ok == True`
  - キー: `timestamp + signal_type`（`timestamp` 欠損時 `log_time` fallback）
- 新規 `htf_rejected_entry_set`（v0）を追加:
  - 定義: `entry_signal == True AND htf_filter_rejected == True`
  - 判定列:
    - `htf_filter_rejected` 列が存在する場合はその列を使用
    - 非存在時は既存runner互換として `htf_filter_enabled == True AND htf_direction_aligned == False` を使用
  - decision log に新規列は追加しない（既存列のみで判定）

## 追加したsummary項目
- accepted entry set（`htf_off` 基準比較）
  - `accepted_entry_set_count`
  - `accepted_entry_set_only_in_htf_off_count`
  - `accepted_entry_set_only_in_condition_count`
  - `accepted_entry_set_intersection_count`
  - `accepted_entry_set_removed_vs_htf_off_count`
  - `accepted_entry_set_added_vs_htf_off_count`
- htf rejected entry set（条件別 + `htf_off`比較）
  - `htf_rejected_entry_set_count`
  - `htf_rejected_entry_set_vs_htf_off_added_count`
  - `htf_rejected_entry_set_vs_htf_off_intersection_count`

## テスト
- 3条件mock decision logsで以下を固定:
  - candidate entry set は同一だが、`htf_rejected_entry_set` で差分が出るケース
  - `trade_ok` 差分に応じて `accepted_entry_set` が変わるケース
  - permissive/strict が別々に集計されること
  - 既存 summary 出力テストを維持

## 解釈上の注意
- `entry_set_*` は候補生成の集合であり、HTF filterの通過判定差分を直接表すとは限らない。
- `accepted_entry_set_*` は `trade_ok` 依存のため、HTF rejection が `trade_ok` に反映されない設計では差分が出ない可能性がある。
- `htf_rejected_entry_set_*` は HTF rejection そのものを見るための diagnostic 集合である。
- これは収益性評価ではない。
- HTF filter本体採用判断ではない。
