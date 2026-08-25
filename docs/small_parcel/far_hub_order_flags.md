# Far-hub OPID flags (supplier-first)

Generated: 2026-08-25

Primary pipeline for **misshipping** and **ghost warehouse** detection. True directs builders are rare; this flow diagnoses supplier behavior first, then flags each `ops` (OPID).

## How to run

```bash
# Supplier diagnosis (default — start here)
python3 scripts/run_far_hub_order_flags.py

# Candidate OPID flags (order-level)
python3 scripts/run_far_hub_order_flags.py --order-level

# One supplier
python3 scripts/run_far_hub_order_flags.py --order-level --supplier-id 110022
```

SQL: `sql/far_hub_order_flags.sql`

## Flow

1. **Order attrs** on DS volume (default window: last 10 weeks by PDD)
2. **Supplier rollup** — misshipping share, undeclared far-hub patterns, directish volume
3. **`supplier_behavior`** diagnosis (priority below)
4. **`opid_flag`** on each order using diagnosis + order attrs

## Candidate (far wrong-hub)

1. `assignedhub_notequal_actualhub_flag = 1`
2. `distance_assignedhub_customer >= 400`
3. `distance_assignedhub_actualhub >= 200`

(Raw distances only; do not trust `distance_assignedhub_actualhub_200_plus`.)

## Supplier behavior (priority)

| Behavior | Meaning |
|----------|---------|
| `ghost_warehouse` | Undeclared location: concentrated hub (≥10% vol, persistent) **or** fragmented state (≥2% vol, ≥8 hubs in one undeclared state — e.g. Loloi TX → CA) |
| `misshipping` | ≥1% volume inducts in a sibling parent-warehouse state |
| `builds_directs` | Rare: ≥50 ops and ≥5% volume look like intentional directs (not ghost/misship) |
| `far_hub_noise` | Some far-hub candidates, no clear ghost/misship/direct pattern |
| `clean` | Little far-hub candidate activity |

Undeclared = induction state ≠ own state **and** parent has no WH in that state.  
Sibling / misshipping = parent has another WH in the induction state.

## OPID flag (priority)

| Flag | Rule |
|------|------|
| `non_candidate` | Not a far wrong-hub candidate |
| `misshipping` | Candidate + sibling state |
| `ghost_warehouse` | Candidate + hub/state on supplier’s ghost list |
| `jumbo` | Candidate + `direct_gain < 0.4` |
| `direct` | Only if supplier is `builds_directs` + gain ≥ 0.4 + material hub |
| `other_far` | Remaining candidates (noise / weak signal) |

Each order row also carries `supplier_behavior` so you can filter OPIDs by how the supplier was diagnosed.

## Outputs

| File | Contents |
|------|----------|
| `output/directs/far_hub_supplier_behavior.csv` | One row per supplier |
| `output/directs/far_hub_supplier_behavior_summary.csv` | Counts by behavior |
| `output/directs/far_hub_behavior_*.csv` | Per-behavior supplier slices |
| `output/directs/far_hub_order_flags.csv` | Candidate OPID flags (`--order-level`) |

## Relation to older cohort SQL

`sql/directs_supplier_cohorts.sql` classified every gain≥0.4 candidate as a direct-ish bucket first. That overstated directs builders. Prefer this supplier-first pipeline for operational flagging; keep the old cohort SQL only for historical comparison.
