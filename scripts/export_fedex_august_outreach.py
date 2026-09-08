#!/usr/bin/env python3
"""Export August delivery outreach packs from fedex_order_classfication_ET.

Three packs (delivery_date 2026-08-01 → 2026-08-31):
  1. Unexpected farther (misship farther + other_farther)
  2. Right-hub underperformers vs bucket benchmark
  3. Local-hub-swap underperformers vs bucket benchmark

Each pack writes parent summary, SUID summary, and sample trackings CSVs.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from gbq import query_df

TABLE = "`wf-gcp-us-ae-global-tnd-prod.speed_and_reliability.fedex_order_classfication_ET`"
OUT = Path("output/fedex_august_exports")
AUG = "delivery_date BETWEEN '2026-08-01' AND '2026-08-31'"
TRACKING_PER_SUID = 25


def _flatten_top_count(val) -> str:
    """Turn BigQuery APPROX_TOP_COUNT arrays into 'HUB (n); HUB (n)'."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    if isinstance(val, str):
        return val.replace("\n", " ").strip()
    items = list(val) if not isinstance(val, list) else val
    parts = []
    for x in items:
        if x is None:
            continue
        if isinstance(x, dict):
            value, count = x.get("value"), x.get("count")
        else:
            value = getattr(x, "value", None)
            count = getattr(x, "count", None)
            if value is None and hasattr(x, "get"):
                value, count = x.get("value"), x.get("count")
        if value is None:
            continue
        parts.append(f"{value} ({count})")
    return "; ".join(parts)


def _flatten_hub_cols(df):
    for col in ("top_assigned_hubs", "top_actual_hubs"):
        if col in df.columns:
            df[col] = df[col].map(_flatten_top_count)
    return df


def _save(df, name: str) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    df.to_csv(path, index=False)
    print(f"wrote {path} ({len(df):,} rows)")
    return path


def export_farther() -> None:
    parents = query_df(
        f"""
        WITH base AS (
          SELECT *
          FROM {TABLE}
          WHERE {AUG}
            AND bucket IN (
              'misshipping - farther from customer',
              'other_farther'
            )
        ),
        net AS (
          SELECT COUNT(DISTINCT ops) AS net_vol
          FROM {TABLE}
          WHERE {AUG}
        ),
        parent_all AS (
          SELECT parent_suid, COUNT(DISTINCT ops) AS parent_vol
          FROM {TABLE}
          WHERE {AUG}
          GROUP BY 1
        )
        SELECT
          b.parent_suid,
          ANY_VALUE(b.parent_su_name) AS parent_su_name,
          ANY_VALUE(b.sto) AS sto,
          ANY_VALUE(b.srm_contact) AS srm_contact,
          COUNT(DISTINCT b.ops) AS farther_vol,
          pa.parent_vol,
          SAFE_DIVIDE(COUNT(DISTINCT b.ops), pa.parent_vol) AS farther_share_of_parent,
          SAFE_DIVIDE(COUNT(DISTINCT b.ops), (SELECT net_vol FROM net)) AS farther_share_of_network,
          AVG(b.inducted_on_time_or_early) AS ifr,
          AVG(b.delivery_rel) AS delivery_rel,
          AVG(b.actual_minus_assigned_transit) AS avg_transit_delta_days,
          AVG(b.miles_closer_to_customer) AS avg_miles_closer,
          AVG(b.distance_assignedhub_actualhub) AS avg_hub_delta_mi,
          COUNT(DISTINCT b.assigned_induction_hub_name) AS n_assigned_hubs,
          COUNT(DISTINCT b.actual_induction_hub_name) AS n_actual_hubs
        FROM base b
        JOIN parent_all pa USING (parent_suid)
        GROUP BY b.parent_suid, pa.parent_vol
        HAVING farther_vol >= 200
        ORDER BY farther_vol DESC
        """
    )
    _save(parents, "01_farther_parents_august.csv")

    top_parents = parents["parent_suid"].head(20).tolist()
    parent_list = ", ".join(str(int(x)) for x in top_parents)

    suids = query_df(
        f"""
        WITH base AS (
          SELECT *
          FROM {TABLE}
          WHERE {AUG}
            AND bucket IN (
              'misshipping - farther from customer',
              'other_farther'
            )
            AND parent_suid IN ({parent_list})
        ),
        suid_all AS (
          SELECT supplier_id, COUNT(DISTINCT ops) AS suid_vol
          FROM {TABLE}
          WHERE {AUG}
          GROUP BY 1
        )
        SELECT
          b.parent_suid,
          ANY_VALUE(b.parent_su_name) AS parent_su_name,
          b.supplier_id,
          ANY_VALUE(b.su_name) AS su_name,
          ANY_VALUE(b.sto) AS sto,
          ANY_VALUE(b.srm_contact) AS srm_contact,
          ANY_VALUE(b.own_state) AS own_state,
          ANY_VALUE(b.city_name) AS city_name,
          COUNT(DISTINCT b.ops) AS farther_vol,
          sa.suid_vol,
          SAFE_DIVIDE(COUNT(DISTINCT b.ops), sa.suid_vol) AS farther_share_of_suid,
          AVG(b.inducted_on_time_or_early) AS ifr,
          AVG(b.delivery_rel) AS delivery_rel,
          AVG(b.actual_minus_assigned_transit) AS avg_transit_delta_days,
          AVG(b.miles_closer_to_customer) AS avg_miles_closer,
          AVG(b.distance_assignedhub_actualhub) AS avg_hub_delta_mi,
          APPROX_TOP_COUNT(b.assigned_induction_hub_name, 3) AS top_assigned_hubs,
          APPROX_TOP_COUNT(b.actual_induction_hub_name, 3) AS top_actual_hubs
        FROM base b
        JOIN suid_all sa ON sa.supplier_id = b.supplier_id
        GROUP BY b.parent_suid, b.supplier_id, sa.suid_vol
        HAVING farther_vol >= 50
        ORDER BY farther_vol DESC
        """
    )
    _save(_flatten_hub_cols(suids), "01_farther_suids_august.csv")

    trackings = query_df(
        f"""
        WITH base AS (
          SELECT *
          FROM {TABLE}
          WHERE {AUG}
            AND bucket IN (
              'misshipping - farther from customer',
              'other_farther'
            )
            AND parent_suid IN ({parent_list})
        ),
        ranked AS (
          SELECT
            *,
            ROW_NUMBER() OVER (
              PARTITION BY supplier_id
              ORDER BY distance_assignedhub_actualhub DESC NULLS LAST, ops
            ) AS rn
          FROM base
        )
        SELECT
          parent_suid,
          parent_su_name,
          supplier_id,
          su_name,
          sto,
          srm_contact,
          bucket,
          ops,
          purchase_order_number,
          tracking_number,
          delivery_date,
          own_state,
          assigned_induction_hub_name,
          assigned_station_state,
          actual_induction_hub_name,
          actual_induction_hub_state,
          destination_state,
          destination_zipcode,
          distance_assignedhub_actualhub,
          miles_closer_to_customer,
          actual_minus_assigned_transit,
          inducted_on_time_or_early,
          delivery_rel
        FROM ranked
        WHERE rn <= {TRACKING_PER_SUID}
        ORDER BY parent_suid, supplier_id, rn
        """
    )
    _save(trackings, "01_farther_sample_trackings_august.csv")


