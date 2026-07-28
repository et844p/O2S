-- Safavieh parent-level fast-badge simulation
-- Base: June 2026 MSBD (msbd_su BETWEEN '2026-06-01' AND '2026-06-30')
-- Scenarios: current | policy (2pm + no cushion) | full (+ weekend shipping)
--
-- Simulation rules (stacked):
--   1. If cushion > 0: subtract 1 day from o2d_stated
--   2. If order before 2pm local AND not pre-cutoff (o2sumsbd > 0)
--      AND warehouse cutoff < 2pm (or null): subtract 1 day
--   3. If Fri/Sat placed AND not inducted Sat/Sun: subtract 1 day
--   4. Simulated fast badge = simulated o2d_stated <= 5

WITH base AS (
  SELECT
    ops,
    parent_su_name,
    supplier_id,
    su_name,
    city_name,
    state_name,
    cutoff,
    cushion,
    o2d_stated,
    o2d_stated_5,
    o2sumsbd,
    order_dow,
    induction_dow_adj,
    order_complete_date_time_local,
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
    END AS adj_weekend,
    o2d_stated AS sim_current,
    o2d_stated
      - CASE WHEN cushion > 0 THEN 1 ELSE 0 END
      - CASE
          WHEN EXTRACT(HOUR FROM order_complete_date_time_local) < 14
            AND o2sumsbd > 0
            AND (cutoff IS NULL OR cutoff < TIME '14:00:00')
          THEN 1
          ELSE 0
        END AS sim_policy,
    o2d_stated
      - CASE WHEN cushion > 0 THEN 1 ELSE 0 END
      - CASE
          WHEN EXTRACT(HOUR FROM order_complete_date_time_local) < 14
            AND o2sumsbd > 0
            AND (cutoff IS NULL OR cutoff < TIME '14:00:00')
          THEN 1
          ELSE 0
        END
      - CASE
          WHEN order_dow IN (5, 6) AND induction_dow_adj NOT IN (6, 7)
          THEN 1
          ELSE 0
        END AS sim_full
  FROM base
)

SELECT
  parent_su_name,
  COUNT(DISTINCT ops) AS volume,
  AVG(o2d_stated_5) AS current_fast_badge_pct,
  AVG(CASE WHEN sim_policy <= 5 THEN 1 ELSE 0 END) AS policy_fast_badge_pct,
  AVG(CASE WHEN sim_full <= 5 THEN 1 ELSE 0 END) AS full_sim_fast_badge_pct,
  AVG(inducted_on_time_or_early) AS ifr,
  COUNT(DISTINCT CASE WHEN o2d_stated_5 = 0 AND sim_policy <= 5 THEN ops END) AS newly_fast_policy,
  COUNT(DISTINCT CASE WHEN o2d_stated_5 = 0 AND sim_full <= 5 THEN ops END) AS newly_fast_full,
  SUM(adj_cushion) AS orders_adj_cushion,
  SUM(adj_2pm) AS orders_adj_2pm,
  SUM(adj_weekend) AS orders_adj_weekend
FROM scored
GROUP BY parent_su_name
