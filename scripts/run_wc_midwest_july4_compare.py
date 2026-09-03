#!/usr/bin/env python3
"""West Coast → Midwest directs: high-vol week vs July 4 MSBD week.

Note: classified `direct` volume on this corridor peaks Memorial Day week
(2026-05-24), not July 4. July 4 / July 5 weeks are high corridor volume
but almost all long-haul via West Coast hubs (non-direct).

Compares suppliers who built directs on:
  - O2D stated vs actual
  - IFR (inducted_on_time_or_early)
  - delivery_rel
"""

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

OUTPUT_DIR = ROOT / "output" / "directs"

# Sunday-start MSBD weeks
PEAK_WEEK = "2026-05-24"  # Memorial Day — true high-vol directs week
JULY4_WEEK = "2026-06-28"  # week containing July 4 2026 (Sat)
JULY5_WEEK = "2026-07-05"  # following week — higher network/corridor vol


def region_expr(col: str) -> str:
    return f"""
CASE
  WHEN {col} IN ('CA', 'OR', 'WA', 'AK', 'HI') THEN 'West Coast'
  WHEN {col} IN ('AZ', 'NV', 'UT', 'CO', 'NM', 'ID', 'MT', 'WY') THEN 'Mountain'
  WHEN {col} IN ('TX', 'OK', 'AR', 'LA') THEN 'South Central'
  WHEN {col} = 'FL' THEN 'Florida'
  WHEN {col} IN ('GA', 'SC', 'NC', 'AL', 'TN', 'MS', 'KY') THEN 'Southeast'
  WHEN {col} IN ('VA', 'MD', 'DC', 'DE', 'WV') THEN 'Mid-Atlantic'
  WHEN {col} IN ('NJ', 'NY', 'PA', 'CT', 'MA', 'RI', 'NH', 'VT', 'ME') THEN 'Northeast'
  WHEN {col} IN ('IL', 'IN', 'OH', 'MI', 'WI', 'MN', 'IA', 'MO', 'KS', 'NE', 'ND', 'SD') THEN 'Midwest'
  ELSE COALESCE({col}, 'Unknown')
END
"""


