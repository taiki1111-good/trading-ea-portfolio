# Trading EA プロジェクト概要

## プロジェクト名
Trading EA

## 目的
モジュール分割と段階的テストを前提として、売買判断・リスク制御・ログ検証を切り分けた分析/検証基盤を設計・実装する。

## プロジェクト形態
個人プロジェクト。
現在は設計先行の実装・検証フェーズである（実運用フェーズではない）。

## 主な特徴
- 設計文書を先に整備し、repo 内文書だけで継続できる状態を目指している
- 全体フローを `Data -> HTFContext -> LTFStructure -> Signal -> RiskFilter -> Execution -> Logger -> Evaluator` に分割している
- 状態管理と理由記録を前提にした構成を採る
- 実験領域を本体から分離して運用する
- near-live dry-run / diagnostic / shadow comparison で説明可能性を優先して検証する

## 開発方針
1. 設計を先に確定する
2. 上流モジュールから順に実装する
3. 各段階でテストを挟む
4. 実装と並行して外部説明資料も整理する

## 現時点の成果物
- 実装コード
- テストスイート
- 設計文書群
- ポートフォリオドキュメント
- dry-run / diagnostic / shadow comparison の出力と記録

## プロジェクト段階
現在は以下を到達点としている。
- Phase 9 CSV replay pipeline dry-run minimal completion reached
- Risk/Stop v0 minimal implementation adopted
- PipelineAdapter planner chain 正式接続（fixed baseline 同値維持目的）
- HTF diagnostic comparison v0 完了
- Lot Sizing shadow comparison 採用（diagnostic tool）

## 未実装（明示）
- 実 broker / OANDA API / 実注文送信
- 収益性確認
- lot sizing 本体接続（`PositionSizer` は placeholder）
- Session / SR / HTF の本体filter化

## 補足
この文書は外部説明用の下書きであり、Source of Truth ではない。
正式な設計内容は `docs/02_requirements.md` から `docs/08_development_plan.md` を参照する。
