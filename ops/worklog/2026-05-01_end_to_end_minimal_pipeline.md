# 2026-05-01 End-to-End Minimal Pipeline

## Summary
- 実装: `tests/integration/test_end_to_end_minimal_pipeline.py` を追加し、`Data -> HTFContext -> LTFStructure -> Signal -> RiskFilter -> Execution -> Logger -> Evaluator` の最小骨組みエンドツーエンドフローを検証。
- 結果: `pytest -q` で `127 passed` を確認。

## 変更点
- E2E 用 CSV フィクスチャ `tests/fixtures/price_e2e_minimal.csv` を追加。
- 既存の logger/evaluator skeleton を接続し、最小限のログ記録と評価集計を辿れるようにした。
- Execution の状態遷移は dry-run skeleton の暫定簡略化（`IDLE` 起点中心、正式イベント駆動遷移は未収束）として扱い、次段で `docs/06_state_spec.md` へ収束予定。
- `ops/CURRENT_TASKS.md` を更新し、E2E 統合テストの完了と次優先事項を反映。

## 次の作業
1. E2E テストのレビュー反映
2. `Execution` の状態遷移と `docs/06` の整合化
3. 永続化 / 可視化境界の最小設計検討
