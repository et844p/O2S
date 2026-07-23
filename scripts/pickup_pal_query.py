#!/usr/bin/env python3
"""Run Pickup Pal queries for common large-parcel pickup questions."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

_default_creds = ROOT / ".gcp" / "credentials.json"
if _default_creds.exists():
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(_default_creds)

from pickup_pal.queries import QUERIES, run_query


def main() -> int:
    parser = argparse.ArgumentParser(description="Pickup Pal query runner")
    parser.add_argument(
        "query",
        choices=sorted(QUERIES),
        help="Query type to run",
    )
    parser.add_argument(
        "--supplier",
        required=True,
        help='Supplier name fragment (e.g. "Flash Furniture")',
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Print raw DataFrame instead of formatted summary",
    )
    args = parser.parse_args()

    print(run_query(args.query, args.supplier, raw=args.raw))
    return 0


if __name__ == "__main__":
    sys.exit(main())
