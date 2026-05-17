# 10_interface_contract

## 1. この文書の位置づけ
本書は、実装前にモジュール間I/O契約を整理するための補助文書である。

> 重要:
> - 本書は Source of Truth（正本）ではない
> - 正式定義は `docs/04_module_spec.md`、`docs/05_variable_spec.md`、`docs/06_state_spec.md`、`docs/07_test_plan.md` を参照する
> - 本書は上記正本から「境界契約」を抜き出して横断整理する目的に限定する

本書内で新しい責務、状態、命名を先に定義しない。

---

## 2. 参照元と優先順位
契約整理時の優先順位は以下とする。

1. `docs/04_module_spec.md`（モジュール責務と上位出力）
2. `docs/05_variable_spec.md`（命名、主要変数）
3. `docs/06_state_spec.md`（状態集合と遷移）
4. `docs/07_test_plan.md`（結合観点、契約判定）

矛盾が見つかった場合は、本書で独自解決せず `ops/DECISION_LOG.md` で扱う。

---

## 3. 契約整理の原則（SoT準拠）
- 命名は `docs/05_variable_spec.md` の語彙を優先する
- 状態は `position_state` と `IDLE / ENTRY_PENDING / POSITION_OPEN / EXIT_PENDING / SUSPENDED / ERROR` を使用する
- 正常系、異常系、取引不可（見送り）を分けて記述する
- 下位実装の詳細（dataclass/pydantic、例外階層、永続化形式など）は固定しない
- 未確定事項は本書末尾に隔離し、契約本文に混在させない

---

## 4. モジュール境界I/O契約（抽出整理）

### 4.1 Data -> HTFContext / LTFStructure
根拠: `docs/04` 3.5, `docs/05` 3章

### 受け渡し対象
| 項目 | 必須性 | 用途 |
|---|---|---|
| `timestamp`, `open`, `high`, `low`, `close`, `spread`, `volume` | 必須 | 価格系列の基礎入力 |
| `event_time`, `event_flag` | 条件付き | イベント近接判定、停止判定 |
| `event_type` | 任意 | イベント種別を扱う場合に利用 |
| `data_valid_flag` | 必須 | 後続モジュールへ進行可能かの判定 |
| `validation_reason` | 条件付き | `data_valid_flag=false` 時の理由（進行停止の根拠） |

### 境界条件
- 時系列は昇順で扱う（`docs/05` 11.1）
- 欠損・逆順・異常値は Data 側で検出する（`docs/04` DataValidator）

### 系統別の扱い
- 正常系: 必須項目が揃い、後続モジュールへ受け渡し可能
- 異常系: 検証NGは `data_valid_flag = false` と `validation_reason` で返す（失敗結果方式）
- 例外: 入力契約違反または処理継続不能な障害に限定する（必須列不足、時刻列解釈不能、読み込み元不存在、タイムフレーム指定不正）
- 取引不可: `event_flag` 等は直ちに異常とせず、主に RiskFilter の停止判定へ渡す

---

### 4.2 HTFContext -> Signal
根拠: `docs/04` 4.5, `docs/05` 4章, `docs/07` 5.2

### 受け渡し対象
| 項目 | 必須性 | 用途 |
|---|---|---|
| `htf_trend_dir` | 必須 | 上位足方向 |
| `htf_trend_strength` | 条件付き | 方向強度 |
| `htf_bias` | 必須 | 上位足バイアス |
| `htf_resistance_ok`, `htf_support_ok` | 必須 | 余地・障害判定 |
| `htf_context_reason` | 必須 | 判定理由追跡 |

### 境界条件
- `htf_trend_dir` は定義済み値のみ返す（`docs/07` 4.7）
- `htf_context_reason` は追跡可能性のため保持する（`docs/05` 13.1）

### 系統別の扱い
- 正常系: 上記項目を揃えて `Signal` に引き渡す
- 異常系: 方向不明や型不整合を曖昧値で埋めない
- 取引不可: `htf_bias` や `*_ok` の結果として見送り可能だが、異常とは区別する

---

