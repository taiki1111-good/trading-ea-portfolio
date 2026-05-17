# 2026-05-17 lot sizing shadow comparison adoption

## 目的
- `compare_lot_sizing_shadow.py` を、fixed baseline と risk-based lot の差分確認用 diagnostic / shadow comparison tool として採用する。
- これは lot sizing本体接続ではない。

## 到達点
- fixed baseline (`fixed_lot`) と risk-based lot の差分確認用scriptとして整備済み。
- `fixed_lot <= 0` 時は diff/ratio を算出しない（空欄）仕様をテストで固定済み。
- summary 側の average/max/min diff/ratio も空欄仕様をテストで固定済み。

## 採用範囲
- diagnostic / shadow comparison tool として採用する。
- 本体 lot sizing 接続は行わない。
- `PositionSizer` placeholder は維持する。
- fixed baseline 同値維持を壊さない。

## 非スコープ
- 収益性評価ではない。
- PnL改善確認ではない。
- 実運用ロット管理ではない。
- 実注文対応ではない。

## 次タスク候補
- portfolio docs / README / presentation notes に、Risk/Stop v0 と lot sizing shadow comparison の位置づけを反映する。
- または representative run で shadow comparison output を1回記録するか判断する。
