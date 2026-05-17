# 2026-05-03 Phase 3 Halt/Risk Integration Go/No-Go Criteria

## なぜ Go/No-Go 基準が必要か
- Phase 2 で `price_shock_halt` / `volatility_spike_halt` の副作用が観測されており、Phase 3 本体統合前に判断基準を先に固定する必要がある。
- 事後的に結果へ合わせて threshold/cooldown を逐次調整すると、比較の再現性と判断の一貫性が崩れる。
- そのため、Phase 3 へ進む前に Go 条件 / No-Go 条件を文書化し、診断シナリオ運用を固定する。

## 今回の診断結果が No-Go である理由（OOS-2 2024-11 OFF trailing）
- combined: `net_counterfactual_effect_pips=-16.77`、`missed_profit_pips=16.87`、`avoided_loss_pips=0.10`
- price_shock only: `net_counterfactual_effect_pips=-6.07`、`missed_profit_pips=6.07`、`avoided_loss_pips=0.00`
- volatility_spike only: `net_counterfactual_effect_pips=-13.32`、`missed_profit_pips=13.42`、`avoided_loss_pips=0.10`
- 全シナリオで `net_counterfactual_effect_pips` がマイナス。
- `missed_profit_pips` が `avoided_loss_pips` を大きく上回る。
- `volatility_spike_halt` は発火数・停止時間が大きく、過剰停止の主因候補。
- よって初期閾値のまま Phase 3 本体統合は No-Go。

## 次の Phase 2 diagnostic scenario 方針
1. Go/No-Go基準の確認。
2. cooldown影響診断のシナリオ設計。
3. `volatility_spike_halt` の過剰発火要因分析。
4. threshold/cooldown候補比較を行う場合は diagnostic scenario として事前固定。
5. Phase 3統合は保留。

## 注意
- これは収益性確認ではない。
- これは閾値本採用ではない。
