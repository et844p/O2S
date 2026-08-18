# Directs Supplier Cohorts

Generated: 2026-08-18

Classifies dropship (`fulfillment_type = 'DS'`) candidates into exclusive buckets.

## Lookbacks

| Window | Timebase | Length | Min volume |
|--------|----------|--------|------------|
| `pdd_10w` | `promised_delivery_end_range_date_at_order` | 10 weeks | 50 ops |
| `msbd_2w` | `msbd_su` | 2 weeks | 20 ops |

## Step 1 — Candidate

Distance conditions only (raw columns; do **not** trust `distance_assignedhub_actualhub_200_plus`):

1. `assignedhub_notequal_actualhub_flag = 1` (wrong hub)
2. `distance_assignedhub_customer >= 400`
3. `distance_assignedhub_actualhub >= 200`

## Step 2 — Exclusive buckets under candidate

Priority order (first match wins):

| Bucket | Rule |
|--------|------|
| **Misshipping** | Parent has another warehouse in the induction state |
| **Ghost warehouse** | Persistent far hub (≥10% supplier vol, most weeks) where parent has **no** warehouse in that state (day-in/day-out undeclared location) |
| **Jumbo** | `direct_gain < 0.4` (null treated as &lt; 0.4) |
| **Direct** | `direct_gain >= 0.4` **and** material volume at that hub (see below) |
| **Sparse far** | `direct_gain >= 0.4` but hub fails materiality — noise / data quirks / one-off far hubs (e.g. tiny Salt Lake scans) |

### Material direct hub

A hub counts as intentional direct volume only if either:

1. `hub_candidate_vol >= GREATEST(20, CEIL(0.3% × supplier total_vol))`, or
2. `hub_share >= 0.5%` **and** `hub_candidate_vol >= 10`

This keeps multi-hub directors (Kingston, Modway, etc.) while demoting sub-scale far hubs that are not meaningful directs.

```
candidate_vol = direct + sparse_far + jumbo + ghost + misshipping
```

`candidate_partition_ok` is true when that identity holds.

## Supplier cohorts (priority order)

| Cohort | Meaning |
|--------|---------|
| `ghost_warehouses` | Any ghost-bucket volume |
| `consistently_builds_directs` | Material direct weeks nearly every week (`direct_vol` ≥ 20 on pdd_10w / ≥ 10 on msbd_2w) |
| `sometimes_builds_directs` | Material direct in some weeks (same `direct_vol` floor) |
| `misshipping` | Sibling-state candidates only (no material direct) |
| `no_directs` | No material direct / ghost / misshipping (sparse_far alone does **not** qualify) |

## Performance columns

IFR (`inducted_on_time_or_early`) and `delivery_rel` for overall, candidates, and each bucket (including `sparse_far`). Cohort summary uses volume-weighted averages.

## How to run

```bash
python3 scripts/run_directs_supplier_cohorts.py
python3 scripts/run_directs_order_flags_perf.py
```

## Outputs

| File | Contents |
|------|----------|
| `output/directs/directs_supplier_cohorts.csv` | Full supplier × window |
| `output/directs/directs_supplier_cohorts_summary.csv` | Cohort counts + weighted IFR/delivery_rel |
| `output/directs/pdd_10w_*.csv` / `msbd_2w_*.csv` | Per-cohort slices |
| `output/directs/directs_supplier_perf_by_flag.csv` | IFR / delivery_rel by bucket |

## Note on undeclared warehouses

Fragmented shipping from an undeclared location (e.g. Loloi TX → Tracy/Rialto CA, each hub under the ghost 10% bar) can still land in **direct** if a hub clears materiality. Register the warehouse under the parent (→ misshipping) or concentrate volume at one hub (→ ghost) to reclassify. Tiny far hubs like Salt Lake fall into **sparse_far**.
