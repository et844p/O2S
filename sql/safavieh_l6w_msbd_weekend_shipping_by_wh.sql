-- Safavieh — L6W MSBD weekend shipping by warehouse (matches weekend_shipping table logic)
-- Fri/Sat placed: order_dow IN (5, 6) · Weekend induct: induction_dow_adj IN (1, 7)

SELECT
  supplier_id,
  su_name,
  TRIM(city_name) AS city_name,
  state_name,
  COUNT(DISTINCT ops) AS msbd_vol,
  COUNT(DISTINCT CASE WHEN order_dow IN (5, 6) THEN ops END) AS fri_sat_vol,
  COUNT(DISTINCT CASE WHEN order_dow IN (5, 6) AND induction_dow_adj IN (1, 7) THEN ops END) AS fri_sat_weekend_shipped,
  ROUND(
    SAFE_DIVIDE(
      COUNT(DISTINCT CASE WHEN order_dow IN (5, 6) AND induction_dow_adj IN (1, 7) THEN ops END),
      COUNT(DISTINCT CASE WHEN order_dow IN (5, 6) THEN ops END)
    ),
    4
  ) AS pct_fri_sat_weekend_ship
FROM `wf-gcp-us-ae-global-tnd-prod.speed_and_reliability.HVE_perf_Monitoring`
WHERE msbd_su >= DATE_SUB(CURRENT_DATE(), INTERVAL 6 WEEK)
  AND msbd_su < CURRENT_DATE()
  AND parent_su_name = 'Safavieh'
  AND fulfillment_type = 'DS'
  AND sto = 'Rugs'
GROUP BY supplier_id, su_name, city_name, state_name
HAVING fri_sat_vol >= 100
ORDER BY fri_sat_vol DESC
