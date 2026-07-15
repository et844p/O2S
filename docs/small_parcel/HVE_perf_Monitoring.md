# Small Parcel Metrics — HVE_perf_Monitoring

Use this reference for natural-language data pull requests against the Small Parcel monitoring table.

## Table

| Setting | Value |
|---------|-------|
| Project | `wf-gcp-us-ae-global-tnd-prod` |
| Dataset | `speed_and_reliability` |
| Table | `HVE_perf_Monitoring` |
| Fully qualified | `` `wf-gcp-us-ae-global-tnd-prod.speed_and_reliability.HVE_perf_Monitoring` `` |

## Query rules

- Always use backticks for the table name.
- Default timebase: `msbd_su` (Supplier Must Ship By Date) unless the user specifies otherwise.
- Default category / speed captain filter: `sto`.
- Boolean columns: `1` = Yes, `0` = No.
- Use **distinct counts** when aggregating volume (e.g. `COUNT(DISTINCT ops)` or `COUNT(DISTINCT purchase_order_number)`).
- Limit results to **10 rows** unless the user asks for more.
- **Performance** requests: calculate average of `inducted_on_time_or_early` (Induction Fill Rate / on-time performance).
- **PO / order number** queries: use `purchase_order_number`.
- **CTC (Contribution to Change)**: `(% of Network Volume) * (Late Orders)` where Late Orders = `Volume * (1 - Induction Fill Rate)`.

## Column reference

### Supplier identity & location

| Column | Type | Description |
|--------|------|-------------|
| `supplier_id` | INT | Unique Supplier ID / SUID for the supplier |
| `su_name` | STR | Name of the child supplier |
| `parent_suid` | INT | Unique ID for the parent supplier entity |
| `parent_su_name` | STR | Name of the parent supplier entity |
| `states` | STR | List of states where the supplier operates/ships from |
| `count_states` | INT | Total number of unique states associated with this supplier |
| `sto` | STR | Internal Wayfair Single Threaded Ownership reference (e.g., Upholstery, Rugs). **Default filter for category / speed captain ownership requests** |
| `sto2` | STR | Backup column for Single Threaded Ownership reference |
| `srm_contact` | STR | SRM (Supplier Relationship Management) point of contact |
| `address_1` | STR | Primary street address for the supplier location fulfilling this order |
| `city_name` | STR | City where the supplier is located |
| `state_name` | STR | Full name of the state for the supplier's address |
| `postal_code` | STR | ZIP or postal code for the supplier location |
| `summer26_target` | STR | Flag if supplier was on Summer 2026 target list (`1` or `0`) |
| `summer26_cohorts` | STR | Summer 2026 grouping: Induction Fill Rate Target or Stated Speed target |

### Lead time & capacity

| Column | Type | Description |
|--------|------|-------------|
| `sp_lt` | INT | Small Parcel supplier lead time setting (hours; e.g. 24 = 1 day, 48 = 2 days). Use for LT setting value. Can be null for Product Lead Time suppliers |
| `cutoff` | TIME | Daily time limit for same-day or next-day shipping processing |
| `order_lt` | INT | Actual Small Parcel lead time assigned to the order (hours). Use for actual or average LT |
| `cushion` | INT | Safety margin days added to lead time |
| `OrderCapacityPadDays` | INT | Days an order waterfalled due to order capacity. Sum for total waterfalling; average for mean |

### Order & shipment identifiers

| Column | Type | Description |
|--------|------|-------------|
| `ops` | INT | Unique order product ID. One PO can have multiple ops. Use for granular order counts |
| `purchase_order_number` | INT | **Use for PO / order number queries** |
| `tracking_number` | STR | Carrier tracking identifier |

### Hub, routing & distance

| Column | Type | Description |
|--------|------|-------------|
| `destinationentityid` | STR | Unique ID for the destination facility or entity |
| `StationName` | STR | Name of the assigned FedEx logistics station or hub |
| `constrained_market` | INT | Boolean (1/0): market is capacity-constrained |
| `assigned_constrained_market` | INT | Supplier inducts into a constrained market |
| `assigned_induction_hub_id` | STR | ID of the hub originally scheduled for induction |
| `assigned_induction_hub_name` | STR | Name of the planned induction hub |
| `assigned_station_zip` | STR | ZIP of the planned logistics station |
| `assigned_station_state` | STR | State of the planned logistics station |
| `destination_zipcode` | STR | Final delivery ZIP code |
| `destination_state` | STR | Final delivery state |
| `destination_country_id` | INT | Destination country code (`1` = US, `2` = CA) |
| `actual_induction_hub_id` | STR | ID of the hub where the package was actually inducted |
| `actual_induction_hub_name` | STR | Name of the actual induction hub |
| `actual_induction_hub_zip` | STR | ZIP of the actual induction hub |
| `actual_induction_hub_state` | STR | State of the actual induction hub |
| `assignedhub_notequal_actualhub_flag` | INT | Boolean (1/0): routing deviation from planned hub |
| `assignedstate_notequal_actualstate_flag` | INT | Boolean (1/0): inducted in different state than planned |
| `state_pairing` | STR | Origin-to-destination state combination (e.g. `GA-TN`) |
| `distance_assignedhub_customer` | FLOAT | Distance between planned hub and customer |
| `distance_actualhub_customer` | FLOAT | Distance between actual hub and customer |
| `distance_assignedhub_actualhub` | FLOAT | Distance between planned and actual hub |
| `distance_assignedhub_customer_400_plus` | INT | Flag for shipments over 400 miles |
| `distance_assignedhub_actualhub_200_plus` | INT | Flag for routing deviation over 200 miles |
| `direct_gain` | FLOAT | Efficiency gains from potential direct shipping routes |
| `ship_confirm_differentSUID_flag` | INT | Flag when shipping SUID differs from ordering SUID |

