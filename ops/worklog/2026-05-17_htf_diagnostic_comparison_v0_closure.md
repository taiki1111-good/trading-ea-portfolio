# 2026-05-17 HTF diagnostic comparison v0 closure

## 目的
- HTF diagnostic comparison v0 を、現時点の到達点でいったん完了扱いとして整理する。
- 今回は ops 記録の更新のみとし、追加実装は行わない。

## v0 到達点
- 3条件 runner（`htf_off` / `htf_permissive` / `htf_strict`）は実装済み。
- representative run は実施済み。
- 以下の実出力確認は完了済み。
  - candidate entry set summary（`entry_set_*`）
  - accepted entry set summary（`accepted_entry_set_*`）
  - htf_rejected entry set summary（`htf_rejected_entry_set_*`）

## 代表runの解釈（現時点）
- candidate entry set は3条件で同一。
- accepted entry set も3条件で同一。
- `htf_rejected_entry_set` も3条件で0件。
- ただし `htf_filter_rejected_count` は permissive/strict で2件。
- したがって、今回の代表fixtureでは HTF rejection観測は `entry_signal==True` の候補行には反映していない。

## scope note
- これは収益性評価ではない。
- HTF filter採用判断ではない。
- 本体filter ON化ではない。
- near_live diagnostic comparison の説明可能性向上を目的とした整理である。

## future optional（現時点では非優先）
- 必要になれば、`entry_signal` 非依存の全行ベース HTF rejection trace を追加できる。
- ただし現時点では優先しない。

## 次タスク候補
- lot sizing shadow comparison の軽微修正・採用確認へ戻る。
- または portfolio docs / README / presentation notes の整理へ進む。
