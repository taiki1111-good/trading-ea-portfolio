# 2026-05-03 HTFContext v0.2 runner wiring

## 失敗原因
- `run_backtest_exit_experiment.py` は HTF v1 引数のみ対応で、`--htf-v2-enabled` などの HTF v2 引数が未定義だった。
- そのため `unrecognized arguments` で代表月runが失敗していた。

## 修正内容
- `run_backtest_exit_experiment.py` に以下を追加:
  - `--htf-v2-enabled`
  - `--htf-v2-policy`（`diagnostic_only`）
  - `--htf-v2-h4-ma-fast`
  - `--htf-v2-h4-ma-slow`
  - `--htf-v2-h1-ma-fast`
  - `--htf-v2-slope-window`
- 上記を `PipelineAdapterConfig` へ配線。
- `backtest_summary.csv` / `run_metadata.json` に HTF v2 設定値を出力。

## 互換性
- 既定は `htf_v2_enabled=False` を維持。
- 既存 HTF v1 引数（`--htf-filter-enabled` 等）との併用互換を維持。
- `diagnostic_only` は entry を止めず、ラベル出力用途のみ。

## テスト
- parse_args で HTF v2 引数が受理されることを確認。
- HTF v2 既定値が期待どおりであることを確認。
- main 経由で `PipelineAdapterConfig` への引数受け渡しを確認。
- summary / metadata に HTF v2 設定が出力されることを確認。

## 未解決事項
- `transition` context は引き続き deferred。
- 代表月runでのラベル分布確認はユーザー実行タスク。
