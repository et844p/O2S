#!/usr/bin/env python3
"""Consolidate LP first-mile add/cancel recs for the current week."""

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

SQL_PATH = ROOT / "sql" / "large_parcel" / "add_cancel_this_week.sql"
OUTPUT_DIR = ROOT / "output" / "add_cancel"
DOC_PATH = ROOT / "docs" / "large_parcel" / "add_cancel_this_week.md"

COMBINED_COLS = [
    "LaneID",
    "SuName",
    "PoolPoint",
    "PlannedDate",
    "PlannedPickups",
    "Add",
    "Cancel",
]


def _md_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "_None._"
    cols = list(df.columns)
    header = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join("---" for _ in cols) + " |"
    rows = []
    for _, row in df.iterrows():
        cells = []
        for c in cols:
            val = row[c]
            if pd.isna(val):
                cells.append("")
            elif isinstance(val, float) and val.is_integer():
                cells.append(str(int(val)))
            else:
                cells.append(str(val))
        rows.append("| " + " | ".join(cells) + " |")
    return "\n".join([header, sep, *rows])


def lane_summary(detail: pd.DataFrame) -> pd.DataFrame:
    lane = (
        detail.groupby(["LaneID", "SuName", "PoolPoint", "RoutingType"], as_index=False)
        .agg(
            Days=("PlannedDate", "nunique"),
            PlannedPickups=("PlannedPickups", "sum"),
            Add=("Add", "sum"),
            Cancel=("Cancel", "sum"),
            OutstandingPOs=("TotalOutstandingPOs", "max"),
            PO_PU=("PO_PU", "max"),
        )
        .sort_values(["Add", "Cancel"], ascending=False)
    )
    lane["Net"] = lane["Add"] - lane["Cancel"]
    return lane


