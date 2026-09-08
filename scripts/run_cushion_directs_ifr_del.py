#!/usr/bin/env python3
"""Directs → IFR → cushions, while det delivery reliability still holds?

Uses refreshed det_delivery_date / det_del_rel / det_one_more_day_del_early.

Also computes corrected on-time metrics (delivery_date <= det_delivery_date
and <= det_delivery_date - 1) because stored CASE uses EndDate <= delivery_date,
which flips early vs late vs typical reliability.
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

SQL = """
WITH
base AS (
  SELECT
    o.supplier_id,
    o.su_name,
    o.parent_suid,
    o.parent_su_name,
    o.sto,
    o.ops,
    o.cushion,
    o.state_name AS own_state,
    o.actual_induction_hub_name,
    o.actual_induction_hub_state,
    o.direct_gain,
    o.inducted_on_time_or_early,
    o.delivery_rel,
    o.o2d_actual,
    o.o2d_stated,
    o.delivery_date,
    o.det_delivery_date,
    o.det_del_rel,
    o.det_one_more_day_del_early,
    o.distance_assignedhub_customer,
    o.distance_assignedhub_actualhub,
    COALESCE(o.msbd_su_week, DATE_TRUNC(o.msbd_su, WEEK(SUNDAY))) AS msbd_week,
    CASE
      WHEN o.assignedhub_notequal_actualhub_flag = 1
        AND COALESCE(o.distance_assignedhub_customer, 0) >= 400
        AND COALESCE(o.distance_assignedhub_actualhub, 0) >= 200 THEN 1
      ELSE 0
    END AS is_candidate,
    -- Corrected reliability interpretations (delivery on/before det end)
    IF(o.delivery_date IS NOT NULL AND o.det_delivery_date IS NOT NULL
       AND o.delivery_date <= o.det_delivery_date, 1, 0) AS det_on_time,
    IF(o.delivery_date IS NOT NULL AND o.det_delivery_date IS NOT NULL
       AND o.delivery_date <= DATE_SUB(o.det_delivery_date, INTERVAL 1 DAY), 1, 0) AS det_hits_minus_1_day
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
    END AS candidate_bucket,
    IF(COALESCE(e.cushion, 0) >= 1, 1, 0) AS is_cushioned
  FROM enriched AS e
  LEFT JOIN ghost_hubs AS g
    ON e.supplier_id = g.supplier_id
   AND e.actual_induction_hub_name = g.actual_induction_hub_name
)

SELECT
  supplier_id,
  su_name,
  parent_suid,
  parent_su_name,
  sto,
  is_cushioned,
  ANY_VALUE(cushion) AS cushion_sample,
  candidate_bucket,
  COUNT(DISTINCT ops) AS vol,
  COUNTIF(det_delivery_date IS NOT NULL AND delivery_date IS NOT NULL) AS vol_det,
  AVG(inducted_on_time_or_early) AS ifr,
  AVG(delivery_rel) AS delivery_rel,
  AVG(CAST(det_del_rel AS FLOAT64)) AS stored_det_del_rel,
  AVG(CAST(det_one_more_day_del_early AS FLOAT64)) AS stored_det_one_more,
  AVG(det_on_time) AS det_on_time,
  AVG(det_hits_minus_1_day) AS det_hits_minus_1_day,
  AVG(o2d_actual) AS avg_o2d_actual,
  AVG(o2d_stated) AS avg_o2d_stated
