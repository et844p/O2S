-- Enabled Safavieh warehouses — pre/post enable Sunday & weekend induction (induction_dow_adj)
-- Pre-enable window: order_complete_date 2026-05-31 through 2026-07-04
-- Post-enable: order_complete_date >= 2026-07-07
-- Fri/Sat placed: order_dow IN (5, 6)
-- induction_dow_adj: Sunday = 1, Saturday = 7
-- Weekend Sat/Sun: induction_dow_adj IN (1, 7)

WITH enabled_wh AS (
  SELECT supplier_id, su_name
  FROM UNNEST([
    STRUCT(93132 AS supplier_id, 'Safavieh IN46075' AS su_name),
    STRUCT(223799 AS supplier_id, 'Safavieh Texas' AS su_name),
    STRUCT(59119 AS supplier_id, 'Safavieh CA 92518' AS su_name),
    STRUCT(34809 AS supplier_id, 'Safavieh GA31407 B' AS su_name)
  ])
),

base AS (
  SELECT
    h.supplier_id,
    h.su_name,
    h.ops,
    h.order_dow,
    h.induction_dow_adj,
    h.order_complete_date,
    DATE_TRUNC(h.order_complete_date, WEEK(SUNDAY)) AS week_start
  FROM `wf-gcp-us-ae-global-tnd-prod.speed_and_reliability.HVE_perf_Monitoring` h
  INNER JOIN enabled_wh e ON e.supplier_id = h.supplier_id
  WHERE h.parent_su_name = 'Safavieh'
    AND h.fulfillment_type = 'DS'
    AND h.sto = 'Rugs'
    AND h.order_dow IN (5, 6)
    AND h.order_complete_date >= '2026-05-31'
    AND h.order_complete_date < DATE_ADD(DATE_TRUNC(CURRENT_DATE(), WEEK(SUNDAY)), INTERVAL 7 DAY)
),

pre_enable AS (
  SELECT
    supplier_id,
    su_name,
    COUNT(DISTINCT ops) AS fri_sat_vol,
    COUNT(DISTINCT CASE WHEN induction_dow_adj = 1 THEN ops END) AS sun_adj1_vol,
    COUNT(DISTINCT CASE WHEN induction_dow_adj = 7 THEN ops END) AS sat_adj7_vol,
    COUNT(DISTINCT CASE WHEN induction_dow_adj IN (1, 7) THEN ops END) AS weekend_adj17_vol,
    ROUND(
      COUNT(DISTINCT CASE WHEN induction_dow_adj = 1 THEN ops END)
      / COUNT(DISTINCT ops),
      4
    ) AS pct_sun_adj1,
    ROUND(
      COUNT(DISTINCT CASE WHEN induction_dow_adj IN (1, 7) THEN ops END)
      / COUNT(DISTINCT ops),
      4
    ) AS pct_weekend_adj17
  FROM base
  WHERE order_complete_date BETWEEN '2026-05-31' AND '2026-07-04'
  GROUP BY supplier_id, su_name
),

weekly_post AS (
  SELECT
    supplier_id,
    su_name,
    week_start,
    COUNT(DISTINCT ops) AS fri_sat_vol,
    COUNT(DISTINCT CASE WHEN induction_dow_adj = 1 THEN ops END) AS sun_adj1_vol,
    COUNT(DISTINCT CASE WHEN induction_dow_adj = 7 THEN ops END) AS sat_adj7_vol,
    COUNT(DISTINCT CASE WHEN induction_dow_adj IN (1, 7) THEN ops END) AS weekend_adj17_vol,
    ROUND(
      COUNT(DISTINCT CASE WHEN induction_dow_adj = 1 THEN ops END)
      / COUNT(DISTINCT ops),
      4
    ) AS pct_sun_adj1,
    ROUND(
      COUNT(DISTINCT CASE WHEN induction_dow_adj IN (1, 7) THEN ops END)
      / COUNT(DISTINCT ops),
      4
    ) AS pct_weekend_adj17
  FROM base
  WHERE order_complete_date >= '2026-07-07'
  GROUP BY supplier_id, su_name, week_start
)

SELECT
  'pre_enable' AS period,
  supplier_id,
  su_name,
  CAST(NULL AS DATE) AS week_start,
  fri_sat_vol,
  sun_adj1_vol,
  sat_adj7_vol,
  weekend_adj17_vol,
  pct_sun_adj1,
  pct_weekend_adj17
FROM pre_enable
UNION ALL
SELECT
  'post_enable_weekly' AS period,
  supplier_id,
  su_name,
  week_start,
  fri_sat_vol,
  sun_adj1_vol,
  sat_adj7_vol,
  weekend_adj17_vol,
  pct_sun_adj1,
  pct_weekend_adj17
FROM weekly_post
ORDER BY supplier_id, period, week_start
