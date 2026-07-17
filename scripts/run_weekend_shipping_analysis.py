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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_DIR / "weekend_shipping_supplier_analysis.csv",
        help="CSV path for supplier results",
    )
    parser.add_argument(
        "--candidates-only",
        action="store_true",
        help="Only write suppliers flagged as weekend shipping candidates",
    )
    args = parser.parse_args()

    df = query_df(SQL_PATH.read_text())

    export_df = df
    if args.candidates_only:
        export_df = df[df["weekend_shipping_candidate"].fillna(False).astype(bool)]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    export_df.to_csv(args.output, index=False)

    candidates = int(df["weekend_shipping_candidate"].fillna(False).astype(bool).sum())
    print(f"Wrote {len(export_df)} rows to {args.output}")
    print(f"Suppliers with >= 500 L6W ops: {len(df):,}")
    print(f"Weekend shipping candidates: {candidates}")


if __name__ == "__main__":
    main()
