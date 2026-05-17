# 2026-05-03 Minimum Core v0.1 structural validation complete

## cost scenario 結果（representative logs）
前提:
- `slippage_pips_round_turn=0.2`
- `commission_pips_round_turn=0.1`
- `additional_spread_pips=0.0`
- `spread_already_included=true`
- `swap_mode=note_only`

結果（gross/net pips）:
- OOS-1 2024-08:
  - baseline: `-9.0 / -26.1`
  - simple: `123.6 / 106.5`
  - conservative: `69.9 / 52.8`
  - next_bar_activation: `-4.7 / -21.8`
- OOS-2 2024-11:
  - baseline: `12.0 / -6.9`
  - simple: `110.1 / 91.2`
  - conservative: `91.8 / 72.9`
  - next_bar_activation: `17.6 / -1.3`
- OOS-2 2024-12:
  - baseline: `22.0 / -2.0`
  - simple: `66.3 / 42.3`
  - conservative: `50.2 / 26.2`
  - next_bar_activation: `24.6 / 0.6`

## v0.1 完了判断
- conservative は代表3期間すべてで cost控除後も baseline を上回った。
- simple は強いが楽観寄り上限として扱う。
- next_bar_activation は cost控除後に弱く、ストレス軸として扱う。
- 以上により Minimum Core v0.1 は `structural validation complete` として閉じる。

## v0.2 へ移る理由
- v0.1 は最小核の構造検証完了であり、完成EA・収益性確認・実運用可能性確認ではない。
- 未実装裁量・停止条件（H4/H1複合、S/R、ATR/volatility、spread widening halt、session/time、daily/consecutive/drawdown stop、risk sizing）は v0.2 として分離導入する。
