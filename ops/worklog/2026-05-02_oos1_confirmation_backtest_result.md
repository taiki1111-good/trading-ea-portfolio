# 2026-05-02 OOS-1 Confirmation Backtest Result

## 目的
- Candidate Freeze v0.1 の OOS-1（`2024-07-01`〜`2024-10-01`）確認結果を記録する。
- 本記録は収益性確認ではなく、OOS-2へ進むかの暫定判断材料として扱う。

## 前提
- Candidate Freeze v0.1 は固定済み（entry/exit/HTF policy は変更しない）。
- 比較条件は OFF/permissive × fixed/trailing の4条件。
- 実 broker / OANDA API / 実注文送信は未実装。
- spread=0.2 pips fallback、手数料・スリッページ・スワップ未反映。

## OOS-1 月別結果
### 2024-07
- OFF + `fixed_sl_tp`: `trade_count=75`, `total_pnl=0.0060`
- OFF + `simple_trailing_after_1R`: `trade_count=75`, `total_pnl=0.1791`
- permissive + `fixed_sl_tp`: `trade_count=79`, `total_pnl=0.0020`
- permissive + `simple_trailing_after_1R`: `trade_count=79`, `total_pnl=0.1848`

### 2024-08
- OFF + `fixed_sl_tp`: `trade_count=57`, `total_pnl=-0.0240`
- OFF + `simple_trailing_after_1R`: `trade_count=57`, `total_pnl=0.2703`
- permissive + `fixed_sl_tp`: `trade_count=58`, `total_pnl=-0.0250`
- permissive + `simple_trailing_after_1R`: `trade_count=58`, `total_pnl=0.2766`

### 2024-09
- OFF + `fixed_sl_tp`: `trade_count=56`, `total_pnl=-0.0110`
- OFF + `simple_trailing_after_1R`: `trade_count=56`, `total_pnl=0.2578`
- permissive + `fixed_sl_tp`: `trade_count=57`, `total_pnl=-0.0090`
- permissive + `simple_trailing_after_1R`: `trade_count=57`, `total_pnl=0.2627`

## entry集合差分（trailing比較）
- 2024-07: `compare_only=7`, `base_only=3`, `shifted_5min=3`, `neutral_passed=8`, `total_pnl_diff=+0.0057`
- 2024-08: `compare_only=2`, `base_only=1`, `shifted_5min=1`, `neutral_passed=2`, `total_pnl_diff=+0.0063`
- 2024-09: `compare_only=2`, `base_only=1`, `shifted_5min=1`, `neutral_passed=3`, `total_pnl_diff=+0.0049`

## 暫定判断
- `simple_trailing_after_1R` は `fixed_sl_tp` を OOS-1全月で上回った。
- permissive + trailing は OFF + trailing を OOS-1全月で小幅に上回った。
- permissive の効果は小さいが一貫しており、主効果は trailing exit にある。
- Candidate Freeze v0.1 は OOS-1では棄却せず、OOS-2へ進める継続候補とする。
- ただし本採用判断ではなく、収益性確認済みを意味しない。

## 次アクション
- OOS-2（`2024-10-01`〜`2025-01-01`）で同一4条件を実施する。
- OOS-2結果を確認するまで、本採用判断は行わない。
- 結果を見て即時ルール変更しない。変更が必要な場合は Candidate Freeze v0.2 として分離管理する。
