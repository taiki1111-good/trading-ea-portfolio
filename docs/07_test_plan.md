# テスト計画

## 1. 目的
本ドキュメントでは、本EAの品質を確保するために、どの粒度で、どの観点から、どのようにテストを行うかを整理する。

本システムでは、単に「動くこと」ではなく、以下を確認対象とする。
- 下位部品単体の正しさ
- 上位モジュールとしての整合性
- モジュール間接続の妥当性
- 状態遷移の安全性
- 停止条件の妥当性
- ログの追跡可能性
- 新規裁量パターン追加時の比較可能性

## 2. 基本方針

### 2.1 ボトムアップを基本とする
本システムでは、上位モジュールをいきなり巨大な単位で検証するのではなく、まず下位部品を単体で確認し、それらを組み上げて上位モジュールを検証する。

基本順序は以下とする。
1. 下位モジュール単体テスト
2. 上位モジュール結合テスト
3. 上位モジュール間結合テスト
4. システム統合テスト
5. シナリオテスト
6. 実験比較テスト

### 2.2 モジュールごとに判定方式は異なる
本システムでは、すべてのテストを同じ判定方式で評価することは想定しない。

モジュールや部品によって、以下のように判定方式が異なることを許容する。
- 真偽判定
- 分類結果の一致
- 数値範囲の妥当性
- 状態遷移の一致
- ログ出力の有無
- 理由文字列の有無
- 比較結果の傾向

### 2.3 設計資料との整合
テストは以下の設計資料と整合している必要がある。
- `docs/03_architecture.md`
- `docs/04_module_spec.md`
- `docs/05_variable_spec.md`
- `docs/06_state_spec.md`
- `docs/08_development_plan.md`

### 2.4 契約テストを含める
本システムの下位モジュール単体テストでは、通常の正答確認だけでなく、契約テストも含める。

契約テストでは主に以下を確認する。
- 事前条件を満たす入力で正常に動作するか
- 事前条件を破る入力で定義通り失敗するか
- 事後条件が常に満たされるか
- 不変条件が破れないか
- 失敗時に理由が残るか

### 2.5 テストフレームワーク方針（初期版）
- 初期版のテスト実装は `pytest` を基本とする
- 既存に `unittest` ベース資産がある場合は無理に即時移行せず、段階的に `pytest` へ寄せる
- 最終的な完全統一タイミングは、Data から Signal の骨組み実装後に再判定する

## 3. テスト対象の粒度

### 3.1 下位モジュール単体テスト
交換可能な部品単位のテスト。
例:
- `TrendDetector`
- `ResistanceDetector`
- `SwingExtractor`
- `TriangleDetector`
- `BreakoutDetector`
- `EventFilter`
- `SpreadFilter`
- `PositionSizer`
- `OrderBuilder`
- `StateTransitionManager`

#### 主な目的
- 部品の責務が単独で正しく動くかを確認する
- 修正時の影響範囲を局所化する
- 新規部品を追加・差し替えしやすくする
- 契約違反時の壊れ方が定義通りであるかを確認する

#### 境界
- unit test は原則として 1部品のみを対象とする
- 隣接上位モジュールの実装結果を前提にしない
- broker 接続、永続化、複数上位モジュール横断の確認は unit に含めない

### 3.2 上位モジュール結合テスト
下位部品を組み上げた上位モジュール単位のテスト。
例:
- `HTFContext = TrendDetector + ResistanceDetector + SupportDetector + ContextAssembler`
- `LTFStructure = SwingExtractor + WaveClassifier + TriangleDetector + BreakoutDetector + StructureAssembler`
- `RiskFilter = EventFilter + SpreadFilter + TradeLimitFilter + StopLossPlanner + TakeProfitPlanner + PositionSizer + RiskAssembler`

#### 主な目的
- 下位部品同士の接続が妥当か確認する
- Assembler が正しく働くか確認する
- 上位モジュールの出力が module_spec と一致するか確認する

#### 境界
- integration test は同一上位モジュール内の複数部品、または直接隣接する上位モジュール境界までを対象とする
- 状態機械全体を何状態も跨ぐ確認は scenario 側へ回す

### 3.3 上位モジュール間結合テスト
主要モジュール同士の受け渡し確認。
例:
- `Data → HTFContext`
- `Data → LTFStructure`
- `HTFContext → Signal`
- `LTFStructure → Signal`
- `Signal → RiskFilter`
- `RiskFilter → Execution`
- `Execution → Logger`
- `Logger → Evaluator`

