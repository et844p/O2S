#!/usr/bin/env python3
"""WC→Midwest: directs vs SoCal-induct non-directs (same dest region).

Compares O2D stated/actual, IFR, delivery_rel for:
  - direct path: classified `direct` to Midwest customers
  - socal_nondirect: Midwest customers, actual induction at SoCal hubs, not a direct
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

PEAK_WEEK = "2026-05-24"
JULY4_WEEK = "2026-06-28"
JULY5_WEEK = "2026-07-05"

# SoCal = LA basin / Inland Empire / SD (exclude NorCal: Fairfield, Tracy, Sac, Fresno, etc.)
SOCAL_HUBS = (
    "Chino",
    "Chino Hills Ncpc",
    "Rialto",
    "South Rialto - Ncpc",
    "West Rialto",
    "Industry",
    "Arcadia",
    "Anaheim",
    "Santa Fe Springs",
    "Carson",
    "Burbank",
    "Los Angeles",
    "Diamond Bar Rsf",
    "Oceanside",
    "Otay Mesa",
    "San Diego",
    "Vernon",
    "Commerce",
    "Pico Rivera",
    "City Of Industry",
)


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


SOCAL_LIST = ", ".join(f"'{h}'" for h in SOCAL_HUBS)

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
    ({region_expr("b.actual_induction_hub_state")}) AS actual_hub_region,
    IF(b.actual_induction_hub_name IN ({SOCAL_LIST}), 1, 0) AS is_socal_actual
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
),

pathed AS (
  SELECT
    f.*,
    CASE
      WHEN f.candidate_bucket = 'direct' THEN 'midwest_direct'
      WHEN f.is_socal_actual = 1 AND f.candidate_bucket != 'direct' THEN 'socal_nondirect'
      WHEN f.actual_hub_region = 'Midwest' AND f.candidate_bucket != 'direct' THEN 'midwest_other_candidate'
      ELSE 'other'
    END AS path
  FROM flagged AS f
  WHERE f.origin_region = 'West Coast'
    AND f.dest_region = 'Midwest'
)

SELECT
  path,
  candidate_bucket,
  CAST(msbd_week AS STRING) AS msbd_week,
  supplier_id,
  su_name,
  parent_suid,
  parent_su_name,
  sto,
  assigned_induction_hub_name,
  actual_induction_hub_name,
  destination_state AS dest_state,
  COUNT(DISTINCT ops) AS vol,
  AVG(inducted_on_time_or_early) AS ifr,
  AVG(delivery_rel) AS delivery_rel,
  AVG(o2d_stated) AS avg_o2d_stated,
  AVG(o2d_actual) AS avg_o2d_actual,
  AVG(direct_gain) AS avg_direct_gain,
  AVG(distance_actualhub_customer) AS avg_mi_actual_to_cust,
  AVG(distance_assignedhub_customer) AS avg_mi_assigned_to_cust
FROM pathed
WHERE path IN ('midwest_direct', 'socal_nondirect')
GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11
"""


def wavg(df: pd.DataFrame, col: str, wcol: str = "vol") -> float:
    w, v = df[wcol], df[col]
    m = v.notna() & w.notna() & (w > 0)
    if not m.any() or w[m].sum() == 0:
        return float("nan")
    return float((v[m] * w[m]).sum() / w[m].sum())


def rollup(g: pd.DataFrame) -> pd.Series:
    stated = wavg(g, "avg_o2d_stated")
    actual = wavg(g, "avg_o2d_actual")
    return pd.Series(
        {
            "vol": float(g["vol"].sum()),
            "ifr": wavg(g, "ifr"),
            "delivery_rel": wavg(g, "delivery_rel"),
            "avg_o2d_stated": stated,
            "avg_o2d_actual": actual,
            "o2d_gap": (actual - stated) if pd.notna(actual) and pd.notna(stated) else float("nan"),
            "avg_direct_gain": wavg(g, "avg_direct_gain"),
            "avg_mi_actual_to_cust": wavg(g, "avg_mi_actual_to_cust"),
            "suppliers": int(g["supplier_id"].nunique()),
        }
    )


def fmt_pct(x) -> str:
    return "—" if pd.isna(x) else f"{x:.1%}"


