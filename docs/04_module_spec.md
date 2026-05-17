# モジュール仕様

## 1. 方針
本システムでは、責務の大枠を表す上位モジュールと、それを構成する下位部品を分けて設計する。

上位モジュールはシステム全体の流れを表し、下位部品は交換・修正・比較しやすい部品単位を表す。

これにより、以下を実現する。
- 可読性の向上
- 修正容易性の向上
- 高凝集・低結合
- 新規裁量パターンの追加容易性
- ボトムアップなテスト容易性

## 1.1 契約ベースの下位モジュール設計

本システムの下位モジュールは、役割説明だけでなく、入出力契約を明示する。

各下位モジュールでは、可能な限り以下を定義対象とする。
- 入力
- 事前条件
- 出力
- 事後条件
- 不変条件
- 異常時の扱い

### 1.1.1 目的
これにより、以下を実現する。
- 部品単体テストの明確化
- 差し替え時の破壊範囲縮小
- 将来の agent / 別チャットへの引き継ぎ容易化
- 暗黙前提の可視化
- 「壊れ方」の明示

### 1.1.2 設計上の補足
- 関数や部品名は、短さよりも役割の明確さを優先する
- 1部品1責務を原則とする
- パラメータ数は無理に減らさず、意味単位の context に束ねる
- 未来参照の可否は必ず明示する
- 判定不能や入力不正は、黙って通さず理由を返す

## 2. 上位モジュール一覧
本システムの上位モジュールは以下とする。

Data -> HTFContext -> LTFStructure -> Signal -> RiskFilter -> Execution -> Logger -> Evaluator

---

## 3. Data

### 3.1 上位モジュールとしての役割
複数時間足の価格データ、およびイベント時刻データを読み込み、後続モジュールで扱える形に整える。

### 3.2 下位部品候補
- PriceDataLoader
- EventDataLoader
- TimeframeAligner
- DataValidator

### 3.3 各下位モジュールの役割と契約

#### PriceDataLoader
- 役割:
  価格データを読み込み、後続で扱える基本形式に整える。
- 入力:
  - price_source
  - timeframe
  - loader_config
- 事前条件:
  - 読み込み元が存在する
  - 必須列対応規則が定義されている
  - timeframe が有効値である
- 出力:
  - timestamp
  - open
  - high
  - low
  - close
  - spread
  - volume
- 事後条件:
  - 必須列が揃う
  - timestamp が時刻として解釈できる
  - OHLC が数値として扱える
- 不変条件:
  - 売買判断を行わない
  - 外部の隠れた状態に依存しない
- 異常時の扱い:
  - 読み込み不能時は理由を返す

#### EventDataLoader
- 役割:
  指標時刻などのイベントデータを読み込む。
- 入力:
  - event_source
  - event_config
- 事前条件:
  - 読み込み元が存在する
  - event_time の解釈規則が定義されている
- 出力:
  - event_time
  - event_type
  - event_flag の生成に必要な元データ
- 事後条件:
  - event_time が時刻として扱える
  - event_type が定義済み分類に属する
- 不変条件:
  - 価格方向の判定を行わない
- 異常時の扱い:
  - 破損行は理由付きで除外、または failure とする

#### TimeframeAligner
- 役割:
  複数時間足の整合を取り、下位足から安全に参照できる形にする。
- 入力:
  - ltf_price_frame
  - htf_price_frame
  - align_config
- 事前条件:
  - 各時間足データが timestamp 昇順である
  - 時刻基準が統一されている
  - 上位足確定時刻ルールが定義されている
- 出力:
  - aligned_ltf_frame
  - aligned_htf_context_ref
  - align_reason
- 事後条件:
  - 各下位足バーは未来の上位足バーを参照しない
  - 出力件数は基準となる下位足件数と整合する
- 不変条件:
  - 未来参照禁止
  - 時刻丸め規則は一貫している
  - 売買判断を行わない
- 異常時の扱い:
  - 時刻不整合時は理由付きで失敗させる