### 3.4 システム統合テスト
システム全体として、上流から下流まで基本フローが通るか確認する。

### 3.5 シナリオテスト
具体的な相場状況・イベント状況を想定し、期待する挙動になるか確認する。

#### 境界
- scenario test は 3状態以上の遷移、または複数上位モジュールを跨ぐ end-to-end 挙動を対象とする
- 停止条件、見送り、復帰、約定後の状態維持などの時間的挙動を確認する

### 3.6 実験比較テスト
本体未採用ロジックを `experiments` 領域で比較・検証する。
- 通常の stop hit と、失敗確定後の逆走拡大ケースとの差分比較を実施する。

## 4. 判定方式の分類

### 4.1 真偽判定
例:
- `event_flag` が立つか
- `trade_ok` が false になるか
- `breakout_flag` が true になるか

### 4.2 分類結果の一致
例:
- `htf_trend_dir = up/down/neutral`
- `structure_type = third_wave_break / triangle_break / none`
- `signal_type = long_entry / short_entry / exit / none`

### 4.3 数値範囲の妥当性
例:
- `lot > 0`
- `stop_loss` が異常値でない
- `take_profit` が負値にならない
- `htf_trend_strength` が想定範囲内

### 4.4 状態遷移の一致
例:
- `IDLE → ENTRY_PENDING`
- `ENTRY_PENDING → POSITION_OPEN`
- `POSITION_OPEN → EXIT_PENDING`
- `ANY → ERROR`

### 4.5 ログ・理由出力の確認
例:
- `signal_reason` が残るか
- `filter_reason` が残るか
- `execution_reason` が残るか
- `transition_reason` が残るか

### 4.6 比較判定
例:
- 実験ロジック A と B の取引数差
- フィルター有無による見送り回数差
- 新旧パターンの比較

### 4.7 契約判定
例:
- 未来参照禁止が守られているか
- `htf_trend_dir` が定義済み値以外を返さないか
- `breakout_flag = true` のとき根拠が `pattern_reason` から追跡可能か
- Data の検証NGが `data_valid_flag = false` と `validation_reason` で返るか
- Data の入力契約違反や処理継続不能障害が例外になるか
- pkl を正本扱いせず、CSV / parquet / pkl の役割が `docs/11_data_source_policy.md` と一致するか
- `trade_ok = true` のとき `lot / stop_loss / take_profit` が有効か
- 不正状態遷移が拒否または安全側遷移されるか

## 5. モジュール別テスト方針

## 5.1 Data

### 下位モジュール単体テスト
#### PriceDataLoader
- timestamp を読めるか
- OHLC が読めるか
- 欠損時の扱いが定義通りか
- timezone を UTC に統一できるか
- timestamp の逆順と重複を検出できるか
- OHLC 異常値（`high < low` など）を検出できるか

#### EventDataLoader
- event_time を読めるか
- event_flag を生成できるか
- event_type を保持できるか

#### TimeframeAligner
- 複数時間足の整合が取れるか
- 上位足と執行足の参照が破綻しないか

#### DataValidator
- 異常値を検出できるか
- 時系列順の崩れを検出できるか
- 検証NG時に、例外ではなく `data_valid_flag = false` と `validation_reason` を返せるか
- 必須列不足・時刻列解釈不能・読み込み元不存在・タイムフレーム指定不正を例外として扱えるか
- `spread` / `bid-ask` / `volume` / `timezone` / 欠損 / `H1/H4` 集約ルールの受け入れ判定ができるか
- `spread` 欠損時の forward fill / fixed fallback の扱いが `docs/11` と一致するか
- `bid` / `ask` 欠損時の再構成可否が `docs/11` と一致するか
- `volume` 欠損時の `0` 正規化と採用可否が `docs/11` と一致するか
- `data_valid_flag` / `validation_reason` を常にペアで返せるか

### データ受け入れ基準テスト（`docs/11_data_source_policy.md` 準拠）
- 年次 CSV を一次ソース候補として扱えるか
- parquet を正規化済み高速処理用として扱えるか
- pkl を作業キャッシュとして扱い、正本扱いしないか
- UTC 統一（`timestamp` / `event_time`）を維持できるか
- H1/H4 集約で未来参照しないか
- 用途別採用判定（構造検証用 / バックテスト基準 / 実運用近似）を区別できるか

### 上位モジュール結合テスト
- Data 全体として必要な出力を揃えられるか
- HTFContext と LTFStructure の両方へ渡せるか

---

## 5.2 HTFContext

### 下位モジュール単体テスト
#### TrendDetector
- 上位足方向を妥当に分類できるか

