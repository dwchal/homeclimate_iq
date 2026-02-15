from pathlib import Path

from src.analysis.utility_csv_report import format_text_report, summarize_utility_csv


def test_summarize_and_format(tmp_path: Path) -> None:
    csv_path = tmp_path / "utility.csv"
    csv_path.write_text(
        "date,kwh,cost\n"
        "2026-01-01,10.25,1.50\n"
        "2026-01-01,1.75,0.20\n"
        "2026-01-02,8.0,1.10\n",
        encoding="utf-8",
    )

    rows = summarize_utility_csv(csv_path)

    assert len(rows) == 2
    assert rows[0].date == "2026-01-01"
    assert rows[0].kwh == 12.0
    assert rows[0].cost == 1.7

    report = format_text_report(rows)
    assert "Total usage: 20.000 kWh" in report
    assert "Peak usage day: 2026-01-01 (12.000 kWh)" in report


def test_alias_columns_supported(tmp_path: Path) -> None:
    csv_path = tmp_path / "utility_aliases.csv"
    csv_path.write_text(
        "timestamp,usage_kwh,usd\n"
        "01/03/2026 00:00,2.5,0.40\n",
        encoding="utf-8",
    )

    rows = summarize_utility_csv(csv_path)

    assert rows[0].date == "2026-01-03"
    assert rows[0].kwh == 2.5
