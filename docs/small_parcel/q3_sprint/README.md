# Q3 Sprint — Induction Fill Rate & Weekend Shipping

Supplier outreach sprint combining **Induction Fill Rate (IFR)** improvement with **Weekend Must Ship By Date (MSBD)** enablement ahead of peak.

## Sprint timeline

| Date | Event |
|------|-------|
| Monday, August 3 | Suppliers receive Growth@ emails; Sprint Window begins |
| August 3 – August 14 | Daily Office Hours for action plan support |
| August 21 | Deadline: All SRM action plans due in tracker |
| Sept – Nov | Implementation and performance tracking |

## Documents in this folder

| File | Purpose |
|------|---------|
| [cohort_definitions.md](./cohort_definitions.md) | Cohort criteria, routing logic, and SQL-ready thresholds |
| [email_templates.md](./email_templates.md) | Supplier-facing email copy by cohort |
| [merge_fields.md](./merge_fields.md) | Dynamic field dictionary and conditional blocks |
| [cm_announcement.md](./cm_announcement.md) | Category Management partner announcement |

## Cohort summary

| ID | Cohort | Primary focus | Weekend MSBD push |
|----|--------|---------------|-------------------|
| Q3-A | Operational Issues | Label + IFR both low | No |
| Q3-B | Reliability — Forecasting & Constrained | FedEx forecasting, induction timing | Yes (all) |
| Q3-C | Reliability — FIFO & Handshake | Dock execution, trailer loading | Yes (constrained markets only) |
| Q3-D | Speed & Reliability | IFR 70–90%; directs & splits | Yes |
| Q3-E | Speed | IFR > 90%; protect reliability at peak | Yes |
| Q3-F | Weekend MSBD Enablement | Already shipping weekends; enable MSBD | Enablement (not improvement) |

## Related resources

- Weekend shipping analysis: [weekend_shipping_supplier_analysis.md](../weekend_shipping_supplier_analysis.md)
- HVE column reference: [HVE_perf_Monitoring.md](../HVE_perf_Monitoring.md)
- SQL cohort logic: `sql/weekend_shipping_supplier_analysis.sql`

## Next step: supplier lists

Once templates are approved, supplier lists are built by:

1. Running cohort assignment SQL against `HVE_perf_Monitoring` (L6W baseline, `fulfillment_type = 'DS'`)
2. Merging `assigned_constrained_market` for Q3-C conditional copy
3. Joining weekend ship rate (`l6w_pct_fri_sat_shipped_sat_sun`) for Q3-F enablement candidates
4. Exporting merge fields per supplier for Growth@ send
