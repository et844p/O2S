-- Safavieh June MSBD — Fri/Sat placed: % weekend shipping (actual induction)
-- order_dow IN (5, 6) = Fri/Sat placed (ISO order_dow)
-- induction_dow_adj IN (1, 7) = Sun/Sat inducted (Sun=1, Sat=7)

SELECT
  supplier_id,
  su_name,
  TRIM(city_name) AS city_name,
  state_name,
  COUNT(DISTINCT ops) AS fri_sat_vol,
  COUNT(DISTINCT CASE WHEN induction_dow_adj = 1 THEN ops END) AS fri_sat_induct_sunday,
  COUNT(DISTINCT CASE WHEN induction_dow_adj = 7 THEN ops END) AS fri_sat_induct_saturday,
  COUNT(DISTINCT CASE WHEN induction_dow_adj IN (1, 7) THEN ops END) AS fri_sat_induct_weekend,
  ROUND(
    COUNT(DISTINCT CASE WHEN induction_dow_adj IN (1, 7) THEN ops END)
    / COUNT(DISTINCT ops),
    4
  ) AS pct_fri_sat_weekend_ship,
  ROUND(
    COUNT(DISTINCT CASE WHEN induction_dow_adj = 1 THEN ops END)
    / COUNT(DISTINCT ops),
    4
  ) AS pct_fri_sat_induct_sunday
FROM `wf-gcp-us-ae-global-tnd-prod.speed_and_reliability.HVE_perf_Monitoring`
WHERE msbd_su BETWEEN '2026-06-01' AND '2026-06-30'
  AND parent_su_name = 'Safavieh'
  AND fulfillment_type = 'DS'
  AND sto = 'Rugs'
  AND order_dow IN (5, 6)
GROUP BY supplier_id, su_name, city_name, state_name
HAVING fri_sat_vol >= 50
ORDER BY fri_sat_vol DESC
