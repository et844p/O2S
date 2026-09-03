# SoCal constrained origins: do directs help O2D actual?

## Framing

- **Origin:** SoCal assigned hubs with `assigned_constrained_market = 1`
- **Paths:** `direct` (classified) vs `local` (`non_candidate`, SoCal induct)
- **High-vol / constraint stress:** MSBD week `2026-05-24` (Memorial Day)
- **BAU:** weeks `2026-06-14, 2026-06-21, 2026-06-28, 2026-07-12, 2026-07-19` (material vol, mostly local fulfillment)
- **Primary metric:** O2D **actual** (is the direct faster to customer?)
- **IFR:** expected to dip in high-vol — reported, not pass/fail

## Period totals

| Period | Path | Vol | IFR | Del Rel | O2D stated | O2D actual | Gap | % ≤5d | Mi to cust |
|--------|------|-----|-----|---------|------------|------------|-----|-------|------------|
| highvol_memorial_direct | direct | 113,846 | 84.2% | 85.4% | 7.65 | 6.81 | -0.85 | 32.2% | 82 |
| highvol_memorial_local | local | 85,134 | 84.7% | 85.9% | 7.99 | 7.01 | -0.98 | 50.7% | 122 |
| bau_local | local | 755,445 | 90.2% | 86.6% | 6.90 | 5.99 | -0.91 | 46.8% | 1397 |
| bau_direct | direct | 6,620 | 88.4% | 90.5% | 9.43 | 6.22 | -3.20 | 53.3% | 243 |
| july5_highvol_local | local | 202,191 | 88.7% | 84.7% | 7.05 | 6.20 | -0.85 | 44.5% | 1397 |
| july5_highvol_direct | direct | 885 | 78.9% | 88.2% | 9.22 | 5.35 | -3.88 | 67.6% | 376 |

## Test 1 — Within Memorial Day week: direct vs local

- Direct O2D actual **6.81d** vs local **7.01d** (Δ -0.21d; negative = direct faster)
- IFR: direct 84.2% vs local 84.7% (-0.5 pp) — dip expected on directs / stress
- % O2D actual ≤5d: direct 32.2% vs local 50.7%
- Miles after induction: direct ~82 vs local ~122

## Test 2 — Similar BAU pattern → built directs in high-vol

Cohort: ≥50 BAU local ops, BAU direct share ≤20%, ≥30 Memorial Day direct ops (same suppliers, normal fulfillment ≈ local).

- **n = 738** suppliers
- **12.7%** faster O2D actual than their own BAU local (94/738)
- Median O2D delta (HV direct − BAU local): **+0.77d**
- Vol-weighted O2D delta: **+0.79d**
- Vol-weighted IFR delta: **-7.3 pp** (dip expected)

### Verdict

**Not helpful on speed:** high-vol directs were **slower** than own BAU local by ~0.79d vol-weighted (despite much shorter post-induction miles).

### Top suppliers (by HV direct vol)

| SUID | Supplier | BAU local vol | BAU O2D act | HV direct vol | HV O2D act | O2D Δ | BAU IFR | HV IFR | IFR Δ |
|------|----------|---------------|-------------|---------------|------------|-------|---------|--------|-------|
| 237104 | Devion Furniture | 16,289 | 7.70 | 3,292 | 8.86 | +1.16 | 93.8% | 43.0% | -50.7 pp |
| 316872 | Heze Starfire Trading Co., Ltd CA 91761(5) | 3,630 | 7.77 | 1,141 | 8.48 | +0.71 | 81.8% | 74.0% | -7.8 pp |
| 119437 | Aosom LLC CA 92374 | 6,574 | 4.64 | 970 | 5.03 | +0.39 | 99.6% | 99.4% | -0.2 pp |
| 28971 | NFusion CA 91761 Warehouse CA11 | 4,387 | 5.66 | 924 | 6.57 | +0.91 | 84.0% | 82.1% | -1.9 pp |
| 238512 | CP HomeDecor CA 91761(2) | 4,951 | 6.65 | 904 | 7.82 | +1.17 | 94.9% | 62.1% | -32.8 pp |
| 39837 | Kingston CA | 4,936 | 6.99 | 893 | 8.04 | +1.05 | 97.9% | 87.8% | -10.1 pp |
| 59119 | Safavieh CA 92518 | 5,238 | 3.94 | 831 | 4.86 | +0.91 | 97.0% | 99.2% | +2.1 pp |
| 17066 |   CA2 | 1,781 | 6.31 | 800 | 6.03 | -0.28 | 84.9% | 70.1% | -14.8 pp |
| 272805 | Karat Home Inc (14 Karat) CA 92880 | 3,610 | 6.14 | 740 | 7.99 | +1.85 | 98.4% | 63.4% | -35.0 pp |
| 292636 | Green Living Group INC CA 91762 | 3,648 | 5.83 | 685 | 7.11 | +1.28 | 93.4% | 88.2% | -5.2 pp |
| 297318 | Eazeemats CA 91752 (4) | 2,725 | 6.32 | 639 | 6.82 | +0.50 | 99.2% | 95.9% | -3.2 pp |
| 20530 | Million Dollar Baby CA 90660 | 3,942 | 5.88 | 602 | 6.53 | +0.65 | 96.7% | 95.8% | -0.8 pp |
| 293214 | CIAO JING INC CA 92879  | 639 | 6.51 | 560 | 7.25 | +0.74 | 84.4% | 71.6% | -12.7 pp |
| 117518 | Winsome House CA 92881 | 3,408 | 4.97 | 535 | 5.77 | +0.79 | 92.7% | 96.4% | +3.7 pp |
| 399345 | Shenzhen Like Keji Youxiangongsi CA 91730(2) | 291 | 7.05 | 534 | 5.87 | -1.18 | 60.5% | 95.5% | +35.0 pp |
| 27593 | NFusion CA El Monte | 3,100 | 5.16 | 527 | 5.77 | +0.61 | 95.6% | 89.8% | -5.8 pp |
| 236498 | Oberon Dist | 2,138 | 7.48 | 522 | 8.36 | +0.88 | 93.4% | 76.2% | -17.2 pp |
| 8833 | Lifetime Brands Inc.92376 | 3,340 | 5.72 | 514 | 6.77 | +1.05 | 86.6% | 69.5% | -17.1 pp |
| 60106 | Winado CA 91762 | 4,038 | 5.14 | 487 | 5.69 | +0.55 | 87.6% | 75.2% | -12.5 pp |
| 373889 |  SLM CA3 | 2,522 | 4.43 | 483 | 5.07 | +0.64 | 93.3% | 95.9% | +2.6 pp |
| 126078 | Ideal Ventures - GGI International CA | 2,099 | 5.72 | 471 | 6.67 | +0.95 | 97.2% | 98.1% | +0.9 pp |
| 275205 | Town Country Linen Corporation CA 92376 | 2,119 | 6.64 | 467 | 6.73 | +0.09 | 97.7% | 99.4% | +1.6 pp |
| 322082 | Hangzhou Mengfeisi Home Furnishings Co., CA 92571  | 1,850 | 5.44 | 443 | 6.46 | +1.02 | 99.5% | 98.6% | -0.8 pp |
| 280028 |  CHINO | 2,970 | 6.28 | 423 | 6.42 | +0.14 | 98.2% | 98.6% | +0.4 pp |
| 70741 | Westin Outdoor CA | 664 | 5.83 | 422 | 7.42 | +1.59 | 70.8% | 32.2% | -38.6 pp |

