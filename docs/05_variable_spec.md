# 変数仕様

## 1. 方針
本ドキュメントでは、本システムにおける主要変数の意味と役割を整理する。

ここで扱うのは、実装上必要になるすべての細かい変数ではなく、設計上重要な骨格変数である。
特に以下を明確にすることを目的とする。
- どのモジュールで生成されるか
- 何を意味するか
- どこで利用されるか

## 2. 基本方針

### 2.1 命名の考え方
変数名は、できるだけ以下が分かるようにする。
- どの層の情報か
- 何を意味するか
- flag なのか state なのか reason なのか

### 2.2 接尾辞の使い方
- `_flag`: 真偽判定
- `_state`: 状態
- `_reason`: 理由・説明
- `_dir`: 方向
- `_strength`: 強さ
- `_type`: 種類
- `_count`: 回数
- `_price`: 価格
- `_time`: 時刻

### 2.3 接頭辞の使い方
- `htf_`: 上位足関連
- `ltf_`: 執行足関連
- `event_`: 指標・イベント関連
- `entry_`: エントリー関連
- `exit_`: イグジット関連

### 2.4 契約属性
主要変数については、意味だけでなく以下も定義対象とする。

- 型
- 取りうる値または値域
- 単位
- nullable 可否
- 生成モジュール
- 主な利用モジュール

特に、価格、ロット、時刻、方向、状態、flag 系の変数は、曖昧運用を避ける。

### 2.5 初期版の基準固定
- `timestamp`、`event_time`、`log_time` は timezone-aware な UTC datetime とする
- 時刻のシリアライズは ISO 8601 UTC（例: `2026-04-06T00:00:00Z`）を最低基準とする
- `open`、`high`、`low`、`close`、`entry_price`、`stop_loss`、`take_profit`、`fill_price`、`execution_price` は raw price とする
- `spread` は pips 単位の float とする
- `lot` は lot 単位の float とする
- bool 系は `true / false` のみを取り、null を使わない
- 理由変数は string とし、未成立時は null ではなく空文字を基本とする

### 2.6 初期版の正式 enum 集合
- `event_type`: `cpi / nfp / policy_rate / other`
- `htf_trend_dir`: `up / down / neutral`
- `htf_bias`: `long_bias / short_bias / neutral`
- `structure_type`: `third_wave_break / triangle_break / none`
  - 初期 main では `third_wave_break / none` を対象とし、`triangle_break` は `experiments` 先行とする
- `structure_direction`: `long / short / neutral`
- `wave_phase`: `first / second / third / unknown`
- `signal_type`: `long_entry / short_entry / exit / none`
- `order_result`: `filled / rejected / cancelled / failed / none`
- `position_state`: `IDLE / ENTRY_PENDING / POSITION_OPEN / EXIT_PENDING / SUSPENDED / ERROR`

## 3. Data で扱う主要変数

### 3.1 価格データ
- `timestamp`
  - 各バーの時刻
  - 後続の全モジュールで利用する

- `open`
- `high`
- `low`
- `close`
  - 各バーのOHLC

- `spread`
  - スプレッド情報
  - RiskFilter で利用する

- `volume`
  - 出来高またはティックボリューム
  - 必要に応じて利用する

### 3.2 イベントデータ
- `event_time`
  - 指標発表などのイベント時刻

- `event_flag`
  - 当該バーまたは周辺時刻がイベント対象かどうか

- `event_type`
  - イベントの種類
  - 例: 雇用統計、CPI、政策金利など

### 3.3 検証結果
- `data_valid_flag`
  - Data の検証結果（有効/無効）
  - `false` の場合は後続モジュールへ進まない

- `validation_reason`
  - `data_valid_flag = false` の理由
  - 検証NG理由を追跡するために保持する

## 4. HTFContext で扱う主要変数

### 4.1 上位足方向
- `htf_trend_dir`
  - 上位足の方向
  - 例: up / down / neutral

- `htf_trend_strength`
  - 上位足トレンドの強さ
  - 数値または段階評価を想定する

- `htf_bias`
  - 上位足全体としての売買バイアス
  - 買い寄り、売り寄り、様子見などを表す

### 4.2 上位足余地・障害
- `htf_resistance_ok`
  - 上方向に近い抵抗がなく、買い余地があるか

