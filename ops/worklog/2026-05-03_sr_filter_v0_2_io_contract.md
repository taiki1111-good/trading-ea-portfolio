# 2026-05-03 SR Filter v0.2 I/O Contract

## 目的
- Phase 5 Support/Resistance filter v0.2 の実装前段階として、SR v0.2 I/O Contract と Diagnostic Policy を固定する。
- 今回は設計契約の明文化に限定し、backtest実行・SR実装・PipelineAdapter変更・売買ロジック変更・HTF v2 filter化は行わない。

## 重要前提
- 実 broker / OANDA API / 実注文送信は未実装。
- 収益性確認済みではない。
- SR filterは本採用ではない。
- HTF v2 は diagnostic/explanation layer として継続する。

## SR v0.2 初期定義
- 初期実装候補は `fixed window rolling high / low` を優先。
- 理由:
  - swing判定より実装が単純。
  - future leak監査が容易。
  - diagnostic_onlyで分布確認に向く。
- `recent swing high/low` と `H1/H4 recent high/low` は後続候補として保持。
- 初期定義は本採用扱いしない。

## I/O Contract
入力:
- M5 bars
- existing entry signal / trade logs
- optional HTF v2 labels
- sr_v2 config

Config候補:
- `sr_v2_enabled: bool = False`
- `sr_v2_policy: diagnostic_only`
- `sr_v2_window_bars: int = 48`
- `sr_v2_near_threshold_pips: float = 10.0`
- `sr_v2_pip_size: float = 0.01`
- `sr_v2_use_atr_normalized: bool = False`

rolling high/low 計算方針:
- `resistance` は entry判定時点より前の直近N本 high 最大値。
- `support` は entry判定時点より前の直近N本 low 最小値。
- current bar と未来barは不使用。
- N本不足時は `sr_data_valid_flag=False`。
- 距離は entry判定時点の close または entry予定価格基準で算出。

direction別判定:
- long候補: `nearest_resistance_distance_pips <= threshold` で `sr_proximity_flag=True`、`sr_block_side=resistance`。
- short候補: `nearest_support_distance_pips <= threshold` で `sr_proximity_flag=True`、`sr_block_side=support`。
- 逆側SRは初期block対象外。
- range boundaryは両側距離を記録するが、初期filter判定には使わない。

出力列候補:
- `sr_v2_enabled`
- `sr_policy`
- `sr_window_bars`
- `nearest_resistance`
- `nearest_support`
- `nearest_resistance_distance_pips`
- `nearest_support_distance_pips`
- `sr_proximity_flag`
- `sr_block_side`
- `sr_reason`
- `sr_data_valid_flag`
- `sr_counterfactual_group`

## Diagnostic Policy
- `diagnostic_only` を採用し、`entry_signal` / `trade_ok` は変更しない。
- `sr_proximity_flag` は仮想的な「止める候補」タグとしてのみ出力。
- `sr_reason` に `diagnostic_only:no_entry_filter` を含める。
- 実filter化は後続判断とする。

## Future Leak 防止方針
- entry時点以前に確定済みのM5 barのみ使用。
- current bar以降のhigh/lowをSR計算に使わない。
- H1/H4 SRを導入する場合も確定済みHTF barのみ使用。
- rolling window は `timestamp < current decision timestamp` のbarで構成。

## Go/No-Go 方針
- 代表月だけでfilter化しない。
- `sr_proximity_flag=True` 側が明確に悪い場合のみ次の診断候補。
- `sr_proximity_flag=True` 側が利益源ならfilter化しない。
- 閾値を結果に合わせて逐次調整しない。
- 複数月確認前に本体filter化しない。

## 未解決事項
- rolling window 初期値 48 の妥当性。
- pips閾値 10.0 の妥当性。
- ATR正規化導入タイミング。
- swing high/low 定義への移行可否。
- HTF v2 との責務境界。
- long/short 閾値の非対称化可否。
