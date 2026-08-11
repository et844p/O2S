-- Directs order-level flags + supplier performance rollup
--
-- Same classification rules as directs_supplier_cohorts.sql:
--   CANDIDATE = assignedhub != actualhub
--               AND distance_assignedhub_customer >= 400
--               AND distance_assignedhub_actualhub >= 200
--   Then split candidates via parent warehouse states + induction grouping:
--     non_compliant / ghost_warehouse / actually_direct / jumbo / other_candidate
--   Sibling-state candidates are always non_compliant.
--   Actually direct: grouped far batches, <10% supplier vol, no minimum share, gain >= 0.4.
--   Jumbo: same pattern with gain < 0.4 / null.
--   Large grouped alternate hubs (>=10% grouped) that are not ghost = relief/FedEx → non_candidate.
--
-- Default window: last 10 weeks by promised_delivery_end_range_date_at_order.
-- Change `windows` CTE to switch timebase/length.
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

hub_day AS (
  SELECT
    lookback_window,
    supplier_id,
    actual_induction_hub_name,
    ind_day,
    COUNT(DISTINCT IF(is_direct_candidate = 1, ops, NULL)) AS candidate_on_day
  FROM base
  WHERE missing_actual_hub = 0
    AND is_direct_candidate = 1
    AND actual_induction_hub_name IS NOT NULL
  GROUP BY 1, 2, 3, 4
),

base_enriched AS (
  SELECT
    b.*,
    CASE
      WHEN b.is_direct_candidate = 1 AND COALESCE(hd.candidate_on_day, 0) >= 2 THEN 1
      ELSE 0
    END AS is_grouped,
    CASE
      WHEN ps.warehouse_state IS NOT NULL
        AND b.actual_induction_hub_state IS NOT NULL
        AND b.actual_induction_hub_state != b.own_state THEN 1
      ELSE 0
    END AS is_sibling_state
  FROM base AS b
  LEFT JOIN hub_day AS hd
    ON b.lookback_window = hd.lookback_window
   AND b.supplier_id = hd.supplier_id
   AND b.actual_induction_hub_name = hd.actual_induction_hub_name
   AND b.ind_day = hd.ind_day
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
    actual_induction_hub_state,
    ANY_VALUE(is_sibling_state) AS is_sibling_state,
    COUNT(DISTINCT ops) AS hub_vol,
    COUNT(DISTINCT IF(is_direct_candidate = 1, ops, NULL)) AS hub_candidate_vol,
    COUNT(DISTINCT IF(is_grouped = 1, ops, NULL)) AS hub_grouped_vol,
    COUNT(DISTINCT IF(is_direct_candidate = 1, week_start, NULL)) AS weeks_with_candidate,
    COUNT(DISTINCT IF(is_grouped = 1, week_start, NULL)) AS weeks_with_grouped,
    AVG(CASE WHEN is_far_hub_induction = 1 THEN 1 ELSE 0 END) AS pct_far
  FROM base_enriched
  WHERE missing_actual_hub = 0
    AND actual_induction_hub_name IS NOT NULL
  GROUP BY 1, 2, 3, 4
),

hub_bucketed AS (
  SELECT
    h.lookback_window,
    h.supplier_id,
    h.actual_induction_hub_name,
    h.actual_induction_hub_state,
    CASE
      WHEN h.is_sibling_state = 0
        AND h.pct_far >= 0.8
        AND h.weeks_with_candidate >= GREATEST(2, CAST(CEIL(0.5 * m.weeks_with_vol) AS INT64))
        AND SAFE_DIVIDE(h.hub_vol, m.total_vol) >= 0.10
        THEN 'ghost_warehouse'
      WHEN h.is_sibling_state = 1
        AND h.hub_candidate_vol > 0
        THEN 'non_compliant'
      WHEN h.is_sibling_state = 0
        AND SAFE_DIVIDE(h.hub_grouped_vol, m.total_vol) >= 0.10
        THEN 'not_candidate'
      WHEN h.hub_grouped_vol > 0
        AND h.weeks_with_grouped >= 2
        AND h.pct_far >= 0.8
        AND SAFE_DIVIDE(h.hub_grouped_vol, m.total_vol) < 0.10
        THEN 'actually_direct'
      WHEN h.hub_candidate_vol > 0 THEN 'other_candidate'
      ELSE 'not_candidate'
    END AS hub_bucket
  FROM hub_agg AS h
  JOIN supplier_meta AS m
    USING (lookback_window, supplier_id)
),

