-- Safavieh warehouse-level badging simulation (June MSBD)
-- Badge tiers: sim_o2d_stated <= N days — current vs full simulation (stated promise model)

WITH base AS (
  SELECT
    ops,
    city_name,
    state_name,
    o2d_stated,
    cushion,
    order_dow,
    inducted_on_time_or_early
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
    b.city_name,
    b.state_name,
    b.inducted_on_time_or_early,
    b.o2d_stated AS sim_current,
    b.o2d_stated
      - CASE WHEN b.cushion > 0 THEN 1 ELSE 0 END
      - CASE
          WHEN b.order_dow IN (1, 2, 3, 4, 5)
            AND t.is_before_cutoff = 0
            AND t.order_hour_supplier_local <= 14
          THEN 1
          ELSE 0
        END
      - CASE
          WHEN b.order_dow IN (5, 6)
          THEN 1
          ELSE 0
        END AS sim_full
  FROM base b
  LEFT JOIN toolkit t ON b.ops = t.ops
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
