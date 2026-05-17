# 2026-05-03 Session/Time Filter v0.2 Design Start

## Phase 5 から Phase 6 へ進む理由
- Phase 5 SR v0.2（rolling high/low）は `diagnostic_only` 代表月分析で `sr_proximity_flag=True` 側が悪化群ではなかった。
- rolling high/low SR は実filter化を保留し、diagnostic/explanation layer 継続とした。
- SR概念は rolling high/low 型と reaction SR 型に分離済みで、reaction SR は後続候補として保持中。
- Roadmap順序に沿い、次候補として Phase 6 Session/Time filter の実装前設計を整理する。

## 設計方針（実装前）
- 初期は `diagnostic_only` とし、entryを止めない。
- 内部基準はUTC固定、JSTは表示補助として扱う。
- session/time label を `decision_logs` に出力し、分類別損益で有効性を確認する。
- 実filter化判断は複数月確認後に行う。

## 禁止事項（本タスク）
- backtest再実行をしない。
- Session filter本体実装をしない。
- PipelineAdapter変更をしない。
- 売買ロジック変更をしない。
- SR/HTFをfilter化しない。
- 閾値を本採用扱いしない。

## 未解決事項
- session境界時刻の定義（Tokyo/London/New York/overlap）。
- DSTの扱い。
- JST表示列を入れるか。
- low liquidity hour の初期定義。
- event halt や既存halt診断との責務境界。