### 4.3 LTFStructure -> Signal
根拠: `docs/04` 5.7, `docs/05` 5章, `docs/07` 5.3

### 受け渡し対象
| 項目 | 必須性 | 用途 |
|---|---|---|
| `structure_type` | 必須 | 構造種別 |
| `structure_direction` | 必須 | 構造方向 |
| `breakout_flag` | 必須 | ブレイク有無 |
| `wave_phase` | 必須 | 波動段階 |
| `pattern_reason` | 必須 | 構造判定理由 |
| `structure_candidate` | 必須 | 候補有無 |

### 境界条件
- LTFStructure 系の正式理由変数は `pattern_reason` とする（`breakout_reason` は境界契約に含めない）
- `breakout_flag=true` 時は根拠理由を `pattern_reason` から追跡可能にする（`docs/07` 4.7）
- 初期 main の対象構造は `third_wave_break` とする
- `triangle_break` は `experiments` 先行とし、main へ初期段階で同時導入しない
- 競合ケースは安全側で扱う

### 系統別の扱い
- 正常系: 構造情報を `Signal` へ渡す
- 異常系: 方向・種別未定義のまま通さない
- 取引不可: `structure_candidate=false` は正常な見送り結果として扱う
- 競合ケース: `third_wave_break` と `triangle_break` が同時成立しそうな場合は、`structure_candidate=false`、`structure_type=none`、`structure_direction=neutral` とし、`pattern_reason` に競合理由を残す

---

### 4.4 Signal -> RiskFilter
根拠: `docs/04` 6.5, `docs/05` 6章, `docs/07` 5.4

### 受け渡し対象
| 項目 | 必須性 | 用途 |
|---|---|---|
| `entry_signal` | 必須 | 新規候補判定 |
| `exit_signal` | 必須 | 決済候補判定 |
| `signal_type` | 必須 | 種別（entry/exit/none） |
| `signal_reason` | 必須 | 判定理由 |

### 境界条件
- `signal_type` は定義済み分類に従う（`docs/05` 6.1, `docs/07` 4.2）
- 理由項目は後追い可能な形で保持する（`docs/05` 13.1）

### 系統別の扱い
- 正常系: シグナル情報を `RiskFilter` へ渡す
- 異常系: `entry_signal` と `signal_type` の矛盾は契約違反として扱う
- 取引不可: `entry_signal=false` または `signal_type=none` は見送り

---

### 4.5 RiskFilter -> Execution
根拠: `docs/04` 7.5, `docs/05` 7章, `docs/06` 4章, `docs/07` 5.5

補足（Risk/Stop v0）:
- 本境界では `trade_ok`、`stop_loss`、`take_profit`、`risk_reason`、`filter_reason` の責務を先に固定する。
- `lot` は契約上の受け渡し項目として維持するが、lot sizing 詳細は後続で固定する。
- RiskFilter 入力文脈の価格は `entry_price_candidate` を優先語とし、Execution 後の確定価格（`entry_price` / `fill_price`）と区別する。
- `signal_type` / `structure_type` / `spread` / `event_flag` は upstream 文脈として RiskFilter 判定に使われる想定とし、本書では境界I/Oの追跡方針のみ固定する。
- `fixed_sl_tp` baseline（`docs/17`）を壊さないことを前提にする。
- `risk_reason` / `filter_reason` は enum ではなく、Reason Catalog（固定文字列カタログ）で管理する。
- 文字列形式は `category_token[:detail]` を許容し、主要集計は `category_token` で行う。

### 受け渡し対象
| 項目 | 必須性 | 用途 |
|---|---|---|
| `trade_ok` | 必須 | 発注可否 |
| `lot` | 条件付き | 発注量 |
| `stop_loss`, `take_profit` | 条件付き | リスク制御価格 |
| `risk_reason` | 必須 | リスク設定理由 |
| `filter_reason` | 条件付き | 停止・見送り理由 |

