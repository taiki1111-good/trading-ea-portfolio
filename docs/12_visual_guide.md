# 理解補助図ガイド

## 1. 目的
この文書は、`trading-ea` の設計理解を補助するための図ドキュメントへの入口である。  
ここで示す図は説明補助であり、仕様の正本は既存 docs 群とする。

## 2. 前提
- core spec は変更しない
- 判断・契約・命名は正本 docs を優先する
- 図と説明文の不一致があれば、正本 docs を採用する

## 3. 図ドキュメント一覧
- [01_system_flow.md](./diagrams/01_system_flow.md): 上位モジュール間の全体フロー
- [02_module_map.md](./diagrams/02_module_map.md): 上位モジュールと下位部品の分解
- [03_state_transitions.md](./diagrams/03_state_transitions.md): `position_state` の基本遷移
- [04_data_pipeline.md](./diagrams/04_data_pipeline.md): データ形式・検証・受け渡しの流れ
- [05_test_map.md](./diagrams/05_test_map.md): モジュールと契約テスト観点の対応
- [06_ai_workflow.md](./diagrams/06_ai_workflow.md): AI/Human の運用ワークフロー

## 4. 推奨閲覧順
1. `01_system_flow.md`
2. `02_module_map.md`
3. `04_data_pipeline.md`
4. `03_state_transitions.md`
5. `05_test_map.md`
6. `06_ai_workflow.md`

## 5. 参照元（正本）
- `docs/01_overview.md`
- `docs/03_architecture.md`
- `docs/04_module_spec.md`
- `docs/05_variable_spec.md`
- `docs/06_state_spec.md`
- `docs/07_test_plan.md`
- `docs/10_interface_contract.md`
- `docs/11_data_source_policy.md`
- `ops/AGENT_WORKFLOW.md`
- `ops/CURRENT_TASKS.md`
