# 2026-05-03 halt cooldown / threshold diagnostic scenario v0.1

## 背景
- OOS-2 2024-11 OFF trailing の初期診断・分離診断で、combined / price_shock only / volatility_only の全シナリオが `net_counterfactual_effect_pips < 0`。
- 初期閾値のまま Phase 3 本体統合には進まない（No-Go）。
- 過剰停止の主因候補は `volatility_spike_halt`。

## なぜ候補セットを事前固定するか
- 結果を見ながら threshold/cooldown を逐次変更すると、比較の再現性と判断の一貫性が崩れる。
- Go/No-Go 判断を設計として成立させるため、候補セットと評価指標を先に固定する。
- これは最適化ではなく、過剰停止の要因分解を目的とした診断シナリオである。

## なぜ逐次最適化しないか
- 都合のよい後追い調整は、Phase 2 診断と Phase 3 統合判断を混同させる。
- 単月の偶然に過適合し、複数月で再現しないリスクが高い。
- そのため v0.1 では A〜F の候補セットを固定し、途中で細かい閾値探索を追加しない。

## v0.1 実行候補（固定）
1. `initial_combined`
2. `cooldown_short_combined`
3. `price_shock_only_initial`
4. `volatility_only_initial`
5. `volatility_less_sensitive`
6. `volatility_less_sensitive_short_cooldown`

## 方針
- 代表月（OOS-2 2024-11）で明らかに悪いシナリオは棄却候補化。
- 改善が見えたもののみ複数月確認候補に進める。
- Phase 3 本体統合は保留のまま。

## 注意
- これは収益性確認ではない。
- これは閾値本採用ではない。
