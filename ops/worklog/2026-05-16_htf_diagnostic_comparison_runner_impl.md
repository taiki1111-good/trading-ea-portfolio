# 2026-05-16 htf diagnostic comparison runner impl

## 実行目的
- HTF diagnostic comparison 設計に基づき、near_live単体で OFF / permissive / strict の3条件を再現可能に比較できる最小runnerを実装する。
- 本実装は diagnostic comparison 用であり、本体HTF filter採用・ON化ではない。

## 変更ファイル
- 追加:
  - `scripts/run_htf_diagnostic_comparison.py`
  - `tests/unit/backtest/test_run_htf_diagnostic_comparison.py`
- 既存ファイル変更なし:
  - `scripts/run_csv_replay_pipeline_dry_run.py`（既定挙動を維持）

## 実装内容
### 1) 3条件実行runner
- `run_htf_diagnostic_comparison.py` を追加。
- CLI入力:
  - `--input-csv`
  - `--output-dir`
  - `--run-id`
  - `--warmup-start`
  - `--replay-start`
  - `--replay-end`
  - `--expected-timeframe-minutes`
- 内部で `run_csv_replay_pipeline_dry_run()` を3条件で実行:
  - `htf_off`:
    - `htf_filter_enabled=False`
    - `htf_timeframe_policy="H1_only"`
    - `htf_neutral_policy="permissive"`
  - `htf_permissive`:
    - `htf_filter_enabled=True`
    - `htf_timeframe_policy="H1_only"`
    - `htf_neutral_policy="permissive"`
  - `htf_strict`:
    - `htf_filter_enabled=True`
    - `htf_timeframe_policy="H1_only"`
    - `htf_neutral_policy="strict"`

### 2) 条件別出力
- 各条件をサブディレクトリに分離:
  - `<output-dir>/htf_off/`
  - `<output-dir>/htf_permissive/`
  - `<output-dir>/htf_strict/`
- 各条件で `near_live_decision_logs.csv` / `near_live_summary.csv` など既存near_live出力を生成。

### 3) 比較summary出力
- 追加出力:
  - `htf_diagnostic_comparison_summary.csv`
  - `htf_diagnostic_comparison_summary.md`
- 最小項目:
  - `condition`
  - `replay_bar_count`
  - `decision_log_count`
  - `entry_signal_true_count`
  - `trade_ok_true_count`
  - `htf_filter_enabled`
  - `htf_timeframe_policy`
  - `htf_neutral_policy`
  - `htf_direction_aligned_count`
  - `htf_against_entry_count`（v0では `htf_direction_aligned=False` の保守的仮集計）
  - `neutral_passed_count`
  - `neutral_rejected_count`
  - `htf_filter_rejected_count`
  - `htf_filter_rejected_by_reason`（文字列reason counts）
  - `real_order_sent_count`
  - `no_real_order_integrity_violation_count`

## 非対応範囲（今回未実施）
- main path の既定HTF filter ON化
- 本体filter採用判断
- PnL / win_rate / average_pnl / total_pnl / exit_reason counts
- backtest decision_logs 側の同等列追加
- entry集合差分の高度解析
- Reason Catalog への HTF reason 統合
- OANDA/API、実注文
- 収益性確認済みの主張

## テスト結果
- `pytest -q tests/unit/backtest/test_run_htf_diagnostic_comparison.py` -> `2 passed`
- `pytest -q tests/unit/backtest/test_run_csv_replay_pipeline_dry_run.py` -> `7 passed`
- `git diff --check` -> 問題なし

## 非影響確認
- `run_csv_replay_pipeline_dry_run.py` の既存テストは通過し、既定挙動維持を確認。
- 本実装は比較runner追加であり、既存main path設定の `htf_filter_enabled=false` を変更しない。
- PnL / trade_count / entry / exit / `trade_ok` に影響する本体ロジック変更は行っていない。

## 次に進む判断
- 次フェーズは、runner結果を使った representative比較実行と、entry集合差分（`timestamp + signal_type` 基準）の追加設計要否判断へ進む。
