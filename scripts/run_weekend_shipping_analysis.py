#!/usr/bin/env python3
"""Run weekend shipping supplier enablement analysis against HVE_perf_Monitoring."""

from __future__ import annotations

import argparse
import os
import sys
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Prefer repo-local credentials when env points at a missing file.
_default_creds = ROOT / ".gcp" / "credentials.json"
if _default_creds.exists():
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(_default_creds)

from gbq import query_df

SQL_PATH = ROOT / "sql" / "weekend_shipping_supplier_analysis.sql"
OUTPUT_DIR = ROOT / "output"
DOCS_DIR = ROOT / "docs" / "small_parcel"


def _pct(value: float | None) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return f"{float(value) * 100:.1f}%"


def _md_cell(value: object) -> str:
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def write_markdown_table(df, path: Path, *, candidates_only: bool) -> None:
    table_df = df.copy()
    if candidates_only:
        table_df = table_df[table_df["weekend_shipping_candidate"].fillna(False).astype(bool)]
        title = "Weekend Shipping Candidates (24hr, ≥70% Fri/Sat weekend ship rate, IFR > 85%)"
    else:
        title = "Weekend Shipping Supplier Analysis — All Suppliers"

    columns = [
        ("supplier_id", "Supplier ID"),
        ("su_name", "Supplier Name"),
        ("lt", "LT"),
        ("cutoff", "Cutoff"),
        ("station_name", "Station"),
        ("address", "Address"),
        ("city", "City"),
        ("state", "State"),
        ("postal_code", "Postal Code"),
        ("sto", "STO"),
        ("marketing_category", "Marketing Category"),
        ("srm", "SRM"),
        ("last_6_weeks_volume", "6-Wk Vol"),
        ("fri_sat_order_volume", "Fri/Sat Vol"),
        ("fri_sat_weekend_shipped_volume", "Fri/Sat Wknd Shipped"),
        ("pct_fri_sat_shipped_on_sat_or_sun", "% Fri/Sat Shipped Sat/Sun"),
        ("ifr", "IFR"),
        ("weekend_shipping_candidate", "Candidate"),
    ]

    header = "| " + " | ".join(label for _, label in columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    rows = []
    for _, row in table_df.iterrows():
        cells = []
        for col, _ in columns:
            val = row[col]
            if col in ("pct_fri_sat_shipped_on_sat_or_sun", "ifr"):
                cells.append(_pct(val))
            elif col == "weekend_shipping_candidate":
                cells.append("Yes" if pd.notna(val) and bool(val) else "No")
            else:
                cells.append(_md_cell(val))
        rows.append("| " + " | ".join(cells) + " |")

    lines = [
        f"# {title}",
        "",
        f"Generated: {date.today().isoformat()}",
        "",
        "Analysis window: last 6 weeks. Weekend ship = Fri/Sat placed orders inducted on Saturday or Sunday (`induction_dow_adj` 6 or 7).",
        "",
        f"Rows: {len(table_df):,}",
        "",
        header,
        separator,
        *rows,
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_DIR / "weekend_shipping_supplier_analysis.csv",
        help="CSV path for full supplier results",
    )
    parser.add_argument(
        "--markdown",
        type=Path,
        default=DOCS_DIR / "weekend_shipping_supplier_analysis.md",
        help="Markdown table path for GitHub",
    )
    parser.add_argument(
        "--candidates-only",
        action="store_true",
        help="Only write suppliers flagged as weekend shipping candidates",
    )
    args = parser.parse_args()

    sql = SQL_PATH.read_text()
    df = query_df(sql)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    export_df = df
    if args.candidates_only:
        export_df = df[df["weekend_shipping_candidate"]]
    export_df.to_csv(args.output, index=False)

    write_markdown_table(df, args.markdown, candidates_only=True)

    candidates = int(df["weekend_shipping_candidate"].sum())
    print(f"Wrote {len(export_df)} rows to {args.output}")
    print(f"Wrote markdown table to {args.markdown}")
    print(f"Weekend shipping candidates: {candidates}")


if __name__ == "__main__":
    main()
