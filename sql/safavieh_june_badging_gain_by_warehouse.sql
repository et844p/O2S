-- Safavieh June MSBD — badging cohorts: current, cutoff-policy gain, weekend gain
-- Parent rollup + warehouse breakout (city/state)
-- Policy = zero cushion + weekday cutoff extension to 2pm (IsBeforeCutoff=0, hour≤14)
-- Weekend = Fri/Sat Sun MSBD promise (incremental after policy)

WITH base AS (
  SELECT
    ops,
    TRIM(city_name) AS city_name,
    state_name,
    o2d_stated,
    cushion,
    order_dow
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
    b.*,
    CASE WHEN b.cushion > 0 THEN 1 ELSE 0 END AS adj_cushion,
    CASE
      WHEN b.order_dow IN (1, 2, 3, 4, 5)
        AND t.is_before_cutoff = 0
        AND t.order_hour_supplier_local <= 14
      THEN 1
      ELSE 0
    END AS adj_2pm,
    CASE WHEN b.order_dow IN (5, 6) THEN 1 ELSE 0 END AS adj_weekend,
    b.o2d_stated AS sim_current,
    b.o2d_stated
      - CASE WHEN b.cushion > 0 THEN 1 ELSE 0 END
      - CASE
          WHEN b.order_dow IN (1, 2, 3, 4, 5)
            AND t.is_before_cutoff = 0
            AND t.order_hour_supplier_local <= 14
          THEN 1
          ELSE 0
        END AS sim_policy,
    b.o2d_stated
      - CASE WHEN b.cushion > 0 THEN 1 ELSE 0 END
      - CASE
          WHEN b.order_dow IN (1, 2, 3, 4, 5)
            AND t.is_before_cutoff = 0
            AND t.order_hour_supplier_local <= 14
          THEN 1
          ELSE 0
        END
      - CASE WHEN b.order_dow IN (5, 6) THEN 1 ELSE 0 END AS sim_full
  FROM base b
  LEFT JOIN toolkit t ON b.ops = t.ops
),

