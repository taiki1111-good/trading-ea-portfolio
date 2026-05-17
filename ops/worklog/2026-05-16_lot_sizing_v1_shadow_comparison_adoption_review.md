# 2026-05-16 lot sizing v1 shadow comparison v0 adoption review

## 目的
- `scripts/compare_lot_sizing_shadow.py` を採用扱いにしてよいかを、契約・非影響・テスト・ops整合の観点で確認する。

## 対象
- `scripts/compare_lot_sizing_shadow.py`
- `tests/unit/backtest/test_compare_lot_sizing_shadow.py`
- `src/risk_filter/lot_sizing_calculator.py`
- `tests/unit/risk_filter/test_lot_sizing_calculator.py`
- `ops/CURRENT_TASKS.md`
- `ops/worklog/2026-05-15_lot_sizing_v1_shadow_comparison_impl.md`
- 関連 policy/decision worklog

## レビュー結果
### 1) 入力契約
- `stop_loss_distance_pips` は「CSV列優先 -> CLI fallback -> 両方欠損でエラー」を実装・テストで確認した。
- `account_balance` / `risk_per_trade` / `pip_value_per_lot` / `lot_step` / `min_lot` / `max_lot` は `LotSizingCalculator` 契約に従って `LotSizingV1Config` へ明示入力される。
- calculator 側 invalid 条件（bool/NaN/inf含む）・floor rounding・max clamp・below_min invalid は unit test で固定済み。

### 2) 出力契約
- `lot_sizing_shadow_rows.csv` に、fixed/risk-based lot、diff/ratio、valid flag、reason、clamp flag が出力され、行単位追跡が可能。
- `lot_sizing_shadow_summary.csv` / `.md` に、row数、valid/invalid、clamp、below_min、invalid_input、diff/ratio統計、reason counts が出力される。
- 将来の本線接続判断材料として、v0の comparison-only 診断用途を満たす。

### 3) 非影響保証
- `PipelineAdapter` / `BacktestRunner` / `PositionSizer` / Execution path への変更はない。
- `PnL` / `trade_count` / `entry` / `exit` / `trade_ok` へ影響する経路変更はない。
- docs/ops の shadow comparison-only 方針（No-Go/Hold 本線接続）と整合する。

### 4) テスト
- `pytest -q tests/unit/backtest/test_compare_lot_sizing_shadow.py` -> `9 passed`
- `pytest -q tests/unit/risk_filter/test_lot_sizing_calculator.py` -> `13 passed`
- `git diff --check` -> 問題なし
- v0採用判断に必要な契約テストは充足しているため、今回は追加テストなし。

## 判断
- 判定: **Go（採用）**
- 採用範囲:
  - `Lot Sizing v1 shadow comparison v0`（offline comparison script）
  - comparison-only / diagnostic-only 用途
- 非採用（継続保留）:
  - `PipelineAdapter` / `PositionSizer` / `BacktestRunner` 本線接続
  - PnL/trade_count/entry/exit/trade_ok へ影響する変更

## 出力形式に関する次判断
- 行単位派生列CSV（`lot_sizing_shadow_rows.csv`）は当面維持する（接続判断材料として有用）。
- canonical出力へ段階移行する場合も、既存出力の削除・改名は行わず「追加形式」で進める。
- legacy detail は即廃止せず deprecated 扱いで段階移行する。

## 残課題
- run metadata としての `account_balance` / `risk_per_trade` / `pip_value_per_lot` 供給経路を後続で固定する。
- canonical summary形式への段階移行案を、既存互換を壊さずに整理する。
