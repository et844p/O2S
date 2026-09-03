#!/usr/bin/env python3
"""SoCal constrained origins: do directs help O2D actual in high-vol weeks?

Framing:
- Origin = SoCal assigned hubs (constrained markets ~96%)
- BAU = weeks where suppliers mostly induct local (non-direct)
- High-vol / constraint stress = Memorial Day week (vol + directs spike; IFR dips)
- Primary metric = O2D actual (faster?)
- IFR reported but expected to dip — not the pass/fail

Compares:
1) Within high-vol week: direct vs local (non_candidate) O2D actual
2) Same suppliers: BAU local O2D actual vs high-vol direct O2D actual
3) Same suppliers: BAU local vs high-vol local (stress on staying local)
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

HIGH_VOL_WEEK = "2026-05-24"  # Memorial Day — high vol + directs spike
# BAU = nearby weeks with material SoCal vol but low direct share
BAU_WEEKS = ("2026-06-14", "2026-06-21", "2026-06-28", "2026-07-12", "2026-07-19")
# Optional second high-vol week that stayed mostly local (July 5)
JULY_HIGH_VOL_LOCAL = "2026-07-05"

SOCAL_ASSIGNED = """
(
  UPPER(o.assigned_induction_hub_name) LIKE '%CHINO%'
  OR UPPER(o.assigned_induction_hub_name) LIKE '%RIALTO%'
  OR UPPER(o.assigned_induction_hub_name) LIKE '%INDUSTRY%'
  OR UPPER(o.assigned_induction_hub_name) LIKE '%LOS ANGELES%'
  OR UPPER(o.assigned_induction_hub_name) LIKE '%ANAHEIM%'
  OR UPPER(o.assigned_induction_hub_name) LIKE '%ARCADIA%'
  OR UPPER(o.assigned_induction_hub_name) LIKE '%SANTA FE%'
  OR UPPER(o.assigned_induction_hub_name) LIKE '%CARSON%'
  OR UPPER(o.assigned_induction_hub_name) LIKE '%BURBANK%'
  OR UPPER(o.assigned_induction_hub_name) LIKE '%OCEANSIDE%'
  OR UPPER(o.assigned_induction_hub_name) LIKE '%OTAY%'
  OR UPPER(o.assigned_induction_hub_name) LIKE '%SAN DIEGO%'
  OR UPPER(o.assigned_induction_hub_name) LIKE '%DIAMOND BAR%'
)
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
    o.assigned_constrained_market,
    o.distance_assignedhub_customer,
    o.distance_actualhub_customer,
    o.distance_assignedhub_actualhub,
    o.direct_gain,
    o.inducted_on_time_or_early,
    o.delivery_rel,
    o.o2d_stated,
    o.o2d_actual,
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
    AND {SOCAL_ASSIGNED}
    AND o.assigned_constrained_market = 1
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
      WHEN f.candidate_bucket = 'direct' THEN 'direct'
      WHEN f.candidate_bucket = 'non_candidate' THEN 'local'
      ELSE 'other_candidate'
    END AS path
  FROM flagged AS f
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
  AVG(IF(o2d_actual IS NOT NULL AND o2d_stated IS NOT NULL AND o2d_actual <= o2d_stated, 1, 0)) AS pct_meet_beat_stated,
  AVG(IF(o2d_actual IS NOT NULL AND o2d_actual <= 5, 1, 0)) AS pct_o2d_le5,
  AVG(direct_gain) AS avg_direct_gain,
  AVG(distance_actualhub_customer) AS avg_mi_actual_to_cust,
  AVG(distance_assignedhub_customer) AS avg_mi_assigned_to_cust
FROM pathed
WHERE path IN ('direct', 'local')
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
            "pct_meet_beat_stated": wavg(g, "pct_meet_beat_stated"),
            "pct_o2d_le5": wavg(g, "pct_o2d_le5"),
            "avg_mi_actual_to_cust": wavg(g, "avg_mi_actual_to_cust"),
            "suppliers": int(g["supplier_id"].nunique()),
        }
    )


def supplier_agg(g: pd.DataFrame, label: str) -> pd.DataFrame:
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
                f"pct_le5_{label}": wavg(sg, "pct_o2d_le5"),
                f"mi_{label}": wavg(sg, "avg_mi_actual_to_cust"),
            }
        )
    return pd.DataFrame(rows)


