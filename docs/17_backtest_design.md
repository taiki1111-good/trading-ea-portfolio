# BacktestRunner 設計（研究用EA）

## 1. 文書の目的
本書は `BacktestRunner`（仮称）の設計方針を整理し、Backtest 層の責務・入力・出力・仮 exit ルール・Logger / Evaluator 接続点・対象外範囲を明確にする。

位置づけとして、本書は「構造検証（設計どおりの一方向フローが成立するか）」から「過去データを使った研究用EAの検証（entry / exit / pnl / log / evaluator の一連の流れが成立するか）」へ進むための橋渡しである。

## 2. Backtest の位置づけ
- Backtest は収益性を即断するための最終評価ではない。まずは **entry / exit / pnl / log / evaluator** の一連の流れが、過去データ上で破綻なく動くことを検証する。
- 本 Backtest は **研究用EA** のための基盤であり、**実運用EAではない**。
- **実 broker 接続 / OANDA API / 実注文送信は扱わない**（本書の対象外）。

関連（用語の区別）:
- `docs/16_operation_design.md` の「backtest / 構造検証 / 実運用近似」の区別に従う。

## 3. BacktestRunner の責務
BacktestRunner は、過去データを入力として、主要骨組み（Data -> HTFContext -> LTFStructure -> Signal -> RiskFilter -> Execution -> Logger -> Evaluator）を **backtest 用に駆動**し、取引ログと評価結果を生成する。

### 3.1 時系列駆動
- 過去データ（バー列）を **時系列順**に流す（future leak を禁止）。
- BacktestRunner は **DataLoader を各バーで再実行しない**。
- BacktestRunner は **Data 層で事前に検証・正規化済みの `price_frame`**（バー列）を受け取り、時系列順にスライスして後続モジュールへ渡す。
- 各タイムステップ `i` では、後続モジュールに渡す入力は常に **現在バーまで**に限定する（例: `bars[:i+1]`）。
- 各バー（または各タイムステップ）で、以下を順に接続する:
  - `Data`（`price_frame` のスライス供給。再ロードや再検証はしない）
  - `HTFContext`
  - `LTFStructure`
  - `Signal`
  - `RiskFilter`
  - `Execution`（backtest モード / dry-run 相当）

### 3.2 future leak 防止（具体ルール）
- 各タイムステップ `i` で参照可能なのは **`bars[:i+1]` のみ**とする（現在バーまで）。
- 未来バー **`bars[i+1:]` は entry / structure / context 判定に使用しない**。
- position 保有中の exit 判定では **現在バーの OHLC のみ**を使用する（未来バーや将来確定情報を使わない）。

### 3.2.1 intrabar leak 防止（初期固定ルール）
- entry は **現在バー `i` の close で約定した**ものとみなす。
- exit 判定は **次バー `i+1` 以降**から開始する。
- **entry と同じバーでは SL / TP / max_holding_bars exit を行わない**（entry バーの high/low を exit 判定に使わない）。
- これは初期版で tick / 低位足が無い前提における **intrabar leak 防止**のための固定ルールである。

### 3.2.2 timestamp semantics（bar timestamp と約定有効時刻）
- M5 生成スクリプト（`scripts/make_m5_backtest_slice_from_dat.py`）は `timestamp=floor('5min')` を採用しており、bar timestamp は bar open time（5分足開始時刻）である。
- BacktestRunner は bar close entry 前提であり、`entry_time` が bar timestamp と同値でも、それは **entry decision bar timestamp** を表す。
- したがって `trade_logs.entry_time` と「entry約定が有効になった時刻（entry_effective_time）」は概念的に区別が必要である。
- M1 replay で M5 close entry を再現する場合、`entry_effective_time`（例: M5 の場合 `entry_time + 5分`）以降だけを exit 判定対象にする。

### 3.3 エントリーとポジション生成
- entry 条件が成立した場合に `position`（ポジション状態）を生成する。
- BacktestRunner は「ポジションが無い/ある」の状態を追跡し、保有中は新規エントリーを抑止する（初期版の単純化）。

### 3.4 exit 判定と決済
- position 保有中、各バーで exit 条件を判定する（初期版は本書の仮ルール）。
- 決済が成立した場合、exit 情報を確定し **PnL を計算**する。

### 3.5 ログ生成と引き渡し
- Logger / Persistence / Evaluator に渡せる形で、少なくとも以下を生成する:
  - `trade_logs`
  - `decision_logs`
  - `state_logs`
  - `event_logs`
- `trade_logs` は、Evaluator が集計可能な最小情報（entry / exit / pnl / reason / timestamps 等）を含む。

## 4. BacktestRunner が扱わないもの（対象外）
初期版 BacktestRunner は、研究用EAの検証を目的とし、以下は対象外とする（**実装済みのように書かない**）。

- 実 broker API
- OANDA API
- 実注文送信
- スリッページの本格モデル
- 約定遅延の本格モデル
- 手数料・スワップの厳密計算
- 最適化探索（パラメータサーチ）
- 複数戦略比較基盤
- 本格レポート生成（PDF/HTML 等の整形）

## 5. 入力 / 出力（I/O）
### 5.1 入力（Inputs）
- 過去データ（バー列）
  - 初期版では fixture（短い CSV 等）を想定する
- Data 層出力
  - Data 層で検証・正規化済みの `price_frame`（バー列）を受け取る
  - BacktestRunner は `price_frame` を時系列順にスライスして後続へ渡す（DataLoader の再実行はしない）
- 設定（Config）
  - シンボル、時間足、期間、初期資金（必要なら）、`max_holding_bars`、`stop_loss`、`take_profit` 等
- Strategy / Pipeline
  - `Signal` / `RiskFilter` / `Execution` の組み合わせ（既存の主要骨組み）
- Run metadata
  - `run_id`（`docs/16_operation_design.md` の CSV persistence 方針に従う）

### 5.2 出力（Outputs）
BacktestRunner の主要出力はログと集計結果である。

- `trade_logs`
- `decision_logs`
- `state_logs`
- `event_logs`
- `backtest_summary`（走行サマリ: 期間、バー数、トレード数など）
- `evaluator_result`（Evaluator が返す基本指標）

## 6. 初期 exit ルール（Signal exit が skeleton のため）
現状 `Signal` の exit signal は skeleton である前提のため、初期 Backtest では exit を **仮ルール**で決める。

### 6.1 long の仮 exit
- `low <= stop_loss` なら `stop_loss` で決済
- `high >= take_profit` なら `take_profit` で決済
- `max_holding_bars` 到達なら `close`（当該バーの close）で決済

### 6.2 short の仮 exit
- `high >= stop_loss` なら `stop_loss` で決済
- `low <= take_profit` なら `take_profit` で決済
- `max_holding_bars` 到達なら `close`（当該バーの close）で決済

### 6.3 同一バーで SL/TP 両到達した場合
- 初期版は **`stop_loss` 優先**で固定する（保守的）。
- 将来、tick / 低位足データで「到達順序」を検証できる場合のみ、このルールを拡張する。

### 6.4 future exit experiments（将来実験候補）
MTFチャートの目視確認により、固定距離/固定時間中心の exit では、トレンド継続中でも早期撤退となる可能性がある。
ただし現時点では、これは構造検証段階での観察であり、収益性確認済みを意味しない。

- `fixed_sl_tp_exit`:
  - 現行方式（`stop_loss` / `take_profit` / `max_holding_bars`）
  - 比較基準として維持する
- `trend_break_exit`:
  - トレンド崩壊まで保有する候補
  - 例: 押し安値割れ / 戻り高値超え / MA傾き反転 / swing構造崩壊
- `hybrid_exit`:
  - 初期SLは維持
  - 固定TP単独ではなく、トレンド崩壊または構造崩壊で撤退する候補
  - 含み益発生後の `trailing` / `break-even` / `swing-based stop` を候補化
- `time_based_exit`:
  - `max_holding_bars` は比較軸として残す
  - 単独の主exitとしては使わない構成を比較する

実験上の注意:
- 売買ロジック本体（entry判定）とは切り分けて検証する。
- 実 broker / OANDA API / 実注文送信は対象外のままとする。
- spread=0.2 pips fallback、手数料・スリッページ・スワップ未反映の前提を維持する。

### 6.5 counterfactual exit analysis 方針（entry固定）
exit 改善候補は、いきなり BacktestRunner / ExitRuleEngine 本体へ組み込まず、既存 `trade_logs` の entry を固定した後追い比較で切り分ける。

- 既存entryは固定する（entry時刻・entry方向・entry価格は変更しない）
- 比較対象は exit 条件のみ（SL/TP幅、break-even、trailing など）
- BacktestRunner 本体の exit 仕様とは分離した分析スクリプトで実施する
- 目的は `exit strategy experiments` 候補評価であり、収益性評価ではなく構造検証とする
- `htf_against_entry` が一定数残る場合、exit 改善だけで本採用判断を行わない
- 次段で本物の HTFContext 導入候補と比較し、entry 側課題と exit 側課題を分離検証する

前提の維持:
- 実 broker / OANDA API / 実注文送信は未実装のまま
- walk-forward / ML / parameter optimization は本節の対象外
- spread=0.2 pips fallback、手数料・スリッページ・スワップ未反映の前提を維持する

### 6.6 position-aware counterfactual replay 方針（entry候補固定 + 同時保有抑止）
独立 counterfactual exit analysis は「各tradeを独立に評価する局所比較」であり、保有延長による後続entry抑止を考慮しない。
この限界を補うため、既存 `trade_logs` の entry 候補を時系列順に再生し、同時保有なし制約を適用する `position-aware counterfactual replay` を別分析として扱う。

- 独立分析と position-aware replay は別物として記録する
- 独立分析は exit候補の局所評価（entry固定・trade独立）
- position-aware replay は同時保有抑止を含むため、実Backtest挙動により近い比較ができる
- ただし position-aware replay も既存entry候補を使った後追いであり、正式な BacktestRunner 統合ではない
- 目的は収益性評価ではなく、exit改善候補の構造検証
- spread=0.2 pips fallback、手数料・スリッページ・スワップ未反映の前提を維持する

### 6.7 trailing系 counterfactual の intrabar ambiguity 監査方針
M5 OHLC ではバー内の価格到達順序（high先行かlow先行か）が不明であるため、trailing / break-even 系では同一バー内の activation と stop 到達に曖昧性が残る。

- 例（long）:
  - 同一バーで `high` が 1R 到達条件を満たす
  - かつ `low` が stop 到達条件を満たす
- 例（short）:
  - 同一バーで `low` が 1R 到達条件を満たす
  - かつ `high` が stop 到達条件を満たす

このため counterfactual replay では、`simple_trailing_after_1R` に加えて以下を比較する。

- `simple_trailing_after_1R_conservative`:
  - 曖昧ケースで不利側を優先して exit する保守的 variant
- `simple_trailing_after_1R_next_bar_activation`:
  - 1R 到達バーでは trailing を有効化せず、次バーから有効化する variant

これらは OHLC 順序不明による楽観バイアスを下げるための構造検証であり、収益性評価を目的としない。
前提は従来どおり、spread=0.2 pips fallback、手数料・スリッページ・スワップ未反映である。

### 6.8 M1 exit replay による曖昧性低減検証（entry固定）
M5 position-aware replay で `simple_trailing_after_1R` が有力候補となった一方、M5 OHLC では intrabar ambiguity（activation と stop 到達順序不明）が残る。
このため、BacktestRunner統合前の検証として、entry は既存 M5 `trade_logs` に固定し、exit 判定のみを M1 DAT/CSV で再評価する `M1 exit replay` を追加する。

- M1 replay は M5 intrabar ambiguity を減らすが、完全には消さない
- M1 でも同一バー内の OHLC 到達順序不明は残る
- ただし M5 より細かい粒度で exit 挙動を確認できる
- これは本体統合前の構造検証段階であり、収益性評価ではない
- 前提は従来どおり、spread=0.2 pips fallback、手数料・スリッページ・スワップ未反映
- M1 replay の単体結果だけで exit 採用判断は行わない
- `baseline_fixed_exit` / trailing variants を同一条件（同一期間・同一 entry・同一 holding 制約）で比較する
- M5 と M1 の差には intrabar sequence 解像度差の影響が含まれる

### 6.9 experimental exit policy 比較方針（本体既定維持）
- `fixed_sl_tp` は BacktestRunner 本体既定の baseline として維持する。
- `simple_trailing_after_1R` は experimental exit candidate として扱う。
- counterfactual replay（M5/M1）で有望結果があっても、本採用は別判断とする。
- 本体既定動作を壊さないため、比較は experimental runner または設定フラグで分離して実施する。
- M1 replay の検証では `entry_time_mode=m5_close` が必要だった点を前提として記録する。
- M5 experimental exit 比較は構造検証であり、M1 replay 相当の厳密検証とは区別する。
- 前提は継続して spread=0.2 pips fallback、手数料・スリッページ・スワップ未反映。
- Q1全体の一括実行前に、月別（2024-01/02/03）分割で完走性とログ整合を確認する。
- M1 replay は entry固定・低位足exit再評価、experimental runner はM5上でのexit policy比較であり、役割が異なる。
- 実験結果は収益性確認ではなく構造検証として扱う。

### 6.10 Q2 out-of-sample 的確認方針
- Q1内比較（2024-01/02/03）だけでは採用判断を行わない。
- 同一条件を変えずに Q2（2024-04-01〜2024-07-01）で out-of-sample 的な再現確認を行う。
- M5 experimental runner と M1 replay は役割が異なるため、結果を混同せずに併記する。
- これは収益性確認ではなく、exit candidate の構造検証である。
- 前提は継続して spread=0.2 pips fallback、手数料・スリッページ・スワップ未反映。
- Q1/Q2 の M5 experimental comparison では `simple_trailing_after_1R` は `fixed_sl_tp` より有力な experimental exit candidate として扱う。
- ただし `simple_trailing_after_1R` は本採用ではなく、BacktestRunner 既定 exit としては採用しない。
- M1 replay では `simple_trailing_after_1R` 本体は優位を維持したが、`simple_trailing_after_1R_conservative` / `simple_trailing_after_1R_next_bar_activation` は弱く、約定仮定・発動タイミング依存の検証余地を残す。
- 次工程では exit candidate 検証を継続しつつ、HTFContext 本格導入候補との比較で entry 側課題と exit 側課題を分離して判断する。

### 6.11 HTFContext本格導入比較方針（experimental comparison）
目的:
- entry側課題（`htf_against_entry` など）と exit側課題（fixed/trailing差分）を分離して検証する。
- 収益性確認ではなく構造検証として扱う。

比較実施の前提:
- BacktestRunner / PipelineAdapter / ExitRuleEngine の既定動作は変更しない。
- 売買ロジック本体へ直ちに組み込まず、experimental comparison として分離実施する。
- `simple_trailing_after_1R` は本採用ではなく experimental exit candidate のまま扱う。
- 前提は継続して spread=0.2 pips fallback、手数料・スリッページ・スワップ未反映。

HTF filter v1（今回の比較対象）:
- H1 only + direction alignment のみに限定する。
- H4 利用（H4 only / H1&H4 aligned / H4 bias + H1 context）は v1 対象外とし、次段階候補に分離する。
- support/resistance 判定（`htf_resistance_ok` / `htf_support_ok`）は v1 対象外とし、将来拡張候補に分離する。

設定インターフェース（v1確定）:
- `htf_filter_enabled: bool`
- `htf_timeframe_policy: H1_only`
- `htf_neutral_policy: permissive | strict`

既定動作（互換性）:
- 既定値は `htf_filter_enabled=false` とする。
- 既存backtest結果との互換性を維持し、HTF filter ON は明示フラグ指定時のみ有効化する。

HTF filter v1 の基本ルール（ON時）:
- long entry 候補:
  - H1 `htf_bias` または `htf_trend_dir` が `up` なら通す。
  - `down` なら見送り。
  - `neutral` は neutral policy に従う。
- short entry 候補:
  - H1 `htf_bias` または `htf_trend_dir` が `down` なら通す。
  - `up` なら見送り。
  - `neutral` は neutral policy に従う。

判定優先順位（v1確定）:
- 主判定は `htf_bias` を優先し、`htf_trend_dir` は補助ログとして扱う。
- ただし、実装時点で `htf_bias` が判定不能または欠損のケースでは、暫定fallbackとして `htf_trend_dir` を使用してよい。
- 上記fallbackを使った場合は `htf_filter_reason` に理由を残し、後続で `htf_bias` 主判定へ収束させる。

未確定事項（実装前に決定が必要）:
- `neutral` 扱い:
  - strict: `neutral` は見送り
  - permissive: `neutral` は通す
  - comparison: strict / permissive を別条件で比較
- 初回実験で strict/permissive のどちらかを本採用と断定しない（比較条件として扱う）。

時系列整合（future leak 防止）:
- 各M5バー時点で参照可能なのは確定済みHTFバーのみとする。
- 未確定H1バーは判定に使用しない。
- M5 timestamp が bar open time、entry は M5 close 前提である点との整合を確認対象に含める。

比較軸:
- 2x2 の基本軸（HTF OFF/ON × fixed/trailing）を維持する。
- ただし v1 では neutral policy 比較を追加し、以下 6 条件を初回候補とする。
1. HTF OFF + `fixed_sl_tp`
2. HTF OFF + `simple_trailing_after_1R`
3. HTF ON（H1 only, neutral permissive）+ `fixed_sl_tp`
4. HTF ON（H1 only, neutral permissive）+ `simple_trailing_after_1R`
5. HTF ON（H1 only, neutral strict）+ `fixed_sl_tp`
6. HTF ON（H1 only, neutral strict）+ `simple_trailing_after_1R`

評価指標（最低限）:
- `trade_count`
- `win_rate`
- `total_pnl`
- `average_pnl`
- `exit_reason counts`
- `htf_filter_rejected_count`
- `htf_filter_rejected_by_reason`
- `htf_direction_aligned count`
- `htf_against_entry count`
- `neutral_passed_count`
- `neutral_rejected_count`
- HTF filter OFF/ON 差分
- fixed exit / trailing exit 差分
- 月別比較
- Q1/Q2 同一条件比較
- HTF filter の効果は trade_count 減少だけで判断しない（除外entry理由を併記する）。
- これは収益性確認ではなく構造検証である。

ログ・スキーマ観点（文書化のみ）:
- decision_logs で HTF判断の追跡列が十分かを事前確認する。
- 既存列で不足がある場合、以下を v1最小追加候補として固定する（今回は実装しない）。
  - `htf_filter_enabled`
  - `htf_timeframe_policy`
  - `htf_neutral_policy`
  - `htf_trend_dir`
  - `htf_bias`
  - `htf_direction_aligned`
  - `htf_filter_reason`
  - `htf_context_reason`

### 6.12 HTF alignment policy comparison の注意（2024-04 単月観察）
- 本節は構造検証上の観察整理であり、収益性確認ではない。
- 2024-04 単月 `fixed_sl_tp` の確認では、HTF v1 は単純な「取引数を減らす filter」とは限らない挙動を示した。
- 観察値:
  - HTF OFF: `trade_count=80`
  - HTF ON strict: `trade_count=80`（OFF と entry 集合が一致）
  - HTF ON permissive: `trade_count=84`
- permissive 側でのみ成立した entry は、`htf_bias=neutral` かつ `htf_neutral_policy=permissive` による通過が起点となった。
- permissive only の一部は、OFF 側 entry と比べて「5分前倒し」で発生しうる。
- このため、比較名は `HTF filter ON/OFF` だけでなく、`HTF alignment policy comparison` として扱う。
- 比較時の最低確認項目:
  - `trade_count` 差分
  - entry 集合差分（共通 / only）
  - entry 時刻の前倒し有無（例: 5分先行）
  - `neutral_passed_count` / `neutral_rejected_count`
- 上記は HTF v1（H1 only + direction alignment only）の挙動確認であり、H4 や support/resistance は対象外とする。

### 6.13 Q2 HTF alignment policy comparison 要約（2024-04/05/06）
- 本節は構造検証の整理であり、収益性確認ではない。
- 共通前提: spread=0.2 pips fallback、手数料・スリッページ・スワップ未反映。

| month | condition | trade_count | total_pnl |
|---|---|---:|---:|
| 2024-04 | OFF fixed | 80 | -0.0260 |
| 2024-04 | OFF trailing | 80 | 0.0621 |
| 2024-04 | permissive fixed | 84 | -0.0210 |
| 2024-04 | permissive trailing | 84 | 0.0689 |
| 2024-04 | strict fixed | 80 | -0.0260 |
| 2024-04 | strict trailing | 80 | 0.0621 |
| 2024-05 | OFF fixed | 72 | -0.0270 |
| 2024-05 | OFF trailing | 72 | 0.0870 |
| 2024-05 | permissive fixed | 76 | -0.0280 |
| 2024-05 | permissive trailing | 76 | 0.0962 |
| 2024-05 | strict fixed | 72 | -0.0270 |
| 2024-05 | strict trailing | 72 | 0.0870 |
| 2024-06 | OFF fixed | 59 | -0.0140 |
| 2024-06 | OFF trailing | 59 | 0.0582 |
| 2024-06 | permissive fixed | 62 | -0.0110 |
| 2024-06 | permissive trailing | 62 | 0.0634 |
| 2024-06 | strict fixed | 59 | -0.0140 |
| 2024-06 | strict trailing | 59 | 0.0582 |

- 観察要点:
  - Q2 全月で strict は OFF と一致（trade_count / total_pnl とも一致）。
  - permissive は全月で trade_count を増やした（neutral 通過 policy の影響）。
  - permissive + trailing は Q2 全月で OFF/strict + trailing を上回った。
  - permissive + fixed は 2024-05 で OFF/strict より悪化し、単独での採用判断はできない。
- 以上より、Q2比較は `HTF filter ON/OFF` ではなく `HTF alignment policy comparison` として扱い、entry集合差分と前倒し差分を併記して評価する。

### 6.14 Candidate Freeze v0.1（確認用BT前の候補固定）
- 本節は、探索・構造検証フェーズから確認用バックテスト（confirmation backtest）準備へ移行するための候補固定定義である。
- 収益性確認ではなく、構造検証の次工程管理を目的とする。
- Q1/Q2（2024-01-02〜2024-07-01）は探索・構造検証で使用済み期間として扱い、確認用バックテストの評価期間とは区別する。
- ここから先は、確認用期間の結果を見て即座にルール変更しない。
- 確認用バックテストで崩れた場合は、結果を「候補棄却または再設計理由」として扱う。
- 結果を見ながら逐次調整する場合は、別バージョンとして記録し、元の確認用バックテストと分離する。

Candidate Freeze v0.1:

| Category | Frozen candidate | Notes |
|---|---|---|
| Entry | `third_wave_break` + `detector_chain_temporal` | fallback OFF, lookback=5, dedup=1, `entry_time_mode=m5_close` |
| Exit baseline | `fixed_sl_tp` | comparison baseline |
| Exit candidate | `simple_trailing_after_1R` | experimental exit candidate, not adopted |
| HTF baseline | OFF/default | current/default comparison |
| HTF candidate | permissive | neutral early-entry/added-entry policy |
| Excluded from v0.1 | strict | Q2 matched OFF; keep as future spec comparison |
| Excluded from v0.1 | H4/support-resistance | future candidate |
| Excluded from v0.1 | H1&H4 aligned / H4 bias + H1 context | outside v1 scope |
| Excluded from v0.1 | additional exit modifications | swing-based trailing / trend-break exit are postponed |

### 6.15 Confirmation Backtest Design v0.1
- 本節は Candidate Freeze v0.1 の次工程として、確認用バックテスト（confirmation backtest）の設計を定義する。
- 収益性確認ではなく、「次段階に残す価値があるか」を判定するための確認工程として扱う。
- Q1/Q2 は探索・構造検証に使用済み期間のため、確認用評価から分離する。
- 確認用期間の結果を見ても、その場でルール変更しない。
- ルール変更が必要な場合は Candidate Freeze v0.2 として別管理する。

確認用期間（OOS）:
- OOS-1（第一確認期間）: `2024-07-01` 〜 `2024-10-01`
- OOS-2（第二確認候補）: `2024-10-01` 〜 `2025-01-01`
- 実行順序: まず OOS-1 のみ実行し、結果を見ても即時ルール変更は行わない。

比較条件（v0.1 は4条件に限定）:
1. OFF + `fixed_sl_tp`
2. OFF + `simple_trailing_after_1R`
3. permissive + `fixed_sl_tp`
4. permissive + `simple_trailing_after_1R`

対象外（確認用BT主軸から除外）:
- strict（Q2でOFF一致のため主軸から除外。将来仕様比較候補として保持）
- H4 / support-resistance / H1&H4 aligned / H4 bias + H1 context
- 追加exit改造（swing-based trailing / trend-break exit 含む）

合否判定基準（収益性確認ではない）:
- `simple_trailing_after_1R` が `fixed_sl_tp` より安定しているか
- permissive + trailing が OFF + trailing を上回るか、少なくとも大きく悪化しないか
- 月別で一部月だけに依存していないか
- `trade_count` が少なすぎないか
- schema validation / consistency が valid か
- entry集合差分、`neutral_passed_count`、`shifted_5min_count` を確認する
- 結果が悪い場合は即修正せず、v0.1棄却またはv0.2再設計候補として記録する

OOS-1 合否判定基準（v0.1 運用）:
- 必須条件:
  - 全4条件runで schema validation / consistency が `valid`。
- 比較条件A（exit比較）:
  - OOS-1合計で `simple_trailing_after_1R` が `fixed_sl_tp` より良いこと（OFF比較・permissive比較の双方を確認）。
  - 月別（2024-07/08/09）のうち **2/3以上** で、`simple_trailing_after_1R` が `fixed_sl_tp` より良いこと。
- 比較条件B（policy比較）:
  - OOS-1合計で permissive + trailing が OFF + trailing に対して **同等以上**。
  - 月別（2024-07/08/09）のうち **2/3以上** で、permissive + trailing が OFF + trailing に対して **同等以上**。
- 注意条件:
  - `trade_count` が少なすぎる場合は判定保留とする。
  - 成果が1か月だけに依存する場合は要注意（過適合疑い）として扱う。
  - entry集合差分、`neutral_passed_count`、`shifted_5min_count` を併記し、挙動の整合を確認する。
- 失敗時の扱い:
  - 即時修正は行わず、Candidate Freeze v0.1 棄却または Candidate Freeze v0.2 再設計候補として記録する。

ローカルPowerShell実行テンプレート（実行はユーザー側）:
```powershell
$env:PYTHONPATH='.'

# 例: OOS-1 の4条件実行テンプレート（run_id/out_dirは適宜置換）
python scripts/run_backtest_exit_experiment.py --input-csv <oos1_m5_slice_csv> --run-id <oos1_off_fixed> --output-dir <out_off_fixed> --max-holding-bars 50 --exit-policy fixed_sl_tp --entry-time-mode m5_close --third-candidate-lookback-bars 5 --max-entries-per-recent-third-candidate 1 --disable-heuristic-fallback --start 2024-07-01 --end 2024-10-01
python scripts/run_backtest_exit_experiment.py --input-csv <oos1_m5_slice_csv> --run-id <oos1_off_trailing> --output-dir <out_off_trailing> --max-holding-bars 50 --exit-policy simple_trailing_after_1R --entry-time-mode m5_close --third-candidate-lookback-bars 5 --max-entries-per-recent-third-candidate 1 --disable-heuristic-fallback --start 2024-07-01 --end 2024-10-01
python scripts/run_backtest_exit_experiment.py --input-csv <oos1_m5_slice_csv> --run-id <oos1_perm_fixed> --output-dir <out_perm_fixed> --max-holding-bars 50 --exit-policy fixed_sl_tp --entry-time-mode m5_close --third-candidate-lookback-bars 5 --max-entries-per-recent-third-candidate 1 --disable-heuristic-fallback --htf-filter-enabled --htf-neutral-policy permissive --start 2024-07-01 --end 2024-10-01
python scripts/run_backtest_exit_experiment.py --input-csv <oos1_m5_slice_csv> --run-id <oos1_perm_trailing> --output-dir <out_perm_trailing> --max-holding-bars 50 --exit-policy simple_trailing_after_1R --entry-time-mode m5_close --third-candidate-lookback-bars 5 --max-entries-per-recent-third-candidate 1 --disable-heuristic-fallback --htf-filter-enabled --htf-neutral-policy permissive --start 2024-07-01 --end 2024-10-01
```

### 6.16 OOS-1 Confirmation Backtest 結果要約（2024-07-01〜2024-10-01）
本節は Candidate Freeze v0.1 の OOS-1 結果記録であり、収益性確認や本採用判断ではない。

月別結果（4条件）:
- 2024-07:
  - OFF + `fixed_sl_tp`: `trade_count=75`, `total_pnl=0.0060`
  - OFF + `simple_trailing_after_1R`: `trade_count=75`, `total_pnl=0.1791`
  - permissive + `fixed_sl_tp`: `trade_count=79`, `total_pnl=0.0020`
  - permissive + `simple_trailing_after_1R`: `trade_count=79`, `total_pnl=0.1848`
- 2024-08:
  - OFF + `fixed_sl_tp`: `trade_count=57`, `total_pnl=-0.0240`
  - OFF + `simple_trailing_after_1R`: `trade_count=57`, `total_pnl=0.2703`
  - permissive + `fixed_sl_tp`: `trade_count=58`, `total_pnl=-0.0250`
  - permissive + `simple_trailing_after_1R`: `trade_count=58`, `total_pnl=0.2766`
- 2024-09:
  - OFF + `fixed_sl_tp`: `trade_count=56`, `total_pnl=-0.0110`
  - OFF + `simple_trailing_after_1R`: `trade_count=56`, `total_pnl=0.2578`
  - permissive + `fixed_sl_tp`: `trade_count=57`, `total_pnl=-0.0090`
  - permissive + `simple_trailing_after_1R`: `trade_count=57`, `total_pnl=0.2627`

entry集合差分（trailing比較）:
- 2024-07: `compare_only=7`, `base_only=3`, `shifted_5min=3`, `neutral_passed=8`, `total_pnl_diff=+0.0057`
- 2024-08: `compare_only=2`, `base_only=1`, `shifted_5min=1`, `neutral_passed=2`, `total_pnl_diff=+0.0063`
- 2024-09: `compare_only=2`, `base_only=1`, `shifted_5min=1`, `neutral_passed=3`, `total_pnl_diff=+0.0049`

OOS-1での観察整理:
- `simple_trailing_after_1R` は `fixed_sl_tp` を OOS-1 全月で上回った。
- permissive + `simple_trailing_after_1R` は OFF + `simple_trailing_after_1R` を OOS-1 全月で小幅に上回った。
- permissive の効果は小さいが一貫しており、entry集合差分でも `neutral_passed` を伴う軽微な上乗せとして整合した。
- 主効果は trailing exit にあり、permissive は補助的上乗せとして扱う。

暫定判断（Candidate Freeze v0.1）:
- Candidate Freeze v0.1 は OOS-1 では棄却せず、OOS-2へ進める継続候補とする。
- ただし本採用判断ではなく、収益性確認済みを意味しない。
- 実 broker / OANDA API / 実注文送信は未実装、spread=0.2 pips fallback、手数料・スリッページ・スワップ未反映の前提は継続する。

### 6.17 OOS-2 Confirmation Backtest 結果要約（2024-10-01〜2025-01-01）
本節は Candidate Freeze v0.1 の OOS-2 結果記録であり、収益性確認や本採用判断ではない。

月別結果（4条件）:
- 2024-10:
  - OFF + `fixed_sl_tp`: `trade_count=67`, `total_pnl=-0.0130`
  - OFF + `simple_trailing_after_1R`: `trade_count=67`, `total_pnl=0.1472`
  - permissive + `fixed_sl_tp`: `trade_count=71`, `total_pnl=-0.0170`
  - permissive + `simple_trailing_after_1R`: `trade_count=71`, `total_pnl=0.1486`
- 2024-11:
  - OFF + `fixed_sl_tp`: `trade_count=64`, `total_pnl=-0.0040`
  - OFF + `simple_trailing_after_1R`: `trade_count=64`, `total_pnl=0.2901`
  - permissive + `fixed_sl_tp`: `trade_count=66`, `total_pnl=-0.0060`
  - permissive + `simple_trailing_after_1R`: `trade_count=66`, `total_pnl=0.2918`
- 2024-12:
  - OFF + `fixed_sl_tp`: `trade_count=80`, `total_pnl=-0.0080`
  - OFF + `simple_trailing_after_1R`: `trade_count=80`, `total_pnl=0.2018`
  - permissive + `fixed_sl_tp`: `trade_count=84`, `total_pnl=-0.0030`
  - permissive + `simple_trailing_after_1R`: `trade_count=84`, `total_pnl=0.2079`

validation（全12run）:
- `trade_schema_valid=true`
- `decision_schema_valid=true`
- `consistency_valid=true`

entry集合差分（trailing比較）:
- 2024-10: `compare_only=5`, `base_only=1`, `shifted_5min=1`, `neutral_passed=7`, `total_pnl_diff=+0.0014`
- 2024-11: `compare_only=5`, `base_only=3`, `shifted_5min=2`, `neutral_passed=6`, `total_pnl_diff=+0.0017`
- 2024-12: `compare_only=6`, `base_only=2`, `shifted_5min=2`, `neutral_passed=9`, `total_pnl_diff=+0.0061`

OOS-2での観察整理:
- `simple_trailing_after_1R` は `fixed_sl_tp` を OOS-2 全月で上回った。
- permissive + `simple_trailing_after_1R` は OFF + `simple_trailing_after_1R` を OOS-2 全月で小幅に上回った。
- OOS-1/OOS-2 を通じて、主効果は trailing exit、permissive は小幅補助効果として整理する。

暫定判断（Candidate Freeze v0.1）:
- Candidate Freeze v0.1 は OOS-1/OOS-2 では棄却されず、次段階へ進める structural pass 候補とする。
- ただし本採用判断ではなく、収益性確認済み・実運用可能性確認済みを意味しない。
- 実 broker / OANDA API / 実注文送信は未実装、spread=0.2 pips fallback、手数料・スリッページ・スワップ未反映の前提は継続する。

### 6.18 現実耐性確認計画 v0.1
本節は、OOS-1/OOS-2で structural pass 候補となった Candidate Freeze v0.1 が、より現実的な仮定に耐えるかを確認するための計画である。
目的は現候補の耐性確認であり、新ロジック追加や即時ルール変更ではない。

計画の位置づけ:
- 現段階は構造検証であり、本採用判断・収益性確認・実運用可能性確認ではない。
- `simple_trailing_after_1R` と permissive は本採用扱いしない。
- Candidate Freeze v0.1 の売買ロジックは変更しない。
- 重いbacktest実行はユーザーのローカル PowerShell で行う。

優先確認項目:
- spread / commission / slippage / swap の扱いを比較条件として明文化する。
- `simple_trailing_after_1R` の約定仮定（M5 bar内順序不明による楽観性）を監査する。
- M5 experimental結果と M1 replay / conservative / next_bar_activation の整合を確認する。
- 評価を raw pnl だけに依存せず、pips / R / drawdown 系指標へ拡張する必要性を確認する。
- 2024-12 年末データ終端の注記（期間終端影響）を明示する。

検証上の中核論点:
- trailing の強さが戦略構造由来なのか、約定仮定の楽観由来なのかを分離して扱う。
- そのため、exit policy比較と約定仮定監査を同時に混ぜず、観点を分離して記録する。

非対象（本節で実施しないこと）:
- 新しいentry/exitロジック追加
- HTFロジック拡張
- Candidate Freeze v0.1 の変更
- 実 broker / OANDA API / 実注文送信対応