#### DataValidator
- 役割:
  欠損、型、順序、異常値を確認する。
- 入力:
  - price_frame
  - event_frame
  - validation_config
- 事前条件:
  - 入力フレームが存在する
  - 必須列ルールが定義されている
- 出力:
  - data_valid_flag
  - validation_reason
  - validated_frame
- 事後条件:
  - timestamp は昇順である
  - 必須列欠損の有無が確定している
  - `high >= max(open, close)`
  - `low <= min(open, close)`
  - `high >= low`
  - `spread >= 0`
- 不変条件:
  - 検証処理は売買判断を行わない
  - 検証ルールは config と入力データにのみ依存する
- 異常時の扱い:
  - 検証失敗は例外にせず、`data_valid_flag = false` と `validation_reason` を返す
  - 例外は、入力契約違反または処理継続不能な障害に限定する
    - 必須列不足
    - 時刻列解釈不能
    - 読み込み元不存在
    - タイムフレーム指定不正

### 3.4 想定ファイル
- `price_loader.py`
- `event_loader.py`
- `timeframe_aligner.py`
- `validator.py`
- `types.py`

### 3.5 上位モジュールの出力
- timestamp
- open
- high
- low
- close
- spread
- volume
- event_time
- event_flag
- data_valid_flag
- validation_reason

### 3.6 データソース役割と受け入れ基準（初期版）
Data は `docs/11_data_source_policy.md` に従い、入力データの役割と採用可否を扱う。

- 年次 CSV: 一次ソース候補
- parquet: 正規化済み高速処理用
- pkl: 作業キャッシュ（正本にしない）

受け入れ判定には最低限 `spread`、`bid/ask`、`volume`、`timezone`、欠損、`H1/H4` 集約ルールを含める。

採用可否は用途別に判定する。
- 構造検証用
- バックテスト基準
- 実運用近似

---

## 4. HTFContext

### 4.1 上位モジュールとしての役割
1時間足・4時間足などの上位足を用いて、方向性・環境・余地を判定する。

### 4.2 下位部品候補
- TrendDetector
- ResistanceDetector
- SupportDetector
- ContextAssembler

### 4.3 各下位モジュールの役割と契約

#### TrendDetector
- 役割:
  上位足の方向と強さを判定する。
- 入力:
  - htf_price_frame
  - trend_config
- 事前条件:
  - 必要本数以上の上位足データが存在する
  - 判定ルールが定義されている
  - 入力データが検証済みである
- 出力:
  - htf_trend_dir
  - htf_trend_strength
  - trend_reason
- 事後条件:
  - `htf_trend_dir` は `up / down / neutral`
  - `htf_trend_strength` は定義済み範囲内
  - 判定不能時は neutral と理由を返す
- 不変条件:
  - 同一入力に対して決定的である
  - execution 状態や口座残高に依存しない

#### ResistanceDetector
- 役割:
  上方向の抵抗余地を判定する。
- 入力:
  - htf_price_frame
  - resistance_config
- 事前条件:
  - 上位足データが検証済みである
  - 判定基準が定義済みである
- 出力:
  - htf_resistance_ok
  - resistance_reason
- 事後条件:
  - `htf_resistance_ok` は bool
- 不変条件:
  - 抵抗判定は価格構造または定義済み特徴量にのみ依存する

#### SupportDetector
- 役割:
  下方向の支持・余地を判定する。
- 入力:
  - htf_price_frame
  - support_config
- 事前条件:
  - 上位足データが検証済みである
  - 判定基準が定義済みである
- 出力:
  - htf_support_ok
  - support_reason
- 事後条件:
  - `htf_support_ok` は bool
- 不変条件:
  - 支持判定は価格構造または定義済み特徴量にのみ依存する

#### ContextAssembler
- 役割:
  各判定結果をまとめ、上位足環境を表す出力に整える。
