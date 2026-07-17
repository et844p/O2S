# O2S

## BigQuery (GBQ) setup

This repo is configured to query BigQuery through Google's official MCP Toolbox.

### What is already configured

- **GCP project:** `wf-gcp-us-ae-profit-prod`
- **MCP server:** `.cursor/mcp.json` (BigQuery toolbox via `npx @toolbox-sdk/server`)
- **Credential bootstrap:** `scripts/bootstrap-gcp-credentials.sh`

### Cloud Agent secret

If you use Cursor Cloud Agents, add a secret named `GOOGLE_APPLICATION_CREDENTIALS` containing your service account JSON. The bootstrap script writes that JSON to `/workspace/.gcp/service-account.json` because GCP libraries expect a file path, not inline JSON.

Recommended service account roles:

- `roles/bigquery.dataViewer` (read schemas and data)
- `roles/bigquery.jobUser` (run queries)

### Local Cursor setup

1. Ensure Node.js and `npx` are available.
2. Add the same `GOOGLE_APPLICATION_CREDENTIALS` secret/value, or run:

```bash
export GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/to/service-account.json
```

3. Open **Cursor Settings → MCP** and confirm the `bigquery` server shows a green status.
4. Ask the agent things like: "List BigQuery datasets in wf-gcp-us-ae-profit-prod".

### Verify connectivity

```bash
./scripts/bootstrap-gcp-credentials.sh
GOOGLE_APPLICATION_CREDENTIALS=/workspace/.gcp/service-account.json python3 - <<'PY'
from google.cloud import bigquery
client = bigquery.Client(project="wf-gcp-us-ae-profit-prod")
print([d.dataset_id for d in client.list_datasets(max_results=10)])
PY
```

### Available MCP tools

Once connected, the agent can use tools such as `list_dataset_ids`, `list_table_ids`, `get_table_info`, `execute_sql`, `search_catalog`, and `ask_data_insights`.
