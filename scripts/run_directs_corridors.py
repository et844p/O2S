#!/usr/bin/env python3
"""Map where directs are built: origin region → destination region/state.

Isolates the top corridor and compares suppliers on that volume.
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

def region_expr(col: str) -> str:
    """Map a state column to a logistics region."""
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
    o.assigned_constrained_market,
    DATE_TRUNC(o.promised_delivery_end_range_date_at_order, WEEK(SUNDAY)) AS week_start,
    CASE
      WHEN o.assignedhub_notequal_actualhub_flag = 1
        AND COALESCE(o.distance_assignedhub_customer, 0) >= 400
        AND COALESCE(o.distance_assignedhub_actualhub, 0) >= 200 THEN 1
      ELSE 0
    END AS is_candidate
  FROM `wf-gcp-us-ae-global-tnd-prod.speed_and_reliability.HVE_perf_Monitoring` AS o
  WHERE o.fulfillment_type = 'DS'
    AND o.promised_delivery_end_range_date_at_order
        >= DATE_SUB(CURRENT_DATE(), INTERVAL 10 WEEK)
    AND o.promised_delivery_end_range_date_at_order < CURRENT_DATE()
),

parent_states AS (
  SELECT DISTINCT parent_suid, state_name AS warehouse_state
  FROM `wf-gcp-us-ae-global-tnd-prod.speed_and_reliability.HVE_perf_Monitoring`
  WHERE fulfillment_type = 'DS'
    AND parent_suid IS NOT NULL
    AND state_name IS NOT NULL
    AND promised_delivery_end_range_date_at_order
        >= DATE_SUB(CURRENT_DATE(), INTERVAL 10 WEEK)
    AND promised_delivery_end_range_date_at_order < CURRENT_DATE()
),

enriched AS (
  SELECT
    b.*,
    IF(
      ps.warehouse_state IS NOT NULL
      AND b.actual_induction_hub_state IS NOT NULL
      AND b.actual_induction_hub_state != b.own_state,
      1, 0
    ) AS is_sibling_state
  FROM base AS b
  LEFT JOIN parent_states AS ps
    ON b.parent_suid = ps.parent_suid
   AND b.actual_induction_hub_state = ps.warehouse_state
),

supplier_meta AS (
  SELECT
    supplier_id,
    COUNT(DISTINCT ops) AS total_vol,
    COUNT(DISTINCT week_start) AS weeks_with_vol
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
     AND COUNT(DISTINCT e.week_start)
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

with_regions AS (
  SELECT
    f.*,
    ({region_expr("f.assigned_station_state")}) AS origin_region,
    ({region_expr("f.actual_induction_hub_state")}) AS actual_hub_region,
    ({region_expr("f.destination_state")}) AS dest_region
  FROM flagged AS f
)

SELECT
  candidate_bucket,
  origin_region,
  assigned_station_state AS origin_state,
  actual_hub_region,
  actual_induction_hub_state AS actual_hub_state,
  dest_region,
  destination_state AS dest_state,
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
  AVG(direct_gain) AS avg_direct_gain,
  AVG(o2d_stated) AS avg_o2d_stated,
  AVG(o2d_actual) AS avg_o2d_actual,
  AVG(distance_actualhub_customer) AS avg_mi_actual_to_cust,
  AVG(distance_assignedhub_customer) AS avg_mi_assigned_to_cust,
  AVG(CAST(assigned_constrained_market AS FLOAT64)) AS pct_constrained
FROM with_regions
WHERE candidate_bucket = 'direct'
GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14
"""


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print("Querying direct corridors (pdd_10w, DS)...")
    df = query_df(SQL)
    print(f"Rows: {len(df):,}")

    grain_path = OUTPUT_DIR / "directs_corridors_supplier_grain.csv"
    df.to_csv(grain_path, index=False)

    total_direct = df["vol"].sum()

    # Region → region corridors
    rr = (
        df.groupby(["origin_region", "dest_region"], dropna=False)
        .agg(
            vol=("vol", "sum"),
            suppliers=("supplier_id", "nunique"),
            ifr=("ifr", lambda s: (s * df.loc[s.index, "vol"]).sum() / df.loc[s.index, "vol"].sum()),
            delivery_rel=(
                "delivery_rel",
                lambda s: (s * df.loc[s.index, "vol"]).sum() / df.loc[s.index, "vol"].sum(),
            ),
            avg_direct_gain=(
                "avg_direct_gain",
                lambda s: (s * df.loc[s.index, "vol"]).sum() / df.loc[s.index, "vol"].sum(),
            ),
            avg_o2d_actual=(
                "avg_o2d_actual",
                lambda s: (s * df.loc[s.index, "vol"]).sum() / df.loc[s.index, "vol"].sum(),
            ),
            avg_mi_actual_to_cust=(
                "avg_mi_actual_to_cust",
                lambda s: (s * df.loc[s.index, "vol"]).sum() / df.loc[s.index, "vol"].sum(),
            ),
        )
        .reset_index()
    )
    rr["pct_of_directs"] = rr["vol"] / total_direct
    rr = rr.sort_values("vol", ascending=False)
    rr.to_csv(OUTPUT_DIR / "directs_corridors_region_to_region.csv", index=False)

    # Origin region → dest state (top destinations per origin)
    rs = (
        df.groupby(["origin_region", "dest_state"], dropna=False)
        .agg(vol=("vol", "sum"), suppliers=("supplier_id", "nunique"))
        .reset_index()
        .sort_values("vol", ascending=False)
    )
    rs["pct_of_directs"] = rs["vol"] / total_direct
    rs.to_csv(OUTPUT_DIR / "directs_corridors_region_to_state.csv", index=False)

    # Origin state → dest region
    sr = (
        df.groupby(["origin_state", "dest_region"], dropna=False)
        .agg(vol=("vol", "sum"), suppliers=("supplier_id", "nunique"))
        .reset_index()
        .sort_values("vol", ascending=False)
    )
    sr["pct_of_directs"] = sr["vol"] / total_direct
    sr.to_csv(OUTPUT_DIR / "directs_corridors_state_to_region.csv", index=False)

    # Assigned hub → actual hub region (where they induct)
    ah = (
        df.groupby(["origin_region", "actual_hub_region"], dropna=False)
        .agg(vol=("vol", "sum"), suppliers=("supplier_id", "nunique"))
        .reset_index()
        .sort_values("vol", ascending=False)
    )
    ah["pct_of_directs"] = ah["vol"] / total_direct
    ah.to_csv(OUTPUT_DIR / "directs_corridors_origin_to_actual_hub_region.csv", index=False)

    # Top corridor = max origin_region → dest_region
    top = rr.iloc[0]
    top_origin, top_dest = top["origin_region"], top["dest_region"]
    print(f"\nTop corridor: {top_origin} → {top_dest} ({top['vol']:,.0f} ops, {top['pct_of_directs']:.1%} of directs)")

    # Also show cumulative top 5
    print("\nTop 10 origin→dest region corridors:")
    print(
        rr.head(10)
        .assign(pct=lambda x: (x["pct_of_directs"] * 100).round(1).astype(str) + "%")
        [["origin_region", "dest_region", "vol", "pct", "suppliers"]]
        .to_string(index=False)
    )

    corridor = df[(df["origin_region"] == top_origin) & (df["dest_region"] == top_dest)].copy()

    # Supplier comparison on top corridor
    # Also get each supplier's non-direct / local volume on same dest region for baseline
    # For now compare suppliers within the corridor directs slice
    def wavg(g, col):
        w = g["vol"]
        v = g[col]
        mask = v.notna() & w.notna()
        if mask.sum() == 0 or w[mask].sum() == 0:
            return float("nan")
        return float((v[mask] * w[mask]).sum() / w[mask].sum())

    supplier = (
        corridor.groupby(["supplier_id", "su_name", "parent_suid", "parent_su_name", "sto"], dropna=False)
        .apply(
            lambda g: pd.Series(
                {
                    "vol": g["vol"].sum(),
                    "ifr": wavg(g, "ifr"),
                    "delivery_rel": wavg(g, "delivery_rel"),
                    "avg_direct_gain": wavg(g, "avg_direct_gain"),
                    "avg_o2d_stated": wavg(g, "avg_o2d_stated"),
                    "avg_o2d_actual": wavg(g, "avg_o2d_actual"),
                    "avg_mi_actual_to_cust": wavg(g, "avg_mi_actual_to_cust"),
                    "avg_mi_assigned_to_cust": wavg(g, "avg_mi_assigned_to_cust"),
                    "pct_constrained": wavg(g, "pct_constrained"),
                    "top_assigned_hub": g.groupby("assigned_induction_hub_name")["vol"].sum().idxmax()
                    if g["assigned_induction_hub_name"].notna().any()
                    else None,
                    "top_actual_hub": g.groupby("actual_induction_hub_name")["vol"].sum().idxmax()
                    if g["actual_induction_hub_name"].notna().any()
                    else None,
                }
            ),
            include_groups=False,
        )
        .reset_index()
        .sort_values("vol", ascending=False)
    )
    supplier["pct_of_corridor"] = supplier["vol"] / corridor["vol"].sum()
    supplier.to_csv(
        OUTPUT_DIR / f"directs_corridor_{_slug(top_origin)}_to_{_slug(top_dest)}_suppliers.csv",
        index=False,
    )

    # Dest-state mix within top corridor
    dest_mix = (
        corridor.groupby("dest_state", dropna=False)
        .agg(vol=("vol", "sum"), suppliers=("supplier_id", "nunique"))
        .reset_index()
        .sort_values("vol", ascending=False)
    )
    dest_mix["pct_of_corridor"] = dest_mix["vol"] / corridor["vol"].sum()
    dest_mix.to_csv(
        OUTPUT_DIR / f"directs_corridor_{_slug(top_origin)}_to_{_slug(top_dest)}_dest_states.csv",
        index=False,
    )

    # Write markdown summary
    md = []
    md.append("# Directs corridors (PDD last 10w, DS)")
    md.append("")
    md.append(f"Total direct volume: **{total_direct:,.0f}** ops")
    md.append("")
    md.append("## Top origin → destination region corridors")
    md.append("")
    md.append("| Origin | Dest | Vol | % of directs | Suppliers | IFR | Del Rel | Gain | O2D act | Mi to cust |")
    md.append("|--------|------|-----|--------------|-----------|-----|---------|------|---------|------------|")
    for _, r in rr.head(15).iterrows():
        md.append(
            f"| {r['origin_region']} | {r['dest_region']} | {r['vol']:,.0f} | "
            f"{r['pct_of_directs']:.1%} | {r['suppliers']:.0f} | "
            f"{r['ifr']:.1%} | {r['delivery_rel']:.1%} | {r['avg_direct_gain']:.2f} | "
            f"{r['avg_o2d_actual']:.2f} | {r['avg_mi_actual_to_cust']:.0f} |"
        )
    md.append("")
    md.append(f"## Isolate: {top_origin} → {top_dest}")
    md.append("")
    md.append(
        f"**{top['vol']:,.0f}** ops ({top['pct_of_directs']:.1%} of all directs), "
        f"**{top['suppliers']:.0f}** suppliers"
    )
    md.append("")
    md.append("### Destination states in this corridor")
    md.append("")
    md.append("| Dest state | Vol | % of corridor | Suppliers |")
    md.append("|------------|-----|---------------|-----------|")
    for _, r in dest_mix.head(15).iterrows():
        md.append(
            f"| {r['dest_state']} | {r['vol']:,.0f} | {r['pct_of_corridor']:.1%} | {r['suppliers']:.0f} |"
        )
    md.append("")
    md.append("### Top suppliers on this corridor (by direct vol)")
    md.append("")
    md.append(
        "| SUID | Supplier | STO | Vol | % corridor | IFR | Del Rel | Gain | O2D act | Top actual hub |"
    )
    md.append(
        "|------|----------|-----|-----|------------|-----|---------|------|---------|----------------|"
    )
    for _, r in supplier.head(20).iterrows():
        md.append(
            f"| {int(r['supplier_id'])} | {r['su_name']} | {r['sto']} | "
            f"{r['vol']:,.0f} | {r['pct_of_corridor']:.1%} | "
            f"{r['ifr']:.1%} | {r['delivery_rel']:.1%} | {r['avg_direct_gain']:.2f} | "
            f"{r['avg_o2d_actual']:.2f} | {r['top_actual_hub']} |"
        )
    md.append("")
    md.append("### Origin → actual hub region (where directs induct)")
    md.append("")
    md.append("| Origin | Actual hub region | Vol | % of directs | Suppliers |")
    md.append("|--------|-------------------|-----|--------------|-----------|")
    for _, r in ah.head(15).iterrows():
        md.append(
            f"| {r['origin_region']} | {r['actual_hub_region']} | {r['vol']:,.0f} | "
            f"{r['pct_of_directs']:.1%} | {r['suppliers']:.0f} |"
        )

    summary_path = OUTPUT_DIR / "directs_corridors_summary.md"
    summary_path.write_text("\n".join(md) + "\n")
    print(f"\nWrote {summary_path}")
    print(f"Top corridor suppliers: {len(supplier)}")
    print(supplier.head(10).to_string(index=False))


def _slug(s: str) -> str:
    return str(s).lower().replace(" ", "_").replace("/", "_")


if __name__ == "__main__":
    main()
