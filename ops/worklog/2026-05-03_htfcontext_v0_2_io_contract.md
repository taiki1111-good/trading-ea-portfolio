# 2026-05-03 HTFContext v0.2 I/O Contract & Calculation Policy

## 目的
- Phase 4 HTFContext v0.2 の実装前に、H4 bias / H1 context の初期計算方針と I/O 契約を固定する。
- v0.2 は本採用ではなく、experimental policy 比較として扱う。

## H4/H1 計算方針（初期）
- H4 bias:
  - `up/down/neutral/unknown`
  - MA20/MA50 と MA20 slope を用いた説明可能な最小ルール
- H1 context:
  - `aligned_up/aligned_down/pullback_against_h4/range_or_neutral/transition/unknown`
  - H1 trend と H4 bias の組み合わせで初期ラベル化

## policy 候補
1. `diagnostic_only`
2. `aligned_only`
3. `pullback_permissive`

方針:
- v0.2 初期は `diagnostic_only` を先行し、entry 集合を変えずにラベル分布を観察する。
- entry停止を伴う policy は別フェーズで判断する。

## future leak 防止
- `m5_decision_time = m5_timestamp + 5min`
- 参照可能 HTF は `htf_bar_close_time <= m5_decision_time`
- 未確定 H1/H4、および HTF bar open 中の途中情報は不使用
- aggregation 時の lookahead を禁止

## 未解決事項
- MA window / slope window の最終値（初期仮説のまま）
- `transition` 判定の具体条件
- `neutral` / `unknown` の扱い詳細
- support/resistance との責務境界（Phase 5 分離）
- 実装前に行うか、先に診断スクリプトを追加するかの手順判断

## 注意
- これは収益性確認ではない。
- これは HTF 本採用条件の確定ではない。