- 入力:
  - htf_trend_dir
  - htf_trend_strength
  - htf_resistance_ok
  - htf_support_ok
  - sub_reasons
- 事前条件:
  - 各下位判定が完了している
- 出力:
  - htf_bias
  - htf_context_reason
- 事後条件:
  - `htf_bias` は定義済み分類に属する
  - `htf_context_reason` は追跡可能な要約理由を持つ
- 不変条件:
  - 新しい裁量判断を持ち込まず、既存判定の統合に徹する

### 4.4 想定ファイル
- `trend_detector.py`
- `resistance_detector.py`
- `support_detector.py`
- `assembler.py`
- `types.py`

### 4.5 上位モジュールの出力
- htf_trend_dir
- htf_trend_strength
- htf_bias
- htf_resistance_ok
- htf_support_ok
- htf_context_reason

---

## 5. LTFStructure

### 5.1 上位モジュールとしての役割
5分足などの執行足を用いて、エントリー候補となる構造を認識する。

### 5.2 下位部品候補
- SwingExtractor
- WaveClassifier
- TriangleDetector
- BreakoutDetector
- StructureAssembler
- FailurePatternDetector
- FailureConfirmChecker
- ReversalSignalEvaluator

### 5.3 各下位モジュールの役割と契約

#### SwingExtractor
- 役割:
  高値安値やスイング点を抽出する。
- 入力:
  - ltf_price_frame
  - swing_config
- 事前条件:
  - LTF データが検証済みである
  - 因果版か非因果版かが定義済みである
  - スイング抽出ルールが定義済みである
- 出力:
  - swing_points
  - swing_reason
- 事後条件:
  - swing 点は timestamp 順に並ぶ
  - 各点は時刻、価格、種別を持つ
  - 種別は `high / low` のいずれか
- 不変条件:
  - causal 版では未来バーを参照しない
  - 因果版と非因果版を混在させない

#### WaveClassifier
- 役割:
  波動段階を分類する。
- 入力:
  - swing_points
  - wave_config
- 事前条件:
  - swing_points が時系列順である
  - 最低限必要な swing 数が揃っている
- 出力:
  - wave_phase
  - wave_direction
  - wave_reason
- 事後条件:
  - `wave_phase` は定義済み分類に属する
  - `wave_direction` は `long / short / neutral`
- 不変条件:
  - execution 状態や残高に依存しない
  - 同一入力に対して決定的である

#### TriangleDetector
- 役割:
  三角持ち合いなどの収縮構造を判定する。
- 入力:
  - ltf_price_frame
  - swing_points
  - triangle_config
- 事前条件:
  - swing_points が生成済みである
  - 判定対象本数と許容誤差が定義済みである
- 出力:
  - triangle_flag
  - triangle_direction_hint
  - triangle_reason
- 事後条件:
  - `triangle_flag` は bool
- 不変条件:
  - 構造認識に徹し、最終売買判断は行わない

#### BreakoutDetector
- 役割:
  高値安値突破や持ち合い離脱を判定する。
- 入力:
  - ltf_price_frame
  - swing_points
  - breakout_config
- 事前条件:
  - swing_points が最新時点まで更新済みである
  - 終値基準かヒゲ基準かが明示されている
- 出力:
  - breakout_flag
  - breakout_direction
  - breakout_level
  - breakout_reason（内部補助情報）
- 事後条件:
  - `breakout_flag` は bool
  - `breakout_direction` は `long / short / neutral`
  - `breakout_flag = true` のとき、内部補助情報としての `breakout_reason` は空でない
  - 上位モジュール境界での正式理由変数は `pattern_reason` を用いる
  - `breakout_flag = false` のとき `breakout_direction = neutral`
- 不変条件:
  - 同一バーに対して long / short を同時に true にしない
  - 未来バーを参照しない

#### StructureAssembler
- 役割:
  複数の構造認識結果をまとめ、構造候補出力に整える。
- 入力:
  - wave_phase
  - breakout_flag
  - breakout_direction
  - triangle_flag
  - sub_reasons
