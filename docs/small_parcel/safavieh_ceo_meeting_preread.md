# Safavieh — CEO In-Office Pre-Read

**Meeting:** Safavieh CEO in-office (high-level partnership review)  
**Generated:** 2026-07-28  
**Base:** **June 2026 MSBD** (`msbd_su` 2026-06-01 – 2026-06-30)  
**Scope:** Dropship only (`fulfillment_type = 'DS'`) · Rugs STO

**Full package (doc + data + SQL):** [GitHub — Safavieh CEO branch](https://github.com/et844p/O2S/tree/cursor/safavieh-ceo-preread-b7d6)

---

## TL;DR

Safavieh shipped **~73k** dropship rug ops in **June MSBD** across **13 US warehouses**, with **90.3% IFR**.

**Same-day induction before 2pm:** **68.3%** parent-wide (toolkit, Mon–Fri excl. Sun/Sat) — varies **42%** Easton PA to **94%** Carlisle PA.

**Badging simulation on June volume** (sim `o2d_stated` after cushion / 2pm / weekend adjustments):

| Scenario | 1-day | 2-day | 3-day | Fast (≤5d) |
|----------|------:|------:|------:|-----------:|
| June actual | **0.5%** | **9.5%** | **42.5%** | **84.7%** |
| 2pm + no cushion | 5.1% | 24.1% | 55.7% | 85.8% |
| **+ Weekend shipping** | **6.3%** | **26.4%** | **59.5%** | **86.9%** |
| **Uplift (full vs June)** | **+5.8 pp** | **+17.1 pp** | **+17.0 pp** | **+2.2 pp** |

**Newly badged orders (full simulation):** 4,260 (1-day) · 12,406 (2-day) · 12,479 (3-day) · 1,644 (fast).

**Framing for the CEO:** *"Policy alignment is a big story at 2- and 3-day speed (+17 pp each) — not just fast badge. Same-day induction before 2pm at 68% is still the ops proof point."*

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

Source: `toolkit_hourly_performance` — `less_14_o2i_0` logic (orders placed Mon–Fri, `order_dow_supplier_local` 1=Sun/7=Sat so `NOT IN (1,7)`; hour ≤ 14 local; `o2i_0` same-day induction). June `order_complete_date`. Mas_SuID from supplier feed-level logic.

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

sim_badge_Nd = sim_o2d_stated ≤ N  (1-day, 2-day, 3-day, or fast ≤ 5)
```

| Scenario | 1-day | 2-day | 3-day | Fast (≤5d) |
|----------|------:|------:|------:|-----------:|
| June actual | 0.5% | 9.5% | 42.5% | 84.7% |
| Policy (cushion + 2pm) | 5.1% | 24.1% | 55.7% | 85.8% |
| + Weekend shipping | **6.3%** | **26.4%** | **59.5%** | **86.9%** |

---

## Charts & visualizations

| Chart | Description |
|-------|-------------|
| [01 — IFR by warehouse](safavieh_charts/01_ifr_by_warehouse.png) | June MSBD induction fill rate by site |
| [02 — Before-2pm same-day induction](safavieh_charts/02_before_2pm_same_day_induction.png) | Toolkit hourly — operational gap by warehouse |
| [03 — IFR vs before-2pm scatter](safavieh_charts/03_ifr_vs_before_2pm_scatter.png) | Sites with high IFR but low before-2pm induction |
| [04 — Badging tiers current vs sim](safavieh_charts/04_badging_tiers_current_vs_sim.png) | 1 / 2 / 3 / fast-day coverage — June vs full simulation |
| [05 — Badging opportunity](safavieh_charts/05_badging_opportunity_uplift.png) | Uplift (pp) and newly badged orders by tier |
| [06 — 3-day badge by warehouse](safavieh_charts/06_3d_badge_by_warehouse.png) | Warehouse-level 3-day badge opportunity |
| [07 — Volume by warehouse](safavieh_charts/07_volume_by_warehouse.png) | June MSBD volume distribution |

Regenerate: `python scripts/analyze_safavieh_charts.py`

GitHub: [safavieh_charts folder](https://github.com/et844p/O2S/tree/cursor/safavieh-ceo-preread-b7d6/docs/small_parcel/safavieh_charts)

---

## Key themes for the CEO conversation

### 1. June IFR was strong — induction execution matters more than badge policy

90.3% IFR in June vs ~83% L3M suggests recent months dipped. NJ sites still weak in June: Flemington 75.9%, Lebanon 82.1%.

### 2. Same-day induction before 2pm is the operational proof point

Policy says 2pm cutoff — but only **68%** of before-2pm orders get same-day induction network-wide. Committing to 2pm cutoff requires **FedEx pickup + warehouse processing** aligned to that window.

### 3. Badge policy stack — biggest lift at 2- and 3-day speed

Full simulation adds **+17 pp** at 2-day and 3-day badges (~12.4k newly badged orders each tier). Fast badge (≤5d) gains only **+2.2 pp** — the CEO conversation should cover the full speed ladder, not just fast.

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

## Google Slides deck

| Resource | Link |
|----------|------|
| **Download PPTX** (import to Google Slides) | [Safavieh_CEO_June_MSBD.pptx](https://github.com/et844p/O2S/raw/cursor/safavieh-ceo-preread-b7d6/output/safavieh/Safavieh_CEO_June_MSBD.pptx) |
| **Import instructions** | [IMPORT_TO_GOOGLE_SLIDES.md](https://github.com/et844p/O2S/blob/cursor/safavieh-ceo-preread-b7d6/output/safavieh/IMPORT_TO_GOOGLE_SLIDES.md) |

**Quick import:** [Google Slides](https://slides.google.com) → File → Import slides → Upload the PPTX.

Regenerate: `python scripts/create_safavieh_google_slides.py`

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

### June scenario summary (all badge tiers)

| Scenario | 1-day | 2-day | 3-day | Fast (≤5d) | Newly 3-day | Newly fast |
|----------|------:|------:|------:|-----------:|------------:|-----------:|
| June actual | 0.52% | 9.46% | 42.46% | 84.67% | — | — |
| Policy (2pm + no cushion) | 5.09% | 24.09% | 55.71% | 85.84% | 9,717 | 862 |
| Full (+ weekend) | 6.34% | 26.38% | **59.48%** | **86.91%** | **12,479** | **1,644** |

---

*June MSBD base. Toolkit hourly performance for before-2pm same-day induction. Excludes CastleGate (`CG`). Badge simulation models stated speed only.*
