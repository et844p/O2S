-- Enabled-supplier order extract for pre/post weekend MSBD impact
-- Prepend sql/weekend_shipping_pre_post_cte.sql
--
-- Same calendar cuts for Wave 1 and Wave 2 (MSBD timebase):
--   Pre:  msbd_su 2026-05-31 .. 2026-06-27
--   Post: msbd_su 2026-08-02 .. 2026-08-29
-- US delivered only: destination_country_id = 1, delivery_date IS NOT NULL
-- (country 2 = CA / northbound; det_del_rel is near-zero there)

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
  h.det_delivery_date,
  h.det_del_rel,
  DATE_DIFF(h.det_delivery_date, h.order_complete_date, DAY) AS det_o2d,
  h.inducted_on_time_or_early,
  h.destination_country_id,
  CASE
    WHEN h.msbd_su >= DATE '2026-05-31' AND h.msbd_su <= DATE '2026-06-27' THEN 'pre'
    WHEN h.msbd_su >= DATE '2026-08-02' AND h.msbd_su <= DATE '2026-08-29' THEN 'post'
  END AS period,
  CASE
    WHEN h.order_dow IN (6, 7) THEN 'fri_sat'
    WHEN h.order_dow IN (2, 3, 4, 5) THEN 'weekday'
    WHEN h.order_dow = 1 THEN 'sunday'
  END AS order_bucket,
  DATE_TRUNC(h.msbd_su, WEEK(SUNDAY)) AS week_start,
  DATE_DIFF(
    DATE_TRUNC(h.msbd_su, WEEK(SUNDAY)),
    e.enable_week,
    WEEK
  ) AS weeks_from_enable
FROM `wf-gcp-us-ae-global-tnd-prod.speed_and_reliability.HVE_perf_Monitoring` AS h
INNER JOIN enabled_suppliers AS e
  ON e.supplier_id = h.supplier_id
WHERE h.fulfillment_type = 'DS'
  AND h.sp_lt = 24
  AND h.destination_country_id = 1
  AND h.delivery_date IS NOT NULL
  AND h.order_dow BETWEEN 1 AND 7
  AND (
    (h.msbd_su >= DATE '2026-05-31' AND h.msbd_su <= DATE '2026-06-27')
    OR (h.msbd_su >= DATE '2026-08-02' AND h.msbd_su <= DATE '2026-08-29')
  )