#### ResistanceDetector
- 上方向の抵抗余地を判定できるか

#### SupportDetector
- 下方向の余地を判定できるか

#### ContextAssembler
- 複数判定をまとめて `htf_bias`, `htf_context_reason` を生成できるか

### 上位モジュール結合テスト
- `htf_trend_dir`
- `htf_trend_strength`
- `htf_resistance_ok`
- `htf_support_ok`
- `htf_context_reason`
が揃うか

### 判定方式例
- 分類一致
- 真偽判定
- 理由文字列の有無

### temporal third_wave_break（Backtest/PipelineAdapter）追加観点
- fallback OFF（`allow_heuristic_fallback=false`）かつ temporal ON（`allow_temporal_third_break=true`）で `structure_source=detector_chain_temporal` の entry が成立するか
- 同一 `recent_third_timestamp` に対して `max_entries_per_recent_third_candidate=1` で2回目以降が抑止されるか
- `max_entries_per_recent_third_candidate=None` で既存挙動（重複許可）が維持されるか
- 異なる `recent_third_timestamp` では dedup 設定下でも entry 可能か
- `fallback_used=false` が維持されるか（fallback OFF 時）
- future leak 防止として、各 step が `bars[:i+1]` のみを使い、`window[-1]` が current bar である契約が壊れていないか

---

## 5.3 LTFStructure

### 下位モジュール単体テスト
#### SwingExtractor
- スイング点を抽出できるか

#### WaveClassifier
- 波動段階を妥当に分類できるか

#### TriangleDetector
- 三角持ち合い候補を検出できるか

#### BreakoutDetector
- 直近高値・安値突破を判定できるか

#### StructureAssembler
- `structure_type`, `pattern_reason`, `structure_candidate` を生成できるか

### 上位モジュール結合テスト
- 初期構想の
  - `third_wave_break`
を main の正式対象として扱えるか
- `triangle_break` は `experiments` テストへ分離されているか
- 競合ケースで `structure_type = none`、`structure_direction = neutral`、`structure_candidate = false` を返せるか

### 判定方式例
- 分類一致
- 真偽判定
- 理由文字列の有無

---

## 5.4 Signal

### 下位モジュール単体テスト
#### DirectionAlignChecker
- 上位足方向と執行足方向の整合を確認できるか

#### PatternGate
- 許容パターンだけ通せるか

#### EntryRuleEngine
- エントリー候補を生成できるか

#### ExitRuleEngine
- イグジット候補を生成できるか

#### SignalAssembler
- `entry_signal`, `exit_signal`, `signal_type`, `signal_reason` を生成できるか

### 上位モジュール結合テスト
- HTF と LTF の結果を正しく統合できるか
- `Signal` が `RiskFilter` に必要な情報を渡せるか

### 判定方式例
- 真偽判定
- 分類一致
- 理由文字列の有無

---

## 5.5 RiskFilter

### 下位モジュール単体テスト
#### EventFilter
- 指標前後停止ができるか
- 外部イベント入力がある場合の停止条件比較テストを行い、誤停止率と危険局面回避率を比較する

#### SpreadFilter
- spread異常で停止できるか

#### TradeLimitFilter
- 当日回数制限、連敗停止を判定できるか

#### StopLossPlanner
- 損切りを異常値なく出せるか

#### TakeProfitPlanner
- 利確を異常値なく出せるか

#### PositionSizer
- ロットが異常値にならないか

#### RiskAssembler
- `trade_ok`, `risk_reason`, `filter_reason` を組み立てられるか

### 上位モジュール結合テスト
- 停止条件とリスク設定をまとめて処理できるか
- `Execution` に安全な入力を渡せるか

### 判定方式例
- 真偽判定
- 数値範囲確認
- 理由文字列の有無

---

## 5.6 Execution

### 下位モジュール単体テスト
#### OrderBuilder
- 注文情報を組み立てられるか

#### OrderSender
- 発注結果を扱えるか

#### FillHandler
- 約定結果を整理できるか

#### StateTransitionManager
- 06_state_spec に沿って状態遷移できるか
- `entry_timeout` で `ENTRY_PENDING -> IDLE` へ戻れるか
- `exit_timeout` で `EXIT_PENDING -> ERROR -> SUSPENDED` の安全側遷移が取れるか

### 上位モジュール結合テスト
- `Execution` 全体として `position_state` を正しく更新できるか
- `Logger` に必要情報を渡せるか

### 判定方式例
- 状態遷移一致
- 真偽判定
- 理由文字列の有無

---