- 事前条件:
  - 下位判定が完了している
- 出力:
  - structure_type
  - structure_direction
  - pattern_reason
  - structure_candidate
- 事後条件:
  - `structure_type` は定義済み分類に属する
  - `structure_direction` は `long / short / neutral`
  - `structure_candidate` は bool
- 不変条件:
  - 新しい裁量ルールを追加せず、統合に徹する
  - 競合時の扱いを曖昧にしない

### 5.4 想定ファイル
- `swing_extractor.py`
- `wave_classifier.py`
- `triangle_detector.py`
- `breakout_detector.py`
- `assembler.py`
- `types.py`

### 5.5 初期段階の対象構造
初期段階の main では `third_wave_break` を優先対象とする。

`triangle_break` は `experiments` で先行検証し、main には初期段階で同時導入しない。

初期段階で main が扱う構造は以下とする。
- 第三波候補における高値・安値突破

`experiments` で先行検証する構造候補は以下とする。
- 三角持ち合いなどの収縮後の離脱

### 5.6 競合ケース方針
複数パターンが同一バーまたは同一判定窓で同時に成立しそうな場合、初期段階では安全側を優先する。

初期段階の推奨扱いは以下とする。
- `structure_candidate = false`
- `structure_type = none`
- `structure_direction = neutral`
- `pattern_reason` に競合理由を残す

競合解決規則が明文化されるまでは、`third_wave_break` と `triangle_break` を main で同時採用しない。

### 5.7 将来拡張方針
新たな裁量パターンを追加する場合は、既存ロジック全体を書き換えるのではなく、下位部品の追加・差し替えで対応できる構造を目指す。

将来的には、執行足の失敗検知や、執行足のブレイク/第三波進行が短時間で否定された場合の逆走拡大候補を検証する下位部品を追加する余地を残す。
候補例:
- FailurePatternDetector
- FailureConfirmChecker
- ReversalSignalEvaluator

### 5.8 上位モジュールの出力
- structure_type
- structure_direction
- breakout_flag
- wave_phase
- pattern_reason
- structure_candidate

### 5.9 Backtest/Pipeline 接続補足（temporal third_wave_break）
- `WaveClassifier` と `BreakoutDetector` の責務は従来どおり単時点の判定であり、各部品自体の責務を拡張しない。
- 一方、Backtest の `PipelineAdapter` では構造検証用途として `detector_chain_temporal` を扱い、`third` candidate と breakout を同一バー限定にせず、lookback 窓内で時間差接続できるようにする。
- この接続は `bars[:i+1]` の範囲だけで判定し、future leak を許容しない。
- 同一 `recent_third_timestamp` の再発火制御は PipelineAdapter 側設定（`max_entries_per_recent_third_candidate`）で扱い、LTFStructure 下位部品の責務には含めない。

---

## 6. Signal

### 6.1 上位モジュールとしての役割
上位足環境と執行足構造を統合し、売買候補を判定する。

### 6.2 下位部品候補
- DirectionAlignChecker
- PatternGate
- EntryRuleEngine
- ExitRuleEngine
- SignalAssembler

### 6.3 下位部品の役割
#### DirectionAlignChecker
上位足方向と執行足方向の整合を確認する。

#### PatternGate
利用する構造パターンごとの通過判定を行う。

#### EntryRuleEngine
エントリー候補を生成する。

#### ExitRuleEngine
イグジット候補を生成する。

補足（Backtest初期実装の扱い）:
- `src/backtest/exit_rule_engine.py` の現行 backtest exit は固定 `stop_loss` / 固定 `take_profit` / `max_holding_bars` 中心の初期方式である。
- trend-break exit（例: 押し安値割れ / 戻り高値超え / MA傾き反転 / swing構造崩壊）は、現時点では本体仕様ではなく将来の実験候補として扱う。
- これは構造検証段階の方針であり、収益性確認済みを意味しない。

#### SignalAssembler
各判定をまとめて signal 出力へ整える。