### Dates & must-ship-by

| Column | Type | Description |
|--------|------|-------------|
| `order_complete_date` | DATE | Date the order was fully processed |
| `order_complete_date_time_local` | DATETIME | Order placed date/time in supplier local time |
| `order_dow` | INT | Day of week order was placed (1–7) |
| `msbd_su_week` | DATE | Start of week for Supplier Must Ship By Date |
| `msbd_su` | DATE | **Supplier Must Ship By Date. Default timebase for analysis** |
| `msbd_cu` | DATE | Customer-facing Must Ship By Date |
| `event_datetime` | STR | Label created timestamp (e.g. `2026-05-15 13:17:00`) |
| `fulfillment_ship_date_time` | DATETIME | ASN timestamp (adjusted to midnight; e.g. `2026-05-15T00:00:00`) |
| `SU_FR` | INT | Supplier Fill Rate (1/0): ASN on or before `msbd_su` |
| `induction_date_lidd` | DATE | Induction date of the order |
| `induction_date_WCP_local` | DATE | Backup induction date |
| `induction_dow_adj` | INT | Adjusted day of week for induction (holidays/weekends) |
| `carrier_first_induction_date_time` | DATETIME | Timestamp for carrier network induction scan |
| `carrier_first_induction_WCP_local` | DATETIME | Backup induction scan timestamp |
| `delivery_date` | DATE | Delivery date of the order |
| `promised_delivery_end_range_date_at_order` | DATE | Latest promised delivery date at order placement |

### Speed & delivery metrics

| Column | Type | Description |
|--------|------|-------------|
| `o2sumsbd` | INT | Days from `order_complete_date` to `msbd_su` |
| `o2cumsbd` | INT | Days from `order_complete_date` to `msbd_cu` |
| `o2s_actual` | INT | Actual order-to-ship days (`order_complete_date` to `induction_date_lidd`; adjusted to previous day if scan before 8am) |
| `o2d_stated` | INT | Promised/stated order-to-delivery duration |
| `o2d_actual` | INT | Actual order-to-delivery duration |
| `o2d_stated_5` | INT | Boolean (1/0): stated O2D ≤ 5 days (fast-badged orders) |
| `o2d_actual_5` | INT | Boolean (1/0): actual O2D ≤ 5 days |
| `delivery_rel` | INT | Boolean (1/0): delivered on or before promised delivery date |
| `S2D` | INT | Ship-to-delivery days. Total delivery = O2S + S2D |

### Induction performance (supplier MSBD)

| Column | Type | Description |
|--------|------|-------------|
| `label_by_msbd_7` | INT | Boolean (1/0): label by 7pm on MSBD |
| `label_by_msbd_2` | INT | Boolean (1/0): label by 2pm on MSBD |
| `label_7_ind_8` | INT | Boolean (1/0): label by 7pm MSBD and inducted by 8am next day |
| `inducted_early` | INT | Boolean (1/0): inducted before Supplier MSBD |
| `inducted_over_weekend` | INT | Boolean (1/0): inducted Saturday or Sunday |
| `inducted_on_time_or_early` | INT | Boolean (1/0): **use for On Time Performance % / Induction Fill Rate (IFR)** |
| `inducted_on_time_or_early_10AM` | INT | Boolean (1/0): on-time with 10am adjustment (previous day if before 10am) |
| `inducted_late` | INT | Boolean (1/0): inducted after Supplier MSBD |
| `not_inducted_but_late_already` | INT | Boolean (1/0): not scanned but already past MSBD |
| `not_inducted_not_late_yet` | INT | Boolean (1/0): open orders still within MSBD window |
| `one_day_late` | INT | Boolean (1/0): inducted exactly 1 day after MSBD |
| `two_day_late` | INT | Boolean (1/0): inducted exactly 2 days after MSBD |
| `three_five_day_inducted_late` | INT | Boolean (1/0): inducted 3–5 days late |
| `five_ten_day_inducted` | INT | Boolean (1/0): inducted 5–10 days late |
| `three_days_plus_late` | INT | Boolean (1/0): inducted 3+ days late |
| `ten_day_plus` | INT | Boolean (1/0): inducted 10+ days late |
| `ifr_status` | INT | Boolean (1/0): backup Induction Fill Rate column |

### Induction performance (customer MSBD)