## 5.7 Logger

### 下位モジュール単体テスト
#### DecisionLogger
- `signal_reason`, `risk_reason`, `filter_reason` を残せるか

#### TradeLogger
- 約定や損益を残せるか

#### StateLogger
- `state_logs` を生成できるか
- `position_state / previous_state / next_state / transition_reason / order_result / execution_reason / log_time` を `state_logs` に残せるか

#### EventLogger
- 見送りや停止を記録できるか
- 状態遷移情報を `event_logs` に混在させないか

### 上位モジュール結合テスト
- Evaluator に必要なログ形式を揃えられるか
- `state_logs` を独立ログ集合として揃えられるか

### 判定方式例
- ログ有無
- 項目有無
- 参照可能性

---

## 5.8 Evaluator

### 下位モジュール単体テスト
#### MetricsCalculator
- `trade_count`, `win_rate`, `average_pnl`, `profit_factor`, `max_drawdown` を算出できるか
- 全期間と月次で集計できるか

#### StructureAnalyzer
- 構造ごとの成績比較ができるか
- `structure_type_stats` を生成できるか
- 構造種別単位で集計できるか

#### FilterAnalyzer
- フィルター停止回数を集計できるか
- `filter_hit_stats` を生成できるか
- `filter_reason` 別の集計ができるか

#### ReportAssembler
- 要約を生成できるか
- `signal_type_stats` を含む初期版出力をまとめられるか

### 上位モジュール結合テスト
- Logger の出力を読んで集計できるか
- `state_logs` を独立入力として扱えるか
- `signal_type` 別の集計ができるか
- 必要に応じて `event_type` 別の集計ができるか
- 実験ロジックと本体ロジックを比較できるか

---

## 6. 上位モジュール間結合テスト方針

### 6.1 基本方針
上位モジュール間では、内部実装ではなく出力インターフェースの整合を重視する。

### 6.2 主な確認対象
- 必要変数が渡っているか
- 命名が variable_spec と一致しているか
- `*_reason` が欠けていないか
- `state_spec` と矛盾がないか
- `state_logs` と `event_logs` の責務が分離されているか

---

## 7. 状態遷移テスト方針
06_state_spec に基づき、状態遷移は重点的に確認する。

### 重点確認項目
- `IDLE → ENTRY_PENDING`
- `ENTRY_PENDING → POSITION_OPEN`
- `ENTRY_PENDING → IDLE`
- `POSITION_OPEN → EXIT_PENDING`
- `EXIT_PENDING → IDLE`
- `IDLE → SUSPENDED`
- `ANY → ERROR`
- `ERROR → SUSPENDED`

### 特に防ぎたいもの
- 二重エントリー
- ENTRY_PENDING 中の再発注
- EXIT_PENDING 中の新規発注
- SUSPENDED 中の通常取引

---

## 8. 境界値・停止条件テスト方針

### 対象例
- spread閾値の直前・直後
- 最大取引回数の直前・直後
- 連敗停止回数の直前・直後
- 指標時刻の直前・直後
- ATR条件の直前・直後

### 方針
停止条件は本システムの安全性に直結するため、通常条件より優先して確認する。

---

## 9. 実験ロジックのテスト方針

### 基本方針
新しい裁量パターンや補助ロジックは、原則として `experiments` 領域で先にテストする。

### 確認項目
- 本体を壊していないか
- 既存部品と分離されているか
- 比較可能な形で結果を出せるか
- 採用前に review へ回せるか
- 誤停止率と危険局面回避率の比較を含める
---

## 10. テスト実装の置き場
- 下位モジュール単体テスト: `tests/unit/`
- 上位モジュール結合テスト: `tests/integration/`
- システム統合・状態遷移・シナリオテスト: `tests/scenario/`
- テストデータ・補助: `tests/fixtures/`
- 実験ロジック用テスト: `tests/experiments/`

### 10.1 初期 fixture 一覧
初期版で最低限そろえる fixture 単位は以下とする。

