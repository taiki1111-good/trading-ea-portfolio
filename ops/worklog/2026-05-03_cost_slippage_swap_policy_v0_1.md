# 2026-05-03 cost slippage swap policy v0.1

## この段階で必要な理由
- Candidate Freeze v0.1 は OOS-1/OOS-2 で structural pass 候補となり、M1 replay で exit 仮定監査を進めた。
- ただし現在の比較は raw price差分中心で、手数料・スリッページ・スワップ未反映のため、現実耐性確認としては不足がある。
- trailing優位がコスト控除後にどこまで残るかを検証するため、cost/slippage/swap 反映方針を先に固定する必要がある。

## v0.1 方針
- 追加ロジック実装ではなく、既存 `trade_logs` / M1 replay summary への後処理評価として扱う。
- BacktestRunner 本体へ直ちに組み込まない。
- USDJPY は `1 pip = 0.01` とし、`pnl_price_diff / 0.01` で pips 換算する。
- spread / commission / slippage / swap を分離し、`gross_pnl -> ... -> net_pnl` の順で控除する。

## 前提維持
- 本記録は本採用・収益性確認・実運用可能性確認ではない。
- Candidate Freeze v0.1 の売買ルールは変更しない。
- `simple_trailing_after_1R` / `simple_trailing_after_1R_conservative` / permissive は本採用扱いしない。
