SELECT
  supplier_id,
  su_name,
  parent_su_name,
  sto,
  srm,
  sp_lt,
  enable_week,
  wave,
  ROUND(pre6w_weekend_msbd_rate, 4) AS pre6w_weekend_msbd_rate,
  pre6w_fri_sat_vol
FROM enabled_suppliers
ORDER BY enable_week, pre6w_fri_sat_vol DESC