| fixture_id | path | 形式 | 主用途 |
|---|---|---|---|
| `DATA_PRICE_001` | `tests/fixtures/price_m5_valid_utc.csv` | CSV | Data 正常系 |
| `DATA_PRICE_002` | `tests/fixtures/price_m5_reverse_timestamp.csv` | CSV | timestamp 逆順検出 |
| `DATA_PRICE_003` | `tests/fixtures/price_m5_missing_spread.csv` | CSV | spread 欠損 fallback |
| `DATA_PRICE_004` | `tests/fixtures/price_m5_missing_bid_ask.csv` | CSV | bid/ask 再構成 |
| `DATA_PRICE_005` | `tests/fixtures/price_m5_h1_h4_base.csv` | CSV | H1/H4 集約 |
| `DATA_EVENT_001` | `tests/fixtures/event_valid_utc.csv` | CSV | event 正常系 |
| `DATA_EVENT_002` | `tests/fixtures/event_invalid_row.csv` | CSV | event 破損行扱い |
| `STATE_001` | `tests/fixtures/state_entry_success.json` | JSON | `IDLE -> ENTRY_PENDING -> POSITION_OPEN` |
| `STATE_002` | `tests/fixtures/state_entry_timeout.json` | JSON | `ENTRY_PENDING -> IDLE` |
| `STATE_003` | `tests/fixtures/state_error_to_suspended.json` | JSON | `ERROR -> SUSPENDED` |
| `LTF_MAIN_001` | `tests/fixtures/ltf_third_wave_break_long.csv` | CSV | `third_wave_break` 正常系 |
| `LTF_MAIN_002` | `tests/fixtures/ltf_pattern_conflict.csv` | CSV | 競合ケース安全側 |
| `LTF_EXP_001` | `tests/fixtures/ltf_triangle_break_long.csv` | CSV | `triangle_break` 実験系 |

### 10.2 fixture の最低方針
- market data fixture は UTF-8 CSV を基本とする
- state fixture は JSON のイベント列を基本とする
- timestamp は ISO 8601 UTC 文字列で保存する
- fixture 名は対象レイヤと主ケースが読めること
- 1 fixture 1主目的を原則とする

---

## 11. 初期段階の優先順位

### 優先度高
- Data の整合性
- HTFContext の下位部品
- LTFStructure の初期構造認識部品
- Signal → RiskFilter → Execution の基本接続
- StateTransitionManager
- EventFilter
- SpreadFilter

### 優先度中
- Logger の追跡可能性
- Evaluator の基本集計
- experiments 比較基盤

### 優先度低
- 高度な補助AI前提の検証
- 複雑な比較分析自動化

### 11.1 初期版の合否基準
- unit test:
  - 期待する enum / bool / state が完全一致すること
  - 契約違反でない限り、unexpected exception を出さないこと
  - `*_reason` が必要なケースで空にならないこと
- integration test:
  - 必須変数が欠落しないこと
  - 命名が `docs/05` と一致すること
  - main と experiments の境界が崩れないこと
- scenario test:
  - 期待状態遷移列が完全一致すること
  - 禁止遷移が発生しないこと
  - 競合ケースが安全側の見送りになること

### 11.2 最初の具体ケース
#### Data
- `DATA_001`:
  - fixture: `DATA_PRICE_001`
  - scope: unit
  - expected: `data_valid_flag = true`、`validation_reason = ""`
- `DATA_002`:
  - fixture: `DATA_PRICE_002`
  - scope: unit
  - expected: `data_valid_flag = false`、`validation_reason` に逆順理由が残る
- `DATA_003`:
  - fixture: `DATA_PRICE_003`
  - scope: unit
  - expected: `spread` 欠損が `docs/11` の fallback ルールで扱われる

#### State
- `STATE_CASE_001`:
  - fixture: `STATE_001`
  - scope: scenario
  - expected: `IDLE -> ENTRY_PENDING -> POSITION_OPEN`
- `STATE_CASE_002`:
  - fixture: `STATE_002`
  - scope: scenario
  - expected: `ENTRY_PENDING -> IDLE`、自動再発注なし
- `STATE_CASE_003`:
  - fixture: `STATE_003`
  - scope: scenario
  - expected: `ERROR -> SUSPENDED`、通常売買停止

#### `third_wave_break`
- `TWB_CASE_001`:
  - fixture: `LTF_MAIN_001`
  - scope: integration
  - expected: `structure_type = third_wave_break`、`structure_direction = long`、`structure_candidate = true`
- `TWB_CASE_002`:
  - fixture: `LTF_MAIN_002`
  - scope: integration
  - expected: `structure_type = none`、`structure_direction = neutral`、`structure_candidate = false`

---

## 12. 未確定として隔離するもの
- pytest を初期版の基本とした上での最終統一タイミング
- 実験採用基準の数値閾値
- 高度なパフォーマンスベンチマーク

## 13. 初期段階のパターン採用方針

### 13.1 目的
初期段階では、複数の裁量パターンを同時に main 系へ投入すると、
原因切り分け、裁量一致確認、テストケース整理が難しくなる。

