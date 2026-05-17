# Worklog: HTF v2 Diagnostic Trade Analysis Result

## 実行結果
- **Run 名**: oos2_20241101_1201_htf_v2_diag_off_trailing_warmup_semantics
- **取引数**: 64
- **総損益 (total_pnl)**: 0.2901

## 集計結果
### h4_bias
| Bias     | Trade Count | Total PnL | Average PnL | Win Rate |
|----------|-------------|-----------|-------------|----------|
| Down     | 14          | 0.0262    | 0.00187     | 85.71%   |
| Neutral  | 35          | 0.2167    | 0.00619     | 80.00%   |
| Up       | 15          | 0.0472    | 0.00315     | 93.33%   |

### h1_context
| Context               | Trade Count | Total PnL | Average PnL | Win Rate |
|-----------------------|-------------|-----------|-------------|----------|
| Aligned Down          | 6           | 0.0224    | 0.00373     | 100.00%  |
| Aligned Up            | 14          | 0.0383    | 0.00273     | 92.86%   |
| Pullback Against H4   | 5           | 0.0126    | 0.00252     | 100.00%  |
| Range or Neutral      | 25          | 0.1676    | 0.00670     | 84.00%   |
| Unknown               | 14          | 0.0492    | 0.00351     | 64.29%   |

### Policy Diagnostic
| Policy                          | Trade Count | Total PnL | Average PnL | Win Rate |
|---------------------------------|-------------|-----------|-------------|----------|
| Aligned Only Allowed = False    | 53          | 0.2532    | 0.00478     | 81.13%   |
| Aligned Only Allowed = True     | 11          | 0.0369    | 0.00335     | 100.00%  |
| Pullback Permissive Allowed = False | 52      | 0.2530    | 0.00487     | 80.77%   |
| Pullback Permissive Allowed = True  | 12      | 0.0371    | 0.00309     | 100.00%  |

## 解釈と判断
1. **Aligned Only / Pullback Permissive の実 filter 化を行わない理由**:
   - Aligned Only Allowed = True の取引数は 11 件、総損益は 0.0369 と少なく、実 filter 化すると取引数と総利益が大幅に減少する可能性がある。
   - Pullback Permissive Allowed = True も同様に 12 件のみであり、Aligned Only からほぼ増加しない。

2. **Neutral / Range or Neutral / Context Uncertain の解釈**:
   - h4_bias = Neutral と h1_context = Range or Neutral が代表月で大きな利益源となっている。
   - Context Uncertain = True 側も総損益が 0.2168 と大きく、機械的に除外する根拠はない。

3. **Hard Conflict の扱い**:
   - 平均損益が低く監視価値はあるが、総損益はプラスであり、即除外は不可。

## 次タスク
- HTF v2 を diagnostic/explanation layer として継続する方針を整理。
- 複数月で同様の分類別損益を確認するか判断。
- Phase 5 Support/Resistance へ進むか判断。
- Aligned Only / Pullback Permissive 実 filter 化は保留。