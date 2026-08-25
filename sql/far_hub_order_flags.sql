-- Far-hub OPID flags (supplier-first diagnosis → order flags)
--
-- Primary use: flag each ops (OPID) for misshipping / ghost / rare directs.
-- True "builds directs" suppliers are uncommon — focus is ghost + misshipping.
--
-- Flow:
--   1) Order attrs on DS volume (window: pdd_10w by default)
--   2) Roll up supplier behavior signals
--   3) Diagnose supplier_behavior
--   4) Flag each ops using supplier diagnosis + order attrs
--
-- Candidate (far wrong-hub):
--   wrong hub
--   AND distance_assignedhub_customer >= 400
--   AND distance_assignedhub_actualhub >= 200
--   (raw distances; do NOT trust distance_assignedhub_actualhub_200_plus)
--
-- Ghost (undeclared location — no parent WH in induction state, not own state):
--   hub ghost:     hub_share >= 10%, weeks_cand >= 2, mostly far
--   state ghost:   fragmented — state_share >= 2%, >=8 hubs in that state,
--                  material candidate vol (catches Loloi TX → CA multi-hub)
--
-- Misshipping: parent has another WH in the induction state (sibling state)
--
-- Direct (rare): supplier diagnosed builds_directs AND order is candidate
--                with gain >= 0.4 at a material hub, not misship/ghost
--
-- OPID flag priority:
--   non_candidate → misshipping → ghost_warehouse → jumbo → direct → other_far
--
-- Final SELECT defaults to ORDER-LEVEL (candidates only for size).
-- Swap to supplier_summary CTE select for supplier rollup.

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
    AND o.promised_delivery_end_range_date_at_order >= w.window_start
    AND o.promised_delivery_end_range_date_at_order < w.window_end
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
    o.ops,
    o.purchase_order_number,
    o.tracking_number,
    o.msbd_su,
    o.promised_delivery_end_range_date_at_order,
    o.order_complete_date,
    o.induction_date_lidd,
    o.delivery_date,
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
    o.distance_assignedhub_customer,
    o.distance_actualhub_customer,
    o.distance_assignedhub_actualhub,
    o.assignedhub_notequal_actualhub_flag,
    o.assignedstate_notequal_actualstate_flag,
    o.direct_gain,
    o.inducted_on_time_or_early,
    o.delivery_rel,
    o.cushion,
    COALESCE(DATE(o.carrier_first_induction_date_time), o.induction_date_lidd) AS ind_day,
    DATE_TRUNC(o.promised_delivery_end_range_date_at_order, WEEK(SUNDAY)) AS week_start,
    CASE
      WHEN o.actual_induction_hub_id IS NULL
        OR TRIM(CAST(o.actual_induction_hub_id AS STRING)) = ''
        THEN 1
      ELSE 0
    END AS missing_actual_hub,
    CASE
      WHEN o.assignedhub_notequal_actualhub_flag = 1
        AND COALESCE(o.distance_assignedhub_customer, 0) >= 400
        AND COALESCE(o.distance_assignedhub_actualhub, 0) >= 200
        THEN 1
      ELSE 0
    END AS is_candidate,
    CASE
      WHEN o.assignedhub_notequal_actualhub_flag = 1
        AND COALESCE(o.distance_assignedhub_actualhub, 0) >= 200
        THEN 1
      ELSE 0
    END AS is_far_hub
  FROM `wf-gcp-us-ae-global-tnd-prod.speed_and_reliability.HVE_perf_Monitoring` AS o
  CROSS JOIN windows AS w
  WHERE o.fulfillment_type = 'DS'
    AND o.promised_delivery_end_range_date_at_order >= w.window_start
    AND o.promised_delivery_end_range_date_at_order < w.window_end
),

