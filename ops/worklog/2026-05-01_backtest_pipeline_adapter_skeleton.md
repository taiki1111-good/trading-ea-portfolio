# 2026-05-01 Backtest Pipeline Adapter Skeleton

## Summary
- `src/backtest/pipeline_adapter.py` を追加し、BacktestRunner の `entry_event_provider` として渡せる最小 adapter を実装。
- adapter は `bars[:i+1]` を受け取り、`HTFContext -> LTFStructure -> Signal -> RiskFilter` を順に接続する。
- `trade_ok=true` の場合のみ `EntryEvent` を返し、`lot / stop_loss / take_profit` は RiskFilter 出力を利用。
- `entry_reason` は `signal_reason / risk_reason / filter_reason` を連結して生成。

## Leak Prevention
- adapter は全 bars を受け取らず、window のみ受け取る。
- `current_index == len(window)-1` を強制し、future bar 混入時は `ValueError` を返す。
- HTF/LTF/Signal/RiskFilter 実行は window 内データのみで実施。

## Test Scope
- unit:
  - `trade_ok=false` で `None`
  - `trade_ok=true` で `EntryEvent`
  - long/short 方向反映
  - `lot / stop_loss / take_profit` の反映
  - `entry_reason` 非空
  - future bar 混入検知
- integration:
  - fixture 読み込み
  - 各 step で `window=bars[:i+1]` を渡して event 生成
  - event を provider 経由で BacktestRunner に渡し、接続確認（本格収益評価は対象外）

## Notes
- `entry_event_provider` は削除せず、unit/scenario 補助として維持。
- walk-forward / ML / 実 broker 接続 / 本格最適化は対象外。
