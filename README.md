# O2S

BigQuery (GBQ) connection utilities.

## Target project

| Setting | Value |
|---------|-------|
| Data project | `wf-gcp-us-ae-global-tnd-prod` |
| Dataset | `speed_and_reliability` (alias: `speed`) |
| Billing project | `wf-gcp-us-ae-profit-prod` |

The `speed` shorthand maps to the `speed_and_reliability` dataset in the global TND project.

## Setup

```bash
pip install -r requirements.txt
```

`GOOGLE_APPLICATION_CREDENTIALS` is injected in Cursor Cloud. It can be either a file path or inline service-account JSON; the client helper writes it to `.gcp/credentials.json` automatically.

## Verify connection

```bash
python scripts/connect_gbq.py
```

## Small Parcel data pulls

Column definitions and query rules for `HVE_perf_Monitoring` live in
[`docs/small_parcel/HVE_perf_Monitoring.md`](docs/small_parcel/HVE_perf_Monitoring.md).

Ask in plain language, for example:

- "Show IFR by STO for the last 7 days"
- "Top 10 suppliers by late order volume in March 2026"
- "Pull orders where `inducted_late = 1` for Decor suppliers"

## Usage

```python
from gbq import SP_TABLE_FQN, query_df

df = query_df(f"""
    SELECT sto, COUNT(DISTINCT ops) AS volume, AVG(inducted_on_time_or_early) AS ifr
    FROM {SP_TABLE_FQN}
    WHERE msbd_su >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
    GROUP BY sto
    ORDER BY volume DESC
    LIMIT 10
""")
```
