-- Safavieh June MSBD — supplier-level before-2pm same-day induction + badging cohorts
-- Before-2pm: toolkit less_14_o2i_0 (Mon–Fri placed, hour ≤ 14, o2i_0 same-day induction)
-- Badging cohorts: % of June MSBD vol with sim o2d_stated ≤ 1 / 2 / 3 / 5 days

WITH base AS (
  SELECT
    h.supplier_id,
    h.su_name,
    h.ops,
    h.o2d_stated,
    h.cushion,
    h.order_dow
  FROM `wf-gcp-us-ae-global-tnd-prod.speed_and_reliability.HVE_perf_Monitoring` h
  WHERE h.msbd_su BETWEEN '2026-06-01' AND '2026-06-30'
    AND h.parent_su_name = 'Safavieh'
    AND h.fulfillment_type = 'DS'
    AND h.sto = 'Rugs'
    AND h.o2d_stated IS NOT NULL
),

toolkit_cutoff AS (
  SELECT
    CAST(opid AS INT64) AS ops,
    MAX(IsBeforeCutoff) AS is_before_cutoff,
    MAX(order_hour_supplier_local) AS order_hour_supplier_local
  FROM `wf-gcp-us-ae-global-tnd-prod.speed_and_reliability.toolkit_hourly_performance`
  WHERE order_complete_date BETWEEN '2026-06-01' AND '2026-06-30'
    AND ship_class_group = 'Small Parcel'
    AND CAST(opid AS STRING) NOT LIKE '8%'
  GROUP BY 1
),

toolkit_before_2pm AS (
  SELECT
    t.supplierid,
    SUM(CASE WHEN t.order_hour_supplier_local <= 14 THEN t.o2i_0 END)
      / COUNT(CASE WHEN t.order_hour_supplier_local <= 14 THEN t.opid END) AS pct_same_day_before_2pm,
    COUNT(CASE WHEN t.order_hour_supplier_local <= 14 THEN t.opid END) AS orders_before_2pm
  FROM `wf-gcp-us-ae-global-tnd-prod.speed_and_reliability.toolkit_hourly_performance` t
  WHERE t.order_dow_supplier_local NOT IN (1, 7)
    AND t.ship_class_group = 'Small Parcel'
    AND t.order_complete_date BETWEEN '2026-06-01' AND '2026-06-30'
    AND CAST(t.opid AS STRING) NOT LIKE '8%'
    AND t.supplierid IN (SELECT DISTINCT supplier_id FROM base)
  GROUP BY 1
),

scored AS (
  SELECT
    b.supplier_id,
    b.su_name,
    b.ops,
    b.order_dow,
    b.o2d_stated AS sim_current,
    b.o2d_stated - CASE WHEN b.order_dow IN (5, 6) THEN 1 ELSE 0 END AS sim_fri_sat_minus1,
    b.o2d_stated
      - CASE WHEN b.cushion > 0 THEN 1 ELSE 0 END
      - CASE
          WHEN b.order_dow IN (1, 2, 3, 4, 5)
            AND tc.is_before_cutoff = 0
            AND tc.order_hour_supplier_local <= 14
          THEN 1
          ELSE 0
        END
      - CASE WHEN b.order_dow IN (5, 6) THEN 1 ELSE 0 END AS sim_full
  FROM base b
  LEFT JOIN toolkit_cutoff tc ON b.ops = tc.ops
),

