# 2026-05-03 Validation Summary Script v0.2 design

## 入力候補
- `run_metadata.json`
- `backtest_summary.csv`
- `trade_logs.csv`
- `htf_v2_group_summary.csv`
- `sr_v2_group_summary.csv`
- `session_v2_group_summary.csv`
- `risk_stop_v2_summary.csv`
- `cost_adjusted_summary.csv`
- `validation_targets.csv`（手動定義）

## 出力候補
- `validation_v0_2_summary.csv`
- `validation_v0_2_decision_log.csv`
- `validation_v0_2_layer_status.csv`
- `validation_v0_2_summary.md`

## validation_targets設計
- `validation_target_id`
- `period_start`
- `period_end`
- `period_type`
- `run_id`
- `run_dir`
- `module_name`
- `candidate_name`
- `policy`
- `notes`

## decision rule初期案
- `trade_count < 20`: `insufficient_sample` 候補
- `representative_month` 単独: `candidate_for_implementation` 禁止
- `net_counterfactual_effect < 0`: `pause_no_go` 寄り
- `missed_profit > avoided_loss`: 副作用として `decision_reason` に記録
- `cost_adjusted_flag=False`: `needs_cost_adjusted_check` 候補
- HTF/SR/Sessionでfilter根拠なし: `keep_as_explanation_layer`
- 複数月確認前: `continue_diagnostic`

## 未解決事項
- `validation_targets.csv` の配置場所
- 既存runの命名揺れ対応
- diagnostic summary間のschema差吸収
- `max_drawdown` 未計算時の扱い
- cost_adjusted標準入力化
- Markdown reportの粒度

## 注意
- 今回は実装前設計のみ。
- backtest再実行・Validation実装・Runner変更・売買ロジック変更・閾値変更は未実施。
