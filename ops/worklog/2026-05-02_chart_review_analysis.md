# 2026-05-02 Chart Review Analysis

## 目的
MTFチャート30件の目視レビュー結果を集計し、次に優先すべき改善対象を判断する材料を作成する。

## 実施内容
- `scripts/analyze_chart_review.py` を追加。
- 入力:
  - `--review-csv`
  - `--output-dir`
- 出力:
  - `chart_review_analysis.csv`
  - `chart_review_analysis.md`

## 集計項目
- review_count
- visual_entry_ok counts
- visual_exit_ok counts
- issue_category counts
- priority counts
- signal_type x issue_category
- exit_reason x issue_category
- pnl sign x issue_category
- temporal_lag_bars x issue_category
- high priority issue count
- entry問題件数
- exit問題件数
- HTF逆行件数
- range/noise件数

## 出力サマリ
- review_count: 30
- issue_category: sl_tp_too_fixed が最多（10）
- priority: high が 18
- 暫定改善優先度: exit strategy experiments を優先候補

## 注意
- これは目視レビュー集計であり、統計的な収益性評価ではない。
- H1/H4は現行BT判断には未使用（visual reference only）。
- 現行BTはM5-derived pipeline windowで動作。

## 制約確認
- 売買ロジック変更なし
- BacktestRunner / PipelineAdapter / ExitRuleEngine 変更なし
- 実 broker / OANDA API / 実注文送信の実装なし
