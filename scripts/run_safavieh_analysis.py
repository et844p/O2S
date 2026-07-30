#!/usr/bin/env python3
"""
Run full Safavieh June MSBD analysis — all BigQuery pulls and CSV exports.

Data sources:
  - HVE_perf_Monitoring (IFR, badging, cutoff, cushion, o2d_stated)
  - toolkit_hourly_performance (before-2pm same-day induction / less_14_o2i_0)
      DOW convention: order_dow_supplier_local 1=Sunday, 7=Saturday;
      NOT IN (1,7) = Monday–Friday only
  - tbl_supplier + tbl_supplier_ext (Mas_SuID)

Outputs (output/safavieh/):
  - safavieh_june_warehouse_analysis.csv
  - safavieh_june_badging_scenarios.csv
  - safavieh_june_wh_badging_sim.csv

Optional follow-ups:
  python scripts/analyze_safavieh_charts.py      # charts
  python scripts/create_safavieh_google_slides.py  # PPTX deck
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

_default_creds = ROOT / ".gcp" / "credentials.json"
if _default_creds.exists():
    os.environ.setdefault("GOOGLE_APPLICATION_CREDENTIALS", str(_default_creds))

from gbq import query_df

SQL_DIR = ROOT / "sql"
OUT = ROOT / "output" / "safavieh"

# Parent-level badging scenarios (stated promise model; toolkit IsBeforeCutoff for cutoff extension)
SQL_BADGING_SCENARIOS = """
WITH base AS (
  SELECT ops, o2d_stated, cushion, order_dow
  FROM `wf-gcp-us-ae-global-tnd-prod.speed_and_reliability.HVE_perf_Monitoring`
  WHERE msbd_su BETWEEN '2026-06-01' AND '2026-06-30'
    AND parent_su_name = 'Safavieh'
    AND fulfillment_type = 'DS'
    AND sto = 'Rugs'
    AND o2d_stated IS NOT NULL
),
toolkit AS (
  SELECT
    CAST(opid AS INT64) AS ops,
    MAX(IsBeforeCutoff) AS is_before_cutoff,
    MAX(order_hour_supplier_local) AS order_hour_supplier_local
  FROM `wf-gcp-us-ae-global-tnd-prod.speed_and_reliability.toolkit_hourly_performance`
  WHERE order_complete_date BETWEEN '2026-06-01' AND '2026-06-30'
    AND ship_class_group = 'Small Parcel'
    AND CAST(opid AS STRING) NOT LIKE '8%'
  GROUP BY 1
),
scored AS (
  SELECT
    b.ops,
    b.o2d_stated,
    CASE WHEN b.cushion > 0 THEN 1 ELSE 0 END AS adj_cushion,
    CASE
      WHEN b.order_dow IN (1, 2, 3, 4, 5)
        AND t.is_before_cutoff = 0 AND t.order_hour_supplier_local <= 14 THEN 1
      ELSE 0
    END AS adj_2pm,
    CASE WHEN b.order_dow IN (5, 6) THEN 1 ELSE 0 END AS adj_weekend
  FROM base b
  LEFT JOIN toolkit t ON b.ops = t.ops
),
with_sim AS (
  SELECT *,
    o2d_stated AS sim_current,
    o2d_stated - adj_cushion - adj_2pm AS sim_policy,
    o2d_stated - adj_cushion - adj_2pm - adj_weekend AS sim_full
  FROM scored
)
SELECT scenario, volume, badge_1d_pct, badge_2d_pct, badge_3d_pct, badge_5d_fast_pct,
  newly_fast_1d, newly_fast_2d, newly_fast_3d, newly_fast_5d,
  wknd_incr_1d, wknd_incr_2d, wknd_incr_3d, wknd_incr_5d
