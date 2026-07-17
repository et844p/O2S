-- Weekend shipping supplier enablement analysis
--
-- Cohort: orders placed on Friday or Saturday in the last 6 weeks.
-- Success (Sunday): inducted on or before the Sunday ending that weekend.
-- Success (Saturday): inducted on or before the Saturday ending that weekend.
-- IFR: AVG(inducted_on_time_or_early) across all orders in the window.
-- Enable flags: 24hr suppliers (sp_lt = 24) with >= 70% weekend ship rate AND IFR > 85%.
--
-- Day-of-week reference (order_dow / induction_dow_adj): ISO 8601, Monday = 1 … Sunday = 7.
-- Friday = 5, Saturday = 6, Sunday = 7.

WITH base_orders AS (
  SELECT
    supplier_id,
    su_name,
    parent_suid,
    parent_su_name,
    sto,
    sp_lt,
    ops,
    order_complete_date,
    order_dow,
    induction_date_lidd,
    induction_dow_adj,
    inducted_on_time_or_early,
  FROM `wf-gcp-us-ae-global-tnd-prod.speed_and_reliability.HVE_perf_Monitoring`
  WHERE order_complete_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 6 WEEK)
    AND sto IS NOT NULL
),

-- Fri + Sat placed orders used for weekend ship-rate denominators
weekend_cohort AS (
  SELECT
    *,
    DATE_ADD(DATE_TRUNC(order_complete_date, WEEK(SUNDAY)), INTERVAL 6 DAY) AS target_saturday,
    DATE_ADD(DATE_TRUNC(order_complete_date, WEEK(SUNDAY)), INTERVAL 7 DAY) AS target_sunday,
    order_dow IN (5, 6) AS is_fri_sat_placed,
    induction_date_lidd IS NOT NULL
      AND induction_date_lidd <= DATE_ADD(DATE_TRUNC(order_complete_date, WEEK(SUNDAY)), INTERVAL 6 DAY)
      AS shipped_by_saturday,
    induction_date_lidd IS NOT NULL
      AND induction_date_lidd <= DATE_ADD(DATE_TRUNC(order_complete_date, WEEK(SUNDAY)), INTERVAL 7 DAY)
      AS shipped_by_sunday,
  FROM base_orders
),

supplier_metrics AS (
  SELECT
    supplier_id,
    ANY_VALUE(su_name) AS su_name,
    ANY_VALUE(parent_suid) AS parent_suid,
    ANY_VALUE(parent_su_name) AS parent_su_name,
    ANY_VALUE(sto) AS sto,
    MAX(sp_lt) AS sp_lt,

    -- Overall supplier performance (all orders in window)
    COUNT(DISTINCT ops) AS total_order_volume,
    AVG(inducted_on_time_or_early) AS ifr,

    -- Fri/Sat placed cohort
    COUNT(DISTINCT IF(is_fri_sat_placed, ops, NULL)) AS fri_sat_placed_volume,
    AVG(IF(is_fri_sat_placed, inducted_on_time_or_early, NULL)) AS fri_sat_ifr,

    -- Weekend ship performance on Fri/Sat placed orders
    COUNT(DISTINCT IF(is_fri_sat_placed AND shipped_by_saturday, ops, NULL)) AS fri_sat_shipped_by_sat_volume,
    SAFE_DIVIDE(
      COUNT(DISTINCT IF(is_fri_sat_placed AND shipped_by_saturday, ops, NULL)),
      COUNT(DISTINCT IF(is_fri_sat_placed, ops, NULL))
    ) AS fri_sat_shipped_by_sat_rate,

    COUNT(DISTINCT IF(is_fri_sat_placed AND shipped_by_sunday, ops, NULL)) AS fri_sat_shipped_by_sun_volume,
    SAFE_DIVIDE(
      COUNT(DISTINCT IF(is_fri_sat_placed AND shipped_by_sunday, ops, NULL)),
      COUNT(DISTINCT IF(is_fri_sat_placed, ops, NULL))
    ) AS fri_sat_shipped_by_sun_rate,

    -- Induction day-of-week mix for Fri/Sat placed orders (induction_dow_adj)
    COUNT(DISTINCT IF(is_fri_sat_placed AND induction_dow_adj = 5, ops, NULL)) AS fri_sat_inducted_on_fri,
    COUNT(DISTINCT IF(is_fri_sat_placed AND induction_dow_adj = 6, ops, NULL)) AS fri_sat_inducted_on_sat,
    COUNT(DISTINCT IF(is_fri_sat_placed AND induction_dow_adj = 7, ops, NULL)) AS fri_sat_inducted_on_sun,
  FROM weekend_cohort
  GROUP BY supplier_id
)

SELECT
  supplier_id,
  su_name,
  parent_suid,
  parent_su_name,
  sto,
  sp_lt,
  sp_lt = 24 AS is_24hr_supplier,

  total_order_volume,
  ROUND(ifr, 4) AS ifr,
  fri_sat_placed_volume,
  ROUND(fri_sat_ifr, 4) AS fri_sat_ifr,

  fri_sat_shipped_by_sat_volume,
  ROUND(fri_sat_shipped_by_sat_rate, 4) AS fri_sat_shipped_by_sat_rate,
  fri_sat_shipped_by_sun_volume,
  ROUND(fri_sat_shipped_by_sun_rate, 4) AS fri_sat_shipped_by_sun_rate,

  fri_sat_inducted_on_fri,
  fri_sat_inducted_on_sat,
  fri_sat_inducted_on_sun,

  -- Enable flags: 24hr candidates only, >= 70% weekend ship rate, IFR > 85%
  (
    sp_lt = 24
    AND fri_sat_shipped_by_sat_rate >= 0.70
    AND ifr > 0.85
    AND fri_sat_placed_volume > 0
  ) AS enable_saturday_weekend_shipping,

  (
    sp_lt = 24
    AND fri_sat_shipped_by_sun_rate >= 0.70
    AND ifr > 0.85
    AND fri_sat_placed_volume > 0
  ) AS enable_sunday_weekend_shipping,

FROM supplier_metrics
ORDER BY
  enable_sunday_weekend_shipping DESC,
  enable_saturday_weekend_shipping DESC,
  fri_sat_placed_volume DESC,
  supplier_id
