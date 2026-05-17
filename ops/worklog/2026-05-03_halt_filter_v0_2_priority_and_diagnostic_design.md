# 2026-05-03 Halt Filter v0.2 Priority and Diagnostic Design

## 1. 実施内容
- `docs/17_backtest_design.md` に `Halt / Risk Filter v0.2 Implementation Priority` を追加。
- v0.2 停止フィルターの実装優先順位を P1/P2/P3 で明文化。
- 最初の着手を本体統合ではなく診断スクリプト先行とする方針を明記。
- 診断スクリプト案 `scripts/diagnose_halt_filters_on_m5_slice.py` の入出力・初期閾値・評価観点を記録。
- `ops/CURRENT_TASKS.md` の現在段階を `v0.2 Halt Filter implementation priority / diagnostic design` に更新。
- 次タスクを `price_shock_halt` / `volatility_spike_halt` 診断設計中心に更新。

## 2. 先行対象を price_shock / volatility_spike にした理由
- 既存の M5 価格データだけで検証可能で、追加データ依存が小さい。
- `scheduled_event_halt` はイベントCSV/カレンダー仕様の先行設計が必要。
- `spread_widening_halt` は現行 slice が `spread=0.2 pips fallback` 前提で、実 spread 変動の検証ができない。
- `post_event_or_shock_cooldown` は shock / spike 検出後に付随設計するのが自然。

## 3. 注意点
- これは収益改善の後付け最適化ではなく、危険局面回避の診断整理。
- 閾値は本採用値ではなく初期仮説として固定。
- Q1/Q2/OOS 結果に合わせた都合の良い閾値調整は行わない。
- 先に診断を実施し、その後 `Candidate Freeze v0.2` として固定する。
