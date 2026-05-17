# 2026-05-02 Counterfactual Exit Analysis

## 目的
MTF chart review（30件）で `sl_tp_too_fixed` が最多、`htf_against_entry` も多い結果を受け、BacktestRunner本体を変更せずに既存entry固定の counterfactual exit analysis を追加した。

## 追加内容
- `scripts/analyze_counterfactual_exits.py` を追加。
- 既存 `trade_logs` の entry（時刻/方向/価格）を固定し、exit条件のみ後追い比較する。
- 比較ルール:
  - baseline_fixed_exit
  - wider_sl_fixed_tp（sl x 1.5 / 2.0）
  - fixed_sl_wider_tp（tp x 1.5 / 2.0）
  - wider_sl_wider_tp（sl/tp x 1.5 / 2.0）
  - breakeven_after_1R
  - simple_trailing_after_1R
- `chart_review_template.csv` があれば `trade_index` で結合し、
  - `sl_tp_too_fixed`
  - `htf_against_entry`
  - `entry_ok`
  ごとの改善/悪化件数を追加集計する。

## 出力
- `counterfactual_exit_analysis.csv`
- `counterfactual_exit_analysis.md`

## 注意
- 既存entry固定の後追い分析であり、実際の BacktestRunner 実行結果ではない。
- 収益性評価ではなく、exit改善候補の構造検証。
- spread=0.2 pips fallback、手数料・スリッページ・スワップ未反映。
- `htf_against_entry` が一定数あるため、exit改善のみで採用判断しない。

## テスト
- `tests/unit/backtest/test_analyze_counterfactual_exits.py` を追加。
- `pytest -q`: 212 passed