### 6.4 想定ファイル
- `direction_align_checker.py`
- `pattern_gate.py`
- `entry_rule_engine.py`
- `exit_rule_engine.py`
- `assembler.py`
- `types.py`

### 6.5 上位モジュールの出力
- entry_signal
- exit_signal
- signal_type
- signal_reason

---

## 7. RiskFilter

### 7.1 上位モジュールとしての役割
シグナルを受けて、取引可否、停止条件、ロット、損切り、利確を決定する。

### 7.2 下位部品候補
- EventFilter
- SpreadFilter
- TradeLimitFilter
- StopLossPlanner
- TakeProfitPlanner
- PositionSizer
- RiskAssembler
- ExternalEventIngestor
- OfficialReleaseFilter
- BreakingNewsRiskFilter

### 7.2.1 Risk/Stop v0 スコープ固定（docs整理段階）
- 本節の `Risk/Stop v0` は、`trade_ok`、`stop_loss`、`take_profit`、`risk_reason`、`filter_reason` の責務境界を固定するための docs 整理を対象とする。
- `entry_price`（または `entry_price_candidate`）、`signal_type`、`structure_type`、`spread`、`event_flag` を入力文脈として扱い、`max_holding_bars` は Backtest 側 exit 条件との接続前提として扱う。
- `fixed_sl_tp` baseline は `docs/17_backtest_design.md` の既定方針を維持し、今回の v0 はその既定を壊さない。
- 本節は実装変更を含まず、売買ロジック本体・Execution 本体・BacktestRunner 本体の挙動変更を行わない。
- `lot sizing` 本体（`PositionSizer` 詳細、残高連動、`risk_per_trade`、複利連動、broker lot制約の厳密化）は v0 対象外とし、後続で扱う。
- Risk/Stop v0 実装時は `PositionSizer placeholder` を許容し、`lot` を暫定固定値（または設定値）で返して `RiskFilter -> Execution` 契約を満たす。
- `PositionSizer placeholder` は資金管理最適化を目的としない。

### 7.3 各下位モジュールの役割と契約

#### EventFilter
- 役割:
  指標前後などのイベント停止判定を行う。
  将来的に、外部公式発表や経済カレンダー、速報ニュースなどの外部イベント入力を扱い、売買方向ではなく危険局面判定・停止閾値補正を担う余地を残す。
- 入力:
  - timestamp
  - event_time
  - event_type
  - event_filter_config
  - external_event_flag (将来候補)
  - external_event_reason (将来候補)
- 事前条件:
  - timestamp と event_time が同一時刻基準である
  - 停止窓が定義済みである
- 出力:
  - event_risk_flag
  - event_filter_reason
- 事後条件:
  - 停止対象なら `event_risk_flag = true`
- 不変条件:
  - 価格方向の判定を行わない

#### SpreadFilter
- 役割:
  spread 異常時の停止判定を行う。
- 入力:
  - spread
  - spread_filter_config
- 事前条件:
  - spread の単位が統一されている
  - 上限基準が定義済みである
- 出力:
  - spread_ok
  - spread_filter_reason
- 事後条件:
  - `spread_ok` は bool
- 不変条件:
  - 単位系を暗黙変換しない

#### TradeLimitFilter
- 役割:
  当日回数制限、連敗停止などを判定する。
- 入力:
  - daily_trade_count
  - losing_streak
  - trade_limit_config
- 事前条件:
  - 日次集計基準が定義済みである
  - 各カウンタが負値でない
- 出力:
  - limit_ok
  - limit_filter_reason
  - max_trade_reached_flag
- 事後条件:
  - 上限到達時は `max_trade_reached_flag = true`
- 不変条件:
  - カウンタ更新責務と判定責務を混在させない

#### StopLossPlanner
- 役割:
  損切り候補を決定する（Risk/Stop v0 では SL 決定責務の境界固定を主目的とする）。
