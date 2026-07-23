# Flash Furniture — Induction Performance Analysis

**Analysis period:** Past 3 months (MSBD timebase)  
**Generated:** 2026-07-23  
**Parent supplier:** Flash Furniture  
**Scope:** Dropship only (`fulfillment_type = 'DS'`)

## Executive summary

Flash Furniture moved **22,580** dropship small-parcel ops across three warehouses in the last 3 months at **56.3% network IFR** — well below the 85% target. **9,873 orders (43.7%)** missed supplier MSBD induction, with **6,076** of those only **1 day late**.

The primary issue is **not label creation** — labels are printed on time in >97% of orders. The gap is **carrier induction after label print**: only ~50% of orders are inducted within 1 day of label, and late orders average just 0% same-day label-to-induction.

**Performance has deteriorated sharply in July 2026**, especially at Canton and Olive Branch.

## Warehouse performance (L3M)

| Warehouse | Volume | IFR |
|-----------|-------:|----:|
| Canton, GA | 11,652 | 61.7% |
| Olive Branch, MS | 8,491 | 49.1% |
| Chino, CA | 2,437 | 55.2% |

## Recent trend (last 4 MSBD weeks)

| Warehouse | Volume | IFR |
|-----------|-------:|----:|
| Canton, GA | 2,657 | 31.7% |
| Olive Branch, MS | 1,918 | 33.6% |
| Chino, CA | 420 | 42.1% |

## Key themes — why volume is not inducting on time

### 1. Label-to-induction gap (primary driver)
- Labels are created quickly: **96.9%** of orders have a label within 1 day of order.
- Carrier induction lags: only **49.5%** inducted within 1 day of label (network-wide).
- For **late orders**, only **0.2%** get same-day label-to-induction vs **5.6%** for on-time orders.
- **Implication:** warehouse is largely printing labels on MSBD, but **FedEx pickup / first scan is delayed 1–2 days**.

### 2. 1-day-late concentration
- The largest late bucket is **1 day past MSBD** (Canton, GA: 2,703 | Olive Branch, MS: 2,520 | Chino, CA: 853).
- This is consistent with **next-day pickup failure** rather than multi-day warehouse processing delays.

### 3. Olive Branch (MS) is the weakest site
- Lowest L3M IFR at **49.1%**.
- Mon/Tue order placement IFR is weakest — suggests start-of-week pickup cadence issues.
- Station: **OLIVE BRANCH LOCAL**.

### 4. Canton (GA) volume leader with recent collapse
- Highest volume at **11,652 ops**; July IFR well below L3M average.
- Station: **MARIETTA LOCAL**.

### 5. Weekend induction gap
- Fri/Sat placed orders are **not** getting weekend carrier induction at scale.
- Weekend shipping enablement or Saturday pickup alignment could recover meaningful volume.

### 6. Not a lead-time / cushion / capacity issue
- All sites on **24hr SP LT** with low cushion and negligible capacity padding.

## Recommended discussion topics for Flash Furniture meeting

1. **FedEx pickup schedule & manifest timing** — align label print cutoff with guaranteed daily pickup.
2. **July deterioration** — what changed operationally (staffing, cutoff, carrier switch, volume spike)?
3. **Olive Branch Mon/Tue performance** — dedicated pickup or earlier weekend processing.
4. **Weekend induction** — evaluate Saturday pickup or adjusted MSBD for Fri/Sat orders.
5. **Same-day label-to-induction KPI** — track `label2I_0_adj` weekly by warehouse.

## Charts

| Chart | File |
|-------|------|
| IFR by warehouse | [01_ifr_by_warehouse.png](flash_furniture_charts/01_ifr_by_warehouse.png) |
| Weekly IFR trend | [02_weekly_ifr_trend.png](flash_furniture_charts/02_weekly_ifr_trend.png) |
| Late bucket breakdown | [03_late_bucket_breakdown.png](flash_furniture_charts/03_late_bucket_breakdown.png) |
| Label vs induction timing | [04_label_vs_induction_timing.png](flash_furniture_charts/04_label_vs_induction_timing.png) |
| IFR by order DOW | [05_ifr_by_order_dow.png](flash_furniture_charts/05_ifr_by_order_dow.png) |
| Weekend induction gap | [06_weekend_induction_gap.png](flash_furniture_charts/06_weekend_induction_gap.png) |

## Data exports

- Full order-level: [https://github.com/et844p/O2S/blob/main/output/flash_furniture/flash_furniture_orders_l3m.csv](https://github.com/et844p/O2S/blob/main/output/flash_furniture/flash_furniture_orders_l3m.csv)
- Late orders only: [https://github.com/et844p/O2S/blob/main/output/flash_furniture/flash_furniture_late_orders_l3m.csv](https://github.com/et844p/O2S/blob/main/output/flash_furniture/flash_furniture_late_orders_l3m.csv)