# 2026-05-02 Trade Logs Schema Warning Cleanup

## 実施内容
- `CsvSchemaValidator` の trade_logs 列定義を backtest 実出力に合わせて既知列化。
- 既知列は extra warning 対象外とし、未知列のみ warning を出すよう変更。
- trade_logs 追加チェック:
  - `signal_type` 許容値
  - `structure_source` 許容値
  - `fallback_used` の bool相当
- 既存1か月runの trade/decision logs で再検証し、schema_warnings が空であることを確認。

## 検証結果（既存1か月run）
- trade_logs_schema_valid=True
- decision_logs_schema_valid=True
- log_consistency_valid=True
- schema_warnings=[]
- consistency_warnings=[]

## 注意
- 売買ロジック（BacktestRunner/PipelineAdapter の entry 判定）は未変更。
- 本対応は収益性評価ではなく、ログ契約・schema validation 整備。
