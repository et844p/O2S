# Directs Supplier Cohorts

Generated: 2026-08-10

Classifies dropship (`fulfillment_type = 'DS'`) suppliers by how they show up on direct-eligible induction patterns.

## Lookbacks

| Window | Timebase | Length | Min volume |
|--------|----------|--------|------------|
| `pdd_10w` | `promised_delivery_end_range_date_at_order` | 10 weeks | 50 ops |
| `msbd_2w` | `msbd_su` | 2 weeks | 20 ops |

## Direct-eligible definition

An order is **direct-eligible** when all of:

1. `assignedhub_notequal_actualhub_flag = 1` (excludes missing actual hub cases from eligibility)
2. `distance_assignedhub_customer_400_plus = 1`
3. `distance_assignedhub_actualhub_200_plus = 1`

Orders with no `actual_induction_hub_id` are **not** eligible; their volume is reported as `missing_actual_hub_vol` (about **3.0%** of pdd_10w volume).

## True directs vs ghost warehouses

Flagged directs are split using two signals:

| Signal | Rule |
|--------|------|
| **Batched / same-time true direct** | 2+ direct-eligible ops at the same supplier + actual hub + induction day |
| **Ghost hub** | Actual hub is far from assigned (≥200 mi on ≥80% of that hub’s volume), present in ≥50% of supplier weeks (min 2), and ≥10% of supplier volume |

Ghost hubs take priority: if a supplier has them, they land in `ghost_warehouses_no_directs` even if residual far volume remains.

## Cohorts

| Cohort | Meaning |
|--------|---------|
| `consistently_builds_directs` | Batched true directs in every week (or all-but-one when ≥4 weeks) |
| `sometimes_builds_directs` | Batched true directs in some weeks, not nearly all |
| `ghost_warehouses_no_directs` | Persistent far hubs look like directs but behave like unregistered warehouses |
| `no_directs` | No batched true directs and no ghost-hub pattern |

### Calibration examples

| Supplier | Expected | Result (`pdd_10w`) |
|----------|----------|--------------------|
| Edecor Center Inc._1 NJ 08110 | Ghost warehouses (South Dallas / Diamond Bar), not intentional directs | `ghost_warehouses_no_directs` — South Dallas Rsf (TX) 21%; Diamond Bar Rsf (CA) 16% |
| Nathan James NV 89434 | Sometimes builds directs (e.g. FL batches, not every week) | `sometimes_builds_directs` — true directs in 9/11 weeks |

## Results summary

### 10-week promised delivery (`pdd_10w`)

| Cohort | Suppliers | Volume | Direct-eligible | True direct | Ghost hub vol | Missing actual hub |
|--------|-----------|--------|-----------------|-------------|---------------|--------------------|
| sometimes_builds_directs | 6,484 | 2,478,150 | 476,135 | 279,249 | 0 | 70,847 |
| consistently_builds_directs | 2,745 | 3,813,991 | 1,821,980 | 1,626,197 | 0 | 54,571 |
| ghost_warehouses_no_directs | 1,963 | 799,818 | 417,187 | 190,081 | 258,399 | 10,918 |
| no_directs | 1,538 | 338,122 | 7,480 | 0 | 0 | 88,787 |

### 2-week MSBD (`msbd_2w`)

| Cohort | Suppliers | Volume | Direct-eligible | True direct | Ghost hub vol | Missing actual hub |
|--------|-----------|--------|-----------------|-------------|---------------|--------------------|
| consistently_builds_directs | 3,906 | 834,738 | 351,796 | 335,467 | 0 | 26,432 |
| no_directs | 2,886 | 320,886 | 1,964 | 0 | 0 | 36,928 |
| ghost_warehouses_no_directs | 1,572 | 201,523 | 101,137 | 49,756 | 74,421 | 5,930 |
| sometimes_builds_directs | 1,073 | 278,423 | 74,166 | 70,143 | 0 | 9,411 |

Short-window “consistent” means both weeks with volume had batched true directs; with only two weeks that bar is easier to clear than over 10 weeks.

## How to run

```bash
python3 scripts/run_directs_supplier_cohorts.py
python3 scripts/run_directs_supplier_cohorts.py --window pdd_10w --cohort ghost_warehouses_no_directs
```

## Outputs

| File | Contents |
|------|----------|
| `output/directs/directs_supplier_cohorts.csv` | Full supplier × window results |
| `output/directs/directs_supplier_cohorts_summary.csv` | Cohort counts / volumes |
| `output/directs/pdd_10w_*.csv` / `msbd_2w_*.csv` | Per-window cohort slices |

Useful columns: `true_direct_vol`, `weeks_with_true_direct`, `true_direct_by_week`, `top_true_direct_hubs`, `ghost_hubs`, `ghost_share`, `missing_actual_hub_vol`, `avg_gain_on_direct_eligible`, distances, IFR, SRM.

## Notes / caveats

- Ghost priority means a supplier with both persistent unregistered far hubs **and** intermittent true directs is labeled ghost-only.
- Distributed far volume across many hubs each under 10% share will not trigger ghost and may land in sometimes/consistent instead.
- Large `no_directs` rows with high `missing_actual_hub_vol` (e.g. FBA / virtual WHs) are visibility gaps, not proof of local-only induction.