- `htf_support_ok`
  - 下方向に近い支持・抵抗の状況から、売り余地があるか

- `htf_context_reason`
  - 上位足判定の理由
  - 例: 「1時間足上昇トレンド」「4時間足抵抗近接なし」

## 5. LTFStructure で扱う主要変数

### 5.1 執行足構造
- `structure_type`
  - 認識した構造の種類
  - 例: third_wave_break / triangle_break / none
  - 初期 main の正式対象は `third_wave_break`

- `structure_direction`
  - 構造が示す方向
  - 例: long / short / neutral

- `structure_candidate`
  - エントリー候補となる構造が存在するかどうか

### 5.2 ブレイク・波動関連
- `breakout_flag`
  - 直近高値・安値などのブレイクが発生したか

- `wave_phase`
  - 波動の進行段階
  - 例: first / second / third / unknown

- `pattern_reason`
  - 執行足構造判定の理由
  - 公開契約・SoT・ログ上の正式理由変数として扱う
  - 例: 「第三波候補で直近高値突破」「三角持ち合い離脱」
  - 補足: `breakout_reason` は BreakoutDetector 内で必要な場合のみ使う内部補助情報であり、モジュール境界・SoT・Logger の正式変数としては扱わない

### 5.3 失敗検知・逆走関連（将来候補）
- `failure_setup_flag`
  - 執行足で失敗セットアップが判断されたか
- `failure_type`
  - 失敗の種類（false_breakout / trap / failed_breakout など）
- `failure_confirm_flag`
  - 失敗が一定基準で確定したか
- `failure_confirm_time`
  - 失敗確定の時刻
- `reversal_move_size`
  - 失敗後の逆走幅
- `reversal_move_atr_norm`
  - 逆走幅を ATR 正規化した値
- `trap_direction`
  - 罠・トラップと判断された方向
- `trap_entry_signal`
  - 罠成立後にエントリーが発生したかどうか
- `trap_reason`
  - 逆走・トラップ判定の理由

## 6. Signal で扱う主要変数

### 6.1 売買候補
- `entry_signal`
  - エントリー候補が成立しているか

- `exit_signal`
  - イグジット候補が成立しているか

- `signal_type`
  - シグナルの種類
  - 例: long_entry / short_entry / exit / none

- `signal_reason`
  - シグナル成立理由
  - 例: 「上位足上昇 + 5分足第三波突破 + 抵抗余地あり」

### 6.2 補足的に扱う可能性がある変数
- `entry_priority`
  - 複数候補がある場合の優先度
  - 初期段階の main では正式出力に含めない

## 7. RiskFilter で扱う主要変数

### 7.1 取引可否
- `trade_ok`
  - 実際に取引してよいかどうか
  - Risk/Stop v0 では最終可否フラグとして固定し、`false` 時は理由追跡を必須とする

- `filter_reason`
  - 取引停止または見送り理由
  - 例: 「指標前」「spread超過」「回数上限到達」
  - Risk/Stop v0 では `trade_ok=false` の根拠記録に使用する

### 7.2 リスク管理
- `lot`
  - 発注ロット数
  - Risk/Stop v0 では契約上の変数として維持するが、lot sizing 詳細仕様は後続で固定する
  - `trade_ok=true` の場合は有効値（未算出・空・`<=0`・不正値でない）でなければならない
  - `Lot Sizing v1` 初期は isolated calculator で I/O を先に固定し、`PipelineAdapter` 本線接続は後続判断とする
  - `fixed_lot` baseline は維持し、`PositionSizer` placeholder の現行出力契約を直ちに置換しない
  - `Lot Sizing v1` 初期では `raw_lot`（式計算値）・`rounded_lot`（floor適用値）・`lot`（最終採用値）を区別して扱う
  - 最終 `lot` は `max_lot` clamp を許容するが、`min_lot` 未満は引き上げず invalid とする

- `raw_lot`
  - `Lot Sizing v1` isolated calculator の中間出力
  - 基本式: `account_balance * risk_per_trade / (stop_loss_distance_pips * pip_value_per_lot)`
  - 0以下/不正値は invalid

