-- Large Parcel first-mile add/cancel recommendations for the current week.
--
-- Source of truth: `wf-gcp-us-ae-global-tnd-prod.tnd_planning.fm_msod_dropnew`
-- (live MSOD feed behind FM_LP_WDN_Add_Cancel_Sheet Combined!A:K).
--
-- Week: Monday-start DATE_TRUNC(CURRENT_DATE(), WEEK(MONDAY)).
-- Actionable recs: Recommendation != 0 and ExceptionType is not 'No Add/Cancel'.
-- Add / Cancel map to Combined tab columns; Recommendation is capacity-capped.

SELECT
  laneid AS LaneID,
  LaneName AS SuName,
  PoolPoint,
  Day AS PlannedDate,
  Week,
  RoutingType,
  ExceptionType,
  LoadsPlanned AS PlannedPickups,
  CASE WHEN Recommendation > 0 THEN Recommendation ELSE 0 END AS Add,
  CASE WHEN Recommendation < 0 THEN ABS(Recommendation) ELSE 0 END AS Cancel,
  Recommendation AS NetRecommendation,
  UncappedRecommendation,
  AddsNeeded,
  CancelsNeeded,
  PO_PU,
  TotalOutstandingPOs,
  CurrentDayOutstandingPOs,
  ROUND(LoadsNeeded, 2) AS LoadsNeeded,
  RoundedLoadsNeeded,
  ROUND(LoadVariance, 2) AS LoadVariance,
  RoundedLoadVariance,
  LeadTime,
  TodayFlag,
  TomorrowFlag,
  LastRefreshed
FROM `wf-gcp-us-ae-global-tnd-prod.tnd_planning.fm_msod_dropnew`
WHERE Week = DATE_TRUNC(CURRENT_DATE(), WEEK(MONDAY))
  AND (ExceptionType IS NULL OR ExceptionType != 'No Add/Cancel')
  AND Recommendation IS NOT NULL
  AND Recommendation != 0
ORDER BY PlannedDate, PoolPoint, LaneName
