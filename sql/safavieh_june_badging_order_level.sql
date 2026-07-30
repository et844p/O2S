-- Safavieh June MSBD — order-level badging simulation (stacked chart source)
-- Stacked chart layers (mutually exclusive slices to full policy+weekend stack):
--   current → weekend (Fri/Sat −1 vs current, +9 pp at 3d) → cutoff additional (+8.7 pp) → full stack
-- sim_fri_sat_minus1 = o2d_stated − Fri/Sat weekend adj only
-- sim_policy         = o2d_stated − cushion − weekday 2pm cutoff extension
-- sim_full           = sim_policy − Fri/Sat weekend adj (full stack)

WITH base AS (
  SELECT
    h.ops,
    h.purchase_order_number,
    h.supplier_id,
    h.su_name,
    TRIM(h.city_name) AS city_name,
    h.state_name,
    h.order_complete_date,
    h.msbd_su,
    h.order_dow,
    h.o2d_stated,
    h.cushion,
    h.inducted_on_time_or_early
  FROM `wf-gcp-us-ae-global-tnd-prod.speed_and_reliability.HVE_perf_Monitoring` h
  WHERE h.msbd_su BETWEEN '2026-06-01' AND '2026-06-30'
    AND h.parent_su_name = 'Safavieh'
    AND h.fulfillment_type = 'DS'
    AND h.sto = 'Rugs'
    AND h.o2d_stated IS NOT NULL
),

