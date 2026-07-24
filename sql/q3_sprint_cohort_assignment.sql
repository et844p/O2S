-- Q3 Sprint supplier cohort assignment
--
-- Assigns Q3-A through Q3-F based on L6W performance on HVE_perf_Monitoring.
-- Run output feeds Growth@ mail merge (see docs/small_parcel/q3_sprint/).
--
-- Defaults: DS fulfillment, >= 500 ops L6W.
-- Weekend metrics align with sql/weekend_shipping_supplier_analysis.sql.

WITH params AS (
  SELECT
    CURRENT_DATE() AS report_as_of_date,
    DATE_TRUNC(CURRENT_DATE(), WEEK(SUNDAY)) AS current_week_start,
),

base_orders AS (
  SELECT
    o.supplier_id,
    o.parent_suid,
    o.parent_su_name,
    o.su_name,
    o.srm_contact,
    o.StationName,
    o.ops,
    o.order_complete_date,
    o.order_dow,
    o.induction_dow_adj,
    o.inducted_on_time_or_early,
    o.inducted_late,
    o.one_day_late,
    o.three_days_plus_late,
    o.label_by_msbd_7,
    o.assigned_constrained_market,
    o.summer26_target,
    o.sp_lt,
    o.event_datetime,
    o.induction_date_lidd,
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

l6w AS (
  SELECT
    supplier_id,
    ANY_VALUE(parent_suid) AS parent_suid,
    ANY_VALUE(parent_su_name) AS parent_su_name,
    ANY_VALUE(su_name) AS su_name,
    ANY_VALUE(srm_contact) AS srm,
    ANY_VALUE(StationName) AS station_name,
    MAX(sp_lt) AS sp_lt,
    MAX(assigned_constrained_market) AS is_constrained_market,
    MAX(summer26_target) AS is_repeat_target,

    COUNT(DISTINCT ops) AS l6w_volume,
    AVG(inducted_on_time_or_early) AS ifr,
    AVG(label_by_msbd_7) AS label_by_7,

    COUNT(DISTINCT IF(order_dow IN (5, 6), ops, NULL)) AS fri_sat_volume,
    COUNT(DISTINCT IF(
      order_dow IN (5, 6) AND induction_dow_adj IN (6, 7),
      ops,
      NULL
    )) AS fri_sat_weekend_shipped,
    SAFE_DIVIDE(
      COUNT(DISTINCT IF(
        order_dow IN (5, 6) AND induction_dow_adj IN (6, 7),
        ops,
        NULL
      )),
      COUNT(DISTINCT IF(order_dow IN (5, 6), ops, NULL))
    ) AS weekend_ship_rate,

    SAFE_DIVIDE(
      COUNT(DISTINCT IF(inducted_late = 1 AND one_day_late = 1, ops, NULL)),
      COUNT(DISTINCT IF(inducted_late = 1, ops, NULL))
    ) AS pct_one_day_late_of_lates,

    SAFE_DIVIDE(
      COUNT(DISTINCT IF(inducted_late = 1 AND three_days_plus_late = 1, ops, NULL)),
      COUNT(DISTINCT IF(inducted_late = 1, ops, NULL))
    ) AS pct_3plus_day_late_of_lates,

    SAFE_DIVIDE(
      COUNT(DISTINCT IF(
        event_datetime IS NOT NULL
          AND induction_date_lidd IS NOT NULL
          AND DATE_DIFF(induction_date_lidd, DATE(event_datetime), DAY) > 1,
        ops,
        NULL
      )),
      COUNT(DISTINCT ops)
    ) AS gap_label_induction_pct,
  FROM base_orders
  WHERE week_offset BETWEEN 0 AND 5
  GROUP BY supplier_id
  HAVING COUNT(DISTINCT ops) >= 500
),

l4w AS (
  SELECT
    supplier_id,
    AVG(inducted_on_time_or_early) AS l4w_ifr,
    AVG(label_by_msbd_7) AS l4w_label_by_7,
  FROM base_orders
  WHERE week_offset BETWEEN 0 AND 3
  GROUP BY supplier_id
),

assigned AS (
  SELECT
    l.*,
    l4.l4w_ifr,
    l4.l4w_label_by_7,

    -- Q3-F enablement track (evaluated first for template routing)
    (
      l.sp_lt = 24
      AND l.weekend_ship_rate >= 0.70
      AND l.ifr > 0.85
      AND l.fri_sat_volume > 0
    ) AS meets_q3f_enablement,

    CASE
      -- Q3-F: weekend MSBD enablement candidates
      WHEN l.sp_lt = 24
        AND l.weekend_ship_rate >= 0.70
        AND l.ifr > 0.85
        AND l.fri_sat_volume > 0
        THEN 'Q3-F'

      -- Q3-A: operational issues (low IFR + low label)
      WHEN l.ifr < 0.70 AND l.label_by_7 < 0.80
        THEN 'Q3-A'

      -- Q3-B: reliability — forecasting (high 1-day late share)
      WHEN l.ifr < 0.70
        AND l.label_by_7 >= 0.80
        AND l.pct_one_day_late_of_lates > 0.60
        THEN 'Q3-B'

      -- Q3-C: reliability — FIFO / handshake
      WHEN l.ifr < 0.70
        AND l.label_by_7 >= 0.80
        AND (
          l.pct_one_day_late_of_lates <= 0.60
          OR l.gap_label_induction_pct > 0.10
        )
        THEN 'Q3-C'

      -- Q3-D: speed & reliability
      WHEN l.ifr >= 0.70 AND l.ifr < 0.90
        THEN 'Q3-D'

      -- Q3-E: speed
      WHEN l.ifr >= 0.90
        THEN 'Q3-E'

      ELSE 'UNASSIGNED'
    END AS q3_cohort,

    CASE
      WHEN l.ifr < 0.70 AND l.label_by_7 < 0.80 THEN 'Operational Issues'
      WHEN l.ifr < 0.70 AND l.label_by_7 >= 0.80 AND l.pct_one_day_late_of_lates > 0.60
        THEN 'Reliability — Forecasting & Constrained'
      WHEN l.ifr < 0.70 AND l.label_by_7 >= 0.80
        THEN 'Reliability — FIFO & Handshake'
      WHEN l.ifr >= 0.70 AND l.ifr < 0.90 THEN 'Speed & Reliability'
      WHEN l.ifr >= 0.90 AND NOT (
        l.sp_lt = 24 AND l.weekend_ship_rate >= 0.70 AND l.fri_sat_volume > 0
      ) THEN 'Speed'
      WHEN l.sp_lt = 24 AND l.weekend_ship_rate >= 0.70 AND l.ifr > 0.85
        THEN 'Weekend MSBD Enablement'
      ELSE 'Unassigned'
    END AS cohort_name,

    -- IFR sub-cohort for discovery question blocks
    CASE
      WHEN l.pct_3plus_day_late_of_lates > 0.20 THEN 'B'
      WHEN l.label_by_7 < 0.97 THEN 'C'
      WHEN l.pct_one_day_late_of_lates > 0.20 THEN 'D'
      ELSE 'A'
    END AS ifr_sub_cohort,
  FROM l6w AS l
  LEFT JOIN l4w AS l4 USING (supplier_id)
)

SELECT
  supplier_id AS child_suid,
  parent_suid,
  parent_su_name,
  su_name,
  srm AS srm_name,
  station_name,
  q3_cohort,
  cohort_name,
  ifr_sub_cohort,
  is_constrained_market,
  is_repeat_target,
  l6w_volume,
  ROUND(ifr * 100, 1) AS ifr_pct,
  ROUND(l4w_ifr * 100, 1) AS l4w_ifr_pct,
  ROUND(label_by_7 * 100, 1) AS label_by_7_pct,
  ROUND(l4w_label_by_7 * 100, 1) AS l4w_label_by_7_pct,
  ROUND(weekend_ship_rate * 100, 1) AS weekend_ship_pct,
  fri_sat_volume,
  ROUND(pct_one_day_late_of_lates * 100, 1) AS pct_one_day_late,
  ROUND(gap_label_induction_pct * 100, 1) AS gap_label_induction_pct,
  meets_q3f_enablement,
FROM assigned
WHERE q3_cohort != 'UNASSIGNED'
ORDER BY q3_cohort, l6w_volume DESC