### 境界条件
- `trade_ok=true` の場合は `lot / stop_loss / take_profit` が有効であること（`docs/07` 4.7）
- `lot` が未算出・空・`<=0`・不正値の場合は `trade_ok=true` を許容しない
- `trade_ok=false` の場合は `filter_reason` または `risk_reason` に停止根拠を残し、Execution では新規発注を行わない
- `trade_ok=false` でも理由列を空にせず、Logger/Evaluator で追跡可能にする

### 系統別の扱い
- 正常系: `trade_ok=true` で Execution に進む
- 異常系: 値域不正（`lot<=0` 等）は契約違反として扱う
- 取引不可: `trade_ok=false` は停止条件成立として扱い、`filter_reason` / `risk_reason` を記録する

### 4.5.1 PositionSizer placeholder（v0実装前提）
- Risk/Stop v0 実装時は `PositionSizer placeholder` により暫定固定lot（または設定値lot）を返す方式を許容する。
- 目的は `RiskFilter -> Execution` 契約充足であり、資金管理最適化ではない。
- `account_balance` / `risk_per_trade` / broker lot制約厳密化は後続で扱う。
- placeholder 理由は当面 `risk_reason` に残し、専用変数追加は v0 では必須としない。

### 4.5.2 PipelineAdapter の planner chain 正式接続（実装後現況）
- 現在の `PipelineAdapter` は `PositionSizer` / `StopLossPlanner` / `TakeProfitPlanner` を本体経路で直列接続し、`RiskAssembler` に渡す。
- `PositionSizer` は placeholder のまま維持する。
- `account_balance` は placeholder valid 判定を通す fixed input（`placeholder_account_balance`）として扱う。
- `entry_price_candidate` は `current_bar.close` を使用する。
- 接続目的は fixed baseline 同値維持（`fixed_lot` / fixed SL distance / fixed TP distance）であり、lot sizing 本体や収益性評価ではない。

### 4.5.3 実装後の残課題（非対応範囲）
- lot sizing 本体実装、`account_balance` 連動計算式、`risk_per_trade`、broker lot 制約厳密化は未実装。
- OANDA/API 接続、実注文、broker 連携は未実装。
- Session/SR/HTF filter 本採用化、experimental exit 本採用、株式拡張、収益性評価は対象外。

### 4.5.4 reason語彙の境界（2026-05-15）
- 管理語彙（集計主軸）:
  - `risk_reason`
  - `filter_reason`
- 説明用自由文（人間向けトレース主軸）:
  - `decision_reason`
  - `signal_reason`
  - `pattern_reason`
  - `htf_context_reason`
- 本方針はログ追跡性を維持しつつ、集計軸の安定化を優先する。

### 4.5.5 Lot Sizing v1（独立フェーズ）契約方針（2026-05-15）
- `lot sizing` 本体は独立フェーズ `Lot Sizing v1` として扱う。
- `Lot Sizing v1` 初期は isolated calculator の契約固定を対象とし、`PipelineAdapter` / backtest main path には接続しない。
- `fixed_lot` baseline は維持し、現行 `PositionSizer placeholder` と planner chain 本線挙動を変更しない。
- formula（初期固定）:
  - `lot = account_balance * risk_per_trade / (stop_loss_distance_pips * pip_value_per_lot)`
- calculator 入力（初期固定）:
  - `account_balance`
  - `risk_per_trade`
  - `stop_loss_distance_pips`
  - `pip_value_per_lot`
  - `lot_step`
  - `min_lot`
  - `max_lot`
  - `rounding_mode`
- calculator 出力（初期固定）:
  - `lot`
  - `raw_lot`
  - `rounded_lot`
  - `clamped_flag`
  - `size_reason`
- rounding方針（初期固定）:
  - `rounding_mode=floor` のみ対応
  - `round` / `ceil` は非対応
  - 指定リスク超過を避けるため floor を採用
- clamp方針（初期固定）:
  - `raw_lot` または `rounded_lot` が `max_lot` を超える場合は `max_lot` へ clamp 可
  - `rounded_lot < min_lot` は `min_lot` へ引き上げず invalid とする
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
- 非対応範囲:
  - PipelineAdapter接続
  - PositionSizer置換
  - backtest PnL変更
  - trade_count変更
  - 実運用 broker 制約厳密化
  - OANDA/API 接続
  - 実注文
  - 通貨ペア別pip価値自動計算
  - 収益性評価
  - 売買ロジック変更