- `rounded_lot`
  - `Lot Sizing v1` isolated calculator の中間出力
  - `raw_lot` を `lot_step` で floor 丸めした値
  - `round` / `ceil` は初期非対応

- `clamped_flag`
  - `Lot Sizing v1` isolated calculator の補助出力
  - `max_lot` clamp が発生した場合のみ `true`

- `rounding_mode`
  - `Lot Sizing v1` config 入力
  - 初期は `floor` のみ有効値

- `stop_loss`
  - 損切り価格または損切り幅
  - Risk/Stop v0 の主対象（SL 決定責務）

- `take_profit`
  - 利確価格または利確幅
  - Risk/Stop v0 の主対象（TP 決定責務）

- `risk_reason`
  - リスク設定理由
  - 例: 「ATR基準でSL設定」「当日回数制限内」
  - Risk/Stop v0 では `trade_ok=true/false` の両ケースで追跡可能性を維持する

### 7.2.1 Risk/Stop v0 の理由文字列（推奨トークン例）
- 方針:
  - v0 では `risk_reason` / `filter_reason` を自由文字列のまま維持する。
  - 以下は実装・テスト追跡を容易にする推奨トークン例であり、正式 enum ではない。
- `risk_reason` 推奨例:
  - `fixed_sl_tp`
  - `placeholder_fixed_lot`
  - `invalid_stop_loss`
  - `invalid_take_profit`
  - `invalid_lot`
- `filter_reason` 推奨例:
  - `spread_too_wide`
  - `event_risk`
  - `trade_limit_reached`
  - `risk_contract_invalid`

### 7.2.2 Reason語彙の管理方針（2026-05-15）
- 結論（Phase 9直後）:
  - `risk_reason` / `filter_reason` は **enum化しない**。
  - **Reason Catalog（固定文字列カタログ）+ 定数運用**を採用する（Option B）。
  - 補助的に、将来の拡張理由文を許容するため `category_token[:detail]` 形式を許容する（Option Cの一部）。
- 採用理由:
  - 現行実装・テスト・既存ログは文字列前提で運用中であり、即時enum化は差分影響が大きい。
  - 一方で完全自由文のままだと集計軸が不安定になるため、集計用の管理語彙は固定する。
- 運用ルール:
  - `risk_reason` / `filter_reason` は「集計可能な管理語彙」を優先する。
  - 既存トークンは後方互換のため維持し、急な一括置換は行わない。
  - 必要なら詳細は `:` 以降に追記してよい（例: `risk_contract_invalid: non_entry_signal_type=none`）。
  - 主要集計軸は `:` より前のトークン（category）を使用する。
  - 互換保証の主対象は category token であり、detail 完全一致は保証対象外とする。
  - detail は段階移行対象とし、新旧detailが混在しうる。
  - 集計・分析では reason 文字列の完全一致比較ではなく、`normalize_reason_category` による category 抽出を推奨する。
  - `normalize_reason_category()` は単一reason向けとする。
  - `|` 連結reasonには `normalize_reason_categories()` を使い、category list として扱う。
  - 複数reasonの集計・分析では、文字列完全一致ではなく category list を使用する。
- 境界（自由文との分離）:
  - `risk_reason` / `filter_reason`: 管理語彙（カタログ対象、集計主軸）。
  - `decision_reason` / `signal_reason` / `pattern_reason` / `htf_context_reason`: 説明用自由文（人間向けトレース主軸）。
- 現時点のカタログ最小集合（v0）:
  - `risk_reason`: `fixed_sl_tp`, `placeholder_fixed_lot`, `invalid_lot`, `invalid_stop_loss`, `invalid_take_profit`, `risk_contract_invalid`
  - `filter_reason`: `all_risk_filters_passed`, `event_risk`, `spread_too_wide`, `trade_limit_reached`, `risk_contract_invalid`
- 表記互換:
  - 現行の `"all risk filters passed"` は後方互換のため当面許容し、将来 `all_risk_filters_passed` へ段階移行する。

### 7.3 外部イベント関連（将来候補）
- `scheduled_event_flag`
  - 指標・予定イベントが近いか
- `official_release_flag`
  - 公式発表が検出されたか
- `breaking_news_flag`
  - 速報ニュースが検出されたか
- `source_reliability`
  - 外部イベントソースの信頼度
