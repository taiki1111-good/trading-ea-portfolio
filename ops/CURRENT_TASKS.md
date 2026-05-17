# CURRENT TASKS

## 1. 現在の段階
現在は **Phase 9 CSV replay pipeline dry-run minimal completion reached (Option A)** 段階です。
併せて **Risk/Stop v0 minimal implementation adopted（採用済み最小実装）** 段階です。
加えて **PipelineAdapter planner chain正式接続 採用済み** 段階です。

重要前提:
- 実 broker / OANDA API / 実注文送信は未実装。
- 収益性確認済みではない。
- lot sizing本体は未実装（`PositionSizer` は placeholder）。
- `PositionSizer` は placeholder 実装であり、lot sizing本体ではない。
- `PipelineAdapter` は planner chain（`PositionSizer` / `StopLossPlanner` / `TakeProfitPlanner` / `RiskAssembler`）へ正式接続済み。
- 接続は fixed baseline 同値維持（`fixed_lot` / fixed SL distance / fixed TP distance の価格同値）を目的とし、機能拡張を目的としない。
- Session v2 は diagnostic_only で継続し、entryを止めない。
- 実filter化判断は保留。
- Session/SR/HTF の本体filter化は未実装。
- Phase 9 の minimal completion criteria は `docs/17_backtest_design.md` に記録済み。
- representative run 確認（weekday / weekend expected gap）は完了。
- weekend / market closure gap の初期扱いは `docs/17_backtest_design.md` に記録済み。

## 2. 次タスク
1. Reason Category 系フェーズ（第1段階）は完了扱いとする（Reason Catalog最小実装 + scripts適用 + `FilterAnalyzer.analyze_by_category()` 採用まで完了）。
2. lot sizing本体フェーズ判断は完了とする（独立フェーズ `Lot Sizing v1` を採用、初期は isolated calculator 限定、PipelineAdapter本線接続は後続判断）。
3. `Lot Sizing v1` の実装前契約（formula/config/invalid/rounding/clamp）は固定完了とする。
4. `Lot Sizing v1` isolated calculator 実装は完了とする（unit test限定、PipelineAdapter/BacktestRunner/main path 非接続）。
5. `Lot Sizing v1` isolated calculator は採用済みとする（formula/rounding/clamp/invalid を unit test で固定済み、本線非接続）。
6. `Lot Sizing v1` の `PipelineAdapter` / `PositionSizer` 本線への即時接続は No-Go / Hold とする（fixed_lot baseline維持、PnL/trade_count非影響を優先）。
7. `Lot Sizing v1` shadow mode / comparison-only 方針は固定完了とする（C/B優先、Aは後続候補）。
8. `Lot Sizing v1` shadow mode v0 を C（専用offline comparison script）で実装完了とする。
9. `Lot Sizing v1` shadow comparison v0 の採用前レビューは完了とする（Go採用、comparison-only維持）。
10. 行単位派生列CSV（`lot_sizing_shadow_rows.csv`）は当面維持し、接続判断材料として継続する。
11. canonical出力へ段階移行する場合は、既存出力の削除・改名を行わず追加形式で進める。
12. detail旧形式（legacy detail）は即廃止せず deprecated 扱いで段階移行する。
13. `Lot Sizing v1` shadow comparison v0 の representative run 手順による運用定着確認は完了とする（1回実行で確認済み）。
14. Session / SR / HTF filter化の優先順位整理は完了とする（推奨順: HTF -> Session -> SR）。
15. HTF filter v1 の実装前契約整理は完了とする（ON条件 / neutral policy / 最小ログ項目 / 評価指標 / 非対応範囲を固定）。
16. HTF diagnosticログ確認は完了とする（比較必須列の充足/欠落を整理済み）。
17. HTF diagnostic comparison に必要な不足ログ項目の最小追加設計は完了とする（行レベル8列 + summary候補5項目を固定）。
18. HTF diagnostic comparison に必要な near_live decision log 最小8列の additive 追加は完了とする（既存列互換維持）。
19. HTF near_live 8列追加後の representative run 出力確認は完了とする（実出力で8列存在と非影響を確認済み）。
20. HTF diagnostic comparison 設計は完了とする（OFF/permissive/strict 条件・評価指標・実行フローを固定）。
21. HTF diagnostic comparison runner/analysis script の最小実装は完了とする（OFF/permissive/strict の3条件比較を実行可能化）。
22. HTF diagnostic comparison runner の representative比較実行は完了とする（3条件summaryとno-real-order安全性を確認済み）。
23. HTF diagnostic comparison runner に entry集合差分（`timestamp + signal_type` 基準）の最小summary追加を完了とする（`htf_off` 基準で removed/added/intersection を比較可能化）。
24. entry集合差分は near_live diagnostic comparison 用であり、収益性評価（PnL/win_rate/average_pnl/total_pnl/exit reason counts）ではないことを固定する。
25. `timestamp + signal_type` は v0 比較キーとし、将来は必要に応じて厳密キーへ拡張可能とする。
26. entry集合差分summaryの representative run（3条件、既存代表入力）を完了とする。新規列が出力され、`entry_set_removed_vs_htf_off_count=0` かつ permissive/strict の `htf_filter_rejected_count>0` ケースを確認した。
27. HTF diagnostic comparison runner に accepted/rejected entry set summary（`entry_signal && trade_ok` / `entry_signal && htf_filter_rejected`）の最小追加を完了とする。
28. candidate/accepted/rejected の3集合を分離して比較可能化し、候補生成差分と通過判定差分の切り分けを可能にした。
29. candidate/accepted/rejected 追加後の representative run（3条件、既存代表入力）を完了とする。今回runでは candidate/accepted は同一、`htf_filter_rejected_count>0` でも `entry_signal==True` 条件付き rejected set は0件だった。
30. HTF diagnostic comparison v0 は現時点でいったん完了扱いとする（runner実装・representative run・candidate/accepted/rejected実出力確認まで完了）。
31. v0の解釈として、今回fixtureでは HTF rejection観測が `entry_signal==True` 候補行に反映していないことを確認した（candidate/accepted/rejected差分なし、ただし permissive/strict の `htf_filter_rejected_count=2`）。
32. `entry_signal` 非依存の全行ベース HTF rejection trace 追加は future optional とし、現時点では優先しない。
33. 次判断は、HTF周辺をさらに深掘りするか、lot sizing shadow comparison の軽微修正・採用確認、または portfolio docs / README / presentation notes 整理へ戻るかで行う。
34. OANDA/API接続準備は後続として保持する（Phase 9直後では着手しない）。
35. lot sizing shadow comparison は diagnostic / shadow comparison tool として採用する（fixed baseline と risk-based lot の差分確認用途）。
36. 採用は本体lot sizing接続を意味しない。`PositionSizer` placeholder 維持、`PipelineAdapter` / `BacktestRunner` / `RiskAssembler` / `PositionSizer` の本線挙動は変更しない。
37. `fixed_lot <= 0` 時の diff/ratio 空欄仕様と summary 空欄仕様はテストで固定済みとする。
38. lot sizing shadow comparison の representative output 記録を完了とする（row-level/summary 出力生成を確認、tmp配下で運用）。
39. 次タスク候補は、portfolio docs / README / presentation notes への位置づけ反映へ進む。
40. portfolio docs / README / presentation notes の narrative 整理を完了とする（分析/検証基盤としての位置づけ、未実装範囲、HTF v0 と lot sizing shadow の扱いを明記）。

