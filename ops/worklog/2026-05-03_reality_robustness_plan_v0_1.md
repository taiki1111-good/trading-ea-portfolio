# 2026-05-03 reality robustness plan v0.1

## 背景
- Candidate Freeze v0.1 は OOS-1（2024-07-01〜2024-10-01）/ OOS-2（2024-10-01〜2025-01-01）で棄却されなかった。
- `simple_trailing_after_1R` は `fixed_sl_tp` を一貫して上回り、permissive + trailing は OFF + trailing を小幅に上回った。
- schema / consistency は valid だった。
- ただし、これは本採用・収益性確認・実運用可能性確認を意味しない。

## OOS後に現実耐性確認へ移る理由
- M5 experimental結果には bar内約定仮定の楽観性が残る可能性がある。
- trailing優位が戦略構造由来か、約定仮定由来かを分離して確認する必要がある。
- spread=0.2 pips fallback、手数料・スリッページ・スワップ未反映の前提を見直し、より現実的な比較条件へ進める必要がある。

## 現実耐性確認計画 v0.1 の方針
- Candidate Freeze v0.1 の売買ルールは変更しない。
- `simple_trailing_after_1R` / permissive を本採用扱いしない。
- 新ロジック追加より先に現候補の耐性確認を優先する。
- 重い backtest 実行はユーザーのローカル PowerShell で行う。