warehouse AS (
  SELECT
    'warehouse' AS level,
    city_name,
    state_name,
    COUNT(DISTINCT ops) AS vol,
    -- current %
    ROUND(AVG(CASE WHEN sim_current <= 1 THEN 1 ELSE 0 END) * 100, 2) AS current_1d_pct,
    ROUND(AVG(CASE WHEN sim_current <= 2 THEN 1 ELSE 0 END) * 100, 2) AS current_2d_pct,
    ROUND(AVG(CASE WHEN sim_current <= 3 THEN 1 ELSE 0 END) * 100, 2) AS current_3d_pct,
    ROUND(AVG(CASE WHEN sim_current <= 5 THEN 1 ELSE 0 END) * 100, 2) AS current_fast_pct,
    -- cutoff policy gain (pp)
    ROUND((AVG(CASE WHEN sim_policy <= 1 THEN 1 ELSE 0 END)
      - AVG(CASE WHEN sim_current <= 1 THEN 1 ELSE 0 END)) * 100, 2) AS cutoff_gain_1d_pp,
    ROUND((AVG(CASE WHEN sim_policy <= 2 THEN 1 ELSE 0 END)
      - AVG(CASE WHEN sim_current <= 2 THEN 1 ELSE 0 END)) * 100, 2) AS cutoff_gain_2d_pp,
    ROUND((AVG(CASE WHEN sim_policy <= 3 THEN 1 ELSE 0 END)
      - AVG(CASE WHEN sim_current <= 3 THEN 1 ELSE 0 END)) * 100, 2) AS cutoff_gain_3d_pp,
    ROUND((AVG(CASE WHEN sim_policy <= 5 THEN 1 ELSE 0 END)
      - AVG(CASE WHEN sim_current <= 5 THEN 1 ELSE 0 END)) * 100, 2) AS cutoff_gain_fast_pp,
    -- weekend gain (pp, after policy)
    ROUND((AVG(CASE WHEN sim_full <= 1 THEN 1 ELSE 0 END)
      - AVG(CASE WHEN sim_policy <= 1 THEN 1 ELSE 0 END)) * 100, 2) AS weekend_gain_1d_pp,
    ROUND((AVG(CASE WHEN sim_full <= 2 THEN 1 ELSE 0 END)
      - AVG(CASE WHEN sim_policy <= 2 THEN 1 ELSE 0 END)) * 100, 2) AS weekend_gain_2d_pp,
    ROUND((AVG(CASE WHEN sim_full <= 3 THEN 1 ELSE 0 END)
      - AVG(CASE WHEN sim_policy <= 3 THEN 1 ELSE 0 END)) * 100, 2) AS weekend_gain_3d_pp,
    ROUND((AVG(CASE WHEN sim_full <= 5 THEN 1 ELSE 0 END)
      - AVG(CASE WHEN sim_policy <= 5 THEN 1 ELSE 0 END)) * 100, 2) AS weekend_gain_fast_pp,
    -- newly badged orders from cutoff policy
    COUNT(DISTINCT CASE WHEN sim_current > 1 AND sim_policy <= 1 THEN ops END) AS cutoff_new_1d,
    COUNT(DISTINCT CASE WHEN sim_current > 2 AND sim_policy <= 2 THEN ops END) AS cutoff_new_2d,
    COUNT(DISTINCT CASE WHEN sim_current > 3 AND sim_policy <= 3 THEN ops END) AS cutoff_new_3d,
    COUNT(DISTINCT CASE WHEN sim_current > 5 AND sim_policy <= 5 THEN ops END) AS cutoff_new_fast,
    -- newly badged from weekend (after policy)
    COUNT(DISTINCT CASE WHEN sim_policy > 1 AND sim_full <= 1 THEN ops END) AS weekend_new_1d,
    COUNT(DISTINCT CASE WHEN sim_policy > 2 AND sim_full <= 2 THEN ops END) AS weekend_new_2d,
    COUNT(DISTINCT CASE WHEN sim_policy > 3 AND sim_full <= 3 THEN ops END) AS weekend_new_3d,
    COUNT(DISTINCT CASE WHEN sim_policy > 5 AND sim_full <= 5 THEN ops END) AS weekend_new_fast
  FROM scored
  GROUP BY city_name, state_name
),