base_enriched AS (
  SELECT
    b.*,
    CASE
      WHEN ps.warehouse_state IS NOT NULL
        AND b.actual_induction_hub_state IS NOT NULL
        AND b.actual_induction_hub_state != b.own_state
        THEN 1
      ELSE 0
    END AS is_sibling_state,
    CASE
      WHEN b.actual_induction_hub_state IS NOT NULL
        AND b.actual_induction_hub_state != b.own_state
        AND ps.warehouse_state IS NULL
        THEN 1
      ELSE 0
    END AS is_undeclared_state
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

    COUNT(DISTINCT ops) AS total_vol,
    COUNT(DISTINCT week_start) AS weeks_with_vol,

    COUNT(DISTINCT IF(is_candidate = 1, ops, NULL)) AS candidate_vol,
    COUNT(DISTINCT IF(is_candidate = 1 AND is_sibling_state = 1, ops, NULL)) AS misshipping_vol,
    COUNT(DISTINCT IF(is_candidate = 1 AND is_undeclared_state = 1, ops, NULL)) AS undeclared_candidate_vol,
    COUNT(DISTINCT IF(
      is_candidate = 1
      AND is_sibling_state = 0
      AND is_undeclared_state = 1
      AND COALESCE(direct_gain, 0) >= 0.4,
      ops, NULL
    )) AS directish_undeclared_vol,
    COUNT(DISTINCT IF(
      is_candidate = 1
      AND is_sibling_state = 0
      AND COALESCE(direct_gain, 0) >= 0.4,
      ops, NULL
    )) AS directish_vol,
    COUNT(DISTINCT IF(
      is_candidate = 1
      AND is_sibling_state = 0
      AND COALESCE(direct_gain, 0) < 0.4,
      ops, NULL
    )) AS jumboish_vol,

    AVG(inducted_on_time_or_early) AS ifr,
    AVG(delivery_rel) AS delivery_rel,
    AVG(IF(is_candidate = 1, inducted_on_time_or_early, NULL)) AS ifr_candidate,
    AVG(IF(is_candidate = 1, delivery_rel, NULL)) AS delivery_rel_candidate
  FROM base_enriched
  GROUP BY lookback_window, timebase, lookback_weeks, supplier_id
),

hub_agg AS (
  SELECT
    lookback_window,
    supplier_id,
    actual_induction_hub_name,
    ANY_VALUE(actual_induction_hub_state) AS actual_induction_hub_state,
    MAX(is_sibling_state) AS is_sibling_state,
    MAX(is_undeclared_state) AS is_undeclared_state,
    COUNT(DISTINCT ops) AS hub_vol,
    COUNT(DISTINCT IF(is_candidate = 1, ops, NULL)) AS hub_candidate_vol,
    COUNT(DISTINCT IF(is_candidate = 1, week_start, NULL)) AS weeks_with_candidate,
    AVG(CASE WHEN is_far_hub = 1 THEN 1 ELSE 0 END) AS pct_far
  FROM base_enriched
  WHERE missing_actual_hub = 0
    AND actual_induction_hub_name IS NOT NULL
  GROUP BY 1, 2, 3
),

-- Concentrated undeclared hub (classic ghost warehouse, >=10%)
ghost_hubs AS (
  SELECT
    h.lookback_window,
    h.supplier_id,
    h.actual_induction_hub_name,
    h.actual_induction_hub_state,
    h.hub_vol,
    h.hub_candidate_vol,
    SAFE_DIVIDE(h.hub_vol, m.total_vol) AS hub_share,
    'hub' AS ghost_grain
  FROM hub_agg AS h
  JOIN supplier_meta AS m
    USING (lookback_window, supplier_id)
  WHERE h.is_undeclared_state = 1
    AND h.hub_candidate_vol > 0
    AND h.pct_far >= 0.8
    AND h.weeks_with_candidate >= 2
    AND SAFE_DIVIDE(h.hub_vol, m.total_vol) >= 0.10
),

state_agg AS (
  SELECT
    lookback_window,
    supplier_id,
    actual_induction_hub_state,
    MAX(is_sibling_state) AS is_sibling_state,
    MAX(is_undeclared_state) AS is_undeclared_state,
    COUNT(DISTINCT ops) AS state_vol,
    COUNT(DISTINCT IF(is_candidate = 1, ops, NULL)) AS state_candidate_vol,
    COUNT(DISTINCT IF(is_candidate = 1, week_start, NULL)) AS weeks_with_candidate,
    COUNT(DISTINCT actual_induction_hub_name) AS n_hubs_in_state
  FROM base_enriched
  WHERE missing_actual_hub = 0
    AND actual_induction_hub_state IS NOT NULL
  GROUP BY 1, 2, 3
),

