# 2026-05-03 Validation v0.2 I/O Contract & Decision Policy

## 目的
- Phase 8 Validation v0.2 の実装前段階として、入力/出力契約と意思決定ポリシーを固定する。
- 代表月単独の結果で本採用判断しないための統一ルールを定義する。

## 入力候補
- `backtest_summary.csv`
- `trade_logs.csv`
- `decision_logs.csv`
- HTF/SR/Session diagnostic summaries
- Risk/Stop counterfactual summaries
- cost-adjusted summaries
- `run_metadata.json`
- manually defined validation run list

## 出力候補
- `validation_v0_2_summary.csv`
- `validation_v0_2_decision_log.csv`
- `validation_v0_2_layer_status.csv`
- `validation_v0_2_summary.md`

## decision_status候補
- `continue_diagnostic`
- `promote_to_multi_month_check`
- `keep_as_explanation_layer`
- `pause_no_go`
- `candidate_for_implementation`
- `future_research`
- `insufficient_sample`
- `needs_cost_adjusted_check`

## sample size flag方針（初期仮説）
- 本採用値としては固定しない。
- `trade_count < 20`: `low` 候補
- `20-50`: `medium` 候補
- `>=50`: `normal` 候補
- 少数サンプルは原則 `insufficient_sample` 寄りで扱う。

## module別decision方針
- HTF v2: 説明ラベル継続、複数月で分布と損益確認。
- SR v2 rolling high/low: breakout近接ラベル継続、reaction SRと分離。
- Session v2: UTC固定近似ラベル継続、DST未補正のまま本採用filter化しない。
- Risk/Stop v2: 代表月では統合根拠なし、悪化月・連敗月で再確認。
- Halt/Risk: Phase 2でNo-Go、F候補は将来の複数月確認候補。
- Exit policy: `simple/conservative/next_bar` を現実耐性軸で区別。

## 未解決事項
- validation対象月セット
- adverse_month の選び方
- period_type 最終定義
- max_drawdown正式導入
- cost-adjusted summary標準入力化
- report自動生成タイミング
- near-live dry-run結果との接続

## 注意
- backtest再実行・Validation実装・Runner変更・売買ロジック変更・閾値変更は未実施。
