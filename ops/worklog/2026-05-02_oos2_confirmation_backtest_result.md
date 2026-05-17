# 2026-05-02 OOS-2 Confirmation Backtest Result

## 目的
- Candidate Freeze v0.1 の OOS-2（`2024-10-01`〜`2025-01-01`）確認結果を記録する。
- OOS-1/OOS-2 を通じて棄却可否を整理し、次段階へ進めるかを構造検証として判断する。

## 前提
- Candidate Freeze v0.1 は固定済み（entry/exit/HTF policy は変更しない）。
- 比較条件は OFF/permissive × fixed/trailing の4条件。
- 結果を見て即時ルール変更しない。
- 実 broker / OANDA API / 実注文送信は未実装。
- spread=0.2 pips fallback、手数料・スリッページ・スワップ未反映。

## OOS-2 月別結果
### 2024-10
- OFF + `fixed_sl_tp`: `trade_count=67`, `total_pnl=-0.0130`
- OFF + `simple_trailing_after_1R`: `trade_count=67`, `total_pnl=0.1472`
- permissive + `fixed_sl_tp`: `trade_count=71`, `total_pnl=-0.0170`
- permissive + `simple_trailing_after_1R`: `trade_count=71`, `total_pnl=0.1486`

### 2024-11
- OFF + `fixed_sl_tp`: `trade_count=64`, `total_pnl=-0.0040`
- OFF + `simple_trailing_after_1R`: `trade_count=64`, `total_pnl=0.2901`
- permissive + `fixed_sl_tp`: `trade_count=66`, `total_pnl=-0.0060`
- permissive + `simple_trailing_after_1R`: `trade_count=66`, `total_pnl=0.2918`

### 2024-12
- OFF + `fixed_sl_tp`: `trade_count=80`, `total_pnl=-0.0080`
- OFF + `simple_trailing_after_1R`: `trade_count=80`, `total_pnl=0.2018`
- permissive + `fixed_sl_tp`: `trade_count=84`, `total_pnl=-0.0030`
- permissive + `simple_trailing_after_1R`: `trade_count=84`, `total_pnl=0.2079`

## validation（全12run）
- `trade_schema_valid=true`
- `decision_schema_valid=true`
- `consistency_valid=true`

## entry集合差分（trailing比較）
- 2024-10: `compare_only=5`, `base_only=1`, `shifted_5min=1`, `neutral_passed=7`, `total_pnl_diff=+0.0014`
- 2024-11: `compare_only=5`, `base_only=3`, `shifted_5min=2`, `neutral_passed=6`, `total_pnl_diff=+0.0017`
- 2024-12: `compare_only=6`, `base_only=2`, `shifted_5min=2`, `neutral_passed=9`, `total_pnl_diff=+0.0061`

## 暫定判断
- `simple_trailing_after_1R` は `fixed_sl_tp` を OOS-2全月で上回った。
- permissive + trailing は OFF + trailing を OOS-2全月で小幅に上回った。
- OOS-1/OOS-2を通じて、主効果は trailing exit、permissive は小幅補助効果と整理する。
- Candidate Freeze v0.1 は OOS-1/OOS-2 では棄却されず、次段階へ進める structural pass 候補とする。
- ただし本採用判断ではなく、収益性確認済み・実運用可能性確認済みを意味しない。

## 次段階（現実耐性確認）
- 新しいentry/exitを追加する前に、現 Candidate Freeze v0.1 の現実耐性を確認する。
- 優先確認:
  1. spread / commission / slippage / swap の扱い
  2. `simple_trailing_after_1R` の約定仮定が楽観的すぎないか
  3. M1 replay / conservative / next_bar_activation との整合
  4. 12月年末データ終端の注記
  5. 評価単位を raw pnl から pips / R / drawdown 系に広げるか

## 方針維持
- `simple_trailing_after_1R` と permissive は本採用扱いしない。
- 追加ルール変更が必要な場合は Candidate Freeze v0.2 として分離管理する。
