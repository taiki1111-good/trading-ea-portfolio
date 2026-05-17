# 運用設計

## 1. 文書の目的
この文書は、`trading-ea` の運用設計と異常対応ルールを整理する。
本ドキュメントは `docs/02_requirements.md` の品質要求と `docs/06_state_spec.md` の状態設計をつなぎ、運用時の振る舞いを明確にする。

## 2. ログ運用
- 各判断段階で理由と結果を記録する
- `Logger` は少なくとも以下を残す
  - `timestamp`
  - `position_state`
  - `signal_reason`
  - `filter_reason`
  - `execution_reason`
  - `order_result`
  - `fill_price`
  - `trade_id`
  - `transition_reason`
- ログ形式は後続の評価・再現に使える構造とする
- 可能なら CSV / JSON / DB など、読み取りやすい形式で出力する
- `docs/15_non_functional_requirements.md` の説明可能性・運用性観点を満たす
- CSV を初期正式保存形式とし、JSONL は補助形式として位置づける

### 2.1 CSV persistence の運用方針
- 保存単位は `run_id` 単位で分離する
- `run_id` は UTC timestamp に任意ラベルを組み合わせた文字列を想定する
  - 例: `20260501T093000Z_e2e_minimal`
- 保存先は `logs/{run_id}/`
- 初期版の CSV ファイルは以下を分けて保存する
  - `decision_logs.csv`
  - `trade_logs.csv`
  - `state_logs.csv`
  - `event_logs.csv`
- ローテーションは初期版では `run_id` 単位分離のみとする
- サイズ分割 / 日次分割 / 月次分割は TBD とする
- 履歴管理は初期版で自動削除しない
- 保持期間 / 圧縮 / アーカイブは TBD とする
- schema 方針
  - header は `docs/05_variable_spec.md` の正式変数名を優先する
  - datetime は ISO 8601 UTC 文字列とする
  - bool は `true` / `false` とする
  - 欠損値は原則空文字で表現する
  - nested 構造は初期版では flatten して保存する
  - JSONL は nested 構造保持用の補助形式として扱う

## 3. 異常時対応
- 異常検知時は `ERROR` へ遷移させ、安全側の挙動とする
- `ERROR` 発生時は通常の売買ロジックを停止する
- `ERROR` からの復旧は `safe_fallback_completed` を明示的に経由する
- `SUSPENDED` は意図的停止と異常停止の両方を含む
- `SUSPENDED` 中は新規エントリーを行わない
- `ERROR` / `SUSPENDED` の原因は `transition_reason` とログに明示する
- 復旧手順は現時点では未確定 / TBD

## 4. 停止 / 再開ルール
### 停止ルール
- 指標イベント前後は `SUSPENDED` へ遷移する
- `spread` が許容範囲外のときは `SUSPENDED` へ遷移する
- 当日取引回数上限到達時は `SUSPENDED` へ遷移する
- 連敗数上限到達時は `SUSPENDED` へ遷移する
- `ERROR` 発生時は `ERROR` へ遷移する

### 再開ルール
- `SUSPENDED` 解除条件が満たされるまで `IDLE` に戻さない
- `ERROR` から直接 `IDLE` へ戻すのではなく、`SUSPENDED` を経由することを推奨する
- 再開条件の詳細な閾値は未確定 / TBD

## 5. パラメータ変更ルール
- 重要パラメータ変更は `docs/02_requirements.md` / `docs/08_development_plan.md` の設計方針に照らす
- 変更内容は `ops/DECISION_LOG.md` に記録する
- 変更はまず `experiments` で試し、問題なければ本体に反映する
- 実装フェーズでは、`main` と `experiments` の境界を崩さない
- データ依存パラメータは `docs/11_data_source_policy.md` に従い、データ品質が担保されたソースのみで評価する
- 具体的な変更手順は未確定 / TBD

## 6. experiment 採用フロー
- `experiments` で新規パターン候補を記録する
- `docs/experiments/EXPERIMENT_TEMPLATE.md` に従って試験内容を整理する
- 実験結果を `src/experiments/` / `tests/experiments/` で比較可能な形で残す
- 採用判断は `ops/DECISION_LOG.md` に記録する
- 採用候補は本体 `main` に直接混ぜず、段階的に評価する
- `triangle_break` などの追加候補は、現状では本体に含めず `experiments` で先行検証する

## 7. backtest / 構造検証 / 実運用近似 の区別
### backtest
- 過去データを使い、ロジックの挙動と収益特性を評価する
- 設計段階では構造検証と区別し、検証対象と評価目的を明確にする

### 構造検証
- `docs/03_architecture.md` や `docs/04_module_spec.md` で定義した構造が実装どおりに働くかを確認する
- Data の扱い、時間足整合、`third_wave_break` などの構造認識が設計通りに働くかを重点にする
- 実装前後の設計追従性確認が目的である

### 実運用近似
- 実運用の挙動を想定し、データ品質・停止条件・ログ追跡の観点を確認する
- `docs/16_operation_design.md` と `docs/11_data_source_policy.md` の方針を実機に近い形で検証する
- 実装初期段階では、まず構造検証と backtest を重視し、実運用近似は段階的に進める

## 8. 未確定事項
- `SUSPENDED` 解除条件の具体的な閾値は未確定 / TBD
- 異常復旧手順の詳細は未確定 / TBD
- 実運用での監視・通知体制の具体案は未確定 / TBD
- パラメータ変更時の承認フロー詳細は未確定 / TBD