def fmt_num(x, d=2) -> str:
    return "—" if pd.isna(x) else f"{x:.{d}f}"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print("Querying midwest_direct vs socal_nondirect...")
    df = query_df(SQL)
    df["msbd_week"] = pd.to_datetime(df["msbd_week"]).dt.strftime("%Y-%m-%d")
    print(f"Rows: {len(df):,}")
    print(df.groupby("path")["vol"].sum())

    # Weekly path compare
    weekly = (
        df.groupby(["msbd_week", "path"], dropna=False)
        .apply(rollup, include_groups=False)
        .reset_index()
        .sort_values(["msbd_week", "path"])
    )
    weekly.to_csv(OUTPUT_DIR / "wc_midwest_direct_vs_socal_weekly.csv", index=False)

    # Pivot for side-by-side
    metrics = ["vol", "ifr", "delivery_rel", "avg_o2d_stated", "avg_o2d_actual", "o2d_gap", "avg_mi_actual_to_cust", "suppliers"]
    piv_parts = []
    for m in metrics:
        p = weekly.pivot(index="msbd_week", columns="path", values=m)
        p.columns = [f"{m}__{c}" for c in p.columns]
        piv_parts.append(p)
    side = pd.concat(piv_parts, axis=1).reset_index()
    if "vol__midwest_direct" in side.columns and "vol__socal_nondirect" in side.columns:
        side["direct_share"] = side["vol__midwest_direct"] / (
            side["vol__midwest_direct"].fillna(0) + side["vol__socal_nondirect"].fillna(0)
        )
        side["ifr_delta_direct_minus_socal"] = side.get("ifr__midwest_direct") - side.get("ifr__socal_nondirect")
        side["del_delta_direct_minus_socal"] = side.get("delivery_rel__midwest_direct") - side.get(
            "delivery_rel__socal_nondirect"
        )
        side["o2d_actual_delta_direct_minus_socal"] = side.get("avg_o2d_actual__midwest_direct") - side.get(
            "avg_o2d_actual__socal_nondirect"
        )
        side["o2d_stated_delta_direct_minus_socal"] = side.get("avg_o2d_stated__midwest_direct") - side.get(
            "avg_o2d_stated__socal_nondirect"
        )
    side.to_csv(OUTPUT_DIR / "wc_midwest_direct_vs_socal_weekly_sidebyside.csv", index=False)

    print("\n=== Weekly side-by-side (key cols) ===")
    cols = [
        c
        for c in [
            "msbd_week",
            "vol__midwest_direct",
            "vol__socal_nondirect",
            "ifr__midwest_direct",
            "ifr__socal_nondirect",
            "delivery_rel__midwest_direct",
            "delivery_rel__socal_nondirect",
            "avg_o2d_stated__midwest_direct",
            "avg_o2d_stated__socal_nondirect",
            "avg_o2d_actual__midwest_direct",
            "avg_o2d_actual__socal_nondirect",
            "o2d_actual_delta_direct_minus_socal",
        ]
        if c in side.columns
    ]
    print(side[cols].to_string(index=False))

    # Period focus
    focus_weeks = {
        "peak_memorial": PEAK_WEEK,
        "july4": JULY4_WEEK,
        "july5": JULY5_WEEK,
    }
    period_rows = []
    for label, wk in focus_weeks.items():
        for path in ["midwest_direct", "socal_nondirect"]:
            sub = df[(df["msbd_week"] == wk) & (df["path"] == path)]
            if sub.empty:
                continue
            r = rollup(sub)
            r["period"] = label
            r["msbd_week"] = wk
            r["path"] = path
            period_rows.append(r)
    # Full-window totals
    for path in ["midwest_direct", "socal_nondirect"]:
        sub = df[df["path"] == path]
        r = rollup(sub)
        r["period"] = "all_weeks_may_aug"
        r["msbd_week"] = "all"
        r["path"] = path
        period_rows.append(r)
    period = pd.DataFrame(period_rows)
    period.to_csv(OUTPUT_DIR / "wc_midwest_direct_vs_socal_period.csv", index=False)

    # Supplier-level: peak week both paths + july4 socal (main nondirect week)
    def supplier_path(g: pd.DataFrame, label: str) -> pd.DataFrame:
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
                    f"del_{label}": wavg(sg, "delivery_rel"),
                    f"o2d_stated_{label}": stated,
                    f"o2d_actual_{label}": actual,
                    f"o2d_gap_{label}": (actual - stated) if pd.notna(actual) and pd.notna(stated) else float("nan"),
                    f"mi_{label}": wavg(sg, "avg_mi_actual_to_cust"),
                    f"hub_{label}": (
                        sg.groupby("actual_induction_hub_name")["vol"].sum().idxmax()
                        if sg["actual_induction_hub_name"].notna().any()
                        else None
                    ),
                }
            )
        return pd.DataFrame(rows)

    peak_d = supplier_path(df[(df.msbd_week == PEAK_WEEK) & (df.path == "midwest_direct")], "direct_peak")
    peak_s = supplier_path(df[(df.msbd_week == PEAK_WEEK) & (df.path == "socal_nondirect")], "socal_peak")
    j4_s = supplier_path(df[(df.msbd_week == JULY4_WEEK) & (df.path == "socal_nondirect")], "socal_july4")
    j4_d = supplier_path(df[(df.msbd_week == JULY4_WEEK) & (df.path == "midwest_direct")], "direct_july4")
    j5_s = supplier_path(df[(df.msbd_week == JULY5_WEEK) & (df.path == "socal_nondirect")], "socal_july5")

    # Peak: suppliers with directs vs SoCal nondirect peers (same week)
    peak_merge = peak_d.merge(
        peak_s, on=["supplier_id", "su_name", "parent_suid", "parent_su_name", "sto"], how="outer"
    )
    peak_merge["has_both_peak"] = peak_merge["vol_direct_peak"].fillna(0).gt(0) & peak_merge[
        "vol_socal_peak"
    ].fillna(0).gt(0)
    peak_merge["ifr_delta"] = peak_merge["ifr_direct_peak"] - peak_merge["ifr_socal_peak"]
    peak_merge["del_delta"] = peak_merge["del_direct_peak"] - peak_merge["del_socal_peak"]
    peak_merge["o2d_actual_delta"] = peak_merge["o2d_actual_direct_peak"] - peak_merge["o2d_actual_socal_peak"]
    peak_merge = peak_merge.sort_values("vol_direct_peak", ascending=False, na_position="last")
    peak_merge.to_csv(OUTPUT_DIR / "wc_midwest_direct_vs_socal_suppliers_peak.csv", index=False)

    # July 4 SoCal nondirect scorecard (the "normal" path that week) vs peak directs for same suppliers
    j4_compare = j4_s.merge(
        peak_d, on=["supplier_id", "su_name", "parent_suid", "parent_su_name", "sto"], how="left"
    )
    j4_compare = j4_compare.merge(
        j4_d, on=["supplier_id", "su_name", "parent_suid", "parent_su_name", "sto"], how="left"
    )
    j4_compare["o2d_actual_delta_july4socal_vs_peakdirect"] = (
        j4_compare["o2d_actual_socal_july4"] - j4_compare["o2d_actual_direct_peak"]
    )
    j4_compare["ifr_delta_july4socal_vs_peakdirect"] = (
        j4_compare["ifr_socal_july4"] - j4_compare["ifr_direct_peak"]
    )
    j4_compare = j4_compare.sort_values("vol_socal_july4", ascending=False)
    j4_compare.to_csv(OUTPUT_DIR / "wc_midwest_july4_socal_vs_peak_direct_suppliers.csv", index=False)

    both = peak_merge[peak_merge["has_both_peak"]].copy()
    both = both[(both["vol_direct_peak"] >= 20) & (both["vol_socal_peak"] >= 20)]
    print(f"\nSuppliers with BOTH paths in peak week (≥20 each): {len(both)}")
    if len(both):
        print(
            both.head(15)[
                [
                    "supplier_id",
                    "su_name",
                    "vol_direct_peak",
                    "ifr_direct_peak",
                    "o2d_actual_direct_peak",
                    "vol_socal_peak",
                    "ifr_socal_peak",
                    "o2d_actual_socal_peak",
                    "o2d_actual_delta",
                    "ifr_delta",
                ]
            ].to_string(index=False)
        )

    print("\nTop July4 SoCal nondirect suppliers:")
    print(
        j4_compare.head(15)[
            [
                "supplier_id",
                "su_name",
                "vol_socal_july4",
                "ifr_socal_july4",
                "del_socal_july4",
                "o2d_stated_socal_july4",
                "o2d_actual_socal_july4",
                "vol_direct_peak",
                "o2d_actual_direct_peak",
                "o2d_actual_delta_july4socal_vs_peakdirect",
            ]
        ].to_string(index=False)
    )

    # Aggregate: July4 SoCal vs Peak Direct (network-level)
    print("\n=== Headline period compare ===")
    print(period.to_string(index=False))

    with pd.ExcelWriter(OUTPUT_DIR / "wc_midwest_direct_vs_socal_compare.xlsx", engine="openpyxl") as xw:
        period.to_excel(xw, sheet_name="period_summary", index=False)
        side.to_excel(xw, sheet_name="weekly_sidebyside", index=False)
        weekly.to_excel(xw, sheet_name="weekly_long", index=False)
        peak_merge.head(5000).to_excel(xw, sheet_name="suppliers_peak", index=False)
        both.to_excel(xw, sheet_name="suppliers_both_paths_peak", index=False)
        j4_compare.head(5000).to_excel(xw, sheet_name="july4_socal_vs_peak_direct", index=False)

    # Markdown
    md = []
    md.append("# Midwest dest: directs vs SoCal-induct non-directs")
    md.append("")
    md.append("Same destination region (**Midwest**), West Coast assigned origin.")
    md.append("")
    md.append("| Path | Definition |")
    md.append("|------|------------|")
    md.append("| `midwest_direct` | Classified **direct** bucket (gain ≥ 0.4) |")
    md.append(
        "| `socal_nondirect` | Actual induction at **SoCal** hub (Chino/Rialto/Industry/LA/…; not NorCal), **not** classified direct |"
    )
    md.append("")
    md.append("Metrics: IFR, delivery_rel, O2D stated vs actual. Timebase: `msbd_su_week`.")
    md.append("")
    md.append("## Period totals")
    md.append("")
    md.append("| Period | Path | Vol | Suppliers | IFR | Del Rel | O2D stated | O2D actual | Gap | Mi to cust |")
    md.append("|--------|------|-----|-----------|-----|---------|------------|------------|-----|------------|")
    for _, r in period.iterrows():
        md.append(
            f"| {r['period']} | {r['path']} | {r['vol']:,.0f} | {r['suppliers']:.0f} | "
            f"{fmt_pct(r['ifr'])} | {fmt_pct(r['delivery_rel'])} | "
            f"{fmt_num(r['avg_o2d_stated'])} | {fmt_num(r['avg_o2d_actual'])} | "
            f"{r['o2d_gap']:+.2f} | {fmt_num(r['avg_mi_actual_to_cust'], 0)} |"
        )
    md.append("")

    # Headline deltas for peak and july4
    def path_row(period_name, path):
        sub = period[(period["period"] == period_name) & (period["path"] == path)]
        return sub.iloc[0] if len(sub) else None

    md.append("## Headline: peak Memorial Day week")
    md.append("")
    d = path_row("peak_memorial", "midwest_direct")
    s = path_row("peak_memorial", "socal_nondirect")
    if d is not None and s is not None:
        md.append(
            f"- Direct: **{d['vol']:,.0f}** ops — IFR {d['ifr']:.1%}, Del {d['delivery_rel']:.1%}, "
            f"O2D {d['avg_o2d_stated']:.2f}→{d['avg_o2d_actual']:.2f} ({d['o2d_gap']:+.2f}), "
            f"~{d['avg_mi_actual_to_cust']:.0f} mi after induction"
        )
        md.append(
            f"- SoCal nondirect: **{s['vol']:,.0f}** ops — IFR {s['ifr']:.1%}, Del {s['delivery_rel']:.1%}, "
            f"O2D {s['avg_o2d_stated']:.2f}→{s['avg_o2d_actual']:.2f} ({s['o2d_gap']:+.2f}), "
            f"~{s['avg_mi_actual_to_cust']:.0f} mi after induction"
        )
        md.append(
            f"- **Delta (direct − SoCal):** IFR {(d['ifr']-s['ifr'])*100:+.1f} pp, "
            f"Del {(d['delivery_rel']-s['delivery_rel'])*100:+.1f} pp, "
            f"O2D actual {d['avg_o2d_actual']-s['avg_o2d_actual']:+.2f}d"
        )
    md.append("")
    md.append("## Headline: July 4 week (mostly SoCal long-haul)")
    md.append("")
    d4 = path_row("july4", "midwest_direct")
    s4 = path_row("july4", "socal_nondirect")
    if d4 is not None:
        md.append(
            f"- Direct (thin): **{d4['vol']:,.0f}** — IFR {d4['ifr']:.1%}, Del {d4['delivery_rel']:.1%}, "
            f"O2D {d4['avg_o2d_stated']:.2f}→{d4['avg_o2d_actual']:.2f}"
        )
    if s4 is not None:
        md.append(
            f"- SoCal nondirect: **{s4['vol']:,.0f}** — IFR {s4['ifr']:.1%}, Del {s4['delivery_rel']:.1%}, "
            f"O2D {s4['avg_o2d_stated']:.2f}→{s4['avg_o2d_actual']:.2f} ({s4['o2d_gap']:+.2f})"
        )
    if d is not None and s4 is not None:
        md.append("")
        md.append(
            f"**Cross-period:** July 4 SoCal nondirect O2D actual **{s4['avg_o2d_actual']:.2f}d** vs "
            f"Memorial Day direct **{d['avg_o2d_actual']:.2f}d** "
            f"({s4['avg_o2d_actual']-d['avg_o2d_actual']:+.2f}d). "
            f"IFR {s4['ifr']:.1%} vs direct peak {d['ifr']:.1%}."
        )
    md.append("")
    md.append("## Weekly side-by-side")
    md.append("")
    md.append(
        "| Week | Direct vol | SoCal vol | Direct IFR | SoCal IFR | Direct Del | SoCal Del | Direct O2D act | SoCal O2D act | O2D Δ |"
    )
    md.append(
        "|------|------------|-----------|------------|-----------|------------|-----------|----------------|---------------|-------|"
    )
    for _, r in side.iterrows():
        tag = ""
        if r["msbd_week"] == PEAK_WEEK:
            tag = " ← peak"
        elif r["msbd_week"] == JULY4_WEEK:
            tag = " ← July4"
        elif r["msbd_week"] == JULY5_WEEK:
            tag = " ← July5"
        md.append(
            f"| {r['msbd_week']}{tag} | "
            f"{fmt_num(r.get('vol__midwest_direct'), 0)} | {fmt_num(r.get('vol__socal_nondirect'), 0)} | "
            f"{fmt_pct(r.get('ifr__midwest_direct'))} | {fmt_pct(r.get('ifr__socal_nondirect'))} | "
            f"{fmt_pct(r.get('delivery_rel__midwest_direct'))} | {fmt_pct(r.get('delivery_rel__socal_nondirect'))} | "
            f"{fmt_num(r.get('avg_o2d_actual__midwest_direct'))} | {fmt_num(r.get('avg_o2d_actual__socal_nondirect'))} | "
            f"{fmt_num(r.get('o2d_actual_delta_direct_minus_socal'))} |"
        )
    md.append("")
    md.append("## Suppliers with both paths in peak week (≥20 each)")
    md.append("")
    if both.empty:
        md.append("None at this threshold.")
    else:
        md.append(
            "| SUID | Supplier | Direct vol | Direct IFR | Direct O2D | SoCal vol | SoCal IFR | SoCal O2D | O2D Δ | IFR Δ |"
        )
        md.append(
            "|------|----------|------------|------------|------------|-----------|-----------|-----------|-------|-------|"
        )
        for _, r in both.head(20).iterrows():
            md.append(
                f"| {int(r['supplier_id'])} | {r['su_name']} | "
                f"{r['vol_direct_peak']:,.0f} | {fmt_pct(r['ifr_direct_peak'])} | {fmt_num(r['o2d_actual_direct_peak'])} | "
                f"{r['vol_socal_peak']:,.0f} | {fmt_pct(r['ifr_socal_peak'])} | {fmt_num(r['o2d_actual_socal_peak'])} | "
                f"{r['o2d_actual_delta']:+.2f} | {r['ifr_delta']*100:+.1f} pp |"
            )
    md.append("")
    md.append("## Top July 4 SoCal nondirect suppliers (vs their Memorial Day direct, if any)")
    md.append("")
    md.append(
        "| SUID | Supplier | July4 SoCal vol | IFR | Del | O2D stated | O2D actual | Peak direct vol | Peak direct O2D | O2D Δ |"
    )
    md.append(
        "|------|----------|-----------------|-----|-----|------------|------------|-----------------|-----------------|-------|"
    )
    for _, r in j4_compare.head(20).iterrows():
        md.append(
            f"| {int(r['supplier_id'])} | {r['su_name']} | {r['vol_socal_july4']:,.0f} | "
            f"{fmt_pct(r['ifr_socal_july4'])} | {fmt_pct(r['del_socal_july4'])} | "
            f"{fmt_num(r['o2d_stated_socal_july4'])} | {fmt_num(r['o2d_actual_socal_july4'])} | "
            f"{fmt_num(r.get('vol_direct_peak'), 0)} | {fmt_num(r.get('o2d_actual_direct_peak'))} | "
            f"{fmt_num(r.get('o2d_actual_delta_july4socal_vs_peakdirect'))} |"
        )
    md.append("")
    md.append("## Files")
    md.append("")
    md.append("| File | Contents |")
    md.append("|------|----------|")
    md.append("| `wc_midwest_direct_vs_socal_compare.xlsx` | All tabs |")
    md.append("| `wc_midwest_direct_vs_socal_weekly_sidebyside.csv` | Weekly metrics |")
    md.append("| `wc_midwest_direct_vs_socal_suppliers_peak.csv` | Peak week supplier paths |")
    md.append("| `scripts/run_wc_midwest_direct_vs_socal.py` | Re-run |")

    path = OUTPUT_DIR / "wc_midwest_direct_vs_socal_compare.md"
    path.write_text("\n".join(md) + "\n")
    print(f"\nWrote {path}")


if __name__ == "__main__":
    main()
