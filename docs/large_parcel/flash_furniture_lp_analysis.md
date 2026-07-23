# Flash Furniture — Large Parcel Performance Analysis

**Analysis period:** Past 3 months (supplier MSBD timebase)  
**Generated:** 2026-07-23  
**Parent supplier:** Flash Furniture  
**Scope:** Large parcel (`LP_dash_ET` + `OTR_Tracking_ET` for OTR)

## Executive summary

Flash Furniture moved **435** large-parcel ops in the last 3 months at **24.4% routing-aware pickup on-time** and **20.0% induction fill rate (IFR)**. Warehouses run **different routing setups**, so pickup is measured differently by site:

| Warehouse | Routing | Pickup metric |
|-----------|---------|---------------|
| Canton, GA | Live Load Pooled | RFPD on-time (`rfpd_early_ontime_SU_new`) |
| Chino, CA | Live Load Pooled | RFPD on-time |
| Olive Branch, MS | OTR | Pickup on/before MSBD (`OTR_Tracking_ET`) |

**334 orders (76.8%)** missed pickup on-time. **353 orders (81.1%)** missed induction on-time.

## Warehouse performance (L3M)

| Warehouse | Routing | Volume | Pickup OT | IFR |
|-----------|---------|-------:|----------:|----:|
| Canton, GA | Live Load Pooled | 181 | 14.4% | 11.6% |
| Olive Branch, MS | OTR | 127 | 20.4% | 11.7% |
| Chino, CA | Live Load Pooled | 126 | 42.0% | 40.5% |
| Columbus, OH | LTL to PP | 1 | 100.0% | 0.0% |

## Key themes — how to improve

### 1. Live Load sites (Canton, Chino): RFPD registration is the bottleneck

- Network RFPD on-time: **26.0%** across Live Load warehouses.
- Carrier pickup on RFPD day is much stronger: **78.8%** — carriers are showing up once freight is staged.
- **Canton (GA)** is the weakest Live Load site at only **14.4%** RFPD on-time despite **91.2%** pickup-within-SLA.
- **Implication:** focus supplier conversation on **earlier RFPD registration / warehouse staging**, not carrier scheduling.

### 2. Olive Branch (MS) OTR: pickups not aligning to MSBD days

- Only **17.5%** of OTR orders have carrier pickup on the exact MSBD.
- **20.4%** picked up on or before MSBD.
- RFPD on-time at **43.1%** — better than Canton but still weak.
- OTR truck execution ratio: **103.0%** (executed / planned trucks).
- **Implication:** review **OTR pickup schedule vs MSBD calendar**, confirm orders are loaded onto the correct daily pickup, and validate `OTR_Tracking_ET` load depart dates against MSBD.

### 3. Pickup-on-time does not guarantee induction

- Some orders pass pickup but still miss IFR — see pickup vs induction gap chart.
- For Live Load, late RFPD pushes induction past MSBD even when carrier pickup SLA is met.

### 4. Chino (CA) is the strongest LP performer

- Highest IFR at **40.5%** with **42.0%** RFPD on-time.
- Use Chino as benchmark for RFPD staging practices at Canton.

## Recommended discussion topics

1. **Canton RFPD process** — what prevents staging on MSBD? Partner Home registration timing?
2. **Olive Branch OTR schedule** — align pickup days to MSBD; review truck loading and `Load_Depart_Date` vs MSBD.
3. **Cross-site playbook** — replicate Chino RFPD staging at Canton.
4. **Weekly KPIs** — track routing-aware pickup on-time and IFR by warehouse.

## Charts

| Chart | File |
|-------|------|
| Pickup on-time by warehouse | [01_pickup_by_warehouse.png](flash_furniture_lp_charts/01_pickup_by_warehouse.png) |
| IFR by warehouse | [02_ifr_by_warehouse.png](flash_furniture_lp_charts/02_ifr_by_warehouse.png) |
| Live Load RFPD vs pickup | [03_live_load_rfpd_vs_pickup.png](flash_furniture_lp_charts/03_live_load_rfpd_vs_pickup.png) |
| OTR pickup & trucks | [04_otr_pickup_and_trucks.png](flash_furniture_lp_charts/04_otr_pickup_and_trucks.png) |
| Weekly trend | [05_weekly_trend.png](flash_furniture_lp_charts/05_weekly_trend.png) |
| Pickup vs induction gap | [06_pickup_induction_gap.png](flash_furniture_lp_charts/06_pickup_induction_gap.png) |

## Data exports

- Full order-level: [flash_furniture_lp_orders_l3m.csv](../../output/flash_furniture_lp/flash_furniture_lp_orders_l3m.csv)
- Late pickup orders: [flash_furniture_lp_late_pickup_l3m.csv](../../output/flash_furniture_lp/flash_furniture_lp_late_pickup_l3m.csv)
