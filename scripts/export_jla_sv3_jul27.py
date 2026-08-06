#!/usr/bin/env python3
"""Export JLA SV3 Jul 27 MSBD order-level data with exclusions join and B2B flag."""

from __future__ import annotations

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

SQL = ROOT / "sql" / "jla_sv3_jul27_order_level.sql"
OUT = ROOT / "output" / "jla_savannah"

# Column order matching JLA_JulyMSBD_Vol.xlsx "lates" sheet + B2B flag
EXCEL_COLUMNS = [
    "supplier_id",
    "su_name",
    "ops",
    "purchase_order_number",
    "tracking_number",
    "assigned_induction_hub_id",
    "actual_induction_hub_id",
    "order_complete_date_time_local",
    "msbd_su",
    "label",
    "label_by_msbd_2",
    "label_by_msbd_7",
    "has_relabel",
    "fulfillment_ship_date_time",
    "carrier_first_induction_date_time",
    "inducted_on_time_or_early",
    "label_by_msbd_2_1",
    "SU_FR",
    "one_day_late_between8_and4",
    "one_day_late_between4_and8",
    "sku",
    "supplierpartid",
    "supplierpartnumber",
    "Picked Date",
    "Load Date",
    "Trailer No.",
    "Trailer Complete Date",
    "Trailer Pickup Date",
    "ASN Sent Date",
    "First Scan Date",
    "DeliveryDate",
    "loaded on correct day",
    "no delay in induction",
    "is_b2b_flag",
    "is_b2b_customer_order",
    "sales_channel",
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    df = query_df(SQL.read_text())

    # Rename internal SQL aliases to Excel headers
    rename = {
        "Picked_Date": "Picked Date",
        "Load_Date": "Load Date",
        "Trailer_No": "Trailer No.",
        "Trailer_Complete_Date": "Trailer Complete Date",
        "Trailer_Pickup_Date": "Trailer Pickup Date",
        "ASN_Sent_Date": "ASN Sent Date",
        "First_Scan_Date": "First Scan Date",
        "loaded_on_correct_day": "loaded on correct day",
        "no_delay_in_induction": "no delay in induction",
    }
    df = df.rename(columns=rename)

    export = df[[c for c in EXCEL_COLUMNS if c in df.columns]].copy()

    csv_path = OUT / "jla_sv3_jul27_msbd_orders.csv"
    xlsx_path = OUT / "jla_sv3_jul27_msbd_orders.xlsx"
    export.to_csv(csv_path, index=False)
    export.to_excel(xlsx_path, index=False, sheet_name="jul27_sv3")

    print(f"Exported {len(export):,} rows")
    print(f"  CSV:  {csv_path}")
    print(f"  XLSX: {xlsx_path}")
    print(f"  B2B orders (is_b2b_flag=1): {export['is_b2b_flag'].sum():,}")
    print(f"  Exclusions join match: {df['is_b2b_customer_order'].notna().sum():,} / {len(df):,}")
    print(f"  Late orders: {(export['inducted_on_time_or_early'] == 0).sum():,}")


if __name__ == "__main__":
    main()
