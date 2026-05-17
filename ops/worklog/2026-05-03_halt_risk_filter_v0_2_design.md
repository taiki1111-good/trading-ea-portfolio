# 2026-05-03 Halt Risk Filter v0.2 design

## なぜ独立設計が必要か
- v0.1 は最小核の構造検証完了であり、ユーザー裁量の危険局面回避判断は十分に再現できていない。
- 指標停止・急変停止・ボラ急拡大停止・スプレッド拡大停止は、entry/exitの微調整ではなく別レイヤーの停止判断である。
- そのため v0.2 では Halt / Risk Filter を独立仕様として分離し、v0.1結果と混同しない。

## v0.2 設計の中核
- `scheduled_event_halt`
- `price_shock_halt`
- `volatility_spike_halt`
- `spread_widening_halt`
- `post_event_or_shock_cooldown`

## 方針
- 目的は危険局面回避であり、利益最大化の後付け最適化ではない。
- 閾値は初期仮説として固定し、別期間で確認する。
- API連携は後回しで、初期は手動イベント定義や既存ログで設計検証する。
