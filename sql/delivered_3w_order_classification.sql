-- Order-level classification: last 3 weeks delivered DS volume
--
-- Universe: fulfillment_type = 'DS', delivery_date in [CURRENT_DATE()-3 WEEK, CURRENT_DATE)
-- Grain: one row per ops
--
-- Misshipping if either:
--   (A) Sibling STATE — parent has another WH in the induction state
--       (actual_induction_hub_state != own_state, join to parent_states)
--   (B) Sibling HUB  — inducts at a hub where a *different* SUID under the
--       same parent_suid puts >= 20% of that SUID's volume in this window
--
-- Exclusive vol_bucket (priority):
--   misshipping     — wrong hub AND (sibling state OR sibling hub)
--   ghost           — wrong hub, >=200mi from assigned WH, NOT closer to customer
--                     (missing distances => treated as not closer for ghost)
--   other_closer    — wrong hub, not misship/ghost, known closer to customer
--   other_farther   — wrong hub, not misship/ghost, >=200 from assigned, not closer
--   local_wrong_hub — wrong hub, <200 from assigned, not closer
--   aligned         — not wrong hub
--
-- Closer: actual < assigned distance; NULL if either distance is null
-- Distances: raw columns only (do NOT trust distance_assignedhub_actualhub_200_plus)

WITH params AS (
  SELECT CURRENT_DATE() AS as_of
),

window_bounds AS (
  SELECT
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

parent_state_list AS (
  SELECT
    parent_suid,
    STRING_AGG(DISTINCT warehouse_state, ',' ORDER BY warehouse_state) AS parent_warehouse_states
  FROM parent_states
  GROUP BY 1
),

suid_hub_vol AS (
  SELECT
    o.parent_suid,
    o.supplier_id,
    o.actual_induction_hub_name,
    COUNT(DISTINCT o.ops) AS hub_vol
  FROM `wf-gcp-us-ae-global-tnd-prod.speed_and_reliability.HVE_perf_Monitoring` AS o
  CROSS JOIN window_bounds AS w
  WHERE o.fulfillment_type = 'DS'
    AND o.parent_suid IS NOT NULL
    AND o.actual_induction_hub_name IS NOT NULL
    AND DATE(o.delivery_date) >= w.window_start
    AND DATE(o.delivery_date) < w.window_end
  GROUP BY 1, 2, 3
),

suid_tot AS (
  SELECT
    parent_suid,
    supplier_id,
    SUM(hub_vol) AS total_vol
  FROM suid_hub_vol
  GROUP BY 1, 2
),

-- Hubs that are "home" for a SUID: >=20% of that SUID's delivered vol
sibling_home_hubs AS (
  SELECT
    h.parent_suid,
    h.supplier_id AS home_supplier_id,
    h.actual_induction_hub_name,
    SAFE_DIVIDE(h.hub_vol, t.total_vol) AS home_hub_share
  FROM suid_hub_vol AS h
  JOIN suid_tot AS t
    USING (parent_suid, supplier_id)
  WHERE t.total_vol > 0
    AND SAFE_DIVIDE(h.hub_vol, t.total_vol) >= 0.20
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

    CASE
      WHEN o.assignedhub_notequal_actualhub_flag = 1 THEN 1
      ELSE 0
    END AS is_wrong_hub,

    -- (A) Sibling STATE: parent has WH in induction state ≠ this SUID's own state
    CASE
      WHEN ps.warehouse_state IS NOT NULL
        AND o.actual_induction_hub_state IS NOT NULL
        AND o.actual_induction_hub_state != o.state_name
        THEN 1
      ELSE 0
    END AS is_sibling_state,

    -- (B) Sibling HUB: a *different* SUID under same parent has >=20% vol at this hub
    CASE
      WHEN EXISTS (
        SELECT 1
        FROM sibling_home_hubs AS sh
        WHERE sh.parent_suid = o.parent_suid
          AND sh.actual_induction_hub_name = o.actual_induction_hub_name
          AND sh.home_supplier_id != o.supplier_id
      ) THEN 1
      ELSE 0
    END AS is_sibling_hub,

    (
      SELECT STRING_AGG(
        DISTINCT CAST(sh.home_supplier_id AS STRING),
        ','
        ORDER BY CAST(sh.home_supplier_id AS STRING)
      )
      FROM sibling_home_hubs AS sh
      WHERE sh.parent_suid = o.parent_suid
        AND sh.actual_induction_hub_name = o.actual_induction_hub_name
        AND sh.home_supplier_id != o.supplier_id
    ) AS sibling_hub_home_supplier_ids,

    (
      SELECT MAX(sh.home_hub_share)
      FROM sibling_home_hubs AS sh
      WHERE sh.parent_suid = o.parent_suid
        AND sh.actual_induction_hub_name = o.actual_induction_hub_name
        AND sh.home_supplier_id != o.supplier_id
    ) AS sibling_hub_home_share_max,

    CASE
      WHEN o.distance_actualhub_customer IS NULL
        OR o.distance_assignedhub_customer IS NULL
        THEN NULL
      WHEN o.distance_actualhub_customer < o.distance_assignedhub_customer
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
  CASE
    WHEN b.distance_assignedhub_customer IS NULL
      OR b.distance_actualhub_customer IS NULL
      THEN NULL
    ELSE ROUND(
      b.distance_assignedhub_customer - b.distance_actualhub_customer,
      1
    )
  END AS miles_closer_to_customer,
  b.direct_gain,
  b.inducted_on_time_or_early,
  b.delivery_rel,
  b.is_wrong_hub,
  b.is_sibling_state,
  b.is_sibling_hub,
  b.sibling_hub_home_supplier_ids,
  b.sibling_hub_home_share_max,
  b.is_closer_to_customer,
  b.is_far_from_assigned_wh,

  CASE
    WHEN b.is_wrong_hub = 1
      AND (b.is_sibling_state = 1 OR b.is_sibling_hub = 1)
      THEN 'misshipping'
    WHEN b.is_wrong_hub = 1
      AND b.is_far_from_assigned_wh = 1
      AND COALESCE(b.is_closer_to_customer, 0) = 0
      THEN 'ghost'
    WHEN b.is_wrong_hub = 1
      AND b.is_closer_to_customer = 1
      THEN 'other_closer'
    WHEN b.is_wrong_hub = 1
      AND b.is_far_from_assigned_wh = 1
      THEN 'other_farther'
    WHEN b.is_wrong_hub = 1
      THEN 'local_wrong_hub'
    ELSE 'aligned'
  END AS vol_bucket

FROM base AS b
LEFT JOIN parent_state_list AS p
  ON b.parent_suid = p.parent_suid
ORDER BY b.delivery_date DESC, b.ops
