# 2026-04-24 Data Layer Connectivity Skeleton

## 作業内容
- `ops/CURRENT_TASKS.md` を Data 層完了状態に更新し、次の課題として `Data -> HTFContext / LTFStructure` 接続テスト骨組みを明記
- `tests/unit/test_data_module.py` を Data 層全体契約の軽量確認に整理
- `tests/unit/data/` に詳細部品テストを残したまま、重複を削減
- `tests/fixtures/` の `spread` 単位を pips 前提に統一し、`tests/fixtures/README.md` を追加
- `tests/integration/test_data_to_htf_ltf_connectivity.py` で Data 出力が後続モジュールに渡せる形かを確認する骨組みを追加

## 現状
- Data 骨組み実装は完了
- Data 単体テストは `pytest -q` で実行済み（26 passed）
- HTFContext / LTFStructure の本実装はまだ着手せず

## 次の作業
1. HTFContext / LTFStructure の受け渡し契約を追加で定義
2. `tests/integration/` の骨組みを実装に合わせて拡張
3. `docs/06_state_spec.md` 等と整合させる
