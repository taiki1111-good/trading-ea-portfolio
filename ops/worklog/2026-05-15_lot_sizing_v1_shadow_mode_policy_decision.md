# 2026-05-15 lot sizing v1 shadow mode policy decision

## 目的
- `Lot Sizing v1` shadow mode / comparison-only の設計方針を固定する。
- 今回は docs/ops 判断固定のみで、コード変更・テスト変更は行わない。

## 最終判断
- shadow mode / comparison-only を採用する。
- 本線lotは `fixed_lot` のまま維持する。
- risk-based lot は diagnostic value として算出・比較する候補に留める。

## shadow mode の目的
1. `fixed_lot` と risk-based lot の差分観測
2. invalid / clamp / below_min 頻度の把握
3. 将来の本線接続判断材料の作成
4. 収益性評価ではない

## 実装候補の判断
- A. `PipelineAdapter` 内 shadow calculation:
  - 現時点では採用しない（後続候補）。
- B. backtest後 analysis script 拡張:
  - 採用候補（次点）。
- C. 専用 offline comparison script:
  - 最優先候補（推奨）。

## C/B 優先の理由
- 既存本線挙動への影響を最小化できる。
- `PipelineAdapter` に診断責務を追加しすぎない。
- `account_balance` / `pip_value_per_lot` / `risk_per_trade` 供給経路が未固定でも進めやすい。
- decision log 列追加が本線仕様に見えるリスクを抑えられる。

## 診断値候補
- `fixed_lot`
- `risk_based_raw_lot`
- `risk_based_rounded_lot`
- `risk_based_effective_lot`
- `risk_based_lot_sizing_reason`
- `risk_based_clamped_flag`
- `lot_size_diff`
- `lot_size_ratio`
- `risk_lot_valid_flag`

## 非影響範囲（固定）
- actual lot は `fixed_lot` のまま
- PnLに反映しない
- trade_countを変えない
- entry/exit判断を変えない
- `RiskAssembler` の `trade_ok` 判定を変えない
- Execution / order path に渡さない

## 継続して非対応
- broker制約厳密化
- OANDA/API接続
- 実注文
- 収益性評価

## 次に渡す実装方針
- shadow mode v0 は C（専用offline comparison script）または B（analysis script拡張）で進める。
- A（PipelineAdapter 内 shadow 計算）は shadow mode v1 以降の候補として保持する。
