# 2026-05-01 Backtest Pipeline Adapter LTF/Signal Integration

## Summary
- `PipelineAdapter` の LTF 構造生成を既存部品ベースへ更新。
  - `SwingExtractor.extract`
  - `WaveClassifier.classify`
  - `BreakoutDetector.detect`
  - `TriangleDetector.detect`
  - `StructureAssembler.assemble`
- Signal 判定を既存部品ベースへ更新。
  - `DirectionAlignChecker.check`
  - `PatternGate.check`
  - `EntryRuleEngine.evaluate`
  - `ExitRuleEngine.evaluate`
  - `SignalAssembler.assemble`
- RiskFilter は `RiskAssembler.assemble` を継続使用。
- integration テストを、provider 内で `PipelineAdapter` を直接呼ぶ形に更新。

## Design Notes
- future leak 防止のため `PipelineAdapter` は `window` のみ受け取り、`current_index == len(window)-1` を強制。
- `trade_ok=true` のときのみ `EntryEvent` を返す。
- `entry_reason` は `signal_reason / risk_reason / filter_reason` を連結し、追跡可能にする。
- detector 出力が疎なケースに備えて、初期段階では最小 fallback 構造判定を残す（TODO: 将来削除）。

## Test Updates
- unit:
  - `entry_reason` が `risk_reason` / `filter_reason` を追跡できることを確認
- integration:
  - precomputed events を廃止し、BacktestRunner provider 内で adapter を直接呼ぶ

## Scope
- walk-forward 実装なし
- ML 学習なし
- 実 broker / OANDA API / 実注文送信なし
- 本格スリッページ / 手数料 / swap なし
