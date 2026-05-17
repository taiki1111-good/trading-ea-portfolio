# Public Review Checklist

本書は、`trading-ea` を外部向けポートフォリオとして共有する前に確認するためのチェックリストである。

本書は外部説明用の補助文書であり、Source of Truth ではない。正式な現状・契約・実装境界は `ops/CURRENT_TASKS.md`、`docs/03_architecture.md`、`docs/04_module_spec.md`、`docs/05_variable_spec.md`、`docs/10_interface_contract.md`、`docs/17_backtest_design.md` を優先する。

## 1. 主導線

外部説明では、以下を主導線とする。

1. `README.md`
2. `docs/portfolio/portfolio_overview.md`
3. `docs/portfolio/architecture_for_portfolio.md`
4. `docs/portfolio/interview_pitch.md`
5. `docs/portfolio/disclosure_policy.md`
6. 必要に応じて `docs/09_presentation_notes.md`

`ops/worklog/` は詳細な作業履歴・設計判断履歴であり、古い検討や途中経過を含む。外部説明の最初の導線としては扱わない。

## 2. 公開前に確認すること

### 2.1 到達点の表現

- [ ] 「研究・検証用EAフレームワーク」として説明している。
- [ ] 「設計・検証・説明可能性を重視した分析/検証基盤」として説明している。
- [ ] 売買ロジック単体ではなく、責務分離、ログ設計、dry-run（実注文を行わない検証実行）、diagnostic comparison（採用前の診断比較）、shadow comparison（本体挙動に影響させない比較）を中心に説明している。
- [ ] `Data -> HTFContext -> LTFStructure -> Signal -> RiskFilter -> Execution -> Logger -> Evaluator` の一方向フローを説明している。

### 2.2 未実装事項の明記

- [ ] 実際の取引システムとの接続は未実装であると明記している。
- [ ] 注文送信機能は未実装であると明記している。
- [ ] 収益性の確認を主張していない。
- [ ] lot sizing 本体接続は未実装であると明記している。
- [ ] `PositionSizer` は placeholder であると明記している。
- [ ] HTF は diagnostic comparison v0 であり、本体filter採用ではないと明記している。
- [ ] lot sizing は shadow comparison tool であり、本体接続ではないと明記している。
- [ ] Session v2 は diagnostic_only であり、entry を止めないと明記している。
- [ ] Session / SR / HTF の本体filter化は未実装であると明記している。

### 2.3 誤解されやすい表現

以下を肯定文脈で使わない。説明上必要な場合は、「未実装」「対象外」「意味しない」とセットで扱う。

- [ ] 運用準備が完了しているように見える表現
- [ ] 収益性を確認したように見える表現
- [ ] 注文送信機能まで対応しているように見える表現
- [ ] 取引システム接続済み
- [ ] risk-based lot 本体接続済み
- [ ] HTF filter採用済み
- [ ] 株式対応済み
- [ ] AI自動売買完成
- [ ] live ready
- [ ] demo operation ready
- [ ] 本番運用EA
- [ ] 完成済みEA

誤解されやすい表現を使う場合は、`docs/portfolio/disclosure_policy.md` のように注意事項として扱う場合に限る。

### 2.4 数値・ログの扱い

- [ ] dry-run health の `pass` を、収益性や実運用品質として説明していない。
- [ ] no-real-order integrity（実注文が発生していないことの整合確認）を、注文送信機能の実装済み証明として説明していない。
- [ ] worklog 内の個別runや数値を、収益性確認として扱っていない。
- [ ] PnL、win_rate、total_pnl などの成績数値を外部説明の中心にしていない。
- [ ] 抽象ログ例は実データ・実績値ではないと明記している。

### 2.5 公開不要情報

- [ ] ローカルパスを含めていない。
- [ ] API key / token / secret を含めていない。
- [ ] 実データ本体や公開不要なデータパスを含めていない。
- [ ] 個人情報や特定不要な固有名詞を含めていない。

## 3. 推奨する説明順

外部説明では、次の順番で説明する。

1. これは実運用EAではなく、研究・検証用EAフレームワークである。
2. 主な価値は、売買ロジックそのものではなく、責務分離、時系列整合、ログ追跡、検証手順にある。
3. Data から Evaluator までの一方向フローを設計した。
4. BacktestRunner / PipelineAdapter / CSV replay dry-run で構造検証とログ整合を確認する。
5. HTF diagnostic comparison v0 と lot sizing shadow comparison は、本体採用前の診断・比較用である。
6. 注文送信、実際の取引システムとの接続、収益性確認、lot sizing本体接続は未実装である。

## 4. 公開判断

README と `docs/portfolio/*` を中心に見せる場合は、公開向け説明として扱いやすい。

リポジトリ全体を公開する場合は、`ops/worklog/` が詳細履歴・内部作業記録であり、古い検討や途中経過を含むことを説明する。worklog 内の個別runや数値は、収益性確認や運用準備完了を意味しない。