- 入力:
  - entry_side
  - entry_price_candidate
  - ltf_price_frame
  - sl_config
- 事前条件:
  - entry_side が有効値である
  - 損切り決定方式が定義済みである
- 出力:
  - stop_loss
  - sl_reason
- 事後条件:
  - ロング時は `stop_loss < entry_price_candidate`
  - ショート時は `stop_loss > entry_price_candidate`
- 不変条件:
  - 方向と逆側に損切りを置かない
  - Risk/Stop v0 では `fixed_sl_tp` baseline と矛盾する決定を導入しない

#### TakeProfitPlanner
- 役割:
  利確候補を決定する（Risk/Stop v0 では TP 決定責務の境界固定を主目的とする）。
- 入力:
  - entry_side
  - entry_price_candidate
  - stop_loss
  - tp_config
- 事前条件:
  - entry_side が有効値である
  - 利確方式が定義済みである
- 出力:
  - take_profit
  - tp_reason
- 事後条件:
  - ロング時は `take_profit > entry_price_candidate`
  - ショート時は `take_profit < entry_price_candidate`
- 不変条件:
  - 利確方向を損切り方向と取り違えない
  - Risk/Stop v0 では `fixed_sl_tp` baseline と矛盾する決定を導入しない

#### PositionSizer
- 役割:
  ロットを決定する。
- Risk/Stop v0 での扱い:
  - `PositionSizer` の存在と I/O 境界を維持する。
  - 実装時は placeholder として固定lot（または設定値lot）を返す最小方式を許容する。
  - `lot sizing` 本体仕様（計算式、残高連動、`risk_per_trade`、broker 制約の厳密化）は後続で固定する。
- 入力:
  - account_balance
  - stop_loss
  - entry_price_candidate
  - risk_fraction
  - broker_rule
- 事前条件:
  - `account_balance > 0`
  - `risk_fraction > 0`
  - stop_loss と entry_price_candidate の差が 0 でない
  - broker の最小ロット、刻み値、上限が定義済みである
- 出力:
  - lot
  - size_reason
- 事後条件:
  - `lot > 0`
  - broker 制約に適合する
- 不変条件:
  - 単位系を混在させない

#### PositionSizer（Lot Sizing v1 フェーズ方針）
- `lot sizing` 本体は Risk/Stop v0 から分離し、独立フェーズ `Lot Sizing v1` で扱う。
- `Lot Sizing v1` 初期実装は `PositionSizer` 本線接続ではなく、isolated calculator（単体I/O + unit test）として導入する。
- `Lot Sizing v1` 初期の計算式は以下で固定する。
  - `lot = account_balance * risk_per_trade / (stop_loss_distance_pips * pip_value_per_lot)`
- 初期スコープは以下に限定する。
  - formula 固定（上式）
  - config固定（`account_balance`, `risk_per_trade`, `stop_loss_distance_pips`, `pip_value_per_lot`, `lot_step`, `min_lot`, `max_lot`, `rounding_mode`）
  - 出力固定（`lot`, `raw_lot`, `rounded_lot`, `clamped_flag`, `size_reason`）
  - invalid条件、rounding/clamp方針、reason token方針
- rounding方針（初期固定）:
  - `rounding_mode=floor` のみ対応（`round` / `ceil` は非対応）
  - 理由は「指定リスク超過を避けるため」
- clamp方針（初期固定）:
  - `raw_lot` または `rounded_lot` が `max_lot` を超える場合は `max_lot` へ clamp 可
  - `rounded_lot < min_lot` は `min_lot` へ引き上げず invalid とする
  - 理由は「`min_lot` 引き上げで指定リスク超過の可能性があるため」
- invalid条件（初期固定）:
  - `account_balance <= 0`
  - `risk_per_trade <= 0`
  - `risk_per_trade >= 1`
  - `stop_loss_distance_pips <= 0`
  - `pip_value_per_lot <= 0`
  - `lot_step <= 0`
  - `min_lot <= 0`
  - `max_lot <= 0`
  - `min_lot > max_lot`
  - bool / NaN / inf
  - `rounded_lot < min_lot`
