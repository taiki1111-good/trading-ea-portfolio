#!/usr/bin/env python
from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import timezone
from pathlib import Path
from typing import Any

import pandas as pd

try:
    import pyarrow.parquet as pq
except Exception:  # pragma: no cover
    pq = None

BASE_DIR = Path("data/raw/dukascopy/USDJPY/M1")
TARGET_DIRS = [
    BASE_DIR / "parquet",
    BASE_DIR / "dat_csv_candidates",
    BASE_DIR / "pkl_candidates",
]
OUTPUT_DIR = Path("data/private/data_audit")
OUTPUT_CSV = OUTPUT_DIR / "usdjpy_m1_candidates_summary.csv"
OUTPUT_MD = OUTPUT_DIR / "usdjpy_m1_candidates_summary.md"

TIMESTAMP_ALIASES = ["timestamp", "datetime", "date", "time", "utc_time"]
OPEN_ALIASES = ["open", "o", "bidopen"]
HIGH_ALIASES = ["high", "h", "bidhigh"]
LOW_ALIASES = ["low", "l", "bidlow"]
CLOSE_ALIASES = ["close", "c", "price", "bidclose"]
SPREAD_ALIASES = ["spread", "spread_pips"]
VOLUME_ALIASES = ["volume", "tick_volume", "vol"]

PRICE_LOADER_REQUIRED = {"timestamp", "open", "high", "low", "close", "spread", "volume"}
CSV_SEPARATORS = [",", ";", "\t"]
CSV_EXTENSIONS = {".csv", ".txt", ".dat"}
CSV_CHUNK_SIZE = 200_000
PKL_MAX_INSPECT_MB = 200.0
DAT_NO_HEADER_COLUMNS = ["date", "time", "open", "high", "low", "close", "volume"]


@dataclass
class ColumnCandidates:
    timestamp: str | None
    open: str | None
    high: str | None
    low: str | None
    close: str | None
    spread_exists: bool
    volume_exists: bool


def normalize_name(value: str) -> str:
    return value.strip().lower()


def pick_first_column(columns: list[str], aliases: list[str]) -> str | None:
    lowered = {normalize_name(c): c for c in columns}
    for alias in aliases:
        if alias in lowered:
            return lowered[alias]
    return None


def detect_candidates(columns: list[str]) -> ColumnCandidates:
    return ColumnCandidates(
        timestamp=pick_first_column(columns, TIMESTAMP_ALIASES),
        open=pick_first_column(columns, OPEN_ALIASES),
        high=pick_first_column(columns, HIGH_ALIASES),
        low=pick_first_column(columns, LOW_ALIASES),
        close=pick_first_column(columns, CLOSE_ALIASES),
        spread_exists=pick_first_column(columns, SPREAD_ALIASES) is not None,
        volume_exists=pick_first_column(columns, VOLUME_ALIASES) is not None,
    )


def stringify_missing_summary(df: pd.DataFrame) -> str:
    missing = df.isna().sum()
    missing = missing[missing > 0]
    if missing.empty:
        return "{}"
    return "{" + ", ".join(f"{k}:{int(v)}" for k, v in missing.sort_values(ascending=False).items()) + "}"


def parse_timestamps(series: pd.Series) -> tuple[pd.Series | None, str | None]:
    converted = pd.to_datetime(series, utc=True, errors="coerce")
    valid = int(converted.notna().sum())
    total = int(len(converted))
    if total == 0:
        return converted, None
    if valid == 0:
        return None, "timestamp parse failed: all values are NaT"
    if valid < total:
        return converted, f"timestamp parse partial: valid={valid}, invalid={total - valid}"
    return converted, None


def count_invalid_ohlc(df: pd.DataFrame, c: ColumnCandidates) -> int | None:
    if not all([c.open, c.high, c.low, c.close]):
        return None
    try:
        op = pd.to_numeric(df[c.open], errors="coerce")
        hi = pd.to_numeric(df[c.high], errors="coerce")
        lo = pd.to_numeric(df[c.low], errors="coerce")
        cl = pd.to_numeric(df[c.close], errors="coerce")
    except Exception:
        return None

    valid_num = op.notna() & hi.notna() & lo.notna() & cl.notna()
    if not valid_num.any():
        return None

    invalid = valid_num & (
        (hi < pd.concat([op, cl], axis=1).max(axis=1))
        | (lo > pd.concat([op, cl], axis=1).min(axis=1))
        | (hi < lo)
    )
    return int(invalid.sum())