そのため、本システムでは初期段階の main 系において、
売買構造パターンを段階的に導入する。

### 13.2 初期 main の対象
初期 main では `third_wave_break` を優先対象とする。

`triangle_break` は初期段階では `experiments` 領域で先に検証し、
本体への統合は後段で行う。

### 13.3 方針
初期段階では以下の順で進める。

1. `third_wave_break` のみで Data から Logger までの基本フローを完成させる
2. 状態遷移、停止条件、理由ログの追跡可能性を確認する
3. その後に `triangle_break` を experiments で追加する
4. 採用時に競合解決規則を明示したうえで本体へ統合する

### 13.4 競合ケースの扱い
複数パターンが同時に成立した場合の扱いは、明示的に定義しない限り曖昧にしない。

初期段階では安全側の扱いとして、以下を推奨する。
- `structure_candidate = false`
- `structure_type = none`
- `structure_direction = neutral`
- `entry_signal = false`
- `signal_type = none`
- `pattern_reason` に競合理由を残す

### 13.5 テスト観点
初期段階の LTFStructure および Signal のテストでは、以下を分けて確認する。

- 第三波のみ成立するケース
- 持ち合いのみ成立するケース（`experiments`）
- どちらも成立しないケース
- 両方が成立しそうな競合ケース

### 13.6 補足
初期 main では「パターン種類を増やすこと」よりも、
「1つのパターンで end-to-end の挙動と追跡可能性を成立させること」を優先する。

## 14. 初期ゴールドケース一覧（具体例）

本節のゴールドケースは、初期段階の main / experiments における挙動評価を固定するためのものである。
利益評価や採用判断は本節と分離して扱う。

### 14.1 main v0 対象
- 対象パターン: `third_wave_break`
- `triangle_break` は `experiments` で先行検証する

### 14.2 ゴールドケース表

| case_id | phase | 相場説明 | expected_structure_type | expected_structure_direction | expected_entry_signal | expected_signal_type | expected_trade_ok | expected_state_transition | expected_pattern_reason | expected_filter_reason | 備考 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| TW_001 | main | 1時間足上昇、5分足第三波候補、直近高値突破、4時間足抵抗近接なし、spread正常、指標なし | third_wave_break | long | true | long_entry | true | IDLE -> ENTRY_PENDING -> POSITION_OPEN | 第三波候補で直近高値突破 |  | 初期正常系 |
| TW_002 | main | 第三波候補だが 1時間足方向が不一致 | third_wave_break | long | false | none | false | IDLE 維持 | 第三波候補で直近高値突破 | 上位足方向不一致 | Signal 見送り確認 |
| TW_003 | main | 第三波候補、上位足整合あり、ただし spread 超過 | third_wave_break | long | true | long_entry | false | IDLE 維持 | 第三波候補で直近高値突破 | spread超過 | RiskFilter 停止確認 |
| TW_004 | main | 第三波候補、上位足整合あり、ただし指標前 | third_wave_break | long | true | long_entry | false | IDLE -> SUSPENDED | 第三波候補で直近高値突破 | 指標前 | EventFilter 停止確認 |
| ST_001 | main | `ENTRY_PENDING` 中に再度 entry 条件が成立 | third_wave_break | long | true | long_entry | true | ENTRY_PENDING 維持 | 第三波候補で直近高値突破 |  | 再発注禁止確認 |
| ST_002 | main | `POSITION_OPEN` 中に新規 entry 条件が再成立 | third_wave_break | long | true | long_entry | true | POSITION_OPEN 維持 | 第三波候補で直近高値突破 |  | 新規エントリー禁止確認 |
| TRI_001 | experiments | 三角持ち合い収縮後の上抜け、上位足上昇、spread正常 | triangle_break | long | true | long_entry | true | IDLE -> ENTRY_PENDING -> POSITION_OPEN | 三角持ち合い離脱 |  | 実験系の正常ケース |
| MIX_001 | experiments | 第三波系にも見え、持ち合い離脱にも見える競合局面 | none | neutral | false | none | false | IDLE 維持 | 複数パターン競合 | 構造競合のため見送り | 初期は安全側 |