### 6.19 M1 replay 現実耐性確認結果（OOS-2 2024-11）
本節は OOS-2（2024-11）の trailing entry 群を対象とした M1 replay の記録であり、本採用判断・収益性確認・実運用可能性確認ではない。

OFF trailing entry群:
- `baseline_fixed_exit`: `original_trade_count=64`, `accepted_trade_count=63`, `total_pnl=0.120`, `win_rate=39.68`
- `simple_trailing_after_1R`: `original_trade_count=64`, `accepted_trade_count=63`, `total_pnl=1.101`, `win_rate=55.56`
- `simple_trailing_after_1R_conservative`: `original_trade_count=64`, `accepted_trade_count=63`, `total_pnl=0.918`, `win_rate=46.03`
- `simple_trailing_after_1R_next_bar_activation`: `original_trade_count=64`, `accepted_trade_count=63`, `total_pnl=0.176`, `win_rate=46.03`

permissive trailing entry群:
- `baseline_fixed_exit`: `original_trade_count=66`, `accepted_trade_count=65`, `total_pnl=0.100`, `win_rate=38.46`
- `simple_trailing_after_1R`: `original_trade_count=66`, `accepted_trade_count=65`, `total_pnl=1.059`, `win_rate=53.85`
- `simple_trailing_after_1R_conservative`: `original_trade_count=66`, `accepted_trade_count=65`, `total_pnl=0.876`, `win_rate=44.62`
- `simple_trailing_after_1R_next_bar_activation`: `original_trade_count=66`, `accepted_trade_count=65`, `total_pnl=0.156`, `win_rate=44.62`

結果要約:
- `simple_trailing_after_1R` は M1 replay でも `baseline_fixed_exit` を大きく上回った。
- `simple_trailing_after_1R_conservative` でも `baseline_fixed_exit` を上回り、trailing優位は完全なM5楽観だけではなさそうである。
- ただし `simple_trailing_after_1R_next_bar_activation` では優位が大きく縮み、発動タイミング仮定への依存が大きい。
- permissive は M5 では小幅プラスだった一方、今回の M1 replay では OFF より弱く、補助効果は未確認である。

解釈（現実耐性確認の本線）:
- `simple_trailing_after_1R` は有力候補だが、約定仮定依存が残る候補として扱う。
- permissive は補助効果不安定候補として扱い、本採用判断には進めない。
- 現実耐性確認の本線は exit仮定監査であり、特に `conservative` / `next_bar_activation` 比較を継続する。
- M1 replay でも同一バー内 OHLC 順序曖昧性は完全には消えない前提を維持する。

### 6.20 追加M1 replay 現実耐性確認結果（OOS-1 2024-08 / OOS-2 2024-12）
本節は OFF trailing entry群を対象とした追加M1 replay記録であり、本採用判断・収益性確認・実運用可能性確認ではない。

OOS-1 2024-08（OFF trailing entry群）:
- `baseline_fixed_exit`: `total_pnl=-0.090`, `win_rate=28.07`
- `simple_trailing_after_1R`: `total_pnl=1.236`, `win_rate=56.14`
- `simple_trailing_after_1R_conservative`: `total_pnl=0.699`, `win_rate=31.58`
- `simple_trailing_after_1R_next_bar_activation`: `total_pnl=-0.047`, `win_rate=31.58`

OOS-2 2024-12（OFF trailing entry群）:
- `baseline_fixed_exit`: `total_pnl=0.220`, `win_rate=42.50`
- `simple_trailing_after_1R`: `total_pnl=0.663`, `win_rate=56.25`
- `simple_trailing_after_1R_conservative`: `total_pnl=0.502`, `win_rate=46.25`
- `simple_trailing_after_1R_next_bar_activation`: `total_pnl=0.246`, `win_rate=46.25`

追加結果の要約:
- `simple_trailing_after_1R` は複数月の M1 replay でも `baseline_fixed_exit` より強い。
- `simple_trailing_after_1R_conservative` でも `baseline_fixed_exit` を上回り、trailing優位は完全なM5楽観だけではなさそうである。
- ただし `simple_trailing_after_1R_next_bar_activation` では優位が大きく縮み、発動タイミング依存は明確である。
- permissive HTF policy は M1 replay では補助効果が未確認のため、優先度を後退させる。

現実耐性確認での扱い更新:
- `simple_trailing_after_1R` は楽観寄り上限ケースとして扱う。
- `simple_trailing_after_1R_conservative` は今後の現実寄り主比較候補として重視する。
- `simple_trailing_after_1R_next_bar_activation` は安全側ストレステスト軸として維持する。
- 現実耐性確認の主軸は引き続き exit仮定監査とし、cost/slippage/swap 反映設計へ接続する。

### 6.21 cost / slippage / swap 反映方針 v0.1
本節の目的は、trailing優位がコスト控除後も残るかを確認することである。
本採用判断・収益性確認・実運用可能性確認を行う節ではない。

設計スコープ（v0.1）:
- 既存 `trade_logs` / M1 replay summary に対する後処理評価として設計する。
- BacktestRunner 本体へ直ちに組み込まない。
- Candidate Freeze v0.1 の売買ロジックは変更しない。

単位方針（USDJPY）:
- USDJPY は `1 pip = 0.01` price unit として扱う。
- raw pnl から pips 換算列の追加を検討する。
- long/short を問わず `pnl_price_diff / 0.01` を pips として扱う。

コスト項目（v0.1）:
- spread cost
- commission equivalent
- slippage
- swap

優先度（v0.1）:
- slippage:
  - まず片道・往復の固定 pips 控除で扱う。
- commission:
  - pips換算した固定控除で扱う。
- spread:
  - 既存 `spread=0.2 pips fallback` との二重計上を避ける。
  - 既存結果が spread 内包済みかを明示し、未内包分のみ追加控除する。
- swap:
  - day跨ぎ・保有時間依存のため v0.1 では注記または別枠試算とする。

適用順序（後処理計算）:
1. `gross_pnl`
2. `spread_adjustment`
3. `slippage_adjustment`
4. `commission_adjustment`
5. `swap_adjustment`
6. `net_pnl`

比較対象（固定）:
- `baseline_fixed_exit`
- `simple_trailing_after_1R`
- `simple_trailing_after_1R_conservative`
- `simple_trailing_after_1R_next_bar_activation`

優先評価観点:
- `simple_trailing_after_1R_conservative` がコスト控除後も `baseline_fixed_exit` を上回るか。
- `simple_trailing_after_1R_next_bar_activation` がコスト控除後にどこまで悪化するか。
- `simple_trailing_after_1R` の優位がどの程度削られるか。

評価軸の役割:
- `simple_trailing_after_1R`: 楽観寄り上限ケース
- `simple_trailing_after_1R_conservative`: 現実寄り主比較候補
- `simple_trailing_after_1R_next_bar_activation`: 安全側ストレステスト軸

後処理スクリプトの位置づけ（v0.1）:
- `scripts/apply_cost_scenarios_to_m1_replay.py` を使い、既存 `m1_exit_replay_trades.csv` へ cost scenario 後処理評価を適用する。
- BacktestRunner 本体には組み込まず、v0.1 では後処理評価として `gross_pnl/gross_pips/net_pnl/net_pips` を比較する。

### 6.22 Strategy Scope & Calibration Policy v0.1
本節は、Candidate Freeze v0.1 が現在どこまで裁量意図を再現しているかと、未実装領域・調整方針を分離整理するための運用方針である。
本採用判断・収益性確認・実運用可能性確認を行う節ではない。

現在再現している裁量（v0.1 scope）:
- `third_wave_break`
- `detector_chain_temporal`
- `third_candidate_lookback_bars=5`
- `max_entries_per_recent_third_candidate=1`（dedup=1）
- fallback OFF
- `entry_time_mode=m5_close`
- `fixed_sl_tp` / `simple_trailing_after_1R` の exit 比較
- H1 permissive alignment comparison（OFF/default との比較）

未実装の裁量（v0.1 scope外）:
- H4/H1 複合判断
- support/resistance 近接判断
- ATR/volatility filter
- news/event halt
- spread widening halt
- session/time filter
- liquidity filter
- drawdown stop
- daily loss stop
- consecutive loss stop
- risk sizing
- swap/commission/slippage 実反映

現在の停止条件:
- `stop_loss`
- `take_profit`
- `max_holding_bars`
- position保有中の新規entry抑止

未実装の停止条件:
- 日次停止
- 連敗停止
- drawdown停止
- 指標前後停止
- スプレッド拡大停止
- 低流動性時間停止

パラメータ調整方針（calibration policy）:
- Candidate Freeze v0.1 の範囲では、OOS結果を見て即時調整しない。
- 調整が必要な場合は Candidate Freeze v0.2 として別管理する。
- `lookback` / `dedup` / `exit` / HTF条件を同じOOS結果を見ながら逐次変更しない。
- 現時点で許容する追加は、現実耐性確認のためのコスト・約定仮定・評価指標の追加に限定する。

walk-forward / rolling validation 方針:
- 将来パラメータ調整を行う場合は、探索期間・検証期間・未使用確認期間を分離する。
- rolling / walk-forward 方式を候補にする。
- 未来データを使った最適化を禁止する。

古いデータの扱い方針:
- 古い期間を最近期間と同じ重みで最適化に使わない。
- 最近データを主評価に置く。
- 過去データはレジーム耐性・ストレス確認として扱う。
- 古いデータで良い/悪いだけで即判断しない。

v0.1 / v0.2 の区別:
- v0.1 は現在固定候補。
- 追加裁量・停止条件を入れる場合は v0.2 として分離する。
- v0.1 結果と v0.2 結果を混同しない。

### 6.23 Minimum Core v0.1 Completion Gate
本節は、Minimum Core v0.1 をどの条件で構造検証完了（`structural validation complete`）として閉じるかを定義する。
v0.1 は完成EAではなく、最小ロジック核の構造成立確認を目的とする。

v0.1 の目的:
- 最小ロジックが構造的に破綻しないか確認すること。
- `entry / exit / pnl / log / evaluator` の一連の流れが成立することを確認すること。

v0.1 で確認済みの項目:
- `pytest` が通る。
- schema / consistency が `valid`。
- future leak / intrabar leak 防止方針が文書化済み。
- Candidate Freeze v0.1 が固定済み。
- Q1/Q2 を探索済み期間として分離済み。
- OOS-1/OOS-2 で confirmation backtest 実施済み。
- M1 replay による trailing exit の約定仮定監査を実施済み。
- cost/slippage/swap 反映方針 v0.1 を文書化済み。

v0.1 の完了条件（Completion Gate）:
- cost scenario 後処理評価方針が固定されている。
- `simple_trailing_after_1R_conservative` / `simple_trailing_after_1R_next_bar_activation` を含む net評価の実施準備がある。
- v0.1 を `structural validation complete` として閉じる条件が明記されている。
- 未実装裁量・未実装停止条件を v0.2 へ送る方針が明記されている。

v0.1 で完了扱いにしないもの:
- 収益性確認
- 実運用可能性確認
- OANDA / broker 接続
- 実注文送信
- 厳密な slippage / commission / swap
- H4/H1 複合判断
- support/resistance 判定
- ATR/volatility filter
- news/event halt
- spread widening halt
- daily loss stop
- drawdown stop
- risk sizing

v0.1 以後の変更ルール:
- `lookback` / `dedup` / `exit` / HTF 条件を、v0.1 結果を見ながら逐次調整しない。
- 追加・変更が必要な場合は Candidate Freeze v0.2 として別管理する。
- v0.1 結果と v0.2 結果を混同しない。

v0.1 を閉じた後の次工程:
1. cost scenario 後処理評価
2. Minimum Core v0.1 completion 記録
3. Intended EA Behavior v1.0 / v0.2 Roadmap に従った裁量・停止条件の段階実装

### 6.24 cost scenario 後処理評価結果（representative logs）
本節は representative logs に対する後処理評価結果の記録であり、収益性確認・実運用可能性確認・完成EA判定ではない。
前提は `slippage_pips_round_turn=0.2`、`commission_pips_round_turn=0.1`、`additional_spread_pips=0.0`、`spread_already_included=true`、`swap_mode=note_only`。

結果（gross/net pips）:
- OOS-1 2024-08:
  - `baseline_fixed_exit`: `gross=-9.0`, `net=-26.1`
  - `simple_trailing_after_1R`: `gross=123.6`, `net=106.5`
  - `simple_trailing_after_1R_conservative`: `gross=69.9`, `net=52.8`
  - `simple_trailing_after_1R_next_bar_activation`: `gross=-4.7`, `net=-21.8`
- OOS-2 2024-11:
  - `baseline_fixed_exit`: `gross=12.0`, `net=-6.9`
  - `simple_trailing_after_1R`: `gross=110.1`, `net=91.2`
  - `simple_trailing_after_1R_conservative`: `gross=91.8`, `net=72.9`
  - `simple_trailing_after_1R_next_bar_activation`: `gross=17.6`, `net=-1.3`
- OOS-2 2024-12:
  - `baseline_fixed_exit`: `gross=22.0`, `net=-2.0`
  - `simple_trailing_after_1R`: `gross=66.3`, `net=42.3`
  - `simple_trailing_after_1R_conservative`: `gross=50.2`, `net=26.2`
  - `simple_trailing_after_1R_next_bar_activation`: `gross=24.6`, `net=0.6`

評価整理:
- `simple_trailing_after_1R_conservative` は代表3期間すべてで cost控除後も `baseline_fixed_exit` を上回った。
- `simple_trailing_after_1R` は強いが、引き続き楽観寄り上限ケースとして扱う。
- `simple_trailing_after_1R_next_bar_activation` は cost控除後に大きく弱くなり、ストレス軸として扱う。
- `baseline_fixed_exit` は今回の代表ログでは net negative だった。

Minimum Core v0.1 の扱い:
- 上記をもって Minimum Core v0.1 は `structural validation complete` として閉じてよい。
- ただし本結果は収益性確認・実運用可能性確認・完成EA判定を意味しない。
- 以後の追加裁量・停止条件は Candidate Freeze v0.2 として分離する。

### 6.25 Halt / Risk Filter v0.2 Design
本節は、v0.2 で導入候補とする停止フィルター群の実装前仕様を定義する。
目的は利益最大化ではなく、ユーザーが裁量で回避している危険局面を説明可能な停止レイヤーとして定義することにある。

設計目的:
- 指標・ニュース・急変・流動性低下など、危険局面で新規entryを停止する。
- v0.1 の最小核に後付け最適化を行うのではなく、v0.2 の独立仕様として分離する。

v0.2 で定義する停止フィルター:
- `scheduled_event_halt`
- `price_shock_halt`
- `volatility_spike_halt`
- `spread_widening_halt`
- `post_event_or_shock_cooldown`

`scheduled_event_halt`:
- 経済指標・中央銀行イベント前後で新規entryを停止する。
- 対象候補:
  - 米雇用統計
  - CPI
  - FOMC
  - FRB議長発言
  - 日銀金融政策決定会合
  - 為替介入警戒イベント
  - 重要GDP/小売売上/PMI 等
- v0.2 初期は手動CSVまたは固定イベントカレンダー前提とし、API連携は後回し。
- 停止窓の初期候補（本採用値ではなく検証候補）:
  - high impact: `event_time` 前30分〜後60分
  - very high impact: 前60分〜後120分

`price_shock_halt`:
- 短時間で一定pips以上の急変があれば新規entryを停止する。
- 条件候補:
  - 5分で X pips 以上
  - 15分で Y pips 以上
  - 直近N本レンジが通常のK倍以上
- v0.2 初期候補（固定値ではなく検証対象）:
  - M5 1本で 20 pips 以上
  - M15相当で 35 pips 以上

`volatility_spike_halt`:
- ATRまたは直近レンジが通常状態から急拡大した場合に停止する。
- 条件候補:
  - `current_ATR / rolling_median_ATR > 2.0`
  - `recent_range / rolling_median_range > 2.5`
- ATR期間・median windowは未確定パラメータとして扱う。

`spread_widening_halt`:
- spread が通常より拡大した場合に新規entryを停止する。
- 条件候補:
  - `spread_pips > 1.5`
  - または `spread_pips > rolling_median_spread * 3`
- v0.1 の `spread=0.2 pips fallback` では実測できないため、実 spread 変動検証は後回し。
- `post_event_or_shock_cooldown`:
- event/shock 検出後に再開遅延を設ける。
- 候補:
  - event後 60〜120分
  - price shock後 30〜60分
  - volatility spike後、ATR比率が閾値以下へ戻るまで

既存ポジションの扱い（v0.2初期）:
- 主対象は「新規entry停止」。
- 既存ポジションの強制決済は原則しない。
- 将来候補として `risk_reduction` / `forced_flat` / `no_addition` を分離記録する。

ログ列候補:
- `halt_active`
- `halt_reason`
- `halt_source`
- `halt_start_time`
- `halt_end_time`
- `event_id`
- `event_importance`
- `price_shock_pips`
- `volatility_ratio`
- `spread_pips`
- `cooldown_remaining_minutes`

評価指標:
- `halted_entry_count`
- `halt_reason_counts`
- `skipped_trade_pnl_counterfactual`
- `post_halt_trade_count`
- halt中に避けた負け / 逃した勝ち
- `trade_count` 減少だけで評価しない

注意:
- v0.2 Halt Filter は危険局面回避が目的であり、利益を増やす後付け最適化条件として使わない。
- Q1/Q2/OOS-1/OOS-2 を見ながら閾値を都合よく合わせない。
- 初期閾値は仮説として固定し、別期間で確認する。

### 6.26 Halt / Risk Filter v0.2 Implementation Priority
本節は v0.2 Halt Filter の実装順序を明文化する。
方針として、最初は BacktestRunner / PipelineAdapter / RiskFilter 本体へ組み込まず、診断スクリプトで停止候補の挙動を観測する。

実装優先順位:
- P1: `price_shock_halt`
- P1: `volatility_spike_halt`
- P2: `post_event_or_shock_cooldown`
- P3: `scheduled_event_halt`
- P3: `spread_widening_halt`

優先順位の理由:
- `price_shock_halt` / `volatility_spike_halt` は既存 M5 価格データだけで検証可能。
- `scheduled_event_halt` はイベントCSV/カレンダー仕様の先行設計が必要で、次段階。
- `spread_widening_halt` は現状の M5 slice が `spread=0.2 pips fallback` 前提のため、実 spread 変動検証は後回し。
- `post_event_or_shock_cooldown` は `price_shock_halt` / `volatility_spike_halt` 検出に付随して設計する。

診断先行の実装方針:
- 初手は停止条件の本体統合ではなく、診断スクリプトで停止窓と停止対象entry候補を可視化する。
- 目的は収益改善のための後付け最適化ではなく、危険局面回避診断。
- 閾値は本採用値ではなく初期仮説として扱う。
- Q1/Q2/OOS 結果を見ながら閾値を都合よく調整しない。
- 実装後はまず診断を実施し、その後 `Candidate Freeze v0.2` として固定する。

診断スクリプト案:
- `scripts/diagnose_halt_filters_on_m5_slice.py`

入力引数案:
- `--input-csv`（M5 slice）
- `--decision-logs`
- `--trade-logs`
- `--output-dir`
- `--shock-m5-pips`
- `--shock-m15-pips`
- `--atr-window`
- `--atr-median-window`
- `--atr-ratio-threshold`
- `--range-ratio-threshold`
- `--cooldown-minutes-after-shock`
- `--cooldown-minutes-after-volatility-spike`

出力案:
- `halt_windows.csv`
- `halted_entry_candidates.csv`
- `halt_diagnostic_summary.csv`
- `halt_diagnostic_summary.md`

初期閾値候補（仮説）:
- M5 shock >= 20 pips
- M15 shock >= 35 pips
- ATR ratio > 2.0
- recent range ratio > 2.5

評価観点:
- `halted_entry_count`
- `halt_reason_counts`
- `halted_entry_pnl_counterfactual`
- `avoided_loss_pips`
- `missed_profit_pips`
- `net_counterfactual_effect_pips`
- `trade_count_reduction`

### 6.27 HTF v2 Diagnostic Trade Analysis Results

### 概要
HTF v2 diagnostic trade analysis の代表的な実行結果を以下に記録します。本分析は、HTF v2 を diagnostic/explanation layer として扱い、entry filter 化を行わない方針を確認するためのものです。

### 対象 Run
- **Run 名**: oos2_20241101_1201_htf_v2_diag_off_trailing_warmup_semantics
- **取引数**: 64
- **総損益 (total_pnl)**: 0.2901

### 集計結果
#### h4_bias
| Bias     | Trade Count | Total PnL | Average PnL | Win Rate |
|----------|-------------|-----------|-------------|----------|
| Down     | 14          | 0.0262    | 0.00187     | 85.71%   |
| Neutral  | 35          | 0.2167    | 0.00619     | 80.00%   |
| Up       | 15          | 0.0472    | 0.00315     | 93.33%   |

#### h1_context
| Context               | Trade Count | Total PnL | Average PnL | Win Rate |
|-----------------------|-------------|-----------|-------------|----------|
| Aligned Down          | 6           | 0.0224    | 0.00373     | 100.00%  |
| Aligned Up            | 14          | 0.0383    | 0.00273     | 92.86%   |
| Pullback Against H4   | 5           | 0.0126    | 0.00252     | 100.00%  |
| Range or Neutral      | 25          | 0.1676    | 0.00670     | 84.00%   |
| Unknown               | 14          | 0.0492    | 0.00351     | 64.29%   |

#### Policy Diagnostic
| Policy                          | Trade Count | Total PnL | Average PnL | Win Rate |
|---------------------------------|-------------|-----------|-------------|----------|
| Aligned Only Allowed = False    | 53          | 0.2532    | 0.00478     | 81.13%   |
| Aligned Only Allowed = True     | 11          | 0.0369    | 0.00335     | 100.00%  |
| Pullback Permissive Allowed = False | 52      | 0.2530    | 0.00487     | 80.77%   |
| Pullback Permissive Allowed = True  | 12      | 0.0371    | 0.00309     | 100.00%  |

### 解釈と判断
1. **Aligned Only / Pullback Permissive の実 filter 化を行わない理由**:
   - Aligned Only Allowed = True の取引数は 11 件、総損益は 0.0369 と少なく、実 filter 化すると取引数と総利益が大幅に減少する可能性がある。
   - Pullback Permissive Allowed = True も同様に 12 件のみであり、Aligned Only からほぼ増加しない。

2. **Neutral / Range or Neutral / Context Uncertain の解釈**:
   - h4_bias = Neutral と h1_context = Range or Neutral が代表月で大きな利益源となっている。
   - Context Uncertain = True 側も総損益が 0.2168 と大きく、機械的に除外する根拠はない。

3. **Hard Conflict の扱い**:
   - 平均損益が低く監視価値はあるが、総損益はプラスであり、即除外は不可。

4. **次タスク**:
   - HTF v2 を diagnostic/explanation layer として継続する方針を整理。
   - 複数月で同様の分類別損益を確認するか判断。
   - Phase 5 Support/Resistance へ進むか判断。
   - Aligned Only / Pullback Permissive 実 filter 化は保留。

### 6.28 Candidate Freeze v0.1（確認用BT前の候補固定）
- 本節は、探索・構造検証フェーズから確認用バックテスト（confirmation backtest）準備へ移行するための候補固定定義である。
- 収益性確認ではなく、構造検証の次工程管理を目的とする。
- Q1/Q2（2024-01-02〜2024-07-01）は探索・構造検証で使用済み期間として扱い、確認用バックテストの評価期間とは区別する。
- ここから先は、確認用期間の結果を見て即座にルール変更しない。
- 確認用バックテストで崩れた場合は、結果を「候補棄却または再設計理由」として扱う。
- 結果を見ながら逐次調整する場合は、別バージョンとして記録し、元の確認用バックテストと分離する。

Candidate Freeze v0.1:

| Category | Frozen candidate | Notes |
|---|---|---|
| Entry | `third_wave_break` + `detector_chain_temporal` | fallback OFF, lookback=5, dedup=1, `entry_time_mode=m5_close` |
| Exit baseline | `fixed_sl_tp` | comparison baseline |
| Exit candidate | `simple_trailing_after_1R` | experimental exit candidate, not adopted |
| HTF baseline | OFF/default | current/default comparison |
| HTF candidate | permissive | neutral early-entry/added-entry policy |
| Excluded from v0.1 | strict | Q2 matched OFF; keep as future spec comparison |
| Excluded from v0.1 | H4/support-resistance | future candidate |
| Excluded from v0.1 | H1&H4 aligned / H4 bias + H1 context | outside v1 scope |
| Excluded from v0.1 | additional exit modifications | swing-based trailing / trend-break exit are postponed |

### 6.29 Confirmation Backtest Design v0.1
- 本節は Candidate Freeze v0.1 の次工程として、確認用バックテスト（confirmation backtest）の設計を定義する。
- 収益性確認ではなく、「次段階に残す価値があるか」を判定するための確認工程として扱う。
- Q1/Q2 は探索・構造検証に使用済み期間のため、確認用評価から分離する。
- 確認用期間の結果を見ても、その場でルール変更しない。
- ルール変更が必要な場合は Candidate Freeze v0.2 として別管理する。

確認用期間（OOS）:
- OOS-1（第一確認期間）: `2024-07-01` 〜 `2024-10-01`
- OOS-2（第二確認候補）: `2024-10-01` 〜 `2025-01-01`
- 実行順序: まず OOS-1 のみ実行し、結果を見ても即時ルール変更は行わない。

比較条件（v0.1 は4条件に限定）:
1. OFF + `fixed_sl_tp`
2. OFF + `simple_trailing_after_1R`
3. permissive + `fixed_sl_tp`
4. permissive + `simple_trailing_after_1R`

対象外（確認用BT主軸から除外）:
- strict（Q2でOFF一致のため主軸から除外。将来仕様比較候補として保持）
- H4 / support-resistance / H1&H4 aligned / H4 bias + H1 context
- 追加exit改造（swing-based trailing / trend-break exit 含む）

合否判定基準（収益性確認ではない）:
- `simple_trailing_after_1R` が `fixed_sl_tp` より安定しているか
- permissive + trailing が OFF + trailing を上回るか、少なくとも大きく悪化しないか
- 月別で一部月だけに依存していないか
- `trade_count` が少なすぎないか
- schema validation / consistency が valid か
- entry集合差分、`neutral_passed_count`、`shifted_5min_count` を確認する
- 結果が悪い場合は即修正せず、v0.1棄却またはv0.2再設計候補として記録する

OOS-1 合否判定基準（v0.1 運用）:
- 必須条件:
  - 全4条件runで schema validation / consistency が `valid`。
- 比較条件A（exit比較）:
  - OOS-1合計で `simple_trailing_after_1R` が `fixed_sl_tp` より良いこと（OFF比較・permissive比較の双方を確認）。
  - 月別（2024-07/08/09）のうち **2/3以上** で、`simple_trailing_after_1R` が `fixed_sl_tp` より良いこと。
- 比較条件B（policy比較）:
  - OOS-1合計で permissive + trailing が OFF + trailing に対して **同等以上**。
  - 月別（2024-07/08/09）のうち **2/3以上** で、permissive + trailing が OFF + trailing に対して **同等以上**。
- 注意条件:
  - `trade_count` が少なすぎる場合は判定保留とする。
  - 成果が1か月だけに依存する場合は要注意（過適合疑い）として扱う。
  - entry集合差分、`neutral_passed_count`、`shifted_5min_count` を併記し、挙動の整合を確認する。
- 失敗時の扱い:
  - 即時修正は行わず、Candidate Freeze v0.1 棄却または Candidate Freeze v0.2 再設計候補として記録する。

ローカルPowerShell実行テンプレート（実行はユーザー側）:
```powershell
$env:PYTHONPATH='.'

# 例: OOS-1 の4条件実行テンプレート（run_id/out_dirは適宜置換）
python scripts/run_backtest_exit_experiment.py --input-csv <oos1_m5_slice_csv> --run-id <oos1_off_fixed> --output-dir <out_off_fixed> --max-holding-bars 50 --exit-policy fixed_sl_tp --entry-time-mode m5_close --third-candidate-lookback-bars 5 --max-entries-per-recent-third-candidate 1 --disable-heuristic-fallback --start 2024-07-01 --end 2024-10-01
python scripts/run_backtest_exit_experiment.py --input-csv <oos1_m5_slice_csv> --run-id <oos1_off_trailing> --output-dir <out_off_trailing> --max-holding-bars 50 --exit-policy simple_trailing_after_1R --entry-time-mode m5_close --third-candidate-lookback-bars 5 --max-entries-per-recent-third-candidate 1 --disable-heuristic-fallback --start 2024-07-01 --end 2024-10-01
python scripts/run_backtest_exit_experiment.py --input-csv <oos1_m5_slice_csv> --run-id <oos1_perm_fixed> --output-dir <out_perm_fixed> --max-holding-bars 50 --exit-policy fixed_sl_tp --entry-time-mode m5_close --third-candidate-lookback-bars 5 --max-entries-per-recent-third-candidate 1 --disable-heuristic-fallback --htf-filter-enabled --htf-neutral-policy permissive --start 2024-07-01 --end 2024-10-01
python scripts/run_backtest_exit_experiment.py --input-csv <oos1_m5_slice_csv> --run-id <oos1_perm_trailing> --output-dir <out_perm_trailing> --max-holding-bars 50 --exit-policy simple_trailing_after_1R --entry-time-mode m5_close --third-candidate-lookback-bars 5 --max-entries-per-recent-third-candidate 1 --disable-heuristic-fallback --htf-filter-enabled --htf-neutral-policy permissive --start 2024-07-01 --end 2024-10-01
```

### 6.30 OOS-1 Confirmation Backtest 結果要約（2024-07-01〜2024-10-01）
本節は Candidate Freeze v0.1 の OOS-1 結果記録であり、収益性確認や本採用判断ではない。

月別結果（4条件）:
- 2024-07:
  - OFF + `fixed_sl_tp`: `trade_count=75`, `total_pnl=0.0060`
  - OFF + `simple_trailing_after_1R`: `trade_count=75`, `total_pnl=0.1791`
  - permissive + `fixed_sl_tp`: `trade_count=79`, `total_pnl=0.0020`
  - permissive + `simple_trailing_after_1R`: `trade_count=79`, `total_pnl=0.1848`
- 2024-08:
  - OFF + `fixed_sl_tp`: `trade_count=57`, `total_pnl=-0.0240`
  - OFF + `simple_trailing_after_1R`: `trade_count=57`, `total_pnl=0.2703`
  - permissive + `fixed_sl_tp`: `trade_count=58`, `total_pnl=-0.0250`
  - permissive + `simple_trailing_after_1R`: `trade_count=58`, `total_pnl=0.2766`
- 2024-09:
  - OFF + `fixed_sl_tp`: `trade_count=56`, `total_pnl=-0.0110`
  - OFF + `simple_trailing_after_1R`: `trade_count=56`, `total_pnl=0.2578`
  - permissive + `fixed_sl_tp`: `trade_count=57`, `total_pnl=-0.0090`
  - permissive + `simple_trailing_after_1R`: `trade_count=57`, `total_pnl=0.2627`

entry集合差分（trailing比較）:
- 2024-07: `compare_only=7`, `base_only=3`, `shifted_5min=3`, `neutral_passed=8`, `total_pnl_diff=+0.0057`
- 2024-08: `compare_only=2`, `base_only=1`, `shifted_5min=1`, `neutral_passed=2`, `total_pnl_diff=+0.0063`
- 2024-09: `compare_only=2`, `base_only=1`, `shifted_5min=1`, `neutral_passed=3`, `total_pnl_diff=+0.0049`

OOS-1での観察整理:
- `simple_trailing_after_1R` は `fixed_sl_tp` を OOS-1 全月で上回った。
- permissive + `simple_trailing_after_1R` は OFF + `simple_trailing_after_1R` を OOS-1 全月で小幅に上回った。
- permissive の効果は小さいが一貫しており、entry集合差分でも `neutral_passed` を伴う軽微な上乗せとして整合した。
- 主効果は trailing exit にあり、permissive は補助的上乗せとして扱う。

暫定判断（Candidate Freeze v0.1）:
- Candidate Freeze v0.1 は OOS-1 では棄却せず、OOS-2へ進める継続候補とする。
- ただし本採用判断ではなく、収益性確認済みを意味しない。
- 実 broker / OANDA API / 実注文送信は未実装、spread=0.2 pips fallback、手数料・スリッページ・スワップ未反映の前提は継続する。

### 6.31 OOS-2 Confirmation Backtest 結果要約（2024-10-01〜2025-01-01）
本節は Candidate Freeze v0.1 の OOS-2 結果記録であり、収益性確認や本採用判断ではない。

月別結果（4条件）:
- 2024-10:
  - OFF + `fixed_sl_tp`: `trade_count=67`, `total_pnl=-0.0130`
  - OFF + `simple_trailing_after_1R`: `trade_count=67`, `total_pnl=0.1472`
  - permissive + `fixed_sl_tp`: `trade_count=71`, `total_pnl=-0.0170`
  - permissive + `simple_trailing_after_1R`: `trade_count=71`, `total_pnl=0.1486`
- 2024-11:
  - OFF + `fixed_sl_tp`: `trade_count=64`, `total_pnl=-0.0040`
  - OFF + `simple_trailing_after_1R`: `trade_count=64`, `total_pnl=0.2901`
  - permissive + `fixed_sl_tp`: `trade_count=66`, `total_pnl=-0.0060`
  - permissive + `simple_trailing_after_1R`: `trade_count=66`, `total_pnl=0.2918`
- 2024-12:
  - OFF + `fixed_sl_tp`: `trade_count=80`, `total_pnl=-0.0080`
  - OFF + `simple_trailing_after_1R`: `trade_count=80`, `total_pnl=0.2018`
  - permissive + `fixed_sl_tp`: `trade_count=84`, `total_pnl=-0.0030`
  - permissive + `simple_trailing_after_1R`: `trade_count=84`, `total_pnl=0.2079`

validation（全12run）:
- `trade_schema_valid=true`
- `decision_schema_valid=true`
- `consistency_valid=true`

entry集合差分（trailing比較）:
- 2024-10: `compare_only=5`, `base_only=1`, `shifted_5min=1`, `neutral_passed=7`, `total_pnl_diff=+0.0014`
- 2024-11: `compare_only=5`, `base_only=3`, `shifted_5min=2`, `neutral_passed=6`, `total_pnl_diff=+0.0017`
- 2024-12: `compare_only=6`, `base_only=2`, `shifted_5min=2`, `neutral_passed=9`, `total_pnl_diff=+0.0061`

OOS-2での観察整理:
- `simple_trailing_after_1R` は `fixed_sl_tp` を OOS-2 全月で上回った。
- permissive + `simple_trailing_after_1R` は OFF + `simple_trailing_after_1R` を OOS-2 全月で小幅に上回った。
- OOS-1/OOS-2 を通じて、主効果は trailing exit、permissive は小幅補助効果として整理する。

暫定判断（Candidate Freeze v0.1）:
- Candidate Freeze v0.1 は OOS-1/OOS-2 では棄却されず、次段階へ進める structural pass 候補とする。
- ただし本採用判断ではなく、収益性確認済み・実運用可能性確認済みを意味しない。
- 実 broker / OANDA API / 実注文送信は未実装、spread=0.2 pips fallback、手数料・スリッページ・スワップ未反映の前提は継続する。

