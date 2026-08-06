#!/usr/bin/env python3
"""Export JLA SV3 Jul 27 MSBD order-level data — HVE columns + is_b2b_flag only."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

_default_creds = ROOT / ".gcp" / "credentials.json"
if _default_creds.exists():
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(_default_creds)

from gbq import query_df

SQL = ROOT / "sql" / "jla_sv3_jul27_order_level.sql"
OUT = ROOT / "output" / "jla_savannah"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    df = query_df(SQL.read_text())

    csv_path = OUT / "jla_sv3_jul27_msbd_orders.csv"
    xlsx_path = OUT / "jla_sv3_jul27_msbd_orders.xlsx"
    df.to_csv(csv_path, index=False)
    df.to_excel(xlsx_path, index=False, sheet_name="jul27_sv3")

    print(f"Exported {len(df):,} rows ({len(df.columns)} columns)")
    print(f"  CSV:  {csv_path}")
    print(f"  XLSX: {xlsx_path}")
    print(f"  B2B orders (is_b2b_flag=1): {df['is_b2b_flag'].sum():,}")


if __name__ == "__main__":
    main()
