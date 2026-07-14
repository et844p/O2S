# O2S

BigQuery (GBQ) connection utilities.

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
from gbq import get_client, query, query_df

# List datasets
client = get_client()
print(client.project)

# Run SQL
rows = query("SELECT 1 AS ok")
df = query_df("SELECT * FROM `wf-gcp-us-ae-profit-prod.marketplace.some_table` LIMIT 10")
```
