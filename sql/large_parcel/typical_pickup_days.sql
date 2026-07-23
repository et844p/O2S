-- Typical pickup days for a supplier based on FM planned trucks.
-- Replace {supplier_name} with a case-insensitive name fragment (e.g. "Polywood").
-- Default lookback: 12 weeks.

WITH supplier_match AS (
  SELECT DISTINCT
    laneid,
    LaneName,
    ParentSuName
  FROM `wf-gcp-us-ae-global-tnd-prod.speed_and_reliability.OTR_Tracking_ET`
  WHERE (
    LOWER(SuName) LIKE LOWER('%{supplier_name}%')
    OR LOWER(ParentSuName) LIKE LOWER('%{supplier_name}%')
  )
  AND laneid IS NOT NULL
),
history AS (
  SELECT
    ANY_VALUE(sm.ParentSuName) AS supplier_name,
    p.day,
    EXTRACT(DAYOFWEEK FROM p.day) AS dow_num,
    FORMAT_DATE('%A', p.day) AS day_name,
    SUM(COALESCE(p.plannedtrucks, 0)) AS planned_trucks
  FROM `wf-gcp-us-ae-global-tnd-prod.tnd_reporting.FM_LP_FTL_Variance` p
  JOIN supplier_match sm ON p.laneid = sm.laneid
  WHERE p.day BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 12 WEEK) AND CURRENT_DATE()
  GROUP BY p.day, dow_num, day_name
)
SELECT
  ANY_VALUE(supplier_name) AS supplier_name,
  day_name,
  dow_num,
  COUNTIF(planned_trucks > 0) AS weeks_with_pickup,
  ROUND(AVG(IF(planned_trucks > 0, planned_trucks, NULL)), 2) AS avg_trucks_when_scheduled,
  MAX(planned_trucks) AS max_trucks,
  CASE
    WHEN COUNTIF(planned_trucks > 0) >= 8 THEN 'Typical'
    WHEN COUNTIF(planned_trucks > 0) >= 3 THEN 'Occasional'
    ELSE 'Rare'
  END AS pickup_frequency
FROM history
GROUP BY day_name, dow_num
ORDER BY dow_num;
