# 2026-05-02 Decision Log Semantics Cleanup

## 実施内容
- `PipelineAdapter` の decision trace 生成を見直し、`temporal_candidate=true` のときのみ temporal metadata を埋めるように修正。
- `fail_stage` を `structure / direction_alignment / pattern_gate / signal / risk_filter / dedup / none` へ整理。
- `entry_signal=false` または `signal_type=none` を `signal` ステージ失敗として分類するよう調整。
- `scripts/analyze_decision_logs.py` に temporal 一貫性検査と fail_stage 集計を追加。
- unit/integration テストを更新し、temporal metadata 条件・dedup fail_stage・trade_count整合を検証。

## 影響方針
- 売買ロジック（entry/exit判定アルゴリズム）自体は変更しない。
- ログ意味づけと診断可読性の改善のみを対象とした。

## 実行コマンド
- `python scripts/run_backtest_on_m5_slice.py ...`（2期間）
- `python scripts/analyze_decision_logs.py ...`（各run）
- `$env:PYTHONPATH='.'; pytest -q`
