-- Directs order-level flags + supplier performance rollup
--
-- Same rules as directs_supplier_cohorts.sql:
--   CANDIDATE = wrong hub
--               AND distance_assignedhub_customer >= 400
--               AND distance_assignedhub_actualhub >= 200
--   Partition (priority):
--     misshipping     — parent has another WH in the induction state
--     ghost_warehouse — persistent far hub (>=10% vol, most weeks) with
--                       scattered induction timing (avg <2 candidate ops/day)
--     jumbo           — direct_gain < 0.4 (null treated as < 0.4)
--     direct          — else (gain >= 0.4)
--
-- Default window: last 10 weeks by promised_delivery_end_range_date_at_order.
--
-- Final SELECT is the SUPPLIER ROLLUP (counts, %, IFR, delivery_rel).
-- For order-level rows, replace the final SELECT with:
--   SELECT * FROM order_flagged ORDER BY supplier_id, msbd_su DESC

WITH params AS (
  SELECT CURRENT_DATE() AS as_of
),

windows AS (
  SELECT
    'pdd_10w' AS lookback_window,
    'promised_delivery_end_range_date_at_order' AS timebase,
    10 AS lookback_weeks,
    DATE_SUB((SELECT as_of FROM params), INTERVAL 10 WEEK) AS window_start,
    (SELECT as_of FROM params) AS window_end
),

parent_states AS (
  SELECT DISTINCT
    w.lookback_window,
    o.parent_suid,
    o.state_name AS warehouse_state
  FROM `wf-gcp-us-ae-global-tnd-prod.speed_and_reliability.HVE_perf_Monitoring` AS o
  CROSS JOIN windows AS w
  WHERE o.fulfillment_type = 'DS'
    AND o.parent_suid IS NOT NULL
    AND o.state_name IS NOT NULL
    AND o.promised_delivery_end_range_date_at_order >= w.window_start
    AND o.promised_delivery_end_range_date_at_order < w.window_end
),

parent_state_list AS (
  SELECT
    lookback_window,
    parent_suid,
    STRING_AGG(DISTINCT warehouse_state, ',' ORDER BY warehouse_state) AS parent_warehouse_states,
    COUNT(DISTINCT warehouse_state) AS n_parent_warehouse_states
  FROM parent_states
  GROUP BY 1, 2
),

base AS (
  SELECT
    w.lookback_window,
    w.timebase,
    w.lookback_weeks,
    o.supplier_id,
    o.su_name,
    o.parent_suid,
    o.parent_su_name,
    o.sto,
    o.srm_contact,
    o.state_name AS own_state,
    o.city_name,
    o.postal_code,
    o.address_1,
    o.ops,
    o.purchase_order_number,
    o.tracking_number,
    o.msbd_su,
    o.promised_delivery_end_range_date_at_order,
    o.order_complete_date,
    o.induction_date_lidd,
    o.delivery_date,
    o.assigned_induction_hub_id,
    o.assigned_induction_hub_name,
    o.assigned_station_zip,
    o.assigned_station_state,
    o.actual_induction_hub_id,
    o.actual_induction_hub_name,
    o.actual_induction_hub_zip,
    o.actual_induction_hub_state,
    o.destination_zipcode,
    o.destination_state,
    o.distance_assignedhub_customer,
    o.distance_actualhub_customer,
    o.distance_assignedhub_actualhub,
    o.assignedhub_notequal_actualhub_flag,
    o.assignedstate_notequal_actualstate_flag,
    o.direct_gain,
    o.inducted_on_time_or_early,
    o.delivery_rel,
    COALESCE(DATE(o.carrier_first_induction_date_time), o.induction_date_lidd) AS ind_day,
    DATE_TRUNC(o.promised_delivery_end_range_date_at_order, WEEK(SUNDAY)) AS week_start,
    CASE
      WHEN o.actual_induction_hub_id IS NULL
        OR TRIM(CAST(o.actual_induction_hub_id AS STRING)) = '' THEN 1
      ELSE 0
    END AS missing_actual_hub,
    CASE
      WHEN o.assignedhub_notequal_actualhub_flag = 1
        AND COALESCE(o.distance_assignedhub_customer, 0) >= 400
        AND COALESCE(o.distance_assignedhub_actualhub, 0) >= 200 THEN 1
      ELSE 0
    END AS is_direct_candidate,
    CASE
      WHEN o.assignedhub_notequal_actualhub_flag = 1
        AND COALESCE(o.distance_assignedhub_actualhub, 0) >= 200 THEN 1
      ELSE 0
    END AS is_far_hub_induction
  FROM `wf-gcp-us-ae-global-tnd-prod.speed_and_reliability.HVE_perf_Monitoring` AS o
  CROSS JOIN windows AS w
  WHERE o.fulfillment_type = 'DS'
    AND o.promised_delivery_end_range_date_at_order >= w.window_start
    AND o.promised_delivery_end_range_date_at_order < w.window_end
),

