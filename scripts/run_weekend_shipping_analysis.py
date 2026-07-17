#!/usr/bin/env python3
"""Run weekend shipping supplier enablement analysis against HVE_perf_Monitoring."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from gbq import query_df

SQL_PATH = Path(__file__).resolve().parent.parent / "sql" / "weekend_shipping_supplier_analysis.sql"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_DIR / "weekend_shipping_supplier_analysis.csv",
        help="CSV path for full supplier results",
    )
    parser.add_argument(
        "--candidates-only",
        action="store_true",
        help="Only write 24hr suppliers flagged for weekend shipping",
    )
    args = parser.parse_args()

    sql = SQL_PATH.read_text()
    df = query_df(sql)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.candidates_only:
        candidates = df[
            df["enable_saturday_weekend_shipping"] | df["enable_sunday_weekend_shipping"]
        ]
        candidates.to_csv(args.output, index=False)
        print(f"Wrote {len(candidates)} candidate suppliers to {args.output}")
    else:
        df.to_csv(args.output, index=False)
        print(f"Wrote {len(df)} suppliers to {args.output}")

    enabled_sat = int(df["enable_saturday_weekend_shipping"].sum())
    enabled_sun = int(df["enable_sunday_weekend_shipping"].sum())
    print(f"Saturday weekend shipping candidates: {enabled_sat}")
    print(f"Sunday weekend shipping candidates: {enabled_sun}")


if __name__ == "__main__":
    main()
