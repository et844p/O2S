-- Safavieh warehouse-level badging simulation (June MSBD)
-- Badge tiers: sim_o2d_stated <= N days — current vs full simulation

WITH base AS (
  SELECT
    ops,
    city_name,
    state_name,
    o2d_stated,
    cushion,
    o2sumsbd,
    cutoff,
    order_complete_date_time_local,
    order_dow,
    induction_dow_adj,
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
    ops,
    city_name,
    state_name,
    inducted_on_time_or_early,
    o2d_stated AS sim_current,
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
  TRIM(city_name) AS city_name,
  state_name,
  COUNT(DISTINCT ops) AS vol,
  ROUND(AVG(CASE WHEN sim_current <= 1 THEN 1 ELSE 0 END), 4) AS current_1d,
  ROUND(AVG(CASE WHEN sim_full <= 1 THEN 1 ELSE 0 END), 4) AS sim_1d,
  ROUND(AVG(CASE WHEN sim_current <= 2 THEN 1 ELSE 0 END), 4) AS current_2d,
  ROUND(AVG(CASE WHEN sim_full <= 2 THEN 1 ELSE 0 END), 4) AS sim_2d,
  ROUND(AVG(CASE WHEN sim_current <= 3 THEN 1 ELSE 0 END), 4) AS current_3d,
  ROUND(AVG(CASE WHEN sim_full <= 3 THEN 1 ELSE 0 END), 4) AS sim_3d,
  ROUND(AVG(CASE WHEN sim_current <= 5 THEN 1 ELSE 0 END), 4) AS current_5d,
  ROUND(AVG(CASE WHEN sim_full <= 5 THEN 1 ELSE 0 END), 4) AS sim_5d,
  ROUND(AVG(inducted_on_time_or_early), 4) AS ifr
FROM scored
GROUP BY city_name, state_name
HAVING vol >= 200
ORDER BY vol DESC