## Test 3 — BAU local baseline vs high-vol local (stress without directing)

- BAU local O2D actual **5.99d** vs Memorial Day local **7.01d** (Δ +1.02d)
- BAU local IFR 90.2% vs Memorial Day local 84.7% (-5.5 pp)

## Weekly side-by-side (O2D actual)

| Week | Direct vol | Local vol | Direct O2D | Local O2D | O2D Δ | Direct IFR | Local IFR |
|------|------------|-----------|------------|-----------|-------|------------|-----------|
| 2026-04-26 | 142 | 22601 | 10.40 | 6.22 | 4.18 | 72.5% | 93.7% |
| 2026-05-03 | 1138 | 166419 | 9.66 | 6.31 | 3.34 | 62.3% | 90.4% |
| 2026-05-10 | 5536 | 160337 | 8.43 | 6.49 | 1.94 | 74.1% | 92.6% |
| 2026-05-17 | 79484 | 83701 | 6.47 | 6.86 | -0.39 | 90.2% | 92.0% |
| 2026-05-24 ← high-vol | 113846 | 85134 | 6.81 | 7.01 | -0.21 | 84.2% | 84.7% |
| 2026-05-31 | 81920 | 62933 | 6.16 | 6.59 | -0.43 | 88.3% | 86.7% |
| 2026-06-07 | 70108 | 71618 | 5.91 | 6.41 | -0.49 | 93.0% | 89.1% |
| 2026-06-14 ← BAU | 3452 | 170264 | 6.73 | 5.91 | 0.83 | 94.7% | 91.4% |
| 2026-06-21 ← BAU | 1260 | 144861 | 6.70 | 6.04 | 0.66 | 83.7% | 90.8% |
| 2026-06-28 ← BAU | 659 | 134219 | 5.81 | 6.26 | -0.45 | 76.5% | 86.6% |
| 2026-07-05 | 885 | 202191 | 5.35 | 6.20 | -0.85 | 78.9% | 88.7% |
| 2026-07-12 ← BAU | 604 | 149124 | 4.67 | 5.94 | -1.27 | 84.8% | 90.9% |
| 2026-07-19 ← BAU | 645 | 156977 | 4.43 | 5.85 | -1.42 | 79.7% | 90.8% |
| 2026-07-26 | 1078 | 213970 | 4.38 | 5.87 | -1.48 | 80.1% | 88.0% |
| 2026-08-02 | 797 | 159471 | 4.08 | 5.42 | -1.34 | 80.4% | 90.5% |
| 2026-08-09 | 364 | 90844 | 3.19 | 3.36 | -0.16 | 94.0% | 85.2% |

## Files

| File | Contents |
|------|----------|
| `socal_constrained_directs_o2d_verdict.xlsx` | Period + weekly + supplier cohort |
| `socal_constrained_similar_bau_suppliers.csv` | Similar-BAU suppliers who directed in HV |
| `scripts/run_socal_constrained_directs_o2d.py` | Re-run |
