-- JLA Home Savannah (SV2 + SV3) order-level analysis — July 2026 MSBD
-- SV2 = conveyables (supplier_id 35069)
-- SV3 = non-conveyables (supplier_id 10983)

SELECT
  supplier_id,
  su_name,
  parent_su_name,
  city_name,
  state_name,
  postal_code,
  address_1,
  StationName,
  sto,
  ProductCategory,
  srm_contact,
  ops,
  purchase_order_number,
  tracking_number,
  order_complete_date,
  order_complete_date_time_local,
  order_dow,
  msbd_su,
  msbd_su_week,
  msbd_cu,
  induction_date_lidd,
  induction_dow_adj,
  carrier_first_induction_date_time,
  fulfillment_ship_date_time,
  event_datetime,
  sp_lt,
  order_lt,
  cushion,
  OrderCapacityPadDays,
  cutoff,
  o2s_actual,
  o2sumsbd,
  inducted_on_time_or_early,
  inducted_early,
  inducted_late,
  inducted_over_weekend,
  not_inducted_but_late_already,
  not_inducted_not_late_yet,
  one_day_late,
  two_day_late,
  three_five_day_inducted_late,
  three_days_plus_late,
  label_by_msbd_7,
  label_by_msbd_2,
  o2label_0_adj,
  o2label_1_adj,
  label2I_0_adj,
  label2I_1_adj,
  label2I_2_adj,
  o2I_0_adj,
  o2I_1_adj,
  o2I_2_adj,
  assigned_induction_hub_name,
  actual_induction_hub_name,
  assignedhub_notequal_actualhub_flag,
  destination_state,
  delivery_date,
  fulfillment_type,
  delivery_rel,
  -- Derived fields for warehouse vs FedEx attribution
  DATE(PARSE_DATETIME('%Y-%m-%d %H:%M:%S', event_datetime)) AS label_date,
  EXTRACT(HOUR FROM PARSE_DATETIME('%Y-%m-%d %H:%M:%S', event_datetime)) AS label_hour_et,
  CASE
    WHEN supplier_id = 35069 THEN 'SV2 (conveyables)'
    WHEN supplier_id = 10983 THEN 'SV3 (non-conveyables)'
  END AS warehouse,
  CASE
    WHEN inducted_on_time_or_early = 1 THEN 'On time'
    WHEN label_by_msbd_2 = 0 THEN 'WH: label after 2pm MSBD'
    WHEN label2I_1_adj = 1 THEN 'FedEx: label on time, inducted next day'
    WHEN COALESCE(label2I_1_adj, 0) = 0 AND COALESCE(label2I_0_adj, 0) = 0 THEN 'FedEx: label on time, inducted 2+ days'
    WHEN label2I_0_adj = 1 THEN 'FedEx: label on time, same-day induct but late MSBD'
    ELSE 'Other late'
  END AS delay_attribution
FROM `wf-gcp-us-ae-global-tnd-prod.speed_and_reliability.HVE_perf_Monitoring`
WHERE msbd_su >= '2026-07-01'
  AND msbd_su < '2026-08-01'
  AND fulfillment_type = 'DS'
  AND supplier_id IN (35069, 10983)
ORDER BY msbd_su DESC, supplier_id, ops
