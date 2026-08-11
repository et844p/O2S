# SoCal O2D by cohort — are directs faster to customer?

Scope: last 10w PDD, DS, assigned SoCal hubs (LA basin / Inland Empire / SD; excludes NorCal).

| Bucket | Vol | IFR | Del rel | O2D stated | O2D actual | Slip | % meet/beat stated | % faster than stated | % actual≤5d | Mi actual→cust |
|--------|-----|-----|---------|------------|------------|------|--------------------|----------------------|-------------|----------------|
| direct | 214,734 | 87.7% | 84.9% | 7.42 | 6.56 | -0.86 | 84.9% | 50.3% | 32.8% | 98 |
| jumbo | 64,000 | 86.8% | 81.3% | 6.95 | 6.37 | -0.58 | 81.3% | 45.6% | 38.6% | 1816 |
| ghost_warehouse | 75,145 | 92.0% | 81.0% | 6.20 | 5.64 | -0.57 | 81.0% | 47.0% | 49.6% | 1625 |
| misshipping | 52,537 | 86.2% | 78.6% | 7.14 | 6.34 | -0.79 | 78.6% | 50.3% | 42.2% | 489 |
| non_candidate | 1,532,453 | 89.5% | 85.8% | 7.00 | 6.14 | -0.86 | 85.8% | 53.4% | 47.0% | 1330 |

## Direct vs local (SoCal)

- IFR: direct **87.7%** vs local **89.5%** (-1.7 pp)
- **O2D actual: direct 6.56d vs local 6.14d (+0.43d)**
- O2D stated: direct 7.42d vs local 7.00d (directs promised slower)
- Slip vs promise: both ~-0.86d early vs stated
- Actual ≤5d: direct 32.8% vs local 47.0%
- Miles after induction: direct **98 mi** vs local **1330 mi**

## Verdict

For SoCal-assigned volume, directs get **much closer to the customer after induction** (~98 mi vs ~1,330 mi), but **do not get to the customer faster end-to-end**.

O2D actual is **+0.43d vs local** (direct slower), and share of ≤5-day actuals is much lower (33% vs 47%).

Interpretation: the IFR / induction delay on directs outweighs the transit-mile savings for this SoCal-assigned slice. Directs look like a last-mile/network play, not a faster customer delivery in aggregate.