-- Fragmented undeclared state (many hubs in one undeclared state = WH region)
ghost_states AS (
  SELECT
    s.lookback_window,
    s.supplier_id,
    s.actual_induction_hub_state,
    s.state_vol,
    s.state_candidate_vol,
    s.n_hubs_in_state,
    SAFE_DIVIDE(s.state_vol, m.total_vol) AS state_share,
    'state' AS ghost_grain
  FROM state_agg AS s
  JOIN supplier_meta AS m
    USING (lookback_window, supplier_id)
  WHERE s.is_undeclared_state = 1
    AND s.n_hubs_in_state >= 8
    AND s.weeks_with_candidate >= 2
    AND SAFE_DIVIDE(s.state_vol, m.total_vol) >= 0.02
    AND s.state_candidate_vol >= GREATEST(20, CAST(CEIL(0.005 * m.total_vol) AS INT64))
),

ghost_hub_list AS (
  SELECT
    lookback_window,
    supplier_id,
    STRING_AGG(
      CONCAT(
        actual_induction_hub_name, ' (', actual_induction_hub_state, ') ',
        CAST(ROUND(100 * hub_share) AS STRING), '%'
      ),
      '; ' ORDER BY hub_vol DESC LIMIT 5
    ) AS ghost_hubs,
    COUNT(*) AS n_ghost_hubs
  FROM ghost_hubs
  GROUP BY 1, 2
),

ghost_state_list AS (
  SELECT
    lookback_window,
    supplier_id,
    STRING_AGG(
      CONCAT(
        actual_induction_hub_state, ' ',
        CAST(n_hubs_in_state AS STRING), ' hubs ',
        CAST(ROUND(100 * state_share) AS STRING), '%'
      ),
      '; ' ORDER BY state_vol DESC LIMIT 5
    ) AS ghost_states,
    COUNT(*) AS n_ghost_states
  FROM ghost_states
  GROUP BY 1, 2
),

-- Material direct hubs (only used if supplier is a directs builder)
material_direct_hubs AS (
  SELECT
    h.lookback_window,
    h.supplier_id,
    h.actual_induction_hub_name
  FROM hub_agg AS h
  JOIN supplier_meta AS m
    USING (lookback_window, supplier_id)
  WHERE h.is_sibling_state = 0
    AND (
      h.hub_candidate_vol >= GREATEST(20, CAST(CEIL(0.003 * m.total_vol) AS INT64))
      OR (
        SAFE_DIVIDE(h.hub_vol, m.total_vol) >= 0.005
        AND h.hub_candidate_vol >= 10
      )
    )
),

supplier_diagnosis AS (
  SELECT
    m.*,
    p.parent_warehouse_states,
    p.n_parent_warehouse_states,
    COALESCE(gh.n_ghost_hubs, 0) AS n_ghost_hubs,
    gh.ghost_hubs,
    COALESCE(gs.n_ghost_states, 0) AS n_ghost_states,
    gs.ghost_states,
    SAFE_DIVIDE(m.misshipping_vol, m.total_vol) AS misshipping_share,
    SAFE_DIVIDE(m.candidate_vol, m.total_vol) AS candidate_share,
    SAFE_DIVIDE(m.undeclared_candidate_vol, m.total_vol) AS undeclared_candidate_share,
    SAFE_DIVIDE(m.directish_vol, m.total_vol) AS directish_share,

    CASE
      WHEN COALESCE(gh.n_ghost_hubs, 0) > 0
        OR COALESCE(gs.n_ghost_states, 0) > 0
        THEN 'ghost_warehouse'

      WHEN SAFE_DIVIDE(m.misshipping_vol, m.total_vol) >= 0.01
        THEN 'misshipping'

      -- Rare intentional directs builders (high bar)
      WHEN m.directish_vol >= 50
        AND SAFE_DIVIDE(m.directish_vol, m.total_vol) >= 0.05
        THEN 'builds_directs'

      WHEN m.candidate_vol >= 10
        OR SAFE_DIVIDE(m.candidate_vol, m.total_vol) >= 0.01
        THEN 'far_hub_noise'

      ELSE 'clean'
    END AS supplier_behavior
  FROM supplier_meta AS m
  LEFT JOIN parent_state_list AS p
    USING (lookback_window, parent_suid)
  LEFT JOIN ghost_hub_list AS gh
    USING (lookback_window, supplier_id)
  LEFT JOIN ghost_state_list AS gs
    USING (lookback_window, supplier_id)
  WHERE m.total_vol >= 50
),