### 14.3 ゴールドケースと fixture 対応
| case_id | fixture_id | 主対象 | 最低限の確認項目 |
|---|---|---|---|
| `TW_001` | `LTF_MAIN_001` | main | `third_wave_break` long 成立、`trade_ok = true`、`IDLE -> ENTRY_PENDING -> POSITION_OPEN` |
| `TW_002` | `LTF_MAIN_001` + HTF 不一致条件 | main | `entry_signal = false`、`signal_type = none` |
| `TW_003` | `LTF_MAIN_001` + spread 超過条件 | main | `trade_ok = false`、`filter_reason = spread超過` |
| `TW_004` | `LTF_MAIN_001` + event 近接条件 | main | `IDLE -> SUSPENDED`、`filter_reason = 指標前` |
| `ST_001` | `STATE_001` 変形 | main | `ENTRY_PENDING` 中の再発注禁止 |
| `ST_002` | `STATE_001` 変形 | main | `POSITION_OPEN` 中の新規 entry 無視 |
| `TRI_001` | `LTF_EXP_001` | experiments | `triangle_break` の実験系正常動作 |
| `MIX_001` | `LTF_MAIN_002` | experiments | 競合時に安全側見送り |

## 15. 受入基準（要件対応表）

### 15.1 目的
本節では、`docs/02_requirements.md` に定義した機能要件（FR）および非機能要件（NFR）について、
初期段階でどのように受け入れ判定を行うかを整理する。

ここでの目的は以下とする。

- 要件とテストの対応関係を明示する
- 実装完了時に「どこまでできていれば合格か」を曖昧にしない
- main と experiments の境界を保ちながら段階的に受け入れを進める
- docs ベースで他者や別 agent でも進捗確認できる状態にする

### 15.2 受入判定の基本ルール
初期段階の受入判定は、以下を基本とする。

- Must 要件:
  - 初期版で満たされていなければ未完成とする
- Should 要件:
  - 初期版で満たせれば望ましいが、未達でも main の最小成立を妨げない
- Could 要件:
  - 将来拡張扱いとし、初期版の受入必須条件にはしない

また、受入判定は以下のいずれかの形で行う。

- unit test の合格
- integration test の合格
- scenario test の合格
- ログ出力の確認
- docs 上の設計整合確認
- experiments での比較可能性確認

---

### 15.3 機能要件の受入基準

| ID | 優先度 | 受入基準 | 主な確認方法 |
|---|---|---|---|
| FR-01 | Must | 価格データを読み込み、`timestamp/open/high/low/close/spread/volume` を後続へ渡せること | unit / integration |
| FR-02 | Must | イベントデータを読み込み、`event_time/event_flag/event_type` を生成できること | unit / integration |
| FR-03 | Must | 5分足・1時間足・4時間足を扱えること | integration |
| FR-04 | Must | 欠損、型不正、逆順、異常値を検出し、継続可能時は理由付きで返せること | unit |
| FR-05 | Must | 下位足が未来の上位足を参照しないこと | contract test / integration |
| FR-06 | Must | 上位足方向を `up/down/neutral` 等の定義済み値で返せること | unit |
| FR-07 | Must | 上位足の抵抗・支持・余地を判定できること | unit / integration |
| FR-08 | Must | 執行足でスイング、ブレイク、波動段階を判定できること | unit |
| FR-09 | Must | 初期 main で `third_wave_break` を正式対象として扱えること | integration / scenario |
| FR-10 | Should | `triangle_break` など追加構造を `experiments` 側で分離して検証できること | experiments |
| FR-11 | Must | 上位足環境と執行足構造を統合し、`entry_signal/exit_signal/signal_type` を生成できること | integration |
| FR-12 | Must | 上位足方向と構造方向の不一致時に見送り判定できること | integration / scenario |
| FR-13 | Must | 許容パターンのみを通し、非採用パターンを main へ混在させないこと | integration |
| FR-14 | Must | `trade_ok` を最終取引可否として返せること | integration |
| FR-15 | Must | 指標前後で新規取引停止できること | unit / scenario |
| FR-16 | Must | spread 異常時に新規取引停止できること | unit / scenario |
| FR-17 | Must | 当日回数制限・連敗停止を判定できること | unit / scenario |
| FR-18 | Must | 損切りが方向と矛盾しない位置に設定されること | unit |
| FR-19 | Must | 利確が方向と矛盾しない位置に設定されること | unit |
| FR-20 | Must | ロットが 0 より大きく broker 制約に適合すること | unit |
| FR-21 | Must | 発注要求に必要項目が揃うこと | unit |
| FR-22 | Must | 注文送信結果を取得し、黙って成功扱いしないこと | unit / integration |
| FR-23 | Must | 約定・拒否・取消・失敗を区別して扱えること | unit / integration |
| FR-24 | Must | `IDLE/ENTRY_PENDING/POSITION_OPEN/EXIT_PENDING/SUSPENDED/ERROR` を管理できること | scenario |
| FR-25 | Must | 不正遷移が拒否または安全側遷移されること | scenario |
| FR-26 | Must | `ENTRY_PENDING` 中および `POSITION_OPEN` 中に通常の新規エントリーを禁止できること | scenario |
| FR-27 | Must | 停止条件・異常条件で `SUSPENDED` または `ERROR` に遷移できること | scenario |
| FR-28 | Must | `htf_context_reason/pattern_reason/signal_reason/risk_reason/filter_reason/execution_reason` を残せること | logging test |
| FR-29 | Must | 注文結果、約定価格、損益、識別情報を記録できること | logging test |
| FR-30 | Must | `previous_state/next_state/transition_reason` を記録できること | logging test / scenario |
| FR-31 | Should | `trade_count/win_rate/average_pnl/profit_factor/max_drawdown` を算出できること | unit / integration |
| FR-32 | Should | 構造別・フィルター別集計を出せること | integration |
| FR-33 | Could | 本体ロジックと experiments ロジックを比較可能な形式で評価できること | experiments |

