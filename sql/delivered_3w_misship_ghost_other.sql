-- Last 3 weeks delivered DS volume: misship / ghost / other (closer vs farther)
--
-- Universe: fulfillment_type = 'DS', delivery_date in [as_of-3w, as_of)
--
-- Exclusive buckets (priority):
--   misshipping      — wrong hub AND parent has another WH in induction state
--                      (sibling warehouse under same parent_suid)
--   ghost            — wrong hub
--                      AND distance_assignedhub_actualhub >= 200 (very far from current WH)
--                      AND NOT closer to customer than assigned
--                      AND not misshipping
--   other_closer     — wrong hub, not misship/ghost, actual closer to customer than assigned
--                      (includes near swaps and far "direct-like" moves)
--   other_farther    — wrong hub, not misship/ghost, actual farther/equal, AND >=200 from assigned
--                      (rare residual; most far+not-closer is ghost)
--   local_wrong_hub  — wrong hub, <200 from assigned, not closer (local hub / data noise)
--   aligned          — not wrong-hub
--
-- Distances: raw columns only (do not trust distance_assignedhub_actualhub_200_plus).
-- Volume: COUNT(DISTINCT ops)

WITH params AS (
  SELECT CURRENT_DATE() AS as_of
),

window_bounds AS (
  SELECT
    'delivered_3w' AS lookback_window,
    'delivery_date' AS timebase,
    3 AS lookback_weeks,
    DATE_SUB((SELECT as_of FROM params), INTERVAL 3 WEEK) AS window_start,
    (SELECT as_of FROM params) AS window_end
),

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

base AS (
  SELECT
    w.lookback_window,
    w.timebase,
    w.lookback_weeks,
    w.window_start,
    w.window_end,
    o.supplier_id,
    o.su_name,
    o.parent_suid,
    o.parent_su_name,
    o.sto,
    o.srm_contact,
    o.state_name AS own_state,
    o.ops,
    o.purchase_order_number,
    o.tracking_number,
    DATE(o.delivery_date) AS delivery_date,
    o.assigned_induction_hub_name,
    o.assigned_station_state,
    o.actual_induction_hub_name,
    o.actual_induction_hub_state,
    o.destination_state,
    o.distance_assignedhub_customer,
    o.distance_actualhub_customer,
    o.distance_assignedhub_actualhub,
    o.assignedhub_notequal_actualhub_flag,
    o.direct_gain,
    o.inducted_on_time_or_early,
    o.delivery_rel,

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
),

classified AS (
  SELECT
    b.*,
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
)

SELECT
  lookback_window,
  timebase,
  lookback_weeks,
  window_start,
  window_end,
  vol_bucket,
  COUNT(DISTINCT ops) AS vol,
  SAFE_DIVIDE(
    COUNT(DISTINCT ops),
    SUM(COUNT(DISTINCT ops)) OVER ()
  ) AS pct_of_delivered_vol,
  AVG(inducted_on_time_or_early) AS ifr,
  AVG(delivery_rel) AS delivery_rel,
  AVG(distance_assignedhub_customer) AS avg_dist_assignedhub_customer,
  AVG(distance_actualhub_customer) AS avg_dist_actualhub_customer,
  AVG(distance_assignedhub_actualhub) AS avg_dist_assignedhub_actualhub,
  AVG(direct_gain) AS avg_direct_gain
FROM classified
GROUP BY 1, 2, 3, 4, 5, 6
ORDER BY
  CASE vol_bucket
    WHEN 'misshipping' THEN 1
    WHEN 'ghost' THEN 2
    WHEN 'other_closer' THEN 3
    WHEN 'other_farther' THEN 4
    WHEN 'local_wrong_hub' THEN 5
    ELSE 6
  END
