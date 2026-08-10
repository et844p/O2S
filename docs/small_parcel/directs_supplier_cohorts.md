# Directs Supplier Cohorts

Generated: 2026-08-10

Classifies dropship (`fulfillment_type = 'DS'`) suppliers by intentional directs vs ghost warehouses vs neither.

## Lookbacks

| Window | Timebase | Length | Min volume |
|--------|----------|--------|------------|
| `pdd_10w` | `promised_delivery_end_range_date_at_order` | 10 weeks | 50 ops |
| `msbd_2w` | `msbd_su` | 2 weeks | 20 ops |

## Potential direct (distance only)

An order is a **potential direct** when all of:

1. `assignedhub_notequal_actualhub_flag = 1`
2. `distance_assignedhub_customer >= 400`
3. `distance_assignedhub_actualhub >= 200`

Use the **raw distance columns**, not `distance_assignedhub_actualhub_200_plus` (unreliable for near-hub ID mismatches).

Potential directs are then split using induction timing / hub patterns.

## True directs vs ghost warehouses

| Signal | Rule |
|--------|------|
| **Batched potential** | 2+ potential-direct ops at same supplier + actual hub + induction day |
| **Ghost hub** | Far hub in ≥50% of weeks (min 2) and ≥10% of supplier volume |
| **Direct-building hub** | Recurring (≥2 weeks) batched far hub at **1–10%** of supplier volume |
| **True directs** | Batched potential at direct-building hubs only |

Intentional directing should stay under ~**10%** of supplier volume. If `true_direct_share >= 10%`, classify as ghost-scale. Scattered far scans under 1% per hub (e.g. network noise) do not count as building directs.

## Cohorts

| Cohort | Meaning |
|--------|---------|
| `consistently_builds_directs` | True directs in every week (or all-but-one when ≥4 weeks) |
| `sometimes_builds_directs` | True directs in some weeks only |
| `ghost_warehouses_no_directs` | Persistent ≥10% far hubs, or true-direct share ≥10% |
| `no_directs` | No intentional direct-building hubs |

### Calibration examples

| Supplier | Expected | Result (`pdd_10w`) |
|----------|----------|--------------------|
| Edecor Center Inc._1 NJ 08110 | Ghost (South Dallas / Diamond Bar) | `ghost_warehouses_no_directs` |
| Nathan James NV 89434 | Sometimes (e.g. Orlando batches, limited share) | `sometimes_builds_directs` |
| JLA Home GA 31407 - SV2 | Not directs — far scans are scatter, not a 1–10% recurring hub | `no_directs` |

## Results summary

Updated on each run via `output/directs/directs_supplier_cohorts_summary.csv`.

## How to run

```bash
python3 scripts/run_directs_supplier_cohorts.py
python3 scripts/run_directs_supplier_cohorts.py --window pdd_10w --cohort sometimes_builds_directs
```

## Outputs

| File | Contents |
|------|----------|
| `output/directs/directs_supplier_cohorts.csv` | Full supplier × window results |
| `output/directs/directs_supplier_cohorts_summary.csv` | Cohort counts / volumes |
| `output/directs/pdd_10w_*.csv` / `msbd_2w_*.csv` | Per-window cohort slices |

Useful columns: `potential_direct_vol`, `potential_direct_share`, `true_direct_vol`, `true_direct_share`, `weeks_with_true_direct`, `true_direct_by_week`, `top_true_direct_hubs`, `ghost_hubs`, `within_200_vol`, `pct_within_200_of_assigned`, `missing_actual_hub_vol`.
