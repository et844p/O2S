#!/usr/bin/env python3
"""Capacity lens: do directs-builders get better IFR on remaining in-hub volume?

Hypothesis: suppliers who build directs divert far-market volume off the
constrained SoCal hub, freeing capacity for in-market / local-hub volume →
higher IFR on that remaining local volume vs suppliers who do not direct.

Tests:
1) Between-supplier (Memorial Day / full window): local-path IFR for
   directs-builders vs non-builders (SoCal constrained origin).
2) Dose-response: local IFR by share of supplier vol that is direct.
3) Within-supplier: weeks with high direct share vs low — local IFR lift.
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

HIGH_VOL_WEEK = "2026-05-24"
BAU_WEEKS = ("2026-06-14", "2026-06-21", "2026-06-28", "2026-07-12", "2026-07-19")

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
    o.actual_induction_hub_name,
    o.actual_induction_hub_state,
    o.destination_state,
    o.distance_assignedhub_actualhub,
    o.direct_gain,
    o.inducted_on_time_or_early,
    o.delivery_rel,
    o.o2d_actual,
    o.o2d_stated,
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
    AND o.assigned_constrained_market = 1
    AND {SOCAL_ASSIGNED}
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
)

SELECT
  CAST(msbd_week AS STRING) AS msbd_week,
  supplier_id,
  su_name,
  parent_suid,
  parent_su_name,
  sto,
  assigned_induction_hub_name,
  candidate_bucket,
  CASE
    WHEN candidate_bucket = 'direct' THEN 'direct'
    WHEN candidate_bucket = 'non_candidate' THEN 'local_inhub'
    ELSE 'other'
  END AS path,
  COUNT(DISTINCT ops) AS vol,
  AVG(inducted_on_time_or_early) AS ifr,
  AVG(delivery_rel) AS delivery_rel,
  AVG(o2d_actual) AS avg_o2d_actual,
  AVG(o2d_stated) AS avg_o2d_stated
FROM flagged
GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9
"""


def wavg(df: pd.DataFrame, col: str, wcol: str = "vol") -> float:
    w, v = df[wcol], df[col]
    m = v.notna() & w.notna() & (w > 0)
    if not m.any() or float(w[m].sum()) == 0:
        return float("nan")
    return float((v[m] * w[m]).sum() / w[m].sum())


def fmt_pct(x) -> str:
    return "—" if pd.isna(x) else f"{x:.1%}"


def fmt_num(x, d=2) -> str:
    return "—" if pd.isna(x) else f"{x:.{d}f}"