FROM (
  SELECT 'current' AS scenario, COUNT(DISTINCT ops) AS volume,
    ROUND(AVG(CASE WHEN sim_current <= 1 THEN 1 ELSE 0 END)*100, 2) AS badge_1d_pct,
    ROUND(AVG(CASE WHEN sim_current <= 2 THEN 1 ELSE 0 END)*100, 2) AS badge_2d_pct,
    ROUND(AVG(CASE WHEN sim_current <= 3 THEN 1 ELSE 0 END)*100, 2) AS badge_3d_pct,
    ROUND(AVG(CASE WHEN sim_current <= 5 THEN 1 ELSE 0 END)*100, 2) AS badge_5d_fast_pct,
    0 AS newly_fast_1d, 0 AS newly_fast_2d, 0 AS newly_fast_3d, 0 AS newly_fast_5d,
    0 AS wknd_incr_1d, 0 AS wknd_incr_2d, 0 AS wknd_incr_3d, 0 AS wknd_incr_5d
  FROM with_sim
  UNION ALL
  SELECT 'policy_2pm_no_cushion', COUNT(DISTINCT ops),
    ROUND(AVG(CASE WHEN sim_policy <= 1 THEN 1 ELSE 0 END)*100, 2),
    ROUND(AVG(CASE WHEN sim_policy <= 2 THEN 1 ELSE 0 END)*100, 2),
    ROUND(AVG(CASE WHEN sim_policy <= 3 THEN 1 ELSE 0 END)*100, 2),
    ROUND(AVG(CASE WHEN sim_policy <= 5 THEN 1 ELSE 0 END)*100, 2),
    COUNT(DISTINCT CASE WHEN sim_current > 1 AND sim_policy <= 1 THEN ops END),
    COUNT(DISTINCT CASE WHEN sim_current > 2 AND sim_policy <= 2 THEN ops END),
    COUNT(DISTINCT CASE WHEN sim_current > 3 AND sim_policy <= 3 THEN ops END),
    COUNT(DISTINCT CASE WHEN sim_current > 5 AND sim_policy <= 5 THEN ops END),
    0, 0, 0, 0
  FROM with_sim
  UNION ALL
  SELECT 'policy_plus_weekend', COUNT(DISTINCT ops),
    ROUND(AVG(CASE WHEN sim_full <= 1 THEN 1 ELSE 0 END)*100, 2),
    ROUND(AVG(CASE WHEN sim_full <= 2 THEN 1 ELSE 0 END)*100, 2),
    ROUND(AVG(CASE WHEN sim_full <= 3 THEN 1 ELSE 0 END)*100, 2),
    ROUND(AVG(CASE WHEN sim_full <= 5 THEN 1 ELSE 0 END)*100, 2),
    COUNT(DISTINCT CASE WHEN sim_current > 1 AND sim_full <= 1 THEN ops END),
    COUNT(DISTINCT CASE WHEN sim_current > 2 AND sim_full <= 2 THEN ops END),
    COUNT(DISTINCT CASE WHEN sim_current > 3 AND sim_full <= 3 THEN ops END),
    COUNT(DISTINCT CASE WHEN sim_current > 5 AND sim_full <= 5 THEN ops END),
    COUNT(DISTINCT CASE WHEN sim_policy > 1 AND sim_full <= 1 THEN ops END),
    COUNT(DISTINCT CASE WHEN sim_policy > 2 AND sim_full <= 2 THEN ops END),
    COUNT(DISTINCT CASE WHEN sim_policy > 3 AND sim_full <= 3 THEN ops END),
    COUNT(DISTINCT CASE WHEN sim_policy > 5 AND sim_full <= 5 THEN ops END)
  FROM with_sim
)
ORDER BY CASE scenario WHEN 'current' THEN 1 WHEN 'policy_2pm_no_cushion' THEN 2 ELSE 3 END
"""


def run_query(name: str, sql: str | Path, out_csv: Path) -> None:
    if isinstance(sql, Path):
        sql = sql.read_text()
    print(f"Running {name}...")
    df = query_df(sql)
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_csv, index=False)
    print(f"  → {out_csv} ({len(df)} rows)")


def main() -> None:
    run_query(
        "warehouse + before-2pm O2I (massuid)",
        SQL_DIR / "safavieh_june_msbd_warehouse_analysis.sql",
        OUT / "safavieh_june_warehouse_analysis.csv",
    )
    run_query(
        "parent badging scenarios (1/2/3/5-day)",
        SQL_BADGING_SCENARIOS,
        OUT / "safavieh_june_badging_scenarios.csv",
    )
    run_query(
        "warehouse badging simulation",
        SQL_DIR / "safavieh_june_wh_badging_simulation.sql",
        OUT / "safavieh_june_wh_badging_sim.csv",
    )
    run_query(
        "parent badging (SQL file variant)",
        SQL_DIR / "safavieh_badging_simulation.sql",
        OUT / "safavieh_june_badging_parent_sql.csv",
    )
    run_query(
        "supplier badging cohorts + before-2pm O2I",
        SQL_DIR / "safavieh_june_supplier_badging_cohorts.sql",
        OUT / "safavieh_june_supplier_badging_cohorts.csv",
    )
    run_query(
        "badging gain by warehouse (cutoff vs weekend)",
        SQL_DIR / "safavieh_june_badging_gain_by_warehouse.sql",
        OUT / "safavieh_june_badging_gain_by_warehouse.csv",
    )
    run_query(
        "Fri/Sat Sunday induction by warehouse",
        SQL_DIR / "safavieh_june_fri_sat_sunday_induction_by_wh.sql",
        OUT / "safavieh_june_fri_sat_sunday_induction_by_wh.csv",
    )
    print("\nDone. Next steps:")
    print("  python scripts/analyze_safavieh_charts.py")
    print("  python scripts/create_safavieh_google_slides.py")


if __name__ == "__main__":
    main()
