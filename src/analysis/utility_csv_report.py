"""Utility CSV reporting helpers.

Feature: summarize utility usage and cost from a CSV export.
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

DATE_ALIASES = ("date", "timestamp", "datetime", "start_time")
KWH_ALIASES = ("kwh", "usage_kwh", "energy_kwh", "consumption_kwh")
COST_ALIASES = ("cost", "usd", "charge", "total_cost")


@dataclass(frozen=True)
class DailyUsage:
    date: str
    kwh: float
    cost: float


def _find_column(fieldnames: list[str], aliases: tuple[str, ...]) -> str:
    normalized = {field.strip().lower(): field for field in fieldnames}
    for alias in aliases:
        if alias in normalized:
            return normalized[alias]
    raise ValueError(f"Missing required CSV column. Expected one of: {aliases}")


def _parse_date(value: str) -> str:
    text = value.strip()
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%m/%d/%Y", "%m/%d/%Y %H:%M"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue

    return datetime.fromisoformat(text).date().isoformat()


def summarize_utility_csv(path: Path) -> list[DailyUsage]:
    """Aggregate CSV rows by day.

    Expected columns include aliases for date, kWh and cost.
    """
    by_day: dict[str, dict[str, float]] = defaultdict(lambda: {"kwh": 0.0, "cost": 0.0})

    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError("CSV appears empty or lacks headers")

        date_col = _find_column(reader.fieldnames, DATE_ALIASES)
        kwh_col = _find_column(reader.fieldnames, KWH_ALIASES)
        cost_col = _find_column(reader.fieldnames, COST_ALIASES)

        for row in reader:
            day = _parse_date(row[date_col])
            by_day[day]["kwh"] += float(row[kwh_col] or 0)
            by_day[day]["cost"] += float(row[cost_col] or 0)

    return [
        DailyUsage(date=day, kwh=round(values["kwh"], 3), cost=round(values["cost"], 2))
        for day, values in sorted(by_day.items())
    ]


def format_text_report(rows: list[DailyUsage]) -> str:
    if not rows:
        return "No rows found."

    total_kwh = round(sum(row.kwh for row in rows), 3)
    total_cost = round(sum(row.cost for row in rows), 2)
    peak = max(rows, key=lambda row: row.kwh)

    lines = [
        "Daily Utility Summary",
        "date         | kWh    | cost",
        "-------------|--------|------",
    ]
    for row in rows:
        lines.append(f"{row.date} | {row.kwh:6.3f} | ${row.cost:5.2f}")

    lines.extend(
        [
            "",
            f"Days analyzed: {len(rows)}",
            f"Total usage: {total_kwh:.3f} kWh",
            f"Total cost: ${total_cost:.2f}",
            f"Peak usage day: {peak.date} ({peak.kwh:.3f} kWh)",
        ]
    )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Summarize utility company CSV exports.")
    parser.add_argument("csv_path", type=Path, help="Path to utility CSV file")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    rows = summarize_utility_csv(args.csv_path)
    print(format_text_report(rows))


if __name__ == "__main__":
    main()
