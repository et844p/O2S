-- Short order-level directs flags (DS, last 10w by PDD)
-- candidate_bucket: misshipping | ghost_warehouse | jumbo | direct | sparse_far | non_candidate
-- Uncomment a WHERE at the bottom to filter.

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
    IF(
      ps.warehouse_state IS NOT NULL
      AND b.actual_induction_hub_state IS NOT NULL
      AND b.actual_induction_hub_state != b.own_state,
      1, 0
    ) AS is_sibling_state
  FROM base AS b
  LEFT JOIN parent_states AS ps
    ON b.parent_suid = ps.parent_suid
   AND b.actual_induction_hub_state = ps.warehouse_state
),

supplier_meta AS (
  SELECT
    supplier_id,
    COUNT(DISTINCT ops) AS total_vol,
    COUNT(DISTINCT week_start) AS weeks_with_vol
  FROM enriched
  GROUP BY 1
),

hub_agg AS (
  SELECT
    e.supplier_id,
    e.actual_induction_hub_name,
    MAX(e.is_sibling_state) AS is_sibling_state,
    COUNT(DISTINCT e.ops) AS hub_vol,
    COUNT(DISTINCT IF(e.is_candidate = 1, e.ops, NULL)) AS hub_candidate_vol,
    COUNT(DISTINCT IF(e.is_candidate = 1, e.week_start, NULL)) AS weeks_with_candidate,
    AVG(IF(COALESCE(e.distance_assignedhub_actualhub, 0) >= 200, 1, 0)) AS pct_far
  FROM enriched AS e
  WHERE e.actual_induction_hub_name IS NOT NULL
  GROUP BY 1, 2
),

ghost_hubs AS (
  SELECT h.supplier_id, h.actual_induction_hub_name
  FROM hub_agg AS h
  JOIN supplier_meta AS m USING (supplier_id)
  WHERE h.is_sibling_state = 0
    AND h.hub_candidate_vol > 0
    AND h.pct_far >= 0.8
    AND h.weeks_with_candidate >= GREATEST(2, CAST(CEIL(0.5 * m.weeks_with_vol) AS INT64))
    AND SAFE_DIVIDE(h.hub_vol, m.total_vol) >= 0.10
),

material_direct_hubs AS (
  SELECT h.supplier_id, h.actual_induction_hub_name
  FROM hub_agg AS h
  JOIN supplier_meta AS m USING (supplier_id)
  WHERE h.hub_candidate_vol >= GREATEST(20, CAST(CEIL(0.003 * m.total_vol) AS INT64))
     OR (
       SAFE_DIVIDE(h.hub_vol, m.total_vol) >= 0.005
       AND h.hub_candidate_vol >= 10
     )
)

SELECT
  e.*,
  CASE
    WHEN e.is_candidate = 0 THEN 'non_candidate'
    WHEN e.is_sibling_state = 1 THEN 'misshipping'
    WHEN g.actual_induction_hub_name IS NOT NULL THEN 'ghost_warehouse'
    WHEN COALESCE(e.direct_gain, 0) < 0.4 THEN 'jumbo'
    WHEN md.actual_induction_hub_name IS NOT NULL THEN 'direct'
    ELSE 'sparse_far'
  END AS candidate_bucket
FROM enriched AS e
LEFT JOIN ghost_hubs AS g
  ON e.supplier_id = g.supplier_id
 AND e.actual_induction_hub_name = g.actual_induction_hub_name
LEFT JOIN material_direct_hubs AS md
  ON e.supplier_id = md.supplier_id
 AND e.actual_induction_hub_name = md.actual_induction_hub_name
-- WHERE e.supplier_id = 12345
-- WHERE e.is_candidate = 1
ORDER BY e.supplier_id, e.promised_delivery_end_range_date_at_order DESC, e.ops