order_flagged AS (
  SELECT
    b.lookback_window,
    b.timebase,
    b.ops,
    b.purchase_order_number,
    b.tracking_number,
    b.supplier_id,
    b.su_name,
    b.parent_suid,
    b.parent_su_name,
    d.parent_warehouse_states,
    b.sto,
    b.srm_contact,
    b.own_state,
    b.city_name,
    b.postal_code,
    b.msbd_su,
    b.promised_delivery_end_range_date_at_order,
    b.ind_day,
    b.week_start,
    b.delivery_date,
    b.assigned_induction_hub_name,
    b.assigned_station_state,
    b.actual_induction_hub_name,
    b.actual_induction_hub_state,
    b.destination_zipcode,
    b.destination_state,
    b.distance_assignedhub_customer,
    b.distance_actualhub_customer,
    b.distance_assignedhub_actualhub,
    b.direct_gain,
    b.inducted_on_time_or_early,
    b.delivery_rel,
    b.cushion,
    b.missing_actual_hub,
    b.is_candidate,
    b.is_far_hub,
    b.is_sibling_state,
    b.is_undeclared_state,

    d.supplier_behavior,
    d.total_vol AS supplier_total_vol,
    d.candidate_vol AS supplier_candidate_vol,
    d.misshipping_vol AS supplier_misshipping_vol,
    d.misshipping_share AS supplier_misshipping_share,
    d.undeclared_candidate_vol AS supplier_undeclared_candidate_vol,
    d.directish_vol AS supplier_directish_vol,
    d.directish_share AS supplier_directish_share,
    d.ghost_hubs AS supplier_ghost_hubs,
    d.ghost_states AS supplier_ghost_states,
    d.n_ghost_hubs,
    d.n_ghost_states,
    d.ifr AS supplier_ifr,
    d.delivery_rel AS supplier_delivery_rel,

    CASE
      WHEN b.is_candidate = 0 THEN 'non_candidate'

      WHEN b.is_sibling_state = 1 THEN 'misshipping'

      WHEN ghub.actual_induction_hub_name IS NOT NULL
        OR gst.actual_induction_hub_state IS NOT NULL
        THEN 'ghost_warehouse'

      WHEN COALESCE(b.direct_gain, 0) < 0.4 THEN 'jumbo'

      WHEN d.supplier_behavior = 'builds_directs'
        AND md.actual_induction_hub_name IS NOT NULL
        THEN 'direct'

      ELSE 'other_far'
    END AS opid_flag,

    CASE WHEN b.is_candidate = 1 AND b.is_sibling_state = 1 THEN 1 ELSE 0 END AS is_misshipping,
    CASE
      WHEN b.is_candidate = 1
        AND (
          ghub.actual_induction_hub_name IS NOT NULL
          OR gst.actual_induction_hub_state IS NOT NULL
        )
        THEN 1
      ELSE 0
    END AS is_ghost_warehouse,
    CASE
      WHEN b.is_candidate = 1
        AND b.is_sibling_state = 0
        AND ghub.actual_induction_hub_name IS NULL
        AND gst.actual_induction_hub_state IS NULL
        AND COALESCE(b.direct_gain, 0) < 0.4
        THEN 1
      ELSE 0
    END AS is_jumbo,
    CASE
      WHEN b.is_candidate = 1
        AND d.supplier_behavior = 'builds_directs'
        AND b.is_sibling_state = 0
        AND ghub.actual_induction_hub_name IS NULL
        AND gst.actual_induction_hub_state IS NULL
        AND COALESCE(b.direct_gain, 0) >= 0.4
        AND md.actual_induction_hub_name IS NOT NULL
        THEN 1
      ELSE 0
    END AS is_direct,
    CASE
      WHEN b.is_candidate = 1
        AND b.is_sibling_state = 0
        AND ghub.actual_induction_hub_name IS NULL
        AND gst.actual_induction_hub_state IS NULL
        AND NOT (
          d.supplier_behavior = 'builds_directs'
          AND COALESCE(b.direct_gain, 0) >= 0.4
          AND md.actual_induction_hub_name IS NOT NULL
        )
        AND COALESCE(b.direct_gain, 0) >= 0.4
        THEN 1
      ELSE 0
    END AS is_other_far

  FROM base_enriched AS b
  JOIN supplier_diagnosis AS d
    USING (lookback_window, supplier_id)
  LEFT JOIN ghost_hubs AS ghub
    ON b.lookback_window = ghub.lookback_window
   AND b.supplier_id = ghub.supplier_id
   AND b.actual_induction_hub_name = ghub.actual_induction_hub_name
  LEFT JOIN ghost_states AS gst
    ON b.lookback_window = gst.lookback_window
   AND b.supplier_id = gst.supplier_id
   AND b.actual_induction_hub_state = gst.actual_induction_hub_state
  LEFT JOIN material_direct_hubs AS md
    ON b.lookback_window = md.lookback_window
   AND b.supplier_id = md.supplier_id
   AND b.actual_induction_hub_name = md.actual_induction_hub_name
),

