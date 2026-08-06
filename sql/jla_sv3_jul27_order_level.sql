-- JLA SV3 order-level export — MSBD 2026-07-27
-- HVE columns unchanged; adds is_b2b_flag from exclusions join (ops = customer_order_line_item)

SELECT
  h.*,
  CASE WHEN COALESCE(e.is_b2b_customer_order, 0) = 1 THEN 1 ELSE 0 END AS is_b2b_flag
FROM `wf-gcp-us-ae-global-tnd-prod.speed_and_reliability.HVE_perf_Monitoring` h
LEFT JOIN `wf-gcp-us-ae-gat-prod.ops_reporting_core.tbl_exclusions_standard_line_item` e
  ON h.ops = e.customer_order_line_item
WHERE h.msbd_su = '2026-07-27'
  AND h.fulfillment_type = 'DS'
  AND h.supplier_id = 10983
ORDER BY h.ops
