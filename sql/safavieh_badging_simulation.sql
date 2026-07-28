-- Safavieh parent-level fast-badge simulation
-- Scenario: all warehouses ship same-day until 2pm, zero cushion
--
-- Simulation rules (applied to each order):
--   1. If cushion > 0: subtract 1 day from o2d_stated (remove cushion padding)
--   2. If order placed before 2pm local AND not pre-cutoff (o2sumsbd > 0)
--      AND warehouse cutoff < 2pm (or null): subtract 1 day from o2d_stated
--   3. Simulated fast badge = simulated o2d_stated <= 5

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
    order_complete_date_time_local,
    inducted_on_time_or_early
  FROM `wf-gcp-us-ae-global-tnd-prod.speed_and_reliability.HVE_perf_Monitoring`
  WHERE msbd_su >= DATE_SUB(CURRENT_DATE(), INTERVAL 3 MONTH)
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
    o2d_stated
      - CASE WHEN cushion > 0 THEN 1 ELSE 0 END
      - CASE
          WHEN EXTRACT(HOUR FROM order_complete_date_time_local) < 14
            AND o2sumsbd > 0
            AND (cutoff IS NULL OR cutoff < TIME '14:00:00')
          THEN 1
          ELSE 0
        END AS sim_o2d_stated
  FROM base
)

-- Parent rollup
SELECT
  parent_su_name,
  COUNT(DISTINCT ops) AS volume,
  AVG(o2d_stated_5) AS current_fast_badge_pct,
  AVG(o2d_stated) AS current_avg_o2d_stated,
  AVG(inducted_on_time_or_early) AS ifr,
  AVG(CASE WHEN sim_o2d_stated <= 5 THEN 1 ELSE 0 END) AS sim_fast_badge_pct,
  AVG(sim_o2d_stated) AS sim_avg_o2d_stated,
  COUNT(DISTINCT CASE WHEN o2d_stated_5 = 0 AND sim_o2d_stated <= 5 THEN ops END) AS newly_fast_orders,
  COUNT(DISTINCT CASE WHEN o2d_stated_5 = 1 AND sim_o2d_stated > 5 THEN ops END) AS lost_fast_orders
FROM scored
GROUP BY parent_su_name

-- Warehouse rollup (uncomment to use instead of parent rollup)
/*
SELECT
  city_name,
  state_name,
  ANY_VALUE(cutoff) AS cutoff,
  MAX(cushion) AS max_cushion,
  COUNT(DISTINCT ops) AS volume,
  AVG(inducted_on_time_or_early) AS ifr,
  AVG(o2d_stated_5) AS current_fast_badge_pct,
  AVG(CASE WHEN sim_o2d_stated <= 5 THEN 1 ELSE 0 END) AS sim_fast_badge_pct
FROM scored
GROUP BY city_name, state_name
ORDER BY volume DESC
*/
