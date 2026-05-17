#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Compare multiple exit experiment run directories.')
    parser.add_argument('--run-dir', action='append', required=True, help='Run directory path. Repeat this option.')
    parser.add_argument('--output-csv', required=True)
    parser.add_argument('--output-md', required=True)
    return parser.parse_args()


def _to_float(x: Any) -> float | None:
    try:
        return float(str(x))
    except Exception:
        return None


def _load_csv_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open('r', encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def _summarize_run(run_dir: Path) -> dict[str, Any]:
    summary_path = run_dir / 'backtest_summary.csv'
    trades_path = run_dir / 'trade_logs.csv'
    validation_path = run_dir / 'log_validation_summary.csv'

    summary_rows = _load_csv_rows(summary_path)
    if not summary_rows:
        raise FileNotFoundError(f'backtest_summary.csv not found or empty: {summary_path}')
    s = summary_rows[0]

    trades = _load_csv_rows(trades_path)
    pnls = []
    holds = []
    wins = 0
    exits = Counter()
    structure = Counter()
    fallback_true = 0
    for r in trades:
        p = _to_float(r.get('pnl', ''))
        if p is None:
            continue
        pnls.append(p)
        if p > 0:
            wins += 1
        h = _to_float(r.get('holding_bars', ''))
        if h is not None:
            holds.append(h)
        exits[str(r.get('exit_reason', ''))] += 1
        structure[str(r.get('structure_source', ''))] += 1
        if str(r.get('fallback_used', '')).lower() == 'true':
            fallback_true += 1

    validation_rows = _load_csv_rows(validation_path)
    validation = {r.get('metric', ''): r.get('value', '') for r in validation_rows}

    trade_count = len(pnls)
    return {
        'period': f"{s.get('start_time','')}..{s.get('end_time','')}",
        'run_id': s.get('run_id', ''),
        'exit_policy': s.get('exit_policy', ''),
        'trade_count': trade_count,
        'win_rate': (wins / trade_count * 100.0) if trade_count else 0.0,
        'total_pnl': sum(pnls),
        'average_pnl': mean(pnls) if pnls else 0.0,
        'exit_reason_counts': dict(exits),
        'average_holding_bars': mean(holds) if holds else 0.0,
        'max_holding_bars': max(holds) if holds else 0.0,
        'fallback_used_rate': (fallback_true / trade_count * 100.0) if trade_count else 0.0,
        'structure_source_counts': dict(structure),
        'validation_trade_logs_schema_valid': validation.get('trade_logs_schema_valid', ''),
        'validation_log_consistency_valid': validation.get('log_consistency_valid', ''),
        'run_dir': str(run_dir),
    }


def main() -> int:
    args = parse_args()
    rows = [_summarize_run(Path(d)) for d in args.run_dir]
    rows.sort(key=lambda x: (x['period'], x['exit_policy']))

    out_csv = Path(args.output_csv)
    out_md = Path(args.output_md)
    out_csv.parent.mkdir(parents=True, exist_ok=True)

    with out_csv.open('w', encoding='utf-8', newline='') as f:
        fields = list(rows[0].keys())
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            x = dict(r)
            x['exit_reason_counts'] = json.dumps(x['exit_reason_counts'], ensure_ascii=False)
            x['structure_source_counts'] = json.dumps(x['structure_source_counts'], ensure_ascii=False)
            w.writerow(x)

    lines = [
        '# Exit Experiment Comparison',
        '',
        '## 注意',
        '- spread=0.2 pips fallback 前提。',
        '- 手数料・スリッページ・スワップ未反映。',
        '- 収益性評価ではなく構造検証。',
        '',
        '## Metrics',
    ]
    for r in rows:
        lines.append(
            f"- period={r['period']}, exit_policy={r['exit_policy']}, trade_count={r['trade_count']}, win_rate={r['win_rate']:.2f}, total_pnl={r['total_pnl']:.6f}, average_pnl={r['average_pnl']:.6f}, exit_reason_counts={r['exit_reason_counts']}, average_holding_bars={r['average_holding_bars']:.2f}, max_holding_bars={r['max_holding_bars']}, fallback_used_rate={r['fallback_used_rate']:.2f}, structure_source_counts={r['structure_source_counts']}, validation_trade_logs_schema_valid={r['validation_trade_logs_schema_valid']}, validation_log_consistency_valid={r['validation_log_consistency_valid']}"
        )

    out_md.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f"[done] output_csv={out_csv}")
    print(f"[done] output_md={out_md}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