- `event_severity`
  - イベントの重大度評価
- `external_event_reason`
  - 外部イベント判定理由
- `sns_risk_flag`
  - SNS/X 系のリスク候補フラグ
- `sns_volume_spike_flag`
  - SNS/X 系の話題急増を示すフラグ

### 7.4 運用制約
- `daily_trade_count`
  - 当日取引回数

- `losing_streak`
  - 連敗数

- `account_balance`
  - 口座残高

- `max_trade_reached_flag`
  - 当日上限回数に達したか

- `event_risk_flag`
  - イベント近接により停止すべきか

## 8. Execution で扱う主要変数

### 8.1 注文結果
- `order_result`
  - 注文の結果
  - 例: filled / rejected / cancelled / none

- `fill_price`
  - 約定価格

- `execution_price`
  - 実際の執行価格
  - fill_price と同義で扱う場合は統一する

- `execution_reason`
  - 実行結果の説明
  - 例: 「正常約定」「スリッページ発生」「発注拒否」

### 8.2 ポジション関連
- `entry_price`
  - エントリー価格

### 8.3 `entry_price_candidate` と `entry_price`（Risk/Stop v0 文脈）
- `entry_price_candidate`:
  - RiskFilter が受け取る Execution 前の候補価格として扱う（Risk/Stop v0 の優先語）。
- `entry_price`:
  - Execution 後に確定したエントリー価格として扱う。
- 補足:
  - 既存記述の `entry_price` を即時全置換はしない。
  - v0 では文脈混同を避けるため、候補価格は `entry_price_candidate` を優先して記述する。

- `position_size`
  - 保有数量

- `position_state`
  - 現在のポジション状態
  - 詳細は state_spec で定義する

## 9. Logger で扱う主要変数

### 9.1 記録対象
- `htf_context_reason`
- `pattern_reason`
- `signal_reason`
- `risk_reason`
- `filter_reason`
- `execution_reason`

これらは「なぜそう判断したか」を追跡するための主要記録対象である。

### 9.2 損益関連
- `pnl`
  - 損益

- `realized_pnl`
  - 実現損益

- `unrealized_pnl`
  - 未実現損益

### 9.3 記録用補助
- `log_time`
  - ログ記録時刻

- `trade_id`
  - 取引識別子
  - 後で各記録を紐づけるために使用する可能性がある

### 9.4 `state_logs` の正式記録対象
- `position_state`
- `previous_state`
- `next_state`
- `transition_reason`
- `order_result`
- `execution_reason`
- `log_time`

状態遷移関連は `state_logs` を正式対象とし、`event_logs` には混在させない。

## 10. Evaluator で扱う主要変数

### 10.1 基本成績指標（正式）
- `trade_count`
- `win_rate`
- `average_pnl`
- `profit_factor`
- `max_drawdown`

### 10.2 分析補助指標（正式）
- `structure_type_stats`
  - 構造ごとの成績

- `filter_hit_stats`
  - どのフィルターで何回停止したか

- `signal_type_stats`
  - シグナル種別ごとの成績

### 10.3 初期版で扱う期間単位
- 全期間
- 月次
- 構造種別ごとの集計単位

### 10.4 初期版で扱う比較軸
- `structure_type`
- `signal_type`
- `filter_reason`
- 必要に応じて `event_type`

### 10.5 初期段階で扱わないもの
- シャープレシオ等の高度指標
- 時間帯別・曜日別の詳細分析
- 補助AI由来の複雑な比較指標
- 多数の派生比率指標

### 10.6 初期版の要約出力
- `summary_report`
  - 正式指標本体ではなく、初期版の要約出力として扱う

## 11. 契約上重要な変数

初期版で固定する主要契約属性を以下に示す。

