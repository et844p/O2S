-- Directs supplier cohort analysis
--
-- Flow:
--   1) Direct CANDIDATE = distance conditions (400 / 200)
--   2) Split candidates using parent warehouse states + induction timing:
--        non_compliant       — ANY candidate in a state where parent HAS another WH
--        ghost_warehouse     — persistent far hub (>=10% vol) where parent has NO WH
--        not_candidate       — relief / FedEx constrained-hub pull (>=10% grouped share, not ghost)
--        actually_direct     — grouped far batches, <10% of supplier vol, gain >= 0.4
--                              (no minimum % share — shared direct trailers can be small for one SU)
--        jumbo               — same pattern as actually_direct but gain < 0.4 / null
--        other_candidate     — remaining candidates
--
-- Candidate (use raw distances; do NOT trust distance_assignedhub_actualhub_200_plus):
--   assignedhub_notequal_actualhub_flag = 1
--   AND distance_assignedhub_customer >= 400
--   AND distance_assignedhub_actualhub >= 200
--
-- Parent warehouse states = distinct state_name of all DS SUIDs under parent_suid.
-- Grouped = 2+ candidate ops at same supplier + actual hub + induction day.
--
-- Supplier cohorts (priority):
--   ghost_warehouses
--   consistently_builds_directs / sometimes_builds_directs  (from actually_direct)
--   non_compliant_shipping
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

-- Parent footprint: states where any child SUID is registered
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

hub_day AS (
  SELECT
    lookback_window,
    supplier_id,
    actual_induction_hub_name,
    ind_day,
    COUNT(DISTINCT IF(is_candidate = 1, ops, NULL)) AS candidate_on_day
  FROM base
  WHERE missing_actual_hub = 0
    AND is_candidate = 1
    AND actual_induction_hub_name IS NOT NULL
  GROUP BY 1, 2, 3, 4
),

base_enriched AS (
  SELECT
    b.*,
    CASE
      WHEN b.is_candidate = 1 AND COALESCE(hd.candidate_on_day, 0) >= 2 THEN 1
      ELSE 0
    END AS is_grouped,
    CASE
      WHEN ps.warehouse_state IS NOT NULL
        AND b.actual_induction_hub_state IS NOT NULL
        AND b.actual_induction_hub_state != b.own_state THEN 1
      ELSE 0
    END AS is_sibling_state
  FROM base AS b
  LEFT JOIN hub_day AS hd
    ON b.lookback_window = hd.lookback_window
   AND b.supplier_id = hd.supplier_id
   AND b.actual_induction_hub_name = hd.actual_induction_hub_name
   AND b.ind_day = hd.ind_day
  LEFT JOIN parent_states AS ps
    ON b.lookback_window = ps.lookback_window
   AND b.parent_suid = ps.parent_suid
   AND b.actual_induction_hub_state = ps.warehouse_state
),

supplier_week AS (
  SELECT
    lookback_window,
    supplier_id,
    week_start,
    COUNT(DISTINCT ops) AS week_vol
  FROM base_enriched
  GROUP BY 1, 2, 3
),

hub_agg AS (
  SELECT
    lookback_window,
    supplier_id,
    actual_induction_hub_name,
    actual_induction_hub_state,
    ANY_VALUE(is_sibling_state) AS is_sibling_state,
    COUNT(DISTINCT week_start) AS weeks_present,
    COUNT(DISTINCT ops) AS hub_vol,
    COUNT(DISTINCT IF(is_candidate = 1, ops, NULL)) AS hub_candidate_vol,
    COUNT(DISTINCT IF(is_grouped = 1, ops, NULL)) AS hub_grouped_vol,
    COUNT(DISTINCT IF(is_candidate = 1, week_start, NULL)) AS weeks_with_candidate,
    COUNT(DISTINCT IF(is_grouped = 1, week_start, NULL)) AS weeks_with_grouped,
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
    COUNT(DISTINCT IF(is_grouped = 1, ops, NULL)) AS grouped_candidate_vol,
    COUNT(DISTINCT IF(missing_actual_hub = 1, ops, NULL)) AS missing_actual_hub_vol,
    COUNT(DISTINCT IF(assignedhub_notequal_actualhub_flag = 1, ops, NULL)) AS hub_mismatch_vol,
    COUNT(DISTINCT IF(assignedstate_notequal_actualstate_flag = 1, ops, NULL)) AS state_mismatch_vol,
    COUNT(DISTINCT IF(is_far_hub_induction = 1, ops, NULL)) AS far_hub_vol,
    COUNT(DISTINCT IF(missing_actual_hub = 0, ops, NULL)) AS vol_with_actual_hub,
    COUNT(DISTINCT IF(within_200_of_assigned = 1, ops, NULL)) AS within_200_vol,
    AVG(direct_gain) AS avg_direct_gain,
    AVG(IF(is_candidate = 1, direct_gain, NULL)) AS avg_gain_on_candidate,
    AVG(distance_assignedhub_customer) AS avg_dist_assignedhub_customer,
    AVG(distance_actualhub_customer) AS avg_dist_actualhub_customer,
    AVG(distance_assignedhub_actualhub) AS avg_dist_assignedhub_actualhub,
    AVG(inducted_on_time_or_early) AS ifr
  FROM base_enriched
  GROUP BY lookback_window, timebase, lookback_weeks, supplier_id
),

