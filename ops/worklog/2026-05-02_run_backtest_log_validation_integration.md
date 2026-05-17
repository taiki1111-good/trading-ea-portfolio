# 2026-05-02 Run Backtest Log Validation Integration

## 実施内容
- `scripts/run_backtest_on_m5_slice.py` にログ品質保証を統合。
  - `CsvSchemaValidator.validate_records('trade_logs', trade_logs)`
  - `CsvSchemaValidator.validate_records('decision_logs', decision_logs)`
  - `CsvSchemaValidator.validate_backtest_log_consistency(trade_logs, decision_logs)`
- 出力追加:
  - 標準出力へ `trade_logs_schema_valid`, `decision_logs_schema_valid`, `log_consistency_valid`, reason/warnings を表示
  - `backtest_summary.csv/.md` に validation 要約を追記
  - `log_validation_summary.csv/.md` を `output_dir` に新規出力
- 失敗時制御を追加:
  - デフォルトは invalid で `RuntimeError` 終了
  - `--allow-invalid-logs` 指定時は警告扱いで継続

## 検証
- 対象run:
  - `usdjpy_m5_2024_0102_0201_lb5_dedup1_no_fallback_validation_integrated`
- 結果:
  - trade_count=57
  - decision_log_count=6270
  - trade_logs_schema_valid=True
  - decision_logs_schema_valid=True
  - log_consistency_valid=True

## 補足
- 売買ロジック（BacktestRunner/PipelineAdapter のエントリー判定）は未変更。
- 本対応は収益性評価ではなく、ログ整合性の品質保証追加。
