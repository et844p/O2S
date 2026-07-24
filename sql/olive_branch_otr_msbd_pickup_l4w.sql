-- Olive Branch OTR: MSBD vs pickup dates (last 4 weeks)
-- Warehouse: Flash Furniture MS 38654

SELECT
  supplier_must_ship_by_date AS msbd,
  FORMAT_DATE('%a', supplier_must_ship_by_date) AS msbd_dow,
  COUNT(DISTINCT ponum) AS po_count,
  MAX(plannedtrucks) AS planned_trucks,
  MAX(executedtrucks) AS executed_trucks,
  MAX(TotalOutstandingPOs) AS backlog_on_msbd,
  COUNTIF(pu_on_MSBD = 1) AS picked_up_on_msbd,
  COUNTIF(fm_ship_date IS NOT NULL) AS has_pickup,
  COUNTIF(fm_ship_date IS NULL AND Load_Depart_Date IS NULL) AS no_pickup_yet,
  MIN(fm_ship_date) AS earliest_pickup_fm_ship,
  MAX(fm_ship_date) AS latest_pickup_fm_ship,
  MIN(Load_Depart_Date) AS earliest_load_depart,
  MAX(Load_Depart_Date) AS latest_load_depart,
  COUNTIF(rfpd IS NOT NULL) AS has_rfpd,
  COUNTIF(rfpd_early_ontime_SU = 1) AS rfpd_on_msbd
FROM `wf-gcp-us-ae-global-tnd-prod.speed_and_reliability.OTR_Tracking_ET`
WHERE SuName = 'Flash Furniture MS 38654'
  AND supplier_must_ship_by_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 4 WEEK)
GROUP BY 1, 2
ORDER BY msbd
