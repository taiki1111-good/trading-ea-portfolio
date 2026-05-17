# 2026-05-03 Validation Framework v0.2 design start

## Phase 7からPhase 8へ進む理由
- Phase 4〜7で diagnostic/counterfactual を実施したが、代表月単独での本採用根拠は不十分。
- 個別月の結果に反応した逐次調整を避けるため、複数月・複数条件・複数評価軸の検証枠組みを先に固定する。

## 設計方針
- 収益性断定ではなく、構造安定性・副作用・再現性を評価する。
- OOS月、悪化月、良好月、holdout を分離して評価する。
- 同じOOSを見ながら閾値を逐次変更しない。
- 過剰最適化を避けるため、判断カテゴリとGo/No-Go基準を明示する。

## 各レイヤーの現在ステータス
- HTF v2: diagnostic/explanation layer（filter化保留）
- SR v2 rolling high/low: breakout近接ラベル（filter化保留）
- reaction SR: future candidate
- Session v2: UTC固定近似diagnostic label（filter化保留）
- Risk/Stop v2: 代表月では統合根拠不足、悪化月で再確認候補
- Halt/Risk: Phase 2でNo-Go、一時保留

## 禁止事項（今回）
- backtest再実行をしない。
- Validation framework本体実装をしない。
- BacktestRunner / PipelineAdapter を変更しない。
- 売買ロジックを変更しない。
- HTF/SR/Session/RiskStopをfilter化しない。
- 閾値を本採用扱いしない。
- logs や data/private をGit追加しない。
- 収益性確認済みのように扱わない。

## 未解決事項
- validation対象月セット
- 悪化月の選び方
- walk-forward window長
- holdout期間定義
- max_drawdown正式導入時期
- cost-adjusted logsの標準化可否
- OANDA near-live logs接続タイミング
