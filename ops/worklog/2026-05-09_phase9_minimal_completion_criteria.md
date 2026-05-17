# 2026-05-09 Phase 9 minimal completion criteria

## 目的
- Phase 9 CSV replay pipeline dry-run minimal implementation (Option A) を一区切りにするため、完了条件・非対応範囲・次候補を docs / ops に固定する。

## Phase 9で確認済みのこと
- `run_csv_replay_pipeline_dry_run.py` で pipeline dry-run output を生成できる。
- `summarize_csv_replay_dry_run.py` で pipeline mode health（pass/warn/fail）を出力できる。
- weekday representative run で `dry_run_health_status=pass` を確認済み。
- weekend跨ぎ representative run で `expected_weekend_gap_count=1` かつ `ordinary_missing_bar_gap_count=0` / `unknown_gap_count=0` の条件でも `dry_run_health_status=pass` を確認済み。
- `real_order_sent_count=0` を確認済み。
- `no_real_order_integrity_violation_count=0` を確認済み。
- `near_live_summary.md` / `dry_run_period_summary.md` の最小テンプレート整理済み。

## 完了条件（minimal completion）
1. representative 期間で pipeline dry-run 実行可能。
2. `near_live_*` outputs を生成可能。
3. summarizer により `dry_run_period_summary.*` を生成可能。
4. `decision_log_count == replay_bar_count` を確認可能。
5. `real_order_sent_count == 0` を確認可能。
6. `no_real_order_integrity_violation_count == 0` を確認可能。
7. weekday representative run で health pass を確認済み。
8. weekend expected gap 単独時に過剰 warn/fail にならないことを確認済み。
9. `pass` は収益性や実運用品質を意味しない。
10. `warn` は調査候補であり、必ずしも即failではない。
11. `fail` は実注文送信検出またはログ整合性破綻などの重大条件として扱う。

## 非対応範囲（継続）
- OANDA/API接続
- 実注文
- demo口座接続
- broker連携
- PipelineAdapter本体の売買判断変更
- BacktestRunner本体の戦略変更
- HTF/SR/Session/RiskStop/Haltのfilter化
- 株式拡張
- Equity Adapter
- lot sizing本体実装
- 収益性評価
- パラメータ最適化
- ML/HMM/LSTM実装

## 残る未解決点
- `pipeline_adapter_error` の error type別集計を追加するか未決。
- dry-run artifact の保存・レビュー運用（保管期間、レビュー手順、参照先）の詳細化は未実施。

## 次候補
1. `pipeline_adapter_error` の error type別集計要否を判断。
2. dry-run artifact 保存・レビュー運用の詳細化。
3. 次フェーズ候補の優先順位を整理（OANDA/API接続は後続として保持）。

## 実装変更有無
- 本整理では、実装・売買ロジック変更は行っていない（docs / ops 更新のみ）。