### 4.5.6 Lot Sizing v1 の本線接続判断（2026-05-15）
- 判断:
  - 現時点で `PipelineAdapter` / `PositionSizer` 本線への直接接続は **No-Go / Hold** とする。
- 理由:
  - `fixed_lot` baseline を壊す可能性がある。
  - PnL / trade_count / risk logs の解釈が変化する。
  - `pip_value_per_lot` が手入力前提で、前提差異を本線に持ち込みやすい。
  - broker別制約厳密化、OANDA/API、実運用要件は未対応である。
  - 収益性評価へ論点が拡散しやすい。
- 次フェーズ方針:
  - shadow mode / comparison-only 設計を先行する。
  - `fixed_lot` は本線維持、risk-based lot は診断値として比較に限定する。
  - 診断比較は PnL / trade_count / entry/exit 判断に影響させない。
- shadow mode の比較ログ候補:
  - `fixed_lot`
  - `risk_based_raw_lot`
  - `risk_based_rounded_lot`
  - `risk_based_effective_lot`
  - `lot_sizing_reason`
  - `clamped_flag`
  - `lot_size_diff`

### 4.5.7 Lot Sizing v1 shadow mode / comparison-only 方針（2026-05-15）
- 目的:
  - `fixed_lot` と risk-based lot の差分観測
  - invalid / clamp / below_min 頻度の把握
  - 将来の本線接続判断材料の作成
  - 収益性評価ではない
- 実装候補の優先順位:
  - C: 専用 offline script で既存ログへ後付け適用（優先）
  - B: 既存 analysis script 拡張（次点）
  - A: `PipelineAdapter` 内 shadow 計算（後続候補、現時点は採用しない）
- C/B 優先理由:
  - 既存本線挙動への影響を最小化できる
  - `PipelineAdapter` へ診断責務を追加しない
  - `account_balance` / `pip_value_per_lot` / `risk_per_trade` 供給経路が未固定でも比較設計を先行できる
  - decision log 列追加を本線仕様と誤認するリスクを抑えられる
- 診断値候補（shadow comparison）:
  - `fixed_lot`
  - `risk_based_raw_lot`
  - `risk_based_rounded_lot`
  - `risk_based_effective_lot`
  - `risk_based_lot_sizing_reason`
  - `risk_based_clamped_flag`
  - `lot_size_diff`
  - `lot_size_ratio`
  - `risk_lot_valid_flag`
- 非影響保証:
  - actual lot は `fixed_lot` のまま
  - PnL / trade_count / entry/exit / `trade_ok` 判定に影響させない
  - Execution / order path に渡さない

---

### 4.6 Execution -> Logger
根拠: `docs/04` 8.5, `docs/05` 8章, `docs/06` 8章, `docs/07` 5.6

### 受け渡し対象
| 項目 | 必須性 | 用途 |
|---|---|---|
| `order_result` | 必須 | 注文結果 |
| `fill_price`, `execution_price` | 条件付き | 約定・執行価格 |
| `position_state` | 必須 | 現在状態 |
| `execution_reason` | 必須 | 実行理由 |

### 状態遷移追跡で必須の記録項目
`docs/06` 8章に従い、Logger 側では以下を追跡可能にする。
- `position_state`
- `previous_state`
- `next_state`
- `transition_reason`
- `order_result`
- `execution_reason`
- `log_time`
- 上記の状態遷移情報は `state_logs` に記録し、`event_logs` には含めない

### 系統別の扱い
- 正常系: 実行結果と状態更新を記録へ渡す
- 異常系: 注文応答異常や状態不整合は `ERROR` 遷移候補として扱う
- 取引不可: 実行前段で停止済みの場合、実行しなかった理由を記録する

---

### 4.7 Logger -> Evaluator
根拠: `docs/04` 9.5/10.5, `docs/05` 9章/10章, `docs/07` 5.7/5.8

