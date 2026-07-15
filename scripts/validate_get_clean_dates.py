#!/usr/bin/env python3
"""Validate supplier get-clean dates against weekly IFR from HVE_perf_Monitoring."""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

import pandas as pd

from gbq import SP_TABLE_FQN, query_df

CSV_PATH = Path(
    "/home/ubuntu/.cursor/projects/workspace/uploads/"
    "5_26_GPS_Proposal_SupplierSelection_-_Sheet21_b578.csv"
)
OUTPUT_PATH = Path("/workspace/output/get_clean_validation.csv")
EXPORT_PATH = Path("/workspace/output/get_clean_validation_export.csv")


def pct(value: float | None) -> str:
    if value is None or pd.isna(value):
        return ""
    return f"{value:.1%}"


def build_notes(row: pd.Series) -> str:
    notes: list[str] = []

    wk_m2 = row["ifr_outreach_week_minus_2"]
    wk_m1 = row["ifr_outreach_week_minus_1"]
    wk_0 = row["ifr_outreach_week"]
    wk_clean = row["ifr_get_clean_week"]
    drop = row["ifr_drop_wk_minus_2_to_minus_1"]

    if pd.notna(drop):
        if drop <= -0.10:
            notes.append(f"Outreach trigger confirmed: IFR dropped {drop:+.1%} from wk-2 to wk-1.")
        elif drop >= 0.10:
            notes.append(
                f"Outreach trigger not supported by data: IFR improved {drop:+.1%} from wk-2 to wk-1."
            )
        else:
            notes.append(f"Modest IFR change from wk-2 to wk-1 ({drop:+.1%}).")

    if pd.isna(wk_clean):
        notes.append("No MSBD weekday volume in get-clean week; date is future or not yet measurable.")
    elif row["ifr_at_least_90pct"]:
        notes.append(f"Get-clean date validated: {wk_clean:.1%} IFR in stated week (>=90%).")
    else:
        notes.append(f"Get-clean date not validated: only {wk_clean:.1%} IFR in stated week (<90%).")

    if pd.notna(wk_0) and pd.notna(wk_clean):
        if row["get_clean_week"] == row["outreach_week"]:
            if wk_clean >= 0.90:
                notes.append("Recovered during outreach week; get-clean week same as outreach week.")
            else:
                notes.append("Get-clean week same as outreach week but IFR still below 90%.")
        elif wk_0 >= 0.90 and wk_clean < 0.90:
            notes.append("IFR was >=90% in outreach week but fell below 90% by get-clean week.")
        elif wk_0 < 0.90 and wk_clean >= 0.90:
            notes.append("Recovery lagged outreach week; supplier cleaned up after outreach week.")
        elif pd.notna(wk_m1) and wk_m1 < 0.90 and wk_0 < 0.90 and wk_clean < 0.90:
            notes.append("Persistent underperformance across wk-1, outreach week, and get-clean week.")

    if pd.notna(wk_0) and pd.notna(wk_m1) and wk_0 - wk_m1 >= 0.30:
        notes.append(
            f"Sharp recovery in outreach week ({wk_m1:.1%} -> {wk_0:.1%}); "
            "may reflect backlog clearing."
        )
    if pd.notna(wk_0) and pd.notna(wk_clean) and wk_clean - wk_0 >= 0.30:
        notes.append(
            f"Large improvement after outreach week ({wk_0:.1%} -> {wk_clean:.1%}); "
            "get-clean date may reflect delayed recovery."
        )

    if pd.notna(wk_clean) and int(row["vol_get_clean_week"]) < 100:
        notes.append(f"Low volume in get-clean week ({int(row['vol_get_clean_week'])} ops); interpret with caution.")

    return " ".join(notes)


def build_export(out: pd.DataFrame) -> pd.DataFrame:
    export = out.copy()
    export["notes"] = export.apply(build_notes, axis=1)
    export = export.sort_values(["get_clean_date", "child_id"]).reset_index(drop=True)

    export_cols = [
        "outreach_lead",
        "child_id",
        "outreach_date",
        "get_clean_date",
        "resolution_date",
        "root_cause",
        "outreach_week_minus_2",
        "ifr_outreach_week_minus_2",
        "vol_outreach_week_minus_2",
        "outreach_week_minus_1",
        "ifr_outreach_week_minus_1",
        "vol_outreach_week_minus_1",
        "outreach_week",
        "ifr_outreach_week",
        "vol_outreach_week",
        "get_clean_week",
        "ifr_get_clean_week",
        "vol_get_clean_week",
        "ifr_drop_wk_minus_2_to_minus_1",
        "ifr_at_least_90pct",
        "notes",
    ]
    export = export[export_cols].rename(
        columns={
            "outreach_lead": "Outreach Lead",
            "child_id": "Child Id",
            "outreach_date": "Outreach Date",
            "get_clean_date": "Get Clean Date",
            "resolution_date": "Resolution Date",
            "root_cause": "Root Cause",
            "outreach_week_minus_2": "Outreach Week -2",
            "ifr_outreach_week_minus_2": "IFR Week -2",
            "vol_outreach_week_minus_2": "Volume Week -2",
            "outreach_week_minus_1": "Outreach Week -1",
            "ifr_outreach_week_minus_1": "IFR Week -1",
            "vol_outreach_week_minus_1": "Volume Week -1",
            "outreach_week": "Outreach Week (0)",
            "ifr_outreach_week": "IFR Week 0",
            "vol_outreach_week": "Volume Week 0",
            "get_clean_week": "Get Clean Week",
            "ifr_get_clean_week": "IFR Get-Clean Week",
            "vol_get_clean_week": "Volume Get-Clean Week",
            "ifr_drop_wk_minus_2_to_minus_1": "IFR Drop Wk-2 to Wk-1",
            "ifr_at_least_90pct": "Get Clean Validated (>=90%)",
            "notes": "Notes",
        }
    )

    for col in [
        "IFR Week -2",
        "IFR Week -1",
        "IFR Week 0",
        "IFR Get-Clean Week",
        "IFR Drop Wk-2 to Wk-1",
    ]:
        export[col] = export[col].map(pct)

    export["Get Clean Validated (>=90%)"] = export["Get Clean Validated (>=90%)"].map(
        {True: "Yes", False: "No"}
    )
    return export