base_enriched AS (
  SELECT
    b.*,
    CASE
      WHEN ps.warehouse_state IS NOT NULL
        AND b.actual_induction_hub_state IS NOT NULL
        AND b.actual_induction_hub_state != b.own_state THEN 1
      ELSE 0
    END AS is_sibling_state
  FROM base AS b
  LEFT JOIN parent_states AS ps
    ON b.lookback_window = ps.lookback_window
   AND b.parent_suid = ps.parent_suid
   AND b.actual_induction_hub_state = ps.warehouse_state
),

supplier_meta AS (
  SELECT
    lookback_window,
    supplier_id,
    COUNT(DISTINCT ops) AS total_vol,
    COUNT(DISTINCT week_start) AS weeks_with_vol
  FROM base_enriched
  GROUP BY 1, 2
),

hub_agg AS (
  SELECT
    lookback_window,
    supplier_id,
    actual_induction_hub_name,
    ANY_VALUE(actual_induction_hub_state) AS actual_induction_hub_state,
    MAX(is_sibling_state) AS is_sibling_state,
    COUNT(DISTINCT ops) AS hub_vol,
    COUNT(DISTINCT IF(is_direct_candidate = 1, ops, NULL)) AS hub_candidate_vol,
    COUNT(DISTINCT IF(is_direct_candidate = 1, week_start, NULL)) AS weeks_with_candidate,
    COUNT(DISTINCT IF(is_direct_candidate = 1, ind_day, NULL)) AS candidate_ind_days,
    AVG(CASE WHEN is_far_hub_induction = 1 THEN 1 ELSE 0 END) AS pct_far
  FROM base_enriched
  WHERE missing_actual_hub = 0
    AND actual_induction_hub_name IS NOT NULL
  GROUP BY 1, 2, 3
),

ghost_hubs AS (
  SELECT
    h.lookback_window,
    h.supplier_id,
    h.actual_induction_hub_name
  FROM hub_agg AS h
  JOIN supplier_meta AS m
    USING (lookback_window, supplier_id)
  WHERE h.is_sibling_state = 0
    AND h.hub_candidate_vol > 0
    AND h.pct_far >= 0.8
    AND h.weeks_with_candidate >= GREATEST(2, CAST(CEIL(0.5 * m.weeks_with_vol) AS INT64))
    AND SAFE_DIVIDE(h.hub_vol, m.total_vol) >= 0.10
    AND SAFE_DIVIDE(h.hub_candidate_vol, h.candidate_ind_days) < 2
),

