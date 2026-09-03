-- Order-level classification: last 3 weeks delivered DS volume
--
-- Universe: fulfillment_type = 'DS', delivery_date in [CURRENT_DATE()-3 WEEK, CURRENT_DATE)
-- Volume grain: one row per ops (order product id)
--
-- Exclusive vol_bucket (priority):
--   misshipping     — wrong hub AND inducted in a sibling parent WH state
--                     (another warehouse under same parent_suid)
--   ghost           — wrong hub
--                     AND distance_assignedhub_actualhub >= 200
--                     AND NOT closer to customer than assigned hub
--   other_closer    — wrong hub, not misship/ghost, actual closer to customer
--   other_farther   — wrong hub, not misship/ghost, >=200 from assigned, not closer
--                     (usually empty; ghost already catches this)
--   local_wrong_hub — wrong hub, <200 from assigned, not closer (local hub noise)
--   aligned         — not wrong hub
--
-- Closer = distance_actualhub_customer < distance_assignedhub_customer
-- Distances: raw columns only (do NOT trust distance_assignedhub_actualhub_200_plus)
--
-- Run in BigQuery as-is, or:
--   from gbq import query_df
--   df = query_df(open('sql/delivered_3w_order_classification.sql').read())

WITH params AS (
  SELECT CURRENT_DATE() AS as_of
),

window_bounds AS (
  SELECT
    DATE_SUB((SELECT as_of FROM params), INTERVAL 3 WEEK) AS window_start,
    (SELECT as_of FROM params) AS window_end
),

-- Distinct WH states under each parent in the same delivered window
parent_states AS (
  SELECT DISTINCT
    o.parent_suid,
    o.state_name AS warehouse_state
  FROM `wf-gcp-us-ae-global-tnd-prod.speed_and_reliability.HVE_perf_Monitoring` AS o
  CROSS JOIN window_bounds AS w
  WHERE o.fulfillment_type = 'DS'
    AND o.parent_suid IS NOT NULL
    AND o.state_name IS NOT NULL
    AND DATE(o.delivery_date) >= w.window_start
    AND DATE(o.delivery_date) < w.window_end
),

parent_state_list AS (
  SELECT
    parent_suid,
    STRING_AGG(DISTINCT warehouse_state, ',' ORDER BY warehouse_state) AS parent_warehouse_states
  FROM parent_states
  GROUP BY 1
),

base AS (
  SELECT
    o.ops,
    o.purchase_order_number,
    o.tracking_number,
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
    DATE(o.delivery_date) AS delivery_date,
    o.msbd_su,
    o.promised_delivery_end_range_date_at_order,
    o.assigned_induction_hub_name,
    o.assigned_station_state,
    o.assigned_station_zip,
    o.actual_induction_hub_name,
    o.actual_induction_hub_state,
    o.actual_induction_hub_zip,
    o.destination_state,
    o.destination_zipcode,
    o.distance_assignedhub_customer,
    o.distance_actualhub_customer,
    o.distance_assignedhub_actualhub,
    o.direct_gain,
    o.inducted_on_time_or_early,
    o.delivery_rel,
    o.assignedhub_notequal_actualhub_flag,

    CASE
      WHEN o.assignedhub_notequal_actualhub_flag = 1 THEN 1
      ELSE 0
    END AS is_wrong_hub,

    CASE
      WHEN ps.warehouse_state IS NOT NULL
        AND o.actual_induction_hub_state IS NOT NULL
        AND o.actual_induction_hub_state != o.state_name
        THEN 1
      ELSE 0
    END AS is_sibling_state,

    CASE
      WHEN COALESCE(o.distance_actualhub_customer, 999999)
         < COALESCE(o.distance_assignedhub_customer, 0)
        THEN 1
      ELSE 0
    END AS is_closer_to_customer,

    CASE
      WHEN COALESCE(o.distance_assignedhub_actualhub, 0) >= 200 THEN 1
      ELSE 0
    END AS is_far_from_assigned_wh

  FROM `wf-gcp-us-ae-global-tnd-prod.speed_and_reliability.HVE_perf_Monitoring` AS o
  CROSS JOIN window_bounds AS w
  LEFT JOIN parent_states AS ps
    ON o.parent_suid = ps.parent_suid
   AND o.actual_induction_hub_state = ps.warehouse_state
  WHERE o.fulfillment_type = 'DS'
    AND o.delivery_date IS NOT NULL
    AND DATE(o.delivery_date) >= w.window_start
    AND DATE(o.delivery_date) < w.window_end
)

SELECT
  b.ops,
  b.purchase_order_number,
  b.tracking_number,
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
  b.address_1,
  b.delivery_date,
  b.msbd_su,
  b.promised_delivery_end_range_date_at_order,
  b.assigned_induction_hub_name,
  b.assigned_station_state,
  b.assigned_station_zip,
  b.actual_induction_hub_name,
  b.actual_induction_hub_state,
  b.actual_induction_hub_zip,
  b.destination_state,
  b.destination_zipcode,
  b.distance_assignedhub_customer,
  b.distance_actualhub_customer,
  b.distance_assignedhub_actualhub,
  ROUND(
    COALESCE(b.distance_assignedhub_customer, 0)
    - COALESCE(b.distance_actualhub_customer, 0),
    1
  ) AS miles_closer_to_customer,
  b.direct_gain,
  b.inducted_on_time_or_early,
  b.delivery_rel,
  b.is_wrong_hub,
  b.is_sibling_state,
  b.is_closer_to_customer,
  b.is_far_from_assigned_wh,

  CASE
    WHEN b.is_wrong_hub = 1 AND b.is_sibling_state = 1
      THEN 'misshipping'
    WHEN b.is_wrong_hub = 1
      AND b.is_far_from_assigned_wh = 1
      AND b.is_closer_to_customer = 0
      THEN 'ghost'
    WHEN b.is_wrong_hub = 1 AND b.is_closer_to_customer = 1
      THEN 'other_closer'
    WHEN b.is_wrong_hub = 1 AND b.is_far_from_assigned_wh = 1
      THEN 'other_farther'
    WHEN b.is_wrong_hub = 1
      THEN 'local_wrong_hub'
    ELSE 'aligned'
  END AS vol_bucket

FROM base AS b
LEFT JOIN parent_state_list AS p
  ON b.parent_suid = p.parent_suid
ORDER BY b.delivery_date DESC, b.ops