def can_convert_to_price_loader_csv(columns: list[str]) -> bool:
    normalized = {normalize_name(c) for c in columns}
    return PRICE_LOADER_REQUIRED.issubset(normalized)


def recommend(readable: bool, timestamp_ok: bool, ohlc_ok: bool | None, convertible: bool, file_type: str) -> tuple[str, str]:
    if not readable:
        return "reject", "file not readable"
    if file_type == "pkl-non-dataframe":
        return "reject", "pkl object is not DataFrame"
    if not timestamp_ok:
        return "caution", "timestamp conversion issue"
    if ohlc_ok is False:
        return "reject", "invalid OHLC rows detected"
    if convertible:
        return "strong_candidate", "matches price_loader CSV schema"
    return "candidate_with_transform", "requires column mapping/normalization"


def inspect_dataframe(path: Path, df: pd.DataFrame, file_type: str, notes: list[str]) -> dict[str, Any]:
    columns = [str(c) for c in df.columns]
    candidates = detect_candidates(columns)
    timestamp_ok = False
    start_time = ""
    end_time = ""
    duplicate_timestamp_count: int | None = None
    timestamp_monotonic: bool | None = None

    if candidates.timestamp:
        ts, ts_note = parse_timestamps(df[candidates.timestamp])
        if ts_note:
            notes.append(ts_note)
        if ts is not None:
            valid_ts = ts.dropna()
            if not valid_ts.empty:
                timestamp_ok = True
                start_time = valid_ts.min().isoformat()
                end_time = valid_ts.max().isoformat()
                duplicate_timestamp_count = int(valid_ts.duplicated().sum())
                timestamp_monotonic = bool(valid_ts.is_monotonic_increasing)
            else:
                notes.append("timestamp parse result has no valid rows")
        else:
            notes.append("timestamp cannot be converted to UTC")
    else:
        notes.append("timestamp column candidate not found")

    invalid_ohlc_count = count_invalid_ohlc(df, candidates)
    ohlc_ok: bool | None
    if invalid_ohlc_count is None:
        ohlc_ok = None
        notes.append("OHLC validation skipped: required columns missing or non-numeric")
    else:
        ohlc_ok = invalid_ohlc_count == 0

    convertible = can_convert_to_price_loader_csv(columns)
    recommendation, recommendation_reason = recommend(
        readable=True,
        timestamp_ok=timestamp_ok,
        ohlc_ok=ohlc_ok,
        convertible=convertible,
        file_type=file_type,
    )
    notes.append(recommendation_reason)

    return {
        "file_path": str(path),
        "file_name": path.name,
        "file_type": file_type,
        "file_size_mb": round(path.stat().st_size / (1024 * 1024), 3),
        "readable": True,
        "row_count": int(len(df)),
        "columns": "|".join(columns),
        "timestamp_column_candidate": candidates.timestamp or "",
        "open_column_candidate": candidates.open or "",
        "high_column_candidate": candidates.high or "",
        "low_column_candidate": candidates.low or "",
        "close_column_candidate": candidates.close or "",
        "spread_column_exists": candidates.spread_exists,
        "volume_column_exists": candidates.volume_exists,
        "start_time": start_time,
        "end_time": end_time,
        "duplicate_timestamp_count": "" if duplicate_timestamp_count is None else duplicate_timestamp_count,
        "timestamp_monotonic": "" if timestamp_monotonic is None else timestamp_monotonic,
        "missing_value_summary": stringify_missing_summary(df),
        "invalid_ohlc_count": "" if invalid_ohlc_count is None else invalid_ohlc_count,
        "can_convert_to_price_loader_csv": convertible,
        "recommendation": recommendation,
        "notes": " ; ".join(notes),
    }


def inspect_file(path: Path) -> dict[str, Any]:
    suffix = path.suffix.lower()
    notes: list[str] = []

    if suffix == ".parquet":
        return inspect_parquet(path, notes)

    if suffix == ".pkl":
        return inspect_pickle(path, notes)

    # CSV-like, including extension-less files.
    if suffix in CSV_EXTENSIONS or suffix == "":
        df, sep, err, dat_no_header = read_csv_like(path, nrows=5)
        if err:
            return unreadable_row(path, "csv-like", err)
        if sep:
            notes.append(f"csv separator='{sep}'")
        if dat_no_header:
            notes.append("detected DAT-style no-header format")
        return inspect_csv_like(path, sep, df, notes, dat_no_header)

    return unreadable_row(path, "unknown", "unsupported file extension")