### 6.32 現実耐性確認計画 v0.1
本節は、OOS-1/OOS-2で structural pass 候補となった Candidate Freeze v0.1 が、より現実的な仮定に耐えるかを確認するための計画である。
目的は現候補の耐性確認であり、新ロジック追加や即時ルール変更ではない。

計画の位置づけ:
- 現段階は構造検証であり、本採用判断・収益性確認・実運用可能性確認ではない。
- `simple_trailing_after_1R` と permissive は本採用扱いしない。
- Candidate Freeze v0.1 の売買ロジックは変更しない。
- 重いbacktest実行はユーザーのローカル PowerShell で行う。

優先確認項目:
- spread / commission / slippage / swap の扱いを比較条件として明文化する。
- `simple_trailing_after_1R` の約定仮定（M5 bar内順序不明による楽観性）を監査する。
- M5 experimental結果と M1 replay / conservative / next_bar_activation の整合を確認する。
- 評価を raw pnl だけに依存せず、pips / R / drawdown 系指標へ拡張する必要性を確認する。
- 2024-12 年末データ終端の注記（期間終端影響）を明示する。

検証上の中核論点:
- trailing の強さが戦略構造由来なのか、約定仮定の楽観由来なのかを分離して扱う。
- そのため、exit policy比較と約定仮定監査を同時に混ぜず、観点を分離して記録する。

非対象（本節で実施しないこと）:
- 新しいentry/exitロジック追加
- HTFロジック拡張
- Candidate Freeze v0.1 の変更
- 実 broker / OANDA API / 実注文送信対応

### 6.33 M1 replay 現実耐性確認結果（OOS-2 2024-11）
本節は OOS-2（2024-11）の trailing entry 群を対象とした M1 replay の記録であり、本採用判断・収益性確認・実運用可能性確認ではない。

OFF trailing entry群:
- `baseline_fixed_exit`: `original_trade_count=64`, `accepted_trade_count=63`, `total_pnl=0.120`, `win_rate=39.68`
- `simple_trailing_after_1R`: `original_trade_count=64`, `accepted_trade_count=63`, `total_pnl=1.101`, `win_rate=55.56`
- `simple_trailing_after_1R_conservative`: `original_trade_count=64`, `accepted_trade_count=63`, `total_pnl=0.918`, `win_rate=46.03`
- `simple_trailing_after_1R_next_bar_activation`: `original_trade_count=64`, `accepted_trade_count=63`, `total_pnl=0.176`, `win_rate=46.03`

permissive trailing entry群:
- `baseline_fixed_exit`: `original_trade_count=66`, `accepted_trade_count=65`, `total_pnl=0.100`, `win_rate=38.46`
- `simple_trailing_after_1R`: `original_trade_count=66`, `accepted_trade_count=65`, `total_pnl=1.059`, `win_rate=53.85`
- `simple_trailing_after_1R_conservative`: `original_trade_count=66`, `accepted_trade_count=65`, `total_pnl=0.876`, `win_rate=44.62`
- `simple_trailing_after_1R_next_bar_activation`: `original_trade_count=66`, `accepted_trade_count=65`, `total_pnl=0.156`, `win_rate=44.62`

結果要約:
- `simple_trailing_after_1R` は M1 replay でも `baseline_fixed_exit` を大きく上回った。
- `simple_trailing_after_1R_conservative` でも `baseline_fixed_exit` を上回り、trailing優位は完全なM5楽観だけではなさそうである。
- ただし `simple_trailing_after_1R_next_bar_activation` では優位が大きく縮み、発動タイミング仮定への依存が大きい。
- permissive は M5 では小幅プラスだった一方、今回の M1 replay では OFF より弱く、補助効果は未確認である。

解釈（現実耐性確認の本線）:
- `simple_trailing_after_1R` は有力候補だが、約定仮定依存が残る候補として扱う。
- permissive は補助効果不安定候補として扱い、本採用判断には進めない。
- 現実耐性確認の本線は exit仮定監査であり、特に `conservative` / `next_bar_activation` 比較を継続する。
- M1 replay でも同一バー内 OHLC 順序曖昧性は完全には消えない前提を維持する。

### 6.34 追加M1 replay 現実耐性確認結果（OOS-1 2024-08 / OOS-2 2024-12）
本節は OFF trailing entry群を対象とした追加M1 replay記録であり、本採用判断・収益性確認・実運用可能性確認ではない。

OOS-1 2024-08（OFF trailing entry群）:
- `baseline_fixed_exit`: `total_pnl=-0.090`, `win_rate=28.07`
- `simple_trailing_after_1R`: `total_pnl=1.236`, `win_rate=56.14`
- `simple_trailing_after_1R_conservative`: `total_pnl=0.699`, `win_rate=31.58`
- `simple_trailing_after_1R_next_bar_activation`: `total_pnl=-0.047`, `win_rate=31.58`

OOS-2 2024-12（OFF trailing entry群）:
- `baseline_fixed_exit`: `total_pnl=0.220`, `win_rate=42.50`
- `simple_trailing_after_1R`: `total_pnl=0.663`, `win_rate=56.25`
- `simple_trailing_after_1R_conservative`: `total_pnl=0.502`, `win_rate=46.25`
- `simple_trailing_after_1R_next_bar_activation`: `total_pnl=0.246`, `win_rate=46.25`

追加結果の要約:
- `simple_trailing_after_1R` は複数月の M1 replay でも `baseline_fixed_exit` より強い。
- `simple_trailing_after_1R_conservative` でも `baseline_fixed_exit` を上回り、trailing優位は完全なM5楽観だけではなさそうである。
- ただし `simple_trailing_after_1R_next_bar_activation` では優位が大きく縮み、発動タイミング依存は明確である。
- permissive HTF policy は M1 replay では補助効果が未確認のため、優先度を後退させる。

現実耐性確認での扱い更新:
- `simple_trailing_after_1R` は楽観寄り上限ケースとして扱う。
- `simple_trailing_after_1R_conservative` は今後の現実寄り主比較候補として重視する。
- `simple_trailing_after_1R_next_bar_activation` は安全側ストレステスト軸として維持する。
- 現実耐性確認の主軸は引き続き exit仮定監査とし、cost/slippage/swap 反映設計へ接続する。

### 6.35 cost / slippage / swap 反映方針 v0.1
本節の目的は、trailing優位がコスト控除後も残るかを確認することである。
本採用判断・収益性確認・実運用可能性確認を行う節ではない。

設計スコープ（v0.1）:
- 既存 `trade_logs` / M1 replay summary に対する後処理評価として設計する。
- BacktestRunner 本体へ直ちに組み込まない。
- Candidate Freeze v0.1 の売買ロジックは変更しない。

単位方針（USDJPY）:
- USDJPY は `1 pip = 0.01` price unit として扱う。
- raw pnl から pips 換算列の追加を検討する。
- long/short を問わず `pnl_price_diff / 0.01` を pips として扱う。

コスト項目（v0.1）:
- spread cost
- commission equivalent
- slippage
- swap

優先度（v0.1）:
- slippage:
  - まず片道・往復の固定 pips 控除で扱う。
- commission:
  - pips換算した固定控除で扱う。
- spread:
  - 既存 `spread=0.2 pips fallback` との二重計上を避ける。
  - 既存結果が spread 内包済みかを明示し、未内包分のみ追加控除する。
- swap:
  - day跨ぎ・保有時間依存のため v0.1 では注記または別枠試算とする。

適用順序（後処理計算）:
1. `gross_pnl`
2. `spread_adjustment`
3. `slippage_adjustment`
4. `commission_adjustment`
5. `swap_adjustment`
6. `net_pnl`

比較対象（固定）:
- `baseline_fixed_exit`
- `simple_trailing_after_1R`
- `simple_trailing_after_1R_conservative`
- `simple_trailing_after_1R_next_bar_activation`

優先評価観点:
- `simple_trailing_after_1R_conservative` がコスト控除後も `baseline_fixed_exit` を上回るか。
- `simple_trailing_after_1R_next_bar_activation` がコスト控除後にどこまで悪化するか。
- `simple_trailing_after_1R` の優位がどの程度削られるか。

評価軸の役割:
- `simple_trailing_after_1R`: 楽観寄り上限ケース
- `simple_trailing_after_1R_conservative`: 現実寄り主比較候補
- `simple_trailing_after_1R_next_bar_activation`: 安全側ストレステスト軸

後処理スクリプトの位置づけ（v0.1）:
- `scripts/apply_cost_scenarios_to_m1_replay.py` を使い、既存 `m1_exit_replay_trades.csv` へ cost scenario 後処理評価を適用する。
- BacktestRunner 本体には組み込まず、v0.1 では後処理評価として `gross_pnl/gross_pips/net_pnl/net_pips` を比較する。

### 6.36 Strategy Scope & Calibration Policy v0.1
本節は、Candidate Freeze v0.1 が現在どこまで裁量意図を再現しているかと、未実装領域・調整方針を分離整理するための運用方針である。
本採用判断・収益性確認・実運用可能性確認を行う節ではない。

現在再現している裁量（v0.1 scope）:
- `third_wave_break`
- `detector_chain_temporal`
- `third_candidate_lookback_bars=5`
- `max_entries_per_recent_third_candidate=1`（dedup=1）
- fallback OFF
- `entry_time_mode=m5_close`
- `fixed_sl_tp` / `simple_trailing_after_1R` の exit 比較
- H1 permissive alignment comparison（OFF/default との比較）

未実装の裁量（v0.1 scope外）:
- H4/H1 複合判断
- support/resistance 近接判断
- ATR/volatility filter
- news/event halt
- spread widening halt
- session/time filter
- liquidity filter
- drawdown stop
- daily loss stop
- consecutive loss stop
- risk sizing
- swap/commission/slippage 実反映

現在の停止条件:
- `stop_loss`
- `take_profit`
- `max_holding_bars`
- position保有中の新規entry抑止

未実装の停止条件:
- 日次停止
- 連敗停止
- drawdown停止
- 指標前後停止
- スプレッド拡大停止
- 低流動性時間停止

パラメータ調整方針（calibration policy）:
- Candidate Freeze v0.1 の範囲では、OOS結果を見て即時調整しない。
- 調整が必要な場合は Candidate Freeze v0.2 として別管理する。
- `lookback` / `dedup` / `exit` / HTF条件を同じOOS結果を見ながら逐次変更しない。
- 現時点で許容する追加は、現実耐性確認のためのコスト・約定仮定・評価指標の追加に限定する。

walk-forward / rolling validation 方針:
- 将来パラメータ調整を行う場合は、探索期間・検証期間・未使用確認期間を分離する。
- rolling / walk-forward 方式を候補にする。
- 未来データを使った最適化を禁止する。

古いデータの扱い方針:
- 古い期間を最近期間と同じ重みで最適化に使わない。
- 最近データを主評価に置く。
- 過去データはレジーム耐性・ストレス確認として扱う。
- 古いデータで良い/悪いだけで即判断しない。

v0.1 / v0.2 の区別:
- v0.1 は現在固定候補。
- 追加裁量・停止条件を入れる場合は v0.2 として分離する。
- v0.1 結果と v0.2 結果を混同しない。

### 6.37 Minimum Core v0.1 Completion Gate
本節は、Minimum Core v0.1 をどの条件で構造検証完了（`structural validation complete`）として閉じるかを定義する。
v0.1 は完成EAではなく、最小ロジック核の構造成立確認を目的とする。

v0.1 の目的:
- 最小ロジックが構造的に破綻しないか確認すること。
- `entry / exit / pnl / log / evaluator` の一連の流れが成立することを確認すること。

v0.1 で確認済みの項目:
- `pytest` が通る。
- schema / consistency が `valid`。
- future leak / intrabar leak 防止方針が文書化済み。
- Candidate Freeze v0.1 が固定済み。
- Q1/Q2 を探索済み期間として分離済み。
- OOS-1/OOS-2 で confirmation backtest 実施済み。
- M1 replay による trailing exit の約定仮定監査を実施済み。
- cost/slippage/swap 反映方針 v0.1 を文書化済み。

v0.1 の完了条件（Completion Gate）:
- cost scenario 後処理評価方針が固定されている。
- `simple_trailing_after_1R_conservative` / `simple_trailing_after_1R_next_bar_activation` を含む net評価の実施準備がある。
- v0.1 を `structural validation complete` として閉じる条件が明記されている。
- 未実装裁量・未実装停止条件を v0.2 へ送る方針が明記されている。

v0.1 で完了扱いにしないもの:
- 収益性確認
- 実運用可能性確認
- OANDA / broker 接続
- 実注文送信
- 厳密な slippage / commission / swap
- H4/H1 複合判断
- support/resistance 判定
- ATR/volatility filter
- news/event halt
- spread widening halt
- daily loss stop
- drawdown stop
- risk sizing

v0.1 以後の変更ルール:
- `lookback` / `dedup` / `exit` / HTF 条件を、v0.1 結果を見ながら逐次調整しない。
- 追加・変更が必要な場合は Candidate Freeze v0.2 として別管理する。
- v0.1 結果と v0.2 結果を混同しない。

v0.1 を閉じた後の次工程:
1. cost scenario 後処理評価
2. Minimum Core v0.1 completion 記録
3. Intended EA Behavior v1.0 / v0.2 Roadmap に従った裁量・停止条件の段階実装

### 6.38 cost scenario 後処理評価結果（representative logs）
本節は representative logs に対する後処理評価結果の記録であり、収益性確認・実運用可能性確認・完成EA判定ではない。
前提は `slippage_pips_round_turn=0.2`、`commission_pips_round_turn=0.1`、`additional_spread_pips=0.0`、`spread_already_included=true`、`swap_mode=note_only`。

結果（gross/net pips）:
- OOS-1 2024-08:
  - `baseline_fixed_exit`: `gross=-9.0`, `net=-26.1`
  - `simple_trailing_after_1R`: `gross=123.6`, `net=106.5`
  - `simple_trailing_after_1R_conservative`: `gross=69.9`, `net=52.8`
  - `simple_trailing_after_1R_next_bar_activation`: `gross=-4.7`, `net=-21.8`
- OOS-2 2024-11:
  - `baseline_fixed_exit`: `gross=12.0`, `net=-6.9`
  - `simple_trailing_after_1R`: `gross=110.1`, `net=91.2`
  - `simple_trailing_after_1R_conservative`: `gross=91.8`, `net=72.9`
  - `simple_trailing_after_1R_next_bar_activation`: `gross=17.6`, `net=-1.3`
- OOS-2 2024-12:
  - `baseline_fixed_exit`: `gross=22.0`, `net=-2.0`
  - `simple_trailing_after_1R`: `gross=66.3`, `net=42.3`
  - `simple_trailing_after_1R_conservative`: `gross=50.2`, `net=26.2`
  - `simple_trailing_after_1R_next_bar_activation`: `gross=24.6`, `net=0.6`

評価整理:
- `simple_trailing_after_1R_conservative` は代表3期間すべてで cost控除後も `baseline_fixed_exit` を上回った。
- `simple_trailing_after_1R` は強いが、引き続き楽観寄り上限ケースとして扱う。
- `simple_trailing_after_1R_next_bar_activation` は cost控除後に大きく弱くなり、ストレス軸として扱う。
- `baseline_fixed_exit` は今回の代表ログでは net negative だった。

Minimum Core v0.1 の扱い:
- 上記をもって Minimum Core v0.1 は `structural validation complete` として閉じてよい。
- ただし本結果は収益性確認・実運用可能性確認・完成EA判定を意味しない。
- 以後の追加裁量・停止条件は Candidate Freeze v0.2 として分離する。

### 6.39 Halt / Risk Filter v0.2 Design
本節は、v0.2 で導入候補とする停止フィルター群の実装前仕様を定義する。
目的は利益最大化ではなく、ユーザーが裁量で回避している危険局面を説明可能な停止レイヤーとして定義することにある。

設計目的:
- 指標・ニュース・急変・流動性低下など、危険局面で新規entryを停止する。
- v0.1 の最小核に後付け最適化を行うのではなく、v0.2 の独立仕様として分離する。

v0.2 で定義する停止フィルター:
- `scheduled_event_halt`
- `price_shock_halt`
- `volatility_spike_halt`
- `spread_widening_halt`
- `post_event_or_shock_cooldown`

`scheduled_event_halt`:
- 経済指標・中央銀行イベント前後で新規entryを停止する。
- 対象候補:
  - 米雇用統計
  - CPI
  - FOMC
  - FRB議長発言
  - 日銀金融政策決定会合
  - 為替介入警戒イベント
  - 重要GDP/小売売上/PMI 等
- v0.2 初期は手動CSVまたは固定イベントカレンダー前提とし、API連携は後回し。
- 停止窓の初期候補（本採用値ではなく検証候補）:
  - high impact: `event_time` 前30分〜後60分
  - very high impact: 前60分〜後120分

`price_shock_halt`:
- 短時間で一定pips以上の急変があれば新規entryを停止する。
- 条件候補:
  - 5分で X pips 以上
  - 15分で Y pips 以上
  - 直近N本レンジが通常のK倍以上
- v0.2 初期候補（固定値ではなく検証対象）:
  - M5 1本で 20 pips 以上
  - M15相当で 35 pips 以上

`volatility_spike_halt`:
- ATRまたは直近レンジが通常状態から急拡大した場合に停止する。
- 条件候補:
  - `current_ATR / rolling_median_ATR > 2.0`
  - `recent_range / rolling_median_range > 2.5`
- ATR期間・median windowは未確定パラメータとして扱う。

`spread_widening_halt`:
- spread が通常より拡大した場合に新規entryを停止する。
- 条件候補:
  - `spread_pips > 1.5`
  - または `spread_pips > rolling_median_spread * 3`
- v0.1 の `spread=0.2 pips fallback` では実測できないため、実 spread 変動検証は後回し。
- `post_event_or_shock_cooldown`:
- event/shock 検出後に再開遅延を設ける。
- 候補:
  - event後 60〜120分
  - price shock後 30〜60分
  - volatility spike後、ATR比率が閾値以下へ戻るまで

既存ポジションの扱い（v0.2初期）:
- 主対象は「新規entry停止」。
- 既存ポジションの強制決済は原則しない。
- 将来候補として `risk_reduction` / `forced_flat` / `no_addition` を分離記録する。

ログ列候補:
- `halt_active`
- `halt_reason`
- `halt_source`
- `halt_start_time`
- `halt_end_time`
- `event_id`
- `event_importance`
- `price_shock_pips`
- `volatility_ratio`
- `spread_pips`
- `cooldown_remaining_minutes`

評価指標:
- `halted_entry_count`
- `halt_reason_counts`
- `skipped_trade_pnl_counterfactual`
- `post_halt_trade_count`
- halt中に避けた負け / 逃した勝ち
- `trade_count` 減少だけで評価しない

注意:
- v0.2 Halt Filter は危険局面回避が目的であり、利益を増やす後付け最適化条件として使わない。
- Q1/Q2/OOS-1/OOS-2 を見ながら閾値を都合よく合わせない。
- 初期閾値は仮説として固定し、別期間で確認する。

### 6.40 Halt / Risk Filter v0.2 Implementation Priority
本節は v0.2 Halt Filter の実装順序を明文化する。
方針として、最初は BacktestRunner / PipelineAdapter / RiskFilter 本体へ組み込まず、診断スクリプトで停止候補の挙動を観測する。

実装優先順位:
- P1: `price_shock_halt`
- P1: `volatility_spike_halt`
- P2: `post_event_or_shock_cooldown`
- P3: `scheduled_event_halt`
- P3: `spread_widening_halt`

優先順位の理由:
- `price_shock_halt` / `volatility_spike_halt` は既存 M5 価格データだけで検証可能。
- `scheduled_event_halt` はイベントCSV/カレンダー仕様の先行設計が必要で、次段階。
- `spread_widening_halt` は現状の M5 slice が `spread=0.2 pips fallback` 前提のため、実 spread 変動検証は後回し。
- `post_event_or_shock_cooldown` は `price_shock_halt` / `volatility_spike_halt` 検出に付随して設計する。

診断先行の実装方針:
- 初手は停止条件の本体統合ではなく、診断スクリプトで停止窓と停止対象entry候補を可視化する。
- 目的は収益改善のための後付け最適化ではなく、危険局面回避診断。
- 閾値は本採用値ではなく初期仮説として扱う。
- Q1/Q2/OOS 結果を見ながら閾値を都合よく調整しない。
- 実装後はまず診断を実施し、その後 `Candidate Freeze v0.2` として固定する。

診断スクリプト案:
- `scripts/diagnose_halt_filters_on_m5_slice.py`

入力引数案:
- `--input-csv`（M5 slice）
- `--decision-logs`
- `--trade-logs`
- `--output-dir`
- `--shock-m5-pips`
- `--shock-m15-pips`
- `--atr-window`
- `--atr-median-window`
- `--atr-ratio-threshold`
- `--range-ratio-threshold`
- `--cooldown-minutes-after-shock`
- `--cooldown-minutes-after-volatility-spike`

出力案:
- `halt_windows.csv`
- `halted_entry_candidates.csv`
- `halt_diagnostic_summary.csv`
- `halt_diagnostic_summary.md`

初期閾値候補（仮説）:
- M5 shock >= 20 pips
- M15 shock >= 35 pips
- ATR ratio > 2.0
- recent range ratio > 2.5

評価観点:
- `halted_entry_count`
- `halt_reason_counts`
- `halted_entry_pnl_counterfactual`
- `avoided_loss_pips`
- `missed_profit_pips`
- `net_counterfactual_effect_pips`
- `trade_count_reduction`

### 6.41 Phase 2 Halt/Risk diagnostic I/O contract
本節は `EA Master Implementation Roadmap v0.2+` の Phase 2（Halt/Risk diagnostic layer）に進むための実装前仕様を固定する。
今回は診断スクリプトの I/O・判定・出力・テスト観点の明文化のみを対象とし、スクリプト実装・本体統合は対象外とする。

### 6.42 対象範囲と非対象
対象:
- `price_shock_halt` 診断仕様
- `volatility_spike_halt` 診断仕様
- halt window 生成・統合・entry候補突合の counterfactual 診断仕様

非対象:
- Backtest 実行
- 売買ロジック変更
- RiskFilter / PipelineAdapter への halt 本体統合
- `scheduled_event_halt` / `spread_widening_halt` 実装

前提:
- 実 broker / OANDA API / 実注文送信は未実装。
- 収益性確認済みではない。
- 閾値は初期仮説であり本採用値ではない。
- Q1/Q2/OOS 結果に合わせた都合のよい閾値最適化は行わない。

### 6.43 診断スクリプト候補
- `scripts/diagnose_halt_filters_on_m5_slice.py`

### 6.44 CLI I/O contract
入力引数:
- `--input-csv`（M5 slice）
- `--decision-logs`
- `--trade-logs`
- `--output-dir`
- `--shock-m5-pips`
- `--shock-m15-pips`
- `--atr-window`
- `--atr-median-window`
- `--atr-ratio-threshold`
- `--range-ratio-threshold`
- `--cooldown-minutes-after-shock`
- `--cooldown-minutes-after-volatility-spike`

入出力の基本契約:
- `input-csv` は時系列昇順で扱う。
- `decision-logs` / `trade-logs` は entry 候補または実 entry を持つログとして読み込む。
- 診断は counterfactual とし、実際の entry を止めない。
- 出力は `output-dir` に CSV/MD を生成する。

### 6.45 M5 slice 必須列
必須列:
- `timestamp`
- `open`
- `high`
- `low`
- `close`

任意列:
- `spread`
- `volume`

補足:
- `timestamp` 欠損、OHLC 欠損、または `high < low` は入力異常として扱う。

### 6.46 decision_logs / trade_logs の利用契約
- entry候補時刻（decision_logs）または実entry時刻（trade_logs）を halt window と突合する。
- halt中に発生した entry 候補/実 entry は `halted_entry_candidate` として記録する。
- 本フェーズでは「停止したらどうなったか」を後追い比較する counterfactual 診断に限定する。

### 6.47 price_shock_halt 判定仕様
M5 shock:
- 各 M5 バーの `range_pips = (high - low) * pip_scale` を計算。
- `range_pips >= shock_m5_pips` で shock trigger を成立させる。

M15 shock（M5 3本ローリング）:
- 3本ローリング区間で `rolling_high - rolling_low` を計算し pips 化する。
- `m15_equivalent_range_pips >= shock_m15_pips` で shock trigger を成立させる。

shock window:
- trigger 時刻を起点に halt window を開始する。
- 終了時刻は `cooldown_minutes_after_shock` を加算して決める。

### 6.48 volatility_spike_halt 判定仕様
volatility 指標:
- true range または ATR を算出する（実装時は計算方法を明示固定する）。
- `atr_ratio = current_ATR / rolling_median_ATR`
- `range_ratio = recent_range / rolling_median_range`

spike 判定:
- `atr_ratio > atr_ratio_threshold` または `range_ratio > range_ratio_threshold` のいずれか成立で spike trigger。

spike window:
- trigger 時刻を起点に halt window を開始する。
- 終了時刻は `cooldown_minutes_after_volatility_spike` を加算して決める。

### 6.49 halt window 統合ルール
- shock/spike の各 trigger から生成した window を時系列に並べる。
- 時間重複または接続（end と next start が連続）する window は結合する。
- 結合後 window は複数理由を保持可能にする（例: `price_shock_halt|volatility_spike_halt`）。
- `cooldown` の終了時刻は、結合対象で最も遅い終了時刻を採用する。

### 6.50 出力ファイル契約
生成ファイル:
- `halt_windows.csv`
- `halted_entry_candidates.csv`
- `halt_diagnostic_summary.csv`
- `halt_diagnostic_summary.md`

`halt_windows.csv` 列候補:
- `halt_start_time`
- `halt_end_time`
- `halt_reason`
- `halt_source`
- `trigger_time`
- `trigger_value_pips`
- `atr_ratio`
- `range_ratio`
- `cooldown_minutes`

`halted_entry_candidates.csv` 列候補:
- `entry_time`
- `signal_type`
- `trade_id`（任意）
- `pnl`（任意）
- `halt_reason`
- `halt_start_time`
- `halt_end_time`
- `would_be_halted`
- `counterfactual_pnl`

`halt_diagnostic_summary.csv` / `.md` 指標:
- `halt_window_count`
- `total_halt_minutes`
- `halted_entry_count`
- `halt_reason_counts`
- `avoided_loss_pips`
- `missed_profit_pips`
- `net_counterfactual_effect_pips`
- `trade_count_reduction`

### 6.51 評価時の注意
- `trade_count` 減少だけで評価しない。
- `avoided_loss_pips` と `missed_profit_pips` を両方評価する。
- halt filter は利益最大化ではなく危険局面回避診断のために使う。
- 本体統合の可否は Phase 3 で判断する。

### 6.52 テスト観点（実装前固定）
入力検証:
- M5 必須列欠損時の失敗。
- timestamp 非昇順・重複の検出。

判定検証:
- M5 shock 境界値（閾値ちょうど/未満/超過）。
- M15 shock 3本ローリング境界値。
- ATR ratio / range ratio の境界値。

window 検証:
- shock/spike 単独 window 生成。
- 重複 window の結合。
- 複数 reason 保持。
- cooldown 終了時刻の最大値採用。

突合検証:
- halt window 内 entry の `would_be_halted=true`。
- window 外 entry の非該当確認。
- decision/trade 両ログ入力時の重複扱い方針確認（実装時に優先規則を固定）。

出力検証:
- 4ファイル生成確認。
- 列スキーマ整合確認。
- summary 指標の整合（件数合計一致）。

### 6.53 Phase 2 診断スクリプト実装メモ（2026-05-03）
- `scripts/diagnose_halt_filters_on_m5_slice.py` を追加し、`price_shock_halt` / `volatility_spike_halt` の counterfactual 診断を実装した。
- 本実装は M5 slice と既存 logs を使う診断専用であり、RiskFilter / PipelineAdapter への本体統合は行っていない。
- `halt_windows.csv` / `halted_entry_candidates.csv` / `halt_diagnostic_summary.csv` / `halt_diagnostic_summary.md` を出力する。
- これは構造診断であり、収益性確認や閾値本採用を意味しない。

### 6.54 decision_logs 互換性補足（2026-05-03）
- Phase 2 halt診断では `trade_logs` を優先し、`decision_logs` は補助入力として扱う。
- 実ログでは `decision_logs` に `entry_time` / `signal_type` が無い場合があるため、`trade_logs` から候補取得できる場合は decision 側不足で診断を停止しない。
- ただし `trade_logs` 由来候補が無く、かつ decision 側必須列も無い場合は入力不備としてエラー扱いにする。

### 6.55 summary単位（pips換算）補足と再診断方針（2026-05-03）
- Phase 2 halt診断では、`trade_logs.pnl` が price unit の場合、summary 指標（`avoided_loss_pips` / `missed_profit_pips` / `net_counterfactual_effect_pips`）は `pip_size` により pips 換算して評価する。
- 換算式は `pnl_pips = counterfactual_pnl / pip_size` とする。
- OOS-2 2024-11 OFF trailing の初回診断では、初期閾値で halt が広く発火し、`halt_window_count=87`、`halted_entry_count=23` を確認した。
- ただし初回値には summary 単位の解釈余地があったため、Phase 3 統合へ進まず、単位修正後に同一条件で再診断する。

### 6.56 Phase 2 初回診断結果（OOS-2 2024-11 OFF trailing）と次方針
実行条件（固定）:
- input-csv: `data/private/backtest_slices/USDJPY_M5_2024-11-01_2024-12-01.csv`
- decision-logs: `logs/backtest_runs/oos2_20241101_1201_htf_off_trailing/decision_logs.csv`
- trade-logs: `logs/backtest_runs/oos2_20241101_1201_htf_off_trailing/trade_logs.csv`
- `shock_m5_pips=20`
- `shock_m15_pips=35`
- `atr_window=14`
- `atr_median_window=50`
- `atr_ratio_threshold=2.0`
- `range_ratio_threshold=2.5`
- `cooldown_after_shock=60`
- `cooldown_after_volatility_spike=45`
- `instrument=USDJPY`
- `pip_size=0.01`

初回結果:
- `halt_window_count=87`
- `total_halt_minutes=9215.0`
- `halted_entry_count=23`
- `halt_reason_counts=price_shock_halt:44|volatility_spike_halt:75`
- `avoided_loss_pips=0.10`
- `missed_profit_pips=16.87`
- `net_counterfactual_effect_pips=-16.77`
- `trade_count_reduction=23`
- warning: `decision_logs missing required columns and skipped: ['entry_time', 'signal_type']`

解釈（構造診断）:
- 初期閾値では halt が広く効きすぎている可能性が高い。
- stopped entries は負け回避より利益機会停止が大きい。
- `volatility_spike_halt` の発火数が多く、過剰停止の主因候補。

判断:
- 現時点では Phase 3 本体統合に進まない。
- まず Phase 2 内で分解診断を行い、停止要因を切り分ける。

次方針（閾値はこの場で変更しない）:
- `price_shock_halt` 単独診断。
- `volatility_spike_halt` 単独診断。
- halt reason 別 halted entry 損益分解。
- cooldown 時間の影響診断。
- 閾値調整は必要なら Phase 2 の別シナリオとして記録し、閾値本採用扱いはしない。

注意:
- これは収益性確認ではない。
- これは閾値本採用ではない。

### 6.57 分離診断用 filter toggle CLI（2026-05-03）
- Phase 2 で `price_shock_halt` と `volatility_spike_halt` の寄与を分離診断するため、`scripts/diagnose_halt_filters_on_m5_slice.py` に以下を追加した。
  - `--enable-price-shock`
  - `--enable-volatility-spike`
- 未指定時は後方互換として両方有効（既存挙動維持）。
- 初回診断で halt が広く効きすぎていたため、Phase 3 本体統合前に単独診断・寄与分解を先行する。
- これは構造診断であり、収益性確認や閾値本採用を意味しない。

### 6.58 Phase 2 分離診断結果（OOS-2 2024-11 OFF trailing）
実行条件（固定）:
- input-csv: `data/private/backtest_slices/USDJPY_M5_2024-11-01_2024-12-01.csv`
- decision-logs: `logs/backtest_runs/oos2_20241101_1201_htf_off_trailing/decision_logs.csv`
- trade-logs: `logs/backtest_runs/oos2_20241101_1201_htf_off_trailing/trade_logs.csv`
- `shock_m5_pips=20`
- `shock_m15_pips=35`
- `atr_window=14`
- `atr_median_window=50`
- `atr_ratio_threshold=2.0`
- `range_ratio_threshold=2.5`
- `cooldown_after_shock=60`
- `cooldown_after_volatility_spike=45`
- `instrument=USDJPY`
- `pip_size=0.01`

結果比較:

| scenario | enabled_filters | halt_window_count | total_halt_minutes | halted_entry_count | halt_reason_counts | avoided_loss_pips | missed_profit_pips | net_counterfactual_effect_pips | trade_count_reduction |
| --- | --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: |
| combined | price_shock_halt + volatility_spike_halt | 87 | 9215.0 | 23 | price_shock_halt:44\|volatility_spike_halt:75 | 0.10 | 16.87 | -16.77 | 23 |
| price_shock only | price_shock_halt | 44 | 5495.0 | 11 | price_shock_halt:44 | 0.00 | 6.07 | -6.07 | 11 |
| volatility_spike only | volatility_spike_halt | 81 | 7040.0 | 17 | volatility_spike_halt:81 | 0.10 | 13.42 | -13.32 | 17 |

解釈（構造診断）:
- 初期閾値では combined / price_shock only / volatility_spike only の全シナリオで `net_counterfactual_effect_pips` がマイナス。
- `price_shock_halt` 単独でも利益機会停止（`missed_profit_pips`）が残る。
- `volatility_spike_halt` は発火数・停止時間・`missed_profit_pips` が大きく、過剰停止の主因候補。
- combined では停止窓の重なりにより総停止時間がさらに増加する。

判断:
- 初期閾値のままでは Phase 3 Halt/Risk integration（本体統合）へ進まない。
- 本結果は収益性確認ではなく、Phase 2 の副作用診断記録である。
- 本結果は閾値本採用の根拠ではない。

次方針（Phase 2 diagnostic scenario として別管理）:
- 閾値や cooldown の候補比較は、Phase 2 の診断シナリオとして固定条件で比較する。
- 直ちに閾値変更・本体統合は行わない。

### 6.59 Phase 3 Halt/Risk integration Go/No-Go Criteria
目的:
- Phase 2 診断結果を受けて、Phase 3 本体統合に進む判断基準を事前固定する。
- 結果を見ながら閾値や条件を逐次調整する運用を防ぐ。

Go 条件（全て満たすこと）:
- `net_counterfactual_effect_pips` が代表月で大きくマイナスではない。
- `halted_entry_count / total_trade_count` が過剰ではない（停止比率が説明可能範囲）。
- `total_halt_minutes` が過剰ではない（運用上許容できる停止時間）。
- `avoided_loss_pips` と `missed_profit_pips` の関係を定量的に説明できる。
- halt reason 別（`price_shock_halt` / `volatility_spike_halt`）に副作用を説明できる。
- 単月ではなく複数月で同傾向を確認できる。
- 本体統合前に必要ログ列とテスト観点が定義済みである。

No-Go 条件（いずれかに該当で統合見送り）:
- `net_counterfactual_effect_pips` が大きくマイナス。
- `missed_profit_pips` が `avoided_loss_pips` を大きく上回る。
- `halted_entry_count` が多すぎる。
- `total_halt_minutes` が長すぎる。
- 特定 halt reason が過剰発火している。
- 代表月1つだけで判断している。
- 結果に合わせて threshold/cooldown を逐次調整している。

