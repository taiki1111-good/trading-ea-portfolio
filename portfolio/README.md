# Portfolio README

このディレクトリは、`trading-ea` の外部説明用サマリーを作るための作業用下書き・補助資料領域です。
対象は「収益性確認済みEA」ではなく、設計・検証・説明可能性を重視した分析/検証基盤としての到達点です。

注意:
- Source of Truth は `ops/CURRENT_TASKS.md` と `docs/` を優先します。
- ここに記載する内容は、実装済み / 検証済み / 未実装を分けて記述します。

現時点で外部説明に必ず含める前提:
- 実 broker / OANDA API / 実注文送信は未実装
- 収益性評価ではない
- `PositionSizer` は placeholder（lot sizing本体は未接続）
- HTF は diagnostic comparison v0 を完了（本体filter採用ではない）
- lot sizing は shadow comparison tool（diagnostic用途）として採用