hub_bucketed AS (
  SELECT
    h.lookback_window,
    h.supplier_id,
    h.actual_induction_hub_name,
    h.actual_induction_hub_state,
    h.is_sibling_state,
    h.hub_vol,
    h.hub_candidate_vol,
    h.hub_grouped_vol,
    h.weeks_with_candidate,
    h.weeks_with_grouped,
    SAFE_DIVIDE(h.hub_vol, m.total_vol) AS hub_share,
    CASE
      -- Ghost: no parent WH in induction state; persistent far hub >=10% of supplier vol
      WHEN h.is_sibling_state = 0
        AND h.pct_far >= 0.8
        AND h.weeks_with_candidate >= GREATEST(2, CAST(CEIL(0.5 * m.weeks_with_vol) AS INT64))
        AND SAFE_DIVIDE(h.hub_vol, m.total_vol) >= 0.10
        THEN 'ghost_warehouse'

      -- Non-compliant: parent has a WH in that state (any candidate volume)
      WHEN h.is_sibling_state = 1
        AND h.hub_candidate_vol > 0
        THEN 'non_compliant'

      -- Relief / FedEx constrained-hub pull: large grouped alternate hub that is not ghost
      WHEN h.is_sibling_state = 0
        AND SAFE_DIVIDE(h.hub_grouped_vol, m.total_vol) >= 0.10
        THEN 'not_candidate'

      -- Actually direct: grouped far batches; no minimum share (shared trailers OK);
      -- keep under 10% so ghost-scale hubs stay ghost/relief above
      WHEN h.hub_grouped_vol > 0
        AND h.weeks_with_grouped >= 2
        AND h.pct_far >= 0.8
        AND SAFE_DIVIDE(h.hub_grouped_vol, m.total_vol) < 0.10
        THEN 'actually_direct'

      WHEN h.hub_candidate_vol > 0 THEN 'other_candidate'
      ELSE 'not_candidate'
    END AS hub_bucket
  FROM hub_agg AS h
  JOIN supplier_meta AS m
    USING (lookback_window, supplier_id)
),

ghost_hubs AS (
  SELECT * FROM hub_bucketed WHERE hub_bucket = 'ghost_warehouse'
),

noncompliant_hubs AS (
  SELECT * FROM hub_bucketed WHERE hub_bucket = 'non_compliant'
),

direct_hubs AS (
  SELECT * FROM hub_bucketed WHERE hub_bucket = 'actually_direct'
),

