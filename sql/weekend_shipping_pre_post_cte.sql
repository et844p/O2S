-- Shared CTEs: weekend MSBD enablement roster (June 2026 onward)
--
-- Day-of-week (empirically verified against order_complete_date / induction_date_lidd):
--   Sunday = 1 … Saturday = 7 for BOTH order_dow and induction_dow_adj.
--   Fri/Sat placed: order_dow IN (6, 7)
--   Weekend induction: induction_dow_adj IN (1, 7)  -- do NOT use inducted_over_weekend
--     (that flag undercounts Sunday scans; e.g. Sunday 6–11pm often stored as 0)
--   Weekend MSBD: EXTRACT(DAYOFWEEK FROM msbd_su) IN (1, 7)  -- BQ DAYOFWEEK is also Sun=1
--
-- Enablement = first week on/after 2026-06-21 where a 24hr DS supplier's Fri/Sat
-- weekend-MSBD rate is >= 10% (min 20 Fri/Sat ops that week), and the prior 6-week
-- average weekend-MSBD rate is < 5%.
--
-- Wave 1: enable week <= 2026-07-12 (nuLOOM 6/21, then 7/5 Safavieh/Aosom/GigaCloud/…)
-- Wave 2: enable week >= 2026-08-02 (Q3 sprint)

WITH weekly_fri_sat AS (
  SELECT
    supplier_id,
    ANY_VALUE(su_name) AS su_name,
    ANY_VALUE(parent_su_name) AS parent_su_name,
    ANY_VALUE(sto) AS sto,
    ANY_VALUE(srm_contact) AS srm,
    MAX(sp_lt) AS sp_lt,
    DATE_TRUNC(order_complete_date, WEEK(SUNDAY)) AS week_start,
    COUNT(DISTINCT ops) AS fri_sat_vol,
    SAFE_DIVIDE(
      COUNT(DISTINCT IF(EXTRACT(DAYOFWEEK FROM msbd_su) IN (1, 7), ops, NULL)),
      COUNT(DISTINCT ops)
    ) AS weekend_msbd_rate
  FROM `wf-gcp-us-ae-global-tnd-prod.speed_and_reliability.HVE_perf_Monitoring`
  WHERE fulfillment_type = 'DS'
    AND sp_lt = 24
    AND order_dow IN (6, 7)
    AND order_complete_date >= DATE '2026-04-01'
    AND order_complete_date < DATE '2026-08-30'
  GROUP BY supplier_id, week_start
  HAVING COUNT(DISTINCT ops) >= 20
),

first_hit AS (
  SELECT
    supplier_id,
    MIN(week_start) AS enable_week
  FROM weekly_fri_sat
  WHERE weekend_msbd_rate >= 0.10
    AND week_start >= DATE '2026-06-21'
  GROUP BY supplier_id
),

pre_check AS (
  SELECT
    w.supplier_id,
    AVG(w.weekend_msbd_rate) AS pre6w_weekend_msbd_rate,
    SUM(w.fri_sat_vol) AS pre6w_fri_sat_vol
  FROM weekly_fri_sat AS w
  INNER JOIN first_hit AS f
    ON f.supplier_id = w.supplier_id
  WHERE w.week_start >= DATE_SUB(f.enable_week, INTERVAL 6 WEEK)
    AND w.week_start < f.enable_week
  GROUP BY w.supplier_id
),

enabled_suppliers AS (
  SELECT
    f.supplier_id,
    w.su_name,
    w.parent_su_name,
    w.sto,
    w.srm,
    w.sp_lt,
    f.enable_week,
    CASE
      WHEN f.enable_week <= DATE '2026-07-12' THEN 'wave1_jun_jul'
      WHEN f.enable_week >= DATE '2026-08-02' THEN 'wave2_aug'
      ELSE 'other'
    END AS wave,
    p.pre6w_weekend_msbd_rate,
    p.pre6w_fri_sat_vol
  FROM first_hit AS f
  INNER JOIN pre_check AS p
    ON p.supplier_id = f.supplier_id
  INNER JOIN weekly_fri_sat AS w
    ON w.supplier_id = f.supplier_id
   AND w.week_start = f.enable_week
  WHERE COALESCE(p.pre6w_weekend_msbd_rate, 0) < 0.05
)
