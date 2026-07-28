# Safavieh — CEO In-Office Pre-Read

**Meeting:** Safavieh CEO in-office (high-level partnership review)  
**Generated:** 2026-07-28  
**Scope:** Dropship only (`fulfillment_type = 'DS'`) · Rugs STO · Past 3 months · MSBD timebase

---

## TL;DR

Safavieh is one of our largest rug suppliers (~**241k** dropship ops L3M across **11 US warehouses**). Today they carry **83.8% fast-badge coverage** (stated order-to-delivery ≤ 5 days) at the parent level, with **82.7% induction fill rate (IFR)**.

**The policy conversation:** If Safavieh standardizes to **24-hour small-parcel lead time, 2:00 PM same-day cutoff, and zero cushion** across all warehouses, simulated fast-badge coverage rises to **84.7%** (+**1.0 pp**, ~**2,360** additional fast-badged orders). Badge uplift is real but modest — the bigger customer experience lever is **operational execution** (induction on MSBD), especially at NJ and TX sites.

**Framing for the CEO:** *"You're already close on speed promise — aligning cutoff and cushion policy unlocks a small badge lift, but hitting induction targets at every DC is what converts promise into delivery."*

---

## Parent-level snapshot (L3M)

| Metric | Current | Simulated (2pm + no cushion) |
|--------|--------:|-----------------------------:|
| Volume (distinct ops) | 240,900 | 240,900 |
| Fast-badge % (`o2d_stated ≤ 5`) | **83.8%** | **84.7%** |
| Avg stated O2D (days) | 4.5 | 4.2 |
| Induction Fill Rate | **82.7%** | 82.7% (unchanged — ops metric) |

**Simulation uplift decomposition**

| Adjustment applied | Fast-badge % |
|--------------------|-------------:|
| Current | 83.8% |
| Remove cushion only (−1 day when `cushion > 0`) | 84.3% |
| 2pm cutoff only (see rules below) | 84.2% |
| Both adjustments | **84.7%** |

- **2,360** orders would gain fast-badge status; **0** would lose it under this scenario.

---

## Badging simulation methodology

Simulated stated speed is computed order-by-order, then rolled up at the **parent (`Safavieh`)** level:

```
sim_o2d_stated = o2d_stated
  − 1  if cushion > 0 on the order
  − 1  if order placed before 2:00 PM local
         AND not pre-cutoff (o2sumsbd > 0)
         AND warehouse cutoff < 2:00 PM (or null)

sim_fast_badge = 1 if sim_o2d_stated ≤ 5, else 0
```