order_flagged AS (
  SELECT
    b.lookback_window,
    b.timebase,
    b.supplier_id,
    b.su_name,
    b.parent_suid,
    b.parent_su_name,
    p.parent_warehouse_states,
    b.sto,
    b.srm_contact,
    b.own_state,
    b.city_name,
    b.postal_code,
    b.ops,
    b.purchase_order_number,
    b.tracking_number,
    b.msbd_su,
    b.promised_delivery_end_range_date_at_order,
    b.order_complete_date,
    b.induction_date_lidd,
    b.ind_day,
    b.delivery_date,
    b.week_start,
    b.assigned_induction_hub_name,
    b.assigned_station_state,
    b.assigned_station_zip,
    b.actual_induction_hub_name,
    b.actual_induction_hub_state,
    b.actual_induction_hub_zip,
    b.destination_zipcode,
    b.destination_state,
    b.distance_assignedhub_customer,
    b.distance_actualhub_customer,
    b.distance_assignedhub_actualhub,
    b.direct_gain,
    b.inducted_on_time_or_early,
    b.delivery_rel,
    b.missing_actual_hub,
    b.is_sibling_state,
    b.is_direct_candidate,
    CASE
      WHEN b.is_direct_candidate = 0 THEN 'non_candidate'
      WHEN b.is_sibling_state = 1 THEN 'misshipping'
      WHEN g.actual_induction_hub_name IS NOT NULL THEN 'ghost_warehouse'
      WHEN COALESCE(b.direct_gain, 0) < 0.4 THEN 'jumbo'
      ELSE 'direct'
    END AS candidate_bucket,
    CASE
      WHEN b.is_direct_candidate = 1 AND b.is_sibling_state = 1 THEN 1
      ELSE 0
    END AS is_misshipping,
    CASE
      WHEN b.is_direct_candidate = 1
        AND b.is_sibling_state = 0
        AND g.actual_induction_hub_name IS NOT NULL THEN 1
      ELSE 0
    END AS is_ghost_warehouse,
    CASE
      WHEN b.is_direct_candidate = 1
        AND b.is_sibling_state = 0
        AND g.actual_induction_hub_name IS NULL
        AND COALESCE(b.direct_gain, 0) < 0.4 THEN 1
      ELSE 0
    END AS is_jumbo,
    CASE
      WHEN b.is_direct_candidate = 1
        AND b.is_sibling_state = 0
        AND g.actual_induction_hub_name IS NULL
        AND COALESCE(b.direct_gain, 0) >= 0.4 THEN 1
      ELSE 0
    END AS is_direct
  FROM base_enriched AS b
  LEFT JOIN ghost_hubs AS g
    ON b.lookback_window = g.lookback_window
   AND b.supplier_id = g.supplier_id
   AND b.actual_induction_hub_name = g.actual_induction_hub_name
  LEFT JOIN parent_state_list AS p
    ON b.lookback_window = p.lookback_window
   AND b.parent_suid = p.parent_suid
)