def fmt_pct(x) -> str:
    return "—" if pd.isna(x) else f"{x:.1%}"


def fmt_num(x, d=2) -> str:
    return "—" if pd.isna(x) else f"{x:.{d}f}"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print("Querying SoCal constrained origin direct vs local...")
    df = query_df(SQL)
    df["msbd_week"] = pd.to_datetime(df["msbd_week"]).dt.strftime("%Y-%m-%d")
    print(f"Rows: {len(df):,}")
    print(df.groupby("path")["vol"].sum())

    # Weekly path rollup
    weekly = (
        df.groupby(["msbd_week", "path"], dropna=False)
        .apply(rollup, include_groups=False)
        .reset_index()
        .sort_values(["msbd_week", "path"])
    )
    weekly.to_csv(OUTPUT_DIR / "socal_constrained_direct_vs_local_weekly.csv", index=False)

    # Side-by-side weekly
    metrics = [
        "vol",
        "ifr",
        "delivery_rel",
        "avg_o2d_stated",
        "avg_o2d_actual",
        "o2d_gap",
        "pct_o2d_le5",
        "avg_mi_actual_to_cust",
        "suppliers",
    ]
    parts = []
    for m in metrics:
        p = weekly.pivot(index="msbd_week", columns="path", values=m)
        p.columns = [f"{m}__{c}" for c in p.columns]
        parts.append(p)
    side = pd.concat(parts, axis=1).reset_index()
    side["o2d_actual_delta_direct_minus_local"] = side.get("avg_o2d_actual__direct") - side.get(
        "avg_o2d_actual__local"
    )
    side["ifr_delta_direct_minus_local"] = side.get("ifr__direct") - side.get("ifr__local")
    side.to_csv(OUTPUT_DIR / "socal_constrained_direct_vs_local_weekly_sidebyside.csv", index=False)

    print("\n=== Weekly O2D actual: direct vs local ===")
    cols = [
        c
        for c in [
            "msbd_week",
            "vol__direct",
            "vol__local",
            "avg_o2d_actual__direct",
            "avg_o2d_actual__local",
            "o2d_actual_delta_direct_minus_local",
            "ifr__direct",
            "ifr__local",
            "pct_o2d_le5__direct",
            "pct_o2d_le5__local",
        ]
        if c in side.columns
    ]
    print(side[cols].to_string(index=False))

    # Period summaries
    periods = []
    for label, weeks, path in [
        ("highvol_memorial_direct", [HIGH_VOL_WEEK], "direct"),
        ("highvol_memorial_local", [HIGH_VOL_WEEK], "local"),
        ("bau_local", list(BAU_WEEKS), "local"),
        ("bau_direct", list(BAU_WEEKS), "direct"),
        ("july5_highvol_local", [JULY_HIGH_VOL_LOCAL], "local"),
        ("july5_highvol_direct", [JULY_HIGH_VOL_LOCAL], "direct"),
    ]:
        sub = df[(df["msbd_week"].isin(weeks)) & (df["path"] == path)]
        if sub.empty:
            continue
        r = rollup(sub)
        r["period"] = label
        r["path"] = path
        periods.append(r)
    period = pd.DataFrame(periods)
    period.to_csv(OUTPUT_DIR / "socal_constrained_period_summary.csv", index=False)
    print("\n=== Period summary ===")
    print(period.to_string(index=False))

    # --- Supplier cohort: similar BAU pattern (mostly local in BAU), then built directs in high-vol ---
    bau_local = supplier_agg(
        df[(df["msbd_week"].isin(BAU_WEEKS)) & (df["path"] == "local")], "bau_local"
    )
    bau_direct = supplier_agg(
        df[(df["msbd_week"].isin(BAU_WEEKS)) & (df["path"] == "direct")], "bau_direct"
    )
    hv_direct = supplier_agg(
        df[(df["msbd_week"] == HIGH_VOL_WEEK) & (df["path"] == "direct")], "hv_direct"
    )
    hv_local = supplier_agg(
        df[(df["msbd_week"] == HIGH_VOL_WEEK) & (df["path"] == "local")], "hv_local"
    )

    keys = ["supplier_id", "su_name", "parent_suid", "parent_su_name", "sto"]
    cohort = bau_local.merge(bau_direct, on=keys, how="left")
    cohort = cohort.merge(hv_direct, on=keys, how="inner")  # must have built directs in HV
    cohort = cohort.merge(hv_local, on=keys, how="left")

    # Similar BAU fulfillment: mostly local (direct share of BAU < 20%, enough BAU local vol)
    cohort["bau_direct_vol"] = cohort["vol_bau_direct"].fillna(0)
    cohort["bau_total"] = cohort["vol_bau_local"] + cohort["bau_direct_vol"]
    cohort["bau_direct_share"] = cohort["bau_direct_vol"] / cohort["bau_total"].replace(0, pd.NA)
    similar = cohort[
        (cohort["vol_bau_local"] >= 50)
        & (cohort["vol_hv_direct"] >= 30)
        & (cohort["bau_direct_share"].fillna(0) <= 0.20)
    ].copy()

    similar["o2d_delta_hv_direct_minus_bau_local"] = (
        similar["o2d_actual_hv_direct"] - similar["o2d_actual_bau_local"]
    )
    similar["ifr_delta_hv_direct_minus_bau_local"] = (
        similar["ifr_hv_direct"] - similar["ifr_bau_local"]
    )
    similar["faster_than_bau"] = similar["o2d_delta_hv_direct_minus_bau_local"] < 0
    similar["o2d_delta_hv_direct_minus_hv_local"] = (
        similar["o2d_actual_hv_direct"] - similar["o2d_actual_hv_local"]
    )
    similar = similar.sort_values("vol_hv_direct", ascending=False)
    similar.to_csv(OUTPUT_DIR / "socal_constrained_similar_bau_suppliers.csv", index=False)

    print(f"\nSimilar-BAU suppliers (local in BAU, built directs in Memorial Day): {len(similar)}")
    if len(similar):
        print(
            f"  Faster O2D actual than own BAU local: {similar['faster_than_bau'].mean():.1%} "
            f"({similar['faster_than_bau'].sum():.0f}/{len(similar)})"
        )
        print(
            f"  Vol-weighted O2D delta (HV direct − BAU local): "
            f"{wavg(similar.rename(columns={'vol_hv_direct':'vol','o2d_delta_hv_direct_minus_bau_local':'avg_o2d_actual'}), 'avg_o2d_actual', 'vol'):+.2f}d"
        )
        print(
            f"  Median O2D delta: {similar['o2d_delta_hv_direct_minus_bau_local'].median():+.2f}d"
        )
        print(
            f"  Vol-weighted IFR delta: "
            f"{wavg(similar.assign(vol=similar['vol_hv_direct'], x=similar['ifr_delta_hv_direct_minus_bau_local']), 'x', 'vol')*100:+.1f} pp"
        )
        print("\nTop by HV direct vol:")
        print(
            similar.head(20)[
                [
                    "supplier_id",
                    "su_name",
                    "vol_bau_local",
                    "o2d_actual_bau_local",
                    "vol_hv_direct",
                    "o2d_actual_hv_direct",
                    "o2d_delta_hv_direct_minus_bau_local",
                    "ifr_bau_local",
                    "ifr_hv_direct",
                    "ifr_delta_hv_direct_minus_bau_local",
                ]
            ].to_string(index=False)
        )

    # Within HV week: all direct vs local (not just similar cohort)
    hv_d = period[period["period"] == "highvol_memorial_direct"].iloc[0]
    hv_l = period[period["period"] == "highvol_memorial_local"].iloc[0]
    bau_l = period[period["period"] == "bau_local"].iloc[0]

    with pd.ExcelWriter(
        OUTPUT_DIR / "socal_constrained_directs_o2d_verdict.xlsx", engine="openpyxl"
    ) as xw:
        period.to_excel(xw, sheet_name="period_summary", index=False)
        side.to_excel(xw, sheet_name="weekly_sidebyside", index=False)
        similar.to_excel(xw, sheet_name="similar_bau_suppliers", index=False)
        weekly.to_excel(xw, sheet_name="weekly_long", index=False)

    # Markdown verdict
    md = []
    md.append("# SoCal constrained origins: do directs help O2D actual?")
    md.append("")
    md.append("## Framing")
    md.append("")
    md.append("- **Origin:** SoCal assigned hubs with `assigned_constrained_market = 1`")
    md.append("- **Paths:** `direct` (classified) vs `local` (`non_candidate`, SoCal induct)")
    md.append(f"- **High-vol / constraint stress:** MSBD week `{HIGH_VOL_WEEK}` (Memorial Day)")
    md.append(f"- **BAU:** weeks `{', '.join(BAU_WEEKS)}` (material vol, mostly local fulfillment)")
    md.append("- **Primary metric:** O2D **actual** (is the direct faster to customer?)")
    md.append("- **IFR:** expected to dip in high-vol — reported, not pass/fail")
    md.append("")
    md.append("## Period totals")
    md.append("")
    md.append("| Period | Path | Vol | IFR | Del Rel | O2D stated | O2D actual | Gap | % ≤5d | Mi to cust |")
    md.append("|--------|------|-----|-----|---------|------------|------------|-----|-------|------------|")
    for _, r in period.iterrows():
        md.append(
            f"| {r['period']} | {r['path']} | {r['vol']:,.0f} | "
            f"{fmt_pct(r['ifr'])} | {fmt_pct(r['delivery_rel'])} | "
            f"{fmt_num(r['avg_o2d_stated'])} | {fmt_num(r['avg_o2d_actual'])} | "
            f"{r['o2d_gap']:+.2f} | {fmt_pct(r['pct_o2d_le5'])} | "
            f"{fmt_num(r['avg_mi_actual_to_cust'], 0)} |"
        )
    md.append("")
    md.append("## Test 1 — Within Memorial Day week: direct vs local")
    md.append("")
    md.append(
        f"- Direct O2D actual **{hv_d['avg_o2d_actual']:.2f}d** vs local **{hv_l['avg_o2d_actual']:.2f}d** "
        f"(Δ {hv_d['avg_o2d_actual']-hv_l['avg_o2d_actual']:+.2f}d; negative = direct faster)"
    )
    md.append(
        f"- IFR: direct {hv_d['ifr']:.1%} vs local {hv_l['ifr']:.1%} "
        f"({(hv_d['ifr']-hv_l['ifr'])*100:+.1f} pp) — dip expected on directs / stress"
    )
    md.append(
        f"- % O2D actual ≤5d: direct {hv_d['pct_o2d_le5']:.1%} vs local {hv_l['pct_o2d_le5']:.1%}"
    )
    md.append(
        f"- Miles after induction: direct ~{hv_d['avg_mi_actual_to_cust']:.0f} vs local ~{hv_l['avg_mi_actual_to_cust']:.0f}"
    )
    md.append("")
    md.append("## Test 2 — Similar BAU pattern → built directs in high-vol")
    md.append("")
    md.append(
        "Cohort: ≥50 BAU local ops, BAU direct share ≤20%, ≥30 Memorial Day direct ops "
        "(same suppliers, normal fulfillment ≈ local)."
    )
    md.append("")
    if len(similar):
        vw_o2d = wavg(
            similar.rename(
                columns={
                    "vol_hv_direct": "vol",
                    "o2d_delta_hv_direct_minus_bau_local": "avg_o2d_actual",
                }
            ),
            "avg_o2d_actual",
            "vol",
        )
        vw_ifr = wavg(
            similar.assign(vol=similar["vol_hv_direct"], x=similar["ifr_delta_hv_direct_minus_bau_local"]),
            "x",
            "vol",
        )
        md.append(f"- **n = {len(similar)}** suppliers")
        md.append(
            f"- **{similar['faster_than_bau'].mean():.1%}** faster O2D actual than their own BAU local "
            f"({int(similar['faster_than_bau'].sum())}/{len(similar)})"
        )
        md.append(f"- Median O2D delta (HV direct − BAU local): **{similar['o2d_delta_hv_direct_minus_bau_local'].median():+.2f}d**")
        md.append(f"- Vol-weighted O2D delta: **{vw_o2d:+.2f}d**")
        md.append(f"- Vol-weighted IFR delta: **{vw_ifr*100:+.1f} pp** (dip expected)")
        md.append("")
        verdict_faster = vw_o2d < -0.1
        md.append("### Verdict")
        md.append("")
        if verdict_faster:
            md.append(
                f"**Helpful on speed:** building directs in the high-vol week beat these suppliers’ "
                f"own BAU local O2D actual by ~{abs(vw_o2d):.2f}d vol-weighted, even with an IFR dip."
            )
        elif vw_o2d > 0.1:
            md.append(
                f"**Not helpful on speed:** high-vol directs were **slower** than own BAU local by "
                f"~{vw_o2d:.2f}d vol-weighted (despite much shorter post-induction miles)."
            )
        else:
            md.append(
                f"**Roughly flat on speed:** vol-weighted O2D delta ~{vw_o2d:+.2f}d vs own BAU local."
            )
        md.append("")
        md.append("### Top suppliers (by HV direct vol)")
        md.append("")
        md.append(
            "| SUID | Supplier | BAU local vol | BAU O2D act | HV direct vol | HV O2D act | O2D Δ | BAU IFR | HV IFR | IFR Δ |"
        )
        md.append(
            "|------|----------|---------------|-------------|---------------|------------|-------|---------|--------|-------|"
        )
        for _, r in similar.head(25).iterrows():
            md.append(
                f"| {int(r['supplier_id'])} | {r['su_name']} | "
                f"{r['vol_bau_local']:,.0f} | {fmt_num(r['o2d_actual_bau_local'])} | "
                f"{r['vol_hv_direct']:,.0f} | {fmt_num(r['o2d_actual_hv_direct'])} | "
                f"{r['o2d_delta_hv_direct_minus_bau_local']:+.2f} | "
                f"{fmt_pct(r['ifr_bau_local'])} | {fmt_pct(r['ifr_hv_direct'])} | "
                f"{r['ifr_delta_hv_direct_minus_bau_local']*100:+.1f} pp |"
            )
    else:
        md.append("No suppliers met the similar-BAU cohort thresholds.")

    md.append("")
    md.append("## Test 3 — BAU local baseline vs high-vol local (stress without directing)")
    md.append("")
    md.append(
        f"- BAU local O2D actual **{bau_l['avg_o2d_actual']:.2f}d** vs Memorial Day local "
        f"**{hv_l['avg_o2d_actual']:.2f}d** (Δ {hv_l['avg_o2d_actual']-bau_l['avg_o2d_actual']:+.2f}d)"
    )
    md.append(
        f"- BAU local IFR {bau_l['ifr']:.1%} vs Memorial Day local {hv_l['ifr']:.1%} "
        f"({(hv_l['ifr']-bau_l['ifr'])*100:+.1f} pp)"
    )
    md.append("")
    md.append("## Weekly side-by-side (O2D actual)")
    md.append("")
    md.append("| Week | Direct vol | Local vol | Direct O2D | Local O2D | O2D Δ | Direct IFR | Local IFR |")
    md.append("|------|------------|-----------|------------|-----------|-------|------------|-----------|")
    for _, r in side.iterrows():
        tag = ""
        if r["msbd_week"] == HIGH_VOL_WEEK:
            tag = " ← high-vol"
        elif r["msbd_week"] in BAU_WEEKS:
            tag = " ← BAU"
        md.append(
            f"| {r['msbd_week']}{tag} | "
            f"{fmt_num(r.get('vol__direct'), 0)} | {fmt_num(r.get('vol__local'), 0)} | "
            f"{fmt_num(r.get('avg_o2d_actual__direct'))} | {fmt_num(r.get('avg_o2d_actual__local'))} | "
            f"{fmt_num(r.get('o2d_actual_delta_direct_minus_local'))} | "
            f"{fmt_pct(r.get('ifr__direct'))} | {fmt_pct(r.get('ifr__local'))} |"
        )
    md.append("")
    md.append("## Files")
    md.append("")
    md.append("| File | Contents |")
    md.append("|------|----------|")
    md.append("| `socal_constrained_directs_o2d_verdict.xlsx` | Period + weekly + supplier cohort |")
    md.append("| `socal_constrained_similar_bau_suppliers.csv` | Similar-BAU suppliers who directed in HV |")
    md.append("| `scripts/run_socal_constrained_directs_o2d.py` | Re-run |")

    path = OUTPUT_DIR / "socal_constrained_directs_o2d_verdict.md"
    path.write_text("\n".join(md) + "\n")
    print(f"\nWrote {path}")


if __name__ == "__main__":
    main()