SQL = f"""
WITH
base AS (
  SELECT
    o.supplier_id,
    o.su_name,
    o.parent_suid,
    o.parent_su_name,
    o.sto,
    o.ops,
    o.state_name AS own_state,
    o.assigned_induction_hub_name,
    o.assigned_station_state,
    o.actual_induction_hub_name,
    o.actual_induction_hub_state,
    o.destination_state,
    o.distance_assignedhub_customer,
    o.distance_actualhub_customer,
    o.distance_assignedhub_actualhub,
    o.direct_gain,
    o.inducted_on_time_or_early,
    o.delivery_rel,
    o.o2d_stated,
    o.o2d_actual,
    o.msbd_su,
    COALESCE(o.msbd_su_week, DATE_TRUNC(o.msbd_su, WEEK(SUNDAY))) AS msbd_week,
    CASE
      WHEN o.assignedhub_notequal_actualhub_flag = 1
        AND COALESCE(o.distance_assignedhub_customer, 0) >= 400
        AND COALESCE(o.distance_assignedhub_actualhub, 0) >= 200 THEN 1
      ELSE 0
    END AS is_candidate
  FROM `wf-gcp-us-ae-global-tnd-prod.speed_and_reliability.HVE_perf_Monitoring` AS o
  WHERE o.fulfillment_type = 'DS'
    AND o.msbd_su >= DATE('2026-05-01')
    AND o.msbd_su < CURRENT_DATE()
),

parent_states AS (
  SELECT DISTINCT parent_suid, state_name AS warehouse_state
  FROM `wf-gcp-us-ae-global-tnd-prod.speed_and_reliability.HVE_perf_Monitoring`
  WHERE fulfillment_type = 'DS'
    AND parent_suid IS NOT NULL
    AND state_name IS NOT NULL
    AND msbd_su >= DATE('2026-05-01')
    AND msbd_su < CURRENT_DATE()
),

enriched AS (
  SELECT
    b.*,
    IF(
      ps.warehouse_state IS NOT NULL
      AND b.actual_induction_hub_state IS NOT NULL
      AND b.actual_induction_hub_state != b.own_state,
      1, 0
    ) AS is_sibling_state,
    ({region_expr("b.assigned_station_state")}) AS origin_region,
    ({region_expr("b.destination_state")}) AS dest_region,
    ({region_expr("b.actual_induction_hub_state")}) AS actual_hub_region
  FROM base AS b
  LEFT JOIN parent_states AS ps
    ON b.parent_suid = ps.parent_suid
   AND b.actual_induction_hub_state = ps.warehouse_state
),

supplier_meta AS (
  SELECT
    supplier_id,
    COUNT(DISTINCT ops) AS total_vol,
    COUNT(DISTINCT msbd_week) AS weeks_with_vol
  FROM enriched
  GROUP BY 1
),

ghost_hubs AS (
  SELECT e.supplier_id, e.actual_induction_hub_name
  FROM enriched AS e
  JOIN supplier_meta AS m USING (supplier_id)
  WHERE e.is_candidate = 1
    AND e.actual_induction_hub_name IS NOT NULL
    AND e.is_sibling_state = 0
  GROUP BY e.supplier_id, e.actual_induction_hub_name, m.total_vol, m.weeks_with_vol
  HAVING SAFE_DIVIDE(COUNT(DISTINCT e.ops), m.total_vol) >= 0.10
     AND COUNT(DISTINCT e.msbd_week)
         >= GREATEST(2, CAST(CEIL(0.5 * m.weeks_with_vol) AS INT64))
     AND AVG(IF(e.distance_assignedhub_actualhub >= 200, 1, 0)) >= 0.8
),

flagged AS (
  SELECT
    e.*,
    CASE
      WHEN e.is_candidate = 0 THEN 'non_candidate'
      WHEN e.is_sibling_state = 1 THEN 'misshipping'
      WHEN g.actual_induction_hub_name IS NOT NULL THEN 'ghost_warehouse'
      WHEN COALESCE(e.direct_gain, 0) < 0.4 THEN 'jumbo'
      ELSE 'direct'
    END AS candidate_bucket
  FROM enriched AS e
  LEFT JOIN ghost_hubs AS g
    ON e.supplier_id = g.supplier_id
   AND e.actual_induction_hub_name = g.actual_induction_hub_name
)

SELECT
  candidate_bucket,
  origin_region,
  dest_region,
  actual_hub_region,
  assigned_station_state AS origin_state,
  destination_state AS dest_state,
  CAST(msbd_week AS STRING) AS msbd_week,
  supplier_id,
  su_name,
  parent_suid,
  parent_su_name,
  sto,
  assigned_induction_hub_name,
  actual_induction_hub_name,
  COUNT(DISTINCT ops) AS vol,
  AVG(inducted_on_time_or_early) AS ifr,
  AVG(delivery_rel) AS delivery_rel,
  AVG(o2d_stated) AS avg_o2d_stated,
  AVG(o2d_actual) AS avg_o2d_actual,
  AVG(direct_gain) AS avg_direct_gain,
  AVG(distance_actualhub_customer) AS avg_mi_actual_to_cust,
  AVG(distance_assignedhub_customer) AS avg_mi_assigned_to_cust
FROM flagged
WHERE origin_region = 'West Coast'
  AND dest_region = 'Midwest'
GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14
"""


def wavg(df: pd.DataFrame, col: str, wcol: str = "vol") -> float:
    w, v = df[wcol], df[col]
    m = v.notna() & w.notna() & (w > 0)
    if not m.any() or w[m].sum() == 0:
        return float("nan")
    return float((v[m] * w[m]).sum() / w[m].sum())


def rollup(g: pd.DataFrame) -> pd.Series:
    return pd.Series(
        {
            "vol": float(g["vol"].sum()),
            "ifr": wavg(g, "ifr"),
            "delivery_rel": wavg(g, "delivery_rel"),
            "avg_o2d_stated": wavg(g, "avg_o2d_stated"),
            "avg_o2d_actual": wavg(g, "avg_o2d_actual"),
            "avg_direct_gain": wavg(g, "avg_direct_gain"),
            "avg_mi_actual_to_cust": wavg(g, "avg_mi_actual_to_cust"),
            "suppliers": int(g["supplier_id"].nunique()),
        }
    )