## 3. 保留中
- strategy extension policy（continuation失敗を別戦略入力として扱う方針整理）は future extension として保持（docs/19）。
- Session filter本体実装。
- SR v2 rolling high/low 実filter化。
- reaction SR 実装。
- Risk/Stop本体実装。
- lot sizing実装。
- 売買ロジック変更。
- HTF/SR/Session/RiskStop/Haltのfilter化。

## 4. 今セッションの追記
- PipelineAdapter の暫定 fixed 値直結経路を、`PositionSizer` / `StopLossPlanner` / `TakeProfitPlanner` / `RiskAssembler` の planner chain 経路へ置換した。
- `PositionSizer` は placeholder を維持し、`account_balance` は placeholder valid 判定を通す固定値（`placeholder_account_balance=1000.0`）を使用した。
- `entry_price_candidate=current_bar.close` を使用し、fixed baseline と同値の SL/TP（long/short 方向含む）を維持した。
- `tests/unit/backtest/test_pipeline_adapter.py` に invalid `account_balance` の追加テストを入れ、`trade_ok=false` を確認した。
- テスト結果: targeted `93 passed`（risk_filter 29 + integration 8 + pipeline_adapter 56）、full `421 passed`。
- 実装結果は `ops/worklog/2026-05-15_pipeline_adapter_planner_chain_impl.md` に記録した。
- PipelineAdapter planner chain正式接続について、実装要否判断を A（次フェーズ実装）で固定した。
- 実装スコープは `PipelineAdapter -> PositionSizer / StopLossPlanner / TakeProfitPlanner / RiskAssembler` の接続に限定し、`fixed_sl_tp` baseline 同値維持を必須条件にした。
- `PositionSizer` は placeholder 維持、`account_balance` は placeholder valid判定を通す固定値入力を使用、`entry_price_candidate` は `current_bar.close` を仮固定とした。
- Go/No-Go 条件（trade_count不変、SL/TP同値、decision trace主要列維持、invalid入力で `trade_ok=false`、targeted+full pytest 前提）を worklog に記録した。
- 時系列整理（Risk/Stop v0）:
- 1) docs前段整理:
- `docs/04` / `docs/05` / `docs/10` / `docs/17` に責務境界・I/O・非対応範囲を追記した（`ops/worklog/2026-05-09_risk_stop_v0_scope_design.md`）。
- 2) 実装前受け入れ基準固定:
- `lot` / `trade_ok` 契約、PositionSizer placeholder、`entry_price_candidate`、`max_holding_bars` 境界、実装完了条件を固定した（`ops/worklog/2026-05-09_risk_stop_v0_pre_impl_acceptance.md`）。
- 3) 最小実装完了:
- `src/risk_filter` で PositionSizer placeholder / StopLossPlanner / TakeProfitPlanner / RiskAssembler を実装した。
- `tests/unit/risk_filter`、`tests/integration/test_signal_to_risk_filter.py`、関連 backtest unit test を更新し、`trade_ok` 契約を確認した。
- テスト結果: targeted `88 passed`、full `413 passed`（`ops/worklog/2026-05-09_risk_stop_v0_minimal_impl.md`）。
- 4) `/review` 実施:
- Risk/Stop v0 の docs/code/tests/ops 横断レビューを実施し、採用前の小修正項目を整理した。
- 5) `/review` follow-up（小修正）:
- `PositionSizer` placeholder に `account_balance > 0` 前提チェックを追加し、`fixed_lot` と `account_balance` の不正値（bool/NaN/inf含む）で `invalid_lot` を返すことを確認した。
- `RiskAssembler` に NaN/inf/bool と `signal_type=exit` の拒否テストを追加した。
- （過去経緯）`PipelineAdapter` は planner chain 未接続の暫定固定値経路（`fixed_lot` / fixed SL / fixed TP -> `RiskAssembler`）を維持していた。この扱いは `ops/worklog/2026-05-09_risk_stop_v0_review_followup.md` に記録済み。
- テスト結果: targeted `92 passed`、full `420 passed`。
- 現在の扱い:
- Risk/Stop v0 は「採用済み最小実装（minimal implementation adopted）」として扱う。
- `lot sizing` 本体実装および詳細仕様固定は後続保持とする。
- `risk_reason` / `filter_reason` の語彙管理方針は、enum化ではなく Reason Catalog + 定数運用（`category_token[:detail]` 許容）を採用した。
- Reason Catalog 最小実装として `src/risk_filter/reason_catalog.py` を追加し、`normalize_reason_category()` で旧/新形式のcategory正規化を可能にした。
- `RiskAssembler` / `PositionSizer` / `StopLossPlanner` / `TakeProfitPlanner` で定数利用へ寄せ、`all risk filters passed` は互換維持のため現行出力を保持した。
- 採用前レビューの軽微修正として、互換保証は category token レベル（detail は移行対象）であることを docs/worklog に明記し、旧detail/newdetail 混在時の正規化テストを追加した。
- 最終軽微修正として `_LEGACY_TO_CANONICAL` の適用順序を修正し、raw legacy prefix を先に参照するようにした。加えて複数reason用の `normalize_reason_categories()` を追加し、`|` 連結reasonのcategory list化をテストで固定した。
- Reason Catalog 最小実装は採用済みとし、後続は Evaluator/分析スクリプト側の category 正規化適用計画へ進む。
- analysis script 適用（第1段階）として `scripts/analyze_backtest_run_logs.py` に `risk_reason` / `filter_reason` の category 集計を追加した（`normalize_reason_categories()` 利用、既存列置換なし）。
- analysis script 第1段階（Reason category集計）は採用済みとした。None/空白/欠損は unknown 扱いに統一し、`"none"` category 誤集計を防止した。
- 採用記録は `ops/worklog/2026-05-15_reason_category_analysis_adoption.md` に記載し、次タスクは A（dry-run summary側への適用判断）を推奨とした。
- dry-run summary側（`summarize_csv_replay_dry_run.py`）への reason category 適用要否を判断し、A（最小実装で追加）を採用した。
- dry-run summary側（`summarize_csv_replay_dry_run.py`）に reason category 派生メトリクスを最小追加した（`normalize_reason_categories()` 利用、既存summary項目は維持）。
- `risk_reason` 列なしの場合は risk側を集計対象外（counts空、unknown_count=0）とし、列ありで値欠損時のみ unknown 加算する仕様をテストで固定した。
- 追加対象は `near_live_decision_logs.csv` の `risk_reason` / `filter_reason` を主対象とし、`decision_reason` / `signal_reason` は自由文のため category 集計対象外とする。
- 互換方針として既存 `near_live_summary.csv/.md` と既存 `dry_run_period_summary.csv/.md` の既存項目は削除・改名せず、派生メトリクス追加のみとする。
- 計画記録は `ops/worklog/2026-05-15_reason_category_dry_run_summary_plan.md` に記載した。
- 実装記録は `ops/worklog/2026-05-15_reason_category_dry_run_summary_impl.md` に記載した。
- dry-run summary reason category 派生メトリクス実装は採用済みとして確定した。採用記録は `ops/worklog/2026-05-15_reason_category_dry_run_summary_adoption.md` に記載した。
- 次タスクは `src/evaluator/filter_analyzer.py` の category基準化判断へ進める。
- `FilterAnalyzer` の category基準化方針は A（既存 `analyze()` 維持 + `analyze_by_category()` 追加）を採用した。
- 既存 `FilterStatsResult.filter_reason` を壊さず、完全一致分析とcategory分析を併存させる方針を固定した。
- 方針記録は `ops/worklog/2026-05-15_filter_analyzer_category_policy_decision.md` に記載した。
- `src/evaluator/filter_analyzer.py` に `analyze_by_category()` を追加し、既存 `analyze()` を維持したまま category集計を併存させた。
- `|` 連結reasonの複数category加算、欠損unknown、`"none"` 誤集計防止を unit test で固定した。
- `FilterAnalyzer.analyze_by_category()` 実装は採用済みとして確定した。採用記録は `ops/worklog/2026-05-15_filter_analyzer_category_adoption.md` に記載した。
- Reason Category 系フェーズは第1段階完了として区切り、次タスクを lot sizing本体フェーズ判断へ移した。
- targeted test 結果（Reason Catalog最小実装の最終確認）: `tests/unit/risk_filter` 38 passed、`tests/integration/test_signal_to_risk_filter.py` 8 passed、`tests/unit/backtest/test_pipeline_adapter.py` 56 passed。
- `docs/18_asset_class_extension_policy.md` を追加し、Core Framework + Asset Adapter 方針で将来の資産クラス拡張方針を整理した。
- 本追記は future extension policy の明文化であり、株式対応実装・検証には未着手。
- Phase 9 として `summarize_csv_replay_dry_run.py` に pipeline mode を追加し、no real order integrity を含む最小 health 判定（pass/warn/fail）を実装した。
- representative期間（`tests/fixtures/price_m5_h1_h4_base.csv`）で pipeline dry-run と summarizer を実行し、`dry_run_health_status=pass` と near_live/dry_run カウント整合を確認した。
- weekend跨ぎ representative run（`tmp/phase9_pipeline_weekend_rep_20260509/weekend_replay_input.csv`）を実行し、`expected_weekend_gap_count=1` / `ordinary_missing_bar_gap_count=0` / `unknown_gap_count=0` で `dry_run_health_status=pass`（`pipeline_health_ok`）を確認した。
- Phase 9 minimal completion 後の次フェーズ候補（A〜F）を比較し、優先順位・理由・非対応範囲・実装着手条件を worklog に整理した。
- PipelineAdapter planner chain正式接続について、要否判断の観点（メリット/リスク）、着手条件、非対応範囲、接続時テスト観点を docs/ops に整理した。
- （過去経緯）当時は暫定固定値経路（`fixed_lot` / fixed SL distance / fixed TP distance -> `RiskAssembler`）を維持し、planner chain正式接続を未着手としていた。現在は実装済み。
- lot sizing本体フェーズの扱いを判断し、独立フェーズ `Lot Sizing v1` として進める方針を採用した。
- `Lot Sizing v1` は初期実装を isolated calculator（unit test完結）に限定し、`PipelineAdapter` / backtest main path への接続は後続判断とした。
- `fixed_lot` baseline は維持し、`PositionSizer` placeholder と現行 planner chain の本線挙動は変更しない方針を固定した。
- `Lot Sizing v1` の非対応範囲として、実運用lot制約、OANDA/API、実注文、broker別厳密制約、収益性評価、売買ロジック変更を明記した。
- Go/No-Go 条件（docsでformula/config/invalid固定、unit testのみで検証可能、PipelineAdapter未接続でも完了扱い可）を `ops/worklog/2026-05-15_lot_sizing_v1_policy_decision.md` に記録した。
- `Lot Sizing v1` の実装前 contract を固定した（formula/config/invalid/rounding/clamp）。
- 式は `lot = account_balance * risk_per_trade / (stop_loss_distance_pips * pip_value_per_lot)` で固定した。
- 出力は `lot/raw_lot/rounded_lot/clamped_flag/size_reason` を固定した。
- rounding は `floor` 固定、`round`/`ceil` 非対応を明記した。
- clamp は `max_lot` のみ許容、`rounded_lot < min_lot` は引き上げず invalid と固定した。
- 上記判断は `ops/worklog/2026-05-15_lot_sizing_v1_contract_decision.md` に記録した。
- `src/risk_filter/lot_sizing_calculator.py` に isolated `LotSizingCalculator`（`LotSizingV1Config` / `LotSizingV1Result`）を追加した。
- `tests/unit/risk_filter/test_lot_sizing_calculator.py` を追加し、formula/floor rounding/max clamp/min invalid/invalid条件/PositionSizer非影響を固定した。
- 本実装は isolated calculator + unit test に限定し、`PipelineAdapter` / `BacktestRunner` / `PositionSizer` 本線挙動は変更していない。
- 実装記録は `ops/worklog/2026-05-15_lot_sizing_v1_isolated_calculator_impl.md` に記載した。
- `Lot Sizing v1` isolated calculator は採用済みとした。
- 採用根拠:
- formula / rounding / clamp / invalid 条件が unit test で固定されている。
- `PipelineAdapter` / `BacktestRunner` / `PositionSizer` 本線は未接続。
- `fixed_lot` baseline は維持され、PnL / trade_count 影響経路は変更していない。
- 確認結果:
- `pytest -q tests/unit/risk_filter/test_lot_sizing_calculator.py` は `13 passed`。
- `pytest -q tests/unit/risk_filter` は `51 passed`。
- `git diff --check` は問題なし。
- 採用記録は `ops/worklog/2026-05-15_lot_sizing_v1_isolated_calculator_adoption.md` に記載した。
- `Lot Sizing v1` calculator の `PipelineAdapter` / `PositionSizer` 本線への即時接続は No-Go / Hold と判断した。
- 理由は fixed_lot baseline 破壊リスク、PnL/trade_count/risk logs 解釈変化、`pip_value_per_lot` 手入力前提、broker/OANDA未対応、収益性論点拡散リスクである。
- 次フェーズは shadow mode / comparison-only 設計とし、`fixed_lot` 本線維持 + risk-based lot 診断比較を優先する。
- shadow mode でも PnL/trade_count/entry/exit 判断には影響させない方針を固定した。
- 判断記録は `ops/worklog/2026-05-15_lot_sizing_v1_pipeline_connection_decision.md` に記載した。
- `Lot Sizing v1` shadow mode / comparison-only の方針を固定した。
- 実装候補は C（専用offline comparison script）を優先、B（analysis script拡張）を次点、A（PipelineAdapter内shadow計算）は後続候補とした。
- 診断値候補は `fixed_lot`、`risk_based_*`、`lot_size_diff`、`lot_size_ratio`、`risk_lot_valid_flag` を採用した。
- 非影響範囲として、actual lot固定、PnL/trade_count/entry/exit/`trade_ok` 非影響、Execution path 非接続を明記した。
- 方針記録は `ops/worklog/2026-05-15_lot_sizing_v1_shadow_mode_policy_decision.md` に記載した。
- `scripts/compare_lot_sizing_shadow.py` を追加し、既存 `trade_logs.csv` / `decision_logs.csv` から risk-based lot を後付け比較する offline shadow comparison を実装した。
- 出力として `lot_sizing_shadow_rows.csv` と `lot_sizing_shadow_summary.csv/.md` を生成し、`fixed_lot` との差分・reason・clamp/invalid統計を記録する。
- `stop_loss_distance_pips` は CSV列優先、欠損時は CLI fallback、両方欠損時はエラーとする。
- 本実装は diagnostic/comparison-only であり、`PipelineAdapter` / `BacktestRunner` / `PositionSizer` / PnL / trade_count / entry/exit / `trade_ok` へ影響させていない。
- テスト結果:
- `pytest -q tests/unit/backtest/test_compare_lot_sizing_shadow.py` は `9 passed`。
- `pytest -q tests/unit/risk_filter/test_lot_sizing_calculator.py` は `13 passed`。
- 実装記録は `ops/worklog/2026-05-15_lot_sizing_v1_shadow_comparison_impl.md` に記載した。
