# Wrong LT Monitor — Automation Prompt

Copy into a Cursor Automation (daily schedule). Retarget Slack channel as needed.

---

Run the project skill **wrong-lt-monitor**.

1. Execute `python scripts/run_wrong_lt_monitor.py` from the repo root.
2. Read `output/wrong_lt_monitor/slack_message.md`.
3. If the script printed `notify=True`, send that message to Slack (configured channel) using Send to Slack.
4. If `notify=False`, do not spam Slack; leave a one-line run note in Memories only.
5. Commit and push updates under `output/wrong_lt_monitor/` (especially `state.json`) so the next run can detect resolved/reopened issues.
6. In Memories, store: last run date, last order date, open issue count, and the list of open issue keys.
7. Do not open a pull request unless state/script changes need review.

Focus only on incorrect lead-time mismatches for yesterday's DS US/CA orders.