**Pre-cutoff flag:** `o2sumsbd = 0` (order received before the warehouse's daily cutoff → same-day MSBD).

**Important:** This simulates **what the badge would say**, not whether Safavieh can actually deliver that speed. IFR and delivery reliability must move in parallel with policy changes.

---

## Warehouse network (L3M)

All sites run **24-hour SP lead time**. Cutoff and cushion settings vary today:

| Location | Cutoff | Cushion on some orders | Volume | IFR | Current fast badge | Sim fast badge | Uplift |
|----------|--------|------------------------|-------:|----:|-------------------:|---------------:|-------:|
| Whitestown, IN | 12:00 PM | Yes | 43,338 | 85.8% | 90.0% | 90.8% | +0.8 pp |
| Baytown, TX | 2:00 PM | Yes | 43,064 | 80.2% | 90.8% | 91.1% | +0.3 pp |
| Lebanon, NJ | 8:00 AM | Yes | 32,973 | **73.5%** | 80.5% | 83.3% | +2.7 pp |
| Riverside, CA | 2:00 PM | Yes | 25,841 | 92.6% | 72.3% | 72.3% | — |
| Savannah, GA | 1:00 PM | Yes | 21,437 | 81.8% | 89.6% | 90.3% | +0.7 pp |
| Midway, GA | 11:00 AM | Yes | 17,811 | 86.4% | 88.6% | 89.4% | +0.8 pp |
| Patterson, CA | 2:00 PM | Yes | 17,761 | 89.8% | 60.6% | 60.7% | +0.1 pp |
| Flemington, NJ | 2:00 PM | Yes | 13,810 | 75.5% | 83.4% | 83.7% | +0.3 pp |
| Easton, PA | Midnight* | Yes | 10,341 | 75.8% | 80.3% | 83.4% | +3.1 pp |
| Port Wentworth, GA | Midnight* | Yes | 6,333 | 73.6% | 87.9% | 91.9% | +4.1 pp |
| Carlisle, PA | 2:00 PM | Yes | 5,179 | 89.6% | 91.4% | 91.4% | — |

\* `00:00:00` cutoff in system — effectively no same-day processing window; largest badge uplift opportunity if moved to 2:00 PM.

**Sites with active cushion today** (subset of orders at each location): Lebanon NJ, Easton PA, Port Wentworth GA, Whitestown IN, Baytown TX, Savannah GA, and others — ~39k orders L3M carry `cushion > 0`.

---

## Key themes for the CEO conversation

### 1. Policy alignment is a small, clean win

Standardizing **2:00 PM cutoff + zero cushion** is low-friction on paper and adds ~**1 pp** fast-badge coverage parent-wide. Sites like **Easton PA (+3.1 pp)** and **Port Wentworth GA (+4.1 pp)** benefit most because today's cutoff effectively blocks same-day processing.

### 2. Induction performance is the bigger gap

IFR at **82.7%** means ~**18%** of orders miss supplier MSBD induction — that erodes customer delivery experience regardless of badge. Weak sites:

- **Lebanon, NJ** — 73.5% IFR, 8:00 AM cutoff; only ~21% label same-day, ~11% induct same-day
- **Port Wentworth, GA** — 73.6% IFR
- **Flemington, NJ** — 75.5% IFR
- **Baytown, TX** — 80.2% IFR (second-largest volume node)

Badge simulation does **not** fix induction; committing to 2pm cutoff requires **FedEx pickup and first-scan alignment** at each DC.

### 3. Geography limits badge at some nodes

**Riverside, CA** and **Patterson, CA** have strong IFR (~90%+) but lower fast-badge rates (~60–72%) because stated O2D is driven by distance/transit, not warehouse policy. Cutoff/cushion changes won't move the needle much there.

### 4. Weekend / Fri–Sat order gap

Safavieh ships **~39%** of Fri/Sat volume on Sat/Sun L6W at major nodes — opportunity to discuss weekend pickup if CEO wants to push speed further (separate from badge sim).

---

## Proposed commitments (discussion framework)

| Safavieh commits | Wayfair commits |
|------------------|-----------------|
| **2:00 PM cutoff** at every US warehouse | Update LT/cushion settings to match; re-run badge sim to confirm customer-facing speed |
| **Zero cushion** network-wide | Monitor IFR weekly during transition |
| **Weekly IFR + label-to-induction** reporting by DC | Share network speed targets and badge impact |
| FedEx pickup schedule aligned to 2pm processing window | Escalation path for carrier issues |

---

## Questions to drive in the meeting

1. Is Safavieh willing to **standardize 2:00 PM cutoff** across all US warehouses, including Easton PA and Port Wentworth GA?
2. Can they **eliminate cushion** network-wide, and what operational risk do they perceive?
3. What is driving **NJ and TX IFR** — staffing, carrier pickup timing, or volume?
4. What **FedEx pickup schedule** exists at each DC today vs. the proposed 2pm window?
5. Are they open to **weekend induction** for Fri/Sat orders at high-volume nodes?

---

## SQL reference

Reusable simulation query: [`sql/safavieh_badging_simulation.sql`](../../sql/safavieh_badging_simulation.sql)

---

*Note: Analysis excludes CastleGate (`fulfillment_type = 'CG'`). Badge simulation models stated speed only; actual delivery performance requires IFR and delivery reliability improvement in parallel.*
