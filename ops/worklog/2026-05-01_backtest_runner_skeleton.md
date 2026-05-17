# 2026-05-01 BacktestRunner skeleton

## 目的
「バックテスト可能な研究用EA」の第一段階として、Backtest 層の下位部品と最小 Runner を追加し、Backtest -> Logger -> Persistence -> Evaluator の接続を確認する。

## 変更点（最小）
- `src/backtest/` を追加
  - `types.py`: Backtest 層の最小 dataclass 群
  - `pnl_calculator.py`: raw price 差分 + lot の簡易PnL
  - `exit_rule_engine.py`: 仮 exit ルール（SL/TP/max_holding_bars、同一バーは stop_loss 優先）
  - `position_tracker.py`: 単一ポジション追跡
  - `backtest_logger_adapter.py`: `BacktestTrade` -> `trade_log dict` 変換（CSV schema 必須列を満たす）
  - `backtest_runner.py`: fixture + entry_event_provider で1件以上の trade を生成できる最小 Runner
- fixtures 追加（最小シナリオ用）
  - long win/loss, short win/loss, max_holding_bars close
- tests 追加
  - unit: calculator / exit engine / tracker / adapter / runner
  - integration: trade_logs を CSV persistence に保存し schema validation を通し metrics を計算
  - scenario: long/short の win/loss と max_holding_bars exit を確認

## 前提・制約の保持
- 実 broker / OANDA API / 実注文送信は対象外（実装しない）
- 最適化探索、複数戦略比較、スリッページ/手数料/スワップ本格モデルは対象外
- DataLoader を各バーで再実行しない（検証・正規化済み `price_frame` を受け取る）
- future leak 防止: 各 step は `bars[:i+1]` の範囲のみを利用する前提（Runner 内で window を明示）
- intrabar leak 防止: entry はバー close 約定とみなし、exit 判定は次バー以降から開始（entry 同一バーでは exit しない）

## 残TODO / TBD
- Signal / RiskFilter / Execution と BacktestRunner の本格接続（疑似 entry を排除）
- 実データ（短期）の backtest 実行と結果反映（収益性断定はしない）
- backtest_summary / evaluator_result の正式スキーマ整備
- lot / spread / fee / swap 等の扱い（初期は TODO/TBD のまま）