### 受け渡し対象
| 項目 | 必須性 | 用途 |
|---|---|---|
| `trade_logs` | 必須 | 約定・損益分析用ログ集合 |
| `event_logs` | 必須 | 停止・見送り・イベント分析用ログ集合 |
| `decision_logs` | 必須 | 判断理由分析用ログ集合 |
| `state_logs` | 必須 | 状態遷移分析用ログ集合 |
| `signal_reason`, `risk_reason`, `filter_reason`, `execution_reason` | 必須 | 理由分析 |
| `structure_type`, `signal_type`, `filter_reason` | 必須 | 初期版の主要比較軸 |
| `event_type` | 任意 | 必要時の比較軸 |

### 境界条件
- Evaluator が再集計可能な粒度で保存する（`docs/07` 5.7, 6.2）
- 理由ログ欠損は評価可能性を下げるため、欠損させない
- 状態遷移関連は `state_logs` に集約し、`event_logs` と二重管理しない
- Reason Catalog 適用時は既存 `risk_reason` / `filter_reason` を置換せず、analysis側で派生列（category list / primary category）を追加する方針を優先する
- `risk_reason` / `filter_reason` の `|` 連結は `normalize_reason_categories()` で category list 化して扱う
- 初期版の基本成績指標は `trade_count`, `win_rate`, `average_pnl`, `profit_factor`, `max_drawdown` とする
- 初期版の分析補助指標は `structure_type_stats`, `filter_hit_stats`, `signal_type_stats` とする
- 初期版の期間単位は全期間・月次・構造種別単位とする
- シャープレシオ等の高度指標、時間帯別・曜日別詳細分析、補助AI由来の複雑比較指標、多数の派生比率指標は初期段階で扱わない

### 系統別の扱い
- 正常系: 評価対象ログが揃っている
- 異常系: 欠損時は「評価不能理由」を明示する
- 取引不可: 見送りイベントは `event_logs`、状態遷移は `state_logs` で保持する

---

### 4.7.1 dry-run secondary summary での reason category 集計方針（実装前固定）
根拠: `scripts/summarize_csv_replay_dry_run.py`, `scripts/run_csv_replay_pipeline_dry_run.py`

目的:
- near-live 検証（health/status/warnings中心）を維持したまま、reason語彙の構造追跡を最小追加する。

対象ログと対象列:
- 入力ログ: `near_live_decision_logs.csv`
- category 集計主対象:
  - `risk_reason`
  - `filter_reason`
- 集計対象外（自由文）:
  - `decision_reason`
  - `signal_reason`

適用方式:
- `normalize_reason_categories()` を利用し、`|` 連結reasonを category list 化する。
- `None` / 空白 / 欠損は unknown 扱いに寄せる。
- `"none"` を category として誤集計しない。

出力方針:
- 既存summary項目（`near_live_summary.*`, `dry_run_period_summary.*`）は削除・改名しない。
- 派生メトリクスを追加する方式に限定する。
- `run_csv_replay_pipeline_dry_run.py` のログ生成形式は変更しない。

非対象:
- 行単位派生列CSVの追加。
- Evaluator本体（`src/evaluator/filter_analyzer.py`）の同時変更。
- canonical出力への即時移行。

---

### 4.7.2 Evaluator `FilterAnalyzer` の category分析方針（実装前固定）
根拠: `src/evaluator/filter_analyzer.py`, `src/evaluator/types.py`

目的:
- Evaluator本体で Reason Catalog category 分析を追加する際に、既存完全一致集計との互換を維持する。

判断:
- A方針を採用する。
- 既存 `FilterAnalyzer.analyze(logs)` は維持し、category分析は別メソッド（例: `analyze_by_category(logs)`）で追加する。

互換方針:
- 既存 `FilterStatsResult.filter_reason` の意味（完全一致bucket key）を変更しない。
- 既存呼び出し・既存テストが期待するキー文字列（例: `"spread_too_high"`）を壊さない。
- 既存 `analyze()` の欠損時 warning 挙動は維持する。

