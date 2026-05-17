# 2026-05-02 Confirmation Backtest Acceptance Criteria v0.1

## 目的
- Confirmation Backtest Design v0.1 に、OOS-1（2024-07-01〜2024-10-01）向けの合否判定基準を明文化する。
- 収益性確認ではなく、次段階へ残す価値の判定基準として扱う。

## 前提
- Candidate Freeze v0.1 は完了済み。
- Q1/Q2 は探索済み期間。
- 比較条件は OFF/permissive × fixed/trailing の4条件。
- 結果を見て即時ルール変更しない。
- 悪化時は v0.1 棄却または v0.2 再設計候補として記録する。

## OOS-1 合否判定基準
- 必須:
  - 全4条件runで schema / consistency が valid。
- exit比較:
  - OOS-1合計で trailing が fixed より良いか。
  - 月別（7月/8月/9月）で 2/3 以上 trailing が fixed より良いか。
- policy比較:
  - OOS-1合計で permissive + trailing が OFF + trailing と同等以上か。
  - 月別（7月/8月/9月）で 2/3 以上 permissive + trailing が OFF + trailing と同等以上か。
- 注意:
  - trade_count が少なすぎる場合は判断保留。
  - 1か月だけに依存する場合は要注意。
  - entry集合差分、neutral_passed_count、shifted_5min_count を併記確認。
- 失敗時:
  - 即時修正しない。v0.1棄却またはv0.2再設計候補として記録する。

## 実行運用
- 重いbacktestはユーザーがローカルPowerShellで実行。
- Codexは実行手順整理・結果整理・判定ログ記録を担当。
