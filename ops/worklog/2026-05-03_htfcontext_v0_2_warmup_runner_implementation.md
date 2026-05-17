# 2026-05-03 HTFContext v0.2 warmup runner implementation

## 実装概要
`run_backtest_exit_experiment.py` に `--warmup-start` を追加し、evaluation period と indicator 計算履歴期間を分離した。

## 実装内容
- `--warmup-start` をCLIに追加。
- `warmup_start` 未指定時は従来挙動（indicator入力=評価期間）を維持。
- `warmup_start` 指定時:
  - indicator入力: `warmup_start <= timestamp < end`
  - 評価対象: `start <= timestamp < end`
- providerへ渡す `window` は indicator入力履歴を含むため、評価開始時点でstart前履歴を参照可能。
- warmup区間（start前）では provider/entry/exit 評価を行わず、取引は発生しない。

## 追加したsummary/metadata項目
- `warmup_start`
- `warmup_bar_count`
- `evaluation_start`
- `evaluation_end`
- `evaluation_bar_count`
- `indicator_input_start`
- `indicator_input_end`

## 後方互換性
- `warmup_start` 未指定時は、bar選択・取引対象・summary集計は従来と同一。
- HTF v2 OFF/ON（diagnostic_only）どちらでも既存挙動を壊さない前提でテスト追加。

## テスト
- parse_argsで `--warmup-start` を受理すること。
- 未指定時のbar_count互換。
- 指定時の summary `bar_count` が evaluation のみであること。
- 指定時に provider window が warmup履歴を含むこと。
- warmup区間で entry/trade が発生しないこと。
- summary/metadata に warmup項目が出力されること。

## 未解決事項
1. warmupあり代表月runで unknown 比率改善が再現するかの実測。
2. decision_logs の運用上、評価境界列を追加するかどうか。
3. `warmup_start > start` を許容しない契約でよいかの最終確認。

## 注意
- 本作業は runner 境界実装のみ。
- HTF v2 filter有効化、`aligned_only` / `pullback_permissive` 統合、売買ロジック変更は実施していない。
- これは収益性確認ではない。
