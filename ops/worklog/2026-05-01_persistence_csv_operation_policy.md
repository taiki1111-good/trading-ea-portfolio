# 2026-05-01 Persistence CSV Operation Policy

## Purpose
- CSV persistence の最小運用仕様を整理し、`docs/05_variable_spec.md` の初期正式保存形式方針と整合させる。
- Logger -> CSV Persistence -> Evaluator の責務分離を確認し、運用設計に必要な命名・保存先・ローテーション・履歴管理方針を定義する。

## CSV operation policy
- 保存単位は `run_id` 単位でログを分離する。
- `run_id` は UTC timestamp と任意ラベルを組み合わせた文字列を想定する。
  - 例: `20260501T093000Z_e2e_minimal`
- 保存先ディレクトリは `logs/{run_id}/` とする。
- CSV ファイルは以下を別々に保存する。
  - `decision_logs.csv`
  - `trade_logs.csv`
  - `state_logs.csv`
  - `event_logs.csv`
- 初期版のローテーションは `run_id` 単位の分離のみとする。
- サイズ分割 / 日次分割 / 月次分割は現時点では未採用 / TBD とする。
- 履歴管理は初期版で自動削除しない。
- 保持期間 / 圧縮 / アーカイブは TBD とする。

## schema policy
- CSV header は `docs/05_variable_spec.md` の正式変数名を優先する。
- datetime は ISO 8601 UTC 文字列とする。
- bool は `true` / `false` で表現する。
- 欠損値は原則空文字で表現する。
- nested 構造は初期版では flatten して保存する。
- JSONL は nested 構造保持用の補助形式として扱う。

## JSONL positioning
- JSONL は正式最低方針ではなく、補助形式 / 将来候補として位置づける。
- JSONL は nested 構造の保持や補助的なインポート/エクスポート用途に使う。
- 初期保存・集計経路は CSV が主流であり、JSONL は必要に応じて追加で扱う。

## Notes
- Logger は保存責務を持たず、レコード生成のみに専念する。
- Evaluator は直接ファイル I/O を持たず、読込済み dict を受け取って集計する。
- persistence が保存・読込境界を担い、Logger / Evaluator の責務を分離する。

## Open / TBD
- `run_id` の生成命名規則を具体化する必要がある（UTC 時刻 + ラベル形式の細部）。
- CSV schema validation の最小実装と schema drift 検出ルールは未確定。
- 保存ファイルの archive / retention policy は今後検討とする。
- JSONL 補助形式の利用要件も検討継続とする。

## Next action
- CSV schema validation の最小実装検討
- `run_id` 命名規則の具体化
- portfolio / documentation 整理
- experiments 採用基準の追加検討
