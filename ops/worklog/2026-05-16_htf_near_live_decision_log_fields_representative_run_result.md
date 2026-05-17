# 2026-05-16 htf near_live decision log fields representative run result

## 実行目的
- `near_live_decision_logs.csv` へ追加した HTF行レベル8列が、unit test だけでなく representative run 実出力でも確認できることを記録する。
- 本作業は運用確認であり、HTF filter本体実装・ON化・comparison runner実装は行わない。

## 使用入力
- `tests/fixtures/price_m5_h1_h4_base.csv`
- 期間:
  - `warmup_start=2024-01-01T00:00:00Z`
  - `replay_start=2024-01-01T01:00:00Z`
  - `replay_end=2024-01-01T04:00:00Z`

## 実行コマンド
```powershell
$env:PYTHONPATH='.'
python scripts/run_csv_replay_pipeline_dry_run.py `
  --input-csv tests/fixtures/price_m5_h1_h4_base.csv `
  --output-dir tmp/phase9_pipeline_rep_htf_fields_20260516 `
  --run-id rep_m5_h1h4_htf_fields_20260516 `
  --warmup-start 2024-01-01T00:00:00Z `
  --replay-start 2024-01-01T01:00:00Z `
  --replay-end 2024-01-01T04:00:00Z `
  --expected-timeframe-minutes 5
```

## 出力先
- `tmp/phase9_pipeline_rep_htf_fields_20260516/`

## header確認結果
- 対象ファイル:
  - `tmp/phase9_pipeline_rep_htf_fields_20260516/near_live_decision_logs.csv`
- 追加対象8列はすべて存在:
  - `htf_filter_enabled`
  - `htf_timeframe_policy`
  - `htf_neutral_policy`
  - `htf_trend_dir`
  - `htf_bias`
  - `htf_direction_aligned`
  - `htf_filter_reason`
  - `htf_context_reason`

## 8列の簡易確認結果
- `ROW_COUNT=36`
- `NON_EMPTY_HTF_FILTER_REASON=36`
- `NON_EMPTY_HTF_CONTEXT_REASON=36`
- `FALSE_OR_BLANK_HTF_FILTER_ENABLED=36`
  - 本runでは HTF filter OFF 前提のため想定どおり。
- 欠落列なし（`MISSING=[]`）。

## 整合性確認（非影響観点）
- `near_live_summary.csv` で
  - `replay_bar_count=36`
  - `decision_log_count=36`
  - 整合維持を確認。
- `real_order_sent_count=0`
- `no_real_order_integrity_violation_count=0`
- 既存 no-real-order 安全性指標は維持。

## 非影響確認
- 追加は decision log 列露出のみ。
- HTF filter本体実装なし、ON化なし。
- strict/permissive comparison runner 実装なし。
- summary候補5項目実装なし。
- backtest decision_logs 側の同時対応なし。
- PnL / trade_count / entry / exit / `trade_ok` の挙動変更なし。

## 生成物のGit管理
- 生成物は `tmp/` 配下に出力し、Git管理外であることを確認。

## 次に進む判断
- HTF near_live 8列の実出力確認は完了。
- 次フェーズは HTF diagnostic comparison 設計（strict/permissive 比較条件・評価フロー固定）へ進む。