現時点判定（OOS-2 2024-11 OFF trailing）:
- 現在の初期診断・分離診断結果は No-Go に該当する。
- 理由:
  - combined / price_shock only / volatility_spike only の全シナリオで `net_counterfactual_effect_pips` がマイナス。
  - `missed_profit_pips` が `avoided_loss_pips` を上回る。
  - `volatility_spike_halt` が発火数・停止時間・逸失利益で過剰停止の主因候補。

次に進む場合の運用:
- Phase 3 へ進む前に、Phase 2 diagnostic scenario として cooldown / threshold 候補比較条件を事前固定する。
- 比較は同一入力・同一評価軸で実施し、結果を見ながらの逐次変更は行わない。

注意:
- これは収益性確認ではない。
- これは閾値本採用ではない。

### 6.60 Phase 2 cooldown / threshold diagnostic scenario v0.1
目的:
- Phase 3 統合に進む前に、初期 halt 設定の過剰停止が cooldown 由来か threshold 由来かを分解する。
- 結果に合わせた逐次最適化ではなく、事前固定した候補セットとして比較する。

対象開始月:
- 代表月は OOS-2 2024-11 OFF trailing とする。
- 代表月は初期比較の開始点であり、単月で Go 判定は行わない。

実行候補シナリオ（v0.1 固定）:

| Scenario | Name | Filters | Thresholds | Cooldown |
| --- | --- | --- | --- | --- |
| A | `initial_combined` | `price_shock_halt` + `volatility_spike_halt` | `shock_m5=20`, `shock_m15=35`, `atr_ratio=2.0`, `range_ratio=2.5` | `cooldown_shock=60`, `cooldown_volatility=45` |
| B | `cooldown_short_combined` | `price_shock_halt` + `volatility_spike_halt` | Scenario A と同じ | `cooldown_shock=30`, `cooldown_volatility=20` |
| C | `price_shock_only_initial` | `price_shock_halt` only | `shock_m5=20`, `shock_m15=35` | `cooldown_shock=60` |
| D | `volatility_only_initial` | `volatility_spike_halt` only | `atr_ratio=2.0`, `range_ratio=2.5` | `cooldown_volatility=45` |
| E | `volatility_less_sensitive` | `volatility_spike_halt` only | `atr_ratio=2.5`, `range_ratio=3.0` | `cooldown_volatility=45` |
| F | `volatility_less_sensitive_short_cooldown` | `volatility_spike_halt` only | `atr_ratio=2.5`, `range_ratio=3.0` | `cooldown_volatility=20` |

評価指標（固定）:
- `halt_window_count`
- `total_halt_minutes`
- `halted_entry_count`
- `halted_entry_count / total_trade_count`
- `avoided_loss_pips`
- `missed_profit_pips`
- `net_counterfactual_effect_pips`
- `halt_reason_counts`

Go/No-Go との関係:
- 代表月のみで Go 判定しない。
- 代表月で明らかに悪いものは棄却候補とする。
- 改善が見えたものだけ、後段で複数月確認へ進める。
- Phase 3 統合可否は 17.18 の Go/No-Go Criteria に従って別途判断する。

運用制約:
- 上記 v0.1 セットより細かい閾値探索は行わない。
- 比較途中で候補を追加して都合よく最適化しない。

注意:
- これは閾値最適化ではない。
- これは Phase 2 diagnostic scenario であり、本採用ではない。
- Phase 3 本体統合は保留のままとする。

### 6.61 Phase 2 cooldown / threshold diagnostic scenario v0.1 結果（OOS-2 2024-11 OFF trailing）
結果比較（A〜F）:

| Scenario | Name | enabled_filters | halt_window_count | total_halt_minutes | halted_entry_count | total_trade_count | halted_entry_ratio | halt_reason_counts | avoided_loss_pips | missed_profit_pips | net_counterfactual_effect_pips |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| A | `initial_combined` | `price_shock_halt\|volatility_spike_halt` | 87 | 9215.0 | 23 | 64 | 0.359375 | `price_shock_halt:44\|volatility_spike_halt:75` | 0.10 | 16.87 | -16.77 |
| B | `cooldown_short_combined` | `price_shock_halt\|volatility_spike_halt` | 120 | 6415.0 | 16 | 64 | 0.25 | `price_shock_halt:62\|volatility_spike_halt:98` | 0.10 | 13.65 | -13.55 |
| C | `price_shock_only_initial` | `price_shock_halt` | 44 | 5495.0 | 11 | 64 | 0.171875 | `price_shock_halt:44` | 0.00 | 6.07 | -6.07 |
| D | `volatility_only_initial` | `volatility_spike_halt` | 81 | 7040.0 | 17 | 64 | 0.265625 | `volatility_spike_halt:81` | 0.10 | 13.42 | -13.32 |
| E | `volatility_less_sensitive` | `volatility_spike_halt` | 58 | 4670.0 | 8 | 64 | 0.125 | `volatility_spike_halt:58` | 0.00 | 3.75 | -3.75 |
| F | `volatility_less_sensitive_short_cooldown` | `volatility_spike_halt` | 78 | 2875.0 | 7 | 64 | 0.109375 | `volatility_spike_halt:78` | 0.00 | 3.05 | -3.05 |

解釈（構造診断）:
- A〜F の全シナリオで `net_counterfactual_effect_pips` はマイナス。
- combined 系（A/B）は停止範囲が広く、代表月では副作用が大きい。
- `price_shock_only`（C）も代表月では利益機会停止が目立つ。
- `volatility_only_initial`（D）は過剰停止の主因候補として整合。
- `volatility_less_sensitive`（E/F）は副作用が相対的に小さい。
- F は副作用最小だが、Go 判定条件を満たさない。

判断:
- Phase 3 integration は引き続き No-Go。
- 棄却候補: A / B / C / D
- 保留候補: E / F
- 複数月確認に回すなら F を第一候補とする。
- ただし F は本採用候補・本体統合候補ではない。

次の分岐（Phase 2 診断）:
1. F を複数月確認する。
2. Halt Filter を一時保留し、Phase 4 HTFContext へ進む。

運用制約:
- 追加の細かい閾値探索は行わない。

注意:
- これは収益性確認ではない。
- これは閾値本採用ではない。

### 6.62 Phase 2 Halt/Risk diagnostic pause と Phase 4 HTFContext への遷移判断
判断:
- Phase 3 Halt/Risk integration は現時点で No-Go を維持する。
- Halt Filter（`price_shock_halt` / `volatility_spike_halt`）は一時保留とする。
- Roadmap の次工程として、Phase 4 HTFContext v0.2 設計へ進む。

No-Go 理由（6シナリオ結果ベース）:
- A〜F の全シナリオで `net_counterfactual_effect_pips` がマイナス。
- A/B/C/D は停止副作用が相対的に大きく、代表月では棄却候補。
- E/F は相対的に副作用が小さいが、代表月で net negative のため Go 候補にはならない。
- F は最小副作用（`net_counterfactual_effect_pips=-3.05`）だが、Phase 3 統合条件を満たさない。

Halt Filter 一時保留の理由:
- 初期候補群で Phase 3 Go 条件を満たすシナリオが確認できていない。
- 追加の細かい閾値探索は Phase 2 運用制約に反し、逐次最適化リスクが高い。
- そのため、本線開発は Phase 4 HTFContext v0.2 へ移し、Halt Filter は保留管理とする。

F シナリオの扱い:
- F は将来の複数月確認候補として保持する。
- ただし、現時点では Phase 3 統合候補ではなく、本採用候補でもない。

次工程:
- Phase 4 HTFContext v0.2（H4 bias + H1 context、strict/permissive 再整理、future leak 防止方針再確認）。

注意:
- これは収益性確認ではない。
- これは閾値本採用ではない。

### 6.63 Phase 4 HTFContext v0.2 Design（実装前仕様）
目的:
- H4 bias と H1 context により entry の上位足文脈を強化する。
- 単なる利益最大化ではなく、裁量で見る「大きな方向性」と「直近文脈」を EA 仕様へ落とし込む。

v0.2 基本方針:
- H4 = bias layer
- H1 = context layer
- M5 = entry execution layer

H4 bias 候補:
- `up`
- `down`
- `neutral`
- `unknown`

H1 context 候補:
- `aligned_up`
- `aligned_down`
- `pullback_against_h4`
- `range_or_neutral`
- `transition`
- `unknown`

H4/H1 組み合わせの初期解釈:
- H4 `up` + H1 `aligned_up`: long 優先候補
- H4 `down` + H1 `aligned_down`: short 優先候補
- H4 `up` + H1 `pullback_against_h4`: long 候補だが慎重
- H4 `down` + H1 `pullback_against_h4`: short 候補だが慎重
- H4 `neutral`: 原則慎重、v0.2 では比較条件扱い
- H4/H1 不一致: entry 抑制または比較条件

v0.2 での比較方針（本採用しない）:
- `HTF OFF baseline`
- `H1 only`
- `H4 bias + H1 context`
- 上記を比較候補として扱い、最初から本採用にしない。

future leak 防止方針:
- M5 の entry 判定時点では、確定済み H1/H4 足のみ参照する。
- 未確定 H1/H4 足は参照しない。
- M5 close entry と整合する timestamp semantics を維持する。
- H1/H4 aggregation で lookahead を許容しない。

ログ列候補:
- `htf_v2_enabled`
- `htf_policy`
- `h4_bias`
- `h4_bias_reason`
- `h1_context`
- `h1_context_reason`
- `htf_v2_direction_allowed`
- `htf_v2_filter_reason`
- `htf_v2_conflict_flag`
- `htf_v2_data_valid_flag`

評価指標:
- `trade_count`
- `total_pnl` / `average_pnl`
- `win_rate`
- `htf_rejected_count`
- `htf_conflict_count`
- `h4_bias_counts`
- `h1_context_counts`
- entry 集合差分
- `rejected_entry_counterfactual`

実装前に決める未確定事項:
- H4 bias の計算方法
- H1 context の計算方法
- `neutral` の扱い
- H4/H1 不一致時の扱い
- support/resistance との責務分離

注意:
- v0.2 では HTF を本採用扱いしない。
- 結果を見て逐次閾値調整しない。
- 実装前に I/O 契約とログ列を固定する。
- これは収益性確認ではない。

### 6.64 HTF v0.2 diagnostic_only 最小実装メモ（2026-05-03）
- `PipelineAdapter` に HTF v2 の `diagnostic_only` 最小実装を追加した。
- `htf_v2_enabled=True` でも `diagnostic_only` では entry を止めない（`entry_signal` / `trade_ok` を変更しない）。
- decision trace / decision_logs に HTF v2 列（`h4_bias` / `h1_context` / MA関連 / conflict/data_valid 等）を出力する。
- `aligned_only` / `pullback_permissive` は policy 候補として `direction_allowed` 計算のみ保持し、既定動作は無効（`htf_v2_enabled=False`）。
- 本実装は本体 filter 統合ではなく診断用途であり、HTF v2 本採用を意味しない。
- `transition` context 判定は初期実装では deferred とし、追加条件定義は後続タスクとする。

### 6.65 HTF v0.2 diagnostic_only runner wiring（2026-05-03）
- `scripts/run_backtest_exit_experiment.py` に HTF v2 CLI 引数（`--htf-v2-*`）を追加し、`PipelineAdapterConfig` へ接続した。
- `backtest_summary.csv` と `run_metadata.json` に HTF v2 設定値を出力するようにした。
- 既定値は `htf_v2_enabled=False` のまま維持し、既存 runner 挙動を壊さない。
- `diagnostic_only` は entry filter ではなく、entry を変えないラベル出力用の wiring として扱う。

### 6.66 HTF v2 diagnostic_only 代表run結果（OOS-2 2024-11）
実行条件:
- input-csv: `data/private/backtest_slices/USDJPY_M5_2024-10-01_2025-01-01.csv`
- run-id: `oos2_20241101_1201_htf_v2_diag_off_trailing`
- start: `2024-11-01`
- end: `2024-12-01`
- exit-policy: `simple_trailing_after_1R`
- `htf-v2-enabled`
- `htf-v2-policy diagnostic_only`

実行結果:
- `selected_bars=5925`
- `range=[2024-11-01T00:00:00+00:00, 2024-11-29T16:55:00+00:00]`
- `trade_count=64`
- `total_pnl=0.29010000000004366`
- decision_logs に HTF v2 列が出力されることを確認

HTF v2 分布:
- `h4_bias_counts`
  - `unknown=2456`
  - `down=1487`
  - `neutral=1419`
  - `up=499`
- `h1_context_counts`
  - `unknown=3117`
  - `range_or_neutral=1101`
  - `aligned_down=980`
  - `aligned_up=367`
  - `pullback_against_h4=296`

解釈（構造検証）:
- `diagnostic_only` は entry を止めない前提であり、`trade_count=64` は既存 OOS-2 2024-11 OFF trailing と一致した。
- 上記一致により、代表runでは entry 非変更を概ね確認できた。
- 一方で `h4_bias unknown` 約42%、`h1_context unknown` 約53% と unknown 比率が高い。

unknown 比率が高い原因候補:
- runner が `start/end` スライス後の bars のみを `PipelineAdapter` に渡しており、`start` 以前の warmup 履歴が HTF v2 計算に使えていない可能性がある。
- H4 MA50 には最低 50 本の H4 足（約 200 時間）相当の履歴が必要であり、月初起点 run では序盤の `unknown` が増えうる。

次課題（Phase 4）:
- warmup handling / start-bound handling の設計を先行する。
- trade 評価期間と indicator warmup 期間の分離方針を整理する。
- warmup 後の `h4_bias` / `h1_context` 分布を再確認する。
- この課題整理が終わるまで `aligned_only` / `pullback_permissive` へは進まない。

注意:
- これは収益性確認ではない。
- backtest 再実行・売買ロジック変更・HTF 計算ルール変更は行っていない。

### 6.67 HTF v2 warmup handling / evaluation period separation design
目的:
- HTF v2 `diagnostic_only` 代表runで観測された `unknown` 高比率に対して、評価対象期間と indicator 計算用履歴期間を分離する設計方針を固定する。
- 本節は設計整理であり、実装変更・backtest再実行は行わない。

現状観測（OOS-2 2024-11 代表run）:
- 全 decision row（`n=5861`）
  - `h4_bias unknown = 2456 / 5861`（約41.9%）
  - `h1_context unknown = 3117 / 5861`（約53.2%）
  - `htf_v2_data_valid_flag False = 3117 / 5861`（約53.2%）
- entry候補（`n=64`）
  - `h4_bias unknown = 27 / 64`（約42.2%）
  - `h1_context unknown = 36 / 64`（約56.3%）

warmup不足の原因候補:
- `run_backtest_exit_experiment.py` は `start/end` で slice した後の bars を `PipelineAdapter` へ渡している。
- そのため input-csv に `start` 以前の履歴があっても、HTF v2 計算 warmup に使えていない可能性がある。
- H4 MA50 は最低 50 本の H4 足（約200時間）、H1 MA20 は最低 20 本の H1 足を必要とするため、評価期間開始直後に `unknown` が増えやすい。

評価期間と indicator warmup期間の分離方針:
- 例:
  - `indicator_input_period: 2024-10-01〜2024-12-01`
  - `evaluation_period: 2024-11-01〜2024-12-01`
- `trade_logs` / `backtest_summary` の評価対象は `evaluation_period` のみとする。
- HTF（H1/H4/MA/slope）計算は `indicator_input_period` 全体を使用してよい。

原則:
- entry評価対象は `start/end` 内に限定する。
- H1/H4/MA/slope 計算には `start` 以前の履歴を使ってよい。
- ただし `m5_decision_time` より未来の情報は使わない。
- `start` 以前の取引は発生させず、indicator 計算専用とする。

future leak 防止方針:
- warmup は過去履歴であり許可する。
- 評価期間以降の未来足は参照しない。
- 各 M5 decision 時点で参照可能な HTF bar は `htf_bar_close_time <= m5_decision_time` のみとする。

runner設計候補:
- 候補A: `--warmup-start` を追加し、input-csv 全体から `warmup_start〜end` を `PipelineAdapter` へ渡す。
  - ただし trade / decision の評価対象は `start〜end` に限定する。
- 候補B: `PipelineAdapter` に `history_bars` を渡し、indicator計算専用履歴を別経路で供給する。

推奨案（現時点）:
- runner側で `warmup_start` を扱う。
- BacktestRunner の評価対象 bar と `PipelineAdapter` の indicator 履歴を分離する。
- 後方互換のため、`warmup_start` 未指定時は従来挙動を維持する。

実装時の注意（次工程向け）:
- `trade_count` / summary は `evaluation_period` のみ集計する。
- decision_logs も `evaluation_period` のみでよい。
- HTF 計算だけ warmup 込みにする。
- 既存run比較のため warmup有無・warmup期間を metadata に残す。

進行制約:
- 現時点では `aligned_only` / `pullback_permissive` へ進まない。
- これは収益性確認ではない。

### 6.68 `--warmup-start` runner実装方針（Phase 4）
実装方針:
- `--warmup-start` は indicator 履歴入力期間の開始境界として扱う。
- `--warmup-start` 自体は評価期間や取引期間を意味しない。
- 評価期間は従来どおり `start <= timestamp < end` とする。

挙動:
- `warmup_start` 未指定時は従来挙動を維持する（indicator入力=評価期間）。
- `warmup_start` 指定時は `warmup_start <= timestamp < end` を indicator 入力期間として provider window に渡す。
- ただし entry/exit/trade_logs/decision_logs/summary 集計対象は `start <= timestamp < end` のみ。
- `start` より前の bar は取引を発生させず、indicator 計算専用とする。

future leak 防止:
- warmup は過去履歴であり許可する。
- 評価期間以降の未来足は参照しない。
- HTF 参照可能条件は引き続き `htf_bar_close_time <= m5_decision_time` とする。

運用メモ:
- `run_metadata.json` / `backtest_summary.csv` に warmup と evaluation 分離情報を残し、warmup有無の比較を再現可能にする。
- 本変更は `diagnostic_only` の unknown 比率評価を改善するための runner 境界設計であり、`aligned_only` / `pullback_permissive` 統合には進まない。

### 6.69 HTF v2 warmupあり diagnostic_only 代表run結果（OOS-2 2024-11）
実行条件:
- input-csv: `data/private/backtest_slices/USDJPY_M5_2024-10-01_2025-01-01.csv`
- run-id: `oos2_20241101_1201_htf_v2_diag_off_trailing_warmup`
- output-dir: `logs/backtest_runs/oos2_20241101_1201_htf_v2_diag_off_trailing_warmup`
- start: `2024-11-01T00:00:00Z`
- end: `2024-12-01T00:00:00Z`
- warmup-start: `2024-10-01T00:00:00Z`
- exit-policy: `simple_trailing_after_1R`
- max-holding-bars: `50`
- `htf-v2-enabled`
- `htf-v2-policy: diagnostic_only`

実行結果:
- `selected_bars=5925`
- `indicator_input_bars=12365`
- `warmup_bar_count=6440`
- `trade_count=64`
- `total_pnl=0.29010000000004366`
- `elapsed_seconds=459.08`

metadata（抜粋）:
- `warmup_start=2024-10-01T00:00:00Z`
- `evaluation_start=2024-11-01T00:00:00Z`
- `evaluation_end=2024-12-01T00:00:00Z`
- `evaluation_bar_count=5925`
- `indicator_input_start=2024-10-01T00:00:00+00:00`
- `indicator_input_end=2024-11-29T16:55:00+00:00`
- `htf_v2_enabled=true`
- `htf_v2_policy=diagnostic_only`

warmupあり分布:
- 全 decision row（`rows=5861`）
  - `h4_bias: neutral=2927, down=1725, up=1209`
  - `h1_context: range_or_neutral=2349, aligned_down=1087, unknown=1041, aligned_up=850, pullback_against_h4=534`
  - `htf_v2_data_valid_flag: True=4820, False=1041`
  - `htf_v2_conflict_flag: True=3924, False=1937`
- entry候補64件
  - `h4_bias: neutral=35, up=15, down=14`
  - `h1_context: range_or_neutral=25, unknown=14, aligned_up=14, aligned_down=6, pullback_against_h4=5`

unknown比率比較:

| 比較対象 | warmupなし | warmupあり |
| --- | ---: | ---: |
| 全decision `h4_bias unknown` | `2456/5861 = 41.9%` | `0/5861 = 0.0%` |
| 全decision `h1_context unknown` | `3117/5861 = 53.2%` | `1041/5861 = 17.8%` |
| entry候補 `h4_bias unknown` | `27/64 = 42.2%` | `0/64 = 0.0%` |
| entry候補 `h1_context unknown` | `36/64 = 56.3%` | `14/64 = 21.9%` |

解釈（構造検証）:
- warmup対応により `h4_bias unknown` は実質解消し、`h1_context unknown` も大幅に低下した。
- 前回の unknown 多発は warmup不足由来の影響が大きいことを示唆する。
- `diagnostic_only` で `trade_count=64` / `total_pnl=0.2901` を維持し、entry 非変更を再確認した。
- 一方で entry候補は `h4 neutral` / `h1 range_or_neutral` / `unknown` に偏りが残る。

次課題（semantics review）:
- `htf_v2_direction_allowed` の意味定義確認（`diagnostic_only` 時に hypothetical allowed として扱うか）。
- `htf_v2_conflict_flag` の意味定義確認（`neutral + range_or_neutral` を conflict 扱いする妥当性）。
- `aligned_up` / `aligned_down` でも `htf_v2_direction_allowed=False` が見える行の解釈ルール整理。
- 上記 semantics が固まるまで `aligned_only` / `pullback_permissive` へ進まない。

注意:
- これは収益性確認ではない。
- backtest 再実行・売買ロジック変更・HTF filter有効化・閾値変更は行っていない。

### 6.70 HTF v2 semantics refinement（diagnostic_only 解釈明確化）
目的:
- `diagnostic_only` 結果を誤読しないように、active policy列と仮想policy比較列を分離する。
- `conflict` の意味を `hard_conflict` と `uncertainty` に分解し、neutral帯を過剰に conflict 解釈しない。

方針:
- `htf_v2_direction_allowed` は active policy 用の判定列として維持する。
- `diagnostic_only` は entry を止めないため、`htf_v2_filter_reason=diagnostic_only:no_entry_filter` を維持する。
- `diagnostic_only` 時の policy比較のため、仮想判定列を decision trace / decision_logs に追加する。

追加列:
- `htf_v2_candidate_direction`（`long` / `short` / `unknown`）
- `htf_v2_aligned_only_allowed`
- `htf_v2_pullback_permissive_allowed`
- `htf_v2_context_uncertain_flag`
- `htf_v2_hard_conflict_flag`

allowed 判定仕様:
- `aligned_only_allowed`
  - candidate=`long`: `h4_bias=up` and `h1_context=aligned_up`
  - candidate=`short`: `h4_bias=down` and `h1_context=aligned_down`
- `pullback_permissive_allowed`
  - candidate=`long`: `h4_bias=up` and `h1_context in {aligned_up, pullback_against_h4}`
  - candidate=`short`: `h4_bias=down` and `h1_context in {aligned_down, pullback_against_h4}`

conflict / uncertainty 分離:
- `context_uncertain_flag=True`
  - `h4_bias in {neutral, unknown}` または
  - `h1_context in {unknown, range_or_neutral}`
- `hard_conflict_flag=True`
  - candidate=`long` かつ `h4_bias=down`（または `h1_context=aligned_down`）
  - candidate=`short` かつ `h4_bias=up`（または `h1_context=aligned_up`）
- `neutral` / `range_or_neutral` / `unknown` は hard conflict ではなく uncertainty として扱う。

後方互換:
- 既存列 `htf_v2_conflict_flag` は互換維持のため残し、`hard_conflict_flag` と同義に寄せる。
- `htf_v2_enabled=False` 時の既存挙動は維持する。

進行制約:
- 本変更は診断列整理であり、`aligned_only` / `pullback_permissive` の実filter化は行わない。
- これは収益性確認ではない。

### 6.71 HTF v2 diagnostic trade analysis 後処理
目的:
- `diagnostic_only` 代表runの既存 entry/trade を、HTF v2分類別に損益分解する。
- 実filter化前に、`aligned_only_allowed` / `pullback_permissive_allowed` / `context_uncertain` / `hard_conflict` の分布と損益を確認する。

対象:
- 既存 `decision_logs.csv` と `trade_logs.csv` の後処理集計のみ。
- backtest再実行・売買ロジック変更・HTF filter有効化は行わない。

突合方針:
- `trade_logs.entry_time` を基準に `decision_logs.timestamp` とUTC正規化後に突合する。
- 時刻正規化は `pandas.to_datetime(..., utc=True)` を使用する。
- `trade_logs.pnl` を損益計算に使用する。

付与列（trade単位）:
- `htf_v2_candidate_direction`
- `h4_bias`
- `h1_context`
- `htf_v2_aligned_only_allowed`
- `htf_v2_pullback_permissive_allowed`
- `htf_v2_context_uncertain_flag`
- `htf_v2_hard_conflict_flag`
- `htf_v2_data_valid_flag`

出力:
- `htf_v2_trade_analysis.csv`（trade単位の突合結果）
- `htf_v2_group_summary.csv`（分類別 `trade_count/total_pnl/average_pnl/win_rate`）
- `htf_v2_group_summary.md`（Markdown要約、unmatched warning付き）

集計グループ:
- `h4_bias`
- `h1_context`
- `htf_v2_aligned_only_allowed`
- `htf_v2_pullback_permissive_allowed`
- `htf_v2_context_uncertain_flag`
- `htf_v2_hard_conflict_flag`
- `htf_v2_data_valid_flag`
- `htf_v2_candidate_direction`

注意:
- これは既存ログの後処理診断であり、収益性確認ではない。
- HTF v2 は entry を止めていない。
- `aligned_only` / `pullback_permissive` の実filter化判断は、この分析結果確認後に行う。

## HTF v2 Diagnostic Trade Analysis Results

### 概要
HTF v2 diagnostic trade analysis の代表的な実行結果を以下に記録します。本分析は、HTF v2 を diagnostic/explanation layer として扱い、entry filter 化を行わない方針を確認するためのものです。

### 対象 Run
- **Run 名**: oos2_20241101_1201_htf_v2_diag_off_trailing_warmup_semantics
- **取引数**: 64
- **総損益 (total_pnl)**: 0.2901

### 集計結果
#### h4_bias
| Bias     | Trade Count | Total PnL | Average PnL | Win Rate |
|----------|-------------|-----------|-------------|----------|
| Down     | 14          | 0.0262    | 0.00187     | 85.71%   |
| Neutral  | 35          | 0.2167    | 0.00619     | 80.00%   |
| Up       | 15          | 0.0472    | 0.00315     | 93.33%   |

#### h1_context
| Context               | Trade Count | Total PnL | Average PnL | Win Rate |
|-----------------------|-------------|-----------|-------------|----------|
| Aligned Down          | 6           | 0.0224    | 0.00373     | 100.00%  |
| Aligned Up            | 14          | 0.0383    | 0.00273     | 92.86%   |
| Pullback Against H4   | 5           | 0.0126    | 0.00252     | 100.00%  |
| Range or Neutral      | 25          | 0.1676    | 0.00670     | 84.00%   |
| Unknown               | 14          | 0.0492    | 0.00351     | 64.29%   |

#### Policy Diagnostic
| Policy                          | Trade Count | Total PnL | Average PnL | Win Rate |
|---------------------------------|-------------|-----------|-------------|----------|
| Aligned Only Allowed = False    | 53          | 0.2532    | 0.00478     | 81.13%   |
| Aligned Only Allowed = True     | 11          | 0.0369    | 0.00335     | 100.00%  |
| Pullback Permissive Allowed = False | 52      | 0.2530    | 0.00487     | 80.77%   |
| Pullback Permissive Allowed = True  | 12      | 0.0371    | 0.00309     | 100.00%  |

### 解釈と判断
1. **Aligned Only / Pullback Permissive の実 filter 化を行わない理由**:
   - Aligned Only Allowed = True の取引数は 11 件、総損益は 0.0369 と少なく、実 filter 化すると取引数と総利益が大幅に減少する可能性がある。
   - Pullback Permissive Allowed = True も同様に 12 件のみであり、Aligned Only からほぼ増加しない。

2. **Neutral / Range or Neutral / Context Uncertain の解釈**:
   - h4_bias = Neutral と h1_context = Range or Neutral が代表月で大きな利益源となっている。
   - Context Uncertain = True 側も総損益が 0.2168 と大きく、機械的に除外する根拠はない。

3. **Hard Conflict の扱い**:
   - 平均損益が低く監視価値はあるが、総損益はプラスであり、即除外は不可。

4. **次タスク**:
   - HTF v2 を diagnostic/explanation layer として継続する方針を整理。
   - 複数月で同様の分類別損益を確認するか判断。
   - Phase 5 Support/Resistance へ進むか判断。
   - Aligned Only / Pullback Permissive 実 filter 化は保留。

### 6.72 Phase 3 Halt/Risk integration Go/No-Go Criteria
目的:
- Phase 2 診断結果を受けて、Phase 3 本体統合に進む判断基準を事前固定する。
- 結果を見ながら閾値や条件を逐次調整する運用を防ぐ。

Go 条件（全て満たすこと）:
- `net_counterfactual_effect_pips` が代表月で大きくマイナスではない。
- `halted_entry_count / total_trade_count` が過剰ではない（停止比率が説明可能範囲）。
- `total_halt_minutes` が過剰ではない（運用上許容できる停止時間）。
- `avoided_loss_pips` と `missed_profit_pips` の関係を定量的に説明できる。
- halt reason 別（`price_shock_halt` / `volatility_spike_halt`）に副作用を説明できる。
- 単月ではなく複数月で同傾向を確認できる。
- 本体統合前に必要ログ列とテスト観点が定義済みである。

No-Go 条件（いずれかに該当で統合見送り）:
- `net_counterfactual_effect_pips` が大きくマイナス。
- `missed_profit_pips` が `avoided_loss_pips` を大きく上回る。
- `halted_entry_count` が多すぎる。
- `total_halt_minutes` が長すぎる。
- 特定 halt reason が過剰発火している。
- 代表月1つだけで判断している。
- 結果に合わせて threshold/cooldown を逐次調整している。

現時点判定（OOS-2 2024-11 OFF trailing）:
- 現在の初期診断・分離診断結果は No-Go に該当する。
- 理由:
  - combined / price_shock only / volatility_spike only の全シナリオで `net_counterfactual_effect_pips` がマイナス。
  - `missed_profit_pips` が `avoided_loss_pips` を上回る。
  - `volatility_spike_halt` が発火数・停止時間・逸失利益で過剰停止の主因候補。

次に進む場合の運用:
- Phase 3 へ進む前に、Phase 2 diagnostic scenario として cooldown / threshold 候補比較条件を事前固定する。
- 比較は同一入力・同一評価軸で実施し、結果を見ながらの逐次変更は行わない。

注意:
- これは収益性確認ではない。
- これは閾値本採用ではない。

### 6.73 Phase 2 cooldown / threshold diagnostic scenario v0.1
目的:
- Phase 3 統合に進む前に、初期 halt 設定の過剰停止が cooldown 由来か threshold 由来かを分解する。
- 結果に合わせた逐次最適化ではなく、事前固定した候補セットとして比較する。

対象開始月:
- 代表月は OOS-2 2024-11 OFF trailing とする。
- 代表月は初期比較の開始点であり、単月で Go 判定は行わない。

実行候補シナリオ（v0.1 固定）:

| Scenario | Name | Filters | Thresholds | Cooldown |
| --- | --- | --- | --- | --- |
| A | `initial_combined` | `price_shock_halt` + `volatility_spike_halt` | `shock_m5=20`, `shock_m15=35`, `atr_ratio=2.0`, `range_ratio=2.5` | `cooldown_shock=60`, `cooldown_volatility=45` |
| B | `cooldown_short_combined` | `price_shock_halt` + `volatility_spike_halt` | Scenario A と同じ | `cooldown_shock=30`, `cooldown_volatility=20` |
| C | `price_shock_only_initial` | `price_shock_halt` only | `shock_m5=20`, `shock_m15=35` | `cooldown_shock=60` |
| D | `volatility_only_initial` | `volatility_spike_halt` only | `atr_ratio=2.0`, `range_ratio=2.5` | `cooldown_volatility=45` |
| E | `volatility_less_sensitive` | `volatility_spike_halt` only | `atr_ratio=2.5`, `range_ratio=3.0` | `cooldown_volatility=45` |
| F | `volatility_less_sensitive_short_cooldown` | `volatility_spike_halt` only | `atr_ratio=2.5`, `range_ratio=3.0` | `cooldown_volatility=20` |

評価指標（固定）:
- `halt_window_count`
- `total_halt_minutes`
- `halted_entry_count`
- `halted_entry_count / total_trade_count`
- `avoided_loss_pips`
- `missed_profit_pips`
- `net_counterfactual_effect_pips`
- `halt_reason_counts`

Go/No-Go との関係:
- 代表月のみで Go 判定しない。
- 代表月で明らかに悪いものは棄却候補とする。
- 改善が見えたものだけ、後段で複数月確認へ進める。
- Phase 3 統合可否は 17.18 の Go/No-Go Criteria に従って別途判断する。

運用制約:
- 上記 v0.1 セットより細かい閾値探索は行わない。
- 比較途中で候補を追加して都合よく最適化しない。

注意:
- これは閾値最適化ではない。
- これは Phase 2 diagnostic scenario であり、本採用ではない。
- Phase 3 本体統合は保留のままとする。

### 6.74 Phase 2 cooldown / threshold diagnostic scenario v0.1 結果（OOS-2 2024-11 OFF trailing）
結果比較（A〜F）:

| Scenario | Name | enabled_filters | halt_window_count | total_halt_minutes | halted_entry_count | total_trade_count | halted_entry_ratio | halt_reason_counts | avoided_loss_pips | missed_profit_pips | net_counterfactual_effect_pips |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| A | `initial_combined` | `price_shock_halt\|volatility_spike_halt` | 87 | 9215.0 | 23 | 64 | 0.359375 | `price_shock_halt:44\|volatility_spike_halt:75` | 0.10 | 16.87 | -16.77 |
| B | `cooldown_short_combined` | `price_shock_halt\|volatility_spike_halt` | 120 | 6415.0 | 16 | 64 | 0.25 | `price_shock_halt:62\|volatility_spike_halt:98` | 0.10 | 13.65 | -13.55 |
| C | `price_shock_only_initial` | `price_shock_halt` | 44 | 5495.0 | 11 | 64 | 0.171875 | `price_shock_halt:44` | 0.00 | 6.07 | -6.07 |
| D | `volatility_only_initial` | `volatility_spike_halt` | 81 | 7040.0 | 17 | 64 | 0.265625 | `volatility_spike_halt:81` | 0.10 | 13.42 | -13.32 |
| E | `volatility_less_sensitive` | `volatility_spike_halt` | 58 | 4670.0 | 8 | 64 | 0.125 | `volatility_spike_halt:58` | 0.00 | 3.75 | -3.75 |
| F | `volatility_less_sensitive_short_cooldown` | `volatility_spike_halt` | 78 | 2875.0 | 7 | 64 | 0.109375 | `volatility_spike_halt:78` | 0.00 | 3.05 | -3.05 |

解釈（構造診断）:
- A〜F の全シナリオで `net_counterfactual_effect_pips` はマイナス。
- combined 系（A/B）は停止範囲が広く、代表月では副作用が大きい。
- `price_shock_only`（C）も代表月では利益機会停止が目立つ。
- `volatility_only_initial`（D）は過剰停止の主因候補として整合。
- `volatility_less_sensitive`（E/F）は副作用が相対的に小さい。
- F は副作用最小だが、Go 判定条件を満たさない。