def supplier_roll(g: pd.DataFrame, label: str) -> pd.DataFrame:
    rows = []
    for keys, sg in g.groupby(
        ["supplier_id", "su_name", "parent_suid", "parent_su_name", "sto"], dropna=False
    ):
        stated = wavg(sg, "avg_o2d_stated")
        actual = wavg(sg, "avg_o2d_actual")
        rows.append(
            {
                "supplier_id": keys[0],
                "su_name": keys[1],
                "parent_suid": keys[2],
                "parent_su_name": keys[3],
                "sto": keys[4],
                f"vol_{label}": sg["vol"].sum(),
                f"ifr_{label}": wavg(sg, "ifr"),
                f"delivery_rel_{label}": wavg(sg, "delivery_rel"),
                f"o2d_stated_{label}": stated,
                f"o2d_actual_{label}": actual,
                f"o2d_gap_{label}": (actual - stated) if pd.notna(actual) and pd.notna(stated) else float("nan"),
                f"gain_{label}": wavg(sg, "avg_direct_gain"),
                f"mi_to_cust_{label}": wavg(sg, "avg_mi_actual_to_cust"),
                f"top_actual_hub_{label}": (
                    sg.groupby("actual_induction_hub_name")["vol"].sum().idxmax()
                    if sg["actual_induction_hub_name"].notna().any()
                    else None
                ),
            }
        )
    return pd.DataFrame(rows)


def fmt_pct(x) -> str:
    if pd.isna(x):
        return "—"
    return f"{x:.1%}"


