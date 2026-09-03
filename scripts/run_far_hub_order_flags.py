#!/usr/bin/env python3
"""Far-hub OPID flags: supplier behavior first, then order-level flags.

Diagnoses each DS supplier (ghost / misshipping / builds_directs / noise / clean),
then flags candidate ops (OPIDs) using that diagnosis.

Default export: supplier diagnosis summary (actionable, small).
Use --order-level for candidate OPID rows (larger).
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

_default_creds = ROOT / ".gcp" / "credentials.json"
if _default_creds.exists():
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(_default_creds)

from gbq import query_df

SQL_PATH = ROOT / "sql" / "far_hub_order_flags.sql"
OUTPUT_DIR = ROOT / "output" / "directs"

BEHAVIOR_ORDER = [
    "ghost_warehouse",
    "misshipping",
    "builds_directs",
    "far_hub_noise",
    "clean",
]

SUPPLIER_SELECT = """
SELECT *
FROM supplier_summary
ORDER BY
  CASE supplier_behavior
    WHEN 'ghost_warehouse' THEN 1
    WHEN 'misshipping' THEN 2
    WHEN 'builds_directs' THEN 3
    WHEN 'far_hub_noise' THEN 4
    ELSE 5
  END,
  candidate_vol DESC,
  total_vol DESC
