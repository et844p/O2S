# Directs Supplier Cohorts

Generated: 2026-08-11

Classifies dropship (`fulfillment_type = 'DS'`) candidates into four exclusive buckets.

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
| **Ghost warehouse** | Persistent far hub (≥10% supplier vol, most weeks) with **scattered** induction timing (avg &lt; 2 candidate ops per induction day) |
| **Jumbo** | `direct_gain < 0.4` (null treated as &lt; 0.4) |
| **Direct** | Everything else (`direct_gain >= 0.4`) |

```
candidate_vol = direct + jumbo + ghost + misshipping
```

`candidate_partition_ok` is true when that identity holds.

No separate “grouped candidate” filter — batching is only used to distinguish ghost (scattered timing) from other far hubs.

## Supplier cohorts (priority order)

| Cohort | Meaning |
|--------|---------|
| `ghost_warehouses` | Any ghost-bucket volume |
| `consistently_builds_directs` | Direct weeks nearly every week |
| `sometimes_builds_directs` | Direct in some weeks |
| `misshipping` | Sibling-state candidates only (no material direct) |
| `no_directs` | No material direct / ghost / misshipping |

## Performance columns

IFR (`inducted_on_time_or_early`) and `delivery_rel` for overall, candidates, and each bucket. Cohort summary uses volume-weighted averages.

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