def fmt_num(x, d=2) -> str:
    if pd.isna(x):
        return "—"
    return f"{x:.{d}f}"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print("Querying WC→Midwest by MSBD week...")
    df = query_df(SQL)
    df["msbd_week"] = pd.to_datetime(df["msbd_week"]).dt.strftime("%Y-%m-%d")
    print(f"Rows: {len(df):,}")

    directs = df[df["candidate_bucket"] == "direct"].copy()
    # Operational: inducted in Midwest for Midwest customers from WC assignment
    mw_induct = df[df["actual_hub_region"] == "Midwest"].copy()

    # --- Weekly directs ---
    week_d = (
        directs.groupby("msbd_week", dropna=False)
        .apply(rollup, include_groups=False)
        .reset_index()
        .sort_values("msbd_week")
    )
    week_d["o2d_gap"] = week_d["avg_o2d_actual"] - week_d["avg_o2d_stated"]
    week_d.to_csv(OUTPUT_DIR / "wc_midwest_directs_by_msbd_week.csv", index=False)

    week_all = (
        df.groupby("msbd_week", dropna=False)
        .apply(rollup, include_groups=False)
        .reset_index()
        .sort_values("msbd_week")
    )
    week_all.to_csv(OUTPUT_DIR / "wc_midwest_corridor_by_msbd_week.csv", index=False)

    week_mw = (
        mw_induct.groupby("msbd_week", dropna=False)
        .apply(rollup, include_groups=False)
        .reset_index()
        .sort_values("msbd_week")
    )
    week_mw["o2d_gap"] = week_mw["avg_o2d_actual"] - week_mw["avg_o2d_stated"]
    week_mw.to_csv(OUTPUT_DIR / "wc_midwest_midwest_induct_by_msbd_week.csv", index=False)

    print("\nDirect vol by week (top):")
    print(week_d.sort_values("vol", ascending=False).head(8).to_string(index=False))

    # --- Period summaries ---
    periods = {
        "peak_memorial_2026-05-24": PEAK_WEEK,
        "july4_week_2026-06-28": JULY4_WEEK,
        "july5_week_2026-07-05": JULY5_WEEK,
    }
    period_rows = []
    for name, wk in periods.items():
        for slice_name, slice_df in [("direct", directs), ("midwest_induct", mw_induct), ("corridor_all", df)]:
            sub = slice_df[slice_df["msbd_week"] == wk]
            if sub.empty:
                continue
            r = rollup(sub)
            r["period"] = name
            r["slice"] = slice_name
            r["msbd_week"] = wk
            r["o2d_gap"] = r["avg_o2d_actual"] - r["avg_o2d_stated"]
            period_rows.append(r)
    period = pd.DataFrame(period_rows)
    period.to_csv(OUTPUT_DIR / "wc_midwest_period_summary.csv", index=False)

    print("\n=== Period summary ===")
    print(period.to_string(index=False))

    # --- Supplier compare: peak vs July 4 (directs) ---
    peak_s = supplier_roll(directs[directs["msbd_week"] == PEAK_WEEK], "peak")
    july_s = supplier_roll(directs[directs["msbd_week"] == JULY4_WEEK], "july4")
    july5_s = supplier_roll(directs[directs["msbd_week"] == JULY5_WEEK], "july5")

    # Outer join from peak (high vol) — primary compare set
    merged = peak_s.merge(july_s, on=["supplier_id", "su_name", "parent_suid", "parent_su_name", "sto"], how="outer")
    merged = merged.merge(july5_s, on=["supplier_id", "su_name", "parent_suid", "parent_su_name", "sto"], how="outer")
    merged["ifr_delta_july4_vs_peak"] = merged["ifr_july4"] - merged["ifr_peak"]
    merged["del_delta_july4_vs_peak"] = merged["delivery_rel_july4"] - merged["delivery_rel_peak"]
    merged["o2d_actual_delta_july4_vs_peak"] = merged["o2d_actual_july4"] - merged["o2d_actual_peak"]
    merged["built_july4"] = merged["vol_july4"].fillna(0) > 0
    merged["built_july5"] = merged["vol_july5"].fillna(0) > 0
    merged = merged.sort_values("vol_peak", ascending=False, na_position="last")
    merged.to_csv(OUTPUT_DIR / "wc_midwest_peak_vs_july4_suppliers.csv", index=False)

    # Material peak suppliers
    mat = merged[merged["vol_peak"].fillna(0) >= 30].copy()
    print(f"\nSuppliers with ≥30 directs in peak week: {len(mat)}")
    print(
        mat.head(20)[
            [
                "supplier_id",
                "su_name",
                "vol_peak",
                "ifr_peak",
                "delivery_rel_peak",
                "o2d_stated_peak",
                "o2d_actual_peak",
                "o2d_gap_peak",
                "vol_july4",
                "ifr_july4",
                "o2d_actual_july4",
            ]
        ].to_string(index=False)
    )

    # July 4 directs builders (small)
    j4 = merged[merged["vol_july4"].fillna(0) > 0].sort_values("vol_july4", ascending=False)
    print(f"\nSuppliers who built ANY WC→MW directs in July 4 week: {len(j4)} (vol={j4['vol_july4'].sum():.0f})")
    if len(j4):
        print(
            j4.head(15)[
                [
                    "supplier_id",
                    "su_name",
                    "vol_july4",
                    "ifr_july4",
                    "delivery_rel_july4",
                    "o2d_stated_july4",
                    "o2d_actual_july4",
                    "o2d_gap_july4",
                    "vol_peak",
                    "ifr_peak",
                ]
            ].to_string(index=False)
        )

    # Peak-week supplier scorecard (main deliverable)
    peak_only = peak_s.copy()
    peak_only = peak_only[peak_only["vol_peak"] >= 30].sort_values("vol_peak", ascending=False)
    peak_only["ifr_rank"] = peak_only["ifr_peak"].rank(ascending=False, method="min")
    peak_only["del_rank"] = peak_only["delivery_rel_peak"].rank(ascending=False, method="min")
    peak_only["speed_rank"] = peak_only["o2d_actual_peak"].rank(ascending=True, method="min")  # lower better
    peak_only.to_csv(OUTPUT_DIR / "wc_midwest_peak_week_supplier_scorecard.csv", index=False)

    # Excel
    with pd.ExcelWriter(OUTPUT_DIR / "wc_midwest_july4_directs_compare.xlsx", engine="openpyxl") as xw:
        period.to_excel(xw, sheet_name="period_summary", index=False)
        week_d.to_excel(xw, sheet_name="weekly_directs", index=False)
        week_all.to_excel(xw, sheet_name="weekly_corridor", index=False)
        week_mw.to_excel(xw, sheet_name="weekly_midwest_induct", index=False)
        mat.to_excel(xw, sheet_name="peak_suppliers_ge30", index=False)
        peak_only.to_excel(xw, sheet_name="peak_scorecard", index=False)
        j4.to_excel(xw, sheet_name="july4_direct_builders", index=False)
        merged.head(5000).to_excel(xw, sheet_name="all_suppliers_merged", index=False)

    # Markdown
    md = []
    md.append("# West Coast → Midwest: peak directs week vs July 4")
    md.append("")
    md.append("Corridor: assigned **West Coast** → customer **Midwest**. Timebase: `msbd_su_week`.")
    md.append("Bucket: classified **`direct`** (candidate + gain ≥ 0.4, not misshipping/ghost/jumbo).")
    md.append("")
    md.append("## Important finding")
    md.append("")
    md.append(
        "July 4 MSBD week is **high corridor volume** but **not** a directs week on this lane. "
        "Midwest induction / classified directs concentrated in **Memorial Day week `2026-05-24`** "
        "(~23k directs, ~33k Midwest inductions). By `2026-06-28` (July 4 week) directs fall to ~110–120 ops "
        "and Midwest inductions to ~75 — almost all WC→Midwest volume is long-haul via West Coast hubs again."
    )
    md.append("")
    md.append("| MSBD week | Corridor vol | Direct vol | Midwest-induct vol |")
    md.append("|-----------|--------------|------------|--------------------|")
    for wk, label in [
        (PEAK_WEEK, "Memorial Day peak"),
        (JULY4_WEEK, "July 4 week"),
        (JULY5_WEEK, "July 5 week (high network)"),
    ]:
        c = week_all.loc[week_all["msbd_week"] == wk, "vol"]
        d = week_d.loc[week_d["msbd_week"] == wk, "vol"]
        m = week_mw.loc[week_mw["msbd_week"] == wk, "vol"]
        md.append(
            f"| {wk} ({label}) | "
            f"{(c.iloc[0] if len(c) else 0):,.0f} | "
            f"{(d.iloc[0] if len(d) else 0):,.0f} | "
            f"{(m.iloc[0] if len(m) else 0):,.0f} |"
        )
    md.append("")
    md.append("## Period metrics — classified directs")
    md.append("")
    md.append("| Period | Vol | Suppliers | IFR | Del Rel | O2D stated | O2D actual | Gap |")
    md.append("|--------|-----|-----------|-----|---------|------------|------------|-----|")
    for _, r in period[period["slice"] == "direct"].iterrows():
        md.append(
            f"| {r['period']} | {r['vol']:,.0f} | {r['suppliers']:.0f} | "
            f"{fmt_pct(r['ifr'])} | {fmt_pct(r['delivery_rel'])} | "
            f"{fmt_num(r['avg_o2d_stated'])} | {fmt_num(r['avg_o2d_actual'])} | "
            f"{fmt_num(r['o2d_gap'], 2)} |"
        )
    md.append("")
    md.append("## Weekly directs (full window)")
    md.append("")
    md.append("| MSBD week | Vol | Suppliers | IFR | Del Rel | O2D stated | O2D actual | Gap |")
    md.append("|-----------|-----|-----------|-----|---------|------------|------------|-----|")
    for _, r in week_d.iterrows():
        tag = ""
        if r["msbd_week"] == PEAK_WEEK:
            tag = " ← peak"
        elif r["msbd_week"] == JULY4_WEEK:
            tag = " ← July 4"
        elif r["msbd_week"] == JULY5_WEEK:
            tag = " ← July 5"
        md.append(
            f"| {r['msbd_week']}{tag} | {r['vol']:,.0f} | {r['suppliers']:.0f} | "
            f"{fmt_pct(r['ifr'])} | {fmt_pct(r['delivery_rel'])} | "
            f"{fmt_num(r['avg_o2d_stated'])} | {fmt_num(r['avg_o2d_actual'])} | "
            f"{r['o2d_gap']:+.2f} |"
        )
    md.append("")
    md.append("## Peak week supplier scorecard (Memorial Day, ≥30 directs)")
    md.append("")
    md.append(
        "Speed = O2D actual (lower better). Gap = actual − stated (negative = beat promise)."
    )
    md.append("")
    md.append(
        "| SUID | Supplier | Vol | IFR | Del Rel | O2D stated | O2D actual | Gap | Top hub |"
    )
    md.append(
        "|------|----------|-----|-----|---------|------------|------------|-----|---------|"
    )
    for _, r in peak_only.head(25).iterrows():
        md.append(
            f"| {int(r['supplier_id'])} | {r['su_name']} | {r['vol_peak']:,.0f} | "
            f"{fmt_pct(r['ifr_peak'])} | {fmt_pct(r['delivery_rel_peak'])} | "
            f"{fmt_num(r['o2d_stated_peak'])} | {fmt_num(r['o2d_actual_peak'])} | "
            f"{r['o2d_gap_peak']:+.2f} | {r['top_actual_hub_peak']} |"
        )
    md.append("")
    md.append("### Best / worst IFR in peak week (vol≥30)")
    md.append("")
    best = peak_only.nlargest(8, "ifr_peak")
    worst = peak_only.nsmallest(8, "ifr_peak")
    md.append("**Best IFR:** " + ", ".join(
        f"{r.su_name} ({r.ifr_peak:.0%}, n={r.vol_peak:.0f})" for r in best.itertuples()
    ))
    md.append("")
    md.append("**Worst IFR:** " + ", ".join(
        f"{r.su_name} ({r.ifr_peak:.0%}, n={r.vol_peak:.0f})" for r in worst.itertuples()
    ))
    md.append("")
    md.append("## July 4 week — who still built directs")
    md.append("")
    if j4.empty:
        md.append("No suppliers with classified directs.")
    else:
        md.append(
            f"**{len(j4)}** suppliers, **{j4['vol_july4'].sum():,.0f}** ops total "
            "(vs ~23k in peak week)."
        )
        md.append("")
        md.append(
            "| SUID | Supplier | July4 vol | IFR | Del Rel | O2D stated | O2D actual | Gap | Peak vol | Peak IFR |"
        )
        md.append(
            "|------|----------|-----------|-----|---------|------------|------------|-----|----------|----------|"
        )
        for _, r in j4.head(20).iterrows():
            md.append(
                f"| {int(r['supplier_id'])} | {r['su_name']} | {r['vol_july4']:,.0f} | "
                f"{fmt_pct(r['ifr_july4'])} | {fmt_pct(r['delivery_rel_july4'])} | "
                f"{fmt_num(r['o2d_stated_july4'])} | {fmt_num(r['o2d_actual_july4'])} | "
                f"{fmt_num(r['o2d_gap_july4'])} | "
                f"{fmt_num(r['vol_peak'], 0)} | {fmt_pct(r['ifr_peak'])} |"
            )
    md.append("")
    md.append("## Files")
    md.append("")
    md.append("| File | Contents |")
    md.append("|------|----------|")
    md.append("| `wc_midwest_july4_directs_compare.xlsx` | All tabs |")
    md.append("| `wc_midwest_peak_week_supplier_scorecard.csv` | Memorial Day supplier metrics |")
    md.append("| `wc_midwest_peak_vs_july4_suppliers.csv` | Peak ↔ July 4/5 merge |")
    md.append("| `scripts/run_wc_midwest_july4_compare.py` | Re-run |")

    path = OUTPUT_DIR / "wc_midwest_july4_directs_compare.md"
    path.write_text("\n".join(md) + "\n")
    print(f"\nWrote {path}")


if __name__ == "__main__":
    main()
