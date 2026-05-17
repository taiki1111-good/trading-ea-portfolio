# 2026-05-03 HTFContext v0.2 semantics refinement

## 背景
warmup対応により unknown 比率は大幅改善したが、`htf_v2_direction_allowed` / `htf_v2_conflict_flag` の意味が曖昧で、diagnostic_only結果の解釈にぶれが残った。

## 問題整理
- `diagnostic_only` でも `aligned_up/aligned_down` 行で `htf_v2_direction_allowed=False` があり、active policy判定か仮想判定かが不明瞭。
- `neutral/range_or_neutral` でも `htf_v2_conflict_flag=True` になり、hard conflict と uncertainty が混在していた。

## 実装内容
- `htf_v2_direction_allowed` は active policy列として維持。
- 仮想policy比較用の列を追加:
  - `htf_v2_candidate_direction`
  - `htf_v2_aligned_only_allowed`
  - `htf_v2_pullback_permissive_allowed`
  - `htf_v2_context_uncertain_flag`
  - `htf_v2_hard_conflict_flag`
- `htf_v2_conflict_flag` は後方互換維持のため残し、`hard_conflict` と同義に寄せた。
- `diagnostic_only` の `entry_signal/trade_ok` は変更せず、`htf_v2_filter_reason=diagnostic_only:no_entry_filter` を維持。

## 判定ルール（要点）
- `aligned_only_allowed`
  - long候補: `h4_bias=up` and `h1_context=aligned_up`
  - short候補: `h4_bias=down` and `h1_context=aligned_down`
- `pullback_permissive_allowed`
  - long候補: `h4_bias=up` and `h1_context in {aligned_up, pullback_against_h4}`
  - short候補: `h4_bias=down` and `h1_context in {aligned_down, pullback_against_h4}`
- `context_uncertain_flag`
  - `h4_bias in {neutral, unknown}` or `h1_context in {unknown, range_or_neutral}`
- `hard_conflict_flag`
  - long候補で `h4_bias=down` or `h1_context=aligned_down`
  - short候補で `h4_bias=up` or `h1_context=aligned_up`

## テスト
- diagnostic_onlyでentry非変更（HTF v2 disabledとの同等性）を確認。
- long/short の aligned_only allowed 条件を確認。
- long/short の pullback permissive allowed 条件を確認。
- uncertain/hard_conflict の分離条件を確認。
- decision trace に新列が含まれることを確認。

## 未解決事項
1. warmupあり代表run再実行後の新semantic列分布確認。
2. `htf_v2_conflict_flag` を将来削除するか（互換期間の方針）。
3. `candidate_direction=unknown` 行の解釈ルール（集計時の扱い）を運用で固定するか。

## 注意
- 重いbacktestは本作業で実行していない。
- 実filter化（aligned_only / pullback_permissive）には進んでいない。
- これは収益性確認ではない。
