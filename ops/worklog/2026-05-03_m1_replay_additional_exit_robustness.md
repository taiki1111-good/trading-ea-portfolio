# 2026-05-03 additional M1 replay exit robustness

## 対象
- OOS-1 2024-08 OFF trailing entry群
- OOS-2 2024-12 OFF trailing entry群

## 結果
### OOS-1 2024-08
- `baseline_fixed_exit`: `total_pnl=-0.090`, `win_rate=28.07`
- `simple_trailing_after_1R`: `total_pnl=1.236`, `win_rate=56.14`
- `simple_trailing_after_1R_conservative`: `total_pnl=0.699`, `win_rate=31.58`
- `simple_trailing_after_1R_next_bar_activation`: `total_pnl=-0.047`, `win_rate=31.58`

### OOS-2 2024-12
- `baseline_fixed_exit`: `total_pnl=0.220`, `win_rate=42.50`
- `simple_trailing_after_1R`: `total_pnl=0.663`, `win_rate=56.25`
- `simple_trailing_after_1R_conservative`: `total_pnl=0.502`, `win_rate=46.25`
- `simple_trailing_after_1R_next_bar_activation`: `total_pnl=0.246`, `win_rate=46.25`

## 解釈
- `simple_trailing_after_1R` は追加月でも `baseline_fixed_exit` を上回り、M1 replayでも強さを維持した。
- `simple_trailing_after_1R_conservative` でも `baseline_fixed_exit` を上回ったため、trailing優位は完全なM5楽観だけではなさそうである。
- ただし `simple_trailing_after_1R_next_bar_activation` では優位が大きく縮み、発動タイミング仮定依存は明確。
- permissive HTF policy はM1 replayで補助効果未確認のため優先度を後退させる。

## 次タスク
1. cost / slippage / swap 反映方針の設計へ進む。
2. conservative を現実寄り主比較候補として扱うか検討する。
3. next_bar_activation はストレステスト軸として継続し、優位縮小要因を分析する。
4. permissive は補助効果不安定候補として記録・監視を継続する。

## 前提維持
- 本記録は本採用・収益性確認・実運用可能性確認ではない。
- `simple_trailing_after_1R` / `simple_trailing_after_1R_conservative` / permissive は本採用扱いしない。
- M1 replay でも同一バー内 OHLC 順序曖昧性は完全には消えない。
