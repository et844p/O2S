# Directs Supplier Cohorts

Generated: 2026-08-11

Classifies dropship (`fulfillment_type = 'DS'`) suppliers by splitting **direct candidates** into actually direct vs jumbo vs ghost warehouse vs non-compliant shipping.

## Lookbacks

| Window | Timebase | Length | Min volume |
|--------|----------|--------|------------|
| `pdd_10w` | `promised_delivery_end_range_date_at_order` | 10 weeks | 50 ops |
| `msbd_2w` | `msbd_su` | 2 weeks | 20 ops |

## Step 1 — Distance candidate

Distance conditions only (raw columns; do **not** trust `distance_assignedhub_actualhub_200_plus`):

1. `assignedhub_notequal_actualhub_flag = 1`
2. `distance_assignedhub_customer >= 400`
3. `distance_assignedhub_actualhub >= 200`

## Step 2 — Final candidate + exclusive split

Uses **parent warehouse states** (distinct `state_name` of all DS SUIDs under `parent_suid`) and **induction timing** (grouped = 2+ candidate ops at same actual hub + day).

**Relief** (≥10% grouped alternate hub that is not ghost — FedEx / constrained-hub pull) is **removed** from candidates.

Final candidate volume partitions exhaustively:

```
candidate_vol
  = actually_direct_vol
  + jumbo_vol
  + ghost_candidate_vol
  + noncompliant_candidate_vol
```

| Bucket | Rule |
|--------|------|
| **Actually direct** | Grouped batches at a far hub, recurring (≥2 weeks), **under 10%** of supplier vol; **no minimum %** (shared direct trailers OK); **`direct_gain >= 0.4`** |
| **Jumbo** | Remaining final candidates that are not ghost / non-compliant / actually-direct (direct-pattern with gain &lt; 0.4, plus residual ungrouped / short-recurrence / other hubs) |
| **Ghost warehouse** | Far hub ≥10% of supplier vol, most weeks, and parent has **no** warehouse in that induction state |
| **Non-compliant** | Candidate in a state where parent **has** another warehouse (any volume — not only consistent weeks) |
| **Relief** | Large grouped alternate hub (≥10% grouped share) that is not ghost — **not** counted in `candidate_vol` |

`candidate_partition_ok` is true when the four buckets sum exactly to `candidate_vol`.

## Supplier cohorts (priority order)

| Cohort | Meaning |
|--------|---------|
| `ghost_warehouses` | Persistent unregistered far hubs (or actually-direct share ≥10%) |
| `consistently_builds_directs` | Actually-direct weeks nearly every week |
| `sometimes_builds_directs` | Actually-direct in some weeks |
| `non_compliant_shipping` | Sibling-state candidates only (no material actually-direct) |
| `no_directs` | No material candidate split into the above |

## Performance columns

Each supplier row includes IFR (`inducted_on_time_or_early`) and `delivery_rel` for:

- overall (`ifr`, `delivery_rel`)
- final candidates (`ifr_candidate`, `delivery_rel_candidate`)
- each bucket: actually direct / jumbo / ghost / non-compliant / relief

Cohort summary CSV uses volume-weighted averages of those metrics.

## Calibration (`pdd_10w`)

| Supplier | Parent WH states | Result |
|----------|------------------|--------|
| Unique Loom SC29707 | CA, SC | Fresno CA → **non_compliant**; Orlando etc. can still be actually-direct |
| Nathan James NV 89434 | NV | Orlando → **sometimes_builds_directs** |
| Edecor Center Inc._1 NJ 08110 | NJ | South Dallas / Diamond Bar → **ghost_warehouses** |
| JLA Home GA 31407 - SV2 | (local scatter) | **no_directs** |

## How to run

```bash
python3 scripts/run_directs_supplier_cohorts.py
```

## Order-level flags + IFR / delivery_rel rollup

Separate query tags every ops, then rolls up supplier counts/% with IFR and `delivery_rel` by bucket (same partition rules).

| Artifact | Link |
|----------|------|
| Shared SQL (rollup default) | `sql/directs_order_flags_supplier_perf.sql` |
| Order-level SQL | `sql/directs_order_level_flags.sql` |
| Runner | `scripts/run_directs_order_flags_perf.py` |
| Supplier rollup CSV | `output/directs/directs_supplier_perf_by_flag.csv` |

```bash
# Supplier rollup (counts, %, IFR, delivery_rel by flag)
python3 scripts/run_directs_order_flags_perf.py

# Order-level flags (optionally filter one SUID)
python3 scripts/run_directs_order_flags_perf.py --order-level --supplier-id 34657
```

## Outputs

| File | Contents |
|------|----------|
| `output/directs/directs_supplier_cohorts.csv` | Full supplier × window (vols + IFR/delivery_rel by bucket) |
| `output/directs/directs_supplier_cohorts_summary.csv` | Cohort counts + weighted IFR/delivery_rel |
| `output/directs/pdd_10w_*.csv` / `msbd_2w_*.csv` | Per-cohort slices |
| `output/directs/directs_supplier_perf_by_flag.csv` | IFR / delivery_rel by candidate bucket |

Key columns: `parent_warehouse_states`, `candidate_vol`, `actually_direct_vol`, `jumbo_vol`, `ghost_candidate_vol`, `noncompliant_candidate_vol`, `relief_vol`, `candidate_partition_ok`, `ifr_*`, `delivery_rel_*`, `direct_cohort`.
