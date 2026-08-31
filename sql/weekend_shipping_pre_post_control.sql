-- 24hr DS control: never hit 10% Fri/Sat weekend MSBD on/after 2026-06-21
-- Same MSBD calendar cuts as enabled cohorts; US delivered only.

WITH control_ids AS (
  SELECT supplier_id
  FROM `wf-gcp-us-ae-global-tnd-prod.speed_and_reliability.HVE_perf_Monitoring`
  WHERE fulfillment_type = 'DS'
    AND sp_lt = 24
    AND destination_country_id = 1
    AND delivery_date IS NOT NULL
    AND order_dow IN (6, 7)
    AND (
      (msbd_su >= DATE '2026-05-31' AND msbd_su <= DATE '2026-06-27')
      OR (msbd_su >= DATE '2026-08-02' AND msbd_su <= DATE '2026-08-29')
    )
  GROUP BY supplier_id
  HAVING COUNT(DISTINCT IF(
      msbd_su >= DATE '2026-06-21'
      AND EXTRACT(DAYOFWEEK FROM msbd_su) IN (1, 7),
      ops,
      NULL
    )) = 0
    AND COUNT(DISTINCT IF(msbd_su >= DATE '2026-05-31'
      AND msbd_su <= DATE '2026-06-27', ops, NULL)) >= 50
    AND COUNT(DISTINCT IF(msbd_su >= DATE '2026-08-02'
      AND msbd_su <= DATE '2026-08-29', ops, NULL)) >= 50
)

SELECT
  CASE
    WHEN h.msbd_su >= DATE '2026-05-31' AND h.msbd_su <= DATE '2026-06-27' THEN 'pre'
    WHEN h.msbd_su >= DATE '2026-08-02' AND h.msbd_su <= DATE '2026-08-29' THEN 'post'
  END AS period,
  CASE
    WHEN h.order_dow IN (6, 7) THEN 'fri_sat'
    WHEN h.order_dow IN (2, 3, 4, 5) THEN 'weekday'
    WHEN h.order_dow = 1 THEN 'sunday'
  END AS order_bucket,
  COUNT(DISTINCT h.supplier_id) AS n_suppliers,
  COUNT(DISTINCT h.ops) AS vol,
  SAFE_DIVIDE(
    COUNT(DISTINCT IF(EXTRACT(DAYOFWEEK FROM h.msbd_su) IN (1, 7), h.ops, NULL)),
    COUNT(DISTINCT h.ops)
  ) AS weekend_msbd,
  SAFE_DIVIDE(
    COUNT(DISTINCT IF(h.induction_dow_adj IN (1, 7), h.ops, NULL)),
    COUNT(DISTINCT h.ops)
  ) AS weekend_ship_adj,
  SAFE_DIVIDE(
    COUNT(DISTINCT IF(h.induction_dow_adj = 7, h.ops, NULL)),
    COUNT(DISTINCT h.ops)
  ) AS sat_ship_adj,
  SAFE_DIVIDE(
    COUNT(DISTINCT IF(h.induction_dow_adj = 1, h.ops, NULL)),
    COUNT(DISTINCT h.ops)
  ) AS sun_ship_adj,
  AVG(h.inducted_on_time_or_early) AS ifr,
  AVG(h.o2sumsbd) AS o2s_stated,
  AVG(h.o2s_stated_1) AS o2s_stated_1,
  AVG(h.o2d_stated) AS o2d_stated,
  AVG(h.o2d_actual) AS o2d_actual,
  AVG(h.o2s_actual) AS o2s_actual,
  AVG(h.o2d_stated_5) AS fast_badge,
  AVG(h.o2d_actual_5) AS o2d_actual_less5,
  AVG(h.delivery_rel) AS del_rel,
  AVG(DATE_DIFF(h.det_delivery_date, h.order_complete_date, DAY)) AS det_o2d,
  AVG(h.det_del_rel) AS det_del_rel
FROM `wf-gcp-us-ae-global-tnd-prod.speed_and_reliability.HVE_perf_Monitoring` AS h
INNER JOIN control_ids AS c
  ON c.supplier_id = h.supplier_id
WHERE h.fulfillment_type = 'DS'
  AND h.sp_lt = 24
  AND h.destination_country_id = 1
  AND h.delivery_date IS NOT NULL
  AND h.order_dow BETWEEN 1 AND 7
  AND (
    (h.msbd_su >= DATE '2026-05-31' AND h.msbd_su <= DATE '2026-06-27')
    OR (h.msbd_su >= DATE '2026-08-02' AND h.msbd_su <= DATE '2026-08-29')
  )
GROUP BY period, order_bucket
ORDER BY order_bucket, period
