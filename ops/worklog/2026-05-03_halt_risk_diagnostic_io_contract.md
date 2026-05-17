# 2026-05-03 Halt/Risk diagnostic I/O contract

## 1. 実施内容
- Phase 2（Halt/Risk diagnostic layer）向けに、`price_shock_halt` / `volatility_spike_halt` の I/O contract を文書化。
- 診断スクリプト候補 `scripts/diagnose_halt_filters_on_m5_slice.py` の入力引数、必須入力列、出力スキーマを固定。
- halt window 統合ルール（重複結合、複数理由保持、cooldown終端の扱い）を明文化。
- summary 指標（avoided loss / missed profit を併記）を固定。

## 2. I/O contract 固定が必要な理由
- 本体統合前に診断仕様を固定しないと、結果解釈と比較条件が会話ごとにぶれる。
- 閾値調整の恣意性を避けるため、入出力契約と判定式を先に凍結する必要がある。
- Halt filter は利益最大化ではなく危険局面回避診断であるため、評価軸を `trade_count` 単独にしないルールを事前固定する必要がある。

## 3. 方針
- Phase 2 は counterfactual 診断に限定し、売買ロジック変更や RiskFilter/PipelineAdapter 統合は行わない。
- `scheduled_event_halt` / `spread_widening_halt` は後続フェーズへ分離する。
- 閾値は初期仮説であり、本採用は Phase 3 以降の判断とする。