toolkit AS (
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

scored AS (
  SELECT
    b.*,
    CASE WHEN b.order_dow IN (5, 6) THEN 1 ELSE 0 END AS is_fri_sat_placed,
    CASE WHEN b.cushion > 0 THEN 1 ELSE 0 END AS adj_cushion,
    CASE
      WHEN b.order_dow IN (1, 2, 3, 4, 5)
        AND t.is_before_cutoff = 0
        AND t.order_hour_supplier_local <= 14
      THEN 1
      ELSE 0
    END AS adj_2pm_cutoff,
    CASE WHEN b.order_dow IN (5, 6) THEN 1 ELSE 0 END AS adj_weekend,
    t.is_before_cutoff,
    t.order_hour_supplier_local,
    b.o2d_stated AS sim_current,
    b.o2d_stated
      - CASE WHEN b.cushion > 0 THEN 1 ELSE 0 END
      - CASE
          WHEN b.order_dow IN (1, 2, 3, 4, 5)
            AND t.is_before_cutoff = 0
            AND t.order_hour_supplier_local <= 14
          THEN 1
          ELSE 0
        END AS sim_policy,
    b.o2d_stated
      - CASE WHEN b.cushion > 0 THEN 1 ELSE 0 END
      - CASE
          WHEN b.order_dow IN (1, 2, 3, 4, 5)
            AND t.is_before_cutoff = 0
            AND t.order_hour_supplier_local <= 14
          THEN 1
          ELSE 0
        END
      - CASE WHEN b.order_dow IN (5, 6) THEN 1 ELSE 0 END AS sim_full,
    b.o2d_stated - CASE WHEN b.order_dow IN (5, 6) THEN 1 ELSE 0 END AS sim_fri_sat_minus1
  FROM base b
  LEFT JOIN toolkit t ON b.ops = t.ops
)

SELECT
  ops,
  purchase_order_number,
  supplier_id,
  su_name,
  city_name,
  state_name,
  order_complete_date,
  msbd_su,
  order_dow,
  is_fri_sat_placed,
  o2d_stated,
  cushion,
  is_before_cutoff,
  order_hour_supplier_local,
  adj_cushion,
  adj_2pm_cutoff,
  adj_weekend,
  sim_current,
  sim_fri_sat_minus1,
  sim_policy,
  sim_full,
  inducted_on_time_or_early,
  -- current badges
  CASE WHEN sim_current <= 1 THEN 1 ELSE 0 END AS badge_current_1d,
  CASE WHEN sim_current <= 2 THEN 1 ELSE 0 END AS badge_current_2d,
  CASE WHEN sim_current <= 3 THEN 1 ELSE 0 END AS badge_current_3d,
  CASE WHEN sim_current <= 5 THEN 1 ELSE 0 END AS badge_current_fast,
  -- after cutoff policy (cushion + 2pm)
  CASE WHEN sim_policy <= 1 THEN 1 ELSE 0 END AS badge_policy_1d,
  CASE WHEN sim_policy <= 2 THEN 1 ELSE 0 END AS badge_policy_2d,
  CASE WHEN sim_policy <= 3 THEN 1 ELSE 0 END AS badge_policy_3d,
  CASE WHEN sim_policy <= 5 THEN 1 ELSE 0 END AS badge_policy_fast,
  -- full stack (+ weekend Fri/Sat −1)
  CASE WHEN sim_full <= 1 THEN 1 ELSE 0 END AS badge_full_1d,
  CASE WHEN sim_full <= 2 THEN 1 ELSE 0 END AS badge_full_2d,
  CASE WHEN sim_full <= 3 THEN 1 ELSE 0 END AS badge_full_3d,
  CASE WHEN sim_full <= 5 THEN 1 ELSE 0 END AS badge_full_fast,
  -- stacked chart slices (exclusive, sum with current to full stack %)
  CASE WHEN sim_current > 1 AND sim_fri_sat_minus1 <= 1 THEN 1 ELSE 0 END AS new_from_weekend_vs_current_1d,
  CASE WHEN sim_current > 2 AND sim_fri_sat_minus1 <= 2 THEN 1 ELSE 0 END AS new_from_weekend_vs_current_2d,
  CASE WHEN sim_current > 3 AND sim_fri_sat_minus1 <= 3 THEN 1 ELSE 0 END AS new_from_weekend_vs_current_3d,
  CASE WHEN sim_current > 5 AND sim_fri_sat_minus1 <= 5 THEN 1 ELSE 0 END AS new_from_weekend_vs_current_fast,
  CASE WHEN sim_current > 1 AND sim_full <= 1 AND sim_fri_sat_minus1 > 1 THEN 1 ELSE 0 END AS new_from_cutoff_additional_1d,
  CASE WHEN sim_current > 2 AND sim_full <= 2 AND sim_fri_sat_minus1 > 2 THEN 1 ELSE 0 END AS new_from_cutoff_additional_2d,
  CASE WHEN sim_current > 3 AND sim_full <= 3 AND sim_fri_sat_minus1 > 3 THEN 1 ELSE 0 END AS new_from_cutoff_additional_3d,
  CASE WHEN sim_current > 5 AND sim_full <= 5 AND sim_fri_sat_minus1 > 5 THEN 1 ELSE 0 END AS new_from_cutoff_additional_fast,
  -- legacy: cutoff-only then weekend-incremental (old stacked chart decomposition)
  CASE WHEN sim_current > 1 AND sim_policy <= 1 THEN 1 ELSE 0 END AS new_from_cutoff_1d,
  CASE WHEN sim_current > 2 AND sim_policy <= 2 THEN 1 ELSE 0 END AS new_from_cutoff_2d,
  CASE WHEN sim_current > 3 AND sim_policy <= 3 THEN 1 ELSE 0 END AS new_from_cutoff_3d,
  CASE WHEN sim_current > 5 AND sim_policy <= 5 THEN 1 ELSE 0 END AS new_from_cutoff_fast,
  CASE WHEN sim_policy > 1 AND sim_full <= 1 THEN 1 ELSE 0 END AS new_from_weekend_after_policy_1d,
  CASE WHEN sim_policy > 2 AND sim_full <= 2 THEN 1 ELSE 0 END AS new_from_weekend_after_policy_2d,
  CASE WHEN sim_policy > 3 AND sim_full <= 3 THEN 1 ELSE 0 END AS new_from_weekend_after_policy_3d,
  CASE WHEN sim_policy > 5 AND sim_full <= 5 THEN 1 ELSE 0 END AS new_from_weekend_after_policy_fast
FROM scored
ORDER BY supplier_id, ops