def write_markdown(detail: pd.DataFrame, lane: pd.DataFrame, path: Path) -> None:
    week = pd.to_datetime(detail["Week"].iloc[0]).date()
    refreshed = pd.to_datetime(detail["LastRefreshed"].max())
    today = pd.Timestamp.now("UTC").date()

    n_recs = len(detail)
    n_lanes = int(detail["LaneID"].nunique())
    n_pp = int(detail["PoolPoint"].nunique())
    add_rows = int((detail["Add"] > 0).sum())
    cancel_rows = int((detail["Cancel"] > 0).sum())
    add_loads = int(detail["Add"].sum())
    cancel_loads = int(detail["Cancel"].sum())

    by_day = (
        detail.groupby(["PlannedDate", "RoutingType"], as_index=False)
        .agg(Lanes=("LaneID", "count"), Add=("Add", "sum"), Cancel=("Cancel", "sum"))
        .sort_values(["PlannedDate", "RoutingType"])
    )
    by_day["PlannedDate"] = by_day["PlannedDate"].astype(str)

    by_pp = (
        detail.groupby("PoolPoint", as_index=False)
        .agg(
            Lanes=("LaneID", "nunique"),
            Recs=("LaneID", "count"),
            Add=("Add", "sum"),
            Cancel=("Cancel", "sum"),
        )
        .sort_values(["Add", "Cancel"], ascending=False)
    )

    top_add = (
        lane.sort_values("Add", ascending=False)
        .head(12)[["LaneID", "SuName", "PoolPoint", "RoutingType", "Add", "Cancel", "Net", "OutstandingPOs"]]
        .copy()
    )
    top_cancel = (
        lane.sort_values("Cancel", ascending=False)
        .head(12)[["LaneID", "SuName", "PoolPoint", "RoutingType", "Add", "Cancel", "Net", "OutstandingPOs"]]
        .copy()
    )

    capped = detail[detail["NetRecommendation"] != detail["UncappedRecommendation"]].copy()
    capped_view = capped[
        ["PlannedDate", "PoolPoint", "SuName", "NetRecommendation", "UncappedRecommendation"]
    ].copy()
    if not capped_view.empty:
        capped_view["PlannedDate"] = capped_view["PlannedDate"].astype(str)

    today_df = detail[detail["PlannedDate"] == today].copy()
    today_view = today_df[
        ["Add", "Cancel", "PoolPoint", "SuName", "PlannedPickups", "TotalOutstandingPOs", "RoutingType"]
    ].sort_values(["Add", "Cancel"], ascending=False)

    lines = [
        f"# LP add/cancel recommendations — week of {week}",
        "",
        f"As of **{refreshed:%Y-%m-%d %H:%M UTC}**. Monday-start week `{week}`.",
        "",
        "Consolidated from live MSOD (`fm_msod_dropnew`) into the Combined tab shape of",
        "[FM LP WDN Add/Cancel](https://docs.google.com/spreadsheets/d/19epubeBb3ohHO10UVUJUhd13MTECq_khKhAVQLRU9SI/edit?gid=710144122#gid=710144122)",
        "(`LaneID`, `SuName`, `PoolPoint`, `PlannedDate`, `PlannedPickups`, `Add`, `Cancel`).",
        "",
        "The Google Sheet Combined tab is also registered in BigQuery as",
        "`tnd_planning.FM_LP_WDN_Add_Cancel_Sheet`. Planner completion notes",
        "(`WasCompleted`, `TLPReasonCodes`, comments) live only on the sheet.",
        "",
        "## Snapshot",
        "",
        f"| Metric | Value |",
        f"| --- | --- |",
        f"| Supplier / lane recs | {n_recs} |",
        f"| Distinct lanes | {n_lanes} |",
        f"| Pool points | {n_pp} |",
        f"| Add recs (loads) | {add_rows} recs / **{add_loads}** loads |",
        f"| Cancel recs (loads) | {cancel_rows} recs / **{cancel_loads}** loads |",
        f"| Net loads | **{add_loads - cancel_loads:+d}** |",
        f"| Days with recs | {', '.join(sorted(detail['PlannedDate'].astype(str).unique()))} |",
        "",
        "`Add` / `Cancel` use capacity-capped `Recommendation`. Uncapped need is in the detail CSV.",
        "",
        "## By day and routing type",
        "",
        _md_table(by_day),
        "",
        "## By pool point",
        "",
        _md_table(by_pp),
        "",
        f"## Today's actions ({today})",
        "",
        f"{len(today_view)} lanes — **{int(today_df['Add'].sum())} add** / **{int(today_df['Cancel'].sum())} cancel** loads.",
        "",
        _md_table(today_view),
        "",
        "## Top add lanes (week)",
        "",
        _md_table(top_add),
        "",
        "## Top cancel lanes (week)",
        "",
        _md_table(top_cancel),
        "",
        "## Capacity-capped (uncapped need is higher)",
        "",
        _md_table(capped_view) if not capped_view.empty else "_None._",
        "",
        "## Files",
        "",
        "- Combined-format paste: `output/add_cancel/this_week_combined.csv`",
        "- Full detail: `output/add_cancel/this_week_detail.csv`",
        "- Lane rollup: `output/add_cancel/this_week_lane_summary.csv`",
        "- SQL: `sql/large_parcel/add_cancel_this_week.sql`",
        "",
        "Re-run: `python scripts/consolidate_add_cancel_recs.py`",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--doc", type=Path, default=DOC_PATH)
    args = parser.parse_args()

    detail = query_df(SQL_PATH.read_text())
    if detail.empty:
        raise SystemExit("No add/cancel recommendations found for this week.")

    for col in ("PlannedDate", "Week"):
        detail[col] = pd.to_datetime(detail[col]).dt.date

    combined = detail[COMBINED_COLS].copy()
    combined["WasCompleted"] = pd.NA
    combined["TLPReasonCodes"] = pd.NA
    combined["CommmentsOnNotAddedAsPlanned"] = pd.NA
    combined["Notes"] = pd.NA

    lane = lane_summary(detail)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    combined_path = args.output_dir / "this_week_combined.csv"
    detail_path = args.output_dir / "this_week_detail.csv"
    lane_path = args.output_dir / "this_week_lane_summary.csv"

    combined.to_csv(combined_path, index=False)
    detail.to_csv(detail_path, index=False)
    lane.to_csv(lane_path, index=False)
    write_markdown(detail, lane, args.doc)

    print(f"Wrote {len(combined)} Combined rows to {combined_path}")
    print(f"Wrote {len(detail)} detail rows to {detail_path}")
    print(f"Wrote {len(lane)} lane rows to {lane_path}")
    print(f"Wrote report to {args.doc}")
    print(
        f"Adds={int(detail['Add'].sum())} Cancels={int(detail['Cancel'].sum())} "
        f"Lanes={detail['LaneID'].nunique()}"
    )


if __name__ == "__main__":
    main()
