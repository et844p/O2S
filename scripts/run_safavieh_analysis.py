#!/usr/bin/env python3
"""
Run full Safavieh June MSBD analysis — all BigQuery pulls and CSV exports.

Data sources:
  - HVE_perf_Monitoring (IFR, badging, cutoff, cushion, o2d_stated)
  - toolkit_hourly_performance (before-2pm same-day induction / less_14_o2i_0)
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

# Parent-level badging scenarios (all tiers + newly badged counts)
SQL_BADGING_SCENARIOS = """
WITH base AS (
  SELECT
    ops, o2d_stated, cushion, o2sumsbd, cutoff,
    order_complete_date_time_local, order_dow, induction_dow_adj
  FROM `wf-gcp-us-ae-global-tnd-prod.speed_and_reliability.HVE_perf_Monitoring`
  WHERE msbd_su BETWEEN '2026-06-01' AND '2026-06-30'
    AND parent_su_name = 'Safavieh'
    AND fulfillment_type = 'DS'
    AND sto = 'Rugs'
    AND o2d_stated IS NOT NULL
),
scored AS (
  SELECT *,
    CASE WHEN cushion > 0 THEN 1 ELSE 0 END AS adj_cushion,
    CASE WHEN EXTRACT(HOUR FROM order_complete_date_time_local) < 14
      AND o2sumsbd > 0 AND (cutoff IS NULL OR cutoff < TIME '14:00:00') THEN 1 ELSE 0 END AS adj_2pm,
    CASE WHEN order_dow IN (5,6) AND induction_dow_adj NOT IN (6,7) THEN 1 ELSE 0 END AS adj_weekend
  FROM base
),
with_sim AS (
  SELECT *,
    o2d_stated AS sim_current,
    o2d_stated - adj_cushion - adj_2pm AS sim_policy,
    o2d_stated - adj_cushion - adj_2pm - adj_weekend AS sim_full
  FROM scored
)
SELECT scenario, volume, badge_1d_pct, badge_2d_pct, badge_3d_pct, badge_5d_fast_pct,
  newly_fast_1d, newly_fast_2d, newly_fast_3d, newly_fast_5d
FROM (
  SELECT 'current' AS scenario, COUNT(DISTINCT ops) AS volume,
    ROUND(AVG(CASE WHEN sim_current <= 1 THEN 1 ELSE 0 END)*100, 2) AS badge_1d_pct,
    ROUND(AVG(CASE WHEN sim_current <= 2 THEN 1 ELSE 0 END)*100, 2) AS badge_2d_pct,
    ROUND(AVG(CASE WHEN sim_current <= 3 THEN 1 ELSE 0 END)*100, 2) AS badge_3d_pct,
    ROUND(AVG(CASE WHEN sim_current <= 5 THEN 1 ELSE 0 END)*100, 2) AS badge_5d_fast_pct,
    0 AS newly_fast_1d, 0 AS newly_fast_2d, 0 AS newly_fast_3d, 0 AS newly_fast_5d
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
    COUNT(DISTINCT CASE WHEN sim_current > 5 AND sim_policy <= 5 THEN ops END)
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
    COUNT(DISTINCT CASE WHEN sim_current > 5 AND sim_full <= 5 THEN ops END)
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
    print("\nDone. Next steps:")
    print("  python scripts/analyze_safavieh_charts.py")
    print("  python scripts/create_safavieh_google_slides.py")


if __name__ == "__main__":
    main()
