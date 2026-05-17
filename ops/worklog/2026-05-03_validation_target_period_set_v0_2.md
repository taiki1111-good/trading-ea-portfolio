# 2026-05-03 Validation Target Period Set v0.2

## 対象期間
- OOS-1: `2024-07`, `2024-08`, `2024-09`
- OOS-2: `2024-10`, `2024-11`, `2024-12`
- representative month: `2024-11`
- additional check 候補: `2024-08`, `2024-12`
- holdout候補: 後続で未使用期間を指定

## period_type候補
- `representative_month`
- `confirmation_month`
- `adverse_candidate_month`
- `positive_candidate_month`
- `holdout_candidate`
- `diagnostic_reference_month`

## 各レイヤーの複数月確認方針
- HTF v2: label分布とentry損益を複数月で確認。
- SR v2 rolling high/low: `sr_proximity_flag` の損益傾向を複数月で確認。
- Session v2: `session_label` / `low_liquidity` / `hour_utc` を複数月で確認。
- Risk/Stop v2: 良好月だけでなく悪化月/連敗月で確認。
- Halt/Risk: F候補を確認する場合は対象月を事前固定。
- Exit policy: `simple/conservative/next_bar` の比較対象月を固定。

## holdout方針
- すぐに全期間を使い切らない。
- 本採用候補が出るまで未使用期間を残す。
- holdoutを閾値調整に使わない。
- holdout結果が悪ければ採用を見送る。

## 未解決事項
- adverse_month の定量選定基準
- positive_month の定量選定基準
- holdout期間の最終指定
- cost-adjusted結果を対象月分類に使うか
- max_drawdown正式採用時期
- 2024年以外の期間をいつ使うか

## 注意
- backtest再実行・Validation実装・Runner変更・売買ロジック変更・閾値変更は未実施。
