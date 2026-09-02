#!/usr/bin/env python3
"""Last 3 weeks delivered DS vol: % misship / ghost / other (closer vs farther).

Universe: delivery_date in [today-3w, today), fulfillment_type = 'DS'.

Buckets (exclusive, priority):
  misshipping     — wrong hub + sibling WH state under same parent_suid
  ghost           — wrong hub + >=200mi from assigned WH + NOT closer to customer
  other_closer    — wrong hub, not misship/ghost, actual closer to customer than assigned
  other_farther   — wrong hub, not misship/ghost, farther/equal, AND >=200 from assigned
  local_wrong_hub — wrong hub, <200 from assigned, not closer (local hub noise)
  aligned         — not wrong-hub
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

SQL_NETWORK = ROOT / "sql" / "delivered_3w_misship_ghost_other.sql"
OUTPUT_DIR = ROOT / "output" / "directs"

BUCKET_ORDER = [
    "misshipping",
    "ghost",
    "other_closer",
    "other_farther",
    "local_wrong_hub",
    "aligned",
]

FOCUS_BUCKETS = ["misshipping", "ghost", "other_closer", "other_farther"]

DETAIL_SQL = r"""
WITH params AS (
  SELECT CURRENT_DATE() AS as_of
),
window_bounds AS (
  SELECT
    DATE_SUB((SELECT as_of FROM params), INTERVAL 3 WEEK) AS window_start,
    (SELECT as_of FROM params) AS window_end
),
parent_states AS (
  SELECT DISTINCT
    o.parent_suid,
    o.state_name AS warehouse_state
  FROM `wf-gcp-us-ae-global-tnd-prod.speed_and_reliability.HVE_perf_Monitoring` AS o
  CROSS JOIN window_bounds AS w
  WHERE o.fulfillment_type = 'DS'
    AND o.parent_suid IS NOT NULL
    AND o.state_name IS NOT NULL
    AND DATE(o.delivery_date) >= w.window_start
    AND DATE(o.delivery_date) < w.window_end
),
base AS (
  SELECT
    o.supplier_id,
    o.su_name,
    o.parent_suid,
    o.parent_su_name,
    o.sto,
    o.state_name AS own_state,
    o.ops,
    o.actual_induction_hub_name,
    o.actual_induction_hub_state,
    o.assigned_induction_hub_name,
    o.distance_assignedhub_customer,
    o.distance_actualhub_customer,
    o.distance_assignedhub_actualhub,
    o.inducted_on_time_or_early,
    o.delivery_rel,
    CASE WHEN o.assignedhub_notequal_actualhub_flag = 1 THEN 1 ELSE 0 END AS is_wrong_hub,
    CASE
      WHEN ps.warehouse_state IS NOT NULL
        AND o.actual_induction_hub_state IS NOT NULL
        AND o.actual_induction_hub_state != o.state_name
        THEN 1 ELSE 0
    END AS is_sibling_state,
    CASE
      WHEN COALESCE(o.distance_actualhub_customer, 999999)
         < COALESCE(o.distance_assignedhub_customer, 0)
        THEN 1 ELSE 0
    END AS is_closer_to_customer,
    CASE
      WHEN COALESCE(o.distance_assignedhub_actualhub, 0) >= 200 THEN 1 ELSE 0
    END AS is_far_from_assigned_wh
  FROM `wf-gcp-us-ae-global-tnd-prod.speed_and_reliability.HVE_perf_Monitoring` AS o
  CROSS JOIN window_bounds AS w
  LEFT JOIN parent_states AS ps
    ON o.parent_suid = ps.parent_suid
   AND o.actual_induction_hub_state = ps.warehouse_state
  WHERE o.fulfillment_type = 'DS'
    AND o.delivery_date IS NOT NULL
    AND DATE(o.delivery_date) >= w.window_start
    AND DATE(o.delivery_date) < w.window_end
),
classified AS (
  SELECT
    *,
    CASE
      WHEN is_wrong_hub = 1 AND is_sibling_state = 1 THEN 'misshipping'
      WHEN is_wrong_hub = 1
        AND is_far_from_assigned_wh = 1
        AND is_closer_to_customer = 0 THEN 'ghost'
      WHEN is_wrong_hub = 1 AND is_closer_to_customer = 1 THEN 'other_closer'
      WHEN is_wrong_hub = 1 AND is_far_from_assigned_wh = 1 THEN 'other_farther'
      WHEN is_wrong_hub = 1 THEN 'local_wrong_hub'
      ELSE 'aligned'
    END AS vol_bucket
  FROM base
)
"""


def _sto_sql() -> str:
    return (
        DETAIL_SQL
        + """
SELECT
  COALESCE(sto, '(null)') AS sto,
  vol_bucket,
  COUNT(DISTINCT ops) AS vol,
  AVG(inducted_on_time_or_early) AS ifr,
  AVG(delivery_rel) AS delivery_rel
FROM classified
GROUP BY 1, 2
ORDER BY 1, 2
"""
    )


def _supplier_sql() -> str:
    return (
        DETAIL_SQL
        + """
