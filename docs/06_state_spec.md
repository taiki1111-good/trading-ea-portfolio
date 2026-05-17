# 状態仕様

## 1. 目的
本ドキュメントでは、本EAにおける状態の種類と意味、状態遷移の考え方、各状態で許可される操作を定義する。

本システムでは、売買判断そのものだけでなく、
- 現在ポジションを持っているか
- 注文待ちか
- 停止中か
- 異常状態か

を明示的に管理することを重視する。

## 2. 基本方針

### 2.1 状態を明示する理由
EAは単なる条件判定ではなく、時系列的に動作するシステムである。
そのため、各時点で「何が可能か」を状態として明示しないと、以下の問題が起こりやすい。
- 二重エントリー
- 決済中の再エントリー
- 異常時の暴走
- 停止条件中の誤発注
- ログ上の追跡困難

### 2.2 状態管理の原則
- 状態は `position_state` で管理する
- 状態遷移はイベントに基づいて行う
- 各状態で許可される操作を限定する
- 異常時は安全側の状態へ遷移させる
- 判断ロジックと状態遷移を混在させない

### 2.3 グローバル不変条件
本システムでは、個別状態の許可操作とは別に、全体で常に守るべき不変条件を以下とする。

- `position_state` は定義済み状態集合以外を取らない
- 状態遷移は `StateTransitionManager` を経由してのみ行う
- `ENTRY_PENDING` 中は新規発注を重ねない
- `POSITION_OPEN` 中は通常の新規エントリーを行わない
- `EXIT_PENDING` 中は新規エントリーを行わない
- `SUSPENDED` 中は通常の新規発注を行わない
- `ERROR` 中は通常の売買ロジックを継続しない
- 同時保有を行わない初期方針の間は、1時点で保有中ポジションは高々1つとする
- 注文結果が未確定のまま次の売買状態へ進めない
- 状態遷移時には `previous_state`、`next_state`、`transition_reason` を追跡可能にする

### 2.4 初期版の正式イベント集合
状態遷移で扱う正式イベントは以下とする。

- `entry_order_submitted`
  - `IDLE -> ENTRY_PENDING` を開始する
- `entry_filled`
  - `ENTRY_PENDING -> POSITION_OPEN`
- `entry_rejected`
  - `ENTRY_PENDING -> IDLE`
- `entry_cancelled`
  - `ENTRY_PENDING -> IDLE`
- `entry_timeout`
  - `ENTRY_PENDING -> IDLE`
- `exit_order_submitted`
  - `POSITION_OPEN -> EXIT_PENDING`
- `exit_filled`
  - `EXIT_PENDING -> IDLE`
- `exit_rejected`
  - `EXIT_PENDING` 維持または `ERROR` 候補
- `exit_cancelled`
  - `EXIT_PENDING` 維持または `ERROR` 候補
- `exit_timeout`
  - `EXIT_PENDING -> ERROR`
- `suspend_requested`
  - `IDLE -> SUSPENDED`
- `suspend_released`
  - `SUSPENDED -> IDLE`
- `fatal_error_detected`
  - `ANY -> ERROR`
- `safe_fallback_completed`
  - `ERROR -> SUSPENDED`

補足:
- `entry_signal = true` や `trade_ok = true` は上流条件であり、状態遷移の正式イベント名ではない
- 初期版の自動状態遷移は上記イベント集合のみを扱う

## 3. 状態一覧

### 3.1 IDLE
#### 意味
- ポジション未保有
- 注文待ちなし
- 新規エントリー可能な基本状態

#### 主な特徴
- 通常の待機状態
- Signal による新規候補判定を受けられる
- RiskFilter による取引可否判定を受けられる

#### 許可される操作
- 新規エントリー候補の評価
- フィルター判定
- 注文発行の開始

#### 許可されない操作
- 既存ポジションの決済
- 保有前提のトレーリング処理

---

### 3.2 ENTRY_PENDING
#### 意味
- 新規注文を発行済み、または発行処理中
- 約定待ち・注文結果待ちの状態

#### 主な特徴
- 新たなエントリーを重ねて出さない
- 約定成功か失敗かで次状態が決まる

#### 許可される操作
- 注文結果の確認
- 約定確認
- 注文拒否・失敗処理
- タイムアウト処理

#### 許可されない操作
- 新規エントリーの再発行
- 通常の新規候補評価

