# 2026-05-02 M5 Backtest Slice from DAT

## Summary
- Added `scripts/make_m5_backtest_slice_from_dat.py`.
- Adopted `DAT_MT_USDJPY_M1_20xx.csv` (headerless 7-column DAT) as the source candidate for this task.
- Generated a short M5 slice CSV for initial backtest/structure checks.
- Confirmed `PriceDataLoader.load_from_csv(..., timeframe="M5")` can read the generated file.

## Rationale
- Based on `data/private/data_audit/usdjpy_m1_candidates_summary.*`, yearly DAT CSV candidates were the most stable M1 source for this phase.
- `pkl` remains non-authoritative cache by policy.
- `parquet` is not selected in this step and can be used as comparison later if needed.

## Implementation
- New script: `scripts/make_m5_backtest_slice_from_dat.py`
- Input format:
  - headerless columns: `date,time,open,high,low,close,volume`
  - timestamp parsed from `date + time` as UTC.
- Range filter:
  - `start <= timestamp < end`
- M1 -> M5 aggregation:
  - `open`: first
  - `high`: max
  - `low`: min
  - `close`: last
  - `volume`: sum
  - `spread`: fixed `--spread-pips` (default `0.2`)
  - last incomplete bucket dropped when final bucket has less than 5 source M1 rows.
- Output schema:
  - `timestamp,open,high,low,close,spread,volume`
  - compatible with `src/data/price_loader.py`

## Commands Run
```powershell
$env:PYTHONPATH='.'
python scripts/make_m5_backtest_slice_from_dat.py --input data/raw/dukascopy/USDJPY/M1/dat_csv_candidates/DAT_MT_USDJPY_M1_2024.csv --output data/private/backtest_slices/USDJPY_M5_2024-01-02_2024-01-09.csv --start 2024-01-02 --end 2024-01-09 --spread-pips 0.2
```

```powershell
Get-Content data/private/backtest_slices/USDJPY_M5_2024-01-02_2024-01-09.csv -TotalCount 6
```

```powershell
$env:PYTHONPATH='.'
@'
from src.data.price_loader import PriceDataLoader
p='data/private/backtest_slices/USDJPY_M5_2024-01-02_2024-01-09.csv'
rows=PriceDataLoader.load_from_csv(p,timeframe='M5')
print('bar_count',len(rows))
print('start_time',rows[0].timestamp.isoformat())
print('end_time',rows[-1].timestamp.isoformat())
invalid=sum(1 for r in rows if (r.high < max(r.open,r.close)) or (r.low > min(r.open,r.close)) or (r.high < r.low))
print('invalid_ohlc_count',invalid)
'@ | python -
```

## Verification Result
- Generated CSV:
  - `data/private/backtest_slices/USDJPY_M5_2024-01-02_2024-01-09.csv`
- Loader read:
  - `bar_count = 1439`
  - `start_time = 2024-01-02T00:00:00+00:00`
  - `end_time = 2024-01-08T23:55:00+00:00`
  - `invalid_ohlc_count = 0`

## Note on Spread Fallback
- `spread=0.2 pips` in this output is a fixed fallback for initial structure checks and research backtests only.
- It is not suitable for operation-like / real-trading approximation validation as per `docs/11_data_source_policy.md`.

