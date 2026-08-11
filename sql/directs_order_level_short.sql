-- Short order-level directs flags (DS only, last 10w by PDD)
-- candidate_bucket: misshipping | ghost_warehouse | jumbo | direct | non_candidate
--
-- Optional: add AND supplier_id = 12345 in `base`

WITH
base AS (
  SELECT
    o.supplier_id,
    o.su_name,
    o.parent_suid,
    o.parent_su_name,
    o.sto,
    o.ops,
    o.purchase_order_number,
    o.tracking_number,
    o.msbd_su,
    o.promised_delivery_end_range_date_at_order,
    o.induction_date_lidd,
    o.delivery_date,
    o.state_name AS own_state,
    o.assigned_induction_hub_name,
    o.assigned_station_state,
    o.actual_induction_hub_name,
    o.actual_induction_hub_state,
    o.destination_zipcode,
    o.destination_state,
    o.distance_assignedhub_customer,
    o.distance_actualhub_customer,
    o.distance_assignedhub_actualhub,
    o.direct_gain,
    o.inducted_on_time_or_early,
    o.delivery_rel,
    COALESCE(DATE(o.carrier_first_induction_date_time), o.induction_date_lidd) AS ind_day,
    DATE_TRUNC(o.promised_delivery_end_range_date_at_order, WEEK(SUNDAY)) AS week_start,
    CASE
      WHEN o.assignedhub_notequal_actualhub_flag = 1
        AND COALESCE(o.distance_assignedhub_customer, 0) >= 400
        AND COALESCE(o.distance_assignedhub_actualhub, 0) >= 200 THEN 1
      ELSE 0
    END AS is_candidate
  FROM `wf-gcp-us-ae-global-tnd-prod.speed_and_reliability.HVE_perf_Monitoring` AS o
  WHERE o.fulfillment_type = 'DS'
    AND o.promised_delivery_end_range_date_at_order
        >= DATE_SUB(CURRENT_DATE(), INTERVAL 10 WEEK)
    AND o.promised_delivery_end_range_date_at_order < CURRENT_DATE()
),

parent_states AS (
  SELECT DISTINCT parent_suid, state_name AS warehouse_state
  FROM `wf-gcp-us-ae-global-tnd-prod.speed_and_reliability.HVE_perf_Monitoring`
  WHERE fulfillment_type = 'DS'
    AND parent_suid IS NOT NULL
    AND state_name IS NOT NULL
    AND promised_delivery_end_range_date_at_order
        >= DATE_SUB(CURRENT_DATE(), INTERVAL 10 WEEK)
    AND promised_delivery_end_range_date_at_order < CURRENT_DATE()
),

enriched AS (
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
    ON b.parent_suid = ps.parent_suid
   AND b.actual_induction_hub_state = ps.warehouse_state
),

supplier_weeks AS (
  SELECT supplier_id, COUNT(DISTINCT week_start) AS weeks_with_vol
  FROM enriched
  GROUP BY 1
),

ghost_hubs AS (
  SELECT
    e.supplier_id,
    e.actual_induction_hub_name
  FROM enriched AS e
  JOIN supplier_weeks AS w USING (supplier_id)
  WHERE e.is_candidate = 1
    AND e.actual_induction_hub_name IS NOT NULL
    AND e.is_sibling_state = 0
  GROUP BY e.supplier_id, e.actual_induction_hub_name, w.weeks_with_vol
  HAVING COUNT(DISTINCT e.ops)
         / NULLIF(
             (SELECT COUNT(DISTINCT ops) FROM enriched e2 WHERE e2.supplier_id = e.supplier_id),
             0
           ) >= 0.10
     AND COUNT(DISTINCT e.week_start) >= GREATEST(2, CAST(CEIL(0.5 * w.weeks_with_vol) AS INT64))
     AND AVG(CASE
           WHEN e.distance_assignedhub_actualhub >= 200 THEN 1 ELSE 0
         END) >= 0.8
)

SELECT
  e.*,
  CASE
    WHEN e.is_candidate = 0 THEN 'non_candidate'
    WHEN e.is_sibling_state = 1 THEN 'misshipping'
    WHEN g.actual_induction_hub_name IS NOT NULL THEN 'ghost_warehouse'
    WHEN COALESCE(e.direct_gain, 0) < 0.4 THEN 'jumbo'
    ELSE 'direct'
  END AS candidate_bucket
FROM enriched AS e
LEFT JOIN ghost_hubs AS g
  ON e.supplier_id = g.supplier_id
 AND e.actual_induction_hub_name = g.actual_induction_hub_name
-- WHERE e.supplier_id = 12345   -- optional
-- WHERE e.is_candidate = 1      -- candidates only
ORDER BY e.supplier_id, e.promised_delivery_end_range_date_at_order DESC, e.ops