def export_bucket_underperformers(bucket_mode: str, prefix: str, min_parent_vol: int) -> None:
    if bucket_mode == "right_hub":
        bucket_filter = "bucket = 'right hub'"
        label = "right_hub"
    elif bucket_mode == "local_swap":
        bucket_filter = "STARTS_WITH(bucket, 'local_hub_within_100miles')"
        label = "local_swap"
    else:
        raise ValueError(bucket_mode)

    parents = query_df(
        f"""
        WITH base AS (
          SELECT *
          FROM {TABLE}
          WHERE {AUG}
            AND {bucket_filter}
        ),
        bench AS (
          SELECT
            AVG(inducted_on_time_or_early) AS bench_ifr,
            AVG(delivery_rel) AS bench_dr
          FROM base
        )
        SELECT
          b.parent_suid,
          ANY_VALUE(b.parent_su_name) AS parent_su_name,
          ANY_VALUE(b.sto) AS sto,
          ANY_VALUE(b.srm_contact) AS srm_contact,
          COUNT(DISTINCT b.ops) AS vol,
          AVG(b.inducted_on_time_or_early) AS ifr,
          AVG(b.delivery_rel) AS delivery_rel,
          (SELECT bench_ifr FROM bench) AS bench_ifr,
          (SELECT bench_dr FROM bench) AS bench_dr,
          (SELECT bench_ifr FROM bench) - AVG(b.inducted_on_time_or_early) AS ifr_gap,
          (SELECT bench_dr FROM bench) - AVG(b.delivery_rel) AS dr_gap,
          COUNT(DISTINCT b.ops) * (1 - AVG(b.delivery_rel)) AS late_delivery_ops_est,
          COUNT(DISTINCT b.ops) * (1 - AVG(b.inducted_on_time_or_early)) AS late_induction_ops_est,
          AVG(b.actual_minus_assigned_transit) AS avg_transit_delta_days
        FROM base b
        GROUP BY b.parent_suid
        HAVING vol >= {min_parent_vol}
          AND (
            AVG(b.inducted_on_time_or_early) < (SELECT bench_ifr FROM bench) - 0.03
            OR AVG(b.delivery_rel) < (SELECT bench_dr FROM bench) - 0.05
          )
        ORDER BY late_delivery_ops_est DESC
        LIMIT 20
        """
    )
    _save(parents, f"{prefix}_{label}_underperformer_parents_august.csv")

    if parents.empty:
        print(f"no parents for {label}")
        return

    parent_list = ", ".join(str(int(x)) for x in parents["parent_suid"].tolist())

    suids = query_df(
        f"""
        WITH base AS (
          SELECT *
          FROM {TABLE}
          WHERE {AUG}
            AND {bucket_filter}
            AND parent_suid IN ({parent_list})
        ),
        bench AS (
          SELECT
            AVG(inducted_on_time_or_early) AS bench_ifr,
            AVG(delivery_rel) AS bench_dr
          FROM {TABLE}
          WHERE {AUG}
            AND {bucket_filter}
        )
        SELECT
          b.parent_suid,
          ANY_VALUE(b.parent_su_name) AS parent_su_name,
          b.supplier_id,
          ANY_VALUE(b.su_name) AS su_name,
          ANY_VALUE(b.sto) AS sto,
          ANY_VALUE(b.srm_contact) AS srm_contact,
          ANY_VALUE(b.own_state) AS own_state,
          ANY_VALUE(b.city_name) AS city_name,
          COUNT(DISTINCT b.ops) AS vol,
          AVG(b.inducted_on_time_or_early) AS ifr,
          AVG(b.delivery_rel) AS delivery_rel,
          (SELECT bench_ifr FROM bench) AS bench_ifr,
          (SELECT bench_dr FROM bench) AS bench_dr,
          (SELECT bench_ifr FROM bench) - AVG(b.inducted_on_time_or_early) AS ifr_gap,
          (SELECT bench_dr FROM bench) - AVG(b.delivery_rel) AS dr_gap,
          COUNT(DISTINCT b.ops) * (1 - AVG(b.delivery_rel)) AS late_delivery_ops_est,
          AVG(b.actual_minus_assigned_transit) AS avg_transit_delta_days,
          APPROX_TOP_COUNT(b.assigned_induction_hub_name, 3) AS top_assigned_hubs,
          APPROX_TOP_COUNT(b.actual_induction_hub_name, 3) AS top_actual_hubs
        FROM base b
        GROUP BY b.parent_suid, b.supplier_id
        HAVING vol >= 100
          AND (
            AVG(b.inducted_on_time_or_early) < (SELECT bench_ifr FROM bench) - 0.03
            OR AVG(b.delivery_rel) < (SELECT bench_dr FROM bench) - 0.05
          )
        ORDER BY late_delivery_ops_est DESC
        """
    )
    _save(_flatten_hub_cols(suids), f"{prefix}_{label}_underperformer_suids_august.csv")

    trackings = query_df(
        f"""
        WITH target_suids AS (
          SELECT DISTINCT supplier_id
          FROM {TABLE}
          WHERE {AUG}
            AND {bucket_filter}
            AND parent_suid IN ({parent_list})
        ),
        base AS (
          SELECT t.*
          FROM {TABLE} t
          JOIN target_suids s USING (supplier_id)
          WHERE {AUG}
            AND {bucket_filter}
            AND parent_suid IN ({parent_list})
        ),
        ranked AS (
          SELECT
            *,
            ROW_NUMBER() OVER (
              PARTITION BY supplier_id
              ORDER BY
                CASE WHEN delivery_rel = 0 THEN 0 ELSE 1 END,
                CASE WHEN inducted_on_time_or_early = 0 THEN 0 ELSE 1 END,
                ops
            ) AS rn
          FROM base
        )
        SELECT
          parent_suid,
          parent_su_name,
          supplier_id,
          su_name,
          sto,
          srm_contact,
          bucket,
          ops,
          purchase_order_number,
          tracking_number,
          delivery_date,
          own_state,
          assigned_induction_hub_name,
          assigned_station_state,
          actual_induction_hub_name,
          actual_induction_hub_state,
          destination_state,
          destination_zipcode,
          distance_assignedhub_actualhub,
          miles_closer_to_customer,
          actual_minus_assigned_transit,
          inducted_on_time_or_early,
          delivery_rel
        FROM ranked
        WHERE rn <= {TRACKING_PER_SUID}
        ORDER BY parent_suid, supplier_id, rn
        """
    )
    # Prefer failing examples: already ordered; optionally filter to suids in underperformer list
    if not suids.empty:
        keep = set(suids["supplier_id"].astype(int).tolist())
        trackings = trackings[trackings["supplier_id"].astype(int).isin(keep)]
    _save(trackings, f"{prefix}_{label}_sample_trackings_august.csv")


def main() -> None:
    export_farther()
    export_bucket_underperformers("right_hub", "02", min_parent_vol=2000)
    export_bucket_underperformers("local_swap", "03", min_parent_vol=1500)


if __name__ == "__main__":
    main()
