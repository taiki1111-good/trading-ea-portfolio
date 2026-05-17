# 2026-05-03 Phase 7 Risk Management / Stop Controls v0.2 design start

## Phase 6からPhase 7へ進む理由
- Phase 4 HTF v2、Phase 5 SR v2、Phase 6 Session v2 はいずれも diagnostic/explanation layer として整理済み。
- 代表月では実filter化の根拠が不十分で、entryを止める判断には至っていない。
- 次段階として、entryの良し悪しではなく「EA全体の損失拡大抑制」を扱う Phase 7 を設計する。

## 設計方針
- Risk/Stopはまず既存 `trade_logs` の後処理診断で評価する。
- 初期は counterfactual 中心（避けた損失 / 逃した利益 / 純効果）で確認する。
- `BacktestRunner` / `PipelineAdapter` への停止統合は実装前設計段階では行わない。
- 閾値は初期仮説であり、本採用値として確定しない。
- 結果に合わせた逐次調整を行わない。

## 対象候補（設計スコープ）
- daily_loss_stop
- consecutive_loss_stop
- drawdown_stop
- max_trades_per_day
- cooldown_after_loss
- risk_per_trade
- lot sizing
- equity/balance curve tracking
- stop_resume_rule

## 禁止事項（今回）
- backtest再実行をしない。
- Risk/Stop本体を実装しない。
- BacktestRunner / PipelineAdapterを変更しない。
- 売買ロジックを変更しない。
- lot sizingを実装しない。
- HTF/SR/Sessionをfilter化しない。
- 閾値を本採用扱いしない。
- logs や data/private をGit追加しない。
- 収益性確認済みのように扱わない。

## 未解決事項
- pips基準 / R基準 / 金額基準の優先軸。
- lot sizing導入前の評価限界。
- daily boundary（UTC/JST/NY close）の採用方針。
- open position強制決済を含めるか。
- stop後の再開条件。
- swap/commission/slippage反映後の再評価要否。