| 変数 | 型 | 値域 / 正式集合 | 単位 | nullable | 生成モジュール | 主な利用 |
|---|---|---|---|---|---|---|
| `timestamp` | datetime | 有効な UTC datetime | 時刻 | 不可 | PriceDataLoader | 全モジュール |
| `event_time` | datetime | 有効な UTC datetime | 時刻 | 条件付き可 | EventDataLoader | Data, RiskFilter |
| `log_time` | datetime | 有効な UTC datetime | 時刻 | 不可 | Logger | Logger, Evaluator |
| `open`, `high`, `low`, `close` | float | 有効な価格 | raw price | 不可 | PriceDataLoader | Data 以降 |
| `entry_price`, `fill_price`, `execution_price` | float | 有効な価格 | raw price | 条件付き可 | Execution | Execution, Logger |
| `stop_loss`, `take_profit` | float | 有効な価格 | raw price | 条件付き可 | RiskFilter | Execution |
| `bid`, `ask` | float | 有効な価格 | raw price | 条件付き可 | PriceDataLoader | Data, RiskFilter |
| `spread` | float | `>= 0` | pips | 不可 | PriceDataLoader | Data, RiskFilter |
| `volume` | float | `>= 0` | count | 不可 | PriceDataLoader | Data, Evaluator |
| `data_valid_flag` | bool | `true / false` | なし | 不可 | DataValidator | Data 以降 |
| `validation_reason` | string | 空文字または理由文字列 | なし | 不可 | DataValidator | Data 以降 |
| `event_flag` | bool | `true / false` | なし | 不可 | Data | RiskFilter |
| `event_type` | enum | `cpi / nfp / policy_rate / other` | なし | 条件付き可 | EventDataLoader | RiskFilter, Evaluator |
| `scheduled_event_flag` | bool | `true / false` | なし | 不可 | EventDataLoader / ExternalEventIngestor | RiskFilter, Logger |
| `official_release_flag` | bool | `true / false` | なし | 不可 | ExternalEventIngestor | RiskFilter, Logger |
| `breaking_news_flag` | bool | `true / false` | なし | 不可 | ExternalEventIngestor | RiskFilter, Logger |
| `source_reliability` | float | `0.0 <= x <= 1.0` | score | 条件付き可 | ExternalEventIngestor | RiskFilter |
| `event_severity` | float | `0.0 <= x <= 1.0` | score | 条件付き可 | ExternalEventIngestor | RiskFilter |
| `external_event_reason` | string | 空文字または理由文字列 | なし | 条件付き可 | ExternalEventIngestor | RiskFilter, Logger |
| `sns_risk_flag` | bool | `true / false` | なし | 条件付き可 | ExternalEventIngestor | RiskFilter |
| `sns_volume_spike_flag` | bool | `true / false` | なし | 条件付き可 | ExternalEventIngestor | RiskFilter |
| `htf_trend_dir` | enum | `up / down / neutral` | なし | 不可 | TrendDetector | HTFContext, Signal |
| `htf_trend_strength` | float | `0.0 <= x <= 1.0` | score | 不可 | TrendDetector | HTFContext, Signal |
| `htf_bias` | enum | `long_bias / short_bias / neutral` | なし | 不可 | ContextAssembler | Signal |
| `structure_type` | enum | `third_wave_break / triangle_break / none` | なし | 不可 | StructureAssembler | Signal, Logger, Evaluator |
| `failure_setup_flag` | bool | `true / false` | なし | 条件付き可 | FailurePatternDetector | LTFStructure, Signal |
| `failure_type` | string | `false_breakout / trap / failed_breakout / other` | なし | 条件付き可 | FailurePatternDetector | LTFStructure, Signal |
| `failure_confirm_flag` | bool | `true / false` | なし | 条件付き可 | FailureConfirmChecker | LTFStructure, Signal |
| `failure_confirm_time` | datetime | 有効な UTC datetime | 時刻 | 条件付き可 | FailureConfirmChecker | LTFStructure, Logger |
| `reversal_move_size` | float | `>= 0` | price difference | 条件付き可 | ReversalSignalEvaluator | LTFStructure, Logger |
| `reversal_move_atr_norm` | float | `>= 0` | ATR 正規化値 | 条件付き可 | ReversalSignalEvaluator | LTFStructure, Logger |
| `trap_direction` | enum | `long / short / neutral` | なし | 条件付き可 | FailurePatternDetector | LTFStructure, Signal |
| `trap_entry_signal` | bool | `true / false` | なし | 条件付き可 | ReversalSignalEvaluator | Signal |
| `trap_reason` | string | 空文字または理由文字列 | なし | 条件付き可 | FailurePatternDetector | LTFStructure, Logger |
| `structure_direction` | enum | `long / short / neutral` | なし | 不可 | StructureAssembler | Signal |
| `structure_candidate` | bool | `true / false` | なし | 不可 | StructureAssembler | Signal |
| `breakout_flag` | bool | `true / false` | なし | 不可 | BreakoutDetector | LTFStructure |
| `wave_phase` | enum | `first / second / third / unknown` | なし | 不可 | WaveClassifier | LTFStructure, Signal |
| `pattern_reason` | string | 空文字または理由文字列 | なし | 不可 | StructureAssembler | Signal, Logger |
| `entry_signal`, `exit_signal` | bool | `true / false` | なし | 不可 | Signal | RiskFilter, Execution |
| `signal_type` | enum | `long_entry / short_entry / exit / none` | なし | 不可 | SignalAssembler | RiskFilter, Logger, Evaluator |
| `signal_reason` | string | 空文字または理由文字列 | なし | 不可 | SignalAssembler | Logger |
| `trade_ok` | bool | `true / false` | なし | 不可 | RiskAssembler | Execution |
| `filter_reason`, `risk_reason`, `execution_reason`, `transition_reason` | string | 空文字または理由文字列 | なし | 不可 | RiskFilter / Execution | Logger, Evaluator |
| `lot` | float | `> 0` | lot | 条件付き可 | PositionSizer | Execution |
| `order_result` | enum | `filled / rejected / cancelled / failed / none` | なし | 不可 | Execution | Logger, StateTransitionManager |
| `position_state` | enum | `IDLE / ENTRY_PENDING / POSITION_OPEN / EXIT_PENDING / SUSPENDED / ERROR` | なし | 不可 | StateTransitionManager | Execution, Logger |