supplier_summary AS (
  SELECT
    lookback_window,
    timebase,
    supplier_id,
    ANY_VALUE(su_name) AS su_name,
    ANY_VALUE(parent_suid) AS parent_suid,
    ANY_VALUE(parent_su_name) AS parent_su_name,
    ANY_VALUE(parent_warehouse_states) AS parent_warehouse_states,
    ANY_VALUE(sto) AS sto,
    ANY_VALUE(srm_contact) AS srm_contact,
    ANY_VALUE(own_state) AS own_state,
    ANY_VALUE(supplier_behavior) AS supplier_behavior,
    ANY_VALUE(supplier_total_vol) AS total_vol,
    ANY_VALUE(supplier_candidate_vol) AS candidate_vol,
    ANY_VALUE(supplier_misshipping_vol) AS misshipping_signal_vol,
    ANY_VALUE(supplier_misshipping_share) AS misshipping_share,
    ANY_VALUE(supplier_undeclared_candidate_vol) AS undeclared_candidate_vol,
    ANY_VALUE(supplier_directish_vol) AS directish_vol,
    ANY_VALUE(supplier_directish_share) AS directish_share,
    ANY_VALUE(supplier_ghost_hubs) AS ghost_hubs,
    ANY_VALUE(supplier_ghost_states) AS ghost_states,
    ANY_VALUE(n_ghost_hubs) AS n_ghost_hubs,
    ANY_VALUE(n_ghost_states) AS n_ghost_states,
    ANY_VALUE(supplier_ifr) AS ifr,
    ANY_VALUE(supplier_delivery_rel) AS delivery_rel,

    COUNT(DISTINCT IF(opid_flag = 'misshipping', ops, NULL)) AS misshipping_opid_vol,
    COUNT(DISTINCT IF(opid_flag = 'ghost_warehouse', ops, NULL)) AS ghost_opid_vol,
    COUNT(DISTINCT IF(opid_flag = 'jumbo', ops, NULL)) AS jumbo_opid_vol,
    COUNT(DISTINCT IF(opid_flag = 'direct', ops, NULL)) AS direct_opid_vol,
    COUNT(DISTINCT IF(opid_flag = 'other_far', ops, NULL)) AS other_far_opid_vol,
    COUNT(DISTINCT IF(opid_flag = 'non_candidate', ops, NULL)) AS non_candidate_vol,

    AVG(IF(opid_flag = 'misshipping', inducted_on_time_or_early, NULL)) AS ifr_misshipping,
    AVG(IF(opid_flag = 'ghost_warehouse', inducted_on_time_or_early, NULL)) AS ifr_ghost,
    AVG(IF(opid_flag = 'direct', inducted_on_time_or_early, NULL)) AS ifr_direct,
    AVG(IF(opid_flag = 'other_far', inducted_on_time_or_early, NULL)) AS ifr_other_far,
    AVG(IF(is_candidate = 1, inducted_on_time_or_early, NULL)) AS ifr_candidate,
    AVG(IF(opid_flag = 'misshipping', delivery_rel, NULL)) AS delivery_rel_misshipping,
    AVG(IF(opid_flag = 'ghost_warehouse', delivery_rel, NULL)) AS delivery_rel_ghost,
    AVG(IF(opid_flag = 'direct', delivery_rel, NULL)) AS delivery_rel_direct,
    AVG(IF(is_candidate = 1, delivery_rel, NULL)) AS delivery_rel_candidate
  FROM order_flagged
  GROUP BY lookback_window, timebase, supplier_id
)

-- =====================================================================
-- DEFAULT: ORDER-LEVEL (candidates only). For full volume or supplier
-- rollup, see scripts/run_far_hub_order_flags.py flags.
-- =====================================================================
SELECT *
FROM order_flagged
WHERE is_candidate = 1
ORDER BY supplier_behavior, supplier_id, promised_delivery_end_range_date_at_order DESC, ops