- `PipelineAdapter` / backtest main path への接続は `Lot Sizing v1` 初期では行わず、後続判断とする。
- `fixed_lot` baseline は維持し、`PositionSizer placeholder` の現行責務は壊さない。

#### RiskAssembler
- 役割:
  各判定をまとめて取引可否・理由情報を整える。
  Risk/Stop v0 では `trade_ok` / `risk_reason` / `filter_reason` の追跡可能性固定を優先し、lot sizing 詳細決定には踏み込まない。
- 入力:
  - event_risk_flag
  - spread_ok
  - limit_ok
  - lot
  - stop_loss
  - take_profit
  - sub_reasons
- 事前条件:
  - 各下位判定が完了している
- 出力:
  - trade_ok
  - risk_reason
  - filter_reason
- 事後条件:
  - 停止条件が1つでも成立した場合、`trade_ok = false`
  - 実行可の場合、lot / stop_loss / take_profit が有効値である
- 不変条件:
  - 新規の裁量判断を追加せず、統合に徹する
  - `trade_ok=false` 時は `filter_reason` または `risk_reason` に停止根拠を残す
  - `trade_ok=true` 時は `lot` / `stop_loss` / `take_profit` が有効であることを前提に下流へ渡す
  - `lot` が未算出・空・`<=0`・不正値の場合は `trade_ok=true` を許容しない

### 7.4 想定ファイル
- `event_filter.py`
- `spread_filter.py`
- `trade_limit_filter.py`
- `stop_loss_planner.py`
- `take_profit_planner.py`
- `position_sizer.py`
- `assembler.py`
- `types.py`

### 7.5 上位モジュールの出力
- trade_ok
- lot
- stop_loss
- take_profit
- risk_reason
- filter_reason

---

## 8. Execution

### 8.1 上位モジュールとしての役割
注文実行、約定管理、状態更新を担当する。

### 8.2 下位部品候補
- OrderBuilder
- OrderSender
- FillHandler
- StateTransitionManager

### 8.3 各下位モジュールの役割と契約

#### OrderBuilder
- 役割:
  発注内容を組み立てる。
- 入力:
  - signal_type
  - lot
  - stop_loss
  - take_profit
  - execution_config
- 事前条件:
  - `trade_ok = true`
  - `signal_type` が定義済み値である
  - lot, stop_loss, take_profit が有効値である
- 出力:
  - order_request
  - order_build_reason
- 事後条件:
  - 発注要求に必須項目が揃う
- 不変条件:
  - 送信自体は行わない
  - 外部副作用を持たない

#### OrderSender
- 役割:
  注文を送信する。
- 入力:
  - order_request
  - broker_connection
- 事前条件:
  - order_request が妥当である
  - 接続が利用可能である
- 出力:
  - order_result
  - execution_reason
  - broker_response_raw
- 事後条件:
  - `order_result` は定義済み結果集合に属する
- 不変条件:
  - 送信結果を黙って成功扱いしない

#### FillHandler
- 役割:
  約定結果を処理する。
- 入力:
  - broker_response_raw
  - fill_handler_config
- 事前条件:
  - broker_response_raw が取得済みである
- 出力:
  - fill_price
  - execution_price
  - fill_reason
- 事後条件:
  - filled 時は価格情報が取得できる
  - rejected / cancelled 時は理由が残る
- 不変条件:
  - fill_price と execution_price の意味を曖昧にしない

#### StateTransitionManager
- 役割:
  状態遷移を管理する。
- 入力:
  - previous_state
  - transition_event
  - transition_context
- 事前条件:
  - `previous_state` が定義済み状態に属する
  - `transition_event` が定義済みイベントに属する
- 出力:
  - next_state
  - transition_reason
- 事後条件:
  - `06_state_spec.md` の許可遷移に従う
  - 不正遷移時は拒否または安全側遷移を行う