## 12. 将来拡張を前提とした変数

### 12.1 補助AI・相場分類向け
- `regime_label`
  - 相場状態の分類結果
  - 例: trend / range / unstable

- `regime_confidence`
  - 分類信頼度

- `aux_signal_flag`
  - 補助モデルが何らかの注意や補助判断を出したか

### 12.2 方針
これらの変数は初期段階では未使用でもよい。
ただし、将来差し込みやすいように、命名と層の考え方だけ先に残しておく。

### 12.3 資産クラス拡張向けの将来候補
- `asset_class`
  - FX / Equity などの資産クラス識別子（将来候補）
- `instrument_id`
  - 通貨ペアや銘柄を一意に識別するID（将来候補）
- `price_unit`
  - 価格単位（例: pips / tick）（将来候補）
- `quantity_unit`
  - 数量単位（例: lot / shares）（将来候補）
- `tick_size`
  - 最小価格刻み（将来候補）
- `session_calendar`
  - 市場セッション定義への参照情報（将来候補）
- `liquidity_state`
  - 流動性状態の分類ラベル（将来候補）

補足:
- 上記は将来候補であり、現行の正式変数契約を変更しない。
- 詳細方針は `docs/18_asset_class_extension_policy.md` を参照する。

## 13. 共通ルール

### 13.1 理由変数を残す
売買判断、見送り、停止の理由を追跡できるよう、`*_reason` をできるだけ残す。

### 13.2 flag と state を混同しない
- flag は真偽
- state は状態の種類
として扱う。

### 13.3 変数の責務を越えない
各変数は、可能な限り生成モジュールが明確な状態にする。

### 13.4 初期版のログ保存形式最低方針
- 初期版の正式保存形式は UTF-8 の行指向ファイルとし、`decision_logs`、`trade_logs`、`state_logs`、`event_logs` を別集合で保持する
- ファイル形式は初期版では CSV を最低方針とする
- 1行1レコードを原則とし、ヘッダ名は本書の正式変数名に一致させる
- 時刻列は ISO 8601 UTC 文字列で保存する
- null を多用せず、bool は `true / false`、未成立理由は空文字を基本とする

### 13.5 未確定として隔離するもの
- `event_type` の細分類拡張
- 補助AI向け拡張変数の正式採用
- 初期 main で未使用の比較補助変数
- `lot sizing` 詳細（`account_balance` 連動、`risk_per_trade`、複利連動、broker lot制約厳密化）
  - ただし `Lot Sizing v1` では、上記のうち calculator 単体で完結する範囲（式・config・invalid・rounding/clamp）を先行固定する