"""

ORDER_CANDIDATES_SELECT = """
SELECT *
FROM order_flagged
WHERE is_candidate = 1
ORDER BY supplier_behavior, supplier_id, promised_delivery_end_range_date_at_order DESC, ops
"""

ORDER_ALL_SELECT = """
SELECT *
FROM order_flagged
ORDER BY supplier_behavior, supplier_id, promised_delivery_end_range_date_at_order DESC, ops
"""


def build_sql(mode: str) -> str:
    sql = SQL_PATH.read_text()
    parts = re.split(
        r"\n-- =+\n-- DEFAULT: ORDER-LEVEL.*",
        sql,
        maxsplit=1,
        flags=re.DOTALL,
    )
    if len(parts) != 2:
        raise RuntimeError("Could not locate DEFAULT ORDER-LEVEL marker in SQL")
    head = parts[0].rstrip()
    if mode == "supplier":
        select = SUPPLIER_SELECT
    elif mode == "order_all":
        select = ORDER_ALL_SELECT
    else:
        select = ORDER_CANDIDATES_SELECT
    return head + "\n\n" + select.strip() + "\n"


def inject_supplier_filter(sql: str, mode: str, supplier_id: int) -> str:
    if mode == "supplier":
        needle = "SELECT *\nFROM supplier_summary\n"
        repl = (
            f"SELECT *\nFROM supplier_summary\n"
            f"WHERE supplier_id = {supplier_id}\n"
        )
        if needle not in sql:
            raise RuntimeError("Could not inject supplier_id filter (supplier)")
        return sql.replace(needle, repl, 1)

    # order_flagged selects may already have WHERE is_candidate = 1
    if "FROM order_flagged\nWHERE is_candidate = 1\n" in sql:
        return sql.replace(
            "FROM order_flagged\nWHERE is_candidate = 1\n",
            f"FROM order_flagged\nWHERE supplier_id = {supplier_id}\n"
            f"  AND is_candidate = 1\n",
            1,
        )
    needle = "SELECT *\nFROM order_flagged\n"
    repl = f"SELECT *\nFROM order_flagged\nWHERE supplier_id = {supplier_id}\n"
    if needle not in sql:
        raise RuntimeError("Could not inject supplier_id filter (order)")
    return sql.replace(needle, repl, 1)



def _behavior_summary(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for behavior, g in df.groupby("supplier_behavior", sort=False):
        rows.append(
            {
                "supplier_behavior": behavior,
                "suppliers": len(g),
                "total_vol": int(g["total_vol"].sum()),
                "candidate_vol": int(g["candidate_vol"].sum()),
                "misshipping_opid_vol": int(g["misshipping_opid_vol"].sum()),
                "ghost_opid_vol": int(g["ghost_opid_vol"].sum()),
                "direct_opid_vol": int(g["direct_opid_vol"].sum()),
                "other_far_opid_vol": int(g["other_far_opid_vol"].sum()),
                "jumbo_opid_vol": int(g["jumbo_opid_vol"].sum()),
            }
        )
    out = pd.DataFrame(rows)
    out["_ord"] = out["supplier_behavior"].map(
        {b: i for i, b in enumerate(BEHAVIOR_ORDER)}
    )
    return out.sort_values("_ord").drop(columns="_ord")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--order-level",
        action="store_true",
        help="Export candidate OPID rows instead of supplier summary",
    )
    parser.add_argument(
        "--all-orders",
        action="store_true",
        help="With --order-level, include non-candidate ops (very large)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output CSV path",
    )
    parser.add_argument(
        "--supplier-id",
        type=int,
        default=None,
        help="Optional filter to one supplier_id",
    )
    parser.add_argument(
        "--behavior",
        type=str,
        default=None,
        help="Optional filter to supplier_behavior (e.g. ghost_warehouse)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional row limit after query",
    )
    args = parser.parse_args()

    if args.order_level:
        mode = "order_all" if args.all_orders else "order_candidates"
        default_name = (
            "far_hub_order_flags_all.csv"
            if args.all_orders
            else "far_hub_order_flags.csv"
        )
    else:
        mode = "supplier"
        default_name = "far_hub_supplier_behavior.csv"

    if args.output is None:
        args.output = OUTPUT_DIR / default_name

    sql = build_sql(mode)
    if args.supplier_id is not None:
        sql = inject_supplier_filter(sql, mode, args.supplier_id)

    print(f"Running far-hub flags ({mode})...")
    df = query_df(sql)

    if args.supplier_id is not None and "supplier_id" in df.columns:
        df = df[df["supplier_id"] == args.supplier_id].copy()
    if args.behavior is not None and "supplier_behavior" in df.columns:
        df = df[df["supplier_behavior"] == args.behavior].copy()
    if args.limit is not None:
        df = df.head(args.limit).copy()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output, index=False)
    print(f"Wrote {len(df):,} rows to {args.output}")

    if mode == "supplier" and not df.empty:
        summary = _behavior_summary(df)
        summary_path = OUTPUT_DIR / "far_hub_supplier_behavior_summary.csv"
        summary.to_csv(summary_path, index=False)
        print(f"Wrote behavior summary to {summary_path}")
        print("\nSupplier behavior counts:")
        print(summary.to_string(index=False))

        print("\nExamples by behavior:")
        cols = [
            "su_name",
            "supplier_behavior",
            "total_vol",
            "candidate_vol",
            "misshipping_opid_vol",
            "ghost_opid_vol",
            "direct_opid_vol",
            "other_far_opid_vol",
            "ghost_states",
            "ghost_hubs",
        ]
        cols = [c for c in cols if c in df.columns]
        for behavior in BEHAVIOR_ORDER:
            sample = df[df["supplier_behavior"] == behavior].head(2)
            if sample.empty:
                continue
            print(f"\n--- {behavior} ---")
            print(sample[cols].to_string(index=False))

        for behavior in BEHAVIOR_ORDER:
            slice_df = df[df["supplier_behavior"] == behavior]
            if slice_df.empty:
                continue
            path = OUTPUT_DIR / f"far_hub_behavior_{behavior}.csv"
            slice_df.to_csv(path, index=False)
            print(f"  {behavior}: {len(slice_df):,} -> {path.name}")

    elif mode.startswith("order") and not df.empty and "opid_flag" in df.columns:
        print("\nOPID flag counts:")
        print(df["opid_flag"].value_counts().to_string())
        if "supplier_behavior" in df.columns:
            print("\nSupplier behavior on these rows:")
            print(df["supplier_behavior"].value_counts().to_string())


if __name__ == "__main__":
    main()
