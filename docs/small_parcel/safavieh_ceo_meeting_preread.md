# Safavieh — CEO In-Office Pre-Read

**Meeting:** Safavieh CEO in-office (high-level partnership review)  
**Generated:** 2026-07-28  
**Scope:** Dropship only (`fulfillment_type = 'DS'`) · Rugs STO · Past 3 months · MSBD timebase

**Full package (doc + data + SQL):** [GitHub — Safavieh CEO branch](https://github.com/et844p/O2S/tree/cursor/safavieh-ceo-preread-b7d6)

---

## TL;DR

Safavieh is one of our largest rug suppliers (~**241k** dropship ops L3M across **11 US warehouses**). Today they carry **83.8% fast-badge coverage** (stated order-to-delivery ≤ 5 days) at the parent level, with **82.7% induction fill rate (IFR)**.

**Stacked policy simulation** — if Safavieh commits to **2:00 PM cutoff, zero cushion, and weekend shipping** network-wide:

| Scenario | Fast-badge % | Uplift vs today | Newly fast-badged orders |
|----------|------------:|----------------:|-------------------------:|
| Current | **83.8%** | — | — |
| 2pm cutoff + no cushion | **84.7%** | +1.0 pp | 2,360 |
| **+ Weekend shipping** | **85.9%** | **+2.1 pp** | **5,075** |

Weekend shipping is the **larger incremental lever** on top of cutoff/cushion (+1.1 pp, ~2,715 additional orders). Safavieh currently ships only **46%** of Fri/Sat-placed orders on Sat/Sun L6W — classified as **almost ready** for weekend enablement (30–70% band), not yet at the 70%+ candidate threshold.

**Framing for the CEO:** *"Aligning cutoff, cushion, and weekend pickup is a ~2 pp badge opportunity — but converting that promise requires induction execution at every DC, especially NJ and TX."*

---

## Parent-level snapshot (L3M)

| Metric | Current | Policy only | Full sim (+ weekend) |
|--------|--------:|------------:|---------------------:|
| Volume (distinct ops) | 240,900 | 240,900 | 240,900 |
| Fast-badge % | **83.8%** | **84.7%** | **85.9%** |
| Induction Fill Rate | **82.7%** | 82.7% | 82.7% |

**Simulation uplift decomposition**

| Adjustment applied | Fast-badge % |
|--------------------|-------------:|
| Current | 83.8% |
| Remove cushion only (−1 day when `cushion > 0`) | 84.3% |
| 2pm cutoff only | 84.2% |
| Policy (cushion + 2pm) | **84.7%** |
| **+ Weekend shipping** | **85.9%** |

- **0** orders lose fast-badge status under any scenario.

---

## Badging simulation methodology

Simulated stated speed is computed order-by-order, then rolled up at the **parent (`Safavieh`)** level. Adjustments stack:

```
sim_o2d_stated = o2d_stated
  − 1  if cushion > 0 on the order
  − 1  if order placed before 2:00 PM local
         AND not pre-cutoff (o2sumsbd > 0)
         AND warehouse cutoff < 2:00 PM (or null)
  − 1  if Fri/Sat placed (order_dow 5 or 6)
         AND not inducted Sat/Sun (induction_dow_adj not 6 or 7)

sim_fast_badge = 1 if sim_o2d_stated ≤ 5, else 0
```

| Flag | Definition |
|------|------------|
| Pre-cutoff | `o2sumsbd = 0` — order before warehouse cutoff → same-day MSBD |
| Weekend shipped | `induction_dow_adj IN (6, 7)` — inducted Saturday or Sunday |
| Fri/Sat placed | `order_dow IN (5, 6)` |

**Important:** This simulates **what the badge would say**, not whether Safavieh can actually deliver that speed. IFR and delivery reliability must move in parallel with policy changes.

---

## Weekend shipping analysis

### Parent L6W (last 6 weeks)

| Metric | Value |
|--------|------:|
| Total volume | 109,019 ops |
| Fri/Sat placed volume | 29,285 ops (**27%** of volume) |
| Fri/Sat inducted Sat/Sun | 13,514 ops |
| **% Fri/Sat shipped on weekend** | **46.1%** |

**Cohort:** `almost_ready` (30–70% weekend ship rate). Not yet a weekend-shipping candidate (requires ≥70% + IFR >85%).

### Why weekend shipping moves the badge

Fri/Sat-placed orders that **do** ship on weekends average **4.7 days** stated O2D and **80.7%** fast-badge rate. Those that **don't** average **5.1 days** and **75.3%** fast-badge — a full day slower on MSBD window (`o2sumsbd` ~2.0 vs ~1.0).

Under full simulation, **30,759** L3M orders (Fri/Sat placed, weekday inducted) would gain a 1-day stated-speed reduction if weekend shipping were enabled.

### Weekend ship rate by site (L6W)

| Location | Fri/Sat vol | % shipped Sat/Sun | Fri/Sat not weekend (opportunity) |
|----------|------------:|------------------:|----------------------------------:|
| Baytown, TX | 5,362 | 45.2% | 2,839 |
| Whitestown, IN | 5,314 | 42.8% | 2,835 |
| Lebanon, NJ | 3,519 | 45.9% | 1,824 |
| Riverside, CA | 3,318 | 43.4% | 1,847 |
| Savannah, GA | 2,779 | 48.4% | 1,418 |
| Midway, GA | 2,343 | **54.8%** | 976 |
| Patterson, CA | 2,298 | 43.5% | 1,262 |
| Flemington, NJ | 1,865 | **58.1%** | 763 |
| Easton, PA | 1,023 | 46.7% | 495 |
| Port Wentworth, GA | 661 | **38.4%** | 385 |

**Best weekend performers:** Flemington NJ (58%), Midway GA (55%). **Weakest:** Port Wentworth GA (38%) — also a site with midnight cutoff today.

### Full simulation fast-badge by site (L6W)

| Location | Current | Policy only | Full (+ weekend) |
|----------|--------:|------------:|-----------------:|
| Baytown, TX | 91.9% | 92.5% | **94.0%** |
| Whitestown, IN | 90.3% | 91.1% | **91.7%** |
| Port Wentworth, GA | 87.0% | 91.3% | **92.3%** |
| Savannah, GA | 89.7% | 90.5% | **91.1%** |
| Midway, GA | 89.9% | 90.6% | **91.5%** |
| Flemington, NJ | 83.9% | 84.3% | **85.2%** |
| Lebanon, NJ | 80.0% | 83.3% | **83.6%** |
| Riverside, CA | 71.8% | 71.8% | **74.0%** |
| Patterson, CA | 61.6% | 61.7% | **63.3%** |

---

## Warehouse network (L3M)

All sites run **24-hour SP lead time**. Cutoff and cushion settings vary today:

| Location | Cutoff | Volume | IFR | Current fast | Policy sim | Full sim |
|----------|--------|-------:|----:|-------------:|-----------:|---------:|
| Whitestown, IN | 12:00 PM | 43,338 | 85.8% | 90.0% | 90.8% | — |
| Baytown, TX | 2:00 PM | 43,064 | 80.2% | 90.8% | 91.1% | — |
| Lebanon, NJ | 8:00 AM | 32,973 | **73.5%** | 80.5% | 83.3% | — |
| Riverside, CA | 2:00 PM | 25,841 | 92.6% | 72.3% | 72.3% | — |
| Savannah, GA | 1:00 PM | 21,437 | 81.8% | 89.6% | 90.3% | — |
| Midway, GA | 11:00 AM | 17,811 | 86.4% | 88.6% | 89.4% | — |
| Patterson, CA | 2:00 PM | 17,761 | 89.8% | 60.6% | 60.7% | — |
| Flemington, NJ | 2:00 PM | 13,810 | 75.5% | 83.4% | 83.7% | — |
| Easton, PA | Midnight* | 10,341 | 75.8% | 80.3% | 83.4% | — |
| Port Wentworth, GA | Midnight* | 6,333 | 73.6% | 87.9% | 91.9% | — |
| Carlisle, PA | 2:00 PM | 5,179 | 89.6% | 91.4% | 91.4% | — |

\* `00:00:00` cutoff — effectively no same-day processing window.

---

## Key themes for the CEO conversation

### 1. Three levers, one package

| Lever | Badge uplift (parent) | Operational ask |
|-------|----------------------:|-------------------|
| Zero cushion | +0.5 pp | Remove LT padding in system settings |
| 2:00 PM cutoff everywhere | +0.5 pp | Extend processing window at early-cutoff sites |
| Weekend shipping | +1.1 pp | Sat/Sun FedEx pickup at all DCs |
| **Combined** | **+2.1 pp** | Full network speed alignment |

### 2. Induction performance is still the binding constraint

IFR at **82.7%** — ~18% of orders miss supplier MSBD induction. Weak sites: Lebanon NJ (73.5%), Port Wentworth GA (73.6%), Flemington NJ (75.5%), Baytown TX (80.2%). Weekend shipping and 2pm cutoff require **carrier pickup alignment**, not just policy changes.

### 3. Geography limits badge at CA nodes

Riverside and Patterson have strong IFR but ~60–72% fast badge due to transit distance. Policy/weekend changes help marginally (+2–3 pp at Riverside under full sim).

---

## Proposed commitments (discussion framework)

| Safavieh commits | Wayfair commits |
|------------------|-----------------|
| **2:00 PM cutoff** at every US warehouse | Update LT/cushion settings; confirm badge impact |
| **Zero cushion** network-wide | Monitor IFR weekly during transition |
| **Weekend shipping** — Sat/Sun induction for Fri/Sat orders at all DCs | Enable weekend-shipping flag when ≥70% rate sustained |
| FedEx pickup aligned to 2pm + weekend windows | Escalation path for carrier issues |
| Weekly IFR + weekend ship rate by DC | Share network speed targets and badge impact |

---

## Questions to drive in the meeting

1. Will Safavieh **standardize 2:00 PM cutoff** across all US warehouses?
2. Can they commit to **zero cushion** and **weekend shipping** network-wide?
3. What FedEx **pickup schedule** exists today — is Sat/Sun pickup feasible at NJ and TX nodes?
4. What is driving **NJ and TX IFR** — staffing, carrier timing, or volume?
5. Which sites can reach **70% Fri/Sat weekend ship rate** first (Flemington, Midway already closest)?

---

## Data & files

| Resource | Link |
|----------|------|
| **This pre-read** | [safavieh_ceo_meeting_preread.md](https://github.com/et844p/O2S/blob/cursor/safavieh-ceo-preread-b7d6/docs/small_parcel/safavieh_ceo_meeting_preread.md) |
| **Badging scenario summary (CSV)** | [safavieh_badging_scenarios.csv](https://github.com/et844p/O2S/blob/cursor/safavieh-ceo-preread-b7d6/output/safavieh/safavieh_badging_scenarios.csv) |
| **Warehouse weekend + badging (CSV)** | [safavieh_warehouse_weekend_badging_l6w.csv](https://github.com/et844p/O2S/blob/cursor/safavieh-ceo-preread-b7d6/output/safavieh/safavieh_warehouse_weekend_badging_l6w.csv) |
| **Simulation SQL** | [safavieh_badging_simulation.sql](https://github.com/et844p/O2S/blob/cursor/safavieh-ceo-preread-b7d6/sql/safavieh_badging_simulation.sql) |
| **HVE column reference** | [HVE_perf_Monitoring.md](https://github.com/et844p/O2S/blob/cursor/safavieh-ceo-preread-b7d6/docs/small_parcel/HVE_perf_Monitoring.md) |
| **Weekend shipping methodology** | [weekend_shipping_supplier_analysis.md](https://github.com/et844p/O2S/blob/cursor/safavieh-ceo-preread-b7d6/docs/small_parcel/weekend_shipping_supplier_analysis.md) |
| **Branch (all files)** | [cursor/safavieh-ceo-preread-b7d6](https://github.com/et844p/O2S/tree/cursor/safavieh-ceo-preread-b7d6) |
| **Pull request** | [PR #16](https://github.com/et844p/O2S/pull/16) |

### Scenario summary (from CSV)

| Scenario | Volume | Fast-badge % | Newly fast |
|----------|-------:|------------:|-----------:|
| Current | 240,900 | 83.76% | — |
| Policy (2pm + no cushion) | 240,900 | 84.74% | 2,360 |
| Full (+ weekend shipping) | 240,900 | **85.87%** | **5,075** |

---

*Note: Analysis excludes CastleGate (`fulfillment_type = 'CG'`). Badge simulation models stated speed only; actual delivery performance requires IFR and delivery reliability improvement in parallel.*
