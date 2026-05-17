# 2026-05-03 Phase 2 Halt/Risk pause と Phase 4 HTFContext 遷移判断

## 背景
- OOS-2 2024-11 OFF trailing に対する Phase 2 diagnostic scenario v0.1（A〜F）を実施。
- 全シナリオで `net_counterfactual_effect_pips` がマイナス。
- Phase 3 Go/No-Go Criteria に照らして Phase 3 integration は No-Go。

## 6シナリオ結果（要約）
- A: `halted_entry_ratio=0.359375`, `total_halt_minutes=9215.0`, `net=-16.77`
- B: `halted_entry_ratio=0.25`, `total_halt_minutes=6415.0`, `net=-13.55`
- C: `halted_entry_ratio=0.171875`, `total_halt_minutes=5495.0`, `net=-6.07`
- D: `halted_entry_ratio=0.265625`, `total_halt_minutes=7040.0`, `net=-13.32`
- E: `halted_entry_ratio=0.125`, `total_halt_minutes=4670.0`, `net=-3.75`
- F: `halted_entry_ratio=0.109375`, `total_halt_minutes=2875.0`, `net=-3.05`

## 判断
- Phase 3 integration は No-Go 維持。
- Halt Filter は一時保留。
- 本線は Roadmap の次フェーズである Phase 4 HTFContext v0.2 へ進む。

## 候補整理
- 棄却候補: A / B / C / D
- 保留候補: E / F
- F は副作用最小だが net negative のため Phase 3 候補ではない。
- F は将来の複数月確認候補としてのみ保留。

## なぜ Phase 4 へ進むか
- Phase 2 初期候補群で Phase 3 Go 条件を満たす Halt 条件が確認できていない。
- 追加の細かい threshold/cooldown 探索は逐次最適化リスクが高く、Phase 2 運用制約に反する。
- そのため Halt は一時保留し、HTFContext 側の構造課題へ優先的に進む。

## 注意
- これは収益性確認ではない。
- これは閾値本採用ではない。
