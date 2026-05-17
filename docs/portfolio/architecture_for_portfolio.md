# Architecture for Portfolio

本書は外部説明用の要約であり、Source of Truth ではない。正式な現状・契約・実装境界は `ops/CURRENT_TASKS.md`、`docs/03_architecture.md`、`docs/04_module_spec.md`、`docs/05_variable_spec.md`、`docs/10_interface_contract.md`、`docs/17_backtest_design.md` を優先する。

## 1. 全体フロー
本プロジェクトの中心は、判断を一つの巨大な条件式にせず、責務ごとのモジュールへ分解することである。

```text
Data
  -> HTFContext
  -> LTFStructure
  -> Signal
  -> RiskFilter
  -> Execution
  -> Logger
  -> Evaluator
```

各モジュールは、前段の出力を受け取り、後段へ必要な情報と理由を渡す。外部説明では、売買パラメータよりも、責務分離、時系列整合、ログ追跡を中心に説明する。

## 2. 各モジュールの役割
- `Data`: 価格データやイベントデータを読み込み、後続で扱える形にする。
- `HTFContext`: 上位足の方向性や環境を整理する。
- `LTFStructure`: 執行足の構造候補を認識する。
- `Signal`: HTF と LTF の情報を統合し、entry / exit 候補を生成する。
- `RiskFilter`: `trade_ok`、lot、SL/TP、停止理由を整理する。
- `Execution`: dry-run / backtest 文脈で注文相当の状態を扱う。
- `Logger`: 判断理由、状態、取引相当の結果を記録する。
- `Evaluator`: ログから検証用の集計を行う。

## 3. BacktestRunner / PipelineAdapter / CSV Replay Dry-Run
BacktestRunner は、過去データを時系列順に流し、主要モジュールを backtest 用に駆動する。

PipelineAdapter は、BacktestRunner から主要モジュールを呼び出すための接続層として扱う。現時点では `PositionSizer` / `StopLossPlanner` / `TakeProfitPlanner` / `RiskAssembler` の planner chain へ正式接続済みである。ただし目的は fixed baseline 同値維持であり、機能拡張や収益性評価ではない。`PositionSizer` は placeholder を維持する。

CSV replay dry-run は、near-live 風に CSV を流し、ログ整合、health 判定、no-real-order integrity（実注文が発生していないことの整合確認）を確認するための検証経路である。dry-run は実注文を行わない検証実行であり、`dry_run_health_status=pass` はログ整合の確認結果を示す。収益性や実運用品質を意味しない。

補足:
- HTF は diagnostic comparison v0（採用前に条件差分を診断する比較）までを完了しており、本体filter採用ではない。
- lot sizing は shadow comparison tool（本体挙動へ影響させずに候補値を比較する仕組み）として採用しており、本体接続ではない。

## 4. Logger / Persistence / Evaluator
ログは、後から判断理由と状態を追跡できるように分けて扱う。

- `decision_logs`: 各バーや判断点での判定理由
- `trade_logs`: entry / exit 相当の結果や損益集計用情報
- `state_logs`: 状態遷移
- `event_logs`: 停止・見送り・イベント系の記録

Persistence は CSV skeleton を中心に、run_id ごとの再現性を意識する。Evaluator はこれらのログを読み、構造検証や比較のための基本集計を行う。

### 抽象ログ例
```text
decision_logs.csv (abstract example)
timestamp            signal_type      trade_ok   signal_reason           risk_reason             position_state
2026-01-01T01:00Z    long_entry       true       structure_confirmed     all_risk_filters_passed ENTRY_PENDING
2026-01-01T01:05Z    none             false      no_signal               no_entry_signal         IDLE

state_logs.csv (abstract example)
timestamp            previous_state   next_state      transition_reason
2026-01-01T01:00Z    IDLE             ENTRY_PENDING   entry_order_started
2026-01-01T01:10Z    ENTRY_PENDING    POSITION_OPEN   order_filled

event_logs.csv (abstract example)
timestamp            event_type       event_reason
2026-01-01T02:00Z    warning          data_gap_detected
```

- 目的は成績表示ではなく、判断理由と状態遷移を後から追跡できるようにすること。
- `decision_logs` は各判断点の理由追跡に使う。
- `state_logs` は状態遷移の整合確認に使う。
- `event_logs` は停止・警告・データgap確認に使う。
- `trade_logs` は entry / exit 相当の記録に使うが、外部説明では PnL の優劣を主張しない。
- 上記は抽象例であり、実データ・実績値ではない。
- `PnL` / `win_rate` / `total_pnl` などの成績数値はここでは扱わない。
- 収益性確認や実運用品質を意味しない。
- 実際の取引システムとの接続や注文送信機能とは無関係である。

## 5. Main と Experiments の分離
初期 main は `third_wave_break` を中心に扱う。

新しい裁量仮説や補助ロジックは、最初から main に混ぜず、`docs/experiments/`、`src/experiments/`、`tests/experiments/` で扱う。これにより、既存フローの安定性と、新規仮説の比較可能性を分けて管理する。

## 6. Future Leak 防止
BacktestRunner / PipelineAdapter では、各時点で参照可能なデータを現在バーまでに限定する。

```text
current step i:
  usable data = bars[:i+1]
  forbidden data = bars[i+1:]
```

この方針により、未来の価格や未確定情報を使った楽観的な検証にならないようにする。M5 bar timestamp や entry 判定時刻の意味も、docs 上で区別して管理する。

## 7. 実注文系との分離
現時点の Execution は dry-run / backtest 用の skeleton を中心に扱う。

以下は未実装である。
- 実際の取引システムとの接続
- 注文送信機能
- 約定応答の本格処理
- 実運用監視・通知・復旧

外部説明では、dry-run と実運用を明確に区別する。
