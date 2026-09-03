# Capacity hypothesis: do directs free hub capacity (higher in-hub IFR)?

## Hypothesis

Suppliers who **build directs** divert far-market volume off the constrained SoCal hub, freeing capacity for **in-hub / local** volume → **higher IFR** on remaining local volume vs suppliers who do not direct.

**Scope:** SoCal assigned + `assigned_constrained_market = 1`, DS, May–Aug 2026 MSBD.  
**In-hub volume:** `non_candidate` (local path). **Directs:** classified `direct`.

## Verdict — **mixed / weak; not a clean proof**

| Test | Result | Supports capacity story? |
|------|--------|--------------------------|
| Memorial Day builders vs non-builders (local IFR) | Builders **84.0%** vs non-builders **82.1%** (**+1.9 pp**) | Directionally yes, but **only 6 non-builders** with ≥30 local that week — almost everyone directed |
| Dose-response (Memorial Day) | Local IFR peaks at 10–50% direct share; **50%+ directors worse** (81.0%) | Partial — light/moderate directing looks better than heavy |
| Within-supplier (high-direct vs no-direct weeks) | 52% positive; median +0.26 pp; **vol-weighted -1.48 pp** | **No** at scale — large suppliers’ local IFR worse in high-direct weeks |
| Full-window tiers | 5–30% direct share ~**90%** local IFR; 0% **84%**; 30%+ **86%** | Mild — some directing associated with better local IFR than zero, not monotonic |
| Hub-level Memorial Day | Higher hub direct share ≠ higher local IFR (corr **-0.69**) | **No — opposite direction** |

**Bottom line for FedEx:** We **cannot cleanly prove** that building directs improves IFR on remaining in-hub volume. There is a weak between-supplier signal in the high-vol week, but the control group is tiny, heavy directors look worse, within-supplier vol-weighted lift is negative, and **hubs with more directing have lower local IFR**.

BAU check: Memorial Day builders later show ~91% BAU local IFR vs never-directed ~76%, but never-directed are a tiny/weak set — that looks like **selection** (capable suppliers both direct and run better local ops), not causal capacity relief from directing.

Possible confounders: ops maturity differences; high-direct weeks = most stressed weeks; diverting one supplier’s volume may not free the hub if others fill the slot.

## Test 1 — Memorial Day: builders vs non-builders (local IFR)

| Cohort | Suppliers | Local vol | Direct vol | **Local IFR** | vs non-builders |
|--------|-----------|-----------|------------|---------------|-----------------|
| HV builders (≥30 direct + ≥30 local) | 533 | 52,073 | 71,829 | **84.0%** | +1.9 pp |
| HV light directors (1–29 direct + ≥30 local) | 63 | 2,551 | 1,382 | **85.2%** | +3.0 pp |
| HV non-builders (0 direct + ≥30 local) | 6 | 515 | 0 | **82.1%** | +0.0 pp |

## Test 2 — Dose-response (Memorial Day)

| Direct share | Suppliers | Local vol | Local IFR |
|--------------|-----------|-----------|-----------|
| 0% | 6 | 515 | **82.1%** |
| 0–10% | 2 | 201 | **58.2%** |
| 10–25% | 8 | 938 | **92.2%** |
| 25–50% | 222 | 21,266 | **88.6%** |
| 50%+ | 364 | 32,219 | **81.0%** |

## Test 3 — Within-supplier (high-direct weeks vs no-direct weeks)

n = **733** (≥50 local ops in both regimes).

- Positive local IFR lift: **51.8%**
- Median lift: **+0.26 pp**
- Vol-weighted lift: **-1.48 pp** (large suppliers drag this negative)

| SUID | Supplier | Local vol (high-direct) | IFR high-direct | Local vol (no-direct) | IFR no-direct | Lift pp |
|------|----------|-------------------------|-----------------|----------------------|---------------|---------|
| 237104 | Devion Furniture | 4,235 | 76.0% | 25,542 | 92.8% | -16.7 |
| 59119 | Safavieh CA 92518 | 3,703 | 99.1% | 9,180 | 90.8% | +8.3 |
| 119437 | Aosom LLC CA 92374 | 2,731 | 99.0% | 9,471 | 99.6% | -0.6 |
| 28971 | NFusion CA 91761 Warehouse CA11 | 2,279 | 86.3% | 7,737 | 85.3% | +1.0 |
| 27593 | NFusion CA El Monte | 2,102 | 95.7% | 6,527 | 93.7% | +1.9 |
| 17066 |   CA2 | 2,075 | 76.4% | 116 | 96.6% | -20.2 |
| 70574 | Yaheetech CA 91761 | 2,048 | 89.9% | 6,809 | 91.1% | -1.2 |
| 60106 | Winado CA 91762 | 1,776 | 82.8% | 628 | 98.7% | -16.0 |
| 373889 |  SLM CA3 | 1,747 | 94.2% | 5,669 | 94.4% | -0.3 |
| 39837 | Kingston CA | 1,640 | 93.8% | 5,768 | 98.2% | -4.5 |
| 399345 | Shenzhen Like Keji Youxiangongsi CA 91730(2) | 1,633 | 97.4% | 610 | 54.9% | +42.5 |
| 25980 | California Umbrella CA | 1,567 | 90.1% | 3,792 | 94.4% | -4.2 |
| 149170 | Alphamarts 007-F CA 91789 | 1,355 | 97.9% | 4,665 | 98.9% | -1.1 |
| 117518 | Winsome House CA 92881 | 1,307 | 92.9% | 5,717 | 94.7% | -1.9 |
| 111282 | Costway CA 92374 [2] | 1,246 | 89.4% | 5,021 | 90.2% | -0.8 |

## Test 4 — Full-window builder tier → local IFR

| Builder tier | Suppliers | Local vol | Direct vol | Local IFR |
|--------------|-----------|-----------|------------|-----------|
| 0% (non-builder) | 82 | 19,990 | 0 | **83.9%** |
| 0–5% | 183 | 59,906 | 1,730 | **89.4%** |
| 5–15% | 1281 | 880,012 | 108,968 | **89.7%** |
| 15–30% | 1175 | 870,625 | 199,049 | **90.2%** |
| 30%+ | 77 | 24,892 | 14,700 | **86.4%** |

## Files

| File | Contents |
|------|----------|
| `directs_capacity_ifr_hypothesis.xlsx` | All tests |
| `scripts/run_directs_capacity_ifr.py` | Re-run |
