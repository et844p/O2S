-- Directs supplier cohort analysis
--
-- Flow:
--   1) CANDIDATE = wrong hub
--                  AND distance_assignedhub_customer >= 400
--                  AND distance_assignedhub_actualhub >= 200
--      (raw distances; do NOT trust distance_assignedhub_actualhub_200_plus)
--
--   2) Partition every candidate into exactly one bucket (priority order):
--        misshipping     — parent has another WH in the induction state
--        ghost_warehouse — persistent far hub (>=10% supplier vol, most weeks)
--                          with scattered induction timing (avg <2 candidate
--                          ops/day at that hub — not batchy)
--        jumbo           — direct_gain < 0.4 (null treated as < 0.4)
--        direct          — everything else (gain >= 0.4, not misshipping/ghost)
--
--   candidate_vol = misshipping + ghost + jumbo + direct
--
-- Parent warehouse states = distinct state_name of all DS SUIDs under parent_suid.
--
-- Supplier cohorts (priority):
--   ghost_warehouses
--   consistently_builds_directs / sometimes_builds_directs  (from direct)
--   misshipping
--   no_directs
--
-- Windows: pdd_10w (promised delivery) and msbd_2w (msbd_su)

WITH params AS (
  SELECT CURRENT_DATE() AS as_of
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

parent_states AS (
  SELECT DISTINCT
    w.lookback_window,
    o.parent_suid,
    o.state_name AS warehouse_state
  FROM `wf-gcp-us-ae-global-tnd-prod.speed_and_reliability.HVE_perf_Monitoring` AS o
  CROSS JOIN windows AS w
  WHERE o.fulfillment_type = 'DS'
    AND o.parent_suid IS NOT NULL
    AND o.state_name IS NOT NULL
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

parent_state_list AS (
  SELECT
    lookback_window,
    parent_suid,
    STRING_AGG(DISTINCT warehouse_state, ',' ORDER BY warehouse_state) AS parent_warehouse_states,
    COUNT(DISTINCT warehouse_state) AS n_parent_warehouse_states
  FROM parent_states
  GROUP BY 1, 2
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
    o.state_name AS own_state,
    o.city_name,
    o.postal_code,
    o.address_1,
    o.assigned_induction_hub_name,
    o.assigned_station_state,
    o.assigned_station_zip,
    o.actual_induction_hub_name,
    o.actual_induction_hub_state,
    o.ops,
    o.direct_gain,
    o.inducted_on_time_or_early,
    o.delivery_rel,
    o.distance_assignedhub_customer,
    o.distance_actualhub_customer,
    o.distance_assignedhub_actualhub,
    o.assignedhub_notequal_actualhub_flag,
    o.assignedstate_notequal_actualstate_flag,
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
    END AS is_candidate,
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

base_enriched AS (
  SELECT
    b.*,
    CASE
      WHEN ps.warehouse_state IS NOT NULL
        AND b.actual_induction_hub_state IS NOT NULL
        AND b.actual_induction_hub_state != b.own_state THEN 1
      ELSE 0
    END AS is_sibling_state
  FROM base AS b
  LEFT JOIN parent_states AS ps
    ON b.lookback_window = ps.lookback_window
   AND b.parent_suid = ps.parent_suid
   AND b.actual_induction_hub_state = ps.warehouse_state
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
    ANY_VALUE(own_state) AS own_state,
    ANY_VALUE(city_name) AS city_name,
    ANY_VALUE(postal_code) AS postal_code,
    ANY_VALUE(address_1) AS address_1,
    ANY_VALUE(assigned_induction_hub_name) AS assigned_induction_hub_name,
    ANY_VALUE(assigned_station_state) AS assigned_station_state,
    ANY_VALUE(assigned_station_zip) AS assigned_station_zip,
    COUNT(DISTINCT ops) AS total_vol,
    COUNT(DISTINCT week_start) AS weeks_with_vol,
    COUNT(DISTINCT IF(is_candidate = 1, ops, NULL)) AS candidate_vol,
    COUNT(DISTINCT IF(missing_actual_hub = 1, ops, NULL)) AS missing_actual_hub_vol,
    COUNT(DISTINCT IF(assignedhub_notequal_actualhub_flag = 1, ops, NULL)) AS hub_mismatch_vol,
    COUNT(DISTINCT IF(assignedstate_notequal_actualstate_flag = 1, ops, NULL)) AS state_mismatch_vol,
    COUNT(DISTINCT IF(is_far_hub_induction = 1, ops, NULL)) AS far_hub_vol,
    COUNT(DISTINCT IF(missing_actual_hub = 0, ops, NULL)) AS vol_with_actual_hub,
    COUNT(DISTINCT IF(within_200_of_assigned = 1, ops, NULL)) AS within_200_vol,
    AVG(distance_assignedhub_customer) AS avg_dist_assignedhub_customer,
    AVG(distance_actualhub_customer) AS avg_dist_actualhub_customer,
    AVG(distance_assignedhub_actualhub) AS avg_dist_assignedhub_actualhub,
    AVG(inducted_on_time_or_early) AS ifr,
    AVG(delivery_rel) AS delivery_rel
  FROM base_enriched
  GROUP BY lookback_window, timebase, lookback_weeks, supplier_id
),

-- Hub-level signals for ghost: persistent + scattered induction days
hub_agg AS (
  SELECT
    lookback_window,
    supplier_id,
    actual_induction_hub_name,
    ANY_VALUE(actual_induction_hub_state) AS actual_induction_hub_state,
    MAX(is_sibling_state) AS is_sibling_state,
    COUNT(DISTINCT ops) AS hub_vol,
    COUNT(DISTINCT IF(is_candidate = 1, ops, NULL)) AS hub_candidate_vol,
    COUNT(DISTINCT IF(is_candidate = 1, week_start, NULL)) AS weeks_with_candidate,
    COUNT(DISTINCT IF(is_candidate = 1, ind_day, NULL)) AS candidate_ind_days,
    AVG(CASE WHEN is_far_hub_induction = 1 THEN 1 ELSE 0 END) AS pct_far
  FROM base_enriched
  WHERE missing_actual_hub = 0
    AND actual_induction_hub_name IS NOT NULL
  GROUP BY 1, 2, 3
),

ghost_hubs AS (
  SELECT
    h.lookback_window,
    h.supplier_id,
    h.actual_induction_hub_name,
    h.actual_induction_hub_state,
    h.hub_vol,
    h.hub_candidate_vol,
    SAFE_DIVIDE(h.hub_vol, m.total_vol) AS hub_share,
    SAFE_DIVIDE(h.hub_candidate_vol, h.candidate_ind_days) AS avg_candidate_ops_per_day
  FROM hub_agg AS h
  JOIN supplier_meta AS m
    USING (lookback_window, supplier_id)
  WHERE h.is_sibling_state = 0
    AND h.hub_candidate_vol > 0
    AND h.pct_far >= 0.8
    AND h.weeks_with_candidate >= GREATEST(2, CAST(CEIL(0.5 * m.weeks_with_vol) AS INT64))
    AND SAFE_DIVIDE(h.hub_vol, m.total_vol) >= 0.10
    -- Scattered timing: average < 2 candidate ops per induction day
    AND SAFE_DIVIDE(h.hub_candidate_vol, h.candidate_ind_days) < 2
),

order_classified AS (
  SELECT
    b.*,
    CASE
      WHEN b.is_candidate = 0 THEN 'non_candidate'
      WHEN b.is_sibling_state = 1 THEN 'misshipping'
      WHEN g.actual_induction_hub_name IS NOT NULL THEN 'ghost_warehouse'
      WHEN COALESCE(b.direct_gain, 0) < 0.4 THEN 'jumbo'
      ELSE 'direct'
    END AS candidate_bucket
  FROM base_enriched AS b
  LEFT JOIN ghost_hubs AS g
    ON b.lookback_window = g.lookback_window
   AND b.supplier_id = g.supplier_id
   AND b.actual_induction_hub_name = g.actual_induction_hub_name
),

supplier_buckets AS (
  SELECT
    lookback_window,
    supplier_id,
    COUNT(DISTINCT IF(is_candidate = 1, ops, NULL)) AS candidate_vol,
    COUNT(DISTINCT IF(candidate_bucket = 'direct', ops, NULL)) AS direct_vol,
    COUNT(DISTINCT IF(candidate_bucket = 'jumbo', ops, NULL)) AS jumbo_vol,
    COUNT(DISTINCT IF(candidate_bucket = 'ghost_warehouse', ops, NULL)) AS ghost_vol,
    COUNT(DISTINCT IF(candidate_bucket = 'misshipping', ops, NULL)) AS misshipping_vol,
    AVG(IF(is_candidate = 1, direct_gain, NULL)) AS avg_gain_on_candidate,
    AVG(IF(candidate_bucket = 'direct', inducted_on_time_or_early, NULL)) AS ifr_direct,
    AVG(IF(candidate_bucket = 'direct', delivery_rel, NULL)) AS delivery_rel_direct,
    AVG(IF(candidate_bucket = 'jumbo', inducted_on_time_or_early, NULL)) AS ifr_jumbo,
    AVG(IF(candidate_bucket = 'jumbo', delivery_rel, NULL)) AS delivery_rel_jumbo,
    AVG(IF(candidate_bucket = 'ghost_warehouse', inducted_on_time_or_early, NULL)) AS ifr_ghost,
    AVG(IF(candidate_bucket = 'ghost_warehouse', delivery_rel, NULL)) AS delivery_rel_ghost,
    AVG(IF(candidate_bucket = 'misshipping', inducted_on_time_or_early, NULL)) AS ifr_misshipping,
    AVG(IF(candidate_bucket = 'misshipping', delivery_rel, NULL)) AS delivery_rel_misshipping,
    AVG(IF(is_candidate = 1, inducted_on_time_or_early, NULL)) AS ifr_candidate,
    AVG(IF(is_candidate = 1, delivery_rel, NULL)) AS delivery_rel_candidate,
    (
      COUNT(DISTINCT IF(candidate_bucket = 'direct', ops, NULL))
      + COUNT(DISTINCT IF(candidate_bucket = 'jumbo', ops, NULL))
      + COUNT(DISTINCT IF(candidate_bucket = 'ghost_warehouse', ops, NULL))
      + COUNT(DISTINCT IF(candidate_bucket = 'misshipping', ops, NULL))
    ) AS candidate_bucket_sum,
    (
      COUNT(DISTINCT IF(is_candidate = 1, ops, NULL))
      = (
        COUNT(DISTINCT IF(candidate_bucket = 'direct', ops, NULL))
        + COUNT(DISTINCT IF(candidate_bucket = 'jumbo', ops, NULL))
        + COUNT(DISTINCT IF(candidate_bucket = 'ghost_warehouse', ops, NULL))
        + COUNT(DISTINCT IF(candidate_bucket = 'misshipping', ops, NULL))
      )
    ) AS candidate_partition_ok
  FROM order_classified
  GROUP BY 1, 2
),

ghost_supplier AS (
  SELECT
    lookback_window,
    supplier_id,
    COUNT(*) AS n_ghost_hubs,
    SUM(hub_vol) AS ghost_hub_vol,
    STRING_AGG(
      CONCAT(
        actual_induction_hub_name, ' (', actual_induction_hub_state, ') ',
        CAST(ROUND(100 * hub_share) AS STRING), '%'
      ),
      '; ' ORDER BY hub_vol DESC LIMIT 5
    ) AS ghost_hubs
  FROM ghost_hubs
  GROUP BY 1, 2
),

misshipping_hubs AS (
  SELECT
    o.lookback_window,
    o.supplier_id,
    o.actual_induction_hub_name,
    ANY_VALUE(o.actual_induction_hub_state) AS actual_induction_hub_state,
    COUNT(DISTINCT o.ops) AS hub_misshipping_vol,
    SAFE_DIVIDE(COUNT(DISTINCT o.ops), ANY_VALUE(m.total_vol)) AS hub_share
  FROM order_classified AS o
  JOIN supplier_meta AS m
    USING (lookback_window, supplier_id)
  WHERE o.candidate_bucket = 'misshipping'
  GROUP BY o.lookback_window, o.supplier_id, o.actual_induction_hub_name
),

misshipping_supplier AS (
  SELECT
    lookback_window,
    supplier_id,
    COUNT(*) AS n_misshipping_hubs,
    STRING_AGG(
      CONCAT(
        actual_induction_hub_name, ' (', actual_induction_hub_state, ') ',
        CAST(ROUND(100 * hub_share) AS STRING), '%'
      ),
      '; ' ORDER BY hub_misshipping_vol DESC LIMIT 5
    ) AS misshipping_hubs
  FROM misshipping_hubs
  GROUP BY 1, 2
),

direct_hubs AS (
  SELECT
    o.lookback_window,
    o.supplier_id,
    o.actual_induction_hub_name,
    ANY_VALUE(o.actual_induction_hub_state) AS actual_induction_hub_state,
    COUNT(DISTINCT o.ops) AS hub_direct_vol,
    SAFE_DIVIDE(COUNT(DISTINCT o.ops), ANY_VALUE(m.total_vol)) AS hub_share
  FROM order_classified AS o
  JOIN supplier_meta AS m
    USING (lookback_window, supplier_id)
  WHERE o.candidate_bucket = 'direct'
  GROUP BY o.lookback_window, o.supplier_id, o.actual_induction_hub_name
),

top_direct_hubs AS (
  SELECT
    lookback_window,
    supplier_id,
    STRING_AGG(
      CONCAT(
        actual_induction_hub_name, ' (', actual_induction_hub_state, ') ',
        CAST(ROUND(100 * hub_share) AS STRING), '%'
      ),
      '; ' ORDER BY hub_direct_vol DESC LIMIT 5
    ) AS top_direct_hubs
  FROM direct_hubs
  GROUP BY 1, 2
),

direct_week AS (
  SELECT
    lookback_window,
    supplier_id,
    week_start,
    COUNT(DISTINCT ops) AS direct_vol
  FROM order_classified
  WHERE candidate_bucket = 'direct'
  GROUP BY 1, 2, 3
),

direct_supplier AS (
  SELECT
    lookback_window,
    supplier_id,
    COUNTIF(direct_vol >= 1) AS weeks_with_direct,
    STRING_AGG(
      CONCAT(CAST(week_start AS STRING), ': ', CAST(direct_vol AS STRING)),
      '; ' ORDER BY week_start
    ) AS direct_by_week
  FROM direct_week
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
    p.parent_warehouse_states,
    p.n_parent_warehouse_states,
    m.sto,
    m.srm_contact,
    m.own_state,
    m.city_name,
    m.postal_code,
    m.address_1,
    m.assigned_induction_hub_name,
    m.assigned_station_state,
    m.assigned_station_zip,
    m.total_vol,
    m.weeks_with_vol,
    COALESCE(sb.candidate_vol, 0) AS candidate_vol,
    SAFE_DIVIDE(COALESCE(sb.candidate_vol, 0), m.total_vol) AS candidate_share,
    COALESCE(sb.direct_vol, 0) AS direct_vol,
    SAFE_DIVIDE(COALESCE(sb.direct_vol, 0), m.total_vol) AS direct_share,
    COALESCE(sb.jumbo_vol, 0) AS jumbo_vol,
    SAFE_DIVIDE(COALESCE(sb.jumbo_vol, 0), m.total_vol) AS jumbo_share,
    COALESCE(sb.ghost_vol, 0) AS ghost_vol,
    SAFE_DIVIDE(COALESCE(sb.ghost_vol, 0), m.total_vol) AS ghost_share,
    COALESCE(sb.misshipping_vol, 0) AS misshipping_vol,
    SAFE_DIVIDE(COALESCE(sb.misshipping_vol, 0), m.total_vol) AS misshipping_share,
    COALESCE(t.weeks_with_direct, 0) AS weeks_with_direct,
    SAFE_DIVIDE(COALESCE(t.weeks_with_direct, 0), m.weeks_with_vol) AS pct_weeks_with_direct,
    t.direct_by_week,
    th.top_direct_hubs,
    COALESCE(g.n_ghost_hubs, 0) AS n_ghost_hubs,
    COALESCE(g.ghost_hub_vol, 0) AS ghost_hub_vol,
    g.ghost_hubs,
    COALESCE(ms.n_misshipping_hubs, 0) AS n_misshipping_hubs,
    ms.misshipping_hubs,
    m.missing_actual_hub_vol,
    SAFE_DIVIDE(m.missing_actual_hub_vol, m.total_vol) AS missing_actual_hub_share,
    m.hub_mismatch_vol,
    m.state_mismatch_vol,
    m.far_hub_vol,
    m.within_200_vol,
    SAFE_DIVIDE(m.within_200_vol, m.vol_with_actual_hub) AS pct_within_200_of_assigned,
    sb.avg_gain_on_candidate,
    m.avg_dist_assignedhub_customer,
    m.avg_dist_actualhub_customer,
    m.avg_dist_assignedhub_actualhub,
    m.ifr,
    m.delivery_rel,
    sb.ifr_candidate,
    sb.delivery_rel_candidate,
    sb.ifr_direct,
    sb.delivery_rel_direct,
    sb.ifr_jumbo,
    sb.delivery_rel_jumbo,
    sb.ifr_ghost,
    sb.delivery_rel_ghost,
    sb.ifr_misshipping,
    sb.delivery_rel_misshipping,
    COALESCE(sb.candidate_bucket_sum, 0) AS candidate_bucket_sum,
    COALESCE(sb.candidate_partition_ok, TRUE) AS candidate_partition_ok,
    CASE
      WHEN COALESCE(sb.ghost_vol, 0) > 0 THEN 'ghost_warehouses'
      WHEN COALESCE(t.weeks_with_direct, 0) >= m.weeks_with_vol
        OR (
          m.weeks_with_vol >= 4
          AND COALESCE(t.weeks_with_direct, 0) >= m.weeks_with_vol - 1
        )
        OR (
          m.lookback_weeks <= 2
          AND m.weeks_with_vol >= 2
          AND COALESCE(t.weeks_with_direct, 0) = m.weeks_with_vol
        )
        THEN 'consistently_builds_directs'
      WHEN COALESCE(t.weeks_with_direct, 0) >= 1 THEN 'sometimes_builds_directs'
      WHEN SAFE_DIVIDE(COALESCE(sb.misshipping_vol, 0), m.total_vol) >= 0.01
        THEN 'misshipping'
      ELSE 'no_directs'
    END AS direct_cohort
  FROM supplier_meta AS m
  LEFT JOIN parent_state_list AS p
    USING (lookback_window, parent_suid)
  LEFT JOIN supplier_buckets AS sb
    USING (lookback_window, supplier_id)
  LEFT JOIN ghost_supplier AS g
    USING (lookback_window, supplier_id)
  LEFT JOIN misshipping_supplier AS ms
    USING (lookback_window, supplier_id)
  LEFT JOIN direct_supplier AS t
    USING (lookback_window, supplier_id)
  LEFT JOIN top_direct_hubs AS th
    USING (lookback_window, supplier_id)
  WHERE m.total_vol >= CASE
    WHEN m.lookback_window = 'pdd_10w' THEN 50
    ELSE 20
  END
)

SELECT *
FROM classified
ORDER BY lookback_window, direct_cohort, total_vol DESC
