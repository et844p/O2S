---
name: wrong-lt-monitor
description: Daily (then weekly) monitor for DS orders receiving incorrect lead times. Use when checking wrong LT, incorrect lead time flags, LT mismatches, or posting Slack alerts for new/resolved/reopened wrong-LT issues.
---

# Wrong LT Monitor

Detect dropship (DS) orders where the ledger base lead time does not match the expected Bulk or Product LT setting, then Slack-notify on **new**, **resolved**, and **reopened** issues.

## When to Use

- User asks to run the wrong LT / incorrect lead time check
- Daily automation run of this skill
- Investigating whether a wrong-LT issue cleared or came back

## Cadence

- **Now:** daily (yesterday's `order_complete_date`)
- **Starting next Friday:** switch automation schedule to weekly; keep the same skill/script

## Run Steps

1. From repo root, run:

```bash
python scripts/run_wrong_lt_monitor.py
```

2. Read artifacts:
   - `output/wrong_lt_monitor/slack_message.md` — post this to Slack
   - `output/wrong_lt_monitor/state.json` — open/resolved history (commit + push so the next run can diff)
   - `output/wrong_lt_monitor/wrong_lt_<date>.csv` — raw mismatched OPIDs

3. **Slack**: Post `slack_message.md` via the automation **Send to Slack** tool (or Slack MCP). Always notify when there are **new**, **reopened**, or **resolved** issues. Also notify on a true all-clear after prior open issues. Skip quiet "still ongoing, nothing changed" days unless the user/automation asks for `--notify-ongoing`.

4. **Persist state**: Commit and push `output/wrong_lt_monitor/state.json` (and optionally the dated CSV) on the monitoring branch so the next scheduled run sees prior open/resolved keys. If the automation has **Memories** enabled, also mirror the last bucket counts and open issue keys there as a backup.

5. Do **not** open a PR unless the user asks — state commits can go directly on the automation branch.

## First Run / Baseline

The first successful run will classify everything as **new** (today: hundreds of issue keys is expected). That establishes the open set. From the second run onward, Slack should emphasize **new / resolved / reopened** deltas only.

## Issue Identity

Issue key grain (not OPID):

`supplierid | Supplierpartid | ship_class_group | su_lt_type`

| Status | Meaning |
| --- | --- |
| new | Present today, never open before (and not in resolved history) |
| reopened | Present today after previously resolving |
| ongoing | Still open vs prior run |
| resolved | Was open last run, absent today |

## Query Rules

- SQL: `sql/wrong_lt_monitor.sql`
- Runner: `from gbq import query_df` via `scripts/run_wrong_lt_monitor.py`
- Window: `order_complete_date = CURRENT_DATE() - 1`
- Scope: `fulfillment_type = 'DS'`, `destination_country_id IN (1, 2)`
- Flag: ledger `baseleadtime * 24` ≠ expected Bulk SP/LP or Product part LT

## Slack Message Expectations

- Lead with status: NEW / REOPENED / RESOLVED / ONGOING / ALL CLEAR
- Include order date, open counts, and up to ~15 rows per section
- Prefer reopened and new sections first

## Automation Setup (Cursor)

Create at [cursor.com/automations](https://cursor.com/automations) (or `/automate`):

- **Trigger:** scheduled daily (e.g. `0 14 * * *` UTC ≈ after prior-day data lands)
- **Repo:** this O2S repo
- **Tools:** Send to Slack (+ Memories recommended); BigQuery via repo `gbq` credentials/env
- **Prompt:** use `references/automation_prompt.md` in this skill folder

Next Friday: change the schedule to weekly; leave skill/script unchanged.

## Manual Options

```bash
# Classify empty results against state (no BQ)
python scripts/run_wrong_lt_monitor.py --dry-run

# Always include ongoing in Slack output
python scripts/run_wrong_lt_monitor.py --notify-ongoing
```