FROM flagged
GROUP BY 1, 2, 3, 4, 5, 6, 8
"""


def wavg(df: pd.DataFrame, col: str, wcol: str = "vol") -> float:
    w, v = df[wcol], df[col]
    m = v.notna() & w.notna() & (w > 0)
    if not m.any() or float(w[m].sum()) == 0:
        return float("nan")
    return float((v[m] * w[m]).sum() / w[m].sum())


def wavg_det(df: pd.DataFrame, col: str) -> float:
    """Weight by vol_det when available."""
    return wavg(df, col, "vol_det" if "vol_det" in df.columns and df["vol_det"].sum() > 0 else "vol")


def fmt_pct(x) -> str:
    return "—" if pd.isna(x) else f"{x:.1%}"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print("Querying cushion × bucket with det_* ...")
    df = query_df(SQL)
    print(f"Rows: {len(df):,}, vol_det sum: {df['vol_det'].sum():,.0f}")

    df["path"] = df["candidate_bucket"].map(
        lambda x: "direct" if x == "direct" else ("local" if x == "non_candidate" else "other")
    )

    def roll(sub: pd.DataFrame, label: str) -> dict:
        return {
            "segment": label,
            "vol": sub["vol"].sum(),
            "vol_det": sub["vol_det"].sum(),
            "suppliers": sub["supplier_id"].nunique(),
            "ifr": wavg(sub, "ifr"),
            "delivery_rel": wavg(sub, "delivery_rel"),
            "det_on_time": wavg_det(sub, "det_on_time"),
            "det_hits_minus_1": wavg_det(sub, "det_hits_minus_1_day"),
            "stored_det_del_rel": wavg_det(sub, "stored_det_del_rel"),
            "stored_det_one_more": wavg_det(sub, "stored_det_one_more"),
            "pct_direct": sub.loc[sub["path"] == "direct", "vol"].sum() / max(sub["vol"].sum(), 1),
        }

    overall = pd.DataFrame(
        [
            roll(df[df["is_cushioned"] == 1], "cushion>=1"),
            roll(df[df["is_cushioned"] == 0], "no cushion"),
        ]
    )
    overall["ifr_minus_del_pp"] = (overall["ifr"] - overall["delivery_rel"]) * 100
    overall["ifr_minus_det_on_time_pp"] = (overall["ifr"] - overall["det_on_time"]) * 100
    print("\n=== Cushioned vs not ===")
    print(overall.to_string(index=False))

    cush = df[df["is_cushioned"] == 1]
    path_rows = []
    for path, g in cush.groupby("path"):
        r = roll(g, path)
        r["path"] = path
        r["late_ifr"] = r["vol"] * (1 - r["ifr"])
        r["del_miss"] = r["vol"] * (1 - r["delivery_rel"])
        r["det_miss"] = r["vol_det"] * (1 - r["det_on_time"]) if r["vol_det"] else float("nan")
        r["det_m1_miss"] = r["vol_det"] * (1 - r["det_hits_minus_1"]) if r["vol_det"] else float("nan")
        path_rows.append(r)
    path_df = pd.DataFrame(path_rows).sort_values("vol", ascending=False)
    tot_late = path_df["late_ifr"].sum()
    tot_del = path_df["del_miss"].sum()
    tot_det = path_df["det_miss"].sum()
    tot_m1 = path_df["det_m1_miss"].sum()
    path_df["pct_vol"] = path_df["vol"] / path_df["vol"].sum()
    path_df["pct_ifr_lates"] = path_df["late_ifr"] / max(tot_late, 1)
    path_df["pct_del_misses"] = path_df["del_miss"] / max(tot_del, 1)
    path_df["pct_det_misses"] = path_df["det_miss"] / max(tot_det, 1)
    path_df["pct_det_m1_misses"] = path_df["det_m1_miss"] / max(tot_m1, 1)
    print("\n=== Cushioned by path ===")
    print(path_df.to_string(index=False))

    # Also all network (not just cushioned) by path for context
    net_rows = []
    for path, g in df.groupby("path"):
        r = roll(g, path)
        r["path"] = path
        r["late_ifr"] = r["vol"] * (1 - r["ifr"])
        net_rows.append(r)
    net_df = pd.DataFrame(net_rows)
    net_df["pct_vol"] = net_df["vol"] / net_df["vol"].sum()
    net_df["pct_ifr_lates"] = net_df["late_ifr"] / net_df["late_ifr"].sum()
    print("\n=== Network (all) by path ===")
    print(net_df.to_string(index=False))

    # Supplier pattern: cushioned, material directs, IFR weak, det/del still OK
    def supplier_roll(g: pd.DataFrame) -> pd.Series:
        vol = g["vol"].sum()
        dvol = g.loc[g["path"] == "direct", "vol"].sum()
        lvol = g.loc[g["path"] == "local", "vol"].sum()
        return pd.Series(
            {
                "vol": vol,
                "vol_det": g["vol_det"].sum(),
                "vol_direct": dvol,
                "vol_local": lvol,
                "direct_share": dvol / vol if vol else 0,
                "ifr": wavg(g, "ifr"),
                "delivery_rel": wavg(g, "delivery_rel"),
                "det_on_time": wavg_det(g, "det_on_time"),
                "det_hits_minus_1": wavg_det(g, "det_hits_minus_1_day"),
                "ifr_direct": wavg(g[g["path"] == "direct"], "ifr") if dvol else float("nan"),
                "ifr_local": wavg(g[g["path"] == "local"], "ifr") if lvol else float("nan"),
                "del_direct": wavg(g[g["path"] == "direct"], "delivery_rel") if dvol else float("nan"),
                "det_on_time_direct": wavg_det(g[g["path"] == "direct"], "det_on_time") if dvol else float("nan"),
                "det_m1_direct": wavg_det(g[g["path"] == "direct"], "det_hits_minus_1_day") if dvol else float("nan"),
                "cushion": g["cushion_sample"].dropna().mode().iloc[0]
                if g["cushion_sample"].notna().any()
                else float("nan"),
            }
        )

    keys = ["supplier_id", "su_name", "sto", "is_cushioned"]
    # Filter to det-populated rows weight — still roll all
    sup = df.groupby(keys, dropna=False).apply(supplier_roll, include_groups=False).reset_index()
    cush_sup = sup[(sup["is_cushioned"] == 1) & (sup["vol"] >= 50)].copy()
    cush_sup["ifr_vs_del_pp"] = (cush_sup["ifr"] - cush_sup["delivery_rel"]) * 100
    cush_sup["ifr_vs_det_pp"] = (cush_sup["ifr"] - cush_sup["det_on_time"]) * 100

    # Pattern A: IFR low, delivery_rel high, directs
    pattern_del = cush_sup[
        (cush_sup["ifr"] < 0.80)
        & (cush_sup["delivery_rel"] >= 0.85)
        & (cush_sup["direct_share"] >= 0.10)
    ].sort_values("vol", ascending=False)

    # Pattern B: IFR low, det_on_time still relatively OK (>=75%), or det_hits_minus_1
    pattern_det = cush_sup[
        (cush_sup["ifr"] < 0.80)
        & (cush_sup["det_on_time"] >= 0.70)
        & (cush_sup["direct_share"] >= 0.10)
    ].sort_values("vol", ascending=False)

    # Pattern C: IFR low but still hits EndDate-1 at decent rate? (unlikely if avg is 37%)
    pattern_m1 = cush_sup[
        (cush_sup["ifr"] < 0.80)
        & (cush_sup["det_hits_minus_1"] >= 0.50)
        & (cush_sup["direct_share"] >= 0.10)
    ].sort_values("vol", ascending=False)

    print(f"\nPattern IFR<80% del>=85% direct>=10%: {len(pattern_del)}")
    print(f"Pattern IFR<80% det_on_time>=70% direct>=10%: {len(pattern_det)}")
    print(f"Pattern IFR<80% det_hits_minus_1>=50% direct>=10%: {len(pattern_m1)}")

    # Gap segments
    cush_sup["big_gap"] = cush_sup["ifr_vs_del_pp"] <= -10
    gap_rows = []
    for flag, label in [(True, "IFR << del (≥10pp)"), (False, "IFR not << del")]:
        g = cush_sup[cush_sup["big_gap"] == flag]
        gap_rows.append(
            {
                "segment": label,
                "suppliers": len(g),
                "vol": float(g["vol"].sum()),
                "avg_direct_share": float(
                    (g["direct_share"] * g["vol"]).sum() / g["vol"].sum()
                )
                if g["vol"].sum()
                else float("nan"),
                "ifr": float((g["ifr"] * g["vol"]).sum() / g["vol"].sum()) if g["vol"].sum() else float("nan"),
                "delivery_rel": float((g["delivery_rel"] * g["vol"]).sum() / g["vol"].sum())
                if g["vol"].sum()
                else float("nan"),
                "det_on_time": float((g["det_on_time"] * g["vol"]).sum() / g["vol"].sum())
                if g["vol"].sum()
                else float("nan"),
                "det_hits_minus_1": float((g["det_hits_minus_1"] * g["vol"]).sum() / g["vol"].sum())
                if g["vol"].sum()
                else float("nan"),
            }
        )
    gap_df = pd.DataFrame(gap_rows)

    # Direct-path only on cushioned: IFR vs det metrics
    print("\n=== Gap segments ===")
    print(gap_df.to_string(index=False))

    # Save
    overall.to_csv(OUTPUT_DIR / "cushion_vs_ifr_del_overall.csv", index=False)
    path_df.to_csv(OUTPUT_DIR / "cushion_path_ifr_del.csv", index=False)
    net_df.to_csv(OUTPUT_DIR / "network_path_ifr_det.csv", index=False)
    pattern_del.to_csv(OUTPUT_DIR / "cushion_ifr_low_del_high_directors.csv", index=False)
    pattern_det.to_csv(OUTPUT_DIR / "cushion_ifr_low_det_ok_directors.csv", index=False)
    gap_df.to_csv(OUTPUT_DIR / "cushion_gap_segments.csv", index=False)
    cush_sup.sort_values("vol", ascending=False).to_csv(
        OUTPUT_DIR / "cushion_suppliers_ifr_del.csv", index=False
    )

    with pd.ExcelWriter(OUTPUT_DIR / "cushion_directs_ifr_vs_delrel.xlsx", engine="openpyxl") as xw:
        overall.to_excel(xw, sheet_name="cushion_vs_not", index=False)
        path_df.to_excel(xw, sheet_name="cushioned_by_path", index=False)
        net_df.to_excel(xw, sheet_name="network_by_path", index=False)
        gap_df.to_excel(xw, sheet_name="ifr_del_gap_segments", index=False)
        pattern_del.head(500).to_excel(xw, sheet_name="ifr_low_del_high", index=False)
        pattern_det.head(500).to_excel(xw, sheet_name="ifr_low_det_ok", index=False)
        cush_sup.sort_values("vol", ascending=False).head(2000).to_excel(
            xw, sheet_name="all_cushioned_suppliers", index=False
        )

    # Markdown
    d = path_df[path_df["path"] == "direct"]
    loc = path_df[path_df["path"] == "local"]
    d = d.iloc[0] if len(d) else None
    loc = loc.iloc[0] if len(loc) else None

    md = []
    md.append("# Directs → IFR → cushions vs det delivery reliability")
    md.append("")
    md.append("## Hypothesis")
    md.append("")
    md.append(
        "Direct volume disproportionately tanks **IFR**, triggering **cushions**, even though "
        "**deterministic delivery reliability** is still hit — including when subtracting one day "
        "for the cushion (`delivery_date <= det_delivery_date - 1`)."
    )
    md.append("")
    md.append("## Metric definitions")
    md.append("")
    md.append("| Metric | Definition |")
    md.append("|--------|------------|")
    md.append("| IFR | `inducted_on_time_or_early` |")
    md.append("| delivery_rel | Existing HVE delivery reliability |")
    md.append("| **det_on_time** | `delivery_date <= det_delivery_date` (corrected reliability) |")
    md.append("| **det_hits_minus_1** | `delivery_date <= det_delivery_date - 1` (still hits if 1 cushion day removed from det end) |")
    md.append("| stored `det_del_rel` | Your column: `EndDate <= delivery_date` (flips early/late vs typical on-time) |")
    md.append("| stored `det_one_more_day_del_early` | Your column: `EndDate - 1 <= delivery_date` |")
    md.append("")
    md.append(
        f"Det date coverage: **{df['vol_det'].sum()/df['vol'].sum():.1%}** of ops. "
        "Primary prove metrics below use **det_on_time** / **det_hits_minus_1**."
    )
    md.append("")
    md.append("## Verdict")
    md.append("")
    if d is not None and loc is not None:
        md.append(
            f"On **cushioned** volume: directs are **{d['pct_vol']:.1%}** of vol but "
            f"**{d['pct_ifr_lates']:.1%}** of IFR-late orders "
            f"(IFR **{d['ifr']:.1%}** vs local **{loc['ifr']:.1%}**)."
        )
        md.append("")
        md.append(
            f"Same direct arm delivery_rel **{d['delivery_rel']:.1%}**, det_on_time **{d['det_on_time']:.1%}**, "
            f"det_hits_minus_1 **{d['det_hits_minus_1']:.1%}** "
            f"(local: del {loc['delivery_rel']:.1%}, det {loc['det_on_time']:.1%}, "
            f"det−1 {loc['det_hits_minus_1']:.1%})."
        )
        over = d["pct_ifr_lates"] - d["pct_vol"]
        del_ok = d["delivery_rel"] >= 0.80
        # Supports if over-indexes IFR lates AND delivery/det still reasonably high
        if over > 0.03 and del_ok:
            md.append("")
            md.append(
                "**Directionally supports:** directs over-index on IFR misses vs share of volume, "
                "while delivery_rel on directs stays relatively high vs the IFR crater. "
                "Check det_hits_minus_1 — if that is low network-wide, “still hits with cushion day removed” "
                "is a harder bar than delivery_rel."
            )
        md.append("")
        md.append(
            f"Cushioned suppliers with IFR&lt;80%, delivery_rel≥85%, direct_share≥10%: **{len(pattern_del)}**. "
            f"With det_on_time≥70%: **{len(pattern_det)}**. "
            f"With det_hits_minus_1≥50%: **{len(pattern_m1)}**."
        )
    md.append("")
    md.append("## 1) Cushioned vs not")
    md.append("")
    md.append(
        "| Segment | Vol | IFR | Del rel | Det on-time | Det hits end−1 | IFR−Del pp | % direct |"
    )
    md.append(
        "|---------|-----|-----|---------|-------------|----------------|------------|----------|"
    )
    for _, r in overall.iterrows():
        md.append(
            f"| {r['segment']} | {r['vol']:,.0f} | {fmt_pct(r['ifr'])} | {fmt_pct(r['delivery_rel'])} | "
            f"{fmt_pct(r['det_on_time'])} | {fmt_pct(r['det_hits_minus_1'])} | "
            f"{r['ifr_minus_del_pp']:+.1f} | {r['pct_direct']:.1%} |"
        )
    md.append("")
    md.append("## 2) Within cushioned — by path")
    md.append("")
    md.append(
        "| Path | % vol | IFR | Del rel | Det on-time | Det end−1 | % IFR lates | % del misses | % det misses |"
    )
    md.append(
        "|------|-------|-----|---------|-------------|-----------|-------------|--------------|--------------|"
    )
    for _, r in path_df.iterrows():
        md.append(
            f"| {r['path']} | {r['pct_vol']:.1%} | {fmt_pct(r['ifr'])} | {fmt_pct(r['delivery_rel'])} | "
            f"{fmt_pct(r['det_on_time'])} | {fmt_pct(r['det_hits_minus_1'])} | "
            f"{r['pct_ifr_lates']:.1%} | {r['pct_del_misses']:.1%} | {r['pct_det_misses']:.1%} |"
        )
    md.append("")
    md.append("## 3) Network-wide by path (context)")
    md.append("")
    md.append("| Path | % vol | IFR | Del rel | Det on-time | Det end−1 | % IFR lates |")
    md.append("|------|-------|-----|---------|-------------|-----------|-------------|")
    for _, r in net_df.sort_values("vol", ascending=False).iterrows():
        md.append(
            f"| {r['path']} | {r['pct_vol']:.1%} | {fmt_pct(r['ifr'])} | {fmt_pct(r['delivery_rel'])} | "
            f"{fmt_pct(r['det_on_time'])} | {fmt_pct(r['det_hits_minus_1'])} | {r['pct_ifr_lates']:.1%} |"
        )
    md.append("")
    md.append("## 4) Example cushioned directors — IFR low, delivery still high")
    md.append("")
    md.append(
        "| SUID | Supplier | Vol | Direct % | IFR | Del rel | Det on-time | Det end−1 | Direct IFR | Local IFR |"
    )
    md.append(
        "|------|----------|-----|----------|-----|---------|-------------|-----------|------------|-----------|"
    )
    for _, r in pattern_del.head(20).iterrows():
        md.append(
            f"| {int(r['supplier_id'])} | {r['su_name']} | {r['vol']:,.0f} | {r['direct_share']:.0%} | "
            f"{fmt_pct(r['ifr'])} | {fmt_pct(r['delivery_rel'])} | {fmt_pct(r['det_on_time'])} | "
            f"{fmt_pct(r['det_hits_minus_1'])} | {fmt_pct(r['ifr_direct'])} | {fmt_pct(r['ifr_local'])} |"
        )
    md.append("")
    md.append("## 5) Among cushioned — IFR≪del gap vs not")
    md.append("")
    md.append("| Segment | Suppliers | Vol | Direct share | IFR | Del | Det on-time | Det end−1 |")
    md.append("|---------|-----------|-----|--------------|-----|-----|-------------|-----------|")
    for _, r in gap_df.iterrows():
        md.append(
            f"| {r['segment']} | {r['suppliers']:.0f} | {r['vol']:,.0f} | {r['avg_direct_share']:.1%} | "
            f"{fmt_pct(r['ifr'])} | {fmt_pct(r['delivery_rel'])} | "
            f"{fmt_pct(r['det_on_time'])} | {fmt_pct(r['det_hits_minus_1'])} |"
        )
    md.append("")
    md.append("## Files")
    md.append("")
    md.append("| File | Contents |")
    md.append("|------|----------|")
    md.append("| `cushion_directs_ifr_vs_delrel.xlsx` | All tabs |")
    md.append("| `scripts/run_cushion_directs_ifr_del.py` | Re-run |")

    out = OUTPUT_DIR / "cushion_directs_ifr_vs_delrel.md"
    out.write_text("\n".join(md) + "\n")
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()
