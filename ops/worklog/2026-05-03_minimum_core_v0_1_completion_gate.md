# 2026-05-03 Minimum Core v0.1 Completion Gate

## なぜ v0.1 を閉じる必要があるか
- 現在の v0.1 は完成EAではなく、最小ロジック核の構造検証である。
- ここで完了条件を固定しないと、v0.1 結果を見ながら条件を追加変更して比較軸が崩れる。
- 追加裁量・停止条件・再設計を v0.2 として分離し、評価系列を混同しないために Completion Gate が必要。

## v0.1 で確認済みの範囲
- pytest / schema / consistency など構造成立の基礎確認。
- Candidate Freeze v0.1 固定、Q1/Q2 分離、OOS-1/OOS-2 confirmation 実施。
- M1 replay による trailing exit 約定仮定監査。
- cost/slippage/swap 反映方針 v0.1 の文書化。

## v0.1 で未確認の範囲
- 収益性確認
- 実運用可能性確認
- broker 接続 / 実注文送信
- 厳密なコスト実装（slippage/commission/swap）
- 追加裁量・追加停止条件の導入効果

## v0.2 に送る範囲
- H4/H1 複合判断、support/resistance、ATR/volatility、news/event halt などの追加裁量。
- daily loss stop / drawdown stop / spread widening halt などの追加停止条件。
- v0.1 と別系列で比較・評価し、結果を混同しない。
