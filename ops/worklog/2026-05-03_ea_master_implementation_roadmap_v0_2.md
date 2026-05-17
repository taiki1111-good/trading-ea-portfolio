# 2026-05-03 EA Master Implementation Roadmap v0.2+

## 1. 実施内容
- `docs/17_backtest_design.md` に **EA Master Implementation Roadmap v0.2+**（Phase 0〜9）を追加。
- `docs/ops/EA_MASTER_IMPLEMENTATION_ROADMAP_v0_2_plus.md` を新規作成し、v0.2 以降の実装順序・検証順序・完了条件を固定化。
- `docs/08_development_plan.md` に、初期計画維持と v0.2+ 参照先を追記。
- `ops/CURRENT_TASKS.md` を「EA Master Implementation Roadmap v0.2+ 整備」へ更新。

## 2. 統合ロードマップが必要な理由
- Minimum Core v0.1 の structural validation complete 後に、追加裁量・停止条件・検証順序が会話単位で変動すると、比較条件がぶれやすい。
- Halt/Risk/HTF/SR/Session/RiskManagement の導入順を固定しないと、検証結果の解釈が混線する。
- v0.1 の結果と v0.2 以降の結果を明確に分離し、段階ごとの完了条件を固定する必要がある。

## 3. 今後の進め方（固定方針）
- 今後は場当たり的な順序決定を行わず、Roadmap の Phase 順で進行する。
- 診断可能な停止条件は本体統合前に診断スクリプトで評価する。
- 閾値は初期仮説として固定し、結果を見た都度調整は行わない。
- 閾値再調整が必要な場合は v0.3 など別バージョンとして分離する。
