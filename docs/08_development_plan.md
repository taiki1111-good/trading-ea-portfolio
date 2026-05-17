# 開発計画

## 1. 目的
本ドキュメントでは、本EAをどの順序で設計・実装・検証していくかを整理する。

本プロジェクトでは、いきなり完成形を作るのではなく、
- 設計を先に固める
- 上流から下流へ順に実装する
- 各段階でテストを挟む
- 実験領域と本体を分ける
- agent を活用しつつ、人間が確認する

という方針で進める。

## 2. 全体方針

### 2.1 基本方針
- 先に設計文書を整備する
- 実装は Data から順に進める
- 各段階で単体確認と接続確認を行う
- 新規裁量パターンは experiments 領域で試す
- 採用前にレビューと記録を残す

### 2.2 役割分担の想定
- 5.4thinking（チャット/アプリ）: 戦略、設計、受け入れ基準の整理
- 5.4（VSCode）: repo 内作業単位への落とし込み
- Copilot / Cursor: 実装、下書き、機械的修正
- 5.3 Codex（VSCode auto）: 差分レビュー、整合性確認、揃え込み
- Human: 最終確認、採用判断、設計判断の承認

補足:
- Data 実装準備から骨組み着手までは、5.3 Codex 通常運用で完結できる粒度で進める

## 3. 開発フェーズ

### Phase 1: リポジトリと設計基盤の整備
目的:
- フォルダ構成を確定する
- docs / ops / portfolio / experiments の役割を確定する
- agent 運用ファイルを整備する

完了条件:
- リポジトリ構成が固定されている
- `AGENT_INDEX.md` と `REPO_MAP.md` が整っている
- `ops/` 配下の運用ファイルが存在する

### Phase 2: 設計文書の確定
目的:
- 要件、アーキテクチャ、モジュール仕様、変数仕様、状態仕様、テスト計画を一通り固める

対象:
- `docs/01_overview.md`
- `docs/02_requirements.md`
- `docs/03_architecture.md`
- `docs/04_module_spec.md`
- `docs/05_variable_spec.md`
- `docs/06_state_spec.md`
- `docs/07_test_plan.md`
- `docs/08_development_plan.md`

補足:
- `docs/10_interface_contract.md` は存在する補助文書として認識する
- ただし今回時点では、主要な Source of Truth は上記 `docs/01` から `docs/08` とする
- Data 実装に関しては `docs/11_data_source_policy.md` を必須参照文書として追加する

完了条件:
- 主要文書が一通り埋まっている
- docs 同士の大きな矛盾がない
- `ops/CURRENT_TASKS.md` に次の実装対象が明記されている

### Phase 3: 骨組み実装
目的:
- 本体モジュールの最小骨組みを作る

実装順序:
1. Data
2. HTFContext
3. LTFStructure
4. Signal
5. RiskFilter
6. Execution
7. Logger
8. Evaluator

完了条件:
- 各モジュールに最小のファイルが存在する
- モジュール名と責務が仕様書と一致している
- 単体テストの雛形がある

### Phase 4: 基本接続
目的:
- 上流から下流まで最低限のデータの流れを通す

対象:
- Data -> HTFContext
- Data -> LTFStructure
- HTFContext + LTFStructure -> Signal
- Signal -> RiskFilter
- RiskFilter -> Execution
- Execution -> Logger
- Logger -> Evaluator

完了条件:
- 小規模データで一通り流せる
- 状態遷移が破綻しない
- 理由ログが最低限残る

### Phase 5: 初期売買ロジック導入
目的:
- 初期のコアロジックを入れる

初期対象:
- 上位足方向一致
- 第三波の高値・安値突破
- 上位抵抗余地確認
- 指標停止
- spread 停止

補足:
- 初期 main では `third_wave_break` のみを対象とする
- `triangle_break` は `experiments` 領域で先行検証する
- 複数パターン競合時は安全側で見送る

完了条件:
- 初期ロジックが本体に入っている
- 停止条件が働く
- 最低限のシナリオテストがある

### Phase 6: 実験領域の運用開始
目的:
- 新たな裁量パターンを experiments 領域で試せるようにする

対象:
- `docs/experiments/`
- `src/experiments/`
- `tests/experiments/`
- `triangle_break` の先行検証

完了条件:
- experiment template に沿って新規仮説を記録できる
- 実験コードを本体から分離して置ける
- 採用前後を記録できる

### Phase 7: 本体改善と比較
目的:
- 実験で有望なものを本体へ組み込むか比較する

完了条件:
- 変更メモが残っている
- review 記録が残っている
- decision log に採用判断が残っている

## 4. モジュール実装順序の詳細

### Step 1: Data
作業内容:
- `src/data/price_loader.py` の骨組み作成
- `src/data/event_loader.py` の骨組み作成
- `src/data/timeframe_aligner.py` の骨組み作成
- `src/data/validator.py` の骨組み作成
- `src/data/types.py` の型定義骨組み作成
- `tests/unit/` または `tests/integration/` に Data 向けテスト骨組みを作成
- `tests/fixtures/` に Data 初期 fixture を作成
- `docs/11_data_source_policy.md` に基づき、CSV / parquet / pkl の役割、UTC 統一、spread / bid-ask / volume、H1/H4 集約の受け入れ観点を固定する