---

### 3.3 POSITION_OPEN
#### 意味
- ポジション保有中
- 利確、損切り、手動/機械的クローズ対象の状態

#### 主な特徴
- イグジット候補の評価を行う
- 新規エントリーは通常禁止
- 保有中管理が中心になる

#### 許可される操作
- イグジット候補の評価
- 利確・損切り処理
- 保有ポジション情報の更新
- 損益計算
- 必要に応じた保有中フィルター処理

#### 許可されない操作
- 通常の新規エントリー
- 同一ロジックによる重複エントリー（初期段階では禁止）

---

### 3.4 EXIT_PENDING
#### 意味
- 決済注文を発行済み、または発行処理中
- 決済結果待ちの状態

#### 主な特徴
- 新規エントリーは行わない
- 決済成功なら IDLE に戻る
- 決済失敗時の安全処理が重要

#### 許可される操作
- 決済結果の確認
- 約定確認
- 決済失敗時の再評価
- タイムアウト時の安全処理

#### 許可されない操作
- 新規エントリー
- 通常の保有中判断の継続実行

---

### 3.5 SUSPENDED
#### 意味
- 一時停止状態
- 新規取引を行わない状態

#### 主な特徴
- 指標前後
- 当日回数上限
- 連敗停止
- システム保護
などにより遷移する可能性がある

#### 許可される操作
- 停止解除条件の確認
- ログ記録
- 状態維持

#### 許可されない操作
- 新規エントリー
- 通常の注文発行

#### 補足
SUSPENDED は「異常停止」だけでなく、「意図的な取引停止」も含む。

---

### 3.6 ERROR
#### 意味
- 通常運用を継続するのが危険な異常状態

#### 主な特徴
- データ不整合
- 注文応答異常
- 状態不整合
- 想定外例外
などで遷移する可能性がある

#### 許可される操作
- エラー内容の記録
- 必要に応じた安全停止
- 復旧判定

#### 許可されない操作
- 新規注文
- 通常の売買ロジック継続

#### 補足
初期段階では、ERROR 発生時は安全側へ寄せて SUSPENDED に近い扱いをしてもよい。

## 4. 状態遷移の基本

### 4.1 基本遷移
- `IDLE` → `ENTRY_PENDING`
  - 新規エントリー候補が成立し、RiskFilter で `trade_ok = true` となり、`entry_order_submitted` が発生したとき

- `ENTRY_PENDING` → `POSITION_OPEN`
  - `entry_filled` が発生したとき

- `ENTRY_PENDING` → `IDLE`
  - `entry_rejected`、`entry_cancelled`、`entry_timeout` のいずれかが発生したとき

- `POSITION_OPEN` → `EXIT_PENDING`
  - 利確・損切り・イグジット条件成立などで `exit_order_submitted` が発生したとき

- `EXIT_PENDING` → `IDLE`
  - `exit_filled` が発生したとき

- `IDLE` → `SUSPENDED`
  - 指標前後停止、連敗停止、回数制限などで `suspend_requested` が発生したとき

- `SUSPENDED` → `IDLE`
  - 停止条件が解除され、`suspend_released` が発生したとき

- `ANY` → `ERROR`
  - `fatal_error_detected` が発生したとき

- `ERROR` → `SUSPENDED`
  - `safe_fallback_completed` が発生したとき

### 4.2 timeout の初期方針
- `ENTRY_PENDING` の timeout は注文送信から 120 秒とする
- `EXIT_PENDING` の timeout は注文送信から 120 秒とする
- `entry_timeout` 発生時は自動再発注を行わず、可能ならキャンセル処理を試みた後に `IDLE` へ戻す
- `exit_timeout` 発生時は保有・注文状態の不整合リスクがあるため、`ERROR` へ遷移させる
- timeout 後に自動で通常売買へ復帰させず、安全側を優先する

### 4.3 suspend release 条件
`SUSPENDED -> IDLE` は以下を満たした場合のみ許可する。

- 指標停止由来:
  - 指標対象時刻の後ろ 30 分が経過していること
- 当日回数制限由来:
  - 次の UTC 日付境界（`00:00 UTC`）を超えていること
- 連敗停止由来:
  - 次の UTC 日付境界を超えており、Human が停止理由を維持しないこと
