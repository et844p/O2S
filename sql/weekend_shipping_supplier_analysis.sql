-- Weekend shipping supplier enablement analysis
--
-- Weekly buckets: week_minus_1 (most recent) through week_minus_6 (oldest).
-- Weeks are Sunday-starting, anchored to CURRENT_DATE().
-- Cohort: orders placed Friday or Saturday (order_dow IN 5, 6).
-- Weekend ship: inducted on Saturday or Sunday (induction_dow_adj IN 6, 7).
-- Candidate (L6W): sp_lt = 24, >= 70% Fri/Sat weekend ship rate, IFR > 85%.
-- Almost ready: 24hr suppliers with 30-70% Fri/Sat weekend ship rate.
-- Not weekend shipping: < 30% Fri/Sat weekend ship rate (with Fri/Sat volume).
-- Filter: suppliers with >= 500 ops in the last 6 weeks.
--
-- Day-of-week (historical): this query treated order_dow IN (5, 6) as Fri/Sat and
-- induction_dow_adj IN (6, 7) as Sat/Sun. Empirically both columns are Sunday = 1
-- … Saturday = 7, so those filters are Thu/Fri placed and Fri/Sat induction.
-- Corrected impact analysis: sql/weekend_shipping_pre_post_cte.sql
--   Fri/Sat placed = order_dow IN (6, 7); weekend ship = induction_dow_adj IN (1, 7).

WITH params AS (
  SELECT
    CURRENT_DATE() AS report_as_of_date,
    DATE_TRUNC(CURRENT_DATE(), WEEK(SUNDAY)) AS current_week_start,
),

base_orders AS (
  SELECT
    o.supplier_id,
    o.su_name,
    o.sp_lt,
    o.cutoff,
    o.StationName,
    o.address_1,
    o.city_name,
    o.state_name,
    o.postal_code,
    o.sto,
    o.ProductCategory,
    o.srm_contact,
    o.ops,
    o.order_complete_date,
    o.order_dow,
    o.induction_dow_adj,
    o.inducted_on_time_or_early,
    DATE_TRUNC(o.order_complete_date, WEEK(SUNDAY)) AS order_week_start,
    DATE_DIFF(
      p.current_week_start,
      DATE_TRUNC(o.order_complete_date, WEEK(SUNDAY)),
      WEEK
    ) AS week_offset,
  FROM `wf-gcp-us-ae-global-tnd-prod.speed_and_reliability.HVE_perf_Monitoring` AS o
  CROSS JOIN params AS p
  WHERE o.order_complete_date >= DATE_SUB(p.report_as_of_date, INTERVAL 6 WEEK)
    AND o.order_complete_date < p.report_as_of_date
    AND o.fulfillment_type = 'DS'
),

weekend_cohort AS (
  SELECT
    *,
    week_offset + 1 AS week_minus,
    order_dow IN (5, 6) AS is_fri_sat_placed,
    induction_dow_adj IN (6, 7) AS shipped_on_weekend,
  FROM base_orders
  WHERE week_offset BETWEEN 0 AND 5
),

supplier_weekly AS (
  SELECT
    supplier_id,
    week_minus,
    ANY_VALUE(order_week_start) AS week_start_date,
    COUNT(DISTINCT ops) AS total_volume,
    COUNT(DISTINCT IF(is_fri_sat_placed, ops, NULL)) AS fri_sat_volume,
    COUNT(DISTINCT IF(is_fri_sat_placed AND shipped_on_weekend, ops, NULL)) AS fri_sat_weekend_shipped_volume,
    SAFE_DIVIDE(
      COUNT(DISTINCT IF(is_fri_sat_placed AND shipped_on_weekend, ops, NULL)),
      COUNT(DISTINCT IF(is_fri_sat_placed, ops, NULL))
    ) AS pct_fri_sat_shipped_sat_sun,
    AVG(inducted_on_time_or_early) AS ifr,
  FROM weekend_cohort
  GROUP BY supplier_id, week_minus
),

supplier_l6w AS (
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

    COUNT(DISTINCT ops) AS l6w_total_volume,
    AVG(inducted_on_time_or_early) AS l6w_ifr,
    COUNT(DISTINCT IF(is_fri_sat_placed, ops, NULL)) AS l6w_fri_sat_volume,
    COUNT(DISTINCT IF(is_fri_sat_placed AND shipped_on_weekend, ops, NULL)) AS l6w_fri_sat_weekend_shipped_volume,
    SAFE_DIVIDE(
      COUNT(DISTINCT IF(is_fri_sat_placed AND shipped_on_weekend, ops, NULL)),
      COUNT(DISTINCT IF(is_fri_sat_placed, ops, NULL))
    ) AS l6w_pct_fri_sat_shipped_sat_sun,
  FROM weekend_cohort
  GROUP BY supplier_id
  HAVING COUNT(DISTINCT ops) >= 500
),

