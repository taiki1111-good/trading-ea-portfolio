# 2026-05-03 Session/Time Filter v0.2 diagnostic_only implementation

## 実装内容
- `PipelineAdapterConfig` に `session_v2` 設定を追加:
  - `session_v2_enabled`
  - `session_v2_policy`
  - `session_v2_timezone`
  - `session_v2_use_day_of_week`
  - `session_v2_use_hour_bucket`
  - `session_v2_use_dst_adjustment`
- `PipelineAdapter` に `session_v2 diagnostic_only` 計算を追加:
  - `hour_utc` / `day_of_week` を UTC 基準で出力
  - `session_label` を UTC固定近似境界で分類
  - `is_low_liquidity_hour`（22:00-00:00 UTC）時に `session_risk_flag=True`
  - `session_reason` に `diagnostic_only:no_entry_filter` を付与
- `run_backtest_exit_experiment.py` に session v2 CLI と metadata/summary 出力を追加。

## entryを止めていないこと
- `session_v2_enabled=True` + `diagnostic_only` でも entry制御は実施していない。
- `entry_signal` / `trade_ok` の判定フローを session列で変更していない。

## UTC固定近似 / DST未対応方針
- session分類は UTC固定近似ラベルで実装。
- DST厳密補正は実装していない。
- `session_v2_use_dst_adjustment` は将来拡張用フラグとして保持。

## テスト結果（要点）
- session無効時の既存挙動維持。
- `diagnostic_only` で entry非変更。
- `hour_utc` / `day_of_week` 出力確認。
- tokyo/london/new_york/overlap/low_liquidity 分類確認。
- `low_liquidity` 時の `session_risk_flag=True` 確認。
- `session_reason` に `diagnostic_only:no_entry_filter` を含むこと確認。
- runner CLI/metadata/summary への session設定出力確認。

## 未解決事項
- session境界の最終定義（UTC固定近似から本採用時の境界へどう移行するか）。
- DST厳密対応の導入タイミング。
- JST表示列の要否。
- low liquidity定義の厳密化。
