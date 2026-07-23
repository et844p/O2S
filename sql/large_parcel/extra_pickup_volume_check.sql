-- Extra pickup volume check for a supplier.
-- Replace {supplier_name} with a case-insensitive name fragment (e.g. "Flash Furniture").
-- Answers: open PO volume, po/pu, planned pickups this week, and whether an extra pickup is justified.

WITH supplier_match AS (
  SELECT DISTINCT
    ChildSuID,
    SuName,
    ParentSuName,
    laneid,
    LaneName,
    po_pu
  FROM `wf-gcp-us-ae-global-tnd-prod.speed_and_reliability.OTR_Tracking_ET`
  WHERE LOWER(SuName) LIKE LOWER('%{supplier_name}%')
     OR LOWER(ParentSuName) LIKE LOWER('%{supplier_name}%')
),
supplier_profile AS (
  SELECT
    ANY_VALUE(ParentSuName) AS supplier_name,
    ARRAY_AGG(DISTINCT ChildSuID IGNORE NULLS) AS child_suids,
    ANY_VALUE(LaneName) AS lane_name,
    ANY_VALUE(laneid) AS lane_id,
    MAX(po_pu) AS po_pu
  FROM supplier_match
  WHERE laneid IS NOT NULL
),
open_pos AS (
  SELECT
    COUNT(DISTINCT o.full_ponum) AS open_po_count,
    COUNT(DISTINCT IF(o.not_inducted_not_late_yet = 1, o.full_ponum, NULL)) AS open_not_late_yet,
    COUNT(DISTINCT IF(o.not_inducted_but_late_already = 1, o.full_ponum, NULL)) AS open_already_late
  FROM `wf-gcp-us-ae-global-tnd-prod.speed_and_reliability.OTR_Tracking_ET` o
  JOIN supplier_match sm ON o.ChildSuID = sm.ChildSuID
  WHERE o.carrier_first_induction_date_time IS NULL
),
week_plan AS (
  SELECT
    SUM(COALESCE(p.plannedtrucks, 0)) AS planned_pickups_this_week,
    SUM(COALESCE(p.executedtrucks, 0)) AS executed_pickups_this_week,
    STRING_AGG(
      DISTINCT IF(COALESCE(p.plannedtrucks, 0) > 0, FORMAT_DATE('%A', p.day), NULL),
      ', '
      ORDER BY IF(COALESCE(p.plannedtrucks, 0) > 0, FORMAT_DATE('%A', p.day), NULL)
    ) AS planned_pickup_days
  FROM `wf-gcp-us-ae-global-tnd-prod.tnd_reporting.FM_LP_FTL_Variance` p
  JOIN supplier_profile sp ON p.laneid = sp.lane_id
  WHERE DATE_TRUNC(p.week, WEEK(MONDAY)) = DATE_TRUNC(CURRENT_DATE(), WEEK(MONDAY))
)
SELECT
  sp.supplier_name,
  sp.child_suids,
  sp.lane_name,
  sp.lane_id,
  sp.po_pu,
  op.open_po_count,
  op.open_not_late_yet,
  op.open_already_late,
  wp.planned_pickups_this_week,
  wp.executed_pickups_this_week,
  wp.planned_pickup_days,
  DATE_TRUNC(CURRENT_DATE(), WEEK(MONDAY)) AS week_start,
  ROUND(SAFE_DIVIDE(op.open_po_count, sp.po_pu), 2) AS pickups_needed_by_open_volume,
  ROUND(SAFE_DIVIDE(op.open_po_count, sp.po_pu), 0) AS pickups_needed_rounded,
  CASE
    WHEN SAFE_DIVIDE(op.open_po_count, sp.po_pu) > wp.planned_pickups_this_week
      THEN 'Yes — open volume exceeds planned pickup capacity'
    WHEN op.open_po_count >= sp.po_pu
      THEN 'Yes — enough open POs for at least one pickup'
    ELSE 'No — open volume is below one pickup threshold'
  END AS extra_pickup_recommendation
FROM supplier_profile sp
CROSS JOIN open_pos op
CROSS JOIN week_plan wp;