def parse_date(value: str | None) -> datetime.date | None:
    value = (value or "").strip()
    if not value:
        return None
    for fmt in ("%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def week_start_sun(value) -> datetime.date:
    ts = pd.Timestamp(value)
    return (ts - pd.Timedelta(days=(ts.dayofweek + 1) % 7)).date()


def week_label(start: datetime.date) -> str:
    end = pd.Timestamp(start) + pd.Timedelta(days=6)
    return f"{start} to {end.date()}"


def load_records() -> list[dict]:
    with CSV_PATH.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    records = []
    for row in rows:
        clean = parse_date(row.get("Get Clean Date"))
        if not clean:
            continue
        records.append(
            {
                "outreach_lead": row["Outreach Lead"].strip(),
                "child_id": int(row["Child Id"]),
                "outreach_date": parse_date(row.get("Outreach Date")),
                "get_clean_date": clean,
                "resolution_date": parse_date(row.get("Resolution Date")),
                "root_cause": row.get("Root Cause", "").strip()[:80],
            }
        )
    return records


def fetch_weekly_ifr(suppliers: list[int], min_date, max_date) -> pd.DataFrame:
    supplier_list = ", ".join(str(s) for s in suppliers)
    sql = f"""
    WITH base AS (
      SELECT
        supplier_id,
        msbd_su,
        inducted_on_time_or_early,
        ops,
        DATE_SUB(msbd_su, INTERVAL EXTRACT(DAYOFWEEK FROM msbd_su) - 1 DAY) AS week_start_sun
      FROM {SP_TABLE_FQN}
      WHERE supplier_id IN ({supplier_list})
        AND msbd_su BETWEEN DATE_SUB(DATE '{min_date}', INTERVAL 28 DAY)
                        AND DATE_ADD(DATE '{max_date}', INTERVAL 14 DAY)
        AND EXTRACT(DAYOFWEEK FROM msbd_su) BETWEEN 2 AND 6
    )
    SELECT
      supplier_id,
      week_start_sun,
      COUNT(DISTINCT ops) AS volume,
      ROUND(AVG(inducted_on_time_or_early), 4) AS ifr
    FROM base
    GROUP BY supplier_id, week_start_sun
    ORDER BY supplier_id, week_start_sun
    """
    weekly = query_df(sql)
    weekly["week_start_sun"] = pd.to_datetime(weekly["week_start_sun"]).dt.date
    return weekly


def main() -> None:
    records = load_records()
    suppliers = sorted({record["child_id"] for record in records})
    min_date = min(record["outreach_date"] for record in records)
    max_date = max(
        max(record["get_clean_date"] for record in records),
        max(record["outreach_date"] for record in records),
    )

    weekly = fetch_weekly_ifr(suppliers, min_date, max_date)
    results = []

    for record in records:
        supplier_id = record["child_id"]
        outreach = record["outreach_date"]
        clean = record["get_clean_date"]
        supplier_weeks = weekly[weekly["supplier_id"] == supplier_id]

        outreach_week = week_start_sun(outreach)
        outreach_week_minus_2 = week_start_sun(pd.Timestamp(outreach_week) - pd.Timedelta(days=14))
        outreach_week_minus_1 = week_start_sun(pd.Timestamp(outreach_week) - pd.Timedelta(days=7))
        clean_week = week_start_sun(clean)

        def get_ifr(week: datetime.date) -> tuple[float | None, int]:
            match = supplier_weeks[supplier_weeks["week_start_sun"] == week]
            if match.empty:
                return None, 0
            row = match.iloc[0]
            return float(row["ifr"]), int(row["volume"])

        ifr_outreach_wk_minus_2, vol_outreach_wk_minus_2 = get_ifr(outreach_week_minus_2)
        ifr_outreach_wk_minus_1, vol_outreach_wk_minus_1 = get_ifr(outreach_week_minus_1)
        ifr_outreach_wk, vol_outreach_wk = get_ifr(outreach_week)
        ifr_clean, vol_clean = get_ifr(clean_week)

        drop = None
        if ifr_outreach_wk_minus_2 is not None and ifr_outreach_wk_minus_1 is not None:
            drop = round(ifr_outreach_wk_minus_1 - ifr_outreach_wk_minus_2, 4)

        results.append(
            {
                **record,
                "outreach_week_start": outreach_week,
                "outreach_week": week_label(outreach_week),
                "outreach_week_minus_2": week_label(outreach_week_minus_2),
                "ifr_outreach_week_minus_2": ifr_outreach_wk_minus_2,
                "vol_outreach_week_minus_2": vol_outreach_wk_minus_2,
                "outreach_week_minus_1": week_label(outreach_week_minus_1),
                "ifr_outreach_week_minus_1": ifr_outreach_wk_minus_1,
                "vol_outreach_week_minus_1": vol_outreach_wk_minus_1,
                "ifr_outreach_week": ifr_outreach_wk,
                "vol_outreach_week": vol_outreach_wk,
                "ifr_drop_wk_minus_2_to_minus_1": drop,
                "get_clean_week_start": clean_week,
                "get_clean_week": week_label(clean_week),
                "ifr_get_clean_week": ifr_clean,
                "vol_get_clean_week": vol_clean,
                "ifr_at_least_90pct": ifr_clean is not None and ifr_clean >= 0.90,
                "ifr_improved_from_problem_week": (
                    ifr_clean is not None
                    and ifr_outreach_wk_minus_1 is not None
                    and ifr_clean > ifr_outreach_wk_minus_1
                ),
            }
        )

    out = pd.DataFrame(results)
    out["notes"] = out.apply(build_notes, axis=1)
    export = build_export(out)

    print("=" * 120)
    print("GET CLEAN DATE VALIDATION — Weekly IFR (Sun-Sat, weekdays by MSBD)")
    print("=" * 120)

    for _, row in out.sort_values(["get_clean_date", "child_id"]).iterrows():
        ifr_clean = row["ifr_get_clean_week"]
        ifr_str = f"{ifr_clean:.1%}" if pd.notna(ifr_clean) else "no data"
        flag = "YES" if row["ifr_at_least_90pct"] else ("NO" if pd.notna(ifr_clean) else "N/A")

        print(f"\nSupplier {int(row['child_id'])} | Outreach {row['outreach_date']} | Get Clean {row['get_clean_date']}")
        print(f"  Outreach week:             {row['outreach_week']}")
        if pd.notna(row["ifr_outreach_week_minus_2"]):
            print(
                f"  IFR outreach week -2:      {row['ifr_outreach_week_minus_2']:.1%} "
                f"({int(row['vol_outreach_week_minus_2'])} ops) | {row['outreach_week_minus_2']}"
            )
        else:
            print(f"  IFR outreach week -2:      no data | {row['outreach_week_minus_2']}")
        if pd.notna(row["ifr_outreach_week_minus_1"]):
            print(
                f"  IFR outreach week -1:      {row['ifr_outreach_week_minus_1']:.1%} "
                f"({int(row['vol_outreach_week_minus_1'])} ops) | {row['outreach_week_minus_1']}"
            )
        else:
            print(f"  IFR outreach week -1:      no data | {row['outreach_week_minus_1']}")
        if pd.notna(row["ifr_outreach_week"]):
            print(
                f"  IFR outreach week (0):     {row['ifr_outreach_week']:.1%} "
                f"({int(row['vol_outreach_week'])} ops) | {row['outreach_week']}"
            )
        else:
            print(f"  IFR outreach week (0):     no data | {row['outreach_week']}")
        print(f"  Week of get clean date:    {row['get_clean_week']}")
        print(f"  IFR in get-clean week:     {ifr_str} ({int(row['vol_get_clean_week'])} ops)")
        print(f"  Met >=90% IFR in that week? {flag}")
        print(f"  Notes: {row['notes']}")
        if pd.notna(row["ifr_drop_wk_minus_2_to_minus_1"]):
            print(
                f"  Outreach trigger drop (wk-2 to wk-1): "
                f"{row['ifr_drop_wk_minus_2_to_minus_1']:+.1%}"
            )

    summary = {
        "suppliers_with_get_clean_date": len(out),
        "met_90pct_in_clean_week": int(out["ifr_at_least_90pct"].sum()),
        "below_90pct_in_clean_week": int(
            (out["ifr_get_clean_week"].notna() & ~out["ifr_at_least_90pct"]).sum()
        ),
        "no_data_in_clean_week": int(out["ifr_get_clean_week"].isna().sum()),
    }
    print("\n" + "=" * 120)
    print("SUMMARY:", summary)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUTPUT_PATH, index=False)
    export.to_csv(EXPORT_PATH, index=False)
    print(f"\nSaved detailed results to {OUTPUT_PATH}")
    print(f"Saved export to {EXPORT_PATH}")


if __name__ == "__main__":
    main()
