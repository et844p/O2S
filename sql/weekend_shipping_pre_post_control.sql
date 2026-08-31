-- 24hr DS control: never hit 10% Fri/Sat weekend MSBD on/after 2026-06-21
-- Calendar windows aligned to Wave 1 (pre: 5/03–6/21, post: 7/05–8/17)

WITH control_ids AS (
  SELECT supplier_id
  FROM `wf-gcp-us-ae-global-tnd-prod.speed_and_reliability.HVE_perf_Monitoring`
  WHERE fulfillment_type = 'DS'
    AND sp_lt = 24
    AND order_dow IN (6, 7)
    AND order_complete_date >= DATE '2026-05-03'
    AND order_complete_date < DATE '2026-08-17'
  GROUP BY supplier_id
  HAVING COUNT(DISTINCT IF(
      order_complete_date >= DATE '2026-06-21'
      AND EXTRACT(DAYOFWEEK FROM msbd_su) IN (1, 7),
      ops,
      NULL
    )) = 0
    AND COUNT(DISTINCT IF(order_complete_date >= DATE '2026-05-03'
      AND order_complete_date < DATE '2026-06-21', ops, NULL)) >= 50
    AND COUNT(DISTINCT IF(order_complete_date >= DATE '2026-07-05'
      AND order_complete_date < DATE '2026-08-17', ops, NULL)) >= 50
)

SELECT
  CASE
    WHEN h.order_complete_date >= DATE '2026-05-03'
     AND h.order_complete_date < DATE '2026-06-21' THEN 'pre'
    WHEN h.order_complete_date >= DATE '2026-07-05'
     AND h.order_complete_date < DATE '2026-08-17' THEN 'post'
  END AS period,
  CASE
    WHEN h.order_dow IN (6, 7) THEN 'fri_sat'
    WHEN h.order_dow IN (2, 3, 4, 5) THEN 'weekday'
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
  AVG(h.o2d_actual_5) AS actual_o2d_le_5,
  AVG(IF(h.delivery_date IS NOT NULL, h.delivery_rel, NULL)) AS del_rel
FROM `wf-gcp-us-ae-global-tnd-prod.speed_and_reliability.HVE_perf_Monitoring` AS h
INNER JOIN control_ids AS c
  ON c.supplier_id = h.supplier_id
WHERE h.fulfillment_type = 'DS'
  AND h.sp_lt = 24
  AND h.order_dow IN (2, 3, 4, 5, 6, 7)
  AND (
    (h.order_complete_date >= DATE '2026-05-03' AND h.order_complete_date < DATE '2026-06-21')
    OR (h.order_complete_date >= DATE '2026-07-05' AND h.order_complete_date < DATE '2026-08-17')
  )
GROUP BY period, order_bucket
ORDER BY order_bucket, period
