-- Safavieh June MSBD warehouse analysis
-- Base: msbd_su in June 2026
-- Same-day induction before 2pm: toolkit_hourly_performance (less_14_o2i_0 logic)
-- Mas_SuID from supplier ext feed-level logic

WITH massuid AS (
  SELECT
    s.SuID AS ChildSuID,
    s.SuName,
    s.SuCutOff,
    CASE WHEN s.SuParentSuID IS NULL THEN s.SuID ELSE SuParentSuID END AS ParentSuID,
    CASE
      WHEN SuInventoryFeedLevel = 2 THEN s.SuID
      ELSE CASE WHEN s.SuParentSuID IS NULL THEN s.SuID ELSE SuParentSuID END
    END AS Mas_SuID,
    CASE WHEN SuInventoryFeedLevel = 2 THEN 'Child' ELSE 'Parent' END AS InventoryFeedLevel
  FROM `wf-gcp-us-ae-sql-data-prod.csn_order.tbl_supplier_ext` se
  LEFT JOIN `wf-gcp-us-ae-sql-data-prod.csn_order.tbl_supplier` s ON se.SuID = s.SuID
),

safavieh_suppliers AS (
  SELECT DISTINCT supplier_id
  FROM `wf-gcp-us-ae-global-tnd-prod.speed_and_reliability.HVE_perf_Monitoring`
  WHERE parent_su_name = 'Safavieh'
    AND fulfillment_type = 'DS'
),

june_msbd AS (
  SELECT
    h.supplier_id,
    h.su_name,
    h.parent_suid,
    h.parent_su_name,
    h.sto,
    h.srm_contact,
    CASE WHEN h.sp_lt IS NULL THEN 'PL' ELSE CAST(h.sp_lt AS STRING) END AS LT,
    h.cutoff AS Cutoff,
    h.city_name,
    h.state_name,
    COUNT(DISTINCT h.ops) AS june_msbd_vol,
    AVG(h.inducted_on_time_or_early) AS june_IFR,
    AVG(h.o2d_stated_5) AS june_fast_badge,
    AVG(h.o2I_0_adj) AS june_o2i_0_adj,
    AVG(h.o2label_0_adj) AS june_o2label_0_adj,
    AVG(h.label2I_0_adj) AS june_label2i_0_adj
  FROM `wf-gcp-us-ae-global-tnd-prod.speed_and_reliability.HVE_perf_Monitoring` h
  INNER JOIN safavieh_suppliers ss ON ss.supplier_id = h.supplier_id
  WHERE h.msbd_su BETWEEN '2026-06-01' AND '2026-06-30'
    AND h.fulfillment_type = 'DS'
    AND h.sto = 'Rugs'
  GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10
),

weekdays AS (
  SELECT
    t.supplierid,
    SUM(CASE WHEN t.order_hour_supplier_local <= 14 THEN t.o2i_0 END)
      / COUNT(CASE WHEN t.order_hour_supplier_local <= 14 THEN t.opid END) AS less_14_o2i_0,
    COUNT(CASE WHEN t.order_hour_supplier_local <= 14 THEN t.opid END) AS orders_before_2pm
  FROM `wf-gcp-us-ae-global-tnd-prod.speed_and_reliability.toolkit_hourly_performance` t
  INNER JOIN safavieh_suppliers ss ON ss.supplier_id = t.supplierid
  WHERE t.order_dow_supplier_local NOT IN (1, 7)
    AND t.ship_class_group = 'Small Parcel'
    AND t.order_complete_date BETWEEN '2026-06-01' AND '2026-06-30'
    AND CAST(t.opid AS STRING) NOT LIKE '8%'
  GROUP BY 1
)

SELECT
  m.Mas_SuID,
  j.supplier_id,
  j.su_name,
  j.city_name,
  j.state_name,
  j.LT,
  j.Cutoff,
  j.june_msbd_vol,
  ROUND(j.june_IFR, 4) AS june_IFR,
  ROUND(j.june_fast_badge, 4) AS june_fast_badge,
  ROUND(j.june_o2i_0_adj, 4) AS june_o2i_0_adj,
  ROUND(j.june_o2label_0_adj, 4) AS june_o2label_0_adj,
  ROUND(j.june_label2i_0_adj, 4) AS june_label2i_0_adj,
  ROUND(cu.less_14_o2i_0, 4) AS pct_same_day_induct_before_2pm,
  cu.orders_before_2pm
FROM june_msbd j
LEFT JOIN weekdays cu ON cu.supplierid = j.supplier_id
LEFT JOIN massuid m ON m.ChildSuID = j.supplier_id
ORDER BY j.june_msbd_vol DESC