def unreadable_row(path: Path, file_type: str, reason: str) -> dict[str, Any]:
    recommendation, recommendation_reason = recommend(
        readable=False,
        timestamp_ok=False,
        ohlc_ok=None,
        convertible=False,
        file_type=file_type,
    )
    return {
        "file_path": str(path),
        "file_name": path.name,
        "file_type": file_type,
        "file_size_mb": round(path.stat().st_size / (1024 * 1024), 3),
        "readable": False,
        "row_count": "",
        "columns": "",
        "timestamp_column_candidate": "",
        "open_column_candidate": "",
        "high_column_candidate": "",
        "low_column_candidate": "",
        "close_column_candidate": "",
        "spread_column_exists": False,
        "volume_column_exists": False,
        "start_time": "",
        "end_time": "",
        "duplicate_timestamp_count": "",
        "timestamp_monotonic": "",
        "missing_value_summary": "{}",
        "invalid_ohlc_count": "",
        "can_convert_to_price_loader_csv": False,
        "recommendation": recommendation,
        "notes": f"{reason} ; {recommendation_reason}",
    }


def looks_like_dat_no_header(columns: list[str]) -> bool:
    if len(columns) != 7:
        return False
    return all(any(ch.isdigit() for ch in col) for col in columns[:2])


def read_csv_like(path: Path, nrows: int | None = None) -> tuple[pd.DataFrame | None, str | None, str | None, bool]:
    for sep in CSV_SEPARATORS:
        try:
            df = pd.read_csv(path, sep=sep, nrows=nrows, low_memory=True)
        except Exception:
            continue
        if df is None or (df.empty and len(df.columns) == 0):
            continue
        if len(df.columns) >= 2 or sep == ",":
            cols = [str(c) for c in df.columns]
            if looks_like_dat_no_header(cols):
                try:
                    df2 = pd.read_csv(path, sep=sep, nrows=nrows, low_memory=True, header=None, names=DAT_NO_HEADER_COLUMNS)
                    return df2, sep, None, True
                except Exception:
                    pass
            return df, sep, None, False
    return None, None, "unable to read as CSV-like with separators ',', ';', '\\t'", False