def supplier_week_paths(df: pd.DataFrame) -> pd.DataFrame:
    """One row per supplier × week with direct + local_inhub metrics."""
    keys = ["msbd_week", "supplier_id", "su_name", "parent_suid", "parent_su_name", "sto", "assigned_induction_hub_name"]
    d = df[df["path"] == "direct"].groupby(keys, dropna=False).apply(
        lambda g: pd.Series({"vol_direct": g["vol"].sum(), "ifr_direct": wavg(g, "ifr")}),
        include_groups=False,
    ).reset_index()
    loc = df[df["path"] == "local_inhub"].groupby(keys, dropna=False).apply(
        lambda g: pd.Series(
            {
                "vol_local": g["vol"].sum(),
                "ifr_local": wavg(g, "ifr"),
                "del_local": wavg(g, "delivery_rel"),
                "o2d_local": wavg(g, "avg_o2d_actual"),
            }
        ),
        include_groups=False,
    ).reset_index()
    m = loc.merge(d, on=keys, how="outer")
    for c in ["vol_direct", "vol_local"]:
        m[c] = m[c].fillna(0)
    m["vol_total_dl"] = m["vol_direct"] + m["vol_local"]
    m["direct_share"] = m["vol_direct"] / m["vol_total_dl"].replace(0, pd.NA)
    return m


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print("Querying SoCal constrained supplier×week×path...")
    df = query_df(SQL)
    df["msbd_week"] = pd.to_datetime(df["msbd_week"]).dt.strftime("%Y-%m-%d")
    print(f"Rows: {len(df):,}")

    sw = supplier_week_paths(df)
    sw.to_csv(OUTPUT_DIR / "directs_capacity_supplier_week.csv", index=False)

    # --- Test 1: Memorial Day — builders vs non-builders on LOCAL IFR ---
    hv = sw[sw["msbd_week"] == HIGH_VOL_WEEK].copy()
    # Builder: material directs in HV week; need remaining local vol to measure in-hub IFR
    hv["builder"] = hv["vol_direct"] >= 30
    hv["has_local"] = hv["vol_local"] >= 30
    hv_compare = hv[hv["has_local"]].copy()

    def cohort_roll(g: pd.DataFrame, label: str) -> dict:
        return {
            "cohort": label,
            "suppliers": g["supplier_id"].nunique(),
            "vol_local": g["vol_local"].sum(),
            "vol_direct": g["vol_direct"].sum(),
            "ifr_local": wavg(g.rename(columns={"vol_local": "vol", "ifr_local": "ifr"}), "ifr", "vol"),
            "del_local": wavg(g.rename(columns={"vol_local": "vol", "del_local": "ifr"}), "ifr", "vol"),
            "o2d_local": wavg(g.rename(columns={"vol_local": "vol", "o2d_local": "ifr"}), "ifr", "vol"),
            "avg_direct_share": wavg(
                g.assign(vol=g["vol_total_dl"], x=g["direct_share"].fillna(0)), "x", "vol"
            ),
        }

    builders = hv_compare[hv_compare["builder"]]
    nonbuilders = hv_compare[~hv_compare["builder"] & (hv_compare["vol_direct"] == 0)]
    # also light directors (1-29) as middle
    light = hv_compare[~hv_compare["builder"] & (hv_compare["vol_direct"] > 0)]

    t1 = pd.DataFrame(
        [
            cohort_roll(builders, "HV builders (≥30 direct + ≥30 local)"),
            cohort_roll(light, "HV light directors (1–29 direct + ≥30 local)"),
            cohort_roll(nonbuilders, "HV non-builders (0 direct + ≥30 local)"),
        ]
    )
    t1["ifr_vs_nonbuilders_pp"] = (t1["ifr_local"] - t1.loc[t1["cohort"].str.contains("non-builders"), "ifr_local"].iloc[0]) * 100
    print("\n=== Test 1: Memorial Day local IFR by builder status ===")
    print(t1.to_string(index=False))

    # Volume-matched non-builders: similar total vol to builders
    # Bin by total_dl quartiles among builders, match nonbuilders in same bin
    if len(builders) and len(nonbuilders):
        builders = builders.copy()
        builders["vol_bin"] = pd.qcut(builders["vol_total_dl"], 4, duplicates="drop")
        # apply same bins to nonbuilders via cut edges
        edges = pd.qcut(builders["vol_total_dl"], 4, retbins=True, duplicates="drop")[1]
        non_m = nonbuilders.copy()
        non_m["vol_bin"] = pd.cut(non_m["vol_total_dl"], bins=edges, include_lowest=True)
        matched_rows = []
        for b in builders["vol_bin"].dropna().unique():
            b_g = builders[builders["vol_bin"] == b]
            n_g = non_m[non_m["vol_bin"] == b]
            if len(n_g) == 0:
                continue
            matched_rows.append(
                {
                    "vol_bin": str(b),
                    "n_builders": len(b_g),
                    "n_nonbuilders": len(n_g),
                    "ifr_local_builders": wavg(
                        b_g.rename(columns={"vol_local": "vol", "ifr_local": "ifr"}), "ifr", "vol"
                    ),
                    "ifr_local_nonbuilders": wavg(
                        n_g.rename(columns={"vol_local": "vol", "ifr_local": "ifr"}), "ifr", "vol"
                    ),
                    "vol_local_builders": b_g["vol_local"].sum(),
                    "vol_local_nonbuilders": n_g["vol_local"].sum(),
                }
            )
        matched = pd.DataFrame(matched_rows)
        if len(matched):
            matched["ifr_delta_pp"] = (matched["ifr_local_builders"] - matched["ifr_local_nonbuilders"]) * 100
            print("\nVolume-matched bins (Memorial Day):")
            print(matched.to_string(index=False))
        else:
            matched = pd.DataFrame()
    else:
        matched = pd.DataFrame()

    # --- Test 2: Dose-response on Memorial Day ---
    dose = hv_compare[hv_compare["vol_local"] >= 30].copy()
    dose["direct_share_bin"] = pd.cut(
        dose["direct_share"].fillna(0),
        bins=[-0.01, 0.0, 0.1, 0.25, 0.5, 1.0],
        labels=["0%", "0–10%", "10–25%", "25–50%", "50%+"],
    )
    dose_rows = []
    for lab, g in dose.groupby("direct_share_bin", observed=True):
        dose_rows.append(
            {
                "direct_share_bin": str(lab),
                "suppliers": g["supplier_id"].nunique(),
                "vol_local": g["vol_local"].sum(),
                "vol_direct": g["vol_direct"].sum(),
                "ifr_local": wavg(g.rename(columns={"vol_local": "vol", "ifr_local": "ifr"}), "ifr", "vol"),
            }
        )
    dose_df = pd.DataFrame(dose_rows)
    print("\n=== Test 2: Dose-response (local IFR by direct share) ===")
    print(dose_df.to_string(index=False))

    # --- Test 3: Within-supplier — high-direct weeks vs low-direct weeks ---
    # For each supplier with enough weeks: compare local IFR in weeks with direct_share>=25% vs weeks with direct_share==0
    sw2 = sw[(sw["vol_local"] >= 20)].copy()
    high = sw2[sw2["direct_share"].fillna(0) >= 0.25]
    low = sw2[sw2["vol_direct"] == 0]
    # aggregate per supplier
    def agg_side(g, prefix):
        return pd.Series(
            {
                f"weeks_{prefix}": g["msbd_week"].nunique(),
                f"vol_local_{prefix}": g["vol_local"].sum(),
                f"ifr_local_{prefix}": wavg(
                    g.rename(columns={"vol_local": "vol", "ifr_local": "ifr"}), "ifr", "vol"
                ),
            }
        )

    high_s = high.groupby(["supplier_id", "su_name", "sto"], dropna=False).apply(
        lambda g: agg_side(g, "high_direct"), include_groups=False
    ).reset_index()
    low_s = low.groupby(["supplier_id", "su_name", "sto"], dropna=False).apply(
        lambda g: agg_side(g, "no_direct"), include_groups=False
    ).reset_index()
    within = high_s.merge(low_s, on=["supplier_id", "su_name", "sto"], how="inner")
    within = within[
        (within["vol_local_high_direct"] >= 50) & (within["vol_local_no_direct"] >= 50)
    ].copy()
    within["ifr_lift_pp"] = (within["ifr_local_high_direct"] - within["ifr_local_no_direct"]) * 100
    within["positive_lift"] = within["ifr_lift_pp"] > 0
    within = within.sort_values("vol_local_high_direct", ascending=False)
    within.to_csv(OUTPUT_DIR / "directs_capacity_within_supplier.csv", index=False)

    print(f"\n=== Test 3: Within-supplier local IFR (high-direct weeks vs no-direct weeks) n={len(within)} ===")
    if len(within):
        vw_lift = wavg(
            within.assign(vol=within["vol_local_high_direct"], x=within["ifr_lift_pp"]),
            "x",
            "vol",
        )
        print(f"  % with positive local IFR lift: {within['positive_lift'].mean():.1%}")
        print(f"  Median lift: {within['ifr_lift_pp'].median():+.2f} pp")
        print(f"  Vol-weighted lift: {vw_lift:+.2f} pp")
        print(within.head(15).to_string(index=False))
    else:
        vw_lift = float("nan")

    # --- Test 4: Full-window builder classification ---
    # Supplier-level over May-Aug: direct share, local IFR
    full = sw.groupby(["supplier_id", "su_name", "sto"], dropna=False).apply(
        lambda g: pd.Series(
            {
                "vol_direct": g["vol_direct"].sum(),
                "vol_local": g["vol_local"].sum(),
                "ifr_local": wavg(
                    g[g["vol_local"] > 0].rename(columns={"vol_local": "vol", "ifr_local": "ifr"}),
                    "ifr",
                    "vol",
                )
                if (g["vol_local"] > 0).any()
                else float("nan"),
                "ifr_direct": wavg(
                    g[g["vol_direct"] > 0].rename(columns={"vol_direct": "vol", "ifr_direct": "ifr"}),
                    "ifr",
                    "vol",
                )
                if (g["vol_direct"] > 0).any()
                else float("nan"),
            }
        ),
        include_groups=False,
    ).reset_index()
    full["vol_total"] = full["vol_direct"] + full["vol_local"]
    full["direct_share"] = full["vol_direct"] / full["vol_total"].replace(0, pd.NA)
    full_elig = full[full["vol_local"] >= 100].copy()
    full_elig["builder_tier"] = pd.cut(
        full_elig["direct_share"].fillna(0),
        bins=[-0.01, 0.0, 0.05, 0.15, 0.30, 1.0],
        labels=["0% (non-builder)", "0–5%", "5–15%", "15–30%", "30%+"],
    )
    tier_rows = []
    for lab, g in full_elig.groupby("builder_tier", observed=True):
        tier_rows.append(
            {
                "builder_tier": str(lab),
                "suppliers": len(g),
                "vol_local": g["vol_local"].sum(),
                "vol_direct": g["vol_direct"].sum(),
                "ifr_local": wavg(g.rename(columns={"vol_local": "vol", "ifr_local": "ifr"}), "ifr", "vol"),
                "ifr_direct": wavg(
                    g[g["vol_direct"] > 0].rename(columns={"vol_direct": "vol", "ifr_direct": "ifr"}),
                    "ifr",
                    "vol",
                )
                if (g["vol_direct"] > 0).any()
                else float("nan"),
            }
        )
    tiers = pd.DataFrame(tier_rows)
    print("\n=== Test 4: Full-window local IFR by builder tier ===")
    print(tiers.to_string(index=False))

    # Hub-level: in Memorial Day, for each assigned hub, correlation of % directed with local IFR
    hub = hv_compare.groupby("assigned_induction_hub_name", dropna=False).apply(
        lambda g: pd.Series(
            {
                "suppliers": g["supplier_id"].nunique(),
                "vol_local": g["vol_local"].sum(),
                "vol_direct": g["vol_direct"].sum(),
                "direct_share": g["vol_direct"].sum() / max(g["vol_total_dl"].sum(), 1),
                "ifr_local": wavg(g.rename(columns={"vol_local": "vol", "ifr_local": "ifr"}), "ifr", "vol"),
            }
        ),
        include_groups=False,
    ).reset_index().sort_values("vol_local", ascending=False)
    print("\n=== Hub-level Memorial Day ===")
    print(hub.head(15).to_string(index=False))

    # Save outputs
    t1.to_csv(OUTPUT_DIR / "directs_capacity_hv_cohorts.csv", index=False)
    dose_df.to_csv(OUTPUT_DIR / "directs_capacity_dose_response.csv", index=False)
    tiers.to_csv(OUTPUT_DIR / "directs_capacity_fullwindow_tiers.csv", index=False)
    hub.to_csv(OUTPUT_DIR / "directs_capacity_hub_level_hv.csv", index=False)
    if len(matched):
        matched.to_csv(OUTPUT_DIR / "directs_capacity_vol_matched.csv", index=False)

    with pd.ExcelWriter(OUTPUT_DIR / "directs_capacity_ifr_hypothesis.xlsx", engine="openpyxl") as xw:
        t1.to_excel(xw, sheet_name="HV_builder_cohorts", index=False)
        if len(matched):
            matched.to_excel(xw, sheet_name="HV_vol_matched", index=False)
        dose_df.to_excel(xw, sheet_name="HV_dose_response", index=False)
        within.head(5000).to_excel(xw, sheet_name="within_supplier", index=False)
        tiers.to_excel(xw, sheet_name="fullwindow_tiers", index=False)
        hub.to_excel(xw, sheet_name="hub_level_HV", index=False)

    # Verdict
    builder_ifr = t1.loc[t1["cohort"].str.contains("builders \\("), "ifr_local"]
    non_ifr = t1.loc[t1["cohort"].str.contains("non-builders"), "ifr_local"]
    # fix regex - cohort names
    b_ifr = float(t1.iloc[0]["ifr_local"]) if len(t1) else float("nan")
    n_ifr = float(t1.iloc[2]["ifr_local"]) if len(t1) > 2 else float("nan")
    delta_pp = (b_ifr - n_ifr) * 100 if pd.notna(b_ifr) and pd.notna(n_ifr) else float("nan")

    supports = pd.notna(delta_pp) and delta_pp > 0.5
    contradicts = pd.notna(delta_pp) and delta_pp < -0.5

    md = []
    md.append("# Capacity hypothesis: do directs free hub capacity (higher in-hub IFR)?")
    md.append("")
    md.append("## Hypothesis")
    md.append("")
    md.append(
        "Suppliers who **build directs** divert far-market volume off the constrained SoCal hub, "
        "leaving more capacity for **in-hub / local** volume → **higher IFR** on that remaining local volume "
        "than suppliers who do not direct."
    )
    md.append("")
    md.append("**Scope:** SoCal assigned + `assigned_constrained_market = 1`, DS, May–Aug 2026 MSBD.")
    md.append("**In-hub volume:** `non_candidate` (local path) — still going into assigned SoCal hubs.")
    md.append("**Directs:** classified `direct` bucket.")
    md.append("")
    md.append("## Verdict")
    md.append("")
    if supports:
        md.append(
            f"**Supports hypothesis (weak/strong):** Memorial Day builders’ local IFR "
            f"**{b_ifr:.1%}** vs non-builders **{n_ifr:.1%}** (**{delta_pp:+.1f} pp**)."
        )
    elif contradicts:
        md.append(
            f"**Does not support hypothesis:** Memorial Day builders’ local IFR "
            f"**{b_ifr:.1%}** vs non-builders **{n_ifr:.1%}** (**{delta_pp:+.1f} pp**)."
        )
    else:
        md.append(
            f"**Inconclusive / flat:** Memorial Day builders’ local IFR "
            f"**{b_ifr:.1%}** vs non-builders **{n_ifr:.1%}** (**{delta_pp:+.1f} pp**)."
        )
    if len(within):
        md.append(
            f"Within-supplier (high-direct weeks vs no-direct weeks): "
            f"{within['positive_lift'].mean():.0%} positive lift; "
            f"vol-weighted lift **{vw_lift:+.2f} pp**."
        )
    md.append("")
    md.append("## Test 1 — Memorial Day: builders vs non-builders (local IFR)")
    md.append("")
    md.append("| Cohort | Suppliers | Local vol | Direct vol | **Local IFR** | Del (local) | vs non-builders |")
    md.append("|--------|-----------|-----------|------------|---------------|-------------|-----------------|")
    for _, r in t1.iterrows():
        md.append(
            f"| {r['cohort']} | {r['suppliers']:.0f} | {r['vol_local']:,.0f} | {r['vol_direct']:,.0f} | "
            f"**{fmt_pct(r['ifr_local'])}** | {fmt_pct(r['del_local'])} | "
            f"{r['ifr_vs_nonbuilders_pp']:+.1f} pp |"
        )
    md.append("")
    if len(matched):
        md.append("### Volume-matched bins")
        md.append("")
        md.append("| Vol bin | n builders | n non-builders | Local IFR builders | Local IFR non-builders | Δ pp |")
        md.append("|---------|------------|----------------|--------------------|------------------------|------|")
        for _, r in matched.iterrows():
            md.append(
                f"| {r['vol_bin']} | {r['n_builders']:.0f} | {r['n_nonbuilders']:.0f} | "
                f"{fmt_pct(r['ifr_local_builders'])} | {fmt_pct(r['ifr_local_nonbuilders'])} | "
                f"{r['ifr_delta_pp']:+.1f} |"
            )
        md.append("")
    md.append("## Test 2 — Dose-response (Memorial Day local IFR by direct share)")
    md.append("")
    md.append("| Direct share | Suppliers | Local vol | Direct vol | Local IFR |")
    md.append("|--------------|-----------|-----------|------------|-----------|")
    for _, r in dose_df.iterrows():
        md.append(
            f"| {r['direct_share_bin']} | {r['suppliers']:.0f} | {r['vol_local']:,.0f} | "
            f"{r['vol_direct']:,.0f} | **{fmt_pct(r['ifr_local'])}** |"
        )
    md.append("")
    md.append("## Test 3 — Within-supplier (high-direct weeks vs no-direct weeks)")
    md.append("")
    if len(within):
        md.append(
            f"n = **{len(within)}** suppliers with ≥50 local ops in both regimes."
        )
        md.append(
            f"- Positive local IFR lift: **{within['positive_lift'].mean():.1%}**"
        )
        md.append(f"- Median lift: **{within['ifr_lift_pp'].median():+.2f} pp**")
        md.append(f"- Vol-weighted lift: **{vw_lift:+.2f} pp**")
        md.append("")
        md.append("| SUID | Supplier | Local vol (high-direct wks) | IFR high-direct | Local vol (no-direct wks) | IFR no-direct | Lift pp |")
        md.append("|------|----------|------------------------------|-----------------|----------------------------|---------------|---------|")
        for _, r in within.head(20).iterrows():
            md.append(
                f"| {int(r['supplier_id'])} | {r['su_name']} | "
                f"{r['vol_local_high_direct']:,.0f} | {fmt_pct(r['ifr_local_high_direct'])} | "
                f"{r['vol_local_no_direct']:,.0f} | {fmt_pct(r['ifr_local_no_direct'])} | "
                f"{r['ifr_lift_pp']:+.1f} |"
            )
    else:
        md.append("Insufficient within-supplier pairs.")
    md.append("")
    md.append("## Test 4 — Full-window builder tier → local IFR")
    md.append("")
    md.append("| Builder tier (direct share) | Suppliers | Local vol | Direct vol | Local IFR |")
    md.append("|------------------------------|-----------|-----------|------------|-----------|")
    for _, r in tiers.iterrows():
        md.append(
            f"| {r['builder_tier']} | {r['suppliers']:.0f} | {r['vol_local']:,.0f} | "
            f"{r['vol_direct']:,.0f} | **{fmt_pct(r['ifr_local'])}** |"
        )
    md.append("")
    md.append("## How to read this for FedEx")
    md.append("")
    md.append(
        "If capacity relief were the main benefit of directs, we should see **higher IFR on remaining "
        "in-hub volume** for directs-builders (and in high-direct weeks). "
        "Use Tests 1–3 as the prove/disprove pack."
    )
    md.append("")
    md.append("## Files")
    md.append("")
    md.append("| File | Contents |")
    md.append("|------|----------|")
    md.append("| `directs_capacity_ifr_hypothesis.xlsx` | All tests |")
    md.append("| `scripts/run_directs_capacity_ifr.py` | Re-run |")

    path = OUTPUT_DIR / "directs_capacity_ifr_hypothesis.md"
    path.write_text("\n".join(md) + "\n")
    print(f"\nWrote {path}")
    print(f"\nHeadline Δ local IFR builders vs non-builders: {delta_pp:+.1f} pp")


if __name__ == "__main__":
    main()