, supplier_tot AS (
  SELECT
    supplier_id,
    ANY_VALUE(su_name) AS su_name,
    ANY_VALUE(parent_suid) AS parent_suid,
    ANY_VALUE(parent_su_name) AS parent_su_name,
    ANY_VALUE(sto) AS sto,
    ANY_VALUE(own_state) AS own_state,
    COUNT(DISTINCT ops) AS total_vol
  FROM classified
  GROUP BY 1
)
SELECT
  t.supplier_id,
  t.su_name,
  t.parent_suid,
  t.parent_su_name,
  t.sto,
  t.own_state,
  t.total_vol,
  COUNT(DISTINCT IF(c.vol_bucket = 'misshipping', c.ops, NULL)) AS misshipping_vol,
  COUNT(DISTINCT IF(c.vol_bucket = 'ghost', c.ops, NULL)) AS ghost_vol,
  COUNT(DISTINCT IF(c.vol_bucket = 'other_closer', c.ops, NULL)) AS other_closer_vol,
  COUNT(DISTINCT IF(c.vol_bucket = 'other_farther', c.ops, NULL)) AS other_farther_vol,
  COUNT(DISTINCT IF(c.vol_bucket = 'local_wrong_hub', c.ops, NULL)) AS local_wrong_hub_vol,
  COUNT(DISTINCT IF(c.vol_bucket = 'aligned', c.ops, NULL)) AS aligned_vol,
  SAFE_DIVIDE(COUNT(DISTINCT IF(c.vol_bucket = 'misshipping', c.ops, NULL)), t.total_vol) AS pct_misshipping,
  SAFE_DIVIDE(COUNT(DISTINCT IF(c.vol_bucket = 'ghost', c.ops, NULL)), t.total_vol) AS pct_ghost,
  SAFE_DIVIDE(COUNT(DISTINCT IF(c.vol_bucket = 'other_closer', c.ops, NULL)), t.total_vol) AS pct_other_closer,
  SAFE_DIVIDE(COUNT(DISTINCT IF(c.vol_bucket = 'other_farther', c.ops, NULL)), t.total_vol) AS pct_other_farther
FROM classified AS c
JOIN supplier_tot AS t USING (supplier_id)
GROUP BY
  t.supplier_id, t.su_name, t.parent_suid, t.parent_su_name,
  t.sto, t.own_state, t.total_vol
HAVING t.total_vol >= 50
ORDER BY (misshipping_vol + ghost_vol) DESC, t.total_vol DESC
"""
    )


def _hub_sql() -> str:
    return (
        DETAIL_SQL
        + """
SELECT
  vol_bucket,
  actual_induction_hub_name,
  actual_induction_hub_state,
  COUNT(DISTINCT ops) AS vol,
  AVG(distance_assignedhub_actualhub) AS avg_dist_assignedhub_actualhub,
  AVG(distance_assignedhub_customer) AS avg_dist_assignedhub_customer,
  AVG(distance_actualhub_customer) AS avg_dist_actualhub_customer
FROM classified
WHERE vol_bucket IN ('misshipping', 'ghost', 'other_closer', 'other_farther')
  AND actual_induction_hub_name IS NOT NULL
