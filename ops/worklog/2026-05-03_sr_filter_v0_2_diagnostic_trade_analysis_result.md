# 2026-05-03 SR Filter v0.2 diagnostic trade analysis result

## 対象run
- `run_id: oos2_202411_sr_v2_diag_trailing_matched`
- `trade_count=64`
- `total_pnl=0.29010000000004366`

## matched run確認
- 条件を揃えた run で `trade_count=64` / `total_pnl=0.2901` に復帰。
- SR v2 `diagnostic_only` は entry を変更していない。
- entry 64件すべてで `sr_data_valid_flag=True` を確認。

## 集計結果
`sr_proximity_flag`:
- `false`: `trade_count=47`, `total_pnl=0.1616`, `average_pnl=0.0034382979`, `win_rate=0.851064`
- `true`: `trade_count=17`, `total_pnl=0.1285`, `average_pnl=0.0075588235`, `win_rate=0.823529`

`sr_block_side`:
- `none`: `trade_count=47`, `total_pnl=0.1616`, `average_pnl=0.0034382979`, `win_rate=0.851064`
- `resistance`: `trade_count=12`, `total_pnl=0.0371`, `average_pnl=0.0030916667`, `win_rate=0.750000`
- `support`: `trade_count=5`, `total_pnl=0.0914`, `average_pnl=0.0182800000`, `win_rate=1.000000`

`sr_counterfactual_group`:
- `sr_long_near_resistance`: `trade_count=12`, `total_pnl=0.0371`, `average_pnl=0.0030916667`, `win_rate=0.750000`
- `sr_long_not_near_resistance`: `trade_count=25`, `total_pnl=0.0789`, `average_pnl=0.0031560000`, `win_rate=0.880000`
- `sr_short_near_support`: `trade_count=5`, `total_pnl=0.0914`, `average_pnl=0.0182800000`, `win_rate=1.000000`
- `sr_short_not_near_support`: `trade_count=22`, `total_pnl=0.0827`, `average_pnl=0.0037590909`, `win_rate=0.818182`

## 解釈
- `sr_proximity_flag=True` 側は悪化群ではない。
- `true` 側は勝率はやや低いが `average_pnl` は `false` 側より高い。
- `resistance` 近接は監視価値はあるが、`total_pnl` がプラスのため即除外不可。
- `support` 近接は代表月では強い利益源であり除外不可。
- 現在の `rolling high/low` SR は反発型SRではなく、breakout近接ラベルとして機能している可能性がある。

## 判断
- 現時点では SR v2 rolling high/low を実filter化しない。
- SR v2 は diagnostic/explanation layer として継続する。
- 代表月単独で本採用・棄却は判断しない。
- `window=48` と `near_threshold_pips=10.0` は本採用値扱いせず、結果合わせ調整を行わない。

## 未解決事項
- 反発型SRを別定義（swing由来や上位足高安）として分離するか。
- `resistance` 近接の勝率低下が再現するか（複数月確認）。
- `support` 近接の高収益が再現するか（複数月確認）。
