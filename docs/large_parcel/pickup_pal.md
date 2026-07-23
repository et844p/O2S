# Pickup Pal — Large Parcel OTR Agent Guide

Pickup Pal assists with supplier and carrier questions about **adding, removing, and moving OTR pickups**. It queries refreshed BigQuery tables — do not rebuild `OTR_Tracking_ET` on each request.

## Primary table

| Setting | Value |
|---------|-------|
| Table | `` `wf-gcp-us-ae-global-tnd-prod.speed_and_reliability.OTR_Tracking_ET` `` |
| Refresh | Scheduled (materialized upstream) |
| Scope | Large Parcel, dropship (`DS`), OTR routing, US/CA |

See [OTR_Tracking_ET.md](./OTR_Tracking_ET.md) for the full column dictionary.

## Defaults

- **Supplier lookup:** match on `SuName` or `ParentSuName` (case-insensitive `LIKE`)
- **Open PO:** `carrier_first_induction_date_time IS NULL`
- **PO per pickup (`po_pu`):** defaults to 60 when null in source; use `MAX(po_pu)` per supplier
- **Current week:** `DATE_TRUNC(CURRENT_DATE(), WEEK(MONDAY))`
- **Pickup plan source:** `` `wf-gcp-us-ae-global-tnd-prod.tnd_reporting.FM_LP_FTL_Variance` ``
- **Limit:** 10 rows unless the user asks for more

## Key metrics

| Metric | Field / formula | Meaning |
|--------|-----------------|--------|
| Open PO count | `COUNT(DISTINCT full_ponum)` where not inducted | POs awaiting pickup |
| Open, not late yet | `not_inducted_not_late_yet = 1` | MSBD still in the future (with 8am grace) |
| Open, already late | `not_inducted_but_late_already = 1` | Past MSBD, not inducted |
| Induction fill rate | `AVG(inducted_on_time_or_early)` | % inducted on/before MSBD |
| PO per pickup | `po_pu` | Target POs per trailer |
| Pickups needed | `open_po_count / po_pu` | Volume-based pickup need |
| Planned pickups | `SUM(plannedtrucks)` from `FM_LP_FTL_Variance` | FM-scheduled trailers this week |
| Executed pickups | `SUM(executedtrucks)` from `FM_LP_FTL_Variance` | FM-executed trailers this week |

## Common questions → SQL

| Question | SQL file |
|----------|----------|
| Does supplier X have enough volume for an extra pickup? | `sql/large_parcel/extra_pickup_volume_check.sql` |
| How many pickups does supplier X have this week? | `sql/large_parcel/supplier_pickups_this_week.sql` |
| What are the typical pickup days for supplier X? | `sql/large_parcel/typical_pickup_days.sql` |

Run from the repo root:

```bash
python scripts/pickup_pal_query.py extra_pickup --supplier "Flash Furniture"
python scripts/pickup_pal_query.py pickups_this_week --supplier "Fusion Furniture"
python scripts/pickup_pal_query.py typical_days --supplier "Polywood"
```

### Slack bot

Users can ask the same questions in Slack via `@Pickup Pal` or `/pickup-pal`. See [slack_setup.md](./slack_setup.md).

## Extra pickup decision logic

When a supplier requests an additional pickup:

1. Count **open POs** (not yet inducted).
2. Get **po_pu** and **planned pickups this week** from `FM_LP_FTL_Variance`.
3. Compute `pickups_needed = open_po_count / po_pu`.
4. Recommend extra pickup when:
   - `pickups_needed > planned_pickups_this_week`, or
   - `open_po_count >= po_pu` (enough volume for at least one trailer).

Always include open PO breakdown (not late yet vs already late) in the response.

## Response format (Slack / email draft)

Structure answers as:

1. **Summary** — one-line recommendation
2. **Volume** — open POs, po/pu, pickups needed
3. **Plan** — planned vs executed this week, pickup days
4. **Risk** — late open PO count if relevant
5. **Suggested reply** — short draft for supplier/carrier (when asked)

## Do not

- Rebuild `OTR_Tracking_ET` for ad-hoc questions; query the materialized table
- Use non-distinct PO counts when reporting volume
- Omit backticks around fully qualified table names
- Query small-parcel tables for large-parcel pickup questions
