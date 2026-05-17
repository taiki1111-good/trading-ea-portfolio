# トレーサビリティマトリクス

## 1. 文書の目的
この文書は、`docs/02_requirements.md` の FR / NFR を起点に、モジュール・主要変数・状態・テストへの追跡線を明確化する。

## 2. Requirement ID ルール
- 機能要件は `FR-XX`、非機能要件は `NFR-XX` を使う
- 要件 ID は `docs/02_requirements.md` の定義をそのまま使う
- 新規 ID は本書では追加せず、要件追加時は先に `docs/02` を更新する

## 3. 機能要件（FR）対応表
| 要件 ID | 要件概要 | 主なモジュール | 主要変数（`docs/05` 準拠） | 関連状態 | 代表テスト種類 |
|---|---|---|---|---|---|
| FR-01 | 価格データ読み込み | Data | `timestamp`, `open`, `high`, `low`, `close`, `spread`, `volume` | - | unit: PriceDataLoader |
| FR-02 | イベントデータ読み込み | Data | `event_time`, `event_type`, `event_flag` | - | unit: EventDataLoader |
| FR-03 | 時間足対応（M5/H1/H4） | Data, TimeframeAligner | `timestamp`, `open`, `high`, `low`, `close` | - | integration: TimeframeAligner |
| FR-04 | 欠損・型不正・順序不正・異常値検出 | DataValidator | `data_valid_flag`, `validation_reason` | `ERROR` | unit: DataValidator |
| FR-05 | 複数時間足参照整合 | TimeframeAligner, HTFContext | `timestamp`, `htf_trend_dir`, `htf_trend_strength` | - | contract / integration: Data -> HTFContext |
| FR-06 | 上位足方向判定 | HTFContext | `htf_trend_dir`, `htf_trend_strength`, `htf_bias` | - | unit / integration: HTFContext |
| FR-07 | 上位足抵抗・支持判定 | HTFContext | `htf_resistance_ok`, `htf_support_ok`, `htf_context_reason` | - | unit / integration: HTFContext |
| FR-08 | 執行足構造認識 | LTFStructure | `structure_type`, `structure_direction`, `wave_phase`, `breakout_flag` | - | unit: LTFStructure components |
| FR-09 | `third_wave_break` 判定 | LTFStructure | `structure_type`, `structure_direction`, `structure_candidate`, `pattern_reason` | - | integration / scenario: main flow |
| FR-10 | 追加構造の experiments 分離検証 | LTFStructure, Evaluator, experiments | `structure_type`（`triangle_break` は experiments で扱う）, `pattern_reason` | - | experiments test |
| FR-11 | シグナル統合 | Signal | `entry_signal`, `exit_signal`, `signal_type`, `signal_reason` | - | integration: Signal |
| FR-12 | 方向一致確認 | Signal | `htf_trend_dir`, `structure_direction`, `signal_type`, `signal_reason` | - | integration: Signal |
| FR-13 | 許容構造のみ通過 | Signal | `structure_type`, `entry_signal`, `signal_type`, `pattern_reason` | `IDLE` | integration / scenario |
| FR-14 | 最終取引可否判定 | RiskFilter | `trade_ok`, `filter_reason` | `IDLE` | integration: RiskFilter |
| FR-15 | イベント近接停止 | RiskFilter | `event_flag`, `event_type`, `event_risk_flag`, `trade_ok`, `filter_reason` | `SUSPENDED` | unit / scenario: event stop |
| FR-16 | spread 異常停止 | RiskFilter | `spread`, `trade_ok`, `filter_reason` | `SUSPENDED` | unit / scenario: spread stop |
| FR-17 | 取引回数・連敗停止 | RiskFilter | `daily_trade_count`, `losing_streak`, `max_trade_reached_flag`, `trade_ok`, `filter_reason` | `SUSPENDED` | unit / scenario: trade limit |
| FR-18 | 損切り設定 | RiskFilter | `stop_loss`, `risk_reason` | `POSITION_OPEN` | unit / integration |
| FR-19 | 利確設定 | RiskFilter | `take_profit`, `risk_reason` | `POSITION_OPEN` | unit / integration |
| FR-20 | ロット決定 | RiskFilter | `lot`, `account_balance`, `risk_reason` | `POSITION_OPEN` | unit: PositionSizer |
| FR-21 | 発注内容生成 | Execution | `entry_signal`, `signal_type`, `lot`, `stop_loss`, `take_profit` | `ENTRY_PENDING` | integration: Execution |
| FR-22 | 注文送信 | Execution | `order_result`, `execution_reason` | `ENTRY_PENDING` | integration / scenario |
| FR-23 | 約定・拒否・取消・失敗処理 | Execution | `order_result`, `fill_price`, `execution_price`, `execution_reason` | `ENTRY_PENDING`, `EXIT_PENDING` | scenario: order handling |
| FR-24 | 状態管理 | StateTransitionManager | `position_state` | `IDLE`, `ENTRY_PENDING`, `POSITION_OPEN`, `EXIT_PENDING`, `SUSPENDED`, `ERROR` | scenario: state transition |
| FR-25 | 不正遷移防止 | StateTransitionManager | `position_state`, `transition_reason` | ALL | scenario: invalid transition |
| FR-26 | `ENTRY_PENDING` / `POSITION_OPEN` 中の新規禁止 | Execution | `position_state`, `entry_signal`, `signal_type` | `ENTRY_PENDING`, `POSITION_OPEN` | scenario: duplicate entry |
| FR-27 | 停止・異常遷移 | StateTransitionManager | `position_state`, `transition_reason` | `SUSPENDED`, `ERROR` | scenario: suspension / error |
| FR-28 | 判断理由記録 | Logger | `htf_context_reason`, `pattern_reason`, `signal_reason`, `risk_reason`, `filter_reason`, `execution_reason` | ANY | logging test |
| FR-29 | 注文結果・損益記録 | Logger | `order_result`, `fill_price`, `pnl`, `trade_id` | ANY | logging test |
| FR-30 | 状態遷移記録 | Logger | `previous_state`, `next_state`, `transition_reason`, `position_state`, `log_time` | ANY | state log test |
| FR-31 | 基本成績算出 | Evaluator | `trade_count`, `win_rate`, `average_pnl`, `profit_factor`, `max_drawdown` | - | unit / integration: evaluator |
| FR-32 | 構造・停止理由集計 | Evaluator | `structure_type_stats`, `filter_hit_stats`, `signal_type_stats` | - | integration: evaluator |
| FR-33 | 本体と実験の比較評価 | Evaluator, experiments | `structure_type_stats`, `signal_type_stats`, `filter_hit_stats` | - | experiments comparison |
| FR-34 | 公式発表・経済カレンダー・速報ニュースによる危険局面検知と停止閾値補正の比較検証 | RiskFilter, EventDataLoader, ExternalEventIngestor, Evaluator, experiments | `scheduled_event_flag`, `official_release_flag`, `breaking_news_flag`, `source_reliability`, `event_severity`, `external_event_reason`, `trade_ok`, `filter_reason` | `SUSPENDED`, `IDLE` | experiments / scenario |

