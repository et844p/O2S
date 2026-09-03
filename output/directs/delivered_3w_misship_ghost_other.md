# Delivered 3-week misship / ghost / other

Window: `2026-08-12` → `2026-09-02` (`delivery_date`)
Total DS delivered vol: **2,409,417** distinct ops

## Share of delivered volume

| Bucket | Vol | % of delivered | IFR | Delivery rel |
|--------|-----|----------------|-----|--------------|
| misshipping | 87,720 | 3.64% | 88.6% | 70.3% |
| ghost | 47,586 | 1.98% | 80.3% | 66.1% |
| other_closer | 337,396 | 14.00% | 89.9% | 88.5% |
| local_wrong_hub | 970,823 | 40.29% | 90.7% | 88.4% |
| aligned | 965,892 | 40.09% | 91.3% | 81.4% |

### Focus read

- **Misshipping**: 87,720 (3.64%)
- **Ghost** (far from WH, not closer to customer): 47,586 (1.98%)
- **Other closer** to customer than assigned: 337,396 (14.00%)
- **Other farther** (≥200mi, residual): 0 (0%)

`local_wrong_hub` = wrong hub but <200mi from assigned and not closer — mostly local hub/data noise.

## Definitions

- **misshipping**: wrong hub + induction state has another parent warehouse (same `parent_suid`)
- **ghost**: wrong hub + ≥200 mi from assigned WH + actual hub is **not** closer to customer than assigned
- **other_closer**: wrong hub (not misship/ghost); actual hub **closer** to customer than assigned
- **other_farther**: wrong hub (not misship/ghost); ≥200 mi from assigned and not closer (residual; usually empty/ghost)
- **local_wrong_hub**: wrong hub, <200 mi from assigned, not closer
- **aligned**: not wrong-hub

Closer = `distance_actualhub_customer < distance_assignedhub_customer`.

## How to run

```bash
python3 scripts/run_delivered_3w_misship_ghost_other.py
```