確認:
- unit test 雛形
- Data -> HTFContext / LTFStructure の受け渡し確認
- `data_valid_flag` / `validation_reason` の失敗結果契約確認

### Step 2: HTFContext
作業内容:
- 上位足トレンド方向の骨組み
- 抵抗余地判定の骨組み
- htf_context_reason の設計

確認:
- `docs/05_variable_spec.md` との整合
- Signal への受け渡し確認

### Step 3: LTFStructure
作業内容:
- third_wave_break の骨組み
- main では `third_wave_break` のみを扱う構造組み立て
- `triangle_break` は `experiments` 側で試作・比較できる導線整理
- structure_type / pattern_reason の設計

確認:
- Signal への受け渡し確認
- experiments との住み分け確認

### Step 4: Signal
作業内容:
- HTF と LTF の統合条件の骨組み
- entry_signal / signal_reason の設計

確認:
- RiskFilter への接続確認
- 見送り条件との責務分離確認

### Step 5: RiskFilter
作業内容:
- event 停止
- spread 停止
- lot / stop_loss / take_profit の骨組み

確認:
- filter_reason / risk_reason の記録確認
- Execution への安全な入力確認

### Step 6: Execution
作業内容:
- 状態遷移に沿った実行骨組み
- ENTRY_PENDING / EXIT_PENDING の扱い
- execution_reason の記録

確認:
- `docs/06_state_spec.md` との整合
- Logger への受け渡し確認

### Step 7: Logger
作業内容:
- 各 reason の記録骨組み
- state transition 記録
- trade_id / log_time 設計

### Step 8: Evaluator
作業内容:
- 基本指標集計
- structure_type ごとの比較基盤
- filter_hit の集計基盤

## 5. agent 利用前提の運用

### 5.1 変更の流れ
1. `ops/CURRENT_TASKS.md` で対象を確認
2. agent が実装または修正
3. worklog を残す
4. review に回す
5. 人間が確認
6. 必要なら Codex に横断レビュー依頼
7. 承認後に採用判断を記録

### 5.2 実装前に参照する文書
- `docs/02_requirements.md`
- `docs/03_architecture.md`
- `docs/04_module_spec.md`
- `docs/05_variable_spec.md`
- `docs/06_state_spec.md`
- `docs/07_test_plan.md`
- `docs/11_data_source_policy.md`（Data 実装時は必須）
- `AGENT_INDEX.md`
- `REPO_MAP.md`

必要に応じて:
- `docs/10_interface_contract.md`

### 5.3 実装後に更新対象となる文書
- 該当モジュール仕様
- `ops/CURRENT_TASKS.md`
- worklog
- review 記録
- 必要に応じて `ops/DECISION_LOG.md`

## 6. 実装開始条件
以下を満たしたら本格実装を開始する。
- 設計文書 `docs/01` から `docs/08` が一通り埋まっている
- モジュール責務が明確である
- 主要変数が整理されている
- 状態仕様が整理されている
- テスト計画がある
- agent 運用ファイルが整っている

### 6.1 Data 骨組みの着手条件（直近）
- `docs/11_data_source_policy.md` の受け入れ基準（CSV / parquet / pkl、UTC、spread / bid-ask / volume、H1/H4 集約、用途別採用判定）が参照可能である
- 作成対象ファイル（`src/data/price_loader.py`、`src/data/event_loader.py`、`src/data/timeframe_aligner.py`、`src/data/validator.py`、`src/data/types.py`）が `ops/CURRENT_TASKS.md` に明記されている
- Data テスト骨組み（`tests/unit/` または `tests/integration/`）と初期 fixture（`tests/fixtures/`）の対象ケースが `docs/07_test_plan.md` と整合している
- `data_valid_flag` / `validation_reason` の返却契約が `docs/04`、`docs/05`、`docs/07` で矛盾していない

## 7. 実験追加時の流れ
1. `docs/experiments/` に仮説を記録
2. `src/experiments/` に試作コードを追加
3. `tests/experiments/` で確認
4. worklog を残す
5. review に回す
6. 有望なら本体採用候補にする
7. 採用時は `ops/DECISION_LOG.md` に記録する

## 8. 今後詳細化するもの
- 各フェーズの完了判定をさらに厳密化する
- 実装担当 agent ごとのルール詳細
- review の優先度
- 実験採用基準
- branch 運用の詳細

## 9. Minimum Core v0.1 完了後の参照先（v0.2+）
本ドキュメントは初期開発計画（v0.1 までの骨組み整備）として維持する。

Minimum Core v0.1 を `structural validation complete` として閉じた後の実装順序・検証順序・完了条件は、以下の統合ロードマップを参照する。
- `docs/17_backtest_design.md` の「EA Master Implementation Roadmap v0.2+」
- `docs/ops/EA_MASTER_IMPLEMENTATION_ROADMAP_v0_2_plus.md`

補足:
- v0.1 結果と v0.2 以降の結果を混同しない。
- v0.2 以降の順序は `ops/CURRENT_TASKS.md` の単発更新ではなく、上記 Roadmap を優先して固定運用する。
