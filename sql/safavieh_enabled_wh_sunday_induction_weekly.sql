-- Enabled weekend warehouses — week-over-week % Sunday induction (Fri/Sat placed)
-- induction_dow_adj: Sunday = 1, Saturday = 7 · Weekend = IN (1, 7)

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
    DATE_TRUNC(h.order_complete_date, WEEK(SUNDAY)) AS week_start,
    h.ops,
    h.induction_dow_adj
  FROM `wf-gcp-us-ae-global-tnd-prod.speed_and_reliability.HVE_perf_Monitoring` h
  INNER JOIN enabled_wh e ON e.supplier_id = h.supplier_id
  WHERE h.parent_su_name = 'Safavieh'
    AND h.fulfillment_type = 'DS'
    AND h.sto = 'Rugs'
    AND h.order_dow IN (5, 6)
    AND h.order_complete_date >= DATE_SUB(DATE '2026-07-07', INTERVAL 12 WEEK)
    AND h.order_complete_date < DATE_ADD(DATE_TRUNC(CURRENT_DATE(), WEEK(SUNDAY)), INTERVAL 7 DAY)
),

weekly AS (
  SELECT
    supplier_id,
    su_name,
    week_start,
    COUNT(DISTINCT ops) AS fri_sat_vol,
    COUNT(DISTINCT CASE WHEN induction_dow_adj = 1 THEN ops END) AS sun_adj1_vol,
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
  GROUP BY supplier_id, su_name, week_start
),

l6w_pre_enable AS (
  SELECT
    supplier_id,
    su_name,
    ROUND(AVG(pct_sun_adj1), 4) AS l6w_pre_pct_sun,
    ROUND(AVG(pct_weekend_adj17), 4) AS l6w_pre_pct_weekend,
    SUM(fri_sat_vol) AS l6w_pre_fri_sat_vol
  FROM weekly
  WHERE week_start >= DATE_SUB(DATE '2026-07-07', INTERVAL 6 WEEK)
    AND week_start < DATE_TRUNC(DATE '2026-07-07', WEEK(SUNDAY))
  GROUP BY supplier_id, su_name
)

SELECT
  w.supplier_id,
  w.su_name,
  w.week_start,
  w.fri_sat_vol,
  w.sun_adj1_vol,
  w.weekend_adj17_vol,
  w.pct_sun_adj1,
  w.pct_weekend_adj17,
  p.l6w_pre_pct_sun,
  p.l6w_pre_pct_weekend,
  CASE WHEN w.week_start >= DATE_TRUNC(DATE '2026-07-07', WEEK(SUNDAY)) THEN 1 ELSE 0 END AS post_enable_week
FROM weekly w
LEFT JOIN l6w_pre_enable p
  ON p.supplier_id = w.supplier_id
ORDER BY w.supplier_id, w.week_start
