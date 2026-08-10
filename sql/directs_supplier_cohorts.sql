-- Directs supplier cohort analysis
--
-- Classifies DS suppliers into:
--   consistently_builds_directs  — batched true directs in (nearly) every week
--   sometimes_builds_directs     — batched true directs in some weeks only
--   ghost_warehouses_no_directs  — persistent far hubs look like directs but are
--                                  unregistered warehouses (not intentional directs)
--   no_directs                   — neither true directs nor ghost-warehouse pattern
--
-- Direct-eligible order:
--   assignedhub_notequal_actualhub_flag = 1
--   AND distance_assignedhub_customer >= 400
--   AND distance_assignedhub_actualhub >= 200
-- NOTE: Do NOT use distance_assignedhub_actualhub_200_plus — that flag is unreliable
-- (fires on near-hub pairs like SAVANNAH id 314 vs Savannah id 291 at ~9 miles).
-- Orders missing an actual induction hub are excluded from eligibility and reported
-- separately as missing_actual_hub_vol.
--
-- Local inductor gate:
--   If >=80% of volume with an actual hub is within 200mi of assigned hub, classify
--   as no_directs (residual far scans are not treated as building directs).
--
-- Batched / "same time" true-direct signal:
--   2+ direct-eligible ops at the same supplier + actual hub + induction day.
--
-- Ghost hub:
--   Far from assigned hub (>=200mi on >=80% of that hub's volume),
--   present in >=50% of supplier weeks (min 2), and >=10% of supplier volume.
-- Ghost classification takes priority over true-direct cohorts.
--
-- Two lookback windows (unioned with lookback_window column):
--   pdd_10w  — last 10 weeks by promised_delivery_end_range_date_at_order
--   msbd_2w  — last 2 weeks by msbd_su

WITH params AS (
  SELECT
    CURRENT_DATE() AS as_of,
    DATE_TRUNC(CURRENT_DATE(), WEEK(SUNDAY)) AS current_week_start
),

windows AS (
  SELECT
    'pdd_10w' AS lookback_window,
    'promised_delivery_end_range_date_at_order' AS timebase,
    10 AS lookback_weeks,
    DATE_SUB((SELECT as_of FROM params), INTERVAL 10 WEEK) AS window_start,
    (SELECT as_of FROM params) AS window_end
  UNION ALL
  SELECT
    'msbd_2w',
    'msbd_su',
    2,
    DATE_SUB((SELECT as_of FROM params), INTERVAL 2 WEEK),
    (SELECT as_of FROM params)
),

base AS (
  SELECT
    w.lookback_window,
    w.timebase,
    w.lookback_weeks,
    o.supplier_id,
    o.su_name,
    o.parent_suid,
    o.parent_su_name,
    o.sto,
    o.srm_contact,
    o.state_name,
    o.city_name,
    o.postal_code,
    o.address_1,
    o.assigned_induction_hub_id,
    o.assigned_induction_hub_name,
    o.assigned_station_zip,
    o.assigned_station_state,
    o.actual_induction_hub_id,
    o.actual_induction_hub_name,
    o.actual_induction_hub_zip,
    o.actual_induction_hub_state,
    o.destination_zipcode,
    o.destination_state,
    o.ops,
    o.direct_gain,
    o.inducted_on_time_or_early,
    o.distance_assignedhub_customer,
    o.distance_actualhub_customer,
    o.distance_assignedhub_actualhub,
    o.assignedhub_notequal_actualhub_flag,
    o.assignedstate_notequal_actualstate_flag,
    o.distance_assignedhub_customer_400_plus,
    o.distance_assignedhub_actualhub_200_plus,
    COALESCE(DATE(o.carrier_first_induction_date_time), o.induction_date_lidd) AS ind_day,
    CASE
      WHEN w.lookback_window = 'pdd_10w'
        THEN DATE_TRUNC(o.promised_delivery_end_range_date_at_order, WEEK(SUNDAY))
      ELSE DATE_TRUNC(o.msbd_su, WEEK(SUNDAY))
    END AS week_start,
    CASE
      WHEN o.actual_induction_hub_id IS NULL
        OR TRIM(CAST(o.actual_induction_hub_id AS STRING)) = '' THEN 1
      ELSE 0
    END AS missing_actual_hub,
    CASE
      WHEN o.assignedhub_notequal_actualhub_flag = 1
        AND COALESCE(o.distance_assignedhub_customer, 0) >= 400
        AND COALESCE(o.distance_assignedhub_actualhub, 0) >= 200 THEN 1
      ELSE 0
    END AS is_direct_eligible,
    CASE
      WHEN o.assignedhub_notequal_actualhub_flag = 1
        AND COALESCE(o.distance_assignedhub_actualhub, 0) >= 200 THEN 1
      ELSE 0
    END AS is_far_hub_induction,
    CASE
      WHEN o.actual_induction_hub_id IS NOT NULL
        AND TRIM(CAST(o.actual_induction_hub_id AS STRING)) != ''
        AND COALESCE(o.distance_assignedhub_actualhub, 0) < 200 THEN 1
      ELSE 0
    END AS within_200_of_assigned
  FROM `wf-gcp-us-ae-global-tnd-prod.speed_and_reliability.HVE_perf_Monitoring` AS o
  CROSS JOIN windows AS w
  WHERE o.fulfillment_type = 'DS'
    AND (
      (w.lookback_window = 'pdd_10w'
        AND o.promised_delivery_end_range_date_at_order >= w.window_start
        AND o.promised_delivery_end_range_date_at_order < w.window_end)
      OR
      (w.lookback_window = 'msbd_2w'
        AND o.msbd_su >= w.window_start
        AND o.msbd_su < w.window_end)
    )
),

hub_day AS (
  SELECT
    lookback_window,
    supplier_id,
    actual_induction_hub_name,
    ind_day,
    COUNT(DISTINCT IF(is_direct_eligible = 1, ops, NULL)) AS direct_on_day
  FROM base
  WHERE missing_actual_hub = 0
    AND is_direct_eligible = 1
    AND actual_induction_hub_name IS NOT NULL
  GROUP BY 1, 2, 3, 4
),

base_enriched AS (
  SELECT
    b.*,
    CASE
      WHEN b.is_direct_eligible = 1
        AND COALESCE(hd.direct_on_day, 0) >= 2 THEN 1
      ELSE 0
    END AS is_batched_direct
  FROM base AS b
  LEFT JOIN hub_day AS hd
    ON b.lookback_window = hd.lookback_window
   AND b.supplier_id = hd.supplier_id
   AND b.actual_induction_hub_name = hd.actual_induction_hub_name
   AND b.ind_day = hd.ind_day
),

supplier_week AS (
  SELECT
    lookback_window,
    supplier_id,
    week_start,
    COUNT(DISTINCT ops) AS week_vol,
    COUNT(DISTINCT IF(is_direct_eligible = 1, ops, NULL)) AS week_direct_eligible_vol,
    COUNT(DISTINCT IF(is_batched_direct = 1, ops, NULL)) AS week_batched_direct_vol,
    COUNT(DISTINCT IF(missing_actual_hub = 1, ops, NULL)) AS week_missing_actual_hub_vol
  FROM base_enriched
  GROUP BY 1, 2, 3
),

hub_agg AS (
  SELECT
    lookback_window,
    supplier_id,
    actual_induction_hub_name,
    actual_induction_hub_state,
    COUNT(DISTINCT week_start) AS weeks_present,
    COUNT(DISTINCT ops) AS hub_vol,
    COUNT(DISTINCT IF(is_direct_eligible = 1, ops, NULL)) AS hub_direct_vol,
    COUNT(DISTINCT IF(is_batched_direct = 1, ops, NULL)) AS hub_batched_direct_vol,
    AVG(CASE WHEN is_far_hub_induction = 1 THEN 1 ELSE 0 END) AS pct_far
  FROM base_enriched
  WHERE missing_actual_hub = 0
    AND actual_induction_hub_name IS NOT NULL
  GROUP BY 1, 2, 3, 4
),

supplier_meta AS (
  SELECT
    lookback_window,
    timebase,
    lookback_weeks,
    supplier_id,
    ANY_VALUE(su_name) AS su_name,
    ANY_VALUE(parent_suid) AS parent_suid,
    ANY_VALUE(parent_su_name) AS parent_su_name,
    ANY_VALUE(sto) AS sto,
    ANY_VALUE(srm_contact) AS srm_contact,
    ANY_VALUE(state_name) AS state_name,
    ANY_VALUE(city_name) AS city_name,
    ANY_VALUE(postal_code) AS postal_code,
    ANY_VALUE(address_1) AS address_1,
    ANY_VALUE(assigned_induction_hub_name) AS assigned_induction_hub_name,
    ANY_VALUE(assigned_station_state) AS assigned_station_state,
    ANY_VALUE(assigned_station_zip) AS assigned_station_zip,
    COUNT(DISTINCT ops) AS total_vol,
    COUNT(DISTINCT week_start) AS weeks_with_vol,
    COUNT(DISTINCT IF(is_direct_eligible = 1, ops, NULL)) AS direct_eligible_vol,
    COUNT(DISTINCT IF(is_batched_direct = 1, ops, NULL)) AS batched_direct_vol,
    COUNT(DISTINCT IF(missing_actual_hub = 1, ops, NULL)) AS missing_actual_hub_vol,
    COUNT(DISTINCT IF(assignedhub_notequal_actualhub_flag = 1, ops, NULL)) AS hub_mismatch_vol,
    COUNT(DISTINCT IF(assignedstate_notequal_actualstate_flag = 1, ops, NULL)) AS state_mismatch_vol,
    COUNT(DISTINCT IF(is_far_hub_induction = 1, ops, NULL)) AS far_hub_vol,
    COUNT(DISTINCT IF(missing_actual_hub = 0, ops, NULL)) AS vol_with_actual_hub,
    COUNT(DISTINCT IF(within_200_of_assigned = 1, ops, NULL)) AS within_200_vol,
    AVG(direct_gain) AS avg_direct_gain,
    AVG(IF(is_direct_eligible = 1, direct_gain, NULL)) AS avg_gain_on_direct_eligible,
    AVG(distance_assignedhub_customer) AS avg_dist_assignedhub_customer,
    AVG(distance_actualhub_customer) AS avg_dist_actualhub_customer,
    AVG(distance_assignedhub_actualhub) AS avg_dist_assignedhub_actualhub,
    AVG(inducted_on_time_or_early) AS ifr
  FROM base_enriched
  GROUP BY lookback_window, timebase, lookback_weeks, supplier_id
),

ghost_hubs AS (
  SELECT
    h.lookback_window,
    h.supplier_id,
    h.actual_induction_hub_name,
    h.actual_induction_hub_state,
    h.hub_vol,
    h.hub_direct_vol,
    h.hub_batched_direct_vol,
    h.weeks_present,
    SAFE_DIVIDE(h.hub_vol, m.total_vol) AS hub_share
  FROM hub_agg AS h
  JOIN supplier_meta AS m
    USING (lookback_window, supplier_id)
  WHERE h.pct_far >= 0.8
    AND h.weeks_present >= GREATEST(
      2,
      CAST(CEIL(0.5 * m.weeks_with_vol) AS INT64)
    )
    AND SAFE_DIVIDE(h.hub_vol, m.total_vol) >= 0.10
),

ghost_supplier AS (
  SELECT
    lookback_window,
    supplier_id,
    COUNT(*) AS n_ghost_hubs,
    SUM(hub_vol) AS ghost_hub_vol,
    SUM(hub_direct_vol) AS ghost_direct_vol,
    SUM(hub_batched_direct_vol) AS ghost_batched_direct_vol,
    STRING_AGG(
      CONCAT(
        actual_induction_hub_name,
        ' (', actual_induction_hub_state, ') ',
        CAST(ROUND(100 * hub_share) AS STRING), '%'
      ),
      '; '
      ORDER BY hub_vol DESC
      LIMIT 5
    ) AS ghost_hubs
  FROM ghost_hubs
  GROUP BY 1, 2
),

true_direct_week AS (
  SELECT
    b.lookback_window,
    b.supplier_id,
    b.week_start,
    COUNT(DISTINCT b.ops) AS true_direct_vol,
    ANY_VALUE(sw.week_vol) AS week_vol
  FROM base_enriched AS b
  JOIN supplier_week AS sw
    USING (lookback_window, supplier_id, week_start)
  LEFT JOIN ghost_hubs AS g
    ON b.lookback_window = g.lookback_window
   AND b.supplier_id = g.supplier_id
   AND b.actual_induction_hub_name = g.actual_induction_hub_name
  WHERE b.is_batched_direct = 1
    AND g.actual_induction_hub_name IS NULL
  GROUP BY 1, 2, 3
),

true_direct_supplier AS (
  SELECT
    lookback_window,
    supplier_id,
    SUM(true_direct_vol) AS true_direct_vol,
    COUNTIF(true_direct_vol >= 1) AS weeks_with_true_direct,
    STRING_AGG(
      CONCAT(CAST(week_start AS STRING), ': ', CAST(true_direct_vol AS STRING)),
      '; '
      ORDER BY week_start
    ) AS true_direct_by_week
  FROM true_direct_week
  GROUP BY 1, 2
),

top_true_direct_hubs AS (
  SELECT
    b.lookback_window,
    b.supplier_id,
    STRING_AGG(
      hub_label, '; ' ORDER BY hub_vol DESC LIMIT 5
    ) AS top_true_direct_hubs
  FROM (
    SELECT
      b.lookback_window,
      b.supplier_id,
      CONCAT(
        b.actual_induction_hub_name,
        ' (', b.actual_induction_hub_state, ') ',
        CAST(COUNT(DISTINCT b.ops) AS STRING)
      ) AS hub_label,
      COUNT(DISTINCT b.ops) AS hub_vol
    FROM base_enriched AS b
    LEFT JOIN ghost_hubs AS g
      ON b.lookback_window = g.lookback_window
     AND b.supplier_id = g.supplier_id
     AND b.actual_induction_hub_name = g.actual_induction_hub_name
    WHERE b.is_batched_direct = 1
      AND g.actual_induction_hub_name IS NULL
      AND b.actual_induction_hub_name IS NOT NULL
    GROUP BY 1, 2, b.actual_induction_hub_name, b.actual_induction_hub_state
  ) AS b
  GROUP BY 1, 2
),

classified AS (
  SELECT
    m.lookback_window,
    m.timebase,
    m.lookback_weeks,
    m.supplier_id,
    m.su_name,
    m.parent_suid,
    m.parent_su_name,
    m.sto,
    m.srm_contact,
    m.state_name,
    m.city_name,
    m.postal_code,
    m.address_1,
    m.assigned_induction_hub_name,
    m.assigned_station_state,
    m.assigned_station_zip,
    m.total_vol,
    m.weeks_with_vol,
    m.direct_eligible_vol,
    SAFE_DIVIDE(m.direct_eligible_vol, m.total_vol) AS direct_eligible_share,
    m.batched_direct_vol,
    COALESCE(t.true_direct_vol, 0) AS true_direct_vol,
    COALESCE(t.weeks_with_true_direct, 0) AS weeks_with_true_direct,
    SAFE_DIVIDE(COALESCE(t.weeks_with_true_direct, 0), m.weeks_with_vol) AS pct_weeks_with_true_direct,
    t.true_direct_by_week,
    th.top_true_direct_hubs,
    COALESCE(g.n_ghost_hubs, 0) AS n_ghost_hubs,
    COALESCE(g.ghost_hub_vol, 0) AS ghost_hub_vol,
    SAFE_DIVIDE(COALESCE(g.ghost_hub_vol, 0), m.total_vol) AS ghost_share,
    COALESCE(g.ghost_direct_vol, 0) AS ghost_direct_vol,
    g.ghost_hubs,
    m.missing_actual_hub_vol,
    SAFE_DIVIDE(m.missing_actual_hub_vol, m.total_vol) AS missing_actual_hub_share,
    m.hub_mismatch_vol,
    m.state_mismatch_vol,
    m.far_hub_vol,
    m.within_200_vol,
    SAFE_DIVIDE(m.within_200_vol, m.vol_with_actual_hub) AS pct_within_200_of_assigned,
    m.avg_direct_gain,
    m.avg_gain_on_direct_eligible,
    m.avg_dist_assignedhub_customer,
    m.avg_dist_actualhub_customer,
    m.avg_dist_assignedhub_actualhub,
    m.ifr,
    CASE
      WHEN COALESCE(g.ghost_hub_vol, 0) > 0 THEN 'ghost_warehouses_no_directs'
      -- Local inductors: majority of volume within 200mi of assigned hub
      WHEN SAFE_DIVIDE(m.within_200_vol, m.vol_with_actual_hub) >= 0.80 THEN 'no_directs'
      WHEN COALESCE(t.weeks_with_true_direct, 0) >= m.weeks_with_vol
        OR (
          m.weeks_with_vol >= 4
          AND COALESCE(t.weeks_with_true_direct, 0) >= m.weeks_with_vol - 1
        )
        OR (
          -- Short window: both weeks with true directs = consistent
          m.lookback_weeks <= 2
          AND m.weeks_with_vol >= 2
          AND COALESCE(t.weeks_with_true_direct, 0) = m.weeks_with_vol
        )
        THEN 'consistently_builds_directs'
      WHEN COALESCE(t.weeks_with_true_direct, 0) >= 1 THEN 'sometimes_builds_directs'
      ELSE 'no_directs'
    END AS direct_cohort
  FROM supplier_meta AS m
  LEFT JOIN ghost_supplier AS g
    USING (lookback_window, supplier_id)
  LEFT JOIN true_direct_supplier AS t
    USING (lookback_window, supplier_id)
  LEFT JOIN top_true_direct_hubs AS th
    USING (lookback_window, supplier_id)
  WHERE m.total_vol >= CASE
    WHEN m.lookback_window = 'pdd_10w' THEN 50
    ELSE 20
  END
)

SELECT *
FROM classified
ORDER BY lookback_window, direct_cohort, total_vol DESC