GROUP BY 1, 2, 3
QUALIFY ROW_NUMBER() OVER (PARTITION BY vol_bucket ORDER BY COUNT(DISTINCT ops) DESC) <= 15
ORDER BY vol_bucket, vol DESC
"""
    )


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Network summary (last 3w delivered DS)...")
    network = query_df(SQL_NETWORK.read_text())
    network_path = OUTPUT_DIR / "delivered_3w_misship_ghost_other.csv"
    network.to_csv(network_path, index=False)
    print(f"Wrote {network_path}")

    total = int(network["vol"].sum())
    print(f"\nTotal delivered DS vol: {total:,}")
    print(network.to_string(index=False))

    focus = network[network["vol_bucket"].isin(FOCUS_BUCKETS)].copy()
    focus_vol = int(focus["vol"].sum()) if not focus.empty else 0
    print(
        f"\nFocus buckets (misship / ghost / other): "
        f"{focus_vol:,} ({focus_vol / total:.1%} of delivered)"
    )
    for b in FOCUS_BUCKETS:
        row = network[network["vol_bucket"] == b]
        if row.empty:
            print(f"  {b}: 0")
            continue
        r = row.iloc[0]
        print(
            f"  {b}: {int(r['vol']):,} ({r['pct_of_delivered_vol']:.2%} of delivered)"
        )

    local = network[network["vol_bucket"] == "local_wrong_hub"]
    if not local.empty:
        r = local.iloc[0]
        print(
            f"\nNote — local_wrong_hub (<200mi, not closer): "
            f"{int(r['vol']):,} ({r['pct_of_delivered_vol']:.1%} of delivered) "
            f"— mostly local hub / data noise, excluded from focus %"
        )

    print("\nBy STO...")
    sto = query_df(_sto_sql())
    sto_tot = (
        sto.groupby("sto", as_index=False)["vol"]
        .sum()
        .rename(columns={"vol": "sto_total"})
    )
    sto = sto.merge(sto_tot, on="sto")
    sto["pct_of_sto_vol"] = sto["vol"] / sto["sto_total"]
    sto_path = OUTPUT_DIR / "delivered_3w_misship_ghost_other_by_sto.csv"
    sto.to_csv(sto_path, index=False)
    print(f"Wrote {sto_path}")

    # STO focus pivot
    sto_focus = sto[sto["vol_bucket"].isin(FOCUS_BUCKETS)].copy()
    if not sto_focus.empty:
        pivot = sto_focus.pivot_table(
            index="sto", columns="vol_bucket", values="pct_of_sto_vol", aggfunc="sum"
        ).fillna(0)
        for b in FOCUS_BUCKETS:
            if b not in pivot.columns:
                pivot[b] = 0.0
        pivot = pivot[FOCUS_BUCKETS]
        pivot["pct_focus_total"] = pivot.sum(axis=1)
        pivot = pivot.sort_values("pct_focus_total", ascending=False)
        print("\nTop STOs by misship+ghost+other share of STO vol:")
        print((pivot.head(15) * 100).round(2).to_string())

    print("\nBy supplier (vol>=50)...")
    suppliers = query_df(_supplier_sql())
    sup_path = OUTPUT_DIR / "delivered_3w_misship_ghost_other_by_supplier.csv"
    suppliers.to_csv(sup_path, index=False)
    print(f"Wrote {len(suppliers):,} suppliers -> {sup_path}")
    print("\nTop 10 by misship+ghost vol:")
    top = suppliers.head(10)[
        [
            "su_name",
            "sto",
            "total_vol",
            "misshipping_vol",
            "ghost_vol",
            "other_closer_vol",
            "other_farther_vol",
            "pct_misshipping",
            "pct_ghost",
            "pct_other_closer",
        ]
    ]
    print(top.to_string(index=False))

    print("\nTop hubs by focus bucket...")
    hubs = query_df(_hub_sql())
    hub_path = OUTPUT_DIR / "delivered_3w_misship_ghost_other_top_hubs.csv"
    hubs.to_csv(hub_path, index=False)
    print(f"Wrote {hub_path}")

    md_path = OUTPUT_DIR / "delivered_3w_misship_ghost_other.md"
    lines = [
        "# Delivered 3-week misship / ghost / other",
        "",
        f"Window: `{network['window_start'].iloc[0]}` → `{network['window_end'].iloc[0]}` (`delivery_date`)",
        f"Total DS delivered vol: **{total:,}** distinct ops",
        "",
        "## Share of delivered volume",
        "",
        "| Bucket | Vol | % of delivered | IFR | Delivery rel |",
        "|--------|-----|----------------|-----|--------------|",
    ]
    for b in BUCKET_ORDER:
        row = network[network["vol_bucket"] == b]
        if row.empty:
            continue
        r = row.iloc[0]
        ifr = "" if pd.isna(r["ifr"]) else f"{100 * r['ifr']:.1f}%"
        dr = "" if pd.isna(r["delivery_rel"]) else f"{100 * r['delivery_rel']:.1f}%"
        lines.append(
            f"| {b} | {int(r['vol']):,} | {100 * r['pct_of_delivered_vol']:.2f}% | {ifr} | {dr} |"
        )

    lines.extend(
        [
            "",
            "### Focus read",
            "",
            f"- **Misshipping**: { _pct(network, 'misshipping', total) }",
            f"- **Ghost** (far from WH, not closer to customer): { _pct(network, 'ghost', total) }",
            f"- **Other closer** to customer than assigned: { _pct(network, 'other_closer', total) }",
            f"- **Other farther** (≥200mi, residual): { _pct(network, 'other_farther', total) }",
            "",
            "`local_wrong_hub` = wrong hub but <200mi from assigned and not closer — mostly local hub/data noise.",
            "",
            "## Definitions",
            "",
            "- **misshipping**: wrong hub + induction state has another parent warehouse (same `parent_suid`)",
            "- **ghost**: wrong hub + ≥200 mi from assigned WH + actual hub is **not** closer to customer than assigned",
            "- **other_closer**: wrong hub (not misship/ghost); actual hub **closer** to customer than assigned",
            "- **other_farther**: wrong hub (not misship/ghost); ≥200 mi from assigned and not closer (residual; usually empty/ghost)",
            "- **local_wrong_hub**: wrong hub, <200 mi from assigned, not closer",
            "- **aligned**: not wrong-hub",
            "",
            "Closer = `distance_actualhub_customer < distance_assignedhub_customer`.",
            "",
            "## How to run",
            "",
            "```bash",
            "python3 scripts/run_delivered_3w_misship_ghost_other.py",
            "```",
            "",
        ]
    )
    md_path.write_text("\n".join(lines))
    print(f"\nWrote {md_path}")


def _pct(network: pd.DataFrame, bucket: str, total: int) -> str:
    row = network[network["vol_bucket"] == bucket]
    if row.empty:
        return "0 (0%)"
    r = row.iloc[0]
    return f"{int(r['vol']):,} ({100 * r['pct_of_delivered_vol']:.2f}%)"


if __name__ == "__main__":
    main()
