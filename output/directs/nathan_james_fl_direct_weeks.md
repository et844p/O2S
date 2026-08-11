# Nathan James NV 89434 — FL directs vs weeks without

Window: last 10 weeks PDD. SUID 139182. Assigned hub typically Reno NV.

- Weeks with ≥1 FL direct: **9**
- Weeks without FL direct: **2**
- FL direct ops: **87** (mostly Orlando)

## 1) All supplier volume — weeks with FL directs vs without

| Week type | Weeks | Vol | IFR | Del rel | O2D stated | O2D actual | %≤5d |
|-----------|-------|-----|-----|---------|------------|------------|------|
| has_fl_direct | 9 | 1,296 | 84.4% | 85.5% | 7.54 | 6.66 | 35.6% |
| no_fl_direct | 2 | 320 | 88.1% | 88.4% | 7.51 | 6.72 | 29.7% |

Whole-book O2D actual: FL-direct weeks **6.66d** vs no-FL weeks **6.72d** (-0.07d).

## 2) Florida-bound packages only (the fairer speed test)

| Week type | FL dest vol | IFR | O2D stated | O2D actual | %≤5d | Mi actual→cust |
|-----------|-------------|-----|------------|------------|------|----------------|
| has_fl_direct | 116 | 49.1% | 8.44 | 6.64 | 23.3% | 965 |
| no_fl_direct | 25 | 84.0% | 8.32 | 7.56 | 8.0% | 2945 |

**FL customers O2D actual: 6.64d in FL-direct weeks vs 7.56d in weeks without** (-0.92d).

## 3) FL destination path: Orlando direct vs other hub

| Path | Vol | IFR | O2D stated | O2D actual | %≤5d | Mi actual→cust | Gain |
|------|-----|-----|------------|------------|------|----------------|------|
| fl_direct | 74 | 21.6% | 8.66 | 6.77 | 21.6% | 128 | 0.96 |
| fl_via_other_hub | 67 | 92.5% | 8.15 | 6.84 | 19.4% | 2817 | 0.03 |

## Verdict

Nathan James builds FL directs most weeks (Orlando). IFR on those FL directs is very weak (~18–50% depending on cut), so induction reliability suffers.
But for **Florida customers**, weeks with FL directs are clearly faster on O2D actual than weeks without (~0.9d), and FL packages that actually take the FL direct path sit much closer to the customer after induction.
So for this supplier: directs trade IFR for faster FL customer delivery — the speed win shows up on FL-bound volume, not the whole book.