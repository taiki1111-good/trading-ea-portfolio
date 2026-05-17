# プロジェクト KPI

## 1. 文書の目的
この文書は、`trading-ea` プロジェクトの成功を評価するための指標と受け入れ基準を整理する。
`docs/02_requirements.md` で示した要件を受けて、具体的な完了条件と評価軸を整備する。

## 2. プロジェクト成功条件
- `docs/02_requirements.md` の Must 要件が満たされること
- `docs/03_architecture.md` で定義された基本フローが実装と検証で再現されること
- `docs/07_test_plan.md` で定義されたテスト層が段階的に整備されること
- `ops/CURRENT_TASKS.md` で Data 実装準備が主軸に維持されること
- `docs/15_non_functional_requirements.md` で定義する非機能品質が設計・運用に反映されること

## 3. フェーズ別完了条件
### Phase 1: 基盤設計整備
- `docs/01`〜`docs/08` が一通り整備されている
- `AGENT_INDEX.md` / `REPO_MAP.md` / `ops/CURRENT_TASKS.md` が実務に沿った状態になっている
- `docs/10_interface_contract.md` を補助資料として参照できる

### Phase 2: Data 実装準備
- Data モジュールの受け入れ基準が明確である
- `docs/11_data_source_policy.md` のデータ入力方針が参照可能である
- `PriceDataLoader` / `EventDataLoader` / `TimeframeAligner` / `DataValidator` の骨組みが設計されている

### Phase 3: 骨組み実装と基本接続
- Data から Execution までの基本フローが最小限で通る
- `docs/06_state_spec.md` で定義した状態遷移が再現される
- ログ記録と評価基盤の最低限が存在する

### Phase 4: 初期本体ロジック導入
- `third_wave_break` を中心とした本体ロジックが実装されている
- `triangle_break` は `experiments` 領域で分離されている
- 基本停止条件が動作する

### Phase 5: 実証と改善
- テスト・シナリオで主要ケースが検証できる
- ログから判断理由と状態遷移を追跡できる
- 改善候補が `ops/DECISION_LOG.md` や `docs/experiments/` で記録される

## 4. main v0 受入基準
- `docs/02_requirements.md` の Must 機能要件が主要部分で満たされる
- `Data`、`HTFContext`、`LTFStructure`、`Signal`、`RiskFilter`、`Execution` の基本データフローが確認済みである
- `position_state` の基本状態遷移が `IDLE` / `ENTRY_PENDING` / `POSITION_OPEN` / `EXIT_PENDING` / `SUSPENDED` / `ERROR` で成立する
- `third_wave_break` が本体で扱われ、`triangle_break` は実験領域に留まる
- 最低限のログと評価指標が出力できる状態である
- `tests/` のユニット・統合・シナリオの雛形が作成されている

## 5. ポートフォリオ観点の達成条件
- `portfolio/` に外部向け説明の骨子が用意されている
- 設計の目的、構造、品質方針が正しく伝えられる
- 本体と実験の境界が明確に説明できる
- Data 実装準備に注力する姿勢が明示されている

## 6. 未確定事項
- 数値的なパフォーマンス目標（勝率、プロフィットファクター、ドローダウン許容値）は未確定 / TBD
- 実装後の運用基準（稼働開始条件・停止基準の閾値）は未確定 / TBD
- 実験の採用判断基準の詳細は `docs/16_operation_design.md` で補足するが、現時点では未確定である