by_supplier AS (
  SELECT
    supplier_id,
    su_name,
    COUNT(DISTINCT ops) AS june_msbd_vol,
    COUNT(DISTINCT CASE WHEN order_dow IN (5, 6) THEN ops END) AS fri_sat_vol,
    ROUND(AVG(CASE WHEN sim_current <= 1 THEN 1 ELSE 0 END) * 100, 2) AS current_badge_1d_pct,
    ROUND(AVG(CASE WHEN sim_current <= 2 THEN 1 ELSE 0 END) * 100, 2) AS current_badge_2d_pct,
    ROUND(AVG(CASE WHEN sim_current <= 3 THEN 1 ELSE 0 END) * 100, 2) AS current_badge_3d_pct,
    ROUND(AVG(CASE WHEN sim_current <= 5 THEN 1 ELSE 0 END) * 100, 2) AS current_badge_fast_pct,
    ROUND(AVG(CASE WHEN sim_fri_sat_minus1 <= 1 THEN 1 ELSE 0 END) * 100, 2) AS fri_sat_minus1_badge_1d_pct,
    ROUND(AVG(CASE WHEN sim_fri_sat_minus1 <= 2 THEN 1 ELSE 0 END) * 100, 2) AS fri_sat_minus1_badge_2d_pct,
    ROUND(AVG(CASE WHEN sim_fri_sat_minus1 <= 3 THEN 1 ELSE 0 END) * 100, 2) AS fri_sat_minus1_badge_3d_pct,
    ROUND(AVG(CASE WHEN sim_fri_sat_minus1 <= 5 THEN 1 ELSE 0 END) * 100, 2) AS fri_sat_minus1_badge_fast_pct,
    ROUND((AVG(CASE WHEN sim_fri_sat_minus1 <= 1 THEN 1 ELSE 0 END)
      - AVG(CASE WHEN sim_current <= 1 THEN 1 ELSE 0 END)) * 100, 2) AS lift_1d_pp,
    ROUND((AVG(CASE WHEN sim_fri_sat_minus1 <= 2 THEN 1 ELSE 0 END)
      - AVG(CASE WHEN sim_current <= 2 THEN 1 ELSE 0 END)) * 100, 2) AS lift_2d_pp,
    ROUND((AVG(CASE WHEN sim_fri_sat_minus1 <= 3 THEN 1 ELSE 0 END)
      - AVG(CASE WHEN sim_current <= 3 THEN 1 ELSE 0 END)) * 100, 2) AS lift_3d_pp,
    ROUND((AVG(CASE WHEN sim_fri_sat_minus1 <= 5 THEN 1 ELSE 0 END)
      - AVG(CASE WHEN sim_current <= 5 THEN 1 ELSE 0 END)) * 100, 2) AS lift_fast_pp,
    COUNT(DISTINCT CASE WHEN sim_current > 3 AND sim_fri_sat_minus1 <= 3 THEN ops END) AS new_3d_orders,
    ROUND(AVG(CASE WHEN sim_full <= 1 THEN 1 ELSE 0 END) * 100, 2) AS sim_badge_1d_pct,
    ROUND(AVG(CASE WHEN sim_full <= 2 THEN 1 ELSE 0 END) * 100, 2) AS sim_badge_2d_pct,
    ROUND(AVG(CASE WHEN sim_full <= 3 THEN 1 ELSE 0 END) * 100, 2) AS sim_badge_3d_pct,
    ROUND(AVG(CASE WHEN sim_full <= 5 THEN 1 ELSE 0 END) * 100, 2) AS sim_badge_fast_pct
  FROM scored
  GROUP BY supplier_id, su_name
)

SELECT
  s.supplier_id,
  s.su_name,
  s.june_msbd_vol,
  s.fri_sat_vol,
  ROUND(t.pct_same_day_before_2pm * 100, 2) AS pct_same_day_ship_before_2pm,
  t.orders_before_2pm,
  s.current_badge_1d_pct,
  s.current_badge_2d_pct,
  s.current_badge_3d_pct,
  s.current_badge_fast_pct,
  s.fri_sat_minus1_badge_1d_pct,
  s.fri_sat_minus1_badge_2d_pct,
  s.fri_sat_minus1_badge_3d_pct,
  s.fri_sat_minus1_badge_fast_pct,
  s.lift_1d_pp,
  s.lift_2d_pp,
  s.lift_3d_pp,
  s.lift_fast_pp,
  s.new_3d_orders,
  s.sim_badge_1d_pct,
  s.sim_badge_2d_pct,
  s.sim_badge_3d_pct,
  s.sim_badge_fast_pct
FROM by_supplier s
LEFT JOIN toolkit_before_2pm t ON t.supplierid = s.supplier_id
ORDER BY s.june_msbd_vol DESC
