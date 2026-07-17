-- Weekend shipping supplier enablement analysis
--
-- Cohort: orders placed on Friday or Saturday in the last 6 weeks.
-- Weekend ship: inducted on Saturday or Sunday (induction_dow_adj IN 6, 7).
-- IFR: AVG(inducted_on_time_or_early) across all orders in the window.
-- Candidate: 24hr suppliers (sp_lt = 24) with >= 70% weekend ship rate AND IFR > 85%.
--
-- Day-of-week reference (order_dow / induction_dow_adj): ISO 8601, Monday = 1 … Sunday = 7.

WITH base_orders AS (
  SELECT
    supplier_id,
    su_name,
    sp_lt,
    cutoff,
    StationName,
    address_1,
    city_name,
    state_name,
    postal_code,
    sto,
    ProductCategory,
    srm_contact,
    ops,
    order_complete_date,
    order_dow,
    induction_dow_adj,
    inducted_on_time_or_early,
  FROM `wf-gcp-us-ae-global-tnd-prod.speed_and_reliability.HVE_perf_Monitoring`
  WHERE order_complete_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 6 WEEK)
),

weekend_cohort AS (
  SELECT
    *,
    order_dow IN (5, 6) AS is_fri_sat_placed,
    induction_dow_adj IN (6, 7) AS shipped_on_weekend,
  FROM base_orders
),

supplier_metrics AS (
  SELECT
    supplier_id,
    ANY_VALUE(su_name) AS su_name,
    MAX(sp_lt) AS sp_lt,
    ANY_VALUE(cutoff) AS cutoff,
    ANY_VALUE(StationName) AS station_name,
    ANY_VALUE(address_1) AS address,
    ANY_VALUE(city_name) AS city,
    ANY_VALUE(state_name) AS state,
    ANY_VALUE(postal_code) AS postal_code,
    ANY_VALUE(sto) AS sto,
    ANY_VALUE(ProductCategory) AS marketing_category,
    ANY_VALUE(srm_contact) AS srm,

    COUNT(DISTINCT ops) AS last_6_weeks_volume,
    AVG(inducted_on_time_or_early) AS ifr,

    COUNT(DISTINCT IF(is_fri_sat_placed, ops, NULL)) AS fri_sat_order_volume,
    COUNT(DISTINCT IF(is_fri_sat_placed AND shipped_on_weekend, ops, NULL)) AS fri_sat_weekend_shipped_volume,
    SAFE_DIVIDE(
      COUNT(DISTINCT IF(is_fri_sat_placed AND shipped_on_weekend, ops, NULL)),
      COUNT(DISTINCT IF(is_fri_sat_placed, ops, NULL))
    ) AS pct_fri_sat_shipped_on_sat_or_sun,
  FROM weekend_cohort
  GROUP BY supplier_id
)

SELECT
  supplier_id,
  su_name,
  sp_lt AS lt,
  cutoff,
  station_name,
  address,
  city,
  state,
  postal_code,
  sto,
  marketing_category,
  srm,
  last_6_weeks_volume,
  fri_sat_order_volume,
  fri_sat_weekend_shipped_volume,
  ROUND(pct_fri_sat_shipped_on_sat_or_sun, 4) AS pct_fri_sat_shipped_on_sat_or_sun,
  ROUND(ifr, 4) AS ifr,
  COALESCE(
    sp_lt = 24
      AND pct_fri_sat_shipped_on_sat_or_sun >= 0.70
      AND ifr > 0.85
      AND fri_sat_order_volume > 0,
    FALSE
  ) AS weekend_shipping_candidate,
FROM supplier_metrics
ORDER BY
  weekend_shipping_candidate DESC,
  fri_sat_order_volume DESC,
  supplier_id
