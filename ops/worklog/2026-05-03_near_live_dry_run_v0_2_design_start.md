# 2026-05-03 near-live / dry-run v0.2 design start

## Phase 8からPhase 9へ進む理由
- Phase 8で最小validation summary生成まで完了し、各レイヤーの現状判断を記録済み。
- 次段階では、実注文前に「逐次処理での運用整合性」と「ログ追跡性」を確認する必要がある。
- そのため near-live / dry-run の実装前設計を先に固定する。

## 設計方針
- 実注文・デモ注文・OANDA接続は行わない。
- CSV replay または疑似streamで bar を1本ずつ処理し、paper decision を記録する。
- 収益性ではなく、ログ完全性・時刻整合性・停止判断の追跡可能性を評価する。
- Backtest一致率より「差分の説明可能性」を重視する。

## 禁止事項（今回）
- OANDA/API接続を実装しない。
- 実注文・デモ注文を送らない。
- near-live本体を実装しない。
- BacktestRunner / PipelineAdapter を変更しない。
- 売買ロジックを変更しない。
- HTF/SR/Session/RiskStop/Halt をfilter化しない。
- 閾値を本採用扱いしない。
- logsやdata/privateをGit追加しない。
- 収益性確認済みのように扱わない。

## 未解決事項
- OANDA API接続タイミング
- CSV replay dry-runを先に作るか
- 疑似stream入力形式
- paper position管理の粒度
- spread/slippage/swapの扱い
- dry-runログ保存場所
- 実デモ注文へ進む条件
- エラー時停止/再開方針