category集計方針:
- `normalize_reason_categories()` を使う。
- `|` 連結reasonは category ごとに複数カウントする（1ログが複数bucketに入ることを許容）。
- primary category への単純圧縮は Evaluator本体の第1段階では採用しない。

欠損方針（category分析側）:
- `None` / 空白 / 欠損は unknown として扱う。
- `"None"` が `"none"` category へ誤変換されないよう、正規化前に空文字化する。

非対象:
- 既存 `analyze()` の category置換（C方針）。
- scripts側既存集計の置換。
- 売買ロジック、`trade_ok`、PipelineAdapter挙動の変更。

---

### 4.8 Backtest trade_logs 追加契約（初期構造検証）
根拠: `src/backtest/backtest_logger_adapter.py`, `docs/17_backtest_design.md`

BacktestRunner 初期版では `decision_logs` 本格実装前の追跡性確保のため、`trade_logs` に以下を保持する。

| 項目 | 必須性 | 用途 |
|---|---|---|
| `entry_time` | 必須 | エントリー時刻追跡 |
| `exit_time` | 必須 | 決済時刻追跡 |
| `entry_reason` | 必須 | entry判断理由追跡 |
| `signal_reason` | 必須 | Signal判断理由追跡 |
| `risk_reason` | 必須 | RiskFilter判断理由追跡 |
| `filter_reason` | 必須 | フィルター理由追跡 |
| `fallback_used` | 必須 | heuristic fallback 使用有無 |
| `structure_source` | 必須 | `detector_chain` / `detector_chain_temporal` / `heuristic_fallback` 区別 |
| `recent_third_timestamp` | 条件付き | temporal third candidate の基準時刻 |
| `recent_third_direction` | 条件付き | temporal third candidate の方向 |
| `temporal_lag_bars` | 条件付き | third candidate と breakout の時間差 |
| `temporal_lookback_bars` | 条件付き | temporal 接続探索窓 |
| `breakout_direction` | 条件付き | breakout 方向追跡 |

補足:
- `recent_third_*` と `temporal_*` は `structure_source=detector_chain_temporal` 時に主に利用する。
- `temporal_candidate=true` の行でのみ `recent_third_timestamp` / `recent_third_direction` / `temporal_lag_bars` / `temporal_lookback_bars` は意味を持つ。
- `temporal_candidate=false` の行でこれらが空文字または `None` でも正常とする。
- schema validation では上表の backtest trade_logs 列を既知列として扱い、未知列のみを extra column warning の対象とする。
- これは収益性評価ではなく、構造検証における理由・接続追跡を目的とする。

### 4.8.1 trade_logs timestamp semantics（初期版）
Backtest trade_logs の時刻列は、初期版では以下の意味で扱う。

| 項目 | 現在の意味 |
|---|---|
| `entry_time` | entry decision bar timestamp（bar timestamp） |
| `exit_time` | exit decision bar timestamp（bar timestamp） |

補足:
- BacktestRunner の約定モデルは「現在バー close で entry」であるため、`entry_time`（bar timestamp）と約定有効時刻は同一概念ではない。
- M5 bar timestamp が bar open time の場合、M5 close entry を低位足で再現するには `entry_effective_time=entry_time+timeframe` を別扱いにする。

将来の列候補:
- `entry_effective_time`
- `exit_effective_time`
- `entry_bar_start_time`
- `entry_bar_end_time`

---

### 4.9 Backtest decision_logs 最小列案（初期構造検証）
根拠: `docs/17_backtest_design.md` 14.7