---

### 15.4 非機能要件の受入基準

| ID | 優先度 | 受入基準 | 主な確認方法 |
|---|---|---|---|
| NFR-01 | Must | 各判断と停止理由をログから追跡できること | logging test / review |
| NFR-02 | Must | 修正対象が局所化され、巨大な条件式へ依存しないこと | docs review / code review |
| NFR-03 | Must | unit → integration → scenario の段階的テスト構造を維持していること | docs review |
| NFR-04 | Must | データ不整合や異常時に危険な通常売買へ進まないこと | scenario |
| NFR-05 | Must | 二重エントリー、停止中誤発注、異常時継続売買を防止できること | scenario |
| NFR-06 | Must | 上位モジュール・下位部品が責務分離され、過度に内部依存しないこと | docs review / code review |
| NFR-07 | Must | 新規パターンや補助部品を既存全体を書き換えずに追加できる構造であること | docs review |
| NFR-08 | Must | モジュール名・変数名・理由変数から役割を把握しやすいこと | docs review |
| NFR-09 | Must | 特定部品修正時に他部品への影響が限定されること | code review / change review |
| NFR-10 | Should | USDJPY 起点でも他商品へ広げやすい商品依存分離があること | docs review |
| NFR-11 | Must | docs を見れば別チャット・別 agent でも継続できること | docs review |
| NFR-12 | Must | 上流から下流への単方向データフローを維持していること | architecture review |
| NFR-13 | Must | 状態管理と売買判断が分離されていること | docs review / scenario |
| NFR-14 | Must | 状態遷移と判断経緯をログから復元できること | logging test |
| NFR-15 | Must | experiments が本体を直接汚染しないこと | repo structure review |
| NFR-16 | Must | 設計先行・段階実装・段階テストの開発手順に適合していること | process review |
| NFR-17 | Should | 第三者に対して設計意図を説明しやすいこと | portfolio review |
| NFR-18 | Must | 初期段階で売買中核がルールベースであること | docs review |
| NFR-19 | Could | 将来の補助AI差し込み余地が命名・構造上残っていること | docs review |
| NFR-20 | Must | 個人開発・段階的実装という制約の中で現実的に進行可能であること | process review |

---

### 15.5 初期版リリース受入条件
初期版の main を「受入可能」とみなす最低条件は、以下をすべて満たすこととする。

1. `third_wave_break` を用いた基本フローが Data から Logger まで end-to-end で通ること  
2. `IDLE -> ENTRY_PENDING -> POSITION_OPEN` および `POSITION_OPEN -> EXIT_PENDING -> IDLE` の主要状態遷移が成立すること  
3. `ENTRY_PENDING` 中の再発注禁止、`SUSPENDED` 中の通常取引禁止、異常時の安全側遷移が確認できること  
4. 指標停止および spread 停止が機能すること  
5. `*_reason` および状態遷移ログが追跡可能であること  
6. main と experiments の境界が崩れていないこと

### 15.6 未受入でも初期版を妨げないもの
以下は初期版の受入必須条件には含めない。

- `triangle_break` の本体統合
- 高度な比較分析自動化
- 補助AIの本格導入
- 本格運用インフラの作り込み
- 高度なパフォーマンスベンチマーク

### 15.7 運用ルール
受入基準を変更する場合は、以下を原則とする。

- 要件変更が先、テスト変更が後ではなく、両者の整合を同時に更新する
- main の受入条件を緩める変更は、理由を docs に残す
- experiments の成果を main に入れる場合は、FR / NFR / test plan の3点を更新する