| Column | Type | Description |
|--------|------|-------------|
| `cu_inducted_on_time_or_early` | INT | Boolean (1/0): customer-facing on-time induction vs `msbd_cu` |
| `cu_inducted_late` | INT | Boolean (1/0): customer-facing late induction |
| `cu_not_inducted_but_late_already` | INT | Boolean (1/0): customer-facing pending late orders |
| `cu_not_inducted_not_late_yet` | INT | Boolean (1/0): open orders within `msbd_cu` window |

### Order-to-ship stated performance

| Column | Type | Description |
|--------|------|-------------|
| `o2s_stated_1` | INT | Boolean (1/0): stated O2S = 1 day |
| `o2s_stated_1_rel` | INT | Boolean (1/0): stated O2S = 1 day and inducted on time |
| `o2s_stated_2` | INT | Boolean (1/0): stated O2S = 2 days |
| `o2s_stated_2_rel` | INT | Boolean (1/0): stated O2S = 2 days and inducted on time |

### Order-to-induction & label timing

| Column | Type | Description |
|--------|------|-------------|
| `o2I_0_adj` | INT | Boolean (1/0): carrier induction same day as order (8am-adjusted) |
| `o2I_1_adj` | INT | Boolean (1/0): carrier induction within 1 day of order |
| `o2I_2_adj` | INT | Boolean (1/0): carrier induction within 2 days of order |
| `o2I_3_adj` | INT | Boolean (1/0): carrier induction within 3 days of order |
| `label2I_0_adj` | INT | Boolean (1/0): carrier induction same day as label print |
| `label2I_1_adj` | INT | Boolean (1/0): carrier induction 1 day after label print |
| `label2I_2_adj` | INT | Boolean (1/0): carrier induction 2 days after label print |
| `o2label_0_adj` | INT | Boolean (1/0): label print same day as order |
| `o2label_1_adj` | INT | Boolean (1/0): label print 1 day after order |
| `o2label_2_adj` | INT | Boolean (1/0): label print 2 days after order |
| `o2label_3_adj` | INT | Boolean (1/0): label print 3 days after order |

### WCP backup columns

| Column | Type | Description |
|--------|------|-------------|
| `inducted_early_wcp` | INT | Backup: inducted before Supplier MSBD |
| `inducted_over_weekend_wcp` | INT | Backup: inducted on weekend |
| `inducted_on_time_or_early_wcp` | INT | Backup: on-time / IFR |
| `inducted_late_wcp` | INT | Backup: inducted after MSBD |
| `not_inducted_but_late_already_wcp` | INT | Backup: not scanned, past MSBD |
| `not_inducted_not_late_yet_wcp` | INT | Backup: open, within MSBD window |
| `cu_inducted_on_time_or_early_wcp` | INT | Backup: customer on-time |
| `cu_inducted_late_wcp` | INT | Backup: customer late |
| `cu_not_inducted_but_late_already_wcp` | INT | Backup: customer pending late |
| `cu_not_inducted_not_late_yet_wcp` | INT | Backup: customer open within window |
| `o2I_0_adj_wcp` | INT | Backup: O2I within 0 day |
| `o2I_1_adj_wcp` | INT | Backup: O2I within 1 day |
| `o2I_2_adj_wcp` | INT | Backup: O2I within 2 days |
| `o2I_3_adj_wcp` | INT | Backup: O2I within 3 days |

### Product & order attributes

| Column | Type | Description |
|--------|------|-------------|
| `oosp_baseLT_adj` | STR | Yes/No: Out-of-Stock Purchasing |
| `productclass` | STR | Backup high-level division (Furniture, Hardlines, Softlines) |
| `isB2BOrder` | INT | Boolean (1/0): B2B order |
| `ProductCategory` | STR | Specific product category |
| `assigned_leg2_transit` | INT | Planned second-leg transit time |
| `actual_assumed_leg2_transit` | INT | Estimated actual second-leg transit time |
| `supplierpartid` | INT | Unique part ID |
| `supplierpartnumber` | STR | Unique part number |
| `SKU` | STR | Unique SKU |
| `has_relabel` | INT | Relabel flag (present in table; confirm values as needed) |

## Example queries

### On-time performance by STO (last 7 days)

```sql
SELECT
  sto,
  COUNT(DISTINCT ops) AS volume,
  AVG(inducted_on_time_or_early) AS ifr
FROM `wf-gcp-us-ae-global-tnd-prod.speed_and_reliability.HVE_perf_Monitoring`
WHERE msbd_su >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
GROUP BY sto
ORDER BY volume DESC
LIMIT 10
```

### Late orders by supplier

```sql
SELECT
  supplier_id,
  su_name,
  COUNT(DISTINCT ops) AS volume,
  AVG(inducted_on_time_or_early) AS ifr,
  COUNT(DISTINCT ops) * (1 - AVG(inducted_on_time_or_early)) AS late_orders
FROM `wf-gcp-us-ae-global-tnd-prod.speed_and_reliability.HVE_perf_Monitoring`
WHERE msbd_su >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
GROUP BY supplier_id, su_name
HAVING volume > 0
ORDER BY late_orders DESC
LIMIT 10
```