def inspect_csv_like(path: Path, sep: str, sample_df: pd.DataFrame, notes: list[str], dat_no_header: bool) -> dict[str, Any]:
    columns = [str(c) for c in sample_df.columns]
    candidates = detect_candidates(columns)
    missing_counts = {col: 0 for col in columns}
    row_count = 0
    ts_min = None
    ts_max = None
    ts_col = candidates.timestamp
    timestamp_ok = False
    ts_parse_issue = False
    duplicate_count = 0
    monotonic = True
    prev_ts = None
    seen_ts_sample: set[Any] = set()
    seen_limit = 2_000_000
    invalid_ohlc_count = 0
    ohlc_checked = all([candidates.open, candidates.high, candidates.low, candidates.close])
    start_time = ""
    end_time = ""

    csv_kwargs: dict[str, Any] = {"sep": sep, "chunksize": CSV_CHUNK_SIZE, "low_memory": True}
    if dat_no_header:
        csv_kwargs.update({"header": None, "names": DAT_NO_HEADER_COLUMNS})
    for chunk in pd.read_csv(path, **csv_kwargs):
        row_count += len(chunk)
        for col in columns:
            if col in chunk.columns:
                missing_counts[col] += int(chunk[col].isna().sum())
        if ts_col and ts_col in chunk.columns:
            if ts_col == "date" and "time" in chunk.columns:
                ts = pd.to_datetime(
                    chunk["date"].astype(str).str.strip() + " " + chunk["time"].astype(str).str.strip(),
                    utc=True,
                    errors="coerce",
                    format="%Y.%m.%d %H:%M",
                )
            else:
                ts = pd.to_datetime(chunk[ts_col], utc=True, errors="coerce")
            valid_ts = ts.dropna()
            if not valid_ts.empty:
                timestamp_ok = True
                cmin = valid_ts.min()
                cmax = valid_ts.max()
                ts_min = cmin if ts_min is None else min(ts_min, cmin)
                ts_max = cmax if ts_max is None else max(ts_max, cmax)
                if prev_ts is not None and not valid_ts.empty and valid_ts.iloc[0] < prev_ts:
                    monotonic = False
                if not valid_ts.is_monotonic_increasing:
                    monotonic = False
                prev_ts = valid_ts.iloc[-1]
                if len(seen_ts_sample) < seen_limit:
                    vals = valid_ts.astype("int64").tolist()
                    for v in vals:
                        if v in seen_ts_sample:
                            duplicate_count += 1
                        else:
                            seen_ts_sample.add(v)
            if int(ts.isna().sum()) > 0:
                ts_parse_issue = True
        elif ts_col:
            ts_parse_issue = True

        if ohlc_checked:
            op = pd.to_numeric(chunk[candidates.open], errors="coerce")
            hi = pd.to_numeric(chunk[candidates.high], errors="coerce")
            lo = pd.to_numeric(chunk[candidates.low], errors="coerce")
            cl = pd.to_numeric(chunk[candidates.close], errors="coerce")
            valid_num = op.notna() & hi.notna() & lo.notna() & cl.notna()
            invalid = valid_num & (
                (hi < pd.concat([op, cl], axis=1).max(axis=1))
                | (lo > pd.concat([op, cl], axis=1).min(axis=1))
                | (hi < lo)
            )
            invalid_ohlc_count += int(invalid.sum())

    if ts_parse_issue:
        notes.append("timestamp parse partial or failed for some rows")
    if ts_min is not None:
        start_time = ts_min.isoformat()
    if ts_max is not None:
        end_time = ts_max.isoformat()
    if not ohlc_checked:
        notes.append("OHLC validation skipped: required columns missing")

    missing_summary_pairs = [(k, v) for k, v in missing_counts.items() if v > 0]
    missing_summary = "{}"
    if missing_summary_pairs:
        missing_summary = "{" + ", ".join(f"{k}:{v}" for k, v in sorted(missing_summary_pairs, key=lambda x: x[1], reverse=True)) + "}"

    convertible = can_convert_to_price_loader_csv(columns)
    ohlc_ok = None if not ohlc_checked else (invalid_ohlc_count == 0)
    recommendation, recommendation_reason = recommend(
        readable=True,
        timestamp_ok=timestamp_ok,
        ohlc_ok=ohlc_ok,
        convertible=convertible,
        file_type="csv-like",
    )
    notes.append(recommendation_reason)

    return {
        "file_path": str(path),
        "file_name": path.name,
        "file_type": "csv-like",
        "file_size_mb": round(path.stat().st_size / (1024 * 1024), 3),
        "readable": True,
        "row_count": row_count,
        "columns": "|".join(columns),
        "timestamp_column_candidate": candidates.timestamp or "",
        "open_column_candidate": candidates.open or "",
        "high_column_candidate": candidates.high or "",
        "low_column_candidate": candidates.low or "",
        "close_column_candidate": candidates.close or "",
        "spread_column_exists": candidates.spread_exists,
        "volume_column_exists": candidates.volume_exists,
        "start_time": start_time,
        "end_time": end_time,
        "duplicate_timestamp_count": duplicate_count if ts_col else "",
        "timestamp_monotonic": monotonic if ts_col else "",
        "missing_value_summary": missing_summary,
        "invalid_ohlc_count": invalid_ohlc_count if ohlc_checked else "",
        "can_convert_to_price_loader_csv": convertible,
        "recommendation": recommendation,
        "notes": " ; ".join(notes),
    }


def inspect_parquet(path: Path, notes: list[str]) -> dict[str, Any]:
    if pq is not None:
        try:
            pf = pq.ParquetFile(path)
            columns = pf.schema.names
            row_count = pf.metadata.num_rows if pf.metadata is not None else ""
            notes.append("parquet inspected via metadata")
            sample_df = pd.read_parquet(path, columns=columns[: min(10, len(columns))]).head(5000)
            row = inspect_dataframe(path, sample_df, "parquet", notes)
            row["row_count"] = row_count
            row["notes"] += " ; sample-based stats for large parquet"
            return row
        except Exception as exc:
            notes.append(f"parquet metadata read failed: {exc}")
    try:
        sample_df = pd.read_parquet(path).head(5000)
        row = inspect_dataframe(path, sample_df, "parquet", notes)
        row["notes"] += " ; fallback read_parquet used with head(5000)"
        return row
    except Exception as exc:
        return unreadable_row(path, "parquet", f"read_parquet failed: {exc}")


