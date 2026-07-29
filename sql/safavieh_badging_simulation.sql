-- Safavieh parent-level badging simulation (1 / 2 / 3 / 5-day tiers)
-- Base: June 2026 MSBD (msbd_su BETWEEN '2026-06-01' AND '2026-06-30')
-- Scenarios: current | policy (2pm + no cushion) | full (+ weekend shipping)
--
-- Badge tiers: sim_o2d_stated <= N days (1-day, 2-day, 3-day, fast/5-day)
--
-- Simulation rules (stacked):
--   1. If cushion > 0: subtract 1 day from o2d_stated
--   2. If order before 2pm local AND not pre-cutoff (o2sumsbd > 0)
--      AND warehouse cutoff < 2pm (or null): subtract 1 day
--   3. If Fri/Sat placed AND not inducted Sat/Sun: subtract 1 day

WITH base AS (
  SELECT
    ops,
    parent_su_name,
    o2d_stated,
    cushion,
    o2sumsbd,
    order_dow,
    induction_dow_adj,
    order_complete_date_time_local,
    cutoff,
    inducted_on_time_or_early
  FROM `wf-gcp-us-ae-global-tnd-prod.speed_and_reliability.HVE_perf_Monitoring`
  WHERE msbd_su BETWEEN '2026-06-01' AND '2026-06-30'
    AND parent_su_name = 'Safavieh'
    AND fulfillment_type = 'DS'
    AND sto = 'Rugs'
    AND o2d_stated IS NOT NULL
),

scored AS (
  SELECT
    *,
    CASE WHEN cushion > 0 THEN 1 ELSE 0 END AS adj_cushion,
    CASE
      WHEN EXTRACT(HOUR FROM order_complete_date_time_local) < 14
        AND o2sumsbd > 0
        AND (cutoff IS NULL OR cutoff < TIME '14:00:00')
      THEN 1
      ELSE 0
    END AS adj_2pm,
    CASE
      WHEN order_dow IN (5, 6) AND induction_dow_adj NOT IN (6, 7)
      THEN 1
      ELSE 0
    END AS adj_weekend
  FROM base
),

with_sim AS (
  SELECT
    *,
    o2d_stated AS sim_current,
    o2d_stated - adj_cushion - adj_2pm AS sim_policy,
    o2d_stated - adj_cushion - adj_2pm - adj_weekend AS sim_full
  FROM scored
)

SELECT
  parent_su_name,
  scenario,
  COUNT(DISTINCT ops) AS volume,
  AVG(CASE WHEN sim_o2d <= 1 THEN 1 ELSE 0 END) AS badge_1d_pct,
  AVG(CASE WHEN sim_o2d <= 2 THEN 1 ELSE 0 END) AS badge_2d_pct,
  AVG(CASE WHEN sim_o2d <= 3 THEN 1 ELSE 0 END) AS badge_3d_pct,
  AVG(CASE WHEN sim_o2d <= 5 THEN 1 ELSE 0 END) AS badge_5d_fast_pct,
  COUNT(DISTINCT CASE WHEN sim_current > 1 AND sim_o2d <= 1 THEN ops END) AS newly_badge_1d,
  COUNT(DISTINCT CASE WHEN sim_current > 2 AND sim_o2d <= 2 THEN ops END) AS newly_badge_2d,
  COUNT(DISTINCT CASE WHEN sim_current > 3 AND sim_o2d <= 3 THEN ops END) AS newly_badge_3d,
  COUNT(DISTINCT CASE WHEN sim_current > 5 AND sim_o2d <= 5 THEN ops END) AS newly_badge_5d
FROM (
  SELECT parent_su_name, ops, sim_current, sim_policy AS sim_o2d, 'policy_2pm_no_cushion' AS scenario
  FROM with_sim
  UNION ALL
  SELECT parent_su_name, ops, sim_current, sim_full, 'policy_plus_weekend'
  FROM with_sim
  UNION ALL
  SELECT parent_su_name, ops, sim_current, sim_current, 'current'
  FROM with_sim
)
GROUP BY parent_su_name, scenario
ORDER BY CASE scenario WHEN 'current' THEN 1 WHEN 'policy_2pm_no_cushion' THEN 2 ELSE 3 END