判断:
- Phase 3 integration は引き続き No-Go。
- 棄却候補: A / B / C / D
- 保留候補: E / F
- 複数月確認に回すなら F を第一候補とする。
- ただし F は本採用候補・本体統合候補ではない。

次の分岐（Phase 2 診断）:
1. F を複数月確認する。
2. Halt Filter を一時保留し、Phase 4 HTFContext へ進む。

運用制約:
- 追加の細かい閾値探索は行わない。

注意:
- これは収益性確認ではない。
- これは閾値本採用ではない。

### 6.75 Phase 2 Halt/Risk diagnostic pause と Phase 4 HTFContext への遷移判断
判断:
- Phase 3 Halt/Risk integration は現時点で No-Go を維持する。
- Halt Filter（`price_shock_halt` / `volatility_spike_halt`）は一時保留とする。
- Roadmap の次工程として、Phase 4 HTFContext v0.2 設計へ進む。

No-Go 理由（6シナリオ結果ベース）:
- A〜F の全シナリオで `net_counterfactual_effect_pips` がマイナス。
- A/B/C/D は停止副作用が相対的に大きく、代表月では棄却候補。
- E/F は相対的に副作用が小さいが、代表月で net negative のため Go 候補にはならない。
- F は最小副作用（`net_counterfactual_effect_pips=-3.05`）だが、Phase 3 統合条件を満たさない。

Halt Filter 一時保留の理由:
- 初期候補群で Phase 3 Go 条件を満たすシナリオが確認できていない。
- 追加の細かい閾値探索は Phase 2 運用制約に反し、逐次最適化リスクが高い。
- そのため、本線開発は Phase 4 HTFContext v0.2 へ移し、Halt Filter は保留管理とする。

F シナリオの扱い:
- F は将来の複数月確認候補として保持する。
- ただし、現時点では Phase 3 統合候補ではなく、本採用候補でもない。

次工程:
- Phase 4 HTFContext v0.2（H4 bias + H1 context、strict/permissive 再整理、future leak 防止方針再確認）。

注意:
- これは収益性確認ではない。
- これは閾値本採用ではない。

### 6.76 Phase 4 HTFContext v0.2 Design（実装前仕様）
目的:
- H4 bias と H1 context により entry の上位足文脈を強化する。
- 単なる利益最大化ではなく、裁量で見る「大きな方向性」と「直近文脈」を EA 仕様へ落とし込む。

v0.2 基本方針:
- H4 = bias layer
- H1 = context layer
- M5 = entry execution layer

H4 bias 候補:
- `up`
- `down`
- `neutral`
- `unknown`

H1 context 候補:
- `aligned_up`
- `aligned_down`
- `pullback_against_h4`
- `range_or_neutral`
- `transition`
- `unknown`

H4/H1 組み合わせの初期解釈:
- H4 `up` + H1 `aligned_up`: long 優先候補
- H4 `down` + H1 `aligned_down`: short 優先候補
- H4 `up` + H1 `pullback_against_h4`: long 候補だが慎重
- H4 `down` + H1 `pullback_against_h4`: short 候補だが慎重
- H4 `neutral`: 原則慎重、v0.2 では比較条件扱い
- H4/H1 不一致: entry 抑制または比較条件

v0.2 での比較方針（本採用しない）:
- `HTF OFF baseline`
- `H1 only`
- `H4 bias + H1 context`
- 上記を比較候補として扱い、最初から本採用にしない。

future leak 防止方針:
- M5 の entry 判定時点では、確定済み H1/H4 足のみ参照する。
- 未確定 H1/H4 足は参照しない。
- M5 close entry と整合する timestamp semantics を維持する。
- H1/H4 aggregation で lookahead を許容しない。

ログ列候補:
- `htf_v2_enabled`
- `htf_policy`
- `h4_bias`
- `h4_bias_reason`
- `h1_context`
- `h1_context_reason`
- `htf_v2_direction_allowed`
- `htf_v2_filter_reason`
- `htf_v2_conflict_flag`
- `htf_v2_data_valid_flag`

評価指標:
- `trade_count`
- `total_pnl` / `average_pnl`
- `win_rate`
- `htf_rejected_count`
- `htf_conflict_count`
- `h4_bias_counts`
- `h1_context_counts`
- entry 集合差分
- `rejected_entry_counterfactual`

実装前に決める未確定事項:
- H4 bias の計算方法
- H1 context の計算方法
- `neutral` の扱い
- H4/H1 不一致時の扱い
- support/resistance との責務分離

注意:
- v0.2 では HTF を本採用扱いしない。
- 結果を見て逐次閾値調整しない。
- 実装前に I/O 契約とログ列を固定する。
- これは収益性確認ではない。

### 6.77 HTF v0.2 diagnostic_only 最小実装メモ（2026-05-03）
- `PipelineAdapter` に HTF v2 の `diagnostic_only` 最小実装を追加した。
- `htf_v2_enabled=True` でも `diagnostic_only` では entry を止めない（`entry_signal` / `trade_ok` を変更しない）。
- decision trace / decision_logs に HTF v2 列（`h4_bias` / `h1_context` / MA関連 / conflict/data_valid 等）を出力する。
- `aligned_only` / `pullback_permissive` は policy 候補として `direction_allowed` 計算のみ保持し、既定動作は無効（`htf_v2_enabled=False`）。
- 本実装は本体 filter 統合ではなく診断用途であり、HTF v2 本採用を意味しない。
- `transition` context 判定は初期実装では deferred とし、追加条件定義は後続タスクとする。

### 6.78 HTF v0.2 diagnostic_only runner wiring（2026-05-03）
- `scripts/run_backtest_exit_experiment.py` に HTF v2 CLI 引数（`--htf-v2-*`）を追加し、`PipelineAdapterConfig` へ接続した。
- `backtest_summary.csv` と `run_metadata.json` に HTF v2 設定値を出力するようにした。
- 既定値は `htf_v2_enabled=False` のまま維持し、既存 runner 挙動を壊さない。
- `diagnostic_only` は entry filter ではなく、entry を変えないラベル出力用の wiring として扱う。

### 6.79 HTF v2 diagnostic_only 代表run結果（OOS-2 2024-11）
実行条件:
- input-csv: `data/private/backtest_slices/USDJPY_M5_2024-10-01_2025-01-01.csv`
- run-id: `oos2_20241101_1201_htf_v2_diag_off_trailing`
- start: `2024-11-01`
- end: `2024-12-01`
- exit-policy: `simple_trailing_after_1R`
- `htf-v2-enabled`
- `htf-v2-policy diagnostic_only`

実行結果:
- `selected_bars=5925`
- `range=[2024-11-01T00:00:00+00:00, 2024-11-29T16:55:00+00:00]`
- `trade_count=64`
- `total_pnl=0.29010000000004366`
- decision_logs に HTF v2 列が出力されることを確認

HTF v2 分布:
- `h4_bias_counts`
  - `unknown=2456`
  - `down=1487`
  - `neutral=1419`
  - `up=499`
- `h1_context_counts`
  - `unknown=3117`
  - `range_or_neutral=1101`
  - `aligned_down=980`
  - `aligned_up=367`
  - `pullback_against_h4=296`

解釈（構造検証）:
- `diagnostic_only` は entry を止めない前提であり、`trade_count=64` は既存 OOS-2 2024-11 OFF trailing と一致した。
- 上記一致により、代表runでは entry 非変更を概ね確認できた。
- 一方で `h4_bias unknown` 約42%、`h1_context unknown` 約53% と unknown 比率が高い。

unknown 比率が高い原因候補:
- runner が `start/end` スライス後の bars のみを `PipelineAdapter` に渡しており、`start` 以前の warmup 履歴が HTF v2 計算に使えていない可能性がある。
- H4 MA50 には最低 50 本の H4 足（約 200 時間）相当の履歴が必要であり、月初起点 run では序盤の `unknown` が増えうる。

次課題（Phase 4）:
- warmup handling / start-bound handling の設計を先行する。
- trade 評価期間と indicator warmup 期間の分離方針を整理する。
- warmup 後の `h4_bias` / `h1_context` 分布を再確認する。
- この課題整理が終わるまで `aligned_only` / `pullback_permissive` へは進まない。

注意:
- これは収益性確認ではない。
- backtest 再実行・売買ロジック変更・HTF 計算ルール変更は行っていない。

### 6.80 HTF v2 warmup handling / evaluation period separation design
目的:
- HTF v2 `diagnostic_only` 代表runで観測された `unknown` 高比率に対して、評価対象期間と indicator 計算用履歴期間を分離する設計方針を固定する。
- 本節は設計整理であり、実装変更・backtest再実行は行わない。

現状観測（OOS-2 2024-11 代表run）:
- 全 decision row（`n=5861`）
  - `h4_bias unknown = 2456 / 5861`（約41.9%）
  - `h1_context unknown = 3117 / 5861`（約53.2%）
  - `htf_v2_data_valid_flag False = 3117 / 5861`（約53.2%）
- entry候補（`n=64`）
  - `h4_bias unknown = 27 / 64`（約42.2%）
  - `h1_context unknown = 36 / 64`（約56.3%）

warmup不足の原因候補:
- `run_backtest_exit_experiment.py` は `start/end` で slice した後の bars を `PipelineAdapter` へ渡している。
- そのため input-csv に `start` 以前の履歴があっても、HTF v2 計算 warmup に使えていない可能性がある。
- H4 MA50 は最低 50 本の H4 足（約200時間）、H1 MA20 は最低 20 本の H1 足を必要とするため、評価期間開始直後に `unknown` が増えやすい。

評価期間と indicator warmup期間の分離方針:
- 例:
  - `indicator_input_period: 2024-10-01〜2024-12-01`
  - `evaluation_period: 2024-11-01〜2024-12-01`
- `trade_logs` / `backtest_summary` の評価対象は `evaluation_period` のみとする。
- HTF（H1/H4/MA/slope）計算は `indicator_input_period` 全体を使用してよい。

原則:
- entry評価対象は `start/end` 内に限定する。
- H1/H4/MA/slope 計算には `start` 以前の履歴を使ってよい。
- ただし `m5_decision_time` より未来の情報は使わない。
- `start` 以前の取引は発生させず、indicator 計算専用とする。

future leak 防止方針:
- warmup は過去履歴であり許可する。
- 評価期間以降の未来足は参照しない。
- 各 M5 decision 時点で参照可能な HTF bar は `htf_bar_close_time <= m5_decision_time` のみとする。

runner設計候補:
- 候補A: `--warmup-start` を追加し、input-csv 全体から `warmup_start〜end` を `PipelineAdapter` へ渡す。
  - ただし trade / decision の評価対象は `start〜end` に限定する。
- 候補B: `PipelineAdapter` に `history_bars` を渡し、indicator計算専用履歴を別経路で供給する。

推奨案（現時点）:
- runner側で `warmup_start` を扱う。
- BacktestRunner の評価対象 bar と `PipelineAdapter` の indicator 履歴を分離する。
- 後方互換のため、`warmup_start` 未指定時は従来挙動を維持する。

実装時の注意（次工程向け）:
- `trade_count` / summary は `evaluation_period` のみ集計する。
- decision_logs も `evaluation_period` のみでよい。
- HTF 計算だけ warmup 込みにする。
- 既存run比較のため warmup有無・warmup期間を metadata に残す。

進行制約:
- 現時点では `aligned_only` / `pullback_permissive` へ進まない。
- これは収益性確認ではない。

### 6.81 `--warmup-start` runner実装方針（Phase 4）
実装方針:
- `--warmup-start` は indicator 履歴入力期間の開始境界として扱う。
- `--warmup-start` 自体は評価期間や取引期間を意味しない。
- 評価期間は従来どおり `start <= timestamp < end` とする。

挙動:
- `warmup_start` 未指定時は従来挙動を維持する（indicator入力=評価期間）。
- `warmup_start` 指定時は `warmup_start <= timestamp < end` を indicator 入力期間として provider window に渡す。
- ただし entry/exit/trade_logs/decision_logs/summary 集計対象は `start <= timestamp < end` のみ。
- `start` より前の bar は取引を発生させず、indicator 計算専用とする。

future leak 防止:
- warmup は過去履歴であり許可する。
- 評価期間以降の未来足は参照しない。
- HTF 参照可能条件は引き続き `htf_bar_close_time <= m5_decision_time` とする。

運用メモ:
- `run_metadata.json` / `backtest_summary.csv` に warmup と evaluation 分離情報を残し、warmup有無の比較を再現可能にする。
- 本変更は `diagnostic_only` の unknown 比率評価を改善するための runner 境界設計であり、`aligned_only` / `pullback_permissive` 統合には進まない。

### 6.82 HTF v2 warmupあり diagnostic_only 代表run結果（OOS-2 2024-11）
実行条件:
- input-csv: `data/private/backtest_slices/USDJPY_M5_2024-10-01_2025-01-01.csv`
- run-id: `oos2_20241101_1201_htf_v2_diag_off_trailing_warmup`
- output-dir: `logs/backtest_runs/oos2_20241101_1201_htf_v2_diag_off_trailing_warmup`
- start: `2024-11-01T00:00:00Z`
- end: `2024-12-01T00:00:00Z`
- warmup-start: `2024-10-01T00:00:00Z`
- exit-policy: `simple_trailing_after_1R`
- max-holding-bars: `50`
- `htf-v2-enabled`
- `htf-v2-policy: diagnostic_only`

実行結果:
- `selected_bars=5925`
- `indicator_input_bars=12365`
- `warmup_bar_count=6440`
- `trade_count=64`
- `total_pnl=0.29010000000004366`
- `elapsed_seconds=459.08`

metadata（抜粋）:
- `warmup_start=2024-10-01T00:00:00Z`
- `evaluation_start=2024-11-01T00:00:00Z`
- `evaluation_end=2024-12-01T00:00:00Z`
- `evaluation_bar_count=5925`
- `indicator_input_start=2024-10-01T00:00:00+00:00`
- `indicator_input_end=2024-11-29T16:55:00+00:00`
- `htf_v2_enabled=true`
- `htf_v2_policy=diagnostic_only`

warmupあり分布:
- 全 decision row（`rows=5861`）
  - `h4_bias: neutral=2927, down=1725, up=1209`
  - `h1_context: range_or_neutral=2349, aligned_down=1087, unknown=1041, aligned_up=850, pullback_against_h4=534`
  - `htf_v2_data_valid_flag: True=4820, False=1041`
  - `htf_v2_conflict_flag: True=3924, False=1937`
- entry候補64件
  - `h4_bias: neutral=35, up=15, down=14`
  - `h1_context: range_or_neutral=25, unknown=14, aligned_up=14, aligned_down=6, pullback_against_h4=5`

unknown比率比較:

| 比較対象 | warmupなし | warmupあり |
| --- | ---: | ---: |
| 全decision `h4_bias unknown` | `2456/5861 = 41.9%` | `0/5861 = 0.0%` |
| 全decision `h1_context unknown` | `3117/5861 = 53.2%` | `1041/5861 = 17.8%` |
| entry候補 `h4_bias unknown` | `27/64 = 42.2%` | `0/64 = 0.0%` |
| entry候補 `h1_context unknown` | `36/64 = 56.3%` | `14/64 = 21.9%` |

解釈（構造検証）:
- warmup対応により `h4_bias unknown` は実質解消し、`h1_context unknown` も大幅に低下した。
- 前回の unknown 多発は warmup不足由来の影響が大きいことを示唆する。
- `diagnostic_only` で `trade_count=64` / `total_pnl=0.2901` を維持し、entry 非変更を再確認した。
- 一方で entry候補は `h4 neutral` / `h1 range_or_neutral` / `unknown` に偏りが残る。

次課題（semantics review）:
- `htf_v2_direction_allowed` の意味定義確認（`diagnostic_only` 時に hypothetical allowed として扱うか）。
- `htf_v2_conflict_flag` の意味定義確認（`neutral + range_or_neutral` を conflict 扱いする妥当性）。
- `aligned_up` / `aligned_down` でも `htf_v2_direction_allowed=False` が見える行の解釈ルール整理。
- 上記 semantics が固まるまで `aligned_only` / `pullback_permissive` へ進まない。

注意:
- これは収益性確認ではない。
- backtest 再実行・売買ロジック変更・HTF filter有効化・閾値変更は行っていない。

### 6.83 HTF v2 semantics refinement（diagnostic_only 解釈明確化）
目的:
- `diagnostic_only` 結果を誤読しないように、active policy列と仮想policy比較列を分離する。
- `conflict` の意味を `hard_conflict` と `uncertainty` に分解し、neutral帯を過剰に conflict 解釈しない。

方針:
- `htf_v2_direction_allowed` は active policy 用の判定列として維持する。
- `diagnostic_only` は entry を止めないため、`htf_v2_filter_reason=diagnostic_only:no_entry_filter` を維持する。
- `diagnostic_only` 時の policy比較のため、仮想判定列を decision trace / decision_logs に追加する。

追加列:
- `htf_v2_candidate_direction`（`long` / `short` / `unknown`）
- `htf_v2_aligned_only_allowed`
- `htf_v2_pullback_permissive_allowed`
- `htf_v2_context_uncertain_flag`
- `htf_v2_hard_conflict_flag`

allowed 判定仕様:
- `aligned_only_allowed`
  - candidate=`long`: `h4_bias=up` and `h1_context=aligned_up`
  - candidate=`short`: `h4_bias=down` and `h1_context=aligned_down`
- `pullback_permissive_allowed`
  - candidate=`long`: `h4_bias=up` and `h1_context in {aligned_up, pullback_against_h4}`
  - candidate=`short`: `h4_bias=down` and `h1_context in {aligned_down, pullback_against_h4}`

conflict / uncertainty 分離:
- `context_uncertain_flag=True`
  - `h4_bias in {neutral, unknown}` または
  - `h1_context in {unknown, range_or_neutral}`
- `hard_conflict_flag=True`
  - candidate=`long` かつ `h4_bias=down`（または `h1_context=aligned_down`）
  - candidate=`short` かつ `h4_bias=up`（または `h1_context=aligned_up`）
- `neutral` / `range_or_neutral` / `unknown` は hard conflict ではなく uncertainty として扱う。

後方互換:
- 既存列 `htf_v2_conflict_flag` は互換維持のため残し、`hard_conflict_flag` と同義に寄せる。
- `htf_v2_enabled=False` 時の既存挙動は維持する。

進行制約:
- 本変更は診断列整理であり、`aligned_only` / `pullback_permissive` の実filter化は行わない。
- これは収益性確認ではない。

### 6.84 HTF v2 diagnostic trade analysis 後処理
目的:
- `diagnostic_only` 代表runの既存 entry/trade を、HTF v2分類別に損益分解する。
- 実filter化前に、`aligned_only_allowed` / `pullback_permissive_allowed` / `context_uncertain` / `hard_conflict` の分布と損益を確認する。

対象:
- 既存 `decision_logs.csv` と `trade_logs.csv` の後処理集計のみ。
- backtest再実行・売買ロジック変更・HTF filter有効化は行わない。

突合方針:
- `trade_logs.entry_time` を基準に `decision_logs.timestamp` とUTC正規化後に突合する。
- 時刻正規化は `pandas.to_datetime(..., utc=True)` を使用する。
- `trade_logs.pnl` を損益計算に使用する。

付与列（trade単位）:
- `htf_v2_candidate_direction`
- `h4_bias`
- `h1_context`
- `htf_v2_aligned_only_allowed`
- `htf_v2_pullback_permissive_allowed`
- `htf_v2_context_uncertain_flag`
- `htf_v2_hard_conflict_flag`
- `htf_v2_data_valid_flag`

出力:
- `htf_v2_trade_analysis.csv`（trade単位の突合結果）
- `htf_v2_group_summary.csv`（分類別 `trade_count/total_pnl/average_pnl/win_rate`）
- `htf_v2_group_summary.md`（Markdown要約、unmatched warning付き）

集計グループ:
- `h4_bias`
- `h1_context`
- `htf_v2_aligned_only_allowed`
- `htf_v2_pullback_permissive_allowed`
- `htf_v2_context_uncertain_flag`
- `htf_v2_hard_conflict_flag`
- `htf_v2_data_valid_flag`
- `htf_v2_candidate_direction`

注意:
- これは既存ログの後処理診断であり、収益性確認ではない。
- HTF v2 は entry を止めていない。
- `aligned_only` / `pullback_permissive` の実filter化判断は、この分析結果確認後に行う。

### 6.85 Phase 5 Support/Resistance Filter v0.2 Design（実装前）
目的:
- 上位足または近傍の支持/抵抗に近すぎる entry を診断し、将来的に見送り判断へつなげる設計を固定する。
- ただし v0.2 初期は本体 filter 化せず、diagnostic/counterfactual として扱う。

対象（診断観点）:
- long entry に対する resistance proximity
- short entry に対する support proximity
- range boundary proximity
- breakout 直後の余地不足

v0.2 初期方針:
- SR filter は最初から entry を止めない。
- まず `diagnostic_only` として、entry 時点の SR 近接状態を decision_logs に出力する。
- 実filter化判断は、分類別損益と counterfactual 確認後に行う。

入力候補:
- M5 bars
- H1/H4 aggregated bars
- existing HTF v2 labels
- existing entry signal / trade logs

SR候補の初期定義（比較候補）:
- recent swing high as resistance
- recent swing low as support
- H1/H4 recent high/low
- rolling high/low over fixed window
- 上記のどれを v0.2 初期採用にするかは比較候補として記録し、本採用扱いしない。

距離指標候補:
- price distance
- pips distance
- ATR normalized distance
- `nearest_resistance_distance_pips`
- `nearest_support_distance_pips`
- `distance_to_range_boundary_pips`

初期診断列候補:
- `sr_v2_enabled`
- `sr_policy`
- `nearest_resistance`
- `nearest_support`
- `nearest_resistance_distance_pips`
- `nearest_support_distance_pips`
- `sr_proximity_flag`
- `sr_block_side`
- `sr_reason`
- `sr_data_valid_flag`
- `sr_counterfactual_group`

direction別の考え方:
- long entry では上側 resistance 近接を警戒する。
- short entry では下側 support 近接を警戒する。
- 逆側 SR を stop/反発リスクとして別扱いするかは未確定。

future leak 防止方針:
- entry 判定時点で確定済み bar のみ使用する。
- current bar 以降の high/low を SR 計算に使わない。
- H1/H4 利用時は確定済み HTF bar のみを使用する。

評価指標:
- `sr_proximity_count`
- `sr_proximity_trade_count`
- `sr_proximity_total_pnl`
- `non_sr_proximity_total_pnl`
- `average_pnl`
- `win_rate`
- `avoided_loss / missed_profit` counterfactual
- 月別比較

Go/No-Go 方針:
- 代表月だけで filter 化を決めない。
- `sr_proximity_flag=True` 側が明確に悪い場合のみ次の診断候補とする。
- `sr_proximity_flag=True` 側が利益源なら filter 化しない。
- 閾値は結果に合わせて逐次調整しない。

未確定事項:
- SR 定義を swing 由来にするか、H1/H4 high/low 由来にするか。
- ATR 正規化を初期から使うか。
- pips 閾値の初期仮説。
- long/short で非対称に扱うか。
- HTF v2 との責務分離。

注意:
- HTF v2 は現時点で diagnostic/explanation layer として継続し、entry を止めない。
- SR は本節では実装しない。
- これは収益性確認ではない。

### 6.86 Phase 5 SR v0.2 I/O Contract & Diagnostic Policy（実装前固定）
目的:
- Phase 5 Support/Resistance filter v0.2 の実装前段階として、I/O契約と診断ポリシーを固定する。
- 今回は設計契約の明文化に限定し、backtest実行・SR実装・PipelineAdapter変更・売買ロジック変更・HTF v2 filter化は行わない。

重要前提:
- 実 broker / OANDA API / 実注文送信は未実装。
- 収益性確認済みではない。
- SR filterは本採用ではない。
- HTF v2 は diagnostic/explanation layer として継続し、`aligned_only` / `pullback_permissive` の実filter化は保留する。

v0.2初期のSR定義:
- 初期実装候補は `fixed window rolling high / low` を優先する。
- 理由:
  - swing判定より実装が単純。
  - future leak監査が容易。
  - `diagnostic_only` で最初に分布を見る用途に向く。
- `recent swing high/low` と `H1/H4 recent high/low` は後続候補として保持する。
- 初期定義は本採用扱いしない。

入力（Inputs）:
- M5 bars
- existing entry signal / trade logs
- optional HTF v2 labels
- `sr_v2` config

Config候補:
- `sr_v2_enabled: bool = False`
- `sr_v2_policy: diagnostic_only`
- `sr_v2_window_bars: int = 48`
- `sr_v2_near_threshold_pips: float = 10.0`
- `sr_v2_pip_size: float = 0.01`
- `sr_v2_use_atr_normalized: bool = False`

rolling high/low 計算方針:
- `resistance` は entry判定時点より前の直近N本の `high` 最大値とする。
- `support` は entry判定時点より前の直近N本の `low` 最小値とする。
- current bar および未来barは使わない。
- N本不足時は `sr_data_valid_flag=False` とする。
- entry判定時点の `close` または entry予定価格から距離を計算する。

direction別判定:
- long候補:
  - `nearest_resistance_distance_pips` が閾値以下なら `sr_proximity_flag=True`
  - `sr_block_side=resistance`
- short候補:
  - `nearest_support_distance_pips` が閾値以下なら `sr_proximity_flag=True`
  - `sr_block_side=support`
- 逆側SRは v0.2 初期では block 対象にしない。
- range boundary診断は rolling high/low の両側距離として記録するが、初期filter判定には使わない。

出力列候補:
- `sr_v2_enabled`
- `sr_policy`
- `sr_window_bars`
- `nearest_resistance`
- `nearest_support`
- `nearest_resistance_distance_pips`
- `nearest_support_distance_pips`
- `sr_proximity_flag`
- `sr_block_side`
- `sr_reason`
- `sr_data_valid_flag`
- `sr_counterfactual_group`

diagnostic_only方針:
- `entry_signal` / `trade_ok` は変更しない。
- `sr_proximity_flag` は仮想的に「SR近接なら止める候補」を示すだけとする。
- 実filter化は後続判断とする。
- `sr_reason` には `diagnostic_only:no_entry_filter` を含める。

future leak防止:
- entry時点以前に確定済みのM5 barのみ使用する。
- current bar以降の high/low を SR に使わない。
- H1/H4 SRを後続導入する場合も確定済みHTF barのみ使用する。
- rolling window は `timestamp < current decision timestamp` のbarだけで構成する。

評価指標:
- `sr_proximity_trade_count`
- `sr_proximity_total_pnl`
- `non_sr_proximity_total_pnl`
- `average_pnl`
- `win_rate`
- `sr_data_valid_count`
- `sr_block_side_counts`
- `avoided_loss / missed_profit` counterfactual
- 月別比較

Go/No-Go方針:
- 代表月だけでfilter化しない。
- `sr_proximity_flag=True` 側が明確に悪い場合のみ次の診断候補とする。
- `sr_proximity_flag=True` 側が利益源ならfilter化しない。
- 閾値を結果に合わせて逐次調整しない。
- 複数月確認前に本体filter化しない。

未解決事項:
- rolling window 初期値 `48` の妥当性。
- pips閾値 `10.0` の妥当性。
- ATR正規化をいつ導入するか。
- swing high/low 定義へ移行するか。
- HTF v2 との責務境界。
- long/short で閾値を非対称にするか。

注意:
- 本節は I/O 契約固定であり、実装・本体統合・収益性判断を含まない。

### 6.113 Phase 9 pipeline dry-run health minimum criteria（最小判定）
目的:
- `csv_replay_pipeline` の出力ログ整合と no real order integrity を最小判定する。
- 収益性評価ではなく、dry-run 安全性とログ整合性確認を目的とする。

最小 health_status:
- `pass`
- `warn`
- `fail`

判定（最小）:
- `fail`
  - `real_order_sent_count > 0`
  - `no_real_order_integrity_violation_count > 0`
  - `decision_log_count != replay_bar_count`
- `warn`
  - `pipeline_adapter_error_count > 0`
  - `ordinary_missing_bar_gap_count > 0`
  - `unknown_gap_count > 0`
  - `duplicate_bar_count > 0`
  - `out_of_order_count > 0`
- `pass`
  - 上記 `fail` / `warn` 条件に該当しない

補足:
- `expected_weekend_gap_count` 単独は `warn/fail` にしない。
- `pipeline_adapter_error_count` は `record_and_continue` 方針に合わせ、現段階では `fail` ではなく `warn` とする。

### 6.118 Phase 9 CSV replay pipeline dry-run minimal implementation（Option A）
目的:
- `scripts/run_csv_replay_pipeline_dry_run.py` を新規追加し、CSV replay から `PipelineAdapter` を安全に呼び、near-live風ログへ変換する。
- 収益性評価ではなく、`no_real_order_integrity` を維持した構造検証を目的とする。

実装対象:
- `scripts/run_csv_replay_pipeline_dry_run.py`
- `tests/unit/backtest/test_run_csv_replay_pipeline_dry_run.py`

実装要点:
- Option A を維持し、既存 `run_csv_replay_dry_run.py` は未変更。
- CSV row -> `PriceBar` translator を追加。
  - `spread_pips` 優先、次に `spread`、なければ `0.0`
  - `volume` 未指定時は `0.0`
  - timestamp は UTC 正規化
- replay bar ごとに `window=bars[:i+1]`、`current_index=len(window)-1` で `PipelineAdapter` 呼び出し。
- 例外時は run 全体を停止せず、`pipeline_adapter_status=error` と event 記録で継続。
- EntryEvent は実注文ではなく `paper_candidate` として記録。
- `real_order_sent=False`、`broker_order_id=""` を固定して no-real-order を保証。

出力:
- `near_live_decision_logs.csv`
- `near_live_event_logs.csv`
- `near_live_state_logs.csv`
- `near_live_validation_warnings.csv`
- `near_live_summary.csv`
- `near_live_summary.md`

summary 追加指標（最小実装）:
- `pipeline_adapter_called_count`
- `pipeline_adapter_error_count`
- `pipeline_adapter_skipped_count`
- `entry_signal_true_count`
- `exit_signal_true_count`
- `trade_ok_true_count`
- `paper_order_candidate_count`
- `real_order_sent_count`
- `no_real_order_integrity_violation_count`

注意:
- 本実装は dry-run/paper candidate 記録であり、broker/OANDA/API送信を行わない。
- BacktestRunner本体・既存PipelineAdapter本体・売買ロジックは変更しない。

### 6.117 Phase 9 PipelineAdapter contract audit for csv replay dry-run（実装前監査）
目的:
- `run_csv_replay_pipeline_dry_run.py` 実装前に、既存 `PipelineAdapter` の入力/出力契約を監査し、Phase 9 csv replay pipeline dry-run から安全に呼べるかを判断する。

調査対象ファイル:
- `src/backtest/pipeline_adapter.py`
- `src/backtest/backtest_runner.py`
- `src/data/types.py`
- `src/backtest/types.py`
- `tests/unit/backtest/test_pipeline_adapter.py`
- `tests/integration/test_end_to_end_minimal_pipeline.py`
- `docs/10_interface_contract.md`
- `docs/04_module_spec.md`

PipelineAdapter 公開インターフェース:
- クラス:
  - `PipelineAdapterConfig`
  - `PipelineAdapter`
- 呼び出し面:
  - `PipelineAdapter.__call__(current_index: int, window: List[PriceBar]) -> Optional[EntryEvent]`
  - `PipelineAdapter.get_last_decision_trace() -> dict[str, object]`
  - `PipelineAdapter.reset_run_state() -> None`
- 例外:
  - `window[-1]` が current でない場合 `ValueError`（future bar 混入防止）
  - 下位 detector/assembler の入力不整合由来例外は呼び出し側で捕捉が必要

入力契約:
- 入力型は `List[PriceBar]`（`src/data/types.py`）で、DataFrame 直接入力ではない。
- `PriceBar` 必須属性:
  - `timestamp`（UTC aware datetime）
  - `open`, `high`, `low`, `close`
  - `spread`, `volume`
- 呼び出し条件:
  - `window == bars[:i+1]` を満たすこと
  - `current_index == len(window)-1` を満たすこと
- したがって csv replay 側は `CSV row -> PriceBar` 変換が必須。

出力契約:
- `__call__` 戻り値:
  - `EntryEvent` または `None`
  - `EntryEvent` から取得可能:
    - `direction`, `lot`, `stop_loss`, `take_profit`
    - `entry_reason`, `signal_reason`, `risk_reason`, `filter_reason`
    - `fallback_used`, `structure_source`
    - temporal metadata（`recent_third_*`, `temporal_*`, `breakout_direction`）
- decision log 用追加情報:
  - `get_last_decision_trace()` で各barの判定トレース取得可
  - trace には `entry_signal`, `trade_ok`, `fail_stage`, `decision_reason` に加え、HTF/SR/Session v2 系の診断列が含まれる
- 注意:
  - `exit_signal` は `EntryEvent` では返さない（traceまたは直接Signal層再計算が必要）

内部接続（依存）:
- 接続あり:
  - HTFContext: `TrendDetector` / `ResistanceDetector` / `SupportDetector` / `ContextAssembler`
  - LTFStructure: `SwingExtractor` / `WaveClassifier` / `BreakoutDetector` / `TriangleDetector` / `StructureAssembler`
  - Signal: `DirectionAlignChecker` / `PatternGate` / `EntryRuleEngine` / `ExitRuleEngine` / `SignalAssembler`
  - RiskFilter: `RiskAssembler`
- 接続なし:
  - Execution 直接呼び出しなし
  - Logger 直接書き込みなし
  - broker/OANDA/API 呼び出しなし
- BacktestRunner との関係:
  - `BacktestRunner` の `entry_event_provider` として `PipelineAdapter` を注入する設計
  - `BacktestRunner` は `trace_hook=get_last_decision_trace` を読んで `decision_logs` を組み立て可能

future leak 観点:
- `PipelineAdapter.__call__` は `current_index != len(window)-1` を拒否し、未来バー混入を検知する。
- HTF集約は `_aggregate_completed_htf_bars` で `decision_time` 以後の未確定HTFバーを除外する設計。
- LTF構造判定は `window` のみ参照し、`window` が `bars[:i+1]` であれば future leak を回避可能。
- timestamp semantics:
  - M5 timestamp が bar open time の場合、decision時刻（close相当）との区別を呼び出し側で明示する必要がある。

no_real_order_integrity 観点:
- `PipelineAdapter` 単体は broker/API/実注文送信副作用を持たない。
- `EntryEvent` は「entry候補情報」のみであり、注文送信は実行しない。
- よって Phase 9 pipeline dry-run では:
  - `real_order_sent=False` を runner側で固定可能
  - `broker_order_id` 空欄を runner側で固定可能
  - `paper_order_action` は `none` / `paper_candidate` 制限を runner側で適用可能

csv replay pipeline dry-run からの呼び出し可否:
- 判断: **条件付きで安全に呼び出し可能（Go）**
- 条件:
  - CSV -> `PriceBar` 変換を厳格化
  - 各barで `window=bars[:i+1]` を厳守
  - 例外をbar単位で捕捉し、event logへ記録して継続可能にする
  - no-real-order列を runner側で強制固定する

実装前に必要な変換/ラッパー:
- 必須:
  - `csv row -> PriceBar` translator（timestamp UTC正規化、spread/volume 補完規則）
  - `PipelineAdapter` 呼び出しラッパー（`current_index`, `window` 構築）
