# Directs Supplier Cohorts

Generated: 2026-08-11

Classifies dropship (`fulfillment_type = 'DS'`) suppliers by splitting **direct candidates** into actually direct vs ghost warehouse vs non-compliant shipping.

## Lookbacks

| Window | Timebase | Length | Min volume |
|--------|----------|--------|------------|
| `pdd_10w` | `promised_delivery_end_range_date_at_order` | 10 weeks | 50 ops |
| `msbd_2w` | `msbd_su` | 2 weeks | 20 ops |

## Step 1 — Direct candidate

Distance conditions only (raw columns; do **not** trust `distance_assignedhub_actualhub_200_plus`):

1. `assignedhub_notequal_actualhub_flag = 1`
2. `distance_assignedhub_customer >= 400`
3. `distance_assignedhub_actualhub >= 200`

## Step 2 — Split candidates

Uses **parent warehouse states** (distinct `state_name` of all DS SUIDs under `parent_suid`) and **induction timing** (grouped = 2+ candidate ops at same actual hub + day).

| Bucket | Rule |
|--------|------|
| **Actually direct** | Grouped batches at a far hub, recurring (≥2 weeks), **1–10%** of supplier vol; not systematic sibling cross-ship |
| **Ghost warehouse** | Far hub ≥10% of supplier vol, most weeks, and parent has **no** warehouse in that induction state |
| **Non-compliant** | Candidate in a state where parent **has** another warehouse (sibling) — systematic (most weeks) or sporadic / weakly grouped misships |

## Supplier cohorts (priority order)

| Cohort | Meaning |
|--------|---------|
| `ghost_warehouses` | Persistent unregistered far hubs (or actually-direct share ≥10%) |
| `consistently_builds_directs` | Actually-direct weeks nearly every week |
| `sometimes_builds_directs` | Actually-direct in some weeks |
| `non_compliant_shipping` | Sibling-state candidates only (no material actually-direct) |
| `no_directs` | No material candidate split into the above |

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

## Outputs

| File | Contents |
|------|----------|
| `output/directs/directs_supplier_cohorts.csv` | Full supplier × window |
| `output/directs/directs_supplier_cohorts_summary.csv` | Cohort counts |
| `output/directs/pdd_10w_*.csv` / `msbd_2w_*.csv` | Per-cohort slices |

Key columns: `parent_warehouse_states`, `candidate_vol`, `actually_direct_vol`, `top_actually_direct_hubs`, `ghost_hubs`, `noncompliant_hubs`, `noncompliant_candidate_vol`, `direct_cohort`.
