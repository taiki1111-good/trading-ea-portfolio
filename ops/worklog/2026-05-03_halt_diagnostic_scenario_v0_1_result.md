# 2026-05-03 halt diagnostic scenario v0.1 結果記録

## 対象
- OOS-2 2024-11 OFF trailing
- Phase 2 cooldown / threshold diagnostic scenario v0.1（A〜F）

## 6シナリオ結果サマリ
- A `initial_combined`: `net_counterfactual_effect_pips=-16.77`
- B `cooldown_short_combined`: `net_counterfactual_effect_pips=-13.55`
- C `price_shock_only_initial`: `net_counterfactual_effect_pips=-6.07`
- D `volatility_only_initial`: `net_counterfactual_effect_pips=-13.32`
- E `volatility_less_sensitive`: `net_counterfactual_effect_pips=-3.75`
- F `volatility_less_sensitive_short_cooldown`: `net_counterfactual_effect_pips=-3.05`

## 解釈
- A〜F 全シナリオで `net_counterfactual_effect_pips` はマイナス。
- combined 系 A/B は停止範囲が広く、代表月では副作用が大きい。
- C も利益機会停止が目立つ。
- D は過剰停止の主因候補として整合。
- E/F は相対的に副作用が小さいが、Go 判定には至らない。

## 候補整理
- 棄却候補: A / B / C / D
- 保留候補: E / F
- 複数月確認に回すなら F を第一候補。
- ただし F は本採用・本体統合候補ではない。

## 判断
- Phase 3 integration は引き続き No-Go。
- 追加の細かい閾値探索は行わない。

## 次の分岐
1. F を複数月確認する。
2. Halt Filter を一時保留して Phase 4 HTFContext へ進む。

## 注意
- これは収益性確認ではない。
- これは閾値本採用ではない。
