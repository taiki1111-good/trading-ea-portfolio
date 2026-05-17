# 2026-05-15 reason category analysis application plan

## 1. 目的
- `normalize_reason_categories()` を Evaluator/分析スクリプト側にどう適用するかを、実装前に固定する。
- 今回は docs/ops 計画化のみ（`src/` / `scripts/` 実装変更なし）。

## 2. 現状調査
### 2.1 reason列を読む箇所
- Evaluator:
  - `src/evaluator/filter_analyzer.py`
    - `filter_reason` をそのまま bucket key に利用。
- analysis script:
  - `scripts/analyze_backtest_run_logs.py`
    - `risk_reason` / `filter_reason` は欠損カウントのみ。
    - `exit_reason` は `Counter` で完全一致集計。
- dry-run scripts:
  - `scripts/run_csv_replay_pipeline_dry_run.py`
    - `signal_reason` / `filter_reason` / `decision_reason` をログ出力。
  - `scripts/summarize_csv_replay_dry_run.py`
    - reason語彙集計は未実施（status系のみ）。

### 2.2 完全一致依存
- `FilterAnalyzer` は `filter_reason` 文字列完全一致で bucket 化している。
- `analyze_backtest_run_logs.py` は `exit_reason` で完全一致 `Counter` を使うが、`risk_reason` / `filter_reason` の語彙集計は未実装。

### 2.3 `|` 連結の発生箇所
- `risk_reason` は `RiskAssembler` 成功時に `fixed_sl_tp | placeholder_fixed_lot` 形式になりうる。
- `filter_reason` は基本単一寄りだが、将来複数連結を許容する運用方針。

## 3. 方針判断（最終）
### 3.1 適用スコープ
- **第1段階は analysis script 側限定**。
- Evaluator本体（`FilterAnalyzer` の key 仕様変更）は第2段階候補として後続。

### 3.2 列運用
- 既存列は置換しない。
- 追加は派生列のみ。
- 元列（`risk_reason` / `filter_reason` / `decision_reason`）は保持。

### 3.3 保存形式
- category list は CSV互換優先で `|` 区切り文字列を採用。
- JSON文字列は今回は不採用（可読性・既存CSV運用優先）。

### 3.4 primary category
- ルール: `normalize_reason_categories()` の先頭要素を primary とする。
- 空配列時は `unknown` を使用。

## 4. 派生列案（第1段階）
- `risk_reason_categories`（`|` 連結文字列）
- `filter_reason_categories`（`|` 連結文字列）
- `risk_reason_primary_category`
- `filter_reason_primary_category`

補足:
- 内部処理では list で扱い、CSV出力時に `|` 連結へ変換。

## 5. 実装対象優先順位
1. `scripts/analyze_backtest_run_logs.py`
   - reason派生列作成 + category集計（missing count は現行維持）
2. （必要なら）`scripts/run_csv_replay_pipeline_dry_run.py` の後処理段
   - ただし今回は非対象。まず既存ログを analysis 側で読む。
3. `src/evaluator/filter_analyzer.py` の category基準化
   - 第2段階（互換比較付き）で着手。

## 6. テスト方針（次実装フェーズ向け）
- unit（script helper）:
  - 単一reason / `|` 連結reason / legacy reason / 空文字の category list 化。
- regression:
  - 既存 `trade_log_analysis.csv/.md` の既存項目を壊さない。
- compatibility:
  - 元列保持（置換なし）を確認。
- non-scope:
  - 売買ロジック、`trade_ok`、PipelineAdapter 挙動は不変確認のみ。

## 7. 互換ポリシー（analysis適用段）
- 互換保証の主対象は category token。
- detail は移行対象で新旧混在を許容。
- 完全一致比較は非推奨、category抽出を優先。

## 8. 未解決点
- Evaluator本体に category基準集計をいつ入れるか。
- canonical出力（`all_risk_filters_passed`）への段階移行時期。
- detail旧形式の廃止時期。

## 9. 次フェーズ実装プロンプト案
- 目的:
  - `scripts/analyze_backtest_run_logs.py` に Reason Catalog 派生列を追加し、categoryベース集計を導入する。
- 変更範囲:
  - script内 helper を追加（`normalize_reason_categories` 呼び出し）。
  - `risk_reason_categories` / `filter_reason_categories` / primary category 列を analysis出力へ追加。
  - 既存列と既存メトリクスは維持。
- 非変更:
  - `src/evaluator/` 本体、`src/backtest/`、`src/risk_filter/`、売買ロジック。
- 検証:
  - targeted pytest + sample log analysis 実行で既存項目非破壊を確認。

