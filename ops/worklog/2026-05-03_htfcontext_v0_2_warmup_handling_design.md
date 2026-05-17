# 2026-05-03 HTFContext v0.2 warmup handling design

## 目的
HTF v2 diagnostic_only 代表runの unknown 高比率を受け、warmup handling と evaluation period separation の設計方針を docs/ops に明文化する。
本記録は設計整理のみであり、backtest再実行や実装変更は行わない。

## 観測結果（OOS-2 2024-11 代表run）
- 全decision row（`n=5861`）
  - `h4_bias unknown = 2456 / 5861`（約41.9%）
  - `h1_context unknown = 3117 / 5861`（約53.2%）
  - `htf_v2_data_valid_flag False = 3117 / 5861`（約53.2%）
- entry候補（`n=64`）
  - `h4_bias unknown = 27 / 64`（約42.2%）
  - `h1_context unknown = 36 / 64`（約56.3%）

## warmup不足仮説
- `run_backtest_exit_experiment.py` は `start/end` スライス後の bars のみを `PipelineAdapter` に渡すため、`start` 以前の履歴が HTF 計算 warmup に使われない可能性がある。
- H4 MA50 は最低50本H4足（約200時間）、H1 MA20は最低20本H1足が必要であり、評価期間開始直後は `unknown` が増えやすい。

## 設計方針（evaluation period / warmup period separation）
- 例:
  - `indicator_input_period: 2024-10-01〜2024-12-01`
  - `evaluation_period: 2024-11-01〜2024-12-01`
- `trade_logs` / `backtest_summary` 対象は `evaluation_period` のみ。
- HTF計算（H1/H4/MA/slope）は `indicator_input_period` 全体を使用してよい。

## 原則
- entry評価対象は `start/end` 内に限定する。
- H1/H4/MA/slope計算には `start` 以前の履歴を使ってよい。
- `m5_decision_time` より未来の情報は使わない。
- `start` 以前の取引は発生させない。
- `start` 以前の履歴は indicator 計算専用とする。

## future leak 防止
- warmupは過去履歴利用なので許可。
- evaluation start以降の未来足は使わない。
- 各M5 decision時点で参照可能なHTF barは `htf_bar_close_time <= m5_decision_time` のみ。

## 実装候補と推奨
- 候補A: runnerに `--warmup-start` を追加し、`warmup_start〜end` を HTF計算入力へ渡す。
- 候補B: `PipelineAdapter` に `history_bars` を渡す。
- 推奨: runner側で `warmup_start` を扱い、評価対象barとindicator履歴を分離する。
- 互換性: `warmup_start` 未指定時は従来挙動を維持する。

## 未解決事項
1. `--warmup-start` のCLI契約（未指定時挙動、入力フォーマット、metadata項目）。
2. decision_logsを評価期間のみに限定する境界仕様。
3. warmupあり/なし比較時の最小比較指標セット（unknown率、trade_count整合、entry集合差分）。
4. runner側実装と `history_bars` 実装の最終採用判断。

## 注意
- `aligned_only` / `pullback_permissive` には進まない。
- これは収益性確認ではない。