- 推奨:
  - `safe_call_pipeline_adapter(...)` 相当の例外捕捉層
  - 失敗時は `pipeline_adapter_status=error`、`pipeline_error_type/message` を decision/event に記録
  - `EntryEvent` + `decision_trace` を near-live decision/state/event schema へ射影する mapper

PipelineAdapter call contract for csv replay pipeline dry-run（最小固定）:
- 入力型:
  - `current_index: int`
  - `window: List[PriceBar]`（UTC timestamp, 必須OHLC+spread+volume）
- 必須属性:
  - `PriceBar.timestamp/open/high/low/close/spread/volume`
- timezone:
  - UTC aware を必須
- 読み出し元:
  - `EntryEvent`: `lot/stop_loss/take_profit/signal_reason/risk_reason/filter_reason`
  - `decision_trace`: `entry_signal/trade_ok/fail_stage/decision_reason` と補助診断列
- 例外時:
  - dry-run全体停止ではなくbar単位エラー記録 + 継続を初期方針候補とする
- health接続:
  - `pipeline_adapter_error_count`, `decision_log_count==replay_bar_count`, gap分類、`no_real_order_integrity_violation_count`
- no_real_order_integrity保証:
  - runner側で `real_order_sent=False`, `broker_order_id=""`, `paper_order_action in {none,paper_candidate}` を固定出力

次段判断:
- 次段は `run_csv_replay_pipeline_dry_run.py` の最小実装検討へ進行可能。
- ただし先に translator/mapper/exception-handling の最小仕様を固定してから実装着手する。

### 6.116 Phase 9 CSV replay PipelineAdapter dry-run I/O contract design（実装前固定）
目的:
- Option A（別スクリプト分離）採用前提で、`CSV replay pipeline dry-run` の I/O 契約と追加ログ列を実装前に固定する。
- 現行 `run_csv_replay_dry_run.py` の互換性を維持しつつ、PipelineAdapter 呼び出しを dry-run に接続する設計境界を明確化する。

Option A 採用理由:
- 現行 skeleton（placeholder integrity 運用を含む）を壊さず維持できる。
- Pipeline接続版の障害・整合監査（`no_real_order_integrity`）を独立管理しやすい。
- 同一期間で skeleton / pipeline の横比較が容易になる。

新規スクリプト案（今回は未作成）:
- `scripts/run_csv_replay_pipeline_dry_run.py`
- 役割:
  - CSV replay / warmup-replay split / data quality warning / gap classification は skeleton と同責務で維持
  - decision生成のみ placeholder固定から PipelineAdapter 呼び出しへ切替
  - 実注文・デモ注文は行わず、paper-only / no-real-order 前提でログ出力

入力:
- CSV列（現行skeletonと同一）:
  - 必須: `timestamp`, `open`, `high`, `low`, `close`
  - 任意: `volume`, `spread_pips`, `source`, `data_valid_flag`
- warmup/replay境界:
  - warmup: `warmup_start <= timestamp < replay_start`
  - replay: `replay_start <= timestamp < replay_end`
  - decision/state処理対象は replay bars のみ
- CLI引数:
  - 現行と同一: `--input-csv`, `--output-dir`, `--run-id`, `--warmup-start`, `--replay-start`, `--replay-end`, `--expected-timeframe-minutes`
  - 追加候補: `--symbol`, `--timeframe`, `--pipeline-config`, `--max-bars`（または `--max-replay-bars`）
  - 最小実装方針: 追加引数は必要最小限に絞る

出力:
- 現行skeletonの出力を維持:
  - `near_live_decision_logs.csv`
  - `near_live_event_logs.csv`
  - `near_live_state_logs.csv`
  - `near_live_validation_warnings.csv`
  - `near_live_summary.csv`
  - `near_live_summary.md`
- 追加候補:
  - `near_live_pipeline_trace_logs.csv`（任意）
  - 最小実装では decision/state/event への列追加で代替可

decision log 追加列候補:
- `pipeline_mode`（`skeleton` / `pipeline`）
- `pipeline_adapter_called`
- `pipeline_adapter_status`（`ok` / `skipped` / `error`）
- `pipeline_error_type`
- `pipeline_error_message`
- `htf_context_status`
- `ltf_structure_status`
- `signal_status`
- `risk_filter_status`
- `entry_signal`
- `exit_signal`
- `signal_type`
- `signal_reason`
- `trade_ok`
- `filter_reason`
- `lot`
- `stop_loss`
- `take_profit`
- `paper_order_action`（最小: `none` or `paper_candidate`）
- `real_order_sent`（常に `False`）
- `broker_order_id`（常に空欄）
- `no_real_order_integrity_ok`

state log 追加列候補:
- `pipeline_mode`
- `pipeline_adapter_last_status`
- `last_pipeline_error_type`
- `last_pipeline_error_message`
- `paper_position_state`
- `real_order_sent`
- `no_real_order_integrity_ok`

event log 追加候補:
- `pipeline_adapter_error`
- `pipeline_adapter_skipped`
- `no_real_order_integrity_violation`
- `pipeline_output_schema_error`

summary 追加候補:
- `pipeline_adapter_called_count`
- `pipeline_adapter_error_count`
- `entry_signal_true_count`
- `exit_signal_true_count`
- `trade_ok_true_count`
- `paper_order_candidate_count`
- `real_order_sent_count`
- `no_real_order_integrity_violation_count`
- `pipeline_dry_run_health_status`

placeholder integrity から no_real_order_integrity への移行:
- 現行skeleton:
  - placeholder integrity を使用
  - `entry_signal=False` 全行固定を期待値とする
- Pipeline dry-run:
  - `entry_signal=True` や `trade_ok=True` が発生しうるため placeholder integrity は使わない
  - 代わりに `no_real_order_integrity` を使用
  - 期待値:
    - `real_order_sent=False`
    - `broker_order_id` 空欄
    - `paper_order_action` は `none` または `paper_candidate` のみ
    - broker/API送信を示す副作用なし

Go / No-Go 候補（Pipeline dry-run）:
- `no_go_candidate`
  - `real_order_sent_count > 0`
  - `no_real_order_integrity_violation_count > 0`
  - `pipeline_adapter_error_count` が一定以上
  - `decision_log_count != replay_bar_count`
- `investigate`
  - PipelineAdapter error が少数発生
  - schema error
  - `ordinary_missing_bar_gap` / `unknown_gap`
- `warn`
  - `expected_weekend_gap` only
  - `pipeline_adapter_error_count=0`
  - `no_real_order_integrity` OK
- `pass`
  - warningなし
  - `pipeline_adapter_error_count=0`
  - `no_real_order_integrity` OK

実装前確認事項:
- PipelineAdapter 現在入力契約（DataFrame / bars / price_frame のどれを受けるか）
- 各barで `bars[:i+1]` のみを渡せるか（future leak 防止）
- `HTF/LTF/Signal/RiskFilter` 出力スキーマの追跡列
- 例外時の運用方針（最小候補: event log 記録 + 該当bar `pipeline_adapter_status=error` で続行）

今回実装しないこと:
- `run_csv_replay_pipeline_dry_run.py` 作成
- 既存コード変更（`run_csv_replay_dry_run.py` / `summarize_csv_replay_dry_run.py` / `pipeline_adapter.py`）
- tests変更
- BacktestRunner / PipelineAdapter / Signal / RiskFilter / Execution の変更
- 売買ロジック変更
- OANDA/API接続、実注文、デモ注文

### 6.115 Phase 9 PipelineAdapter connection responsibility design（実装前）
目的:
- Phase 9 CSV replay dry-run に PipelineAdapter を接続するかどうかを、実装前に責務分離で整理する。
- 現行 skeleton を壊さず、future leak 防止・no real order 維持・dry-run health 継続を両立する接続方針を固定する。

現行 `run_csv_replay_dry_run.py` の責務:
- CSV replay（入力CSVを時系列で再生）
- warmup/replay split
- data quality warning（duplicate / out-of-order / data-gap）
- gap classification（expected weekend / ordinary missing / unknown）
- placeholder decision/state/event log 出力
- near-live風ログ一式（`near_live_*`）出力

PipelineAdapter 接続時に増える責務:
- 各replayバーで、現在バーまでの情報のみを使って `HTFContext / LTFStructure / Signal / RiskFilter` を呼ぶ。
- future leak を避ける（`bars[:i+1]` のみ参照、未来バー非参照）。
- `entry_signal / exit_signal / trade_ok` を placeholder固定値ではなく、実モジュール出力に置き換える。
- ただし実注文・デモ注文は行わず、dry-runとして副作用なしを維持する。

接続しないまま残す責務:
- CSV replay / warmup split / data quality warning / gap classification は継続して必須責務とする。
- dry-run health summary（`summarize_csv_replay_dry_run.py`）への入力ログ生成を継続する。
- `paper_order_action` は dry-run policy に従い `none`（または将来 `paper_only`）とし、実注文アクションを出さない。
- OANDA/API接続は対象外のまま維持する。

placeholder integrity check の扱い変更:
- 現在の placeholder integrity（`entry_signal=False` 全行固定等）は Phase 9 csv_replay skeleton 専用とする。
- PipelineAdapter 接続後は entry/exit/trade判定が動くため、同一チェックを適用しない。
- 接続版では別チェックとして `no_real_order_integrity` を定義する。
  - `paper_order_action` が実注文を示さないこと
  - `broker_order_id` 等の実注文識別子が存在しないこと（列導入時）
  - order/trade送信系副作用がないこと

接続方針 Option 比較:
- Option A: 現行skeleton維持 + 別スクリプト分離（例: `run_csv_replay_pipeline_dry_run.py`）
  - 長所: 既存skeleton互換性を壊しにくい、責務分離が明確、比較検証しやすい
  - 短所: スクリプトが増える、共通処理の重複管理が必要
- Option B: `run_csv_replay_dry_run.py` に `--mode skeleton|pipeline` を追加
  - 長所: 実行入口が1つ、共通処理を再利用しやすい
  - 短所: 分岐が増えて責務が混ざりやすく、skeleton回帰リスクが高い
- Option C: 接続を後送りし、summary/validationを先に固定
  - 長所: 安定運用優先、設計凍結を先に進められる
  - 短所: Pipeline接続の実装検証が遅れる

推奨案:
- 初期採用は Option A（別スクリプト分離）を推奨する。
- 理由:
  - 既存 Phase 9 skeleton と placeholder integrity 運用を壊さずに維持できる。
  - Pipeline接続版で必要な integrity policy（`no_real_order_integrity`）を別管理しやすい。
  - 同一入力期間で skeleton vs pipeline の比較が容易になる。

実装前に固定すべき I/O contract（最小）:
- 入力:
  - 現行と同じ `--input-csv / --warmup-start / --replay-start / --replay-end / --expected-timeframe-minutes / --run-id`
  - （必要時）PipelineAdapter向け config path
- 出力（互換性維持）:
  - `near_live_decision_logs.csv`
  - `near_live_event_logs.csv`
  - `near_live_state_logs.csv`
  - `near_live_validation_warnings.csv`
  - `near_live_summary.csv`
- 追加ログ列（Pipeline接続版候補）:
  - decision系: `signal_reason`, `risk_filter_reason`, `pipeline_stage_status`
  - integrity系: `no_real_order_integrity_flag`, `real_order_attempt_flag`
  - 実注文識別子列は、存在時に常に空欄固定（`broker_order_id` 等）
- health判定分離:
  - skeleton版: placeholder integrity
  - pipeline版: no_real_order_integrity（別status_reason候補）

Go / No-Go:
- 現状 dry-run health は `warn`（`expected_weekend_gap_only`）であり No-Go ではない。
- よって PipelineAdapter 接続の設計検討へ進行可能。
- ただし実装開始前に I/O contract と追加ログ列を固定することを必須条件とする。

今回実装しないこと:
- `run_csv_replay_dry_run.py` / `summarize_csv_replay_dry_run.py` のコード変更
- tests変更
- BacktestRunner / PipelineAdapter / Signal / RiskFilter / Execution の変更
- 売買ロジック変更
- OANDA/API接続、実注文、デモ注文

### 6.114 Phase 9 csv_replay skeleton placeholder integrity summary check（最小追加）
目的:
- `summarize_csv_replay_dry_run.py` に、`near_live_decision_logs.csv`（任意入力）を使った placeholder integrity 確認を追加する。
- これは dry-run skeleton で「注文や売買判断が発生していないこと」の確認であり、収益性確認ではない。

対象:
- `near_live_decision_logs.csv` が存在する場合のみ判定する。
- 存在しない場合は `placeholder_integrity_checked=False` として扱い、単独では No-Go にしない。

placeholder期待値（csv_replay skeleton 前提）:
- `entry_signal=False`
- `exit_signal=False`
- `trade_ok=False`
- `paper_order_action=none`
- `paper_position_state=flat`

`dry_run_period_summary.csv` 追加列:
- `placeholder_integrity_checked`
- `placeholder_integrity_ok`
- `placeholder_violation_count`
- `entry_signal_true_count`
- `exit_signal_true_count`
- `trade_ok_true_count`
- `paper_order_action_non_none_count`
- `paper_position_state_non_flat_count`

health判定優先順位（固定）:
1. `decision_log_count != replay_bar_count`
   - `dry_run_health_status=no_go_candidate`
   - `status_reason=decision_log_count_mismatch`
2. `placeholder_integrity_checked=True` かつ `placeholder_integrity_ok=False`
   - `dry_run_health_status=no_go_candidate`
   - `status_reason=placeholder_integrity_violation`
3. duplicate / out_of_order / ordinary_missing / unknown
   - `dry_run_health_status=investigate`
4. `expected_weekend_gap` only
   - `dry_run_health_status=warn`
5. warningなし + log completeness OK + placeholder OKまたは未確認
   - `dry_run_health_status=pass`

注意:
- 本判定は Phase 9 csv_replay skeleton 専用の整合監査である。
- 将来 PipelineAdapter 接続後は placeholder 前提が変化しうるため、同一判定をそのまま適用しない。

### 6.113 Phase 9 CSV replay dry-run summary 実行結果記録（代表M5 slice）
対象:
- 入力run: `near_live_csv_replay_usdjpy_m5_2024_01_03_to_2024_01_09_gap_classified`
- 実行日: 2026-05-04
- 実行コマンド:
  - `python scripts/summarize_csv_replay_dry_run.py --input-dir outputs/near_live/csv_replay/2024-01-03_to_2024-01-09_gap_classified --output-dir outputs/near_live/csv_replay/2024-01-03_to_2024-01-09_gap_classified_summary`

出力確認:
- `dry_run_period_summary.csv`
  - `replay_bar_count=1151`
  - `decision_log_count=1151`
  - `warning_count=1`
  - `duplicate_bar_count=0`
  - `out_of_order_count=0`
  - `data_gap_count=1`
  - `expected_weekend_gap_count=1`
  - `ordinary_missing_bar_gap_count=0`
  - `unknown_gap_count=0`
  - `log_completeness_ok=True`
  - `data_quality_status=warn`
  - `dry_run_health_status=warn`
  - `status_reason=expected_weekend_gap_only`
- `dry_run_warning_summary.csv`
  - `warning_type=data_gap: 1`
  - `gap_class=expected_weekend_gap: 1`
  - `expected_gap_flag=true: 1`
  - `gap_requires_investigation=false: 1`

記録判断:
- 今回のwarningは `expected_weekend_gap` のみであり、初期判定ルールどおり `warn`。
- `decision_log_count == replay_bar_count` を満たし、log completeness は維持。
- これは収益性確認ではなく、Phase 9 dry-run 運用整合性の記録である。

### 6.93 Phase 6 Session v0.2 diagnostic trade analysis result（代表runレビュー）
目的:
- Session v2 diagnostic_only の代表run結果を記録し、現時点で実filter化しない判断を明文化する。
- これは既存ログの後処理診断であり、収益性確認ではない。

対象run:
- `run_id=oos2_202411_session_v2_diag_trailing_matched`
- `trade_count=64`
- `total_pnl=0.29010000000004366`
- `Session v2` は diagnostic_only のため entry を止めていない。
- `hour_utc` summary の `true/false` 混入問題は修正済みで、修正版 summary では `hour_utc` は `0..23` のみ。

`session_label` 集計:

| session_label | trade_count | total_pnl | average_pnl | win_rate |
| --- | ---: | ---: | ---: | ---: |
| london | 14 | 0.0653 | 0.0046642857 | 0.857143 |
| london_ny_overlap | 11 | 0.0717 | 0.0065181818 | 0.727273 |
| low_liquidity | 4 | 0.0101 | 0.0025250000 | 0.750000 |
| new_york | 9 | 0.0438 | 0.0048666667 | 1.000000 |
| tokyo | 26 | 0.0992 | 0.0038153846 | 0.846154 |

`session_risk_flag` 集計:

| session_risk_flag | trade_count | total_pnl | average_pnl | win_rate |
| --- | ---: | ---: | ---: | ---: |
| false | 60 | 0.2800 | 0.0046666667 | 0.850000 |
| true | 4 | 0.0101 | 0.0025250000 | 0.750000 |

`hour_utc` 観測メモ（抜粋）:
- `hour_utc=16`: `trade_count=7`, `total_pnl=0.0623`, `average_pnl=0.0089`, `win_rate=0.714286`
- `hour_utc=9`: `trade_count=4`, `total_pnl=0.0337`, `average_pnl=0.008425`, `win_rate=1.0`
- `hour_utc=8`: `trade_count=4`, `total_pnl=0.0285`, `average_pnl=0.007125`, `win_rate=1.0`
- `hour_utc=6`: `trade_count=3`, `total_pnl=-0.0018`, `average_pnl=-0.0006`, `win_rate=0.333333`
- `hour_utc=12/14`: 各 `trade_count=1`, 各 `total_pnl=-0.0010`（件数不足）

`day_of_week` 集計:

| day_of_week | trade_count | total_pnl | average_pnl | win_rate |
| --- | ---: | ---: | ---: | ---: |
| friday | 12 | 0.0904 | 0.0075333333 | 0.750000 |
| monday | 12 | 0.0686 | 0.0057166667 | 0.916667 |
| sunday | 7 | 0.0351 | 0.0050142857 | 1.000000 |
| thursday | 10 | 0.0237 | 0.0023700000 | 1.000000 |
| tuesday | 11 | 0.0242 | 0.0022000000 | 0.727273 |
| wednesday | 12 | 0.0481 | 0.0040083333 | 0.750000 |

解釈:
- `session_label` 別では全sessionがプラス。
- `low_liquidity` は4件のみで平均pnl/勝率はやや低いが、`total_pnl` はプラス。
- `session_risk_flag=true` は件数4件で、悪化群とは断定できない。
- `hour_utc=6` や `hour_utc=12/14` は弱い値があるが、件数不足で filter 判断根拠に不足。
- `day_of_week` 別でも全曜日がプラス。
- `session_label` は UTC固定近似で DST未補正のため、本採用filter判断にそのまま使わない。

判断（現時点）:
- Session v2 は `diagnostic/explanation layer` として継続する。
- 現時点では Session v2 を実filter化しない。
- 代表月単独で本採用・棄却判断を行わない。

注意:
- これは代表月の構造診断記録であり、収益性確認を意味しない。

### 6.94 Phase 7 Risk Management / Stop Controls v0.2 Design（実装前）
目的:
- 個別entryの優劣ではなく、EA全体の損失拡大を抑える管理レイヤーを設計する。
- 初期段階では本体停止は行わず、既存 `trade_logs` に対する diagnostic/counterfactual として扱う。
- 実停止ロジック化（本体統合）は後続判断とする。

対象候補:
- `daily_loss_stop`
- `consecutive_loss_stop`
- `drawdown_stop`
- `max_trades_per_day`
- `cooldown_after_loss`
- `risk_per_trade`
- `lot sizing`
- `equity curve / balance curve tracking`
- `stop_resume_rule`

v0.2 初期方針:
- まず既存 `trade_logs` の後処理診断から開始する。
- いきなり `BacktestRunner` / `PipelineAdapter` に停止処理を入れない。
- 停止した場合に「避けられた損失」と「逃した利益」を counterfactual で確認する。
- 閾値は初期仮説とし、本採用値として扱わない。

初期診断候補:
- `daily_pnl`
- `cumulative_pnl`
- `max_drawdown`
- `consecutive_loss_count`
- `trades_per_day`
- `loss_after_loss_pnl`
- `pnl_after_daily_loss_threshold`
- `pnl_after_consecutive_losses`

diagnostic出力候補:
- `risk_date`
- `daily_trade_count`
- `daily_pnl`
- `cumulative_pnl`
- `equity_peak`
- `drawdown`
- `drawdown_pips`
- `consecutive_loss_count`
- `would_daily_stop_trigger`
- `would_consecutive_loss_stop_trigger`
- `would_drawdown_stop_trigger`
- `would_cooldown_trigger`
- `avoided_loss_pnl`
- `missed_profit_pnl`
- `net_counterfactual_effect_pnl`

初期閾値候補（仮説）:
- `daily_loss_stop_pips`: 20〜50 pips 候補
- `consecutive_loss_stop_count`: 2〜3 候補
- `drawdown_stop_pips`: 30〜80 pips 候補
- `cooldown_after_loss_minutes`: 30〜120 候補
- 本節では確定しない。
- 結果を見て逐次調整しない。

HTF/SR/Session との関係:
- HTF/SR/Session は環境説明ラベル（diagnostic/explanation layer）。
- Risk/Stop は資金曲線・損失履歴に基づく上位管理レイヤー。
- entry条件と独立に、EAの継続/停止を判断する責務を持つ。
- Commander的な上位制御に近い。

Go/No-Go:
- 代表月だけで停止条件を本採用しない。
- stop発動後に「避けた損失」より「逃した利益」が大きいなら本体統合しない。
- stop条件が特定月だけ有効なら複数月確認候補とする。
- risk managementは収益最大化ではなく破滅回避・損失拡大抑制を主目的とする。
- 実filter化前に複数月確認する。

未解決事項:
- pips基準 / R基準 / 金額基準のどれを主軸にするか。
- lot sizing導入前にどこまで評価可能か。
- daily boundaryを UTC / JST / NY close のどれにするか。
- open positionを強制決済するか、新規entry停止のみとするか。
- stop後の再開条件。
- swap/commission/slippage 反映後に再評価するか。

注意:
- 本節は実装前設計であり、backtest再実行・売買ロジック変更・Risk/Stop本体実装・lot sizing実装・閾値変更を含まない。

### 6.95 Phase 7 Risk/Stop v0.2 I/O Contract & Diagnostic Policy（実装前固定）
目的:
- Phase 7 Risk Management / Stop Controls v0.2 の実装前段階として、I/O契約と診断ポリシーを固定する。
- entry選別ではなく、EA全体の損失拡大抑制・破滅回避・停止/再開管理を対象とする。
- 今回は設計契約固定に限定し、Risk/Stop本体実装は行わない。

初期評価単位:
- v0.2初期は `trade_logs` 後処理で評価する。
- 評価対象は closed trades のみ。
- open position の強制決済は初期対象外。
- 停止は「新規entry停止」を仮想評価する。
- 実停止ロジック化は後続判断とする。

損益単位:
- v0.2初期は `pnl`（price unit）を source とする。
- USDJPYでは補助的に pips 換算を使う。
- `pip_size=0.01` を初期値とする。
- R基準・金額基準・lot sizing は後続候補。
- pips / R / 金額を混同しない。

daily boundary:
- 初期は UTC date を daily boundary とする。
- JST / NY close 境界は後続候補。
- broker/OANDA時間との整合は未解決事項として保持する。

入力:
- `trade_logs.csv`
- optional `decision_logs.csv`
- optional cost-adjusted trade logs
- risk_stop config

Config候補:
- `risk_stop_v2_enabled: bool = False`
- `risk_stop_v2_policy: diagnostic_only`
- `risk_stop_pip_size: float = 0.01`
- `daily_boundary: UTC`
- `daily_loss_stop_pips_candidates: [20, 30, 50]`
- `consecutive_loss_stop_count_candidates: [2, 3]`
- `drawdown_stop_pips_candidates: [30, 50, 80]`
- `cooldown_after_loss_minutes_candidates: [30, 60, 120]`
- `force_close_open_position: bool = False`

diagnostic出力候補:
- `trade_id`
- `entry_time`
- `exit_time`
- `trade_date_utc`
- `pnl`
- `pnl_pips`
- `cumulative_pnl`
- `cumulative_pips`
- `daily_pnl`
- `daily_pips`
- `daily_trade_count`
- `equity_peak`
- `drawdown`
- `drawdown_pips`
- `consecutive_loss_count`
- `would_daily_loss_stop_trigger`
- `would_consecutive_loss_stop_trigger`
- `would_drawdown_stop_trigger`
- `would_cooldown_trigger`
- `risk_stop_reason`
- `avoided_loss_pnl`
- `missed_profit_pnl`
- `net_counterfactual_effect_pnl`

counterfactual方針:
- stop条件が発動した時刻以降の同日または cooldown 期間中の新規entryを「止めた場合」を仮想評価する。
- 止めたことで避けた負けを `avoided_loss` とする。
- 止めたことで逃した勝ちを `missed_profit` とする。
- `net_counterfactual_effect = avoided_loss - missed_profit`。
- プラスなら停止候補、マイナスなら副作用大とみなす。
- ただし代表月だけで本採用しない。

stop対象の初期範囲:
- `daily_loss_stop`: 同一UTC日で累積損失が閾値を超えた後、新規entry停止候補。
- `consecutive_loss_stop`: 連敗数が閾値に達した後、新規entry停止候補。
- `drawdown_stop`: cumulative equity の peak からの下落が閾値を超えた後、新規entry停止候補。
- `cooldown_after_loss`: 負けtrade後、一定時間の新規entry停止候補。
- `max_trades_per_day` は後続候補として保持する。

Go/No-Go:
- 代表月だけで停止条件を本採用しない。
- stop発動後に `missed_profit` が `avoided_loss` を上回るなら統合しない。
- stop条件が少数tradeにしか効かない場合は判断保留。
- risk managementは収益最大化ではなく破滅回避・損失拡大抑制を主目的とする。
- 複数月確認前に本体停止ロジック化しない。
- lot sizing導入前の評価限界を明記する。

未解決事項:
- pips / R / 金額の最終基準。
- lot sizing導入タイミング。
- daily boundaryを UTC / JST / NY close のどれにするか。
- open position 強制決済を扱うか。
- stop後の再開条件。
- cost-adjusted logs を使うか。
- swap/commission/slippage反映後に再評価するか。

注意:
- 本節は I/O 契約固定であり、backtest再実行・Risk/Stop実装・BacktestRunner変更・PipelineAdapter変更・売買ロジック変更・lot sizing実装・閾値確定を含まない。

### 6.96 Risk/Stop v0.2 diagnostic script（最小後処理）
目的:
- 既存 `trade_logs` に対して `daily_loss_stop` と `consecutive_loss_stop` の counterfactual を評価する。
- 本体停止ロジックではなく、closed trade の後処理診断として実施する。

実装範囲（v0.2最小）:
- 対象: `daily_loss_stop` / `consecutive_loss_stop`
- 対象外（後続候補）: `drawdown_stop` / `cooldown_after_loss` / `lot sizing`
- backtest再実行・BacktestRunner/PipelineAdapter変更・売買ロジック変更は行わない。

時刻/評価方針:
- `entry_time` / `exit_time` は UTC正規化して扱う。
- daily boundary は UTC date。
- closed tradesのみ評価し、open position強制決済は扱わない。
- trade順は `exit_time` 昇順（同時刻は `entry_time` / `trade_id` で安定化）。

損益方針:
- source は `trade_logs.pnl`（price unit）。
- `pnl_pips = pnl / pip_size` で補助評価（USDJPY初期 `pip_size=0.01`）。
- price unit と pips を分離して出力する。

counterfactual仕様:
- `daily_loss_stop`:
  - 同一UTC日で `daily_pips` が `-threshold` 以下になった時点以降、同日後続tradeを仮想停止対象とする。
  - trigger trade自体は止めない。
- `consecutive_loss_stop`:
  - 連敗数が threshold 到達後、同日後続tradeを仮想停止対象とする。
  - trigger trade自体は止めない。
  - 連敗カウントとstop状態はUTC日でリセットする。
- stopped trades から `avoided_loss` / `missed_profit` / `net_counterfactual_effect` を算出する。

出力:
- `risk_stop_v2_trade_analysis.csv`
- `risk_stop_v2_summary.csv`
- `risk_stop_v2_summary.md`

注意:
- これは既存trade_logsの後処理診断であり、収益性確認ではない。
- 代表月単独で本採用判断を行わない。

### 6.97 Risk/Stop v0.2 diagnostic result（代表runレビュー）
対象run:
- `run_id: oos2_202411_session_v2_diag_trailing_matched`
- `trade_count=64`
- `total_pnl=0.29010000000004366`

前提:
- これは既存 `trade_logs` の後処理診断であり、本体停止ロジックではない。
- backtest再実行・売買ロジック変更・閾値確定は行っていない。

結果要約:

| stop_type | threshold | stopped_trade_count | avoided_loss_pips | missed_profit_pips | net_counterfactual_effect_pips | avoided_loss_pnl | missed_profit_pnl | net_counterfactual_effect_pnl | trigger_count |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| consecutive_loss_stop | 2 | 2 | 0.0 | 0.75 | -0.75 | 0.0 | 0.0075 | -0.0075 | 1 |
| consecutive_loss_stop | 3 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0 |
| daily_loss_stop | 20 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0 |
| daily_loss_stop | 30 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0 |
| daily_loss_stop | 50 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0 |

解釈:
- `daily_loss_stop`（20/30/50）は代表月で発動なしのため、採用判断は保留。
- `consecutive_loss_stop=2` は1回発動したが、回避損失なし・逸失利益0.75 pipsで `net` がマイナス。
- `consecutive_loss_stop=3` は発動なしのため、採用判断は保留。
- よって、この代表月では Risk/Stop 本体統合の根拠は得られていない。

現時点判断:
- `daily_loss_stop` / `consecutive_loss_stop` の本体統合は保留（No-Go寄り）。
- ただし「Risk/Stop不要」の意味ではなく、良好月では停止条件が効きにくい可能性を示す。
- 悪化月・連敗月・高DD月で複数月確認するまで、本採用判断を行わない。
- Risk/Stop は diagnostic/counterfactual layer として継続する。

注意:
- これは収益性確認ではなく、既存trade_logsの構造診断結果である。

### 6.98 Phase 8 Validation Framework v0.2 Design（実装前）
目的:
- 代表月単独の結果で filter化・本採用判断をしないための検証枠組みを定義する。
- OOS月、複数月、悪化月、良好月、条件別比較を分離する。
- 過剰最適化を避ける。
- 収益性断定ではなく、構造安定性・副作用・再現性を確認する。

対象:
- HTF v2
- SR v2 rolling high/low
- Session v2
- Risk/Stop v2
- Halt/Risk保留候補
- Exit policy
- future candidate filters

Validationの基本単位:
- monthly run
- quarter run
- representative month
- adverse month
- positive month
- volatility regime
- trade_count bucket
- diagnostic label group

データ分割方針:
- exploration period
- confirmation period
- holdout / untouched period
- rolling / walk-forward 候補
- 同じOOS結果を見ながら閾値を逐次変更しない。
- 古いデータを最近データと同じ重みで最適化しない。

評価軸:
- `trade_count`
- `total_pnl`
- `average_pnl`
- `win_rate`
- `max_drawdown`
- `net_counterfactual_effect`
- `avoided_loss / missed_profit`
- `label coverage`
- `stopped_trade_count`
- `monthly consistency`
- `degradation / instability`
- `sample size sufficiency`

判定カテゴリ:
- Continue diagnostic
- Promote to multi-month check
- Keep as explanation layer
- Pause / No-Go
- Candidate for implementation
- Candidate for future research

Go/No-Go共通基準:
- 代表月単独ではGoにしない。
- sample sizeが少ない場合は判断保留。
- `missed_profit` が `avoided_loss` を上回る場合は本体統合しない。
- filter化で利益源を削る場合は No-Go。
- 良い月だけに合わせた閾値調整をしない。
- 複数月で同傾向が出る場合のみ次段階へ進む。
- cost/slippage/swap 未反映の限界を明記する。

各レイヤーの現在ステータス:
- HTF v2: `diagnostic/explanation layer`。filter化保留。
- SR v2 rolling high/low: breakout近接ラベル。filter化保留。
- reaction SR: future candidate。
- Session v2: UTC固定近似diagnostic label。filter化保留。
- Risk/Stop v2: daily/consecutive counterfactualは代表月で統合根拠なし。悪化月確認候補。
- Halt/Risk: Phase 2で No-Go、一時保留。

Validation output候補:
- `validation_run_id`
- `period_start`
- `period_end`
- `module_name`
- `candidate_name`
- `policy`
- `trade_count`
- `total_pnl`
- `average_pnl`
- `win_rate`
- `max_drawdown`
- `avoided_loss`
- `missed_profit`
- `net_counterfactual_effect`
- `sample_size_flag`
- `decision_status`
- `decision_reason`

優先検証候補:
- Risk/Stopを悪化月で再確認。
- Session v2を複数月で確認。
- SR v2 rolling high/lowを複数月で確認。
- HTF v2を複数月で説明ラベルとして確認。
- Halt/Risk F候補を必要なら複数月確認。
- ただし一気に実装・本採用しない。

未解決事項:
- validation対象月セット。
- 悪化月の選び方。
- walk-forward window長。
- holdout期間の定義。
- max_drawdown計算の正式導入時期。
- cost-adjusted logsを標準評価に使うか。
- OANDA near-live logsとの接続タイミング。

注意:
- 本節は実装前設計であり、backtest再実行・売買ロジック変更・Validation実装・Runner変更・閾値変更を含まない。

### 6.99 Phase 8 Validation v0.2 I/O Contract & Decision Policy（実装前固定）
目的:
- Phase 8 Validation Framework v0.2 の実装前段階として、I/O契約と意思決定ポリシーを固定する。
- 代表月単独の結果で本採用判断しないため、複数月・悪化月・良好月・OOS/holdout を分けた評価規約を明文化する。

入力候補:
- `backtest_summary.csv`
- `trade_logs.csv`
- `decision_logs.csv`
- HTF/SR/Session diagnostic summaries
- Risk/Stop counterfactual summaries
- cost-adjusted summaries
- `run_metadata.json`
- manually defined validation run list

validation unit:
- one row per module/candidate/period/policy
- `module_name`
- `candidate_name`
- `policy`
- `period_start`
- `period_end`
- `period_type`
- `run_id`
- `source_run_dir`

`period_type` 候補:
- `representative_month`
- `adverse_month`
- `positive_month`
- `oos_month`
- `quarter`
- `holdout`
- `walk_forward_train`
- `walk_forward_test`

出力CSV候補:
- `validation_v0_2_summary.csv`
- `validation_v0_2_decision_log.csv`
- `validation_v0_2_layer_status.csv`
- `validation_v0_2_summary.md`

`validation_v0_2_summary.csv` 列候補:
- `validation_run_id`
- `module_name`
- `candidate_name`
- `policy`
- `period_start`
- `period_end`
- `period_type`
- `run_id`
- `trade_count`
- `total_pnl`
- `average_pnl`
- `win_rate`
- `max_drawdown`
- `avoided_loss`
- `missed_profit`
- `net_counterfactual_effect`
- `label_coverage`
- `stopped_trade_count`
- `sample_size_flag`
- `cost_adjusted_flag`
- `data_quality_flag`
- `decision_status`
- `decision_reason`

