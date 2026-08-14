-- Wrong lead-time (LT) monitor
--
-- Flags DS orders (US/CA) from yesterday where the ledger base lead time
-- does not match the expected Bulk or Product LT setting.
--
-- Filters:
--   order_complete_date = CURRENT_DATE() - 1
--   fulfillment_type = 'DS'
--   destination_country_id IN (1, 2)
--
-- Output grain: one row per mismatched OPID (order product).
-- Issue key used by the Python monitor:
--   supplierid | Supplierpartid | ship_class_group | su_lt_type

WITH m AS (
  SELECT
    s.SuID AS ChildSuID,
    s.SuName,
    s.SuCutOff,
    CASE WHEN s.SuParentSuID IS NULL THEN s.SuID ELSE s.SuParentSuID END AS ParentSuID,
    CASE
      WHEN se.SuInventoryFeedLevel = 2 THEN s.SuID
      ELSE CASE WHEN s.SuParentSuID IS NULL THEN s.SuID ELSE s.SuParentSuID END
    END AS Mas_SuID,
    CASE WHEN se.SuInventoryFeedLevel = 2 THEN 'Child' ELSE 'Parent' END AS InventoryFeedLevel
  FROM `wf-gcp-us-ae-sql-data-prod.csn_order.tbl_supplier_ext` se
  LEFT JOIN `wf-gcp-us-ae-sql-data-prod.csn_order.tbl_supplier` s
    ON se.SuID = s.SuID
),

lt AS (
  SELECT
    lts.SuID,
    CASE
      WHEN SuAllowLeadTimeBulkUpdates = FALSE THEN 'Product LT'
      WHEN SuSmallParcelLeadTimeBulkValue IS NOT NULL THEN 'Bulk LT'
      WHEN SuLargeParcelLeadTimeBulkValue IS NOT NULL THEN 'Bulk LT'
      ELSE 'Product LT'
    END AS SU_LT_Type,
    SuSmallParcelLeadTimeBulkValue AS SP_LT,
    SuLargeParcelLeadTimeBulkValue AS LP_LT
  FROM `wf-gcp-us-ae-bulk-prod.csn_order.tbl_supplier_lead_time_settings` lts
),

partid AS (
  SELECT DISTINCT
    p.SupplierID,
    p.SupplierPartNumber,
    x.Supplierpartid,
    p.SupplierLeadTime,
    p.HardwarePackLeadTime,
    p.ReplacementPartLeadTime
  FROM `wf-gcp-us-ae-sql-data-prod.csn_product.tbl_supplier_part` p
  LEFT JOIN (
    SELECT DISTINCT
      SupplierID,
      ShipViaID,
      SupplierPartID,
      SupplierPartNumber,
      PrSKU,
      BclgID
    FROM `wf-gcp-us-ae-merch-prod.analytics_merch_processing.tbl_shipvia_mix_discrepancies_report_pivot_data`
    WHERE SnapshotDate = (
      SELECT MAX(SnapshotDate)
      FROM `wf-gcp-us-ae-merch-prod.analytics_merch_processing.tbl_shipvia_mix_discrepancies_report_pivot_data`
    )
  ) x
    ON x.SupplierID = p.SupplierID
   AND p.SupplierPartNumber = x.SupplierPartNumber
),

base AS (
  SELECT DISTINCT
    odl.supplierid,
    odl.suname,
    odl.opid,
    odl.ponum,
    odl.order_complete_date,
    odl.supplier_must_ship_by_date,
    odl.ship_class_group,
    l.leadtimedetails.baseleadtime * 24 AS actual_lt,
    lt.su_lt_type,
    lt.sp_lt,
    lt.lp_lt,
    p.SupplierPartNumber,
    p.Supplierpartid,
    p.supplierleadtime AS partleadtime,
    CASE
      WHEN su_lt_type = 'Bulk LT' AND ship_class_group = 'Small Parcel'
        THEN CAST(sp_lt AS STRING)
      WHEN su_lt_type = 'Bulk LT' AND ship_class_group = 'Large Parcel'
        THEN CAST(lp_lt AS STRING)
      WHEN su_lt_type = 'Product LT'
        THEN CAST(p.supplierleadtime AS STRING)
      ELSE 'not found'
    END AS expected_lt,
    CASE
      WHEN su_lt_type = 'Bulk LT'
        AND ship_class_group = 'Small Parcel'
        AND sp_lt <> l.leadtimedetails.baseleadtime * 24 THEN 1
      WHEN su_lt_type = 'Bulk LT'
        AND ship_class_group = 'Large Parcel'
        AND lp_lt <> l.leadtimedetails.baseleadtime * 24 THEN 1
      WHEN su_lt_type = 'Product LT'
        AND p.supplierleadtime <> l.leadtimedetails.baseleadtime * 24 THEN 1
      ELSE 0
    END AS wrong_lt_flag
  FROM `wf-gcp-us-ae-gbl-prf-mgmt-prod.reporting.tbl_global_o2s_data_layer` odl
  LEFT JOIN `wf-gcp-us-ae-fopt-prod.fulfillment_optimization.dataform_ledger_estimation_details` l
    ON l.orderproductid = odl.opid
   AND l.customermilestone = 'LastBasket'
  LEFT JOIN m
    ON m.childsuid = odl.supplierid
  LEFT JOIN lt
    ON lt.suid = m.mas_suid
  LEFT JOIN partid p
    ON p.SupplierID = odl.ParentSuID
   AND p.Supplierpartid = odl.SupplierPartID
  WHERE odl.order_complete_date = CURRENT_DATE() - 1
    AND fulfillment_type = 'DS'
    AND destination_country_id IN (1, 2)
)

SELECT *
FROM base
WHERE wrong_lt_flag = 1
ORDER BY supplierid, Supplierpartid, opid