- 保護停止由来:
  - 停止原因が消えており、Human または明示的ルールが `suspend_released` を出していること

### 4.4 `ERROR -> SUSPENDED` の具体条件
`ERROR -> SUSPENDED` は以下を満たしたときに `safe_fallback_completed` で行う。

- エラー内容が `execution_reason` または `transition_reason` に記録済みである
- 自動再試行を停止している
- ローカル状態で未完了の新規発注ループを継続していない
- 以後の通常売買を止め、人間確認待ちに移れる状態である

## 5. 状態ごとの正式イベント

### 5.1 IDLE で受ける正式イベント
- `entry_order_submitted`
- `suspend_requested`
- `fatal_error_detected`

### 5.2 ENTRY_PENDING で受ける正式イベント
- `entry_filled`
- `entry_rejected`
- `entry_cancelled`
- `entry_timeout`
- `fatal_error_detected`

### 5.3 POSITION_OPEN で受ける正式イベント
- `exit_order_submitted`
- `fatal_error_detected`

### 5.4 EXIT_PENDING で受ける正式イベント
- `exit_filled`
- `exit_rejected`
- `exit_cancelled`
- `exit_timeout`
- `fatal_error_detected`

### 5.5 SUSPENDED で受ける正式イベント
- `suspend_released`
- `fatal_error_detected`

### 5.6 ERROR で受ける正式イベント
- `safe_fallback_completed`

## 6. 各状態で許可される判断

### 6.1 IDLE
- 上位足環境判定: 可
- 執行足構造判定: 可
- シグナル生成: 可
- リスク判定: 可
- 新規発注: 可
- 決済発注: 不可

### 6.2 ENTRY_PENDING
- 上位足環境判定: 原則不要
- 執行足構造判定: 原則不要
- シグナル生成: 停止
- リスク判定: 停止
- 新規発注: 不可
- 注文結果確認: 可

### 6.3 POSITION_OPEN
- 上位足環境判定: 停止
- 執行足構造判定: 停止
- イグジット候補判定: 可
- 新規発注: 不可
- 決済発注: 可

### 6.4 EXIT_PENDING
- 新規シグナル生成: 停止
- 新規発注: 不可
- 決済結果確認: 可

### 6.5 SUSPENDED
- 新規シグナル生成: 停止
- 新規発注: 不可
- 停止解除判定: 可

### 6.6 ERROR
- 通常判断: 停止
- 新規発注: 不可
- ログ記録: 可
- 安全遷移: 可

### 6.7 各 state で無視する上流イベント・条件
初期版では以下を無視対象とする。

| state | 無視する上流イベント・条件 |
|---|---|
| `IDLE` | `exit_signal = true` |
| `ENTRY_PENDING` | 新規の `entry_signal = true`、追加の `trade_ok = true`、`exit_signal = true` |
| `POSITION_OPEN` | 新規の `entry_signal = true`、追加の `trade_ok = true` |
| `EXIT_PENDING` | 新規の `entry_signal = true`、追加の `trade_ok = true`、追加の `exit_signal = true` |
| `SUSPENDED` | `entry_signal = true`、`exit_signal = true`、通常の `trade_ok = true` |
| `ERROR` | 通常の売買条件すべて |

## 7. 初期段階の簡略ルール
初期段階では、状態管理を複雑にしすぎないため、以下を採用する。

- 同時保有は行わない
- ナンピン・両建ては行わない
- ENTRY_PENDING 中の再発注は自動で繰り返さない
- EXIT_PENDING 中の新規シグナルは無視する
- 異常時は安全側に倒す

## 8. ログで残すべき状態関連情報
状態遷移を追跡できるよう、最低限以下を記録対象とする。

- `position_state`
- `previous_state`
- `next_state`
- `transition_reason`
- `order_result`
- `execution_reason`
- `log_time`

## 9. 未確定として隔離するもの
以下は初期版の自動運用対象に含めず、必要時に別途判断する。
- 保有中の部分決済やトレーリングの有無
- broker 固有の再送・再照会仕様
- Human 主導の復旧フロー詳細

## 10. 補足
本ドキュメントで定義する状態は、初期段階の基礎設計である。
将来的に、
- 複数ポジション管理
- 実験モード
- 補助AIによる警告状態
などを追加する場合は、既存状態との整合性を崩さないように拡張する。