`decision_status` 候補:
- `continue_diagnostic`
- `promote_to_multi_month_check`
- `keep_as_explanation_layer`
- `pause_no_go`
- `candidate_for_implementation`
- `future_research`
- `insufficient_sample`
- `needs_cost_adjusted_check`

`decision_reason` 方針:
- 短文で理由を残す。
- 代表月単独の場合はその旨を必ず記録する。
- sample size不足なら件数を明記する。
- `missed_profit > avoided_loss` の場合は副作用として記録する。
- filter化で利益源を削る場合は No-Go 理由として記録する。
- cost/slippage/swap 未反映なら限界を記録する。

sample size 方針（初期仮説）:
- 初期は定量基準を本採用しない。
- `trade_count` が少ないものは `sample_size_flag=low` とする。
- 例:
  - `< 20`: `low` 候補
  - `20-50`: `medium` 候補
  - `>= 50`: `normal` 候補
- 本採用値ではなく、診断上の暫定フラグとする。

module別 decision 方針:
- HTF v2:
  - filter化ではなく説明ラベル継続。
  - 複数月で label distribution と損益を確認する。
- SR v2 rolling high/low:
  - breakout近接ラベルとして継続。
  - reaction SRとは分離する。
- Session v2:
  - UTC固定近似ラベルとして継続。
  - DST未補正のまま本採用filterにしない。
- Risk/Stop v2:
  - daily/consecutive stop は代表月で統合根拠なし。
  - 悪化月・連敗月で再確認候補とする。
- Halt/Risk:
  - Phase 2では No-Go。
  - F候補は将来の複数月確認候補とする。
- Exit policy:
  - `simple` / `conservative` / `next_bar` を現実耐性軸として区別する。

Go/No-Go 共通基準:
- 代表月単独で `candidate_for_implementation` にしない。
- `sample_size_flag=low` の場合は原則 `insufficient_sample` とする。
- `net_counterfactual_effect` がマイナスなら `pause_no_go` 寄りとする。
- `missed_profit` が大きい場合は副作用として記録する。
- 複数月で同傾向が出た場合のみ次段階に進む。
- cost-adjusted未確認なら `needs_cost_adjusted_check` を候補にする。

未解決事項:
- validation対象月セット。
- `adverse_month` の選び方。
- `period_type` の最終定義。
- `max_drawdown` 計算の正式導入。
- cost-adjusted summary の標準入力化。
- validation report 自動生成の実装タイミング。
- near-live dry-run結果との接続。

注意:
- 本節は設計契約固定であり、backtest再実行・Validation実装・Runner変更・売買ロジック変更・閾値変更を含まない。

### 6.100 Phase 8 Validation Target Period Set v0.2（実装前）
目的:
- 複数月確認に使う期間を事前固定する。
- 代表月だけで本採用・棄却判断しない。
- 良い月だけ、悪い月だけを都合よく選ばない。
- `exploration / confirmation / holdout` の役割を分ける。

初期対象期間候補:
- OOS-1: `2024-07`, `2024-08`, `2024-09`
- OOS-2: `2024-10`, `2024-11`, `2024-12`
- `representative_month`: `2024-11`
- `additional_check` 候補: `2024-08`, `2024-12`
- `holdout` 候補: 未使用期間を後続で指定

`period_type` 候補:
- `representative_month`
- `confirmation_month`
- `adverse_candidate_month`
- `positive_candidate_month`
- `holdout_candidate`
- `diagnostic_reference_month`

既存結果からの分類方針:
- `total_pnl` だけで分類しない。
- `trade_count`, `win_rate`, `average_pnl`, `drawdown`, `net_counterfactual_effect` も確認する。
- sample size が少ない月は adverse/positive と断定しない。
- cost未反映の結果だけで最終判断しない。

各レイヤーの複数月確認方針:
- HTF v2: label分布とentry損益を複数月で確認。
- SR v2 rolling high/low: `sr_proximity_flag` の損益傾向を複数月で確認。
- Session v2: `session_label` / `low_liquidity` / `hour_utc` を複数月で確認。
- Risk/Stop v2: 良好月だけでなく悪化月/連敗月で確認。
- Halt/Risk: F候補を確認する場合は事前に対象月を固定。
- Exit policy: `simple/conservative/next_bar` の比較対象月を固定。

holdout方針:
- すぐに全期間を使い切らない。
- 本採用候補が出るまで未使用期間を残す。
- holdoutは閾値調整に使わない。
- holdout結果が悪い場合は採用を見送る。

禁止事項:
- 結果を見ながら対象月を追加・削除しない。
- 良かった月だけで本採用しない。
- 悪かった月だけを理由に構造候補を即棄却しない。
- 代表月単独で `candidate_for_implementation` にしない。

未解決事項:
- `adverse_month` の定量選定基準。
- `positive_month` の定量選定基準。
- holdout期間の最終指定。
- cost-adjusted結果を対象月分類に使うか。
- `max_drawdown` をいつ正式評価軸に入れるか。
- 2024年以外の期間をいつ使うか。

注意:
- 本節は対象期間セットの設計整理であり、backtest再実行・Validation実装・Runner変更・売買ロジック変更・閾値変更を含まない。

### 6.101 Phase 8 Validation v0.2 Summary Script Design（実装前）
目的:
- 既存runや診断結果を集約し、module/candidate/period別の validation summary を作る。
- 代表月単独の判断を避ける。
- `decision_status` / `decision_reason` を機械的に記録する準備をする。
- ただし今回は実装しない。

入力候補:
- `run_metadata.json`
- `backtest_summary.csv`
- `trade_logs.csv`
- `htf_v2_group_summary.csv`
- `sr_v2_group_summary.csv`
- `session_v2_group_summary.csv`
- `risk_stop_v2_summary.csv`
- `cost_adjusted_summary.csv`
- manually defined `validation_targets.csv`

`validation_targets.csv` 設計候補:
- `validation_target_id`
- `period_start`
- `period_end`
- `period_type`
- `run_id`
- `run_dir`
- `module_name`
- `candidate_name`
- `policy`
- `notes`

出力候補:
- `validation_v0_2_summary.csv`
- `validation_v0_2_decision_log.csv`
- `validation_v0_2_layer_status.csv`
- `validation_v0_2_summary.md`

`validation_v0_2_summary.csv` 列候補:
- `validation_run_id`
- `validation_target_id`
- `module_name`
- `candidate_name`
- `policy`
- `period_start`
- `period_end`
- `period_type`
- `run_id`
- `trade_count`
- `total_pnl`
- `average_pnl`
- `win_rate`
- `max_drawdown`
- `avoided_loss`
- `missed_profit`
- `net_counterfactual_effect`
- `label_coverage`
- `stopped_trade_count`
- `sample_size_flag`
- `cost_adjusted_flag`
- `data_quality_flag`
- `decision_status`
- `decision_reason`

初期 decision rule 候補:
- `trade_count < 20`: `insufficient_sample` 候補
- `representative_month` 単独: `candidate_for_implementation` 禁止
- `net_counterfactual_effect < 0`: `pause_no_go` 寄り
- `missed_profit > avoided_loss`: 副作用として `decision_reason` に記録
- `cost_adjusted_flag=False`: `needs_cost_adjusted_check` 候補
- module が HTF/SR/Session で filter化根拠なし: `keep_as_explanation_layer`
- 複数月確認前: `continue_diagnostic`

module別初期ステータス:
- HTF v2: `keep_as_explanation_layer`
- SR v2 rolling high/low: `keep_as_explanation_layer`
- reaction SR: `future_research`
- Session v2: `keep_as_explanation_layer`
- Risk/Stop v2: `continue_diagnostic` / `adverse_month_check` 候補
- Halt/Risk: `pause_no_go` / `future_multi_month_check` 候補
- Exit policy: `continue_diagnostic` / `cost_adjusted_check` 候補

実装時の注意:
- 入力ファイル欠損時は warning にする。
- `logs/data_private` をGit追加しない。
- `validation_targets.csv` はテンプレートとして `docs` または `ops` 配下に置くか将来判断。
- `run_dir` 依存を強くしすぎない。
- 収益性確認済みのように書かない。

未解決事項:
- `validation_targets.csv` をどこに置くか。
- 既存runの命名揺れ対応。
- diagnostic summaryごとのschema差。
- `max_drawdown` 未計算時の扱い。
- cost_adjusted標準入力化。
- Markdown reportの粒度。

注意:
- 本節は実装前設計であり、backtest再実行・Validation実装・Runner変更・売買ロジック変更・閾値変更を含まない。

### 6.102 Phase 8 Validation v0.2 minimal summary script（最小実装）
目的:
- `validation_targets_v0_2.csv` を起点に、既存run/summaryを module/candidate/period 単位で最小集約する。
- 代表月単独での本採用判断を避け、意思決定補助のための `decision_status` を機械的に出す。
- これは検証整理の後処理であり、収益性確認ではない。

最小実装方針:
- 欠損ファイルを許容し、warning扱いで処理継続する。
- 最初から全diagnostic summaryの完全対応を狙わない。
- `backtest_summary.csv` 優先、欠損時は `trade_logs.csv` から基本指標を計算する。
- 両方欠損時は metrics を空欄にし `data_quality_flag=missing_source` とする。

`validation_targets_v0_2.csv`:
- 列:
  - `validation_target_id`
  - `period_start`
  - `period_end`
  - `period_type`
  - `run_id`
  - `run_dir`
  - `module_name`
  - `candidate_name`
  - `policy`
  - `notes`
- `run_dir` は参照文字列として保持し、実ファイル欠損は warning で処理継続する。

出力:
- `validation_v0_2_summary.csv`
- `validation_v0_2_decision_log.csv`
- `validation_v0_2_layer_status.csv`
- `validation_v0_2_summary.md`

初期 decision rule（機械ルール）:
- `trade_count` 不明: `insufficient_sample`（`missing trade_count/source`）
- `trade_count < 20`: `insufficient_sample`
- module が `htf_v2/sr_v2/session_v2`: `keep_as_explanation_layer`
- module が `risk_stop_v2` かつ `net_counterfactual_effect_pips < 0`: `pause_no_go`
- module が `risk_stop_v2` で triggerなし/少数: `continue_diagnostic`
- module が `exit_policy` で cost-adjusted summary 欠損: `needs_cost_adjusted_check`
- 上記以外: `continue_diagnostic`

`sample_size_flag`（初期仮説）:
- `< 20`: `low`
- `20 <= x < 50`: `medium`
- `>= 50`: `normal`
- 不明: `unknown`
- この閾値は初期仮説であり、本採用値ではない。

注意:
- これは既存run/summaryの後処理集約であり、backtest再実行・売買ロジック変更・Runner/PipelineAdapter変更・閾値本採用を含まない。

### 6.103 Phase 8 Validation v0.2 minimal summary result（初回生成レビュー）
対象:
- `validation_run_id: validation_v0_2_minimal`
- target数: 5
- 出力:
  - `validation_v0_2_summary.csv`
  - `validation_v0_2_decision_log.csv`
  - `validation_v0_2_layer_status.csv`
  - `validation_v0_2_summary.md`

結果要約:

| validation_target_id | module_name | candidate_name | trade_count | total_pnl | average_pnl | sample_size_flag | decision_status | decision_reason |
| --- | --- | --- | ---: | ---: | ---: | --- | --- | --- |
| representative_202411_exit_simple | exit_policy | simple_trailing_after_1R | 64 | 0.2901 | 0.004533 | normal | needs_cost_adjusted_check | cost_adjusted_summary missing |
| representative_202411_session_v2 | session_v2 | utc_fixed_session_label | 64 | 0.2901 | 0.004533 | normal | keep_as_explanation_layer | diagnostic label layer; no filter promotion from representative month only |
| representative_202411_risk_stop_v2 | risk_stop_v2 | daily_consecutive_stop | 64 | 0.2901 | 0.004533 | normal | pause_no_go | net_counterfactual_effect=-0.750000 < 0 |
| representative_202411_sr_v2 | sr_v2 | rolling_high_low | 64 | 0.2901 | 0.004533 | normal | keep_as_explanation_layer | diagnostic label layer; no filter promotion from representative month only |
| representative_202411_htf_v2 | htf_v2 | h4_h1_context | 64 | 0.2901 | 0.004533 | normal | keep_as_explanation_layer | diagnostic label layer; no filter promotion from representative month only |

追加観測（risk_stop_v2）:
- `avoided_loss=0.0`
- `missed_profit=0.75`
- `net_counterfactual_effect=-0.75`
- `stopped_trade_count=2`

解釈:
- 初回 validation summary 生成は成功。
- 各レイヤーの `decision_status` は既存の個別診断結果と整合。
- HTF/SR/Session は explanation layer 継続。
- Risk/Stop は代表月では `pause_no_go`。
- Exit policy は `cost_adjusted_check` 待ち。
- 代表月単独で `candidate_for_implementation` は出していない。

改善候補（後続）:
- `win_rate` / `max_drawdown` が現時点では NaN のため、後続補完候補として扱う。

注意:
- これは既存run/summaryの後処理集約レビューであり、収益性確認ではない。

### 6.104 Phase 9 near-live / dry-run v0.2 Design（実装前）
目的:
- 実注文なしで、EAがリアルタイムに近い流れで判断・ログ出力できるか確認する。
- backtestとは異なり、逐次到着するbarを前提にする。
- 注文送信ではなく、`signal / decision / risk / explanation logs` の整合確認を目的とする。
- 収益性確認ではなく、運用前の構造・ログ・停止判断の確認である。

初期スコープ:
- OANDA/API接続は後続。
- 最初はCSVまたは疑似stream入力でよい。
- 1本ずつbarを読み込み、既存Pipeline相当の判断を行う。
- 実注文は送らず、paper decisionとして記録する。
- position管理も最初は仮想扱い。

対象ログ候補:
- `near_live_decision_logs.csv`
- `near_live_signal_logs.csv`
- `near_live_event_logs.csv`
- `near_live_state_logs.csv`
- `near_live_risk_logs.csv`
- `near_live_validation_warnings.csv`

出力列候補:
- `timestamp`
- `input_bar_status`
- `data_valid_flag`
- `signal_type`
- `entry_signal`
- `exit_signal`
- `trade_ok`
- htf_v2 fields
- sr_v2 fields
- session_v2 fields
- `risk_stop_state`
- `halt_state`
- `decision_reason`
- `paper_order_action`
- `paper_position_state`
- `warning_flags`

dry-runの責務:
- 実注文しない。
- 約定したと仮定しない。
- 判断ログを残す。
- `data delay / missing bar / duplicate bar` を検知する。
- decisionが再現可能か確認する。
- Backtest結果と完全一致を要求しないが、原因説明可能性を重視する。

Backtestとの違い:
- backtestは過去データ全体を使った検証。
- dry-runは逐次処理・運用耐性確認。
- dry-runでは未来データを絶対に使わない。
- warmupは過去履歴として明示的に渡す。
- 未確定barは使わない。

Go/No-Go:
- ログ欠損・時刻不整合・重複barが解決できない場合は No-Go。
- signal/decision/reason が追跡できない場合は No-Go。
- 実注文接続は dry-run ログが安定してから。
- near-live で一定期間エラーなく記録できることを次段階条件にする。
- 収益性ではなく、運用整合性・ログ完全性・停止判断の追跡性を評価する。

Validation Frameworkとの接続:
- dry-run結果も将来 validation input に追加する。
- near-live logs は backtest summary と同じ形式へ変換できるようにする。
- `validation_status` に `dry_run_candidate / near_live_observed` などを将来追加する候補を残す。

未解決事項:
- OANDA API接続タイミング。
- CSV replay dry-runを先に作るか。
- 疑似stream入力形式。
- paper position管理の粒度。
- spread/slippage/swap の扱い。
- dry-runログ保存場所。
- 実デモ注文へ進む条件。
- エラー時停止/再開方針。

注意:
- 本節は実装前設計であり、OANDA/API接続・実注文・near-live実装・Runner変更・売買ロジック変更・閾値変更を含まない。

### 6.105 Phase 9 near-live / dry-run v0.2 I/O Contract & Diagnostic Policy（実装前固定）
目的:
- Phase 9 near-live / dry-run v0.2 の実装前段階として、I/O契約と診断ポリシーを固定する。
- 実注文なしで逐次bar処理時の判断・ログ整合性・時刻整合性・追跡可能性を確認する。
- 今回は設計契約の明文化に限定し、dry-run本体実装は行わない。

重要前提:
- 実 broker / OANDA API / 実注文送信は未実装。
- デモ注文も送らない。
- 収益性確認済みではない。
- HTF/SR/Session/RiskStop は本体filter化せず、diagnostic/explanation/counterfactual layer として継続する。

初期入力方針:
- 初期優先は CSV replay input とする。
- OANDA stream/API は後続候補として保持する。
- 基本処理単位は M5 bars とする。
- `warmup bars` と `live/replay bars` を明示的に分離する。
- 未確定barは使用しない。
- timestamp は UTC aware を必須とする。

入力列候補（CSV replay）:
- `timestamp`
- `open`
- `high`
- `low`
- `close`
- `volume`
- `spread_pips`（optional）
- `source`
- `data_valid_flag`（optional）

dry-run mode 候補:
- `csv_replay`
- `pseudo_stream`
- `oanda_dry_run_future`
- 初期設計対象は `csv_replay` のみとする。

状態管理候補:
- `current_timestamp`
- `last_processed_timestamp`
- `warmup_ready_flag`
- `data_gap_flag`
- `duplicate_bar_flag`
- `out_of_order_flag`
- `paper_position_state`
- `pending_signal_state`
- `risk_stop_state`
- `halt_state`

出力ログ候補:
- `near_live_decision_logs.csv`
- `near_live_signal_logs.csv`
- `near_live_event_logs.csv`
- `near_live_state_logs.csv`
- `near_live_risk_logs.csv`
- `near_live_validation_warnings.csv`

`near_live_decision_logs.csv` 列候補:
- `timestamp`
- `mode`
- `input_bar_status`
- `data_valid_flag`
- `warmup_ready_flag`
- `entry_signal`
- `exit_signal`
- `signal_type`
- `trade_ok`
- `decision_reason`
- `htf_v2_* fields`
- `sr_v2_* fields`
- `session_v2_* fields`
- `risk_stop_state`
- `halt_state`
- `paper_order_action`
- `paper_position_state`
- `warning_flags`

`near_live_event_logs.csv` 列候補:
- `timestamp`
- `event_type`
- `severity`
- `message`
- `source`
- `recovery_action`
- `resolved_flag`

diagnostic policy:
- 実注文しない。
- 約定したと断定しない。
- `paper_order_action` は仮想判断として扱う。
- backtest 完全一致を要求しない。
- 差分が出た場合は、入力範囲・warmup・未確定bar・時刻境界・ログ列差分で説明する。
- ログ欠損や時刻不整合は No-Go 候補とする。

Go/No-Go 方針:
- timestamp 重複・欠損・逆順を検知できない場合は No-Go。
- `decision_reason` が空欄になる場合は No-Go。
- warning が多発する場合は No-Go。
- paper decision が追跡不能な場合は No-Go。
- OANDA/API 接続は `csv_replay` dry-run が安定してから着手する。
- 実注文接続はさらに後段とする。

Validation Framework との接続方針:
- dry-run summary を将来 validation input にする。
- near_live logs を `validation_v0_2_summary` へ変換可能にする。
- validation `period_type` 候補に `dry_run_period` / `near_live_observed` を将来追加する。
- dry-run は収益性確認ではなく、運用整合性確認として扱う。

未解決事項:
- csv_replay runner を新規scriptにするか、既存runnerを使うか。
- paper position 管理の粒度。
- exit 判定をどこまで再現するか。
- spread/slippage/swap を dry-run で扱うか。
- warnings の重大度定義。
- dry-run ログ保存場所。
- OANDA 接続の導入条件。
- near-live から demo order へ進む条件。

注意:
- 本節は I/O 契約固定であり、OANDA/API接続・実注文・デモ注文・dry-run本体実装・Runner変更・売買ロジック変更・閾値変更を含まない。

### 6.106 Phase 9 CSV replay dry-run skeleton 実装方針（最小実装）
目的:
- Phase 9 near-live / dry-run v0.2 の最小実装として、CSV replay を1本ずつ処理する dry-run skeleton を追加する。
- 実注文を伴わず、時刻整合性・ログ完全性・追跡可能性を確認する。
- 収益性確認ではなく、運用整合性確認を目的とする。

スコープ:
- `scripts/run_csv_replay_dry_run.py` による最小CLIを追加する。
- 入力はM5 CSVを想定し、timestampを `pandas.to_datetime(..., utc=True)` でUTC正規化する。
- `warmup_start <= timestamp < replay_start` を warmup bars、
  `replay_start <= timestamp < replay_end` を replay bars として分離する。
- replay bars を逐次処理し、near-live風ログを出力する。

初期 skeleton の判断仕様:
- 実注文しない。
- デモ注文しない。
- `entry_signal=False` / `exit_signal=False` / `trade_ok=False` の placeholder とする。
- `paper_order_action` は `none` とする。
- `decision_reason` は空欄にしない。

warning 検知（最小）:
- duplicate timestamp を warning 記録する。
- out-of-order timestamp（CSV原順での逆順）を warning 記録する。
- `expected_timeframe_minutes` と実差分の不一致による data gap を warning 記録する。
- warning を握りつぶさず、`near_live_validation_warnings.csv` と event log に残す。

出力（最小）:
- `near_live_decision_logs.csv`
- `near_live_event_logs.csv`
- `near_live_state_logs.csv`
- `near_live_validation_warnings.csv`
- `near_live_summary.csv`
- `near_live_summary.md`

PipelineAdapter との関係:
- 初期 skeleton では PipelineAdapter 接続を必須にしない。
- 将来、関数分離された処理点から PipelineAdapter を接続できる余地を残す。

注意:
- OANDA/API接続・実注文送信・デモ注文送信・売買ロジック変更・HTF/SR/Session/RiskStop/Halt の filter化は本節の対象外。
- Backtest 完全一致は要求しない。

### 6.107 Phase 9 CSV replay dry-run skeleton 代表M5 sliceローカル実行結果（2024-01-03 1day）
目的:
- Phase 9 CSV replay dry-run skeleton の最小実装が、代表M5 sliceで時刻整合とログ完全性を満たすかを確認する。
- 収益性確認ではなく、構造確認・診断ログ確認を目的とする。

使用CSV:
- `data/private/backtest_slices/USDJPY_M5_2024-01-02_2024-01-09.csv`
- 列: `timestamp, open, high, low, close, spread, volume`
- `spread` は `0.2 pips fixed fallback` 前提。
- 本CSVは dry-run skeleton 構造確認用であり、運用近似スプレッド検証・収益性確認用途ではない。

実行コマンド（PowerShell）:
- `$env:PYTHONPATH='.'`
- `python scripts/run_csv_replay_dry_run.py --input-csv data/private/backtest_slices/USDJPY_M5_2024-01-02_2024-01-09.csv --output-dir outputs/near_live/csv_replay/2024-01-03_1day --run-id near_live_csv_replay_usdjpy_m5_2024_01_03_1day --warmup-start 2024-01-02T00:00:00Z --replay-start 2024-01-03T00:00:00Z --replay-end 2024-01-04T00:00:00Z --expected-timeframe-minutes 5`

結果サマリ:
- `mode=csv_replay`
- `warmup_bar_count=288`
- `replay_bar_count=288`
- `warning_count=0`
- `duplicate_bar_count=0`
- `data_gap_count=0`
- `out_of_order_count=0`
- `decision_log_count=288`

decision logs 先頭/末尾確認:
- first timestamp: `2024-01-03T00:00:00+00:00`
- last timestamp: `2024-01-03T23:55:00+00:00`
- placeholder方針どおり `entry_signal=False` / `exit_signal=False` / `trade_ok=False` / `paper_order_action=none`
- `decision_reason=csv_replay_skeleton:no_signal_no_trade` を全件で保持

解釈:
- 1日分 replay の時刻整合・ログ出力整合は最小要件を満たした。
- warning 0件は当該期間の入力品質（重複・逆順・gap未検知）として記録する。
- 本結果は収益性確認ではない。

注意:
- 本節は実行結果記録のみであり、コード変更・売買ロジック変更・PipelineAdapter接続・OANDA/API接続は行っていない。

### 6.108 Phase 9 CSV replay dry-run skeleton 複数日実行結果と weekend/market closure gap の扱い
目的:
- 1day replay 記録に加えて、複数日 replay の warning 挙動を記録し、weekend / market closure gap の扱いを明文化する。
- 収益性確認ではなく、運用整合性・ログ追跡性の確認を目的とする。

実行条件（複数日）:
- 入力CSV: `data/private/backtest_slices/USDJPY_M5_2024-01-02_2024-01-09.csv`
- `warmup_start=2024-01-02T00:00:00Z`
- `replay_start=2024-01-03T00:00:00Z`
- `replay_end=2024-01-09T00:00:00Z`
- `expected_timeframe_minutes=5`

結果サマリ:
- 1day replay（2024-01-03〜2024-01-04）:
  - `warning_count=0`（正常完了）
- 複数日 replay（2024-01-03〜2024-01-09）:
  - `replay_bar_count=1151`
  - `warning_count=1`
  - `duplicate_bar_count=0`
  - `data_gap_count=1`
  - `out_of_order_count=0`

warning詳細:
- `timestamp=2024-01-07T17:05:00+00:00`
- `warning_type=data_gap`
- `message=data gap detected: expected 0 days 00:05:00, got 2 days 00:10:00`

運用解釈（現時点方針）:
- 当該gapは通常欠損と即断せず、`weekend / market closure gap` 候補として扱う。
- したがって、今回の warning 1件のみを理由に dry-run skeleton を No-Go 判定しない。
- ただし、同種gapが市場休場説明と整合しない期間で多発する場合は、No-Go候補として再評価する。

Go/No-Go補足（csv_replay初期運用）:
- `data_gap` warning は一律 No-Go ではなく、`market closure由来か否か` を一次分類して扱う。
- `duplicate/out_of_order` は引き続き高優先で監視する。
- warningを握りつぶさず、`near_live_validation_warnings.csv` / `near_live_event_logs.csv` に必ず記録する。

注意:
- 本節は実行結果記録と運用方針明文化のみであり、コード変更・売買ロジック変更・PipelineAdapter接続・OANDA/API接続は行っていない。

### 6.109 Phase 9 gap classification design（実装前設計）
目的:
- near-live / CSV replay dry-run において、`data_gap` を一律扱いせず、`ordinary data_gap` と `expected weekend / market closure gap` を区別するための設計方針を固定する。
- warning検知の追跡性を保ったまま、Go/No-Go 判断の精度を上げる。

現状の制約:
- 現行 `scripts/run_csv_replay_dry_run.py` は `expected_timeframe_minutes` 超過を一律 `data_gap` warning として記録する。
- 取引カレンダー（祝日・メンテナンス・市場休止の厳密定義）は未導入。
- 現時点では分類ロジック未実装であり、設計文書化のみを行う。

gap classification案（実装候補）:
1. `ordinary_missing_bar_gap`
   - 通常市場時間中に期待足間隔を超えてbarが欠けている候補。
   - 原則 warning + investigation required。
   - 多発時は dry-run No-Go 候補。
2. `expected_weekend_gap`
   - 金曜終盤から日曜/週明け再開にまたがるgap候補。
   - 初期段階では warning 記録するが、単独では No-Go にしない。
3. `expected_market_closure_gap`
   - weekend 以外の市場休止・メンテナンス・祝日等に由来する可能性があるgap候補。
   - 取引カレンダー未導入段階では candidate 扱い。
4. `unexpected_market_hours_gap`
   - 通常市場時間中に発生し closure説明がつかないgap。
   - 優先度高く調査し、多発・長時間なら No-Go 候補。
5. `unknown_gap`
   - 現行情報では分類不能なgap。
   - warningとして保持し、後続情報で再分類する。

将来ログ列候補（今回は未実装）:
- `gap_class`
- `expected_gap_flag`
- `gap_duration`
- `previous_timestamp`
- `current_timestamp`
- `market_session_status`
- `gap_reason`
- `gap_action`
- `gap_requires_investigation`

Go/No-Go 判断方針（gap分類導入後）:
- `duplicate_timestamp` と `out_of_order_timestamp` は引き続き高優先warningとして扱う。
- `data_gap` は一律 No-Go としない。
- `expected_weekend_gap` / `expected_market_closure_gap` 候補は、単独では No-Go にしない。
- `unexpected_market_hours_gap` が多発する場合は No-Go 候補。
- `unknown_gap` は調査対象として扱う。
- warningは握りつぶさず、`near_live_validation_warnings.csv` / `near_live_event_logs.csv` / `near_live_state_logs.csv` に残す。
- gap分類を導入しても生ログの `warning_count` は維持し、summary側で分類別countを追加する方針とする。

実装しないこと（本節）:
- `scripts/run_csv_replay_dry_run.py` の変更。
- テスト変更、スキーマ変更、BacktestRunner/PipelineAdapter接続変更。
- 売買ロジック変更、HTF/SR/Session/RiskStop/Halt の filter化。
- OANDA/API接続、実注文/デモ注文。

次段階の実装候補:
- `gap_class` / `expected_gap_flag` を最小追加した分類ログの導入可否を判断。
- `expected_weekend_gap` と `unexpected_market_hours_gap` の最小判定ルール（UTCベース）を試験導入。
- summaryに分類別countを追加し、Validation Framework接続時のperiod summaryへ変換可能にする。

### 6.110 Phase 9 gap classification minimal implementation（実装済み最小仕様）
目的:
- CSV replay dry-run skeleton の `data_gap` warning に対して、最小限の分類情報を追加し、expected gap と investigation対象を区別可能にする。
- 収益性確認ではなく、運用整合性・診断追跡性の改善を目的とする。

実装済み最小仕様:
- `data_gap` warning 時に以下を出力する。
  - `gap_class`
  - `expected_gap_flag`
  - `gap_duration`
  - `previous_timestamp`
  - `current_timestamp`
  - `gap_reason`
  - `gap_action`
  - `gap_requires_investigation`
- 出力対象:
  - `near_live_validation_warnings.csv`
  - `near_live_event_logs.csv`
- `near_live_summary.csv` は既存countを維持したまま、分類別countを追加する。
  - `expected_weekend_gap_count`
  - `ordinary_missing_bar_gap_count`
  - `unknown_gap_count`

分類ルール（最小）:
- `expected_weekend_gap`
  - gap区間がUTC基準で weekend をまたぐ場合。
  - `expected_gap_flag=True`
  - `gap_requires_investigation=False`
  - `gap_reason=weekend_or_market_closure_candidate`
  - `gap_action=record_as_expected_gap`
- `ordinary_missing_bar_gap`
  - weekend をまたがない `data_gap`。
  - `expected_gap_flag=False`
  - `gap_requires_investigation=True`
  - `gap_reason=missing_bar_candidate`
  - `gap_action=investigate_missing_bars`
- `unknown_gap`
  - 分類不能時のfallback。
  - `expected_gap_flag=False`
  - `gap_requires_investigation=True`
  - `gap_reason=classification_unknown`
  - `gap_action=inspect_gap`

既存挙動との互換性:
- `warning_count`, `data_gap_count`, `duplicate_bar_count`, `out_of_order_count` は維持する。
- 既存ファイル名は変更しない。
- `duplicate_timestamp` / `out_of_order_timestamp` のwarning検知は維持する。
- duplicate / out_of_order warning では gap分類列は空欄デフォルトで出力する。

今回の対象外:
- 祝日・メンテナンスカレンダー導入。
- `expected_market_closure_gap` / `unexpected_market_hours_gap` の厳密判定実装。
- OANDA/API接続、実注文/デモ注文。
- BacktestRunner / PipelineAdapter / 売買ロジック変更。

注意:
- 本節は dry-run skeleton の最小分類実装記録であり、収益性確認ではない。

### 6.111 Phase 9 dry-run summary validation connection design
目的:
- Phase 9 CSV replay dry-run の `near_live_summary.csv` / `near_live_validation_warnings.csv` を、Phase 8 Validation Framework v0.2 の period summary / diagnostic summary へ接続するための設計を固定する。
- 接続先での評価軸を「収益性」ではなく「operational readiness / dry-run health」に限定する。
- 今回は文書設計のみとし、実装・テスト変更は行わない。

接続対象ログ:
- `near_live_summary.csv`
  - `warmup_bar_count`
  - `replay_bar_count`
  - `warning_count`
  - `duplicate_bar_count`
  - `out_of_order_count`
  - `data_gap_count`
  - `expected_weekend_gap_count`
  - `ordinary_missing_bar_gap_count`
  - `unknown_gap_count`
  - `decision_log_count`
- `near_live_validation_warnings.csv`
  - `warning_type`
  - `gap_class`
  - `expected_gap_flag`
  - `gap_requires_investigation`
  - `timestamp`
  - `previous_timestamp`
  - `current_timestamp`
- 補助参照（将来候補）:
  - `near_live_decision_logs.csv`
  - `near_live_state_logs.csv`
  - `near_live_event_logs.csv`

Validation Framework側で見るべき指標:
1. log completeness
   - `decision_log_count == replay_bar_count` を必須候補とする。
   - `state_log_count == replay_bar_count` は将来候補（現時点は設計メモ）。
   - warning/event logs が生成されること（出力欠落を許容しない）。
2. data quality warning summary
   - `warning_count`
   - `duplicate_bar_count`
   - `out_of_order_count`
   - `data_gap_count`
   - `expected_weekend_gap_count`
   - `ordinary_missing_bar_gap_count`
   - `unknown_gap_count`
3. dry-run placeholder integrity
   - `entry_signal=False`
   - `exit_signal=False`
   - `trade_ok=False`
   - `paper_order_action=none`
   - `paper_position_state=flat`
4. time consistency
   - timestamp は UTC として扱う。
   - warmup/replay split が定義どおりであること。
   - replay対象は `replay_start <= timestamp < replay_end`。
   - previous/current timestamp の順序整合を維持すること。

dry-run health status案:
- `status=pass`
- `status=warn`
- `status=investigate`
- `status=no_go_candidate`

初期判定案:
- `pass`
  - `warning_count=0`
  - log completeness OK
  - placeholder integrity OK
- `warn`
  - `expected_weekend_gap` のみ
  - log completeness OK
  - placeholder integrity OK
- `investigate`
  - `ordinary_missing_bar_gap` または `unknown_gap` あり
  - `duplicate_bar_count>0` または `out_of_order_count>0`
- `no_go_candidate`
  - `decision_log_count != replay_bar_count`
  - UTC/time order破綻
  - placeholder integrity 破綻
  - unexplained gaps（`ordinary_missing_bar_gap` / `unknown_gap`）多発

Go/No-Go候補ルール:
- `duplicate_bar_count>0` または `out_of_order_count>0` は高優先調査。
- `ordinary_missing_bar_gap_count>0` または `unknown_gap_count>0` は調査対象。
- `expected_weekend_gap` 単独は No-Go にしない。
- `decision_log_count != replay_bar_count` は No-Go候補。
- placeholder integrity が崩れた場合は No-Go候補。

出力候補（実装時の候補名のみ、今回は未実装）:
- `dry_run_period_summary.csv`
- `dry_run_period_summary.md`
- `dry_run_warning_summary.csv`
- `dry_run_health_check.csv`

実装しないこと:
- `scripts/run_csv_replay_dry_run.py` の変更。
- tests変更、BacktestRunner/PipelineAdapter接続変更。
- 売買ロジック変更。
- OANDA/API接続、実注文/デモ注文。

