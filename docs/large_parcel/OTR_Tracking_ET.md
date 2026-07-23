# OTR_Tracking_ET — Large Parcel PO-Level Reference

Materialized PO-level table for Large Parcel OTR pickup analysis. Refreshed on a schedule upstream — **query this table directly**.

## Table

`` `wf-gcp-us-ae-global-tnd-prod.speed_and_reliability.OTR_Tracking_ET` ``

## Filters (already applied in the table build)

- `fulfillment_type = 'DS'` (dropship)
- `ship_class_group = 'Large Parcel'`
- `OriginCountryName IN ('US', 'CA')`
- `routingtype = 'OTR'`
- `order_complete_date >= '2025-01-01'`

## Supplier identity

| Column | Description |
|--------|-------------|
| `ChildSuID` | Child supplier ID |
| `SuName` | Child supplier name |
| `ParentSuID` | Parent supplier ID |
| `ParentSuName` | Parent supplier name |
| `mas_suid` | Master supplier ID (inventory feed) |
| `sto` | Single-threaded ownership |
| `SRMContact` | SRM contact |
| `Routingtype` | FM routing type (`OTR`) |
| `PP` | Crossdock / pool point |

## Order identifiers & dates

| Column | Description |
|--------|-------------|
| `ponum` | PO number |
| `full_ponum` | PO with country prefix (`CS` / `CA`) |
| `order_complete_date` | Order complete date |
| `supplier_must_ship_by_date` | MSBD — must ship by date |
| `rfpd` | Ready for pickup date |
| `carrier_first_induction_date_time` | First carrier induction timestamp |
| `induction_date` | Induction date |
| `fm_ship_date` | FM ship / pickup date |

## Open PO status flags

| Column | Value | Meaning |
|--------|-------|---------|
| `not_inducted_not_late_yet` | 1 | Open, MSBD not passed (with grace) |
| `not_inducted_but_late_already` | 1 | Open, past MSBD, not inducted |
| `inducted_on_time_or_early` | 1 | Inducted on/before MSBD (+ 8am next-day grace) |
| `inducted_late` | 1 | Inducted late |
| `carrier_first_induction_date_time IS NULL` | — | PO still open (not inducted) |

## Pickup capacity & lane

| Column | Description |
|--------|-------------|
| `po_pu` | POs per pickup target (default 60 if null in source) |
| `laneid` | Lane ID |
| `LaneName` | Lane name |
| `plannedtrucks` | FM planned trucks for MSBD day |
| `executedtrucks` | FM executed trucks for MSBD day |
| `TotalOutstandingPOs` | Outstanding POs on pickup day |
| `week` / `day` | Pickup schedule week and day |

## Performance metrics (selected)

| Column | Description |
|--------|-------------|
| `inducted_on_time_or_early` | O2I on/before MSBD (induction fill rate numerator) |
| `o2i_early_ontime_SU` | O2I on/before MSBD (supplier-facing) |
| `o2pu_bus` | Order-to-pickup business days |
| `o2i_bus` | Order-to-induction business days |
| `PU_within_SLA` | Pickup within SLA |
| `carrier_unload_ontime` | Carrier unload on time (from FTL milestones) |

## Time bucketing

| Column | Description |
|--------|-------------|
| `msbd_week_start` | MSBD week (Monday start) |
| `current_week_start` | Current week (Monday start) |
| `week_diff` | Weeks between current and MSBD week |
| `week_bucket` | `Current Week`, `Week -N`, or `Future` |

## Related tables (pickup schedule & execution)

| Table | Use |
|-------|-----|
| `` `wf-gcp-us-ae-global-tnd-prod.tnd_reporting.FM_LP_FTL_Variance` `` | Planned/executed trucks by lane and day |
| `` `wf-gcp-us-ae-gbl-prf-mgmt-prod.reporting.FTL_Milestones` `` | Actual OTR pickup departures and delivery |
| `` `wf-gcp-us-ae-global-tnd-prod.tnd_reporting.FM_Routing_Master` `` | Supplier routing type and PP |
