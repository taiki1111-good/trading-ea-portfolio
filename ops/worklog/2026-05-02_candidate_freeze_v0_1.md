# 2026-05-02 Candidate Freeze v0.1

## 目的
- 探索・構造検証フェーズから、確認用バックテスト前の候補固定（Candidate Freeze v0.1）へ移行する。
- 位置づけは収益性確認ではなく、確認用バックテストの評価設計を成立させるための工程管理。

## なぜ候補固定が必要か
- Q1/Q2 はすでに探索・構造検証に使用した期間であり、ここで結果を見ながら継続的にルール調整すると確認用バックテストの意味が薄れる。
- 候補固定せずに逐次最適化を続けると、比較の独立性が下がり、確認結果を採否判断に使いにくくなる。

## Q1/Q2を探索済み期間として扱う理由
- Q1/Q2 で entry / exit / HTF alignment policy の候補比較を実施済み。
- Q2 では strict=OFF一致、permissive は neutral 通過による entry 前倒し/追加を確認済み。
- これらの観察を反映したうえで、次は未使用期間で確認用バックテストを行う。

## Candidate Freeze v0.1 固定内容
- Entry設定:
  - `third_wave_break`
  - `detector_chain_temporal`
  - heuristic fallback OFF
  - `third_candidate_lookback_bars=5`
  - `max_entries_per_recent_third_candidate=1`
  - `entry_time_mode=m5_close`
- Exit比較候補:
  - `fixed_sl_tp`（baseline）
  - `simple_trailing_after_1R`（experimental exit candidate, 本採用ではない）
- HTF alignment policy比較候補:
  - OFF/default
  - permissive

## 後回し・除外候補（v0.1）
- strict（Q2でOFF一致。確認用BT主軸から外すが将来仕様比較候補として保持）
- H4
- support/resistance
- H1&H4 aligned
- H4 bias + H1 context
- 追加のexit改造
- swing-based trailing
- trend-break exit

## 確認用バックテスト運用方針
- 確認用期間の結果を見て、その場でルール変更しない。
- 崩れた場合は「候補棄却または再設計理由」として記録する。
- 逐次調整を行う場合は別バージョンとして分離記録し、元の確認用バックテスト系列とは混在させない。
- 重いbacktest実行はユーザーがローカルPowerShellで実施する。