-- =====================================================================
-- SUPPLIER ROLLUP
-- Swap this block for `SELECT * FROM order_flagged` to get order-level.
-- Partition: candidate = direct + jumbo + ghost + misshipping
-- =====================================================================
SELECT
  lookback_window,
  timebase,
  supplier_id,
  ANY_VALUE(su_name) AS su_name,
  ANY_VALUE(parent_suid) AS parent_suid,
  ANY_VALUE(parent_su_name) AS parent_su_name,
  ANY_VALUE(parent_warehouse_states) AS parent_warehouse_states,
  ANY_VALUE(sto) AS sto,
  ANY_VALUE(srm_contact) AS srm_contact,
  ANY_VALUE(own_state) AS own_state,
  ANY_VALUE(city_name) AS city_name,
  ANY_VALUE(postal_code) AS postal_code,
  ANY_VALUE(assigned_induction_hub_name) AS assigned_induction_hub_name,
  ANY_VALUE(assigned_station_state) AS assigned_station_state,

  COUNT(DISTINCT ops) AS total_vol,
  AVG(inducted_on_time_or_early) AS ifr_all,
  AVG(delivery_rel) AS delivery_rel_all,

  COUNT(DISTINCT IF(is_direct_candidate = 1, ops, NULL)) AS candidate_vol,
  COUNT(DISTINCT IF(is_direct_candidate = 0, ops, NULL)) AS non_candidate_vol,
  SAFE_DIVIDE(
    COUNT(DISTINCT IF(is_direct_candidate = 1, ops, NULL)),
    COUNT(DISTINCT ops)
  ) AS pct_candidate,

  AVG(IF(is_direct_candidate = 1, inducted_on_time_or_early, NULL)) AS ifr_candidate,
  AVG(IF(is_direct_candidate = 0, inducted_on_time_or_early, NULL)) AS ifr_non_candidate,
  AVG(IF(is_direct_candidate = 1, delivery_rel, NULL)) AS delivery_rel_candidate,
  AVG(IF(is_direct_candidate = 0, delivery_rel, NULL)) AS delivery_rel_non_candidate,

  COUNT(DISTINCT IF(is_direct = 1, ops, NULL)) AS direct_vol,
  SAFE_DIVIDE(
    COUNT(DISTINCT IF(is_direct = 1, ops, NULL)),
    COUNT(DISTINCT IF(is_direct_candidate = 1, ops, NULL))
  ) AS pct_of_candidates_direct,
  AVG(IF(is_direct = 1, inducted_on_time_or_early, NULL)) AS ifr_direct,
  AVG(IF(is_direct = 1, delivery_rel, NULL)) AS delivery_rel_direct,
  AVG(IF(is_direct = 1, direct_gain, NULL)) AS avg_gain_direct,

  COUNT(DISTINCT IF(is_jumbo = 1, ops, NULL)) AS jumbo_vol,
  SAFE_DIVIDE(
    COUNT(DISTINCT IF(is_jumbo = 1, ops, NULL)),
    COUNT(DISTINCT IF(is_direct_candidate = 1, ops, NULL))
  ) AS pct_of_candidates_jumbo,
  AVG(IF(is_jumbo = 1, inducted_on_time_or_early, NULL)) AS ifr_jumbo,
  AVG(IF(is_jumbo = 1, delivery_rel, NULL)) AS delivery_rel_jumbo,
  AVG(IF(is_jumbo = 1, direct_gain, NULL)) AS avg_gain_jumbo,

  COUNT(DISTINCT IF(is_ghost_warehouse = 1, ops, NULL)) AS ghost_warehouse_vol,
  SAFE_DIVIDE(
    COUNT(DISTINCT IF(is_ghost_warehouse = 1, ops, NULL)),
    COUNT(DISTINCT IF(is_direct_candidate = 1, ops, NULL))
  ) AS pct_of_candidates_ghost,
  AVG(IF(is_ghost_warehouse = 1, inducted_on_time_or_early, NULL)) AS ifr_ghost,
  AVG(IF(is_ghost_warehouse = 1, delivery_rel, NULL)) AS delivery_rel_ghost,

  COUNT(DISTINCT IF(is_misshipping = 1, ops, NULL)) AS misshipping_vol,
  SAFE_DIVIDE(
    COUNT(DISTINCT IF(is_misshipping = 1, ops, NULL)),
    COUNT(DISTINCT IF(is_direct_candidate = 1, ops, NULL))
  ) AS pct_of_candidates_misshipping,
  AVG(IF(is_misshipping = 1, inducted_on_time_or_early, NULL)) AS ifr_misshipping,
  AVG(IF(is_misshipping = 1, delivery_rel, NULL)) AS delivery_rel_misshipping,

  (
    COUNT(DISTINCT IF(is_direct = 1, ops, NULL))
    + COUNT(DISTINCT IF(is_jumbo = 1, ops, NULL))
    + COUNT(DISTINCT IF(is_ghost_warehouse = 1, ops, NULL))
    + COUNT(DISTINCT IF(is_misshipping = 1, ops, NULL))
  ) AS candidate_bucket_sum,
  (
    COUNT(DISTINCT IF(is_direct_candidate = 1, ops, NULL))
    = (
      COUNT(DISTINCT IF(is_direct = 1, ops, NULL))
      + COUNT(DISTINCT IF(is_jumbo = 1, ops, NULL))
      + COUNT(DISTINCT IF(is_ghost_warehouse = 1, ops, NULL))
      + COUNT(DISTINCT IF(is_misshipping = 1, ops, NULL))
    )
  ) AS candidate_partition_ok

FROM order_flagged
GROUP BY lookback_window, timebase, supplier_id
HAVING COUNT(DISTINCT ops) >= 50
ORDER BY candidate_vol DESC, total_vol DESC
