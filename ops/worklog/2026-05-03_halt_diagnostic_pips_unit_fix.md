# 2026-05-03 Halt diagnostic pips unit fix

## 1. 初回診断結果（OOS-2 2024-11 OFF trailing）
- halt_window_count=87
- total_halt_minutes=9215
- halted_entry_count=23
- halt_reason_counts=price_shock_halt:44|volatility_spike_halt:75
- avoided_loss_pips=0.001
- missed_profit_pips=0.1687
- net_counterfactual_effect_pips=-0.1677

## 2. 単位問題
- 初回実装では `counterfactual_pnl`（price unit）をそのまま `*_pips` 指標へ加算していた可能性があり、表示名と実値の単位が不一致になり得た。
- USDJPY の場合 `pip_size=0.01` のため、pips 評価は換算が必要。

## 3. 修正方針
- summary 集計で `pnl_pips = counterfactual_pnl / pip_size` を使用。
- `avoided_loss_pips` / `missed_profit_pips` / `net_counterfactual_effect_pips` を pips 単位で再計算。
- `halted_entry_candidates.csv` に `counterfactual_pips` 列を追加。
- summary md に pips換算済みである旨を明記。

## 4. 再実行予定
- 同一条件で OOS-2 2024-11 代表診断を再実行し、単位修正後の指標を確認する。
- 本段階は構造診断であり、収益性確認や閾値本採用を意味しない。
