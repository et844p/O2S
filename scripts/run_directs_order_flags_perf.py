#!/usr/bin/env python3
"""Run directs order-flag / supplier performance rollup.

Default: supplier rollup with IFR + delivery_rel by candidate bucket.
Use --order-level to emit flagged order rows (large).
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

_default_creds = ROOT / ".gcp" / "credentials.json"
if _default_creds.exists():
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(_default_creds)

from gbq import query_df

SQL_PATH = ROOT / "sql" / "directs_order_flags_supplier_perf.sql"
OUTPUT_DIR = ROOT / "output" / "directs"

ORDER_LEVEL_SELECT = """
SELECT *
FROM order_flagged
ORDER BY supplier_id, promised_delivery_end_range_date_at_order DESC, ops
"""


def build_sql(order_level: bool) -> str:
    sql = SQL_PATH.read_text()
    if not order_level:
        return sql
    # Keep CTEs through order_flagged; replace supplier rollup final SELECT.
    parts = re.split(
        r"\n-- =+\n-- SUPPLIER ROLLUP.*",
        sql,
        maxsplit=1,
        flags=re.DOTALL,
    )
    if len(parts) != 2:
        raise RuntimeError("Could not locate SUPPLIER ROLLUP marker in SQL file")
    return parts[0].rstrip() + "\n\n" + ORDER_LEVEL_SELECT.strip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--order-level",
        action="store_true",
        help="Export order-level flagged rows instead of supplier rollup",
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
        help="Optional filter to one supplier_id (applied in pandas after query)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional row limit after query (useful for order-level samples)",
    )
    args = parser.parse_args()

    if args.output is None:
        args.output = OUTPUT_DIR / (
            "directs_order_level_flags.csv"
            if args.order_level
            else "directs_supplier_perf_by_flag.csv"
        )

    sql = build_sql(order_level=args.order_level)
    if args.order_level and args.supplier_id is not None:
        # Push filter into SQL for cheaper pulls when sampling one supplier.
        sql = sql.replace(
            "SELECT *\nFROM order_flagged\n",
            f"SELECT *\nFROM order_flagged\nWHERE supplier_id = {args.supplier_id}\n",
        )

    df = query_df(sql)

    if args.supplier_id is not None and "supplier_id" in df.columns:
        df = df[df["supplier_id"] == args.supplier_id].copy()
    if args.limit is not None:
        df = df.head(args.limit).copy()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output, index=False)
    print(f"Wrote {len(df):,} rows to {args.output}")

    if not args.order_level and not df.empty:
        print(
            df[
                [
                    "su_name",
                    "total_vol",
                    "candidate_vol",
                    "actually_direct_vol",
                    "jumbo_vol",
                    "ghost_warehouse_vol",
                    "non_compliant_vol",
                    "relief_vol",
                    "candidate_partition_ok",
                    "ifr_candidate",
                    "delivery_rel_candidate",
                    "ifr_actually_direct",
                    "delivery_rel_actually_direct",
                    "ifr_jumbo",
                    "delivery_rel_jumbo",
                    "ifr_ghost",
                    "delivery_rel_ghost",
                    "ifr_non_compliant",
                    "delivery_rel_non_compliant",
                ]
            ]
            .head(10)
            .to_string(index=False)
        )


if __name__ == "__main__":
    main()
