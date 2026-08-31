-- Enabled-supplier order extract for pre/post weekend MSBD impact
-- Prepend sql/weekend_shipping_pre_post_cte.sql

SELECT
  e.supplier_id,
  e.su_name,
  e.parent_su_name,
  e.sto,
  e.srm,
  e.enable_week,
  e.wave,
  h.ops,
  h.order_complete_date,
  h.order_dow,
  h.msbd_su,
  h.induction_dow_adj,
  h.o2d_stated,
  h.o2d_actual,
  h.o2s_actual,
  h.o2sumsbd,
  h.o2s_stated_1,
  h.o2d_stated_5,
  h.o2d_actual_5,
  h.delivery_rel,
  h.delivery_date,
  h.inducted_on_time_or_early,
  CASE
    WHEN h.order_complete_date >= DATE_SUB(e.enable_week, INTERVAL 6 WEEK)
     AND h.order_complete_date < e.enable_week THEN 'pre'
    WHEN h.order_complete_date >= e.enable_week
     AND h.order_complete_date < DATE '2026-08-17' THEN 'post'
  END AS period,
  CASE
    WHEN h.order_dow IN (6, 7) THEN 'fri_sat'
    WHEN h.order_dow IN (2, 3, 4, 5) THEN 'weekday'
    WHEN h.order_dow = 1 THEN 'sunday'
  END AS order_bucket,
  DATE_TRUNC(h.order_complete_date, WEEK(SUNDAY)) AS week_start,
  DATE_DIFF(
    DATE_TRUNC(h.order_complete_date, WEEK(SUNDAY)),
    e.enable_week,
    WEEK
  ) AS weeks_from_enable
FROM `wf-gcp-us-ae-global-tnd-prod.speed_and_reliability.HVE_perf_Monitoring` AS h
INNER JOIN enabled_suppliers AS e
  ON e.supplier_id = h.supplier_id
WHERE h.fulfillment_type = 'DS'
  AND h.sp_lt = 24
  AND h.order_complete_date >= DATE_SUB(e.enable_week, INTERVAL 6 WEEK)
  AND h.order_complete_date < DATE '2026-08-17'
  AND h.order_dow BETWEEN 1 AND 7
