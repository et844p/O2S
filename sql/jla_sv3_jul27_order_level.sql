-- JLA SV3 order-level export — MSBD 2026-07-27
-- Joins exclusions (ops = customer_order_line_item) for B2B flag
-- Milestone join on purchase_order_number for ASN / induction timestamps

SELECT
  h.supplier_id,
  h.su_name,
  h.ops,
  h.purchase_order_number,
  h.tracking_number,
  h.assigned_induction_hub_id,
  h.actual_induction_hub_id,
  h.order_complete_date_time_local,
  h.msbd_su,
  h.event_datetime AS label,
  h.label_by_msbd_2,
  h.label_by_msbd_7,
  h.has_relabel,
  h.fulfillment_ship_date_time,
  h.carrier_first_induction_date_time,
  h.inducted_on_time_or_early,
  h.label_by_msbd_2 AS label_by_msbd_2_1,
  h.SU_FR,
  CASE
    WHEN h.one_day_late = 1
      AND EXTRACT(HOUR FROM h.carrier_first_induction_date_time) >= 8
      AND EXTRACT(HOUR FROM h.carrier_first_induction_date_time) < 16
    THEN 1 ELSE 0
  END AS one_day_late_between8_and4,
  CASE
    WHEN h.one_day_late = 1
      AND EXTRACT(HOUR FROM h.carrier_first_induction_date_time) >= 16
    THEN 1 ELSE 0
  END AS one_day_late_between4_and8,
  h.SKU AS sku,
  h.supplierpartid,
  h.supplierpartnumber,
  -- Warehouse WMS fields (Picked/Trailer) not in BQ — left null to match Excel layout
  CAST(NULL AS DATETIME) AS Picked_Date,
  m.loaded_onto_trailer_datetime_local AS Load_Date,
  CAST(NULL AS STRING) AS Trailer_No,
  CAST(NULL AS DATETIME) AS Trailer_Complete_Date,
  CAST(NULL AS DATETIME) AS Trailer_Pickup_Date,
  m.asn_ship_datetime_local AS ASN_Sent_Date,
  m.carrier_first_induction_datetime_local AS First_Scan_Date,
  h.delivery_date AS DeliveryDate,
  CASE
    WHEN m.loaded_onto_trailer_datetime_local IS NOT NULL
      AND DATE(m.loaded_onto_trailer_datetime_local) = h.msbd_su
    THEN 1 ELSE 0
  END AS loaded_on_correct_day,
  CASE
    WHEN m.loaded_onto_trailer_datetime_local IS NOT NULL
      AND m.carrier_first_induction_datetime_local IS NOT NULL
      AND DATE(m.carrier_first_induction_datetime_local) <= DATE(m.loaded_onto_trailer_datetime_local)
    THEN 1
    WHEN m.loaded_onto_trailer_datetime_local IS NOT NULL
      AND m.carrier_first_induction_datetime_local IS NULL
    THEN 1
    ELSE 0
  END AS no_delay_in_induction,
  COALESCE(e.is_b2b_customer_order, 0) AS is_b2b_customer_order,
  COALESCE(h.isB2BOrder, 0) AS isB2BOrder_hve,
  CASE WHEN COALESCE(e.is_b2b_customer_order, h.isB2BOrder, 0) = 1 THEN 1 ELSE 0 END AS is_b2b_flag,
  e.sales_channel,
  e.is_order_item_in_standard_exclusion
FROM `wf-gcp-us-ae-global-tnd-prod.speed_and_reliability.HVE_perf_Monitoring` h
LEFT JOIN `wf-gcp-us-ae-gat-prod.ops_reporting_core.tbl_exclusions_standard_line_item` e
  ON h.ops = e.customer_order_line_item
LEFT JOIN `wf-gcp-us-ae-gat-prod.ops_reporting_core.tbl_dim_purchase_order_milestone` m
  ON h.purchase_order_number = m.purchase_order_number
WHERE h.msbd_su = '2026-07-27'
  AND h.fulfillment_type = 'DS'
  AND h.supplier_id = 10983
ORDER BY h.ops
