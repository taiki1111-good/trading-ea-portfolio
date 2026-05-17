# EA Master Implementation Roadmap v0.2+

## 1. 目的
Minimum Core v0.1（structural validation complete）以後の実装順序・検証順序・完了条件を固定し、会話ごとの場当たり的な順序決定を防ぐ。

## 2. 前提
- 実 broker / OANDA API / 実注文送信は未実装。
- 収益性確認済みではない。
- v0.1 と v0.2 以降の結果を混同しない。
- 追加裁量・停止条件は v0.2 以降として扱う。

## 3. 原則
- 診断できるものは先に診断スクリプトで見る。
- 本体統合前にログ列とテストを決める。
- 結果を見て閾値を逐次調整しない。
- 調整する場合は v0.3 など別バージョンとして分離する。
- 実装順序は `ops/CURRENT_TASKS.md` ではなく本 Roadmap を優先する。

## 4. フェーズ

### Phase 0: Minimum Core v0.1 closure
目的:
- v0.1 を structural validation complete として閉じ、変更起点を v0.2 に分離する。

実装対象:
- 追加実装なし（閉鎖整理のみ）。

実装前に必要な設計:
- v0.1 到達点と未実装範囲の明文化。

検証方法:
- 文書整合確認（v0.1 到達点、対象外範囲、禁止事項）。

完了条件:
- v0.1 closure 宣言が docs/ops に明記されている。

次フェーズへ進む条件:
- v0.2 以降を別管理する合意が記録されている。

### Phase 1: v0.2 planning freeze
目的:
- v0.2 に入れる裁量・停止条件を固定する。

実装対象:
- スコープ定義（halt/risk/HTF/SR/session/risk management）。

実装前に必要な設計:
- 各機能の入力・出力・ログ列・テスト観点。

検証方法:
- 設計レビュー、スキーマ草案レビュー。

完了条件:
- v0.2 Candidate Freeze 条件の初版が文書化されている。

次フェーズへ進む条件:
- Phase 2 診断に必要な I/O スキーマが固定されている。

### Phase 2: Halt/Risk diagnostic layer
目的:
- 高優先停止条件の有効性と副作用を本体統合前に診断する。

実装対象:
- `price_shock_halt` / `volatility_spike_halt` 診断スクリプト。
- `scheduled_event_halt` / `spread_widening_halt` は後続。

実装前に必要な設計:
- 診断入力（価格・decision/trade logs）と出力（halt windows 等）スキーマ。
- 初期閾値は仮説として固定。

検証方法:
- 診断レポート（停止件数、回避損失/逸失利益、停止時間）。

完了条件:
- 2種 halt の診断結果が再現可能に出力される。

次フェーズへ進む条件:
- 有効性と副作用を説明できる診断ログが揃っている。

現時点メモ（2026-05-03）:
- OOS-2 2024-11 の Phase 2 scenario（A〜F）では全条件で `net_counterfactual_effect_pips` がマイナスとなり、初期 Halt/Risk 候補は Phase 3 No-Go。
- Halt Filter は一時保留し、Roadmap 順序は維持したまま次工程として Phase 4 HTFContext v0.2 設計へ進む判断を許容する。

### Phase 3: Halt/Risk integration
目的:
- 診断済み halt を本体に段階統合する。

実装対象:
- RiskFilter または PipelineAdapter への統合。
- 対象は新規 entry 停止。

実装前に必要な設計:
- 追加ログ列、テストケース、互換性方針。

検証方法:
- 統合テスト、decision/trade log 整合性確認。

完了条件:
- 新規 entry 停止が再現可能で、既存フローを破壊しない。

次フェーズへ進む条件:
- 強制決済を含めずに停止仕様が安定している。

### Phase 4: HTFContext v0.2
目的:
- H4/H1 複合判断で entry 文脈を強化する。

実装対象:
- H4 bias + H1 context。
- strict/permissive 再整理。

実装前に必要な設計:
- bias/context 判定契約、future leak 防止規約。

検証方法:
- OFF/ON 比較、neutral 処理差分比較、リーク監査。

完了条件:
- H4/H1 判定とログが時系列整合で再現可能。

次フェーズへ進む条件:
- HTF 判定の副作用を説明可能である。

### Phase 5: Support/Resistance filter
目的:
- 上位抵抗/支持近接で不要 entry を見送る。

実装対象:
- 余地判定と近接見送り。

実装前に必要な設計:
- 距離閾値の固定仮説、判定列と理由列。

検証方法:
- 見送り件数、見送り後の counterfactual 比較。

完了条件:
- SR 近接判定が安定し、理由追跡できる。

次フェーズへ進む条件:
- 閾値を逐次最適化せず固定仮説として運用できる。

### Phase 6: Session/Time filter
目的:
- 時間帯リスクを管理し低流動性局面を回避する。

実装対象:
- 東京/欧州/NY セッション。
- 低流動性時間、週末・年末・祝日前後。

実装前に必要な設計:
- セッション定義、祝日近傍ルール、タイムゾーン基準。

検証方法:
- フィルター命中率、セッション別成績差分。

完了条件:
- 時間帯停止理由がログで追跡可能。

次フェーズへ進む条件:
- 運用時間ルールが仕様化され再現できる。

### Phase 7: Risk management layer
目的:
- 口座保全を優先した損失制御を導入する。

実装対象:
- risk sizing。
- daily loss stop。
- consecutive loss stop。
- drawdown stop。

実装前に必要な設計:
- 残高基準、停止解除条件、状態遷移。

検証方法:
- シナリオテスト（連敗、日次損失、DD 到達）。

完了条件:
- 停止・再開条件が一貫して機能する。

次フェーズへ進む条件:
- 資金管理の挙動がログとテストで説明可能。

### Phase 8: Validation framework
目的:
- 過学習抑止を前提に検証基盤を固定する。

実装対象:
- walk-forward / rolling validation。
- レジーム耐性・ストレス確認。

実装前に必要な設計:
- 期間分割方針、評価指標、比較プロトコル。

検証方法:
- 期間別再現比較、OOS 一貫性確認。

完了条件:
- 最近データ偏重の最適化を回避した検証が回る。

次フェーズへ進む条件:
- v0.2 Candidate Freeze 判定に必要な検証が揃う。

### Phase 9: near-live / dry-run
目的:
- 実注文前に dry-run で運用近似の不整合を潰す。

実装対象:
- near-live 実行基盤（実注文送信なし）。

実装前に必要な設計:
- 監視項目、障害時挙動、ログ運用。

検証方法:
- 連続 dry-run、日次運用チェック。

完了条件:
- dry-run で運用上の重大不整合が解消されている。

次フェーズへ進む条件:
- OANDA/API/実注文送信の設計着手可否を別途判断できる。
