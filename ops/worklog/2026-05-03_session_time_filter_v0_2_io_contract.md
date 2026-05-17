# 2026-05-03 Session/Time Filter v0.2 I/O Contract

## 目的
- Phase 6 Session/Time filter v0.2 の実装前段階として、Session v0.2 I/O Contract と Diagnostic Policy を固定する。
- 今回は設計契約の明文化に限定し、backtest再実行・Session実装・PipelineAdapter変更・売買ロジック変更は行わない。

## session境界（UTC固定近似）
- `tokyo`: `00:00-09:00 UTC`
- `london`: `08:00-17:00 UTC`
- `new_york`: `13:00-22:00 UTC`
- `london_ny_overlap`: `13:00-17:00 UTC`
- `low_liquidity`: `22:00-00:00 UTC` and weekend/market thin periods candidate
- `off_session`: 上記以外
- これらは初期診断ラベルであり、本採用時刻ではない。

## DST方針
- 初期v0.2では London / New York の厳密DST補正は行わない。
- `session_label` は UTC固定近似ラベルとして扱う。
- DST厳密対応は後続候補。
- DST未対応のまま本採用filterにしない。

## diagnostic_only方針
- `entry_signal` / `trade_ok` は変更しない。
- `session_risk_flag` は仮想的な注意ラベル。
- `session_reason` には `diagnostic_only:no_entry_filter` を含める。
- 実filter化は後続判断とする。

## future leak / 時刻解釈
- 内部基準はUTC固定で、`hour_utc` / `day_of_week` を必須出力候補とする。
- JSTは表示補助とし、初期実装では必須列にしない。
- 時刻ラベルは decision timestamp の確定値を使う前提とし、未来時刻情報を使わない。

## 未解決事項
- session境界時刻の最終定義。
- DST厳密対応の導入タイミング。
- JST表示列を入れるか。
- low liquidity hour の厳密定義。
- event haltとの責務境界。
- broker時間/OANDA時間との整合。