| 項目 | 必須性 | 用途 |
|---|---|---|
| `log_time` | 必須 | ログ記録時刻 |
| `bar_index` | 必須 | 判定対象バーindex |
| `timestamp` | 必須 | 判定対象バー時刻 |
| `close` | 必須 | 判定時の close |
| `htf_bias` | 条件付き | HTF側判定追跡 |
| `wave_phase` | 条件付き | 波動段階追跡 |
| `wave_direction` | 条件付き | 波動方向追跡 |
| `breakout_flag` | 条件付き | breakout 判定有無 |
| `breakout_direction` | 条件付き | breakout 方向追跡 |
| `structure_candidate` | 条件付き | 構造候補有無 |
| `structure_source` | 条件付き | `detector_chain` / `detector_chain_temporal` 追跡 |
| `temporal_candidate` | 条件付き | temporal 接続候補有無 |
| `recent_third_timestamp` | 条件付き | temporal third candidate 基準時刻 |
| `recent_third_direction` | 条件付き | temporal third candidate 方向 |
| `temporal_lag_bars` | 条件付き | temporal lag |
| `temporal_lookback_bars` | 条件付き | temporal lookback 設定 |
| `direction_aligned` | 条件付き | HTF/LTF 方向整合判定 |
| `pattern_allowed` | 条件付き | PatternGate 判定 |
| `entry_signal` | 条件付き | entry signal 有無 |
| `trade_ok` | 条件付き | RiskFilter 通過判定 |
| `fail_stage` | 必須 | `structure/signal/risk_filter/dedup/...` の失敗段階 |
| `decision_reason` | 必須 | no-entry / entry の理由 |

補足:
- 初期実装では全バー必須ではなく、候補発生バーまたは判定変化バー中心の収集を許容する。
- `fail_stage` は `structure` / `direction_alignment` / `pattern_gate` / `signal` / `risk_filter` / `dedup` / `none` を基本分類とする。
- `decision_logs` の schema validation では、必須列充足に加えて `fail_stage` / `structure_source` の許容値検証と temporal metadata 整合（`temporal_candidate` 条件）を確認する。
- `trade_logs` と `decision_logs` の整合検証では、`trade_ok=true` 件数と `trade_count` の一致、および fallback OFF 時の `heuristic_fallback` 混入有無を確認する。
- 目的は収益性評価ではなく、構造検証とデバッグである。

---

## 5. 状態遷移との接続契約（`docs/06` 準拠）
本書では状態定義を再定義せず、境界接続条件のみを整理する。

| 遷移 | 最低条件 | 主に参照する契約項目 |
|---|---|---|
| `IDLE -> ENTRY_PENDING` | 新規候補成立 + `trade_ok=true` + 注文発行開始 | `entry_signal`, `trade_ok`, `order_result` |
| `ENTRY_PENDING -> POSITION_OPEN` | 注文正常約定 | `order_result=filled`, `position_state` |
| `ENTRY_PENDING -> IDLE` | 注文拒否/キャンセル/失敗で未保有継続 | `order_result`, `execution_reason` |
| `POSITION_OPEN -> EXIT_PENDING` | 決済条件成立で決済発行 | `exit_signal` など |
| `EXIT_PENDING -> IDLE` | 決済完了 | `order_result`, `position_state` |
| `IDLE -> SUSPENDED` | 停止条件成立 | `filter_reason` など |
| `ANY -> ERROR` | 重大不整合/想定外例外 | `execution_reason`, `transition_reason` |
| `ERROR -> SUSPENDED` | 安全側への退避 | `position_state`, `transition_reason` |

---

## 6. 結合・検証観点（`docs/07` 準拠）

### 6.1 上位モジュール間の確認対象
- `Data -> HTFContext`
- `Data -> LTFStructure`
- `HTFContext -> Signal`
- `LTFStructure -> Signal`
- `Signal -> RiskFilter`
- `RiskFilter -> Execution`
- `Execution -> Logger`
- `Logger -> Evaluator`

### 6.2 契約テストで最低限確認すること
- 必須変数の欠落がないこと
- 命名が `docs/05` と一致していること
- `*_reason` が追跡可能に残ること
- `trade_ok=true` 時の `lot / stop_loss / take_profit` 妥当性
- 不正状態遷移が拒否または安全側遷移されること

---

## 7. 本書で定義しないもの
以下は本書で先に固定しない。
- DTO の実装方式（dataclass / pydantic 等）
- enum 実装方式
- 例外クラス階層
- ログ永続化形式（JSON Lines / CSV 等）
- 厳密な型注釈規約

これらは、将来追加予定の同等文書（コーディング規約・実装規約）で扱う。

---

## 8. 未確定事項（隔離）
現時点の初期版スコープで、未確定事項はない。