supplier_pivot AS (
  SELECT
    supplier_id,
    MAX(IF(week_minus = 1, week_start_date, NULL)) AS week_minus_1_start,
    MAX(IF(week_minus = 1, total_volume, NULL)) AS week_minus_1_total_volume,
    MAX(IF(week_minus = 1, fri_sat_volume, NULL)) AS week_minus_1_fri_sat_volume,
    MAX(IF(week_minus = 1, fri_sat_weekend_shipped_volume, NULL)) AS week_minus_1_fri_sat_weekend_shipped_volume,
    MAX(IF(week_minus = 1, pct_fri_sat_shipped_sat_sun, NULL)) AS week_minus_1_pct_fri_sat_shipped_sat_sun,
    MAX(IF(week_minus = 1, ifr, NULL)) AS week_minus_1_ifr,

    MAX(IF(week_minus = 2, week_start_date, NULL)) AS week_minus_2_start,
    MAX(IF(week_minus = 2, total_volume, NULL)) AS week_minus_2_total_volume,
    MAX(IF(week_minus = 2, fri_sat_volume, NULL)) AS week_minus_2_fri_sat_volume,
    MAX(IF(week_minus = 2, fri_sat_weekend_shipped_volume, NULL)) AS week_minus_2_fri_sat_weekend_shipped_volume,
    MAX(IF(week_minus = 2, pct_fri_sat_shipped_sat_sun, NULL)) AS week_minus_2_pct_fri_sat_shipped_sat_sun,
    MAX(IF(week_minus = 2, ifr, NULL)) AS week_minus_2_ifr,

    MAX(IF(week_minus = 3, week_start_date, NULL)) AS week_minus_3_start,
    MAX(IF(week_minus = 3, total_volume, NULL)) AS week_minus_3_total_volume,
    MAX(IF(week_minus = 3, fri_sat_volume, NULL)) AS week_minus_3_fri_sat_volume,
    MAX(IF(week_minus = 3, fri_sat_weekend_shipped_volume, NULL)) AS week_minus_3_fri_sat_weekend_shipped_volume,
    MAX(IF(week_minus = 3, pct_fri_sat_shipped_sat_sun, NULL)) AS week_minus_3_pct_fri_sat_shipped_sat_sun,
    MAX(IF(week_minus = 3, ifr, NULL)) AS week_minus_3_ifr,

    MAX(IF(week_minus = 4, week_start_date, NULL)) AS week_minus_4_start,
    MAX(IF(week_minus = 4, total_volume, NULL)) AS week_minus_4_total_volume,
    MAX(IF(week_minus = 4, fri_sat_volume, NULL)) AS week_minus_4_fri_sat_volume,
    MAX(IF(week_minus = 4, fri_sat_weekend_shipped_volume, NULL)) AS week_minus_4_fri_sat_weekend_shipped_volume,
    MAX(IF(week_minus = 4, pct_fri_sat_shipped_sat_sun, NULL)) AS week_minus_4_pct_fri_sat_shipped_sat_sun,
    MAX(IF(week_minus = 4, ifr, NULL)) AS week_minus_4_ifr,

    MAX(IF(week_minus = 5, week_start_date, NULL)) AS week_minus_5_start,
    MAX(IF(week_minus = 5, total_volume, NULL)) AS week_minus_5_total_volume,
    MAX(IF(week_minus = 5, fri_sat_volume, NULL)) AS week_minus_5_fri_sat_volume,
    MAX(IF(week_minus = 5, fri_sat_weekend_shipped_volume, NULL)) AS week_minus_5_fri_sat_weekend_shipped_volume,
    MAX(IF(week_minus = 5, pct_fri_sat_shipped_sat_sun, NULL)) AS week_minus_5_pct_fri_sat_shipped_sat_sun,
    MAX(IF(week_minus = 5, ifr, NULL)) AS week_minus_5_ifr,

    MAX(IF(week_minus = 6, week_start_date, NULL)) AS week_minus_6_start,
    MAX(IF(week_minus = 6, total_volume, NULL)) AS week_minus_6_total_volume,
    MAX(IF(week_minus = 6, fri_sat_volume, NULL)) AS week_minus_6_fri_sat_volume,
    MAX(IF(week_minus = 6, fri_sat_weekend_shipped_volume, NULL)) AS week_minus_6_fri_sat_weekend_shipped_volume,
    MAX(IF(week_minus = 6, pct_fri_sat_shipped_sat_sun, NULL)) AS week_minus_6_pct_fri_sat_shipped_sat_sun,
    MAX(IF(week_minus = 6, ifr, NULL)) AS week_minus_6_ifr,
  FROM supplier_weekly
  GROUP BY supplier_id
)

