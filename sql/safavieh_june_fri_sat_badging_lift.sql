-- Safavieh June MSBD — badge lift from Fri/Sat Sunday MSBD promise
-- Rule: all June MSBD orders; if placed Fri/Sat (order_dow 5–6 ISO), subtract 1 from o2d_stated
-- Lift = sim_fri_sat_minus1 vs current stated badges (not incremental after cutoff policy)

WITH base AS (
  SELECT
    ops,
    TRIM(city_name) AS city_name,
    state_name,
    o2d_stated,
    order_dow
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
    o2d_stated AS sim_current,
    o2d_stated - CASE WHEN order_dow IN (5, 6) THEN 1 ELSE 0 END AS sim_fri_sat_minus1,
    CASE WHEN order_dow IN (5, 6) THEN 1 ELSE 0 END AS is_fri_sat
  FROM base
),

agg AS (
  SELECT
    level,
    city_name,
    state_name,
    COUNT(DISTINCT ops) AS vol,
    COUNT(DISTINCT CASE WHEN is_fri_sat = 1 THEN ops END) AS fri_sat_vol,
    ROUND(AVG(CASE WHEN sim_current <= 1 THEN 1 ELSE 0 END) * 100, 2) AS current_1d_pct,
    ROUND(AVG(CASE WHEN sim_current <= 2 THEN 1 ELSE 0 END) * 100, 2) AS current_2d_pct,
    ROUND(AVG(CASE WHEN sim_current <= 3 THEN 1 ELSE 0 END) * 100, 2) AS current_3d_pct,
    ROUND(AVG(CASE WHEN sim_current <= 5 THEN 1 ELSE 0 END) * 100, 2) AS current_fast_pct,
    ROUND(AVG(CASE WHEN sim_fri_sat_minus1 <= 1 THEN 1 ELSE 0 END) * 100, 2) AS sim_1d_pct,
    ROUND(AVG(CASE WHEN sim_fri_sat_minus1 <= 2 THEN 1 ELSE 0 END) * 100, 2) AS sim_2d_pct,
    ROUND(AVG(CASE WHEN sim_fri_sat_minus1 <= 3 THEN 1 ELSE 0 END) * 100, 2) AS sim_3d_pct,
    ROUND(AVG(CASE WHEN sim_fri_sat_minus1 <= 5 THEN 1 ELSE 0 END) * 100, 2) AS sim_fast_pct,
    ROUND((AVG(CASE WHEN sim_fri_sat_minus1 <= 1 THEN 1 ELSE 0 END)
      - AVG(CASE WHEN sim_current <= 1 THEN 1 ELSE 0 END)) * 100, 2) AS lift_1d_pp,
    ROUND((AVG(CASE WHEN sim_fri_sat_minus1 <= 2 THEN 1 ELSE 0 END)
      - AVG(CASE WHEN sim_current <= 2 THEN 1 ELSE 0 END)) * 100, 2) AS lift_2d_pp,
    ROUND((AVG(CASE WHEN sim_fri_sat_minus1 <= 3 THEN 1 ELSE 0 END)
      - AVG(CASE WHEN sim_current <= 3 THEN 1 ELSE 0 END)) * 100, 2) AS lift_3d_pp,
    ROUND((AVG(CASE WHEN sim_fri_sat_minus1 <= 5 THEN 1 ELSE 0 END)
      - AVG(CASE WHEN sim_current <= 5 THEN 1 ELSE 0 END)) * 100, 2) AS lift_fast_pp,
    COUNT(DISTINCT CASE WHEN sim_current > 1 AND sim_fri_sat_minus1 <= 1 THEN ops END) AS new_1d,
    COUNT(DISTINCT CASE WHEN sim_current > 2 AND sim_fri_sat_minus1 <= 2 THEN ops END) AS new_2d,
    COUNT(DISTINCT CASE WHEN sim_current > 3 AND sim_fri_sat_minus1 <= 3 THEN ops END) AS new_3d,
    COUNT(DISTINCT CASE WHEN sim_current > 5 AND sim_fri_sat_minus1 <= 5 THEN ops END) AS new_fast
  FROM (
    SELECT
      'warehouse' AS level,
      city_name,
      state_name,
      ops,
      is_fri_sat,
      sim_current,
      sim_fri_sat_minus1
    FROM scored
    UNION ALL
    SELECT
      'account' AS level,
      'Safavieh (parent)' AS city_name,
      CAST(NULL AS STRING) AS state_name,
      ops,
      is_fri_sat,
      sim_current,
      sim_fri_sat_minus1
    FROM scored
  )
  GROUP BY level, city_name, state_name
)

SELECT *
FROM agg
WHERE level = 'account'
   OR (level = 'warehouse' AND vol >= 200)
ORDER BY CASE level WHEN 'account' THEN 0 ELSE 1 END, vol DESC
