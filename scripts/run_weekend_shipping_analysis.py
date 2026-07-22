#!/usr/bin/env python3
"""Run weekend shipping supplier enablement analysis against HVE_perf_Monitoring."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

_default_creds = ROOT / ".gcp" / "credentials.json"
if _default_creds.exists():
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(_default_creds)

from gbq import query_df

SQL_PATH = ROOT / "sql" / "weekend_shipping_supplier_analysis.sql"
OUTPUT_DIR = ROOT / "output"

COHORT_EXPORTS = {
    "candidate": "weekend_shipping_candidates.csv",
    "almost_ready": "weekend_shipping_almost_ready.csv",
    "not_weekend_shipping": "weekend_shipping_not_shipping.csv",
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_DIR / "weekend_shipping_supplier_analysis.csv",
        help="CSV path for full supplier results",
    )
    parser.add_argument(
        "--cohort",
        choices=[*COHORT_EXPORTS.keys(), "all"],
        default="all",
        help="Export a single cohort or all suppliers",
    )
    args = parser.parse_args()

    df = query_df(SQL_PATH.read_text())

    if args.cohort == "all":
        export_df = df
        output_path = args.output
    else:
        export_df = df[df["weekend_shipping_cohort"] == args.cohort]
        output_path = OUTPUT_DIR / COHORT_EXPORTS[args.cohort]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    export_df.to_csv(output_path, index=False)

    cohort_counts = df["weekend_shipping_cohort"].value_counts().to_dict()
    print(f"Wrote {len(export_df)} rows to {output_path}")
    print(f"Suppliers with >= 500 L6W ops: {len(df):,}")
    for cohort, count in sorted(cohort_counts.items()):
        print(f"  {cohort}: {count:,}")


if __name__ == "__main__":
    main()