- 不変条件:
  - 状態遷移はこの部品を経由してのみ行う
  - 不正遷移を黙殺しない
  - `ENTRY_PENDING` 中の再発注禁止などの制約を破らない

### 8.4 想定ファイル
- `order_builder.py`
- `order_sender.py`
- `fill_handler.py`
- `state_transition_manager.py`
- `types.py`

### 8.5 上位モジュールの出力
- order_result
- fill_price
- execution_price
- position_state
- execution_reason

---

## 9. Logger

### 9.1 上位モジュールとしての役割
判断理由、状態、注文結果、損益などを記録する。
ログ集合は `decision_logs`、`trade_logs`、`event_logs`、`state_logs` を分離して扱う。

### 9.2 下位部品候補
- DecisionLogger
- TradeLogger
- StateLogger
- EventLogger

### 9.3 下位部品の役割
#### DecisionLogger
判断理由を記録する。

#### TradeLogger
取引結果や損益を記録する。

#### StateLogger
状態遷移を `state_logs` として記録する。

#### EventLogger
停止・見送り・イベント情報を `event_logs` として記録する（状態遷移は含めない）。

### 9.4 想定ファイル
- `decision_logger.py`
- `trade_logger.py`
- `state_logger.py`
- `event_logger.py`
- `types.py`

### 9.5 上位モジュールの出力
- trade_logs
- event_logs
- decision_logs
- state_logs

---

## 10. Evaluator

### 10.1 上位モジュールとしての役割
ログや損益情報をもとに、成績評価や改善対象の整理を行う。
初期版では、基本成績指標と分析補助指標を少数に絞って算出し、全期間・月次・構造種別単位で比較可能な形にまとめる。

### 10.2 下位部品候補
- MetricsCalculator
- StructureAnalyzer
- FilterAnalyzer
- ReportAssembler

### 10.3 下位部品の役割
#### MetricsCalculator
基本指標を計算する。

#### StructureAnalyzer
構造ごとの成績を分析する。

#### FilterAnalyzer
どのフィルターがどれだけ効いたかを分析する。

#### ReportAssembler
結果をまとめてレポートに整える。

### 10.4 想定ファイル
- `metrics_calculator.py`
- `structure_analyzer.py`
- `filter_analyzer.py`
- `report_assembler.py`
- `types.py`

### 10.5 上位モジュールの出力
- trade_count
- win_rate
- average_pnl
- profit_factor
- max_drawdown
- structure_type_stats
- filter_hit_stats
- signal_type_stats
- summary_report

補足:
- 初期版の比較軸は `structure_type`、`signal_type`、`filter_reason`（必要に応じて `event_type`）
- 初期段階ではシャープレシオ等の高度指標は扱わない

---

## 11. Experiments

### 11.1 上位モジュールとしての役割
本体未採用の新規裁量パターンや補助ロジックを、既存本体から分離して試作・比較する。

### 11.2 方針
実験対象は、最初から本体へ直接混ぜず、比較・記録・レビューを経て採用判断を行う。

### 11.3 想定ファイル
- `README.md`
- 必要に応じて個別実験ファイルやサブフォルダを追加する

---

## 12. 共通設計原則

### 12.1 上位モジュールは流れを表す
上位モジュールはシステム全体の責務のまとまりを表す。

### 12.2 下位部品は交換可能な部品とする
下位部品は、できるだけ単一責務に近づけ、局所的な差し替えや追加ができるようにする。

### 12.3 組み立て処理を独立させる
複数の判定結果をまとめる役割は `assembler` 系に集約し、判定処理と混在させない。

### 12.4 下位部品の内部実装に依存しすぎない
上位モジュールや他モジュールは、下位部品の内部実装ではなく、出力インターフェースに依存するようにする。

### 12.5 新規裁量知見は部品として追加する
新しい裁量パターンは、巨大な条件式へ追記するのではなく、新たな判定部品として追加しやすい構造を目指す。