## 4. 非機能要件（NFR）対応表
| 要件 ID | 担保ポイント | 主な担保文書 / モジュール | 主な確認方法 |
|---|---|---|---|
| NFR-01 | 判断・停止・遷移理由の追跡可能性 | Logger, `docs/05`, `docs/06`, `docs/07` | logging test / docs review |
| NFR-02 | 修正しやすい構造 | `docs/03`, `docs/04` | docs review / code review |
| NFR-03 | 段階的テスト容易性 | `docs/07`, `tests/unit`, `tests/integration`, `tests/scenario` | test structure review |
| NFR-04 | 異常時の安全性 | DataValidator, RiskFilter, StateTransitionManager | scenario / contract test |
| NFR-05 | 二重エントリー等の禁止 | Execution, StateTransitionManager | scenario |
| NFR-06 | 高凝集・低結合 | `docs/03`, `docs/04` | architecture / code review |
| NFR-07 | 拡張追加のしやすさ | `docs/04`, `docs/05`, `src/experiments` | design review |
| NFR-08 | 可読性 | `docs/04`, `docs/05`, 命名規則 | docs review |
| NFR-09 | 影響範囲限定 | モジュール分割方針 | change review |
| NFR-10 | 他商品流用可能性 | `docs/02`, `docs/03`, `docs/15` | docs review |
| NFR-11 | docs ベース継続性 | `docs/00`, `AGENT_INDEX.md`, `REPO_MAP.md`, `ops/` | handoff review |
| NFR-12 | 単方向データフロー維持 | `docs/03`, `docs/04` | architecture review |
| NFR-13 | 売買判断と状態管理の分離 | Signal / RiskFilter / StateTransitionManager | docs review / scenario |
| NFR-14 | ログから復元可能 | Logger, Evaluator, `state_logs` | logging test |
| NFR-15 | experiments の本体分離 | `docs/experiments`, `src/experiments`, `tests/experiments` | repo structure review |
| NFR-16 | 設計先行・段階実装・段階テスト順守 | `docs/08`, `ops/CURRENT_TASKS.md` | process review |
| NFR-17 | 説明しやすさ | `docs/01` から `docs/08`, `docs/12` | docs / portfolio review |
| NFR-18 | ルールベース中核維持 | `docs/02`, Signal / RiskFilter 設計 | docs review |
| NFR-19 | 補助AI差し込み余地 | `docs/02`, `docs/04`, `docs/05` | design review |
| NFR-20 | 個人開発制約下での実現可能性 | `docs/08`, `docs/13`, `ops/CURRENT_TASKS.md` | process / milestone review |

## 5. 未対応 / 保留項目
- `triangle_break` は `experiments` で分離検証し、本体統合は後段判断とする（FR-10）。
- FR-34 の比較検証は初期版 main の受入必須ではなく、`experiments` 側で段階的に実施する。
- 数値閾値（spread 上限、停止時間、外部イベント重み）は本書では未確定（TBD）とする。

## 6. 更新ルール
- 要件 ID の追加・変更は先に `docs/02_requirements.md` を更新する。
- 変数名は `docs/05_variable_spec.md` の正式名を使う。
- 状態名は `docs/06_state_spec.md` の正式名を使う。
- テスト種別と受入観点は `docs/07_test_plan.md` と同期する。
- 重要な追跡方針変更は `ops/DECISION_LOG.md` に記録する。