SELECT
  p.report_as_of_date,
  CURRENT_TIMESTAMP() AS refresh_timestamp,

  l.supplier_id,
  l.su_name,
  l.sp_lt AS lt,
  l.cutoff,
  l.station_name,
  l.address,
  l.city,
  l.state,
  l.postal_code,
  l.sto,
  l.marketing_category,
  l.srm,

  -- Week -1 (most recent) through week -6 (oldest)
  w.week_minus_1_start,
  w.week_minus_1_total_volume,
  w.week_minus_1_fri_sat_volume,
  w.week_minus_1_fri_sat_weekend_shipped_volume,
  ROUND(w.week_minus_1_pct_fri_sat_shipped_sat_sun, 4) AS week_minus_1_pct_fri_sat_shipped_sat_sun,
  ROUND(w.week_minus_1_ifr, 4) AS week_minus_1_ifr,

  w.week_minus_2_start,
  w.week_minus_2_total_volume,
  w.week_minus_2_fri_sat_volume,
  w.week_minus_2_fri_sat_weekend_shipped_volume,
  ROUND(w.week_minus_2_pct_fri_sat_shipped_sat_sun, 4) AS week_minus_2_pct_fri_sat_shipped_sat_sun,
  ROUND(w.week_minus_2_ifr, 4) AS week_minus_2_ifr,

  w.week_minus_3_start,
  w.week_minus_3_total_volume,
  w.week_minus_3_fri_sat_volume,
  w.week_minus_3_fri_sat_weekend_shipped_volume,
  ROUND(w.week_minus_3_pct_fri_sat_shipped_sat_sun, 4) AS week_minus_3_pct_fri_sat_shipped_sat_sun,
  ROUND(w.week_minus_3_ifr, 4) AS week_minus_3_ifr,

  w.week_minus_4_start,
  w.week_minus_4_total_volume,
  w.week_minus_4_fri_sat_volume,
  w.week_minus_4_fri_sat_weekend_shipped_volume,
  ROUND(w.week_minus_4_pct_fri_sat_shipped_sat_sun, 4) AS week_minus_4_pct_fri_sat_shipped_sat_sun,
  ROUND(w.week_minus_4_ifr, 4) AS week_minus_4_ifr,

  w.week_minus_5_start,
  w.week_minus_5_total_volume,
  w.week_minus_5_fri_sat_volume,
  w.week_minus_5_fri_sat_weekend_shipped_volume,
  ROUND(w.week_minus_5_pct_fri_sat_shipped_sat_sun, 4) AS week_minus_5_pct_fri_sat_shipped_sat_sun,
  ROUND(w.week_minus_5_ifr, 4) AS week_minus_5_ifr,

  w.week_minus_6_start,
  w.week_minus_6_total_volume,
  w.week_minus_6_fri_sat_volume,
  w.week_minus_6_fri_sat_weekend_shipped_volume,
  ROUND(w.week_minus_6_pct_fri_sat_shipped_sat_sun, 4) AS week_minus_6_pct_fri_sat_shipped_sat_sun,
  ROUND(w.week_minus_6_ifr, 4) AS week_minus_6_ifr,

  -- Last 6 weeks rollup
  l.l6w_total_volume,
  l.l6w_fri_sat_volume,
  l.l6w_fri_sat_weekend_shipped_volume,
  ROUND(l.l6w_pct_fri_sat_shipped_sat_sun, 4) AS l6w_pct_fri_sat_shipped_sat_sun,
  ROUND(l.l6w_ifr, 4) AS l6w_ifr,

  COALESCE(
    l.sp_lt = 24
      AND l.l6w_pct_fri_sat_shipped_sat_sun >= 0.70
      AND l.l6w_ifr > 0.85
      AND l.l6w_fri_sat_volume > 0,
    FALSE
  ) AS weekend_shipping_candidate,

  COALESCE(
    l.sp_lt = 24
      AND l.l6w_pct_fri_sat_shipped_sat_sun >= 0.30
      AND l.l6w_pct_fri_sat_shipped_sat_sun < 0.70
      AND l.l6w_fri_sat_volume > 0,
    FALSE
  ) AS weekend_shipping_almost_ready,

  COALESCE(
    l.l6w_fri_sat_volume > 0
      AND COALESCE(l.l6w_pct_fri_sat_shipped_sat_sun, 0) < 0.30,
    FALSE
  ) AS not_weekend_shipping,

  CASE
    WHEN l.sp_lt = 24
      AND l.l6w_pct_fri_sat_shipped_sat_sun >= 0.70
      AND l.l6w_ifr > 0.85
      AND l.l6w_fri_sat_volume > 0
      THEN 'candidate'
    WHEN l.sp_lt = 24
      AND l.l6w_pct_fri_sat_shipped_sat_sun >= 0.30
      AND l.l6w_pct_fri_sat_shipped_sat_sun < 0.70
      AND l.l6w_fri_sat_volume > 0
      THEN 'almost_ready'
    WHEN l.l6w_fri_sat_volume > 0
      AND COALESCE(l.l6w_pct_fri_sat_shipped_sat_sun, 0) < 0.30
      THEN 'not_weekend_shipping'
    ELSE 'other'
  END AS weekend_shipping_cohort,

FROM supplier_l6w AS l
CROSS JOIN params AS p
LEFT JOIN supplier_pivot AS w
  ON l.supplier_id = w.supplier_id
ORDER BY
  l.l6w_total_volume DESC,
  l.supplier_id