account AS (
  SELECT
    'account' AS level,
    'Safavieh (parent)' AS city_name,
    CAST(NULL AS STRING) AS state_name,
    COUNT(DISTINCT ops) AS vol,
    ROUND(AVG(CASE WHEN sim_current <= 1 THEN 1 ELSE 0 END) * 100, 2) AS current_1d_pct,
    ROUND(AVG(CASE WHEN sim_current <= 2 THEN 1 ELSE 0 END) * 100, 2) AS current_2d_pct,
    ROUND(AVG(CASE WHEN sim_current <= 3 THEN 1 ELSE 0 END) * 100, 2) AS current_3d_pct,
    ROUND(AVG(CASE WHEN sim_current <= 5 THEN 1 ELSE 0 END) * 100, 2) AS current_fast_pct,
    ROUND((AVG(CASE WHEN sim_policy <= 1 THEN 1 ELSE 0 END)
      - AVG(CASE WHEN sim_current <= 1 THEN 1 ELSE 0 END)) * 100, 2) AS cutoff_gain_1d_pp,
    ROUND((AVG(CASE WHEN sim_policy <= 2 THEN 1 ELSE 0 END)
      - AVG(CASE WHEN sim_current <= 2 THEN 1 ELSE 0 END)) * 100, 2) AS cutoff_gain_2d_pp,
    ROUND((AVG(CASE WHEN sim_policy <= 3 THEN 1 ELSE 0 END)
      - AVG(CASE WHEN sim_current <= 3 THEN 1 ELSE 0 END)) * 100, 2) AS cutoff_gain_3d_pp,
    ROUND((AVG(CASE WHEN sim_policy <= 5 THEN 1 ELSE 0 END)
      - AVG(CASE WHEN sim_current <= 5 THEN 1 ELSE 0 END)) * 100, 2) AS cutoff_gain_fast_pp,
    ROUND((AVG(CASE WHEN sim_full <= 1 THEN 1 ELSE 0 END)
      - AVG(CASE WHEN sim_policy <= 1 THEN 1 ELSE 0 END)) * 100, 2) AS weekend_gain_1d_pp,
    ROUND((AVG(CASE WHEN sim_full <= 2 THEN 1 ELSE 0 END)
      - AVG(CASE WHEN sim_policy <= 2 THEN 1 ELSE 0 END)) * 100, 2) AS weekend_gain_2d_pp,
    ROUND((AVG(CASE WHEN sim_full <= 3 THEN 1 ELSE 0 END)
      - AVG(CASE WHEN sim_policy <= 3 THEN 1 ELSE 0 END)) * 100, 2) AS weekend_gain_3d_pp,
    ROUND((AVG(CASE WHEN sim_full <= 5 THEN 1 ELSE 0 END)
      - AVG(CASE WHEN sim_policy <= 5 THEN 1 ELSE 0 END)) * 100, 2) AS weekend_gain_fast_pp,
    COUNT(DISTINCT CASE WHEN sim_current > 1 AND sim_policy <= 1 THEN ops END) AS cutoff_new_1d,
    COUNT(DISTINCT CASE WHEN sim_current > 2 AND sim_policy <= 2 THEN ops END) AS cutoff_new_2d,
    COUNT(DISTINCT CASE WHEN sim_current > 3 AND sim_policy <= 3 THEN ops END) AS cutoff_new_3d,
    COUNT(DISTINCT CASE WHEN sim_current > 5 AND sim_policy <= 5 THEN ops END) AS cutoff_new_fast,
    COUNT(DISTINCT CASE WHEN sim_policy > 1 AND sim_full <= 1 THEN ops END) AS weekend_new_1d,
    COUNT(DISTINCT CASE WHEN sim_policy > 2 AND sim_full <= 2 THEN ops END) AS weekend_new_2d,
    COUNT(DISTINCT CASE WHEN sim_policy > 3 AND sim_full <= 3 THEN ops END) AS weekend_new_3d,
    COUNT(DISTINCT CASE WHEN sim_policy > 5 AND sim_full <= 5 THEN ops END) AS weekend_new_fast
  FROM scored
)

SELECT
  level,
  city_name,
  state_name,
  vol,
  current_1d_pct,
  current_2d_pct,
  current_3d_pct,
  current_fast_pct,
  cutoff_gain_1d_pp,
  cutoff_gain_2d_pp,
  cutoff_gain_3d_pp,
  cutoff_gain_fast_pp,
  weekend_gain_1d_pp,
  weekend_gain_2d_pp,
  weekend_gain_3d_pp,
  weekend_gain_fast_pp,
  cutoff_new_1d,
  cutoff_new_2d,
  cutoff_new_3d,
  cutoff_new_fast,
  weekend_new_1d,
  weekend_new_2d,
  weekend_new_3d,
  weekend_new_fast
FROM warehouse
UNION ALL
SELECT
  level,
  city_name,
  state_name,
  vol,
  current_1d_pct,
  current_2d_pct,
  current_3d_pct,
  current_fast_pct,
  cutoff_gain_1d_pp,
  cutoff_gain_2d_pp,
  cutoff_gain_3d_pp,
  cutoff_gain_fast_pp,
  weekend_gain_1d_pp,
  weekend_gain_2d_pp,
  weekend_gain_3d_pp,
  weekend_gain_fast_pp,
  cutoff_new_1d,
  cutoff_new_2d,
  cutoff_new_3d,
  cutoff_new_fast,
  weekend_new_1d,
  weekend_new_2d,
  weekend_new_3d,
  weekend_new_fast
FROM account
ORDER BY CASE level WHEN 'account' THEN 0 ELSE 1 END, vol DESC
