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

## Usage

```python
from gbq import DATA_PROJECT, DATASET, get_client, query, query_df, table_ref

client = get_client()
print(client.project)

# Run SQL against the speed dataset
df = query_df(f"SELECT * FROM {table_ref('FM_LP_SpeedMetricsRaw_Global')} LIMIT 10")

# Or use the fully qualified name directly
df = query_df("""
    SELECT *
    FROM `wf-gcp-us-ae-global-tnd-prod.speed_and_reliability.FM_LP_SpeedMetricsRaw_Global`
    LIMIT 10
""")
```
