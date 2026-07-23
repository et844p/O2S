# Large Parcel Metrics — LP_dash_ET

Use this reference for natural-language data pull requests against the Large Parcel monitoring table.

## Tables

| Setting | Value |
|---------|-------|
| Project | `wf-gcp-us-ae-global-tnd-prod` |
| Dataset | `speed_and_reliability` |
| LP table | `LP_dash_ET` |
| LP fully qualified | `` `wf-gcp-us-ae-global-tnd-prod.speed_and_reliability.LP_dash_ET` `` |
| OTR tracking | `OTR_Tracking_ET` |
| OTR fully qualified | `` `wf-gcp-us-ae-global-tnd-prod.speed_and_reliability.OTR_Tracking_ET` `` |

## Query rules

- Always use backticks for table names.
- Default timebase: `supplier_must_ship_by_date` (Supplier MSBD) unless the user specifies otherwise.
- Weekly timebase: `msbd_week`.
- Default category / speed captain filter: `sto`.
- Boolean columns: `1` = Yes, `0` = No.
- Use **distinct counts** when aggregating volume (e.g. `COUNT(DISTINCT opid)` or `COUNT(DISTINCT ponum)`).
- Limit results to **10 rows** unless the user asks for more.
- **Induction performance / IFR**: `AVG(inducted_on_time_or_early)`.
- **RFPD on-time rate**: `AVG(rfpd_early_ontime_SU_new)`.
- **PO / order number** queries: use `ponum`.
- **Truck efficiency**: `executedtrucks / plannedtrucks` (dedupe by MSBD + warehouse when aggregating — truck counts repeat per order on the same MSBD).
- **CTC**: `(% of Network Volume) * (Late Orders)` where Late Orders = `Volume * (1 - IFR)`.

## Routing-type pickup logic

Warehouses run different pickup setups. Use the metric that matches the routing type:

| Routing type | Pickup on-time metric | Source table | Notes |
|--------------|----------------------|--------------|-------|
| **Live Load Pooled** | `rfpd_early_ontime_SU_new` | `LP_dash_ET` | RFPD registered on or before supplier MSBD determines pickup readiness |
| **OTR** | `pu_on_before_MSBD` | `OTR_Tracking_ET` | Carrier pickup on or before MSBD; also check `pu_on_MSBD` for exact-day pickup and truck execution (`plannedtrucks` vs `executedtrucks`) |
| **Drop Pooled** | `pu_withinSLA_new` | `LP_dash_ET` | GAT SLA: MSBD+1 for Drop |
| **Other** | `pu_withinSLA_new` or `rfpd_early_ontime_SU_new` | `LP_dash_ET` | Fall back to network SLA columns |

Join OTR orders to `OTR_Tracking_ET` on `ChildSuID` + `ponum` + `supplier_must_ship_by_date`.

## Key columns

### Supplier identity & routing

| Column | Type | Description |
|--------|------|-------------|
| `ChildSuID` | INT | Unique supplier ID / SUID |
| `suname` | STR | Child supplier name |
| `parentsuid` | INT | Parent supplier ID |
| `parentsuname` | STR | Parent supplier name |
| `sto` | STR | Speed captain / category ownership (default filter) |
| `Routingtype` | STR | Routing method: OTR, Drop Pooled, Live Load Pooled, LTL to PP, LTL to HDO |
| `PP` | STR | Pooling point (e.g. Wayfair - Perris) |
| `RFPD_Type` | STR | Source of RFPD entry (e.g. Partner Home) |

### Lead time

| Column | Type | Description |
|--------|------|-------------|
| `LP_LT` | INT | LP supplier lead time setting (hours; 24 = 1 day) |
| `baseleadtime` | INT | Actual LP lead time assigned to the order (hours) |
| `LP_Cutoff` | TIME | Daily cutoff for same-day warehouse staging |
| `cushion` | FLOAT | Safety margin hours (customer-side calculations) |

### Order identifiers & dates

| Column | Type | Description |
|--------|------|-------------|
| `opid` | INT | Unique order product ID — use `COUNT(DISTINCT opid)` for volume |
| `ponum` | INT | Purchase order number |
| `order_complete_date` | DATE | Order checkout date |
| `supplier_must_ship_by_date` | DATE | **Default timebase** — Supplier MSBD |
| `msbd_week` | DATE | Start of MSBD week |
| `msbd_month` | DATE | Start of MSBD month |

### RFPD & pickup

| Column | Type | Description |
|--------|------|-------------|
| `registration` | TIMESTAMP | When RFPD request was placed |
| `rfpd_new` | DATETIME | Ready for Pickup Date (use for RFPD requests) |
| `rfpd_early_ontime_SU_new` | INT | **RFPD on-time**: RFPD on or before supplier MSBD |
| `rfpd_available` | INT | RFPD registered (1) vs not (0) |
| `registration2rfpd` | INT | Days from registration to RFPD |
| `pu_on_MSBD` | INT | Carrier pickup on exact MSBD |
| `pu_on_before_MSBD` | INT | Carrier pickup on or before MSBD |
| `pu_onrfpd_new` | INT | Carrier pickup aligns with RFPD |
| `pu_withinSLA_new` | INT | Pickup within revised network SLA by routing type |
| `PU_within_SLA` | INT | Backup pickup-within-SLA column |

### Induction & delivery

| Column | Type | Description |
|--------|------|-------------|
| `fm_ship_date` | DATE | First-mile shipment / warehouse out-gate date |
| `carrier_first_induction_date_time` | DATETIME | Carrier induction timestamp |
| `inducted_on_time_or_early` | INT | **IFR** — induction on or before supplier MSBD |
| `GAT_O2I_reliability_SLA` | INT | GAT SLA by routing: MSBD+1 Drop, MSBD+2 OTR, MSBD+1 Live Load |
| `delivery_reliability` | INT | Delivered on or before promised date |
| `o2d_stated` | INT | Stated order-to-delivery days |
| `promised_o2d_7` | INT | Fast-badged orders (O2D ≤ 7 days) |

### OTR truck execution (LP_dash_ET and OTR_Tracking_ET)

| Column | Type | Description |
|--------|------|-------------|
| `plannedtrucks` | INT | Forecast trailers for MSBD (same value per MSBD — dedupe when aggregating) |
| `executedtrucks` | INT | Actual trailers executed on MSBD |
| `TotalOutstandingPOs` | INT | Open PO backlog for MSBD |
| `po_pu` | INT | POs per pickup (trailer capacity) |
| `Load_Depart_Date` | DATE | OTR load departure date (OTR_Tracking_ET only) |
| `Load_Depart_DateTime` | DATETIME | OTR load departure timestamp (OTR_Tracking_ET only) |

### Pool point routing

| Column | Type | Description |
|--------|------|-------------|
| `assigned_pp_LB` | STR | Planned pool point name |
| `actual_pp_SC` | STR | Actual pool point inducted into |
| `actual_hdo_SC` | STR | Actual home delivery operation terminal |

## Formulas

- **Late Orders** = Volume × (1 − IFR)
- **CTC** = (% of Network Volume) × (Late Orders)
- **Truck Efficiency** = executedtrucks / plannedtrucks
- **RFPD On-Time Rate** = AVG(rfpd_early_ontime_SU_new)
- **Pickup On-Time (Live Load)** = AVG(rfpd_early_ontime_SU_new)
- **Pickup On-Time (OTR)** = AVG(pu_on_before_MSBD) from OTR_Tracking_ET
