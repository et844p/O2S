#!/usr/bin/env python3
"""Validate Pickup Pal setup (BigQuery + optional Slack)."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def check_bigquery() -> bool:
    try:
        from gbq import query_df

        df = query_df(
            "SELECT COUNT(*) AS n "
            "FROM `wf-gcp-us-ae-global-tnd-prod.speed_and_reliability.OTR_Tracking_ET`"
        )
        print(f"✓ BigQuery OK ({int(df.iloc[0]['n']):,} rows in OTR_Tracking_ET)")
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"✗ BigQuery failed: {exc}")
        print("  → Run: gcloud auth application-default login")
        return False


def check_slack() -> bool:
    bot = os.environ.get("SLACK_BOT_TOKEN", "")
    app = os.environ.get("SLACK_APP_TOKEN", "")
    if bot.startswith("xoxb-") and app.startswith("xapp-"):
        print("✓ Slack tokens present")
        return True
    print("✗ Slack tokens missing (set SLACK_BOT_TOKEN and SLACK_APP_TOKEN)")
    return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-slack", action="store_true")
    args = parser.parse_args()

    ok = check_bigquery()
    if not args.skip_slack:
        ok = check_slack() and ok

    if ok:
        print("\nPickup Pal is ready.")
        return 0

    print("\nSetup incomplete — see docs/large_parcel/cursor_setup.md")
    return 1


if __name__ == "__main__":
    sys.exit(main())
