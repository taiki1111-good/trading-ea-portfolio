# 2026-05-03 SR filter v0.2 design start

## 背景
- Minimum Core v0.1 は structural validation complete。
- Phase 2 Halt/Risk は初期候補が net negative で一時保留。
- Phase 4 HTFContext v0.2 は diagnostic/explanation layer として継続。
- HTF v2 aligned_only / pullback_permissive の実filter化は保留。

## Phase 5へ進む理由
- Roadmap順序に従い、次段は Phase 5 Support/Resistance filter。
- ただし現時点は本体統合ではなく、実装前の設計固定を優先する。
- 結果に合わせた閾値最適化を避けるため、先に診断列・評価軸・Go/No-Go基準を明文化する。

## 今回決めるべき事項（実装前設計）
1. SR定義候補（swing起点 / H1H4 high-low / rolling window）の比較枠。
2. diagnostic_only 方針（entryを止めない）。
3. SRログ列候補（distance/proximity/reason/data_valid/counterfactual_group）。
4. future leak 防止規約（確定済みbarのみ使用、未来high/low禁止）。
5. 評価指標とGo/No-Go判断条件（代表月単独でfilter化しない）。

## 禁止事項（この段階）
- backtest再実行しない。
- SR filter本体実装しない。
- PipelineAdapter変更しない。
- 売買ロジック変更しない。
- HTF v2を実filter化しない。
- 閾値を本採用扱いしない。

## 未解決事項
1. SR初期定義を swing由来にするか、H1/H4 high/low由来にするか。
2. ATR正規化を初期から使うか。
3. pips閾値の初期仮説。
4. long/short 非対称設計を採用するか。
5. HTF v2とSRの責務境界。

## 注意
- 実 broker / OANDA API / 実注文送信は未実装。
- これは収益性確認ではない。
