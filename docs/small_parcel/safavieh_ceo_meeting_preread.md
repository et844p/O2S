# Safavieh — CEO In-Office Pre-Read

**Meeting:** Safavieh CEO in-office (high-level partnership review)  
**Generated:** 2026-07-28  
**Base:** **June 2026 MSBD** (`msbd_su` 2026-06-01 – 2026-06-30)  
**Scope:** Dropship only (`fulfillment_type = 'DS'`) · Rugs STO

**Full package (doc + data + SQL):** [GitHub — Safavieh CEO branch](https://github.com/et844p/O2S/tree/cursor/safavieh-ceo-preread-b7d6)

---

## TL;DR

Safavieh shipped **~73k** dropship rug ops in **June MSBD** across **13 US warehouses**, with **90.3% IFR** and **84.7% fast-badge coverage** that month.

**Same-day induction before 2pm** (from `toolkit_hourly_performance`, Tue–Sat orders): **68.3%** parent-wide — but varies sharply by warehouse (**42%** Easton PA to **94%** Carlisle PA). This is the operational gap behind the 2pm cutoff conversation.

**Stacked policy simulation on June volume:**

| Scenario | Fast-badge % | Uplift vs June | Newly fast-badged |
|----------|------------:|---------------:|------------------:|
| June actual | **84.7%** | — | — |
| 2pm cutoff + no cushion | **85.9%** | +1.2 pp | 862 |
| **+ Weekend shipping** | **86.9%** | **+2.2 pp** | **1,642** |

**Framing for the CEO:** *"June showed strong IFR — the badge opportunity is aligning cutoff/cushion/weekend policy, but same-day induction before 2pm is only 68% network-wide. That's what customers experience."*

---

## June MSBD parent snapshot

| Metric | Value |
|--------|------:|
| Volume (distinct ops) | 73,253 |
| Induction Fill Rate | **90.3%** |
| Fast-badge % (`o2d_stated ≤ 5`) | **84.7%** |
| Same-day induct before 2pm (toolkit) | **68.3%** |
| Orders before 2pm (toolkit) | 23,237 |

---

## Same-day induction before 2pm by warehouse

Source: `toolkit_hourly_performance` — `less_14_o2i_0` logic (orders placed Tue–Sat, hour ≤ 14 local, `o2i_0` same-day induction). June `order_complete_date`. Mas_SuID from supplier feed-level logic.

| Location | June MSBD vol | IFR | Fast badge | **Same-day induct ≤2pm** | Orders ≤2pm | HVE `o2I_0_adj` |
|----------|-------------:|----:|-----------:|-------------------------:|------------:|----------------:|
| Carlisle, PA | 1,475 | 89.2% | 91.4% | **94.1%** | 1,001 | 31.0% |
| Riverside, CA | 7,967 | 98.5% | 73.2% | **83.8%** | 5,190 | 33.4% |
| Savannah, GA | 6,483 | 94.6% | 89.6% | **84.1%** | 4,201 | 27.8% |
| Whitestown, IN | 13,757 | 92.7% | 90.6% | **73.3%** | 8,102 | 23.8% |
| Patterson, CA | 5,271 | 92.7% | 64.0% | **73.0%** | 3,256 | 30.5% |
| Baytown, TX | 12,824 | 89.2% | 91.3% | **65.6%** | 7,720 | 24.2% |
| Midway, GA | 5,975 | 94.5% | 90.4% | **67.4%** | 3,818 | 21.4% |
| Port Wentworth, GA | 1,665 | 90.5% | 86.8% | **50.8%** | 1,001 | 12.0% |
| Lebanon, NJ | 9,377 | 82.1% | 80.8% | **50.1%** | 5,004 | 15.7% |
| Flemington, NJ | 4,446 | 75.9% | 84.1% | **49.9%** | 2,333 | 18.8% |
| Whitestown, IN (2nd site) | 866 | 99.1% | 87.5% | **45.7%** | 503 | 9.9% |
| Easton, PA | 2,855 | 83.3% | 82.2% | **42.3%** | 1,380 | 11.3% |
| Easton, PA (18042b) | 275 | 94.5% | 73.1% | **54.3%** | 150 | 13.8% |

**Note:** Toolkit `o2i_0` (business-day same-day induction) differs from HVE `o2I_0_adj` (8am-adjusted) — use toolkit column for the "before 2pm" operational view.

**Weakest before-2pm induction:** Easton PA (42%), NJ sites (~50%), Port Wentworth GA (51%). **Strongest:** Carlisle PA (94%), Riverside CA (84%).

---

## Badging simulation (June MSBD)

```
sim_o2d_stated = o2d_stated
  − 1  if cushion > 0
  − 1  if order before 2:00 PM local AND not pre-cutoff (o2sumsbd > 0)
         AND warehouse cutoff < 2:00 PM (or null)
  − 1  if Fri/Sat placed AND not inducted Sat/Sun

sim_fast_badge = sim_o2d_stated ≤ 5
```

| Adjustment | Fast-badge % |
|------------|-------------:|
| June actual | 84.7% |
| Policy (cushion + 2pm) | **85.9%** |
| + Weekend shipping | **86.9%** |

---

## Key themes for the CEO conversation

### 1. June IFR was strong — induction execution matters more than badge policy

90.3% IFR in June vs ~83% L3M suggests recent months dipped. NJ sites still weak in June: Flemington 75.9%, Lebanon 82.1%.

### 2. Same-day induction before 2pm is the operational proof point

Policy says 2pm cutoff — but only **68%** of before-2pm orders get same-day induction network-wide. Committing to 2pm cutoff requires **FedEx pickup + warehouse processing** aligned to that window.

### 3. Badge policy stack adds ~2 pp on June volume

Weekend shipping (+1.0 pp on top of policy) remains meaningful at **1,642** newly fast-badged orders in June alone.

### 4. Site-specific stories

- **Carlisle PA** — best before-2pm induction (94%); model site for cutoff alignment
- **Easton PA** — midnight cutoff today, 42% before-2pm induction; biggest ops gap
- **Riverside CA** — 84% before-2pm induction but only 73% fast badge (transit distance)

---

## Questions to drive in the meeting

1. Can every DC match **Carlisle's 94%** same-day induction for orders before 2pm?
2. Will Safavieh **standardize 2:00 PM cutoff** and **zero cushion** network-wide?
3. Is **weekend shipping** feasible at NJ and PA nodes (currently ~40–50% before-2pm induction)?
4. What **FedEx pickup schedule** runs at Easton, Lebanon, and Port Wentworth today?

---

## Data & files

| Resource | Link |
|----------|------|
| **This pre-read** | [safavieh_ceo_meeting_preread.md](https://github.com/et844p/O2S/blob/cursor/safavieh-ceo-preread-b7d6/docs/small_parcel/safavieh_ceo_meeting_preread.md) |
| **June warehouse analysis (CSV)** | [safavieh_june_warehouse_analysis.csv](https://github.com/et844p/O2S/blob/cursor/safavieh-ceo-preread-b7d6/output/safavieh/safavieh_june_warehouse_analysis.csv) |
| **June badging scenarios (CSV)** | [safavieh_june_badging_scenarios.csv](https://github.com/et844p/O2S/blob/cursor/safavieh-ceo-preread-b7d6/output/safavieh/safavieh_june_badging_scenarios.csv) |
| **June warehouse + O2I SQL** | [safavieh_june_msbd_warehouse_analysis.sql](https://github.com/et844p/O2S/blob/cursor/safavieh-ceo-preread-b7d6/sql/safavieh_june_msbd_warehouse_analysis.sql) |
| **June badging simulation SQL** | [safavieh_badging_simulation.sql](https://github.com/et844p/O2S/blob/cursor/safavieh-ceo-preread-b7d6/sql/safavieh_badging_simulation.sql) |
| **Branch (all files)** | [cursor/safavieh-ceo-preread-b7d6](https://github.com/et844p/O2S/tree/cursor/safavieh-ceo-preread-b7d6) |
| **Pull request** | [PR #16](https://github.com/et844p/O2S/pull/16) |

### June scenario summary

| Scenario | Volume | Fast-badge % | Newly fast |
|----------|-------:|------------:|-----------:|
| June actual | 73,253 | 84.67% | — |
| Policy (2pm + no cushion) | 73,253 | 85.85% | 862 |
| Full (+ weekend) | 73,253 | **86.91%** | **1,642** |

---

*June MSBD base. Toolkit hourly performance for before-2pm same-day induction. Excludes CastleGate (`CG`). Badge simulation models stated speed only.*
