# 2026-05-03 Halt diagnostic filter toggle CLI

## 1. 追加理由
- OOS-2 2024-11 初回診断で `halt_window_count=87`、`halted_entry_count=23`、`halt_reason_counts=price_shock_halt:44|volatility_spike_halt:75` となり、どちらの filter が過剰停止へ寄与しているか分離確認が必要になった。
- Phase 3 本体統合前に、Phase 2 内で寄与分解を行うための操作スイッチが必要。

## 2. 実装方針
- `--enable-price-shock` / `--enable-volatility-spike` を追加。
- 両方未指定時は後方互換として両方有効（既存挙動維持）。
- 片方のみ指定時は指定 filter のみ診断。
- summary csv/md/stdout に `enabled_filters` を記録。

## 3. 注意
- 本変更は診断運用の分離のためであり、閾値調整や本体統合を目的としない。
- これは構造診断であり、収益性確認を意味しない。
