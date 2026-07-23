"""BigQuery connection helpers for O2S."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pandas as pd
from google.cloud import bigquery

from gbq.config import BILLING_PROJECT, DATA_PROJECT, DATASET, DATASET_ALIASES

_DEFAULT_CREDS_PATH = Path(__file__).resolve().parent.parent / ".gcp" / "credentials.json"


def ensure_credentials(creds_path: Path | None = None) -> Path | None:
    """Resolve credentials for BigQuery.

    Priority:
    1. Existing `.gcp/credentials.json`
    2. `GOOGLE_APPLICATION_CREDENTIALS` file path
    3. Inline JSON in `GOOGLE_APPLICATION_CREDENTIALS`
    4. Application Default Credentials (`gcloud auth application-default login`)
    """
    path = creds_path or _DEFAULT_CREDS_PATH
    if path.exists():
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(path)
        return path

    raw = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
    if raw.startswith("{"):
        creds = json.loads(raw)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(creds, indent=2))
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(path)
        return path

    if raw:
        file_path = Path(raw)
        if file_path.exists():
            return file_path
        raise RuntimeError(f"GOOGLE_APPLICATION_CREDENTIALS file not found: {raw}")

    # Fall back to ADC from `gcloud auth application-default login`.
    return None


def resolve_dataset(dataset: str | None = None) -> str:
    """Resolve dataset shorthand (e.g. speed) to the actual dataset name."""
    name = dataset or DATASET
    return DATASET_ALIASES.get(name, name)


def table_ref(table: str, dataset: str | None = None, project: str | None = None) -> str:
    """Return a fully qualified BigQuery table reference."""
    return f"`{project or DATA_PROJECT}.{resolve_dataset(dataset)}.{table}`"


def get_client(project: str | None = None) -> bigquery.Client:
    """Return an authenticated BigQuery client."""
    ensure_credentials()
    return bigquery.Client(project=project or BILLING_PROJECT)


def query(sql: str, project: str | None = None, **job_config_kwargs: Any) -> bigquery.table.RowIterator:
    """Run a SQL query and return the result rows."""
    client = get_client(project)
    job_config = bigquery.QueryJobConfig(**job_config_kwargs) if job_config_kwargs else None
    return client.query(sql, job_config=job_config).result()


def query_df(sql: str, project: str | None = None, **job_config_kwargs: Any) -> pd.DataFrame:
    """Run a SQL query and return results as a pandas DataFrame."""
    return query(sql, project=project, **job_config_kwargs).to_dataframe()