def inspect_pickle(path: Path, notes: list[str]) -> dict[str, Any]:
    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > PKL_MAX_INSPECT_MB:
        return {
            "file_path": str(path),
            "file_name": path.name,
            "file_type": "pkl-skipped-large",
            "file_size_mb": round(size_mb, 3),
            "readable": True,
            "row_count": "",
            "columns": "",
            "timestamp_column_candidate": "",
            "open_column_candidate": "",
            "high_column_candidate": "",
            "low_column_candidate": "",
            "close_column_candidate": "",
            "spread_column_exists": False,
            "volume_column_exists": False,
            "start_time": "",
            "end_time": "",
            "duplicate_timestamp_count": "",
            "timestamp_monotonic": "",
            "missing_value_summary": "{}",
            "invalid_ohlc_count": "",
            "can_convert_to_price_loader_csv": False,
            "recommendation": "caution",
            "notes": f"pkl too large ({size_mb:.1f} MB), deep inspection skipped ; pkl is not source of truth",
        }
    try:
        obj = pd.read_pickle(path)
    except Exception as exc:
        return unreadable_row(path, "pkl", f"read_pickle failed: {exc}")
    if isinstance(obj, pd.DataFrame):
        row = inspect_dataframe(path, obj.head(200_000), "pkl-dataframe", notes)
        row["row_count"] = len(obj)
        row["notes"] += " ; DataFrame inspected with head(200000)"
        return row
    return {
        "file_path": str(path),
        "file_name": path.name,
        "file_type": "pkl-non-dataframe",
        "file_size_mb": round(size_mb, 3),
        "readable": True,
        "row_count": "",
        "columns": "",
        "timestamp_column_candidate": "",
        "open_column_candidate": "",
        "high_column_candidate": "",
        "low_column_candidate": "",
        "close_column_candidate": "",
        "spread_column_exists": False,
        "volume_column_exists": False,
        "start_time": "",
        "end_time": "",
        "duplicate_timestamp_count": "",
        "timestamp_monotonic": "",
        "missing_value_summary": "{}",
        "invalid_ohlc_count": "",
        "can_convert_to_price_loader_csv": False,
        "recommendation": "reject",
        "notes": f"pickle object type={type(obj).__name__} ; 価格データ候補ではない可能性",
    }


def gather_target_files() -> list[Path]:
    files: list[Path] = []
    for base in TARGET_DIRS:
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if path.is_file():
                files.append(path)
    return sorted(files)


def write_markdown(rows: list[dict[str, Any]], output_path: Path) -> None:
    lines: list[str] = []
    lines.append("# USDJPY M1 Data Candidate Inspection")
    lines.append("")
    lines.append(f"- generated_at_utc: {pd.Timestamp.now(tz=timezone.utc).isoformat()}")
    lines.append(f"- inspected_file_count: {len(rows)}")
    lines.append("")

    rec_counts = pd.Series([r["recommendation"] for r in rows]).value_counts().to_dict() if rows else {}
    lines.append("## Recommendation Summary")
    lines.append("")
    if rec_counts:
        for key, count in rec_counts.items():
            lines.append(f"- {key}: {count}")
    else:
        lines.append("- no files")
    lines.append("")

    lines.append("## File Details")
    lines.append("")
    header = [
        "file_name",
        "file_type",
        "readable",
        "row_count",
        "start_time",
        "end_time",
        "duplicate_timestamp_count",
        "timestamp_monotonic",
        "invalid_ohlc_count",
        "can_convert_to_price_loader_csv",
        "recommendation",
        "notes",
    ]
    lines.append("| " + " | ".join(header) + " |")
    lines.append("| " + " | ".join(["---"] * len(header)) + " |")
    for row in rows:
        values = [str(row.get(col, "")).replace("\n", " ") for col in header]
        lines.append("| " + " | ".join(values) + " |")

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    files = gather_target_files()
    rows = [inspect_file(path) for path in files]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    columns = [
        "file_path",
        "file_name",
        "file_type",
        "file_size_mb",
        "readable",
        "row_count",
        "columns",
        "timestamp_column_candidate",
        "open_column_candidate",
        "high_column_candidate",
        "low_column_candidate",
        "close_column_candidate",
        "spread_column_exists",
        "volume_column_exists",
        "start_time",
        "end_time",
        "duplicate_timestamp_count",
        "timestamp_monotonic",
        "missing_value_summary",
        "invalid_ohlc_count",
        "can_convert_to_price_loader_csv",
        "recommendation",
        "notes",
    ]

    with OUTPUT_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)

    write_markdown(rows, OUTPUT_MD)

    print(f"[done] inspected files: {len(rows)}")
    print(f"[done] summary csv: {OUTPUT_CSV}")
    print(f"[done] summary md:  {OUTPUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
