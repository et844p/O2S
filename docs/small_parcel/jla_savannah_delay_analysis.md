# JLA Home Savannah — Warehouse vs FedEx Delay Analysis

**Analysis period:** July 2026 (MSBD timebase)  
**Generated:** 2026-08-04  
**Scope:** JLA Home Savannah dropship only (`fulfillment_type = 'DS'`)  
**Warehouses:** SV2 (conveyables, 550 Northport Pkwy) · SV3 (non-conveyables, 311 International Trade Pkwy)

## Executive summary

JLA Savannah moved **24,881** dropship ops in July at **92.0% network IFR**. The performance gap is almost entirely at **SV3 (non-conveyables)** — **76.1% IFR** vs **97.4%** at SV2 (conveyables).

Of **1,989 late orders**, **1,669 (84%)** were **labeled by 2pm on MSBD** (eligible for the 2:30pm last trailer) but **not inducted on time** — pointing to **FedEx pickup/first-scan delays**, not warehouse labeling.

A sharp deterioration hit **SV3 on MSBD July 27–28** (1,500 ops, **35.3% IFR**). SV2 was largely unaffected those days.

## Timezone check — `event_datetime`

**`event_datetime` is Eastern Time (ET), not California/Pacific time.**

- Savannah warehouses operate 6am–3:30pm ET; last trailer ~2:30pm ET.
- The table's `label_by_msbd_2` flag (label by 2pm on MSBD) aligns **100.0%** with parsing `event_datetime` as ET (label before MSBD, or on MSBD with hour < 14).
- A Pacific-time interpretation only matches ~93.8% of flags — confirming ET.

**Operational rule used:** Labels with `label_by_msbd_2 = 1` (or `label_hour_et < 14` on MSBD) should have made the last trailer.

## Warehouse performance (July 2026)

| Warehouse | Volume | IFR | Late orders | FedEx-driven late | WH-driven late (after 2pm) |
|-----------|-------:|----:|------------:|------------------:|---------------------------:|
| SV2 (conveyables) | 18,544 | 97.4% | 476 | 288 (61%) | 188 |
| SV3 (non-conveyables) | 6,337 | 76.1% | 1,513 | 1,381 (91%) | 132 |

## Attribution methodology

| Category | Logic |
|----------|-------|
| **WH: label after 2pm MSBD** | `label_by_msbd_2 = 0` — missed trailer cutoff |
| **FedEx: label on time, inducted next day** | Labeled by 2pm but `label2I_1_adj = 1` and late MSBD — missed pickup / next-day scan |
| **FedEx: label on time, inducted 2+ days** | Labeled by 2pm but induction 2+ days after label |
| **On time** | `inducted_on_time_or_early = 1` |

## Key findings

### 1. SV3 non-conveyables is the problem site (FedEx-driven)

- **91% of SV3 late orders** had labels by 2pm MSBD but missed induction deadline.
- Largest bucket: **1,055 orders** labeled on time, inducted **next day** (1-day FedEx gap).
- Secondary: **326 orders** with **2+ day** label-to-induction gap.
- Only **132 orders (9% of SV3 late)** are warehouse-driven (label after 2pm).

### 2. SV2 conveyables is healthy

- **97.4% IFR** — FedEx delays exist but at much lower volume (288 vs 1,381 at SV3).
- WH-driven late is similar in count (188) but tiny as a % of volume.

### 3. July 27–28 crisis (SV3 only)

| MSBD | SV3 Volume | SV3 IFR | FedEx late | WH late |
|------|----------:|--------:|-----------:|--------:|
| 2026-07-27 | 1,006 | 42.3% | 560 | 20 |
| 2026-07-28 | 494 | 21.1% | 298 | 92 |
| 2026-07-29+ | — | ~98% | — | — |

SV3 recovered to **>98% IFR** from July 29 onward. SV2 held **>93% IFR** through the crisis window.

### 4. Label batch timing on MSBD

SV3 labels on MSBD day cluster at **~5am ET** (bulk print). Late vs on-time orders share this pattern — the issue is **not** missing the 2pm cutoff for most orders; it's **carrier pickup after labels are ready**.

## Charts

| Chart | File |
|-------|------|
| IFR by warehouse | [01_ifr_by_warehouse.png](jla_savannah_charts/01_ifr_by_warehouse.png) |
| Weekly IFR trend | [02_weekly_ifr_trend.png](jla_savannah_charts/02_weekly_ifr_trend.png) |
| Late order attribution | [03_late_attribution.png](jla_savannah_charts/03_late_attribution.png) |
| SV3 daily IFR | [04_sv3_daily_ifr.png](jla_savannah_charts/04_sv3_daily_ifr.png) |
| SV3 label hour distribution | [05_sv3_label_hour.png](jla_savannah_charts/05_sv3_label_hour.png) |

## Data exports

- Full order-level: `output/jla_savannah/jla_savannah_orders_july2026.csv`
- Late orders only: `output/jla_savannah/jla_savannah_late_orders_july2026.csv`
- Attribution summary: `output/jla_savannah/jla_savannah_attribution_summary.csv`

## Recommended next steps

1. **FedEx Savannah pickup at SV3** — what changed July 27–28 for non-conveyables? Trailer capacity, missed pickup, hub backlog?
2. **SV2 vs SV3 pickup cadence** — same FedEx station (SAVANNAH) but very different outcomes; are conveyables and non-conveyables on separate pickup routes/trailers?
3. **Label-to-induction SLA** — track `label2I_0_adj` weekly at SV3; target same-day induction for labels printed before 2pm.
4. **July 28 WH spike** — 92 SV3 orders labeled after 2pm (unusual vs ~20/day on 7/27); staffing or cutoff issue worth confirming with warehouse ops.
