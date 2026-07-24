-- Flash Furniture large-parcel order-level analysis (past 3 months)
-- Routing-aware pickup metrics:
--   Live Load Pooled -> rfpd_early_ontime_SU_new (RFPD on-time)
--   OTR             -> OTR_Tracking_ET pu_on_before_MSBD / pu_on_MSBD + truck execution

WITH lp AS (
  SELECT
    ChildSuID,
    suname,
    parentsuid,
    parentsuname,
    sto,
    SupplierMarketingCategoryName,
    SRMContact,
    Routingtype,
    PP,
    RFPD_Type,
    LP_LT,
    baseleadtime,
    LP_Cutoff,
    opid,
    ponum,
    full_ponum,
    order_complete_date,
    order_dow,
    supplier_must_ship_by_date,
    msbd_week,
    registration,
    registration_date,
    rfpd_new,
    rfpd,
    fm_ship_date,
    carrier_first_induction_date_time,
    induction_date,
    fulfillment_ship_date_time,
    o2s_stated,
    o2ship,
    o2rfpd,
    o2rfpd_bus,
    registration2rfpd,
    rfpd_available,
    rfpd_early_ontime_SU_new,
    pu_on_MSBD,
    pu_on_before_MSBD,
    pu_onrfpd_new,
    pu_withinSLA_new,
    inducted_on_time_or_early,
    GAT_O2I_reliability_SLA,
    inducted_late,
    not_inducted_but_late_already,
    not_inducted_not_late_yet,
    delivery_reliability,
    o2d_stated,
    promised_o2d_7,
    delivery_date,
    ThirdPartyCarrierName,
    plannedtrucks,
    executedtrucks,
    TotalOutstandingPOs,
    po_pu,
    assigned_pp_LB,
    actual_pp_SC,
    actual_hdo_SC,
    LaneName,
    ordercapacitypaddays,
    datespecificpaddays,
    dayofweekpaddays,
    OTR_Target_SUs
  FROM `wf-gcp-us-ae-global-tnd-prod.speed_and_reliability.LP_dash_ET`
  WHERE parentsuname = 'Flash Furniture'
    AND supplier_must_ship_by_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 3 MONTH)
),
otr AS (
  SELECT
    ChildSuID,
    ponum,
    supplier_must_ship_by_date,
    pu_on_MSBD AS otr_pu_on_msbd,
    pu_on_before_MSBD AS otr_pu_on_or_before_msbd,
    pu_on_rfpd AS otr_pu_on_rfpd,
    pu_on_before_rfpd AS otr_pu_on_or_before_rfpd,
    PU_within_SLA AS otr_pu_within_sla,
    rfpd_early_ontime_SU AS otr_rfpd_ontime,
    inducted_on_time_or_early AS otr_ifr,
    plannedtrucks AS otr_planned_trucks,
    executedtrucks AS otr_executed_trucks,
    TotalOutstandingPOs AS otr_outstanding_pos,
    po_pu AS otr_po_per_truck,
    Load_Depart_Date AS otr_load_depart_date,
    Load_Depart_DateTime AS otr_load_depart_datetime,
    week_bucket AS otr_week_bucket,
    carrier_unload_ontime AS otr_carrier_unload_ontime
  FROM `wf-gcp-us-ae-global-tnd-prod.speed_and_reliability.OTR_Tracking_ET`
  WHERE ParentSuName = 'Flash Furniture'
    AND supplier_must_ship_by_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 3 MONTH)
)
SELECT
  lp.*,
  otr.otr_pu_on_msbd,
  otr.otr_pu_on_or_before_msbd,
  otr.otr_pu_on_rfpd,
  otr.otr_pu_on_or_before_rfpd,
  otr.otr_pu_within_sla,
  otr.otr_rfpd_ontime,
  otr.otr_ifr,
  otr.otr_planned_trucks,
  otr.otr_executed_trucks,
  otr.otr_outstanding_pos,
  otr.otr_po_per_truck,
  otr.otr_load_depart_date,
  otr.otr_load_depart_datetime,
  otr.otr_week_bucket,
  otr.otr_carrier_unload_ontime,
  CASE
    WHEN lp.Routingtype = 'Live Load Pooled' THEN lp.rfpd_early_ontime_SU_new
    WHEN lp.Routingtype = 'OTR' THEN otr.otr_pu_on_or_before_msbd
    ELSE lp.pu_withinSLA_new
  END AS pickup_on_time,
  CASE
    WHEN lp.Routingtype = 'Live Load Pooled' THEN 'RFPD on-time (Live Load)'
    WHEN lp.Routingtype = 'OTR' THEN 'Pickup on/before MSBD (OTR)'
    ELSE 'Pickup within SLA'
  END AS pickup_metric_type,
  CASE
    WHEN lp.Routingtype = 'OTR'
      AND otr.otr_executed_trucks IS NOT NULL
      AND otr.otr_planned_trucks > 0
    THEN SAFE_DIVIDE(otr.otr_executed_trucks, otr.otr_planned_trucks)
  END AS otr_truck_efficiency
FROM lp
LEFT JOIN otr
  ON lp.ChildSuID = otr.ChildSuID
  AND lp.ponum = otr.ponum
  AND lp.supplier_must_ship_by_date = otr.supplier_must_ship_by_date
ORDER BY lp.supplier_must_ship_by_date DESC, lp.ChildSuID, lp.opid