次段階の実装候補:
- Validation Framework側の period summary schema に dry-run health系列を追加する最小案の定義。
- `near_live_summary.csv` から `dry_run_period_summary.csv` へ変換する最小スクリプトの要否判断。
- `near_live_validation_warnings.csv` 集計から `dry_run_warning_summary.csv` を生成する最小実装の要否判断。
- PipelineAdapter接続は行わず、まずは後処理変換で責務分離を維持できるかを判断する。

### 6.112 Phase 9 dry-run summary validation minimal transformation implementation（最小実装）
目的:
- `near_live_summary.csv` と `near_live_validation_warnings.csv` を入力として、Phase 8 Validation Framework 接続用の最小dry-run summaryを生成する。
- 収益性確認ではなく、operational readiness / dry-run health の後処理要約を目的とする。

実装対象:
- `scripts/summarize_csv_replay_dry_run.py`
- `tests/unit/backtest/test_summarize_csv_replay_dry_run.py`

入力:
- 必須:
  - `near_live_summary.csv`
  - `near_live_validation_warnings.csv`
- 任意（今回未使用、将来拡張候補）:
  - `near_live_decision_logs.csv`
  - `near_live_state_logs.csv`
  - `near_live_event_logs.csv`

出力:
- `dry_run_period_summary.csv`
- `dry_run_period_summary.md`
- `dry_run_warning_summary.csv`

`dry_run_period_summary.csv` 最小列:
- `run_id`
- `mode`
- `replay_bar_count`
- `decision_log_count`
- `warning_count`
- `duplicate_bar_count`
- `out_of_order_count`
- `data_gap_count`
- `expected_weekend_gap_count`
- `ordinary_missing_bar_gap_count`
- `unknown_gap_count`
- `log_completeness_ok`
- `data_quality_status`
- `dry_run_health_status`
- `status_reason`

`dry_run_health_status` 判定順序（固定）:
1. `no_go_candidate`
   - `decision_log_count != replay_bar_count`
2. `investigate`
   - `duplicate_bar_count > 0`
   - `out_of_order_count > 0`
   - `ordinary_missing_bar_gap_count > 0`
   - `unknown_gap_count > 0`
3. `warn`
   - `warning_count > 0`
   - warningが `expected_weekend_gap` のみ
4. `pass`
   - `warning_count == 0`
   - `decision_log_count == replay_bar_count`

`dry_run_warning_summary.csv` 集計:
- `warning_type` 別count
- `gap_class` 別count
- `expected_gap_flag` 別count
- `gap_requires_investigation` 別count

今回の範囲:
- placeholder integrity の詳細判定は未実装（任意扱い）。
- 将来候補として、`near_live_decision_logs.csv` を用いた `entry_signal/exit_signal/trade_ok/paper_order_action/paper_position_state` の整合監査を追加可能。

注意:
- 本実装は summary変換の後処理であり、BacktestRunner/PipelineAdapter/売買ロジックは変更しない。
- 収益性確認ではない。

### 6.93 Session v0.2 diagnostic_only 最小実装メモ（2026-05-03）
- `PipelineAdapter` に `session_v2` の `diagnostic_only` 最小実装を追加した。
- `session_v2_enabled=True` でも `diagnostic_only` では entry を止めない（`entry_signal` / `trade_ok` を変更しない）。
- decision trace / decision_logs に session v0.2 列（`hour_utc` / `day_of_week` / `session_label` / sessionフラグ群）を出力する。
- 初期 `session_label` は UTC固定近似ラベル（tokyo/london/new_york/overlap/low_liquidity/off_session）として扱い、本採用時刻ではない。
- DST厳密補正は初期実装で行わず、`session_v2_use_dst_adjustment` は将来拡張フラグとして保持する。
- `session_risk_flag` は初期実装では `is_low_liquidity_hour=True` を仮想注意ラベルとして立てる。
- `session_reason` には `diagnostic_only:no_entry_filter` を含め、実filter化ではないことを明示する。

注意:
- 本実装は診断列追加であり、Session filter を本体entry制御として有効化していない。
- DST未対応のまま本採用filterにしない方針を維持する。
- これは収益性確認ではない。

### 6.94 Session v2 diagnostic trade analysis 後処理
目的:
- Session v2 `diagnostic_only` の既存entry/tradeを、session/time分類別に損益分解する。
- `low_liquidity` や特定sessionが悪化群かどうかを実filter化前に確認する。

対象:
- 既存 `decision_logs.csv` と `trade_logs.csv` の突合・集計のみ。
- backtest再実行・売買ロジック変更・Session filter有効化・閾値変更は行わない。

突合方針:
- `trade_logs.entry_time` を基準に `decision_logs.timestamp` とUTC正規化後に突合する。
- 時刻正規化は `pandas.to_datetime(..., utc=True)` を使用する。
- `decision_logs` に同一timestampが複数ある場合は最後の行を採用する。
- `trade_logs.pnl` を損益計算に使用する。

付与列（trade単位）:
- `session_v2_enabled`
- `session_policy`
- `hour_utc`
- `day_of_week`
- `session_label`
- `is_tokyo_session`
- `is_london_session`
- `is_new_york_session`
- `is_london_ny_overlap`
- `is_low_liquidity_hour`
- `session_risk_flag`
- `session_reason`
- `session_data_valid_flag`

出力:
- `session_v2_trade_analysis.csv`（trade単位の突合結果）
- `session_v2_group_summary.csv`（分類別 `trade_count/total_pnl/average_pnl/win_rate`）
- `session_v2_group_summary.md`（Markdown要約、unmatched warning付き）

集計グループ:
- `session_label`
- `hour_utc`
- `day_of_week`
- `session_risk_flag`
- `is_low_liquidity_hour`
- `is_tokyo_session`
- `is_london_session`
- `is_new_york_session`
- `is_london_ny_overlap`
- `session_policy`

注意:
- これは既存ログの後処理診断であり、収益性確認ではない。
- Session v2 は `diagnostic_only` であり entry を止めていない。
- `session_label` は DST未補正の UTC固定近似ラベルである。
- 実filter化判断ではない。

### 6.87 Phase 5 SR v0.2 diagnostic_only 最小実装メモ（2026-05-03）
- `PipelineAdapter` に `sr_v2` の `diagnostic_only` 最小実装を追加した。
- `sr_v2_enabled=True` でも `diagnostic_only` では entry を止めない（`entry_signal` / `trade_ok` を変更しない）。
- decision trace / decision_logs に SR v0.2 列（`nearest_resistance` / `nearest_support` / 距離pips / `sr_proximity_flag` / `sr_reason` 等）を出力する。
- 初期SR定義は `fixed window rolling high/low` を採用したが、本採用扱いではない。
- SR計算では current bar と未来barを使わず、entry判定時点より前の履歴のみを使用する。
- `sr_v2_window_bars` 本数不足時は `sr_data_valid_flag=False` とする。
- `sr_reason` は `diagnostic_only:no_entry_filter` を含め、実filter化ではないことを明示する。
- `run_backtest_exit_experiment.py` は SR v2 CLI/metadata 配線を追加し、設定値を `run_metadata.json` / `backtest_summary.csv` に出力できるようにした。

注意:
- これは診断列追加であり、SRを本体entry制御として有効化していない。
- 収益性確認ではない。

### 6.88 SR v2 diagnostic trade analysis 後処理
目的:
- SR v2 `diagnostic_only` の既存entry/tradeを、`sr_proximity_flag` 別・`sr_block_side` 別に損益分解する。
- 実filter化前に、`sr_proximity_flag=True` 側が悪いかどうかを後処理で確認する。

対象:
- 既存 `decision_logs.csv` と `trade_logs.csv` の突合・集計のみ。
- backtest再実行・売買ロジック変更・SR filter有効化・閾値変更は行わない。

突合方針:
- `trade_logs.entry_time` を基準に `decision_logs.timestamp` とUTC正規化後に突合する。
- 時刻正規化は `pandas.to_datetime(..., utc=True)` を使用する。
- `decision_logs` に同一timestampが複数ある場合は最後の行を採用する。
- `trade_logs.pnl` を損益計算に使用する。

付与列（trade単位）:
- `sr_v2_enabled`
- `sr_policy`
- `sr_window_bars`
- `nearest_resistance`
- `nearest_support`
- `nearest_resistance_distance_pips`
- `nearest_support_distance_pips`
- `sr_proximity_flag`
- `sr_block_side`
- `sr_reason`
- `sr_data_valid_flag`
- `sr_counterfactual_group`

出力:
- `sr_v2_trade_analysis.csv`（trade単位の突合結果）
- `sr_v2_group_summary.csv`（分類別 `trade_count/total_pnl/average_pnl/win_rate`）
- `sr_v2_group_summary.md`（Markdown要約、unmatched warning付き）

集計グループ:
- `sr_proximity_flag`
- `sr_block_side`
- `sr_data_valid_flag`
- `sr_counterfactual_group`
- `sr_policy`
- `sr_window_bars`

注意:
- これは既存ログの後処理診断であり、収益性確認ではない。
- SR v2 は `diagnostic_only` であり entry を止めていない。
- 実filter化判断ではない。

### 6.89 SR v2 diagnostic trade analysis result（OOS-2 2024-11 representative run）
対象run:
- `run_id: oos2_202411_sr_v2_diag_trailing_matched`
- `trade_count=64`
- `total_pnl=0.29010000000004366`

matched run確認:
- 条件を揃えた run では `trade_count=64` / `total_pnl=0.2901` に戻った。
- SR v2 `diagnostic_only` は entry を変更していない。
- entry 64件すべてで `sr_data_valid_flag=True` を確認した。

`sr_proximity_flag` 別集計:

| group | trade_count | total_pnl | average_pnl | win_rate |
| --- | ---: | ---: | ---: | ---: |
| false | 47 | 0.1616 | 0.0034382979 | 0.851064 |
| true | 17 | 0.1285 | 0.0075588235 | 0.823529 |

`sr_block_side` 別集計:

| group | trade_count | total_pnl | average_pnl | win_rate |
| --- | ---: | ---: | ---: | ---: |
| none | 47 | 0.1616 | 0.0034382979 | 0.851064 |
| resistance | 12 | 0.0371 | 0.0030916667 | 0.750000 |
| support | 5 | 0.0914 | 0.0182800000 | 1.000000 |

`sr_counterfactual_group` 別集計:

| group | trade_count | total_pnl | average_pnl | win_rate |
| --- | ---: | ---: | ---: | ---: |
| sr_long_near_resistance | 12 | 0.0371 | 0.0030916667 | 0.750000 |
| sr_long_not_near_resistance | 25 | 0.0789 | 0.0031560000 | 0.880000 |
| sr_short_near_support | 5 | 0.0914 | 0.0182800000 | 1.000000 |
| sr_short_not_near_support | 22 | 0.0827 | 0.0037590909 | 0.818182 |

解釈（構造診断）:
- `sr_proximity_flag=True` 側は悪化群ではなかった。
- `true` 側は勝率はやや低いが `average_pnl` は `false` 側より高かった。
- `resistance` 近接は勝率がやや低いが `total_pnl` はプラスであり、即除外不可。
- `support` 近接は代表月では利益源となっており、除外不可。
- 現在の `rolling high/low` SR は反発型SRというより breakout 近接ラベルとして機能している可能性がある。

現時点判断:
- SR v2 `rolling high/low` は現時点では実filter化しない。
- SR v2 は `diagnostic/explanation layer` として継続する。
- 代表月単独で本採用・棄却判断はしない。
- `window=48` / `near_threshold_pips=10.0` を結果に合わせて調整しない。

注意:
- これは収益性確認ではなく、代表月における構造診断である。

### 6.90 Phase 5 SR Concept Split: rolling high/low SR vs reaction SR
目的:
- Phase 5 SR v0.2 diagnostic結果を受けて、SR概念を `rolling high/low` 型と `reaction SR` 型に分離して扱う。
- 両者を混同せず、診断結果の解釈と次設計の責務を明確化する。

`rolling high/low SR` の位置づけ:
- 定義は fixed window の直近高値/安値（`max(high[-N:])` / `min(low[-N:])`）。
- 性質としては「breakout近接」「直近高値安値への接近」「余地診断」に近い。
- 代表月診断では `sr_proximity_flag=True` 側は悪化群ではなく、単純な危険filterの根拠は得られていない。
- 現時点では `diagnostic/explanation layer` として継続し、実filter化は保留する。

`reaction SR` の候補定義（将来候補）:
- 複数回反発した価格帯（price zone）を対象にする。
- 例:
  - swing high/low cluster
  - H1/H4 recent high/low
  - price touch count
  - rejection candle / wick
- 人間の裁量でいう「壁・支え」に近い概念として別枠で扱う。

分離方針:
- `rolling high/low SR` と `reaction SR` を同一概念として扱わない。
- `rolling high/low SR` の結果だけで「SRは使えない」と結論づけない。
- `reaction SR` は Phase 5 後続候補として保持し、現時点では未実装。

進行判断（未決）:
- Phase 6 Session/Time filter へ先に進むか、
- `reaction SR` 設計を先に行うかは未決とする。

注意:
- これは設計整理であり、backtest再実行・売買ロジック変更・SR filter有効化・閾値変更を含まない。

### 6.91 Phase 6 Session/Time Filter v0.2 Design（実装前）
目的:
- 時間帯ごとの成績・リスク差を診断する。
- 初期段階では entry を止めず、`diagnostic_only` として session/time label を `decision_logs` に出力する。
- 実filter化は分類別損益確認後に判断する。

対象時間帯候補:
- Tokyo session
- London session
- New York session
- London/New York overlap
- low liquidity hours
- market open / close 周辺
- Friday late / Monday early
- day_of_week
- hour_utc

初期方針:
- UTC基準で扱う。
- JST変換は表示・分析補助として扱い、内部基準はUTCとする。
- 最初は `diagnostic_only` とする。
- `entry_signal` / `trade_ok` は変更しない。

Config候補:
- `session_v2_enabled: bool = False`
- `session_v2_policy: diagnostic_only`
- `session_v2_timezone: str = "UTC"`
- `session_v2_use_day_of_week: bool = True`
- `session_v2_use_hour_bucket: bool = True`

出力列候補:
- `session_v2_enabled`
- `session_policy`
- `hour_utc`
- `day_of_week`
- `session_label`
- `is_tokyo_session`
- `is_london_session`
- `is_new_york_session`
- `is_london_ny_overlap`
- `is_low_liquidity_hour`
- `session_risk_flag`
- `session_reason`
- `session_data_valid_flag`

`session_label` 初期候補:
- `tokyo`
- `london`
- `new_york`
- `london_ny_overlap`
- `off_session`
- `low_liquidity`
- `unknown`

diagnostic_only方針:
- `entry_signal` / `trade_ok` は変更しない。
- `session_risk_flag` は仮想的な注意ラベルとして扱う。
- `session_reason` には `diagnostic_only:no_entry_filter` を含める。
- 実filter化は後続判断とする。

評価指標:
- session別 `trade_count`
- session別 `total_pnl`
- `average_pnl`
- `win_rate`
- `day_of_week` 別成績
- `hour_utc` 別成績
- `low_liquidity` 側の成績
- `avoided_loss / missed_profit` counterfactual

Go/No-Go:
- 代表月だけでfilter化しない。
- 特定時間帯が明確に悪い場合のみ複数月診断候補とする。
- 良い時間帯を結果に合わせて過剰選別しない。
- 複数月確認前に本体filter化しない。

未解決事項:
- session時刻境界の定義。
- DSTをどう扱うか。
- JST表示を入れるか。
- low liquidity hour の初期定義。
- 指標/event haltとの責務境界。

注意:
- これは実装前設計であり、backtest再実行・Session filter実装・売買ロジック変更・閾値変更を含まない。

### 6.92 Phase 6 Session v0.2 I/O Contract & Diagnostic Policy（実装前固定）
目的:
- Phase 6 Session/Time filter v0.2 の実装前段階として、I/O契約と診断ポリシーを固定する。
- 今回は設計契約の明文化に限定し、backtest再実行・Session filter実装・PipelineAdapter変更・売買ロジック変更・閾値変更は行わない。

重要前提:
- 実 broker / OANDA API / 実注文送信は未実装。
- 収益性確認済みではない。
- Session filterは本採用ではない。
- SR v2 rolling high/low は diagnostic/explanation layer 継続、reaction SR は後続候補。
- HTF v2 も diagnostic/explanation layer として継続中。

内部時刻基準:
- 内部処理はUTC固定。
- JSTは表示・分析補助として扱う。
- `decision_logs` には `hour_utc` / `day_of_week` を必ず出す。
- JST列を出す場合は optional とし、初期実装では必須にしない。

DST方針:
- 初期v0.2では London / New York の厳密DST補正は行わない。
- `session_label` は UTC固定の近似ラベルとして扱う。
- DST厳密対応は後続候補。
- `session_label` を本採用filterとして使わない限り、初期は近似でよい。
- 文書上で「UTC固定近似」であることを明記する。

初期session境界候補（UTC固定近似）:
- `tokyo`: `00:00-09:00 UTC`
- `london`: `08:00-17:00 UTC`
- `new_york`: `13:00-22:00 UTC`
- `london_ny_overlap`: `13:00-17:00 UTC`
- `low_liquidity`: `22:00-00:00 UTC` and weekend/market thin periods candidate
- `off_session`: 上記以外
- これは初期診断ラベルであり、本採用時刻ではない。

`day_of_week` 方針:
- UTC基準で Monday〜Friday を記録する。
- weekend は通常データが少ない/ない可能性がある。
- Friday late / Monday early は後続候補として保持する。

Config候補:
- `session_v2_enabled: bool = False`
- `session_v2_policy: str = "diagnostic_only"`
- `session_v2_timezone: str = "UTC"`
- `session_v2_use_day_of_week: bool = True`
- `session_v2_use_hour_bucket: bool = True`
- `session_v2_use_dst_adjustment: bool = False`

出力列候補:
- `session_v2_enabled`
- `session_policy`
- `hour_utc`
- `day_of_week`
- `session_label`
- `is_tokyo_session`
- `is_london_session`
- `is_new_york_session`
- `is_london_ny_overlap`
- `is_low_liquidity_hour`
- `session_risk_flag`
- `session_reason`
- `session_data_valid_flag`

diagnostic_only方針:
- `entry_signal` / `trade_ok` は変更しない。
- `session_risk_flag` は仮想注意ラベルとする。
- `session_reason` には `diagnostic_only:no_entry_filter` を含める。
- 実filter化は後続判断とする。

評価指標:
- `session_label` 別 `trade_count`
- `session_label` 別 `total_pnl`
- `average_pnl`
- `win_rate`
- `hour_utc` 別成績
- `day_of_week` 別成績
- `low_liquidity` 側の成績
- `avoided_loss / missed_profit` counterfactual

Go/No-Go:
- 代表月だけでfilter化しない。
- 明確に悪い時間帯のみ複数月診断候補とする。
- 良い時間帯だけを結果に合わせて過剰選別しない。
- 複数月確認前に本体filter化しない。
- DST未対応のまま本採用filterにしない。

未解決事項:
- session境界時刻の最終定義。
- DST厳密対応の導入タイミング。
- JST表示列を入れるか。
- low liquidity hour の厳密定義。
- event haltとの責務境界。
- broker時間/OANDA時間との整合。

注意:
- 本節は I/O 契約固定であり、実装・本体統合・収益性判断を含まない。

### 6.113 Phase 9 CSV replay pipeline dry-run minimal completion criteria（2026-05-09）
目的:
- Phase 9 を「minimal completion reached」として区切るため、完了条件・非対応範囲・次段候補を固定する。
- これは dry-run / 構造検証 / ログ整合確認の区切りであり、実運用判定ではない。

重要前提:
- 実 broker / OANDA API / 実注文送信は対象外。
- 収益性確認済みを意味しない。
- `pass` は収益性や実運用品質を意味しない。

Minimal completion 条件:
1. pipeline dry-run が representative 期間で実行できる。
2. `near_live_*` outputs が生成される。
3. summarizer が `dry_run_period_summary.*` を生成できる。
4. `decision_log_count == replay_bar_count` を確認できる。
5. `real_order_sent_count == 0` を確認できる。
6. `no_real_order_integrity_violation_count == 0` を確認できる。
7. weekday representative run で `dry_run_health_status=pass` を確認済み。
8. weekend expected gap 単独（`expected_weekend_gap_count>0` かつ `ordinary_missing_bar_gap_count=0` / `unknown_gap_count=0`）で過剰 warn/fail にならないことを確認済み。
9. `warn` は調査候補であり、必ずしも即failではない。
10. `fail` は実注文送信検出やログ整合性破綻などの重大条件として扱う。

Phase 9 完了後に残す候補:
- `pipeline_adapter_error` の error type別集計。
- dry-run artifact の保存・レビュー運用の詳細化。
- OANDA/API接続（後続）。
- HTF/SR/Session/RiskStop/Halt の filter化（後続）。

### 6.114 Risk/Stop v0 と fixed_sl_tp baseline の関係（docs整理）
目的:
- Risk/Stop v0 の責務境界を docs 上で固定し、実装前の曖昧さを減らす。
- 収益性評価ではなく、構造検証のための境界整理として扱う。

固定方針:
- `fixed_sl_tp` は BacktestRunner 本体既定 baseline として当面維持する。
- Risk/Stop v0 は baseline を壊さず、`trade_ok` / `stop_loss` / `take_profit` / `risk_reason` / `filter_reason` の責務境界を明確化する。
- `max_holding_bars` は Backtest 側 exit 条件として維持し、Risk/Stop v0 で exit policy 採用判断は行わない。
- `simple_trailing_after_1R` などは本採用ではなく、experimental exit candidate のまま扱う。
- experimental exit candidate と Risk/Stop v0 を混同しない。

今回の対象外:
- `lot sizing` 本体実装と詳細仕様固定
- `account_balance` / `risk_per_trade` 連動の建玉計算
- 実注文、live OANDA/API 接続、収益性確定判断

### 6.115 Risk/Stop v0 実装前の最終受け入れ基準（docs固定）
目的:
- Risk/Stop v0 実装着手前に、`lot` 契約、命名、責務境界、完了条件を固定する。

固定方針:
- `trade_ok=true` の場合、`lot` / `stop_loss` / `take_profit` は有効値でなければならない。
- `lot` が未算出・空・`<=0`・不正値なら `trade_ok=true` を許容しない。
- Risk/Stop v0 実装時は `PositionSizer placeholder`（暫定固定lotまたは設定値lot）を許容する。
- placeholder は `lot sizing` 本体実装を意味しない。
- `max_holding_bars` は Backtest / Exit 側の時間退出条件として扱い、Risk/Stop v0 の主責務にしない。
- `fixed_sl_tp` baseline 維持方針を壊さない。
- experimental exit candidate（例: `simple_trailing_after_1R`）と混同しない。

実装フェーズへ進む場合の完了条件（今回未実装）:
- StopLossPlanner / TakeProfitPlanner / PositionSizer placeholder / RiskAssembler の最小実装。
- `trade_ok=true` 時に `lot` / `stop_loss` / `take_profit` が有効値。
- `trade_ok=false` 時に `risk_reason` または `filter_reason` が空でない。
- long/short で SL/TP 方向が正しい。
- `lot` 不正時は `trade_ok=false`。
- unit test を追加し、関連 `pytest` が通る。
- BacktestRunner / PipelineAdapter / Signal / Execution の本体挙動を不必要に変更しない。

### 6.116 Risk/Stop v0 review follow-up（過去の暫定固定値経路）
目的:
- /review 指摘を受けて、当時の Risk/Stop v0 契約整合を小修正で揃える。
- BacktestRunner / PipelineAdapter の本体売買挙動は変えない。

当時の固定方針:
- 当時の `PipelineAdapter` は planner chain（`PositionSizer` / `StopLossPlanner` / `TakeProfitPlanner`）を本体経路で直列接続しなかった。
- `PipelineAdapterConfig` の `fixed_lot` / `stop_loss_distance` / `take_profit_distance` から生成した値を `RiskAssembler` に渡す暫定固定値経路を維持していた。
- この暫定経路は Risk/Stop v0 契約検証と pipeline 安定性維持のための措置だった。
- planner chain は unit/integration で契約確認し、本体接続は後続判断としていた。

注意:
- 上記は過去の暫定状態であり、現在の本体経路ではない。

### 6.117 PipelineAdapter planner chain 正式接続の実装後現況
目的:
- planner chain 正式接続の実装後状態を記録し、採用確定前の docs/ops 整合段階を明示する。

現況:
- `PipelineAdapter` は `PositionSizer` / `StopLossPlanner` / `TakeProfitPlanner` / `RiskAssembler` の planner chain 経路へ正式接続済み。
- 接続は `fixed_lot` / fixed SL distance / fixed TP distance baseline と同値維持を目的としている。
- `PositionSizer` は placeholder のまま維持し、`account_balance` は placeholder valid 判定を通す fixed input（`placeholder_account_balance`）を使う。
- `entry_price_candidate` は `current_bar.close` を使用する。
- これは lot sizing 本体、収益性確認、実運用品質、実注文準備を意味しない。

採用確定前の段階:
- 現在は docs/ops 整合修正と cross-file review を行う段階であり、採用確定前である。

非対応範囲（維持）:
- lot sizing 本体実装。
- `account_balance` 連動計算式。
- `risk_per_trade`。
- broker lot 制約厳密化。
- OANDA/API 接続。
- 実注文、broker 連携。
- Session/SR/HTF filter化。
- experimental exit 本採用。
- 株式拡張。
- 収益性評価。

### 6.118 dry-run summary reason category 適用方針（実装前）
目的:
- Phase 9 dry-run health 検証の文脈で、reason語彙を category 軸で追跡できるようにする。
- 収益性評価ではなく、構造検証・診断補助として扱う。

判断:
- Aを採用する。
- `summarize_csv_replay_dry_run.py` に reason category 集計を派生メトリクスとして追加する（最小実装）。

理由:
- dry-run summary は health/status/warnings 中心であり、reason集計を補助追加しても責務を壊しにくい。
- Evaluator本体より影響範囲が小さく、段階導入しやすい。
- `near_live_decision_logs.csv` の `risk_reason` / `filter_reason` を構造的に追跡できる。

実装範囲（次フェーズ）:
- 対象スクリプト:
  - `scripts/summarize_csv_replay_dry_run.py`
- 非対象スクリプト:
  - `scripts/run_csv_replay_pipeline_dry_run.py`（ログ生成形式は変更しない）

対象列:
- category 集計対象:
  - `risk_reason`
  - `filter_reason`
- 集計対象外:
  - `decision_reason`（自由文）
  - `signal_reason`（自由文）

互換方針:
- 既存 `near_live_summary.csv/.md` と `dry_run_period_summary.csv/.md` の既存項目は削除・改名しない。
- 既存列置換なし、派生メトリクス追加のみ。
- `None` / 空白 / 欠損は unknown 扱い。
- `"none"` category の誤集計を防止する。
- 共通helper化は急がず、`normalize_reason_categories()` 利用に留める。

未解決点:
- 行単位派生列CSVの要否。
- `src/evaluator/filter_analyzer.py` の category基準化判断。
- canonical出力への段階移行判断。

### 6.119 Evaluator `FilterAnalyzer` category基準化方針（実装前）
目的:
- scripts側で先行した reason category 集計と、Evaluator本体の集計責務を整合させる。
- 収益性評価ではなく、集計軸の互換と段階導入方針を固定する。

判断:
- Aを採用する。
- 既存 `FilterAnalyzer.analyze()` は維持し、category分析は別メソッド追加で進める（例: `analyze_by_category()`）。

理由:
- 既存完全一致bucket依存の呼び出し・テストを壊しにくい。
- 完全一致分析とcategory分析を併存でき、移行判断を後段に分離できる。
- scripts側の category 集計結果と Evaluator側の新集計を比較しやすい。

集計方針（実装時の固定候補）:
- `normalize_reason_categories()` を利用する。
- `|` 連結reasonは複数categoryへそれぞれカウントする。
- `None` / 空白 / 欠損は unknown 扱いとする。
- `"None"` -> `"none"` の誤category化を防止する。

非対象:
- 既存 `analyze()` のcategory置換。
- 売買ロジック、`trade_ok`、PipelineAdapter挙動の変更。

未解決点:
- 行単位派生列CSVの要否。
- canonical出力への段階移行時期。

### 6.120 Lot Sizing v1 独立フェーズ判断（2026-05-15）
目的:
- lot sizing本体を Risk/Stop v0 と切り分け、実装順序と接続順序を固定する。
- 今回は docs/ops 判断固定のみであり、コード変更・テスト変更は行わない。

判断:
- `Lot Sizing v1` を独立フェーズとして採用する。
- 初期実装は isolated calculator（unit test完結）に限定する。
- `PipelineAdapter` / backtest main path への接続は後続判断とする。
- `fixed_lot` baseline は維持する。

独立させる理由:
- 現行 `PositionSizer` は placeholder であり、本線接続済み経路へ即時投入すると影響範囲が広い。
- lot sizing本体は式・設定・invalid・rounding/clamp の契約確定が先で、接続は後段のほうが差分管理しやすい。
- Pipeline結果（trade_count/PnL）を即時変えずに、unit test中心で品質を固められる。

初期スコープ（Lot Sizing v1）:
- risk-based lot calculation 式
- config項目
- I/O契約
- invalid条件
- rounding/clamp方針
- unit test方針
- fixed_lot baseline との境界
- PipelineAdapter接続の Go/No-Go 条件

非対応範囲:
- PipelineAdapter本線接続
- backtest PnL変更
- 実運用lot制約
- OANDA/API接続
- 実注文
- broker別制約厳密化
- 収益性評価
- 売買ロジック変更

### 6.121 Lot Sizing v1 実装前 contract 固定（2026-05-15）
目的:
- `Lot Sizing v1` isolated calculator 実装前に、formula/config/invalid/rounding/clamp を固定する。
- 今回は docs/ops 固定のみで、`PipelineAdapter` / `BacktestRunner` / `PositionSizer` 本線挙動は変更しない。

formula（固定）:
- `lot = account_balance * risk_per_trade / (stop_loss_distance_pips * pip_value_per_lot)`

入力（固定）:
- `account_balance`
- `risk_per_trade`
- `stop_loss_distance_pips`
- `pip_value_per_lot`
- `lot_step`
- `min_lot`
- `max_lot`
- `rounding_mode`

出力（固定）:
- `lot`
- `raw_lot`
- `rounded_lot`
- `clamped_flag`
- `size_reason`

rounding方針（固定）:
- 初期は `floor` 固定とする。
- 理由は指定リスクを超えないため。
- `round` / `ceil` は初期非対応。

clamp方針（固定）:
- `raw_lot` / `rounded_lot` が `max_lot` を超える場合は `max_lot` に clamp 可。
- `rounded_lot < min_lot` の場合は `min_lot` へ引き上げず invalid とする。
- 理由は `min_lot` 引き上げで指定リスクを超える可能性があるため。

invalid条件（固定）:
- `account_balance <= 0`
- `risk_per_trade <= 0`
- `risk_per_trade >= 1`
- `stop_loss_distance_pips <= 0`
- `pip_value_per_lot <= 0`
- `lot_step <= 0`
- `min_lot <= 0`
- `max_lot <= 0`
- `min_lot > max_lot`
- bool / NaN / inf
- `rounded_lot < min_lot`

非対応範囲（固定）:
- `PipelineAdapter` 接続
- `PositionSizer` 置換
- backtest PnL 変更
- trade_count 変更
- OANDA/API
- broker別厳密制約
- 通貨ペア別pip価値自動計算
- 収益性評価
- 売買ロジック変更

接続判断の扱い:
- `Lot Sizing v1` 初期完了条件は isolated calculator + unit test のみで満たす。
- `PipelineAdapter` / backtest main path 接続は後続 Go/No-Go 判断で扱う。

### 6.122 Lot Sizing v1 Pipeline/PositionSizer 本線接続判断（2026-05-15）
目的:
- `Lot Sizing v1` calculator を `PipelineAdapter` / `PositionSizer` 本線へ接続するかを判断し、次の安全な進め方を固定する。
- 今回は docs/ops 判断固定のみで、実装コード・テストは変更しない。

最終判断:
- 本線への即時接続は **No-Go / Hold** とする。
- 次フェーズは shadow mode / comparison-only 設計へ進む。

No-Go 理由:
- `fixed_lot` baseline を破壊しうる。
- PnL / trade_count / risk logs の解釈が変化する。
- `pip_value_per_lot` が手入力前提で、前提差異の影響が大きい。
- broker別 lot 制約厳密化、OANDA/API、実運用要件は未対応。
- 収益性評価へ論点が広がり、段階分離が崩れる。

shadow mode / comparison-only 方針:
- 本線は `fixed_lot` を維持する。
- risk-based lot は診断値として算出・比較ログ出力する候補に留める。
- 比較ログ候補:
  - `fixed_lot`
  - `risk_based_raw_lot`
  - `risk_based_rounded_lot`
  - `risk_based_effective_lot`
  - `lot_sizing_reason`
  - `clamped_flag`
  - `lot_size_diff`
- 非対応（shadow modeでも実施しない）:
  - PnL反映
  - trade_count変更
  - entry/exit判断変更
  - broker制約厳密化
  - OANDA/API接続
  - 実注文

Go 条件（接続判断を進める前提）:
1. risk-based lot が fixed_lot 比較ログで安定している。
2. invalid / clamp / below_min をログで把握できる。
3. `pip_value_per_lot` 前提が明確である。
4. PnL 非反映の診断モードが用意できる。
5. representative fixture で既存 trade_count / PnL が不変である。

No-Go 条件（継続）:
- 本線lot置換なしでは検証できない前提になる。
- PnL / trade_count が変わる。
- broker/OANDA仕様が必要になる。
- pip_value 自動計算が必須になる。
- 収益性評価へ論点が拡散する。

### 6.123 Lot Sizing v1 shadow mode / comparison-only 設計方針（2026-05-15）
目的:
- `fixed_lot` 本線を維持したまま、risk-based lot を診断値として比較し、接続判断の材料を作る。
- 収益性評価ではなく、構造診断と前提差分の可視化を目的とする。

固定方針:
- 本線lotは `fixed_lot` のまま維持する。
- risk-based lot は diagnostic value として算出・比較する候補に留める。
- PnL / trade_count / entry / exit / `trade_ok` 判定には影響させない。

実装候補の判断:
- A: `PipelineAdapter` 内 shadow calculation は **現時点で採用しない**（後続候補）。
- B: backtest後 analysis script 拡張は採用候補。
- C: 専用 offline comparison script は最優先候補。

推奨順序:
1. C（専用 offline script）
2. B（analysis script 拡張）
3. A（PipelineAdapter 内 shadow 計算）

推奨理由:
- C/B は既存挙動非破壊で比較可能。
- `account_balance` / `pip_value_per_lot` / `risk_per_trade` 供給経路が未固定でも進めやすい。
- `PipelineAdapter` の責務肥大化と本線仕様誤認リスクを避けられる。

診断値候補:
- `fixed_lot`
- `risk_based_raw_lot`
- `risk_based_rounded_lot`
- `risk_based_effective_lot`
- `risk_based_lot_sizing_reason`
- `risk_based_clamped_flag`
- `lot_size_diff`
- `lot_size_ratio`
- `risk_lot_valid_flag`

shadow mode の非対応範囲:
- PnL反映
- trade_count変更
- entry/exit判断変更
- `RiskAssembler.trade_ok` 判定変更
- Execution / order path への受け渡し
- broker制約厳密化
- OANDA/API接続
- 実注文
