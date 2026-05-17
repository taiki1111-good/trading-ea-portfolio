# 2026-05-03 HTFContext v0.2 diagnostic trade analysis script

## 目的
HTF v2 `diagnostic_only` 代表runの decision_logs と trade_logs を突合し、HTF分類別に損益分解する後処理スクリプトを追加した。

## 実装内容
- `scripts/analyze_htf_v2_diagnostic_trades.py` を追加。
- CLI:
  - `--decision-logs`
  - `--trade-logs`
  - `--output-dir`
- `trade_logs.entry_time` と `decision_logs.timestamp` を UTC正規化（`pandas.to_datetime(..., utc=True)`）して突合。
- trade単位出力:
  - `htf_v2_trade_analysis.csv`
- group集計出力:
  - `htf_v2_group_summary.csv`
  - `htf_v2_group_summary.md`

## 集計グループ
- `h4_bias`
- `h1_context`
- `htf_v2_aligned_only_allowed`
- `htf_v2_pullback_permissive_allowed`
- `htf_v2_context_uncertain_flag`
- `htf_v2_hard_conflict_flag`
- `htf_v2_data_valid_flag`
- `htf_v2_candidate_direction`

## 仕様メモ
- unmatched trade（entry_timeでdecision row突合不能）は件数を保持し、Markdown summaryに warning 表示。
- 必須列不足時は `ValueError` を返し、不足列名を明示。
- 本スクリプトは既存ログ後処理のみであり、backtest再実行や売買ロジック変更を行わない。

## テスト
- entry_time/timestamp突合。
- timezone表記差（`Z` と `+00:00`）吸収。
- HTF列付与確認。
- group summary 指標（trade_count/total_pnl/average_pnl/win_rate）確認。
- unmatched warning確認。
- 必須列不足エラー確認。
- Markdown summary出力確認。

## 未解決事項
1. 同一timestampがdecision_logsに複数ある場合の優先規則は現状「最後の行」を採用。
2. 実runの分析値レビュー（分類別損益解釈）はこの後の実行タスク。

## 注意
- これは既存ログの後処理診断であり、収益性確認ではない。
- aligned_only / pullback_permissive の実filter化判断は保留。