ghost_supplier AS (
  SELECT
    lookback_window,
    supplier_id,
    COUNT(*) AS n_ghost_hubs,
    SUM(hub_vol) AS ghost_hub_vol,
    SUM(hub_candidate_vol) AS ghost_candidate_vol,
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

noncompliant_supplier AS (
  SELECT
    lookback_window,
    supplier_id,
    COUNT(*) AS n_noncompliant_hubs,
    SUM(hub_candidate_vol) AS noncompliant_candidate_vol,
    STRING_AGG(
      CONCAT(
        actual_induction_hub_name, ' (', actual_induction_hub_state, ') ',
        CAST(ROUND(100 * hub_share) AS STRING), '%'
      ),
      '; ' ORDER BY hub_candidate_vol DESC LIMIT 5
    ) AS noncompliant_hubs
  FROM noncompliant_hubs
  GROUP BY 1, 2
),

true_direct_week AS (
  SELECT
    b.lookback_window,
    b.supplier_id,
    b.week_start,
    COUNT(DISTINCT IF(b.direct_gain >= 0.4, b.ops, NULL)) AS actually_direct_vol,
    COUNT(DISTINCT IF(NOT (b.direct_gain >= 0.4), b.ops, NULL)) AS jumbo_vol
  FROM base_enriched AS b
  JOIN direct_hubs AS d
    ON b.lookback_window = d.lookback_window
   AND b.supplier_id = d.supplier_id
   AND b.actual_induction_hub_name = d.actual_induction_hub_name
  WHERE b.is_grouped = 1
  GROUP BY 1, 2, 3
),

true_direct_supplier AS (
  SELECT
    lookback_window,
    supplier_id,
    SUM(actually_direct_vol) AS actually_direct_vol,
    SUM(jumbo_vol) AS jumbo_vol,
    COUNTIF(actually_direct_vol >= 1) AS weeks_with_actually_direct,
    STRING_AGG(
      CONCAT(CAST(week_start AS STRING), ': ', CAST(actually_direct_vol AS STRING)),
      '; ' ORDER BY week_start
    ) AS actually_direct_by_week
  FROM true_direct_week
  GROUP BY 1, 2
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
      '; ' ORDER BY hub_grouped_vol DESC LIMIT 5
    ) AS top_actually_direct_hubs
  FROM direct_hubs
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
    m.candidate_vol,
    SAFE_DIVIDE(m.candidate_vol, m.total_vol) AS candidate_share,
    m.grouped_candidate_vol,
    COALESCE(t.actually_direct_vol, 0) AS actually_direct_vol,
    SAFE_DIVIDE(COALESCE(t.actually_direct_vol, 0), m.total_vol) AS actually_direct_share,
    COALESCE(t.jumbo_vol, 0) AS jumbo_vol,
    SAFE_DIVIDE(COALESCE(t.jumbo_vol, 0), m.total_vol) AS jumbo_share,
    COALESCE(t.weeks_with_actually_direct, 0) AS weeks_with_actually_direct,
    SAFE_DIVIDE(COALESCE(t.weeks_with_actually_direct, 0), m.weeks_with_vol) AS pct_weeks_with_actually_direct,
    t.actually_direct_by_week,
    th.top_actually_direct_hubs,
    COALESCE(g.n_ghost_hubs, 0) AS n_ghost_hubs,
    COALESCE(g.ghost_hub_vol, 0) AS ghost_hub_vol,
    SAFE_DIVIDE(COALESCE(g.ghost_hub_vol, 0), m.total_vol) AS ghost_share,
    COALESCE(g.ghost_candidate_vol, 0) AS ghost_candidate_vol,
    g.ghost_hubs,
    COALESCE(nc.n_noncompliant_hubs, 0) AS n_noncompliant_hubs,
    COALESCE(nc.noncompliant_candidate_vol, 0) AS noncompliant_candidate_vol,
    SAFE_DIVIDE(COALESCE(nc.noncompliant_candidate_vol, 0), m.total_vol) AS noncompliant_share,
    nc.noncompliant_hubs,
    m.missing_actual_hub_vol,
    SAFE_DIVIDE(m.missing_actual_hub_vol, m.total_vol) AS missing_actual_hub_share,
    m.hub_mismatch_vol,
    m.state_mismatch_vol,
    m.far_hub_vol,
    m.within_200_vol,
    SAFE_DIVIDE(m.within_200_vol, m.vol_with_actual_hub) AS pct_within_200_of_assigned,
    m.avg_direct_gain,
    m.avg_gain_on_candidate,
    m.avg_dist_assignedhub_customer,
    m.avg_dist_actualhub_customer,
    m.avg_dist_assignedhub_actualhub,
    m.ifr,
    CASE
      WHEN COALESCE(g.ghost_hub_vol, 0) > 0 THEN 'ghost_warehouses'
      WHEN SAFE_DIVIDE(COALESCE(t.actually_direct_vol, 0), m.total_vol) >= 0.10
        THEN 'ghost_warehouses'
      WHEN COALESCE(t.weeks_with_actually_direct, 0) >= m.weeks_with_vol
        OR (
          m.weeks_with_vol >= 4
          AND COALESCE(t.weeks_with_actually_direct, 0) >= m.weeks_with_vol - 1
        )
        OR (
          m.lookback_weeks <= 2
          AND m.weeks_with_vol >= 2
          AND COALESCE(t.weeks_with_actually_direct, 0) = m.weeks_with_vol
        )
        THEN 'consistently_builds_directs'
      WHEN COALESCE(t.weeks_with_actually_direct, 0) >= 1 THEN 'sometimes_builds_directs'
      WHEN SAFE_DIVIDE(COALESCE(nc.noncompliant_candidate_vol, 0), m.total_vol) >= 0.01
        THEN 'non_compliant_shipping'
      ELSE 'no_directs'
    END AS direct_cohort
  FROM supplier_meta AS m
  LEFT JOIN parent_state_list AS p
    USING (lookback_window, parent_suid)
  LEFT JOIN ghost_supplier AS g
    USING (lookback_window, supplier_id)
  LEFT JOIN noncompliant_supplier AS nc
    USING (lookback_window, supplier_id)
  LEFT JOIN true_direct_supplier AS t
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
