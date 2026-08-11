# Constrained market vs directs — is it advantageous?

Window: last 10 weeks PDD, DS. Constrained = `assigned_constrained_market` (supplier assigned hub is constrained).
Supplier labeled constrained if ≥50% of their volume has assigned_constrained_market=1.

## 1) Direct orders: constrained assigned hub vs not

| Segment | Direct vol | Suppliers | IFR | Del rel | Avg gain |
|---------|------------|-----------|-----|---------|----------|
| assigned_constrained | 266,971 | 11,176 | 86.8% | 84.7% | 0.92 |
| not_assigned_constrained | 314,570 | 12,435 | 89.1% | 85.4% | 0.89 |

## 2) Direct volume from constrained suppliers vs not

| Segment | Direct vol | Suppliers | IFR | Del rel | Avg gain |
|---------|------------|-----------|-----|---------|----------|
| constrained_supplier | 269,716 | 10,424 | 86.8% | 84.5% | 0.91 |
| nonconstrained_supplier | 311,825 | 10,943 | 89.1% | 85.6% | 0.89 |

## 3) Within type: directs vs local (non_candidate) baseline

| Segment | Vol | IFR | Del rel |
|---------|-----|-----|---------|
| constrained_supplier | direct | 269,716 | 86.8% | 84.5% |
| constrained_supplier | non_candidate | 2,184,202 | 88.9% | 85.3% |
| nonconstrained_supplier | direct | 311,825 | 89.1% | 85.6% |
| nonconstrained_supplier | non_candidate | 4,483,126 | 89.7% | 86.5% |

## 4) Supplier-level lift (builders with ≥200 direct ops)

| Type | # suppliers | Avg IFR direct | Avg IFR local | Avg IFR lift | % with +IFR lift | Avg del lift | % with +del lift |
|------|-------------|----------------|---------------|--------------|------------------|--------------|------------------|
| constrained | 214 | 85.7% | 88.1% | -2.3 pp | 46% | -0.9 pp | 46% |
| nonconstrained | 287 | 90.0% | 90.3% | -0.3 pp | 55% | -0.1 pp | 53% |

## Verdict

- On **direct orders**, constrained assigned hubs run IFR -2.2 pp and del rel -0.7 pp vs non-constrained directs.
- Among **constrained** direct-builders, directs vs their own local baseline: IFR lift -2.3 pp (46% positive), del lift -0.9 pp (46% positive).
- Among **nonconstrained** direct-builders, directs vs their own local baseline: IFR lift -0.3 pp (55% positive), del lift -0.1 pp (53% positive).

Sheet: `output/directs/constrained_vs_directs_comparison.xlsx`