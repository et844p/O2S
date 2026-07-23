-- Planned and executed pickups for a supplier in the current week.
-- Replace {supplier_name} with a case-insensitive name fragment (e.g. "Fusion Furniture").

WITH supplier_match AS (
  SELECT DISTINCT
    ChildSuID,
    SuName,
    ParentSuName,
    laneid,
    LaneName
  FROM `wf-gcp-us-ae-global-tnd-prod.speed_and_reliability.OTR_Tracking_ET`
  WHERE LOWER(SuName) LIKE LOWER('%{supplier_name}%')
     OR LOWER(ParentSuName) LIKE LOWER('%{supplier_name}%')
),
lanes AS (
  SELECT DISTINCT
    laneid,
    ANY_VALUE(LaneName) AS lane_name
  FROM supplier_match
  WHERE laneid IS NOT NULL
  GROUP BY laneid
),
daily AS (
  SELECT
    ANY_VALUE(sm.ParentSuName) AS supplier_name,
    l.laneid,
    l.lane_name,
    p.day,
    FORMAT_DATE('%A', p.day) AS day_name,
    SUM(COALESCE(p.plannedtrucks, 0)) AS planned_pickups,
    SUM(COALESCE(p.executedtrucks, 0)) AS executed_pickups
  FROM lanes l
  JOIN supplier_match sm ON sm.laneid = l.laneid
  JOIN `wf-gcp-us-ae-global-tnd-prod.tnd_reporting.FM_LP_FTL_Variance` p
    ON p.laneid = l.laneid
  WHERE DATE_TRUNC(p.week, WEEK(MONDAY)) = DATE_TRUNC(CURRENT_DATE(), WEEK(MONDAY))
  GROUP BY l.laneid, l.lane_name, p.day
)
SELECT
  supplier_name,
  DATE_TRUNC(CURRENT_DATE(), WEEK(MONDAY)) AS week_start,
  SUM(planned_pickups) AS planned_pickups_this_week,
  SUM(executed_pickups) AS executed_pickups_this_week,
  STRING_AGG(
    DISTINCT IF(planned_pickups > 0, day_name, NULL),
    ', '
    ORDER BY IF(planned_pickups > 0, day_name, NULL)
  ) AS pickup_days,
  ARRAY_AGG(
    STRUCT(day, day_name, planned_pickups, executed_pickups)
    ORDER BY day
  ) AS daily_breakdown
FROM daily
GROUP BY supplier_name;
