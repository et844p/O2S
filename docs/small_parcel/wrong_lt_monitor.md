# Wrong LT Daily Monitor

Flags dropship orders where the assigned ledger lead time does not match the supplier's Bulk or Product LT setting.

## What it checks

For `order_complete_date = yesterday`, DS fulfillment, destination country US/CA (`1, 2`):

| LT type | Expected | Actual |
| --- | --- | --- |
| Bulk LT + Small Parcel | `SuSmallParcelLeadTimeBulkValue` | `baseleadtime * 24` |
| Bulk LT + Large Parcel | `SuLargeParcelLeadTimeBulkValue` | `baseleadtime * 24` |
| Product LT | `tbl_supplier_part.SupplierLeadTime` | `baseleadtime * 24` |

Mismatch ⇒ `wrong_lt_flag = 1`.

## How to run

```bash
python scripts/run_wrong_lt_monitor.py
```

Artifacts land in `output/wrong_lt_monitor/`:

| File | Purpose |
| --- | --- |
| `wrong_lt_<date>.csv` | Raw mismatched OPIDs |
| `state.json` | Open + resolved history for next diff |
| `slack_message.md` | Ready-to-post Slack summary |

## Alerting logic

Issue key: `supplierid | Supplierpartid | ship_class_group | su_lt_type`

- **New** — first time seen
- **Reopened** — returned after a resolved stretch
- **Resolved** — gone vs prior open set
- **Ongoing** — still present (Slack quiet by default)

## Cursor skill + automation

- Skill: `.cursor/skills/wrong-lt-monitor/`
- Daily automation prompt: `.cursor/skills/wrong-lt-monitor/references/automation_prompt.md`
- Plan: daily while prominent; move schedule to weekly next Friday

## SQL source

`sql/wrong_lt_monitor.sql`
