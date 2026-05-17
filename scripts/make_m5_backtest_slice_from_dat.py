#!/usr/bin/env python
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import pandas as pd

DAT_COLUMNS = ["date", "time", "open", "high", "low", "close", "volume"]
OUTPUT_COLUMNS = ["timestamp", "open", "high", "low", "close", "spread", "volume"]
CHUNK_SIZE = 200_000


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build M5 PriceDataLoader-compatible CSV from DAT_MT_USDJPY_M1_20xx.csv "
            "(headerless 7-column format)."
        )
    )
    parser.add_argument("--input", required=True, help="Path to DAT yearly CSV.")
    parser.add_argument("--output", required=True, help="Path to output M5 CSV.")
    parser.add_argument("--start", required=True, help="UTC inclusive start. Example: 2024-01-02")
    parser.add_argument("--end", required=True, help="UTC exclusive end. Example: 2024-01-09")
    parser.add_argument("--spread-pips", type=float, default=0.2, help="Fixed spread fallback in pips.")
    return parser.parse_args()


def parse_utc_bound(value: str) -> datetime:
    raw = value.strip()
    if "T" not in raw:
        raw = raw + "T00:00:00+00:00"
    elif raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    dt = datetime.fromisoformat(raw)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def load_dat_slice(path: Path, start: datetime, end: datetime) -> pd.DataFrame:
    chunks: list[pd.DataFrame] = []
    usecols: Iterable[str] = DAT_COLUMNS
    for chunk in pd.read_csv(
        path,
        header=None,
        names=DAT_COLUMNS,
        usecols=usecols,
        chunksize=CHUNK_SIZE,
        low_memory=True,
    ):
        ts = pd.to_datetime(
            chunk["date"].astype(str).str.strip() + " " + chunk["time"].astype(str).str.strip(),
            format="%Y.%m.%d %H:%M",
            utc=True,
            errors="coerce",
        )
        valid = ts.notna()
        if not valid.any():
            continue
        chunk = chunk.loc[valid].copy()
        chunk["timestamp"] = ts.loc[valid]
        mask = (chunk["timestamp"] >= start) & (chunk["timestamp"] < end)
        if not mask.any():
            continue
        chunk = chunk.loc[mask, ["timestamp", "open", "high", "low", "close", "volume"]]
        for col in ["open", "high", "low", "close", "volume"]:
            chunk[col] = pd.to_numeric(chunk[col], errors="coerce")
        chunk = chunk.dropna(subset=["open", "high", "low", "close", "volume"])
        if not chunk.empty:
            chunks.append(chunk)

    if not chunks:
        raise ValueError("No valid DAT rows found in requested [start, end) range.")

    df = pd.concat(chunks, ignore_index=True)
    return df.sort_values("timestamp").reset_index(drop=True)


def aggregate_to_m5(df_m1: pd.DataFrame, spread_pips: float) -> pd.DataFrame:
    df = df_m1.copy()
    df["bucket"] = df["timestamp"].dt.floor("5min")

    grouped = df.groupby("bucket", sort=True, as_index=False)
    m5 = grouped.agg(
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
        volume=("volume", "sum"),
        row_count=("open", "size"),
    )

    if not m5.empty and int(m5.iloc[-1]["row_count"]) < 5:
        m5 = m5.iloc[:-1].copy()

    m5 = m5.rename(columns={"bucket": "timestamp"})
    m5["spread"] = float(spread_pips)
    m5["timestamp"] = m5["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    return m5[OUTPUT_COLUMNS]


def validate_ohlc(df: pd.DataFrame) -> int:
    invalid = (df["high"] < df[["open", "close"]].max(axis=1)) | (df["low"] > df[["open", "close"]].min(axis=1)) | (
        df["high"] < df["low"]
    )
    return int(invalid.sum())


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    if not input_path.exists():
        raise FileNotFoundError(f"Input not found: {input_path}")

    start = parse_utc_bound(args.start)
    end = parse_utc_bound(args.end)
    if start >= end:
        raise ValueError("--start must be earlier than --end. Range is [start, end).")

    print(f"[info] input={input_path}")
    print(f"[info] output={output_path}")
    print(f"[info] range_utc=[{start.isoformat()}, {end.isoformat()})")
    print(
        "[info] spread fallback for this output is fixed and synthetic. "
        "Use only for structure checks / initial backtests, not operation-like validation."
    )

    m1 = load_dat_slice(input_path, start, end)
    m5 = aggregate_to_m5(m1, spread_pips=args.spread_pips)
    if m5.empty:
        raise ValueError("No M5 bars produced after aggregation.")

    invalid_ohlc = validate_ohlc(m5)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    m5.to_csv(output_path, index=False)

    print(f"[done] m1_rows_in_range={len(m1)}")
    print(f"[done] m5_rows={len(m5)}")
    print(f"[done] ohlc_invalid_count={invalid_ohlc}")
    print(f"[done] wrote={output_path}")
    print(f"[done] columns={OUTPUT_COLUMNS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

