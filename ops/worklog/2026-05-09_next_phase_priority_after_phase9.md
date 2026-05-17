# 2026-05-09 next phase priority after Phase 9 minimal completion

## 目的
- Phase 9 CSV replay pipeline dry-run minimal completion 後の次フェーズ候補を比較し、優先順位・判断理由・非対応範囲・実装着手条件を整理する。
- 本記録は docs / ops の計画整理であり、実装変更ではない。

## 現状（Phase 9後）
- Phase 9 は minimal completion reached。
- representative run（weekday / weekend expected gap）確認済み。
- 実 broker / OANDA API / 実注文送信は未実装。
- 収益性確認済みではない。
- Session v2 は diagnostic_only 継続（entry を止めない）。
- `pass/warn/fail` は dry-run health / ログ整合判定であり、実運用品質判定ではない。

## 比較候補（A〜F）
### Candidate A: `pipeline_adapter_error` error type別集計追加
- 利点: Phase 9運用の原因切り分けが改善される。
- リスク: 戦略品質や売買挙動改善には直接つながらない。
- 非対応境界: 売買ロジック変更は行わない。

### Candidate B: dry-run artifact 保存・レビュー運用の詳細化
- 利点: 再現性・引き継ぎ性・レビュー効率が上がる。
- リスク: 実装前進ではなく運用整備中心。
- 非対応境界: 実行基盤やbroker接続は扱わない。

### Candidate C: Risk/Stop 本体設計の前段整理
- 利点: exit / risk 管理重視の方針に最も近い。次の実装価値が高い。
- リスク: 売買挙動へ影響する領域のため、受け入れ基準を先に固定しないと設計ブレが出る。
- 非対応境界: いきなり実装・閾値調整は行わない。

### Candidate D: Session / SR / HTF filter化の優先順位整理
- 利点: diagnostic_only から本体適用へ進む前の順序と責務分離を明確化できる。
- リスク: filter化は entry集合に影響するため、順序設計なしで進めると比較不能になりやすい。
- 非対応境界: 本体filter化実装は今回行わない。

### Candidate E: Triangle / Trap / reaction SR など experiments 発展
- 利点: 将来戦略拡張として重要。
- リスク: Phase 9直後の即実装対象にすると main / experiments 境界を崩しやすい。
- 非対応境界: main 導入は行わず experiments 管理を維持する。

### Candidate F: OANDA/API 接続準備
- 利点: 実運用近似へ近づく。
- リスク: 現在の段階（dry-run minimal completion）では時期尚早。安全性・設計固定が先。
- 非対応境界: 後続保持（今回着手しない）。

## 推奨優先順位
1. Candidate C: Risk/Stop 本体設計の前段整理  
2. Candidate D: Session / SR / HTF filter化の優先順位整理  
3. Candidate A: `pipeline_adapter_error` type別集計要否判断  
4. Candidate B: dry-run artifact 保存・レビュー運用詳細化  
5. Candidate E: Triangle / Trap / reaction SR の experiments 候補整理  
6. Candidate F: OANDA/API 接続準備（後続保持）

判断理由（要点）:
- まず exit / risk の設計前段を固定し、売買品質に近い領域へ進む。
- その前後で filter化順序を明確化し、entry集合変化を比較可能に保つ。
- A/B は運用堅牢化に有効だが、戦略中核の前進より優先度を下げる。
- E は重要だが main へ混ぜず experiments で管理する。
- F は現時点では後続とし、急いで進めない。

## 今すぐ実装しないもの
- A〜F すべて実装は未着手（今回は優先順位整理のみ）。
- 特に以下は今回非対応:
  - OANDA/API接続
  - 実注文 / demo口座接続 / broker連携
  - PipelineAdapter本体の売買判断変更
  - BacktestRunner本体の戦略変更
  - HTF/SR/Session/RiskStop/Haltのfilter化実装
  - 株式拡張 / Equity Adapter
  - lot sizing本体実装
  - 収益性評価
  - パラメータ最適化
  - ML/HMM/LSTM実装
  - Triangle / Trap / reaction SR のmain導入

## 次に実装へ進める条件（受け入れ基準）
1. C着手前:
 - `docs/04` / `docs/05` / `docs/10` / `docs/17` の Risk/Stop 境界と I/O を先に固定する。
 - 「売買挙動を変える変更」と「診断列追加」を分離して定義する。
2. D着手前:
 - Session / SR / HTF のどれを先に filter化するか順序を固定する。
 - entry集合変化の比較指標（trade_count差分だけで判断しない）を先に固定する。
3. A着手前:
 - 集計目的（運用監視/デバッグ）と最小列を固定し、summary責務を壊さない。
4. B着手前:
 - 保存先・保管期間・レビュー手順・Git管理外ルールを運用定義として先に固定する。

## 5.4thinking / Human へ確認すべき判断
1. Risk/Stop 前段設計で、最初に固定する対象を「SL/TP決定責務」までに限定するか、`lot sizing` まで含めるか。
2. filter化優先順を `Session -> SR -> HTF` にするか、`HTF -> Session -> SR` にするか。
3. Candidate A/B を C/D の前に短期で挟むか（運用堅牢化優先）をどう判断するか。
4. 次サブフェーズの完了条件を「docs固定完了」か「最小実装+unit test通過」まで含めるか。

## 実装変更有無
- 実装・売買ロジック変更なし。docs / ops 整理のみ。
