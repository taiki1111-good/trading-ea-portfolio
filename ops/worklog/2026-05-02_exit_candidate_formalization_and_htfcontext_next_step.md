# 2026-05-02 exit candidate formalization and HTFContext next step

## 判断ログ（短縮）
- Q1/Q2 experimental exit comparison と M1 replay を踏まえ、`simple_trailing_after_1R` は本採用ではなく「有力な experimental exit candidate」として扱う方針を明記。
- M1 replay では本体 trailing 優位を確認した一方、`conservative` / `next_bar_activation` が弱く、約定仮定・発動タイミング依存の検証余地が残る点を明記。
- 次工程は HTFContext 本格導入比較を中心に進め、entry 側課題と exit 側課題を分離して評価する。
- 追加タスクとして Q3以降 out-of-sample 候補計画化、および 2024-06 run 開始時刻ずれ（`2024-06-02T17:00:00+00:00`）のデータ確認を登録。
- 本フェーズは構造検証であり、収益性確認ではない。前提は spread=0.2 pips fallback、手数料/スリッページ/スワップ未反映。