-- Order-level flagged rows
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
    b.is_grouped,
    b.is_direct_candidate,
    COALESCE(h.hub_bucket, 'not_candidate') AS hub_bucket,
    CASE
      WHEN b.is_direct_candidate = 0 THEN 'non_candidate'
      WHEN COALESCE(h.hub_bucket, 'not_candidate') = 'ghost_warehouse' THEN 'ghost_warehouse'
      WHEN COALESCE(h.hub_bucket, 'not_candidate') = 'non_compliant' THEN 'non_compliant'
      WHEN COALESCE(h.hub_bucket, 'not_candidate') = 'actually_direct'
        AND b.is_grouped = 1
        AND b.direct_gain >= 0.4 THEN 'actually_direct'
      WHEN COALESCE(h.hub_bucket, 'not_candidate') = 'actually_direct'
        AND b.is_grouped = 1 THEN 'jumbo'
      WHEN b.is_direct_candidate = 1 THEN 'other_candidate'
      ELSE 'non_candidate'
    END AS candidate_bucket,
    CASE
      WHEN b.is_direct_candidate = 1
        AND COALESCE(h.hub_bucket, 'not_candidate') = 'ghost_warehouse' THEN 1
      ELSE 0
    END AS is_ghost_warehouse,
    CASE
      WHEN b.is_direct_candidate = 1
        AND COALESCE(h.hub_bucket, 'not_candidate') = 'non_compliant' THEN 1
      ELSE 0
    END AS is_non_compliant,
    CASE
      WHEN b.is_direct_candidate = 1
        AND COALESCE(h.hub_bucket, 'not_candidate') = 'actually_direct'
        AND b.is_grouped = 1
        AND b.direct_gain >= 0.4 THEN 1
      ELSE 0
    END AS is_actually_direct,
    CASE
      WHEN b.is_direct_candidate = 1
        AND COALESCE(h.hub_bucket, 'not_candidate') = 'actually_direct'
        AND b.is_grouped = 1
        AND NOT (b.direct_gain >= 0.4) THEN 1
      ELSE 0
    END AS is_jumbo,
    CASE
      WHEN b.is_direct_candidate = 1
        AND NOT (
          COALESCE(h.hub_bucket, 'not_candidate') IN ('ghost_warehouse', 'non_compliant')
          OR (
            COALESCE(h.hub_bucket, 'not_candidate') = 'actually_direct'
            AND b.is_grouped = 1
          )
        ) THEN 1
      ELSE 0
    END AS is_other_candidate
  FROM base_enriched AS b
  LEFT JOIN hub_bucketed AS h
    ON b.lookback_window = h.lookback_window
   AND b.supplier_id = h.supplier_id
   AND b.actual_induction_hub_name = h.actual_induction_hub_name
  LEFT JOIN parent_state_list AS p
    ON b.lookback_window = p.lookback_window
   AND b.parent_suid = p.parent_suid
)

-- ORDER-LEVEL OUTPUT
-- Flags: is_direct_candidate, is_actually_direct (gain>=0.4), is_jumbo,
--        is_ghost_warehouse, is_non_compliant, is_other_candidate, candidate_bucket
SELECT *
FROM order_flagged
ORDER BY supplier_id, promised_delivery_end_range_date_at_order DESC, ops

