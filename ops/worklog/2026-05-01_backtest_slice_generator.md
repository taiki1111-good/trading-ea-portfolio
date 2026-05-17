# 2026-05-01 Backtest Slice Generator

## 目的
実データの全量CSV（`data/raw` / `data/private`）から、短期バックテスト確認用の小さいCSVを期間指定で生成するスクリプトを追加。

## 追加内容
- `scripts/make_backtest_slice.py`
  - 入力CSVの列名一覧表示
  - 先頭行プレビュー表示
  - 必須列（timestamp/open/high/low/close）の検証
  - `spread` 欠損時は `0.2 pips` fallback（構造検証・初期バックテスト専用）
  - `volume` 欠損時は `0` fallback
  - UTC時刻として正規化し、`timestamp,open,high,low,close,spread,volume` を出力

## 実行例
```bash
python scripts/make_backtest_slice.py \
  --input-csv data/private/USDJPY_M5_2024.csv \
  --output-csv data/private/backtest_slices/USDJPY_M5_2024-01-01_2024-01-07.csv \
  --start 2024-01-01 \
  --end 2024-01-07
```
