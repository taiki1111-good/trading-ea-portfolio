# 2026-05-17 lot sizing shadow edge case tidy

## 目的
- `compare_lot_sizing_shadow.py` の採用前軽微修正として、未使用helper削除と `fixed_lot <= 0` 時の比較指標空欄仕様をテストで固定する。

## 実施内容
- `scripts/compare_lot_sizing_shadow.py` から未使用helper `_to_text()` を削除した。
- `tests/unit/backtest/test_compare_lot_sizing_shadow.py` に `fixed_lot=0.0` ケースを追加した。
  - risk-based lot は valid（`risk_lot_valid_flag=True`）であること
  - `lot_size_diff` / `lot_size_ratio` は空欄であること
  - summary の `average/max/min` diff/ratio が空欄であること

## スコープ
- shadow comparison script の軽微修正のみ。
- `PipelineAdapter` / `BacktestRunner` / `RiskAssembler` / `PositionSizer` の挙動は変更していない。
- `PnL` / `trade_count` / `trade_ok` / `entry` / `exit` への影響はない。
- 実 broker / OANDA API / 実注文送信には触れていない。
