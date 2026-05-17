# 2026-05-09 pipeline dry-run representative run check

## 目的
- Phase 9 CSV replay pipeline dry-run の representative期間運用確認を行う。
- 既存 `run_csv_replay_pipeline_dry_run.py` と `summarize_csv_replay_dry_run.py` の実行結果整合を確認する。

## 使用データと期間
- input CSV: `tests/fixtures/price_m5_h1_h4_base.csv`
- warmup: `2024-01-01T00:00:00Z` 〜 `2024-01-01T01:00:00Z`
- replay: `2024-01-01T01:00:00Z` 〜 `2024-01-01T04:00:00Z`
- run_id: `rep_m5_h1h4_20260509`

## 実行コマンド
```powershell
$env:PYTHONPATH='.'
python scripts/run_csv_replay_pipeline_dry_run.py `
  --input-csv tests/fixtures/price_m5_h1_h4_base.csv `
  --output-dir tmp/phase9_pipeline_rep_20260509/near_live `
  --run-id rep_m5_h1h4_20260509 `
  --warmup-start 2024-01-01T00:00:00Z `
  --replay-start 2024-01-01T01:00:00Z `
  --replay-end 2024-01-01T04:00:00Z `
  --expected-timeframe-minutes 5

python scripts/summarize_csv_replay_dry_run.py `
  --input-dir tmp/phase9_pipeline_rep_20260509/near_live `
  --output-dir tmp/phase9_pipeline_rep_20260509/summary
```

## 主要結果
- `near_live_summary.csv`
  - `replay_bar_count=36`
  - `decision_log_count=36`
  - `pipeline_adapter_called_count=36`
  - `pipeline_adapter_error_count=0`
  - `pipeline_adapter_skipped_count=0`
  - `paper_order_candidate_count=34`
  - `real_order_sent_count=0`
  - `no_real_order_integrity_violation_count=0`
  - `warning_count=0`
  - `expected_weekend_gap_count=0`
- `dry_run_period_summary.csv`
  - `replay_bar_count=36`
  - `decision_log_count=36`
  - `dry_run_health_status=pass`
  - `status_reason=pipeline_health_ok`
  - `real_order_sent_count=0`
  - `no_real_order_integrity_violation_count=0`
  - `pipeline_adapter_error_count=0`

## 整合確認
- near_live と dry_run の `replay_bar_count` は一致。
- `decision_log_count == replay_bar_count` を確認。
- `real_order_sent_count=0` を確認。
- `no_real_order_integrity_violation_count=0` を確認。
- health 判定は `pass`（`pipeline_health_ok`）。
- weekend gap 単独で warn/fail になるケースは今回データでは未発生（`expected_weekend_gap_count=0`）。

## 備考
- 初回実行時に `PYTHONPATH` 未設定で `ModuleNotFoundError: src` が発生。再実行時に `PYTHONPATH='.'` を設定して解消。
- 生成 artifacts は `tmp/phase9_pipeline_rep_20260509/` 配下に出力し、Git管理には含めない。

## weekend跨ぎ representative run（追加確認）

### 使用データと期間
- input CSV: `tmp/phase9_pipeline_weekend_rep_20260509/weekend_replay_input.csv`（一時CSV）
- warmup: `2024-01-05T16:45:00Z` 〜 `2024-01-05T16:55:00Z`
- replay: `2024-01-05T16:55:00Z` 〜 `2024-01-07T17:20:00Z`
- run_id: `rep_weekend_gap_pipeline_20260509`

### 実行コマンド
```powershell
$env:PYTHONPATH='.'
python scripts/run_csv_replay_pipeline_dry_run.py `
  --input-csv tmp/phase9_pipeline_weekend_rep_20260509/weekend_replay_input.csv `
  --output-dir tmp/phase9_pipeline_weekend_rep_20260509/near_live `
  --run-id rep_weekend_gap_pipeline_20260509 `
  --warmup-start 2024-01-05T16:45:00Z `
  --replay-start 2024-01-05T16:55:00Z `
  --replay-end 2024-01-07T17:20:00Z `
  --expected-timeframe-minutes 5

python scripts/summarize_csv_replay_dry_run.py `
  --input-dir tmp/phase9_pipeline_weekend_rep_20260509/near_live `
  --output-dir tmp/phase9_pipeline_weekend_rep_20260509/summary
```

### 主要結果
- `near_live_summary.csv`
  - `replay_bar_count=4`
  - `decision_log_count=4`
  - `warning_count=1`
  - `data_gap_count=1`
  - `expected_weekend_gap_count=1`
  - `ordinary_missing_bar_gap_count=0`
  - `unknown_gap_count=0`
  - `duplicate_bar_count=0`
  - `out_of_order_count=0`
  - `pipeline_adapter_called_count=4`
  - `pipeline_adapter_error_count=0`
  - `real_order_sent_count=0`
  - `no_real_order_integrity_violation_count=0`
- `dry_run_period_summary.csv`
  - `replay_bar_count=4`
  - `decision_log_count=4`
  - `expected_weekend_gap_count=1`
  - `ordinary_missing_bar_gap_count=0`
  - `unknown_gap_count=0`
  - `dry_run_health_status=pass`
  - `status_reason=pipeline_health_ok`
  - `real_order_sent_count=0`
  - `no_real_order_integrity_violation_count=0`

### 判定
- `expected_weekend_gap_count > 0` かつ `ordinary_missing_bar_gap_count=0` / `unknown_gap_count=0` の条件で、`dry_run_health_status=pass`（`status_reason=pipeline_health_ok`）を確認。
- `near_live_validation_warnings.csv` の `data_gap` は `gap_class=expected_weekend_gap` / `gap_requires_investigation=False` のみ。

### 備考
- 既存fixturesに weekend跨ぎ専用CSVがなかったため、テストと同じギャップ時刻パターンで一時CSVを `tmp/` に作成して実行。
- 一時CSVと run artifact は `tmp/phase9_pipeline_weekend_rep_20260509/` 配下に出力し、Git管理対象に含めない。

## 追加整理（CURRENT_TASKS / summary markdown template）
- `ops/CURRENT_TASKS.md` の次タスクから、完了済み representative run 追加実行タスクを外した。
- 次タスクを `summary markdown template整理` / `pipeline_adapter_error内訳要否判断` / `Phase 9完了条件整理` / `OANDA/API後続` に整理した。
- `run_csv_replay_pipeline_dry_run.py` の `near_live_summary.md` を一次summary用途として明記し、gap系と no real order 系の主要項目を追加した。
- `summarize_csv_replay_dry_run.py` の `dry_run_period_summary.md` を二次summary用途として明記し、`pass/warn/fail` の意味と注意文（passは収益性/実運用品質を意味しない、expected_weekend_gap単独pass許容）を追加した。
