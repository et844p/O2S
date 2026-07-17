#!/usr/bin/env python3
"""Verify BigQuery connectivity."""

from gbq.client import get_client, query, resolve_dataset, table_ref
from gbq.config import BILLING_PROJECT, DATA_PROJECT, DATASET


def main() -> None:
    client = get_client()
    print(f"Billing project: {BILLING_PROJECT}")
    print(f"Data project:    {DATA_PROJECT}")
    print(f"Dataset:         {DATASET} (alias: speed)")
    print(f"Client project:  {client.project}")

    data_client = get_client(DATA_PROJECT)
    datasets = list(data_client.list_datasets(max_results=20))
    print(f"\nDatasets in {DATA_PROJECT} ({len(datasets)}):")
    for ds in datasets:
        marker = " <-- default" if ds.dataset_id == DATASET else ""
        print(f"  - {ds.dataset_id}{marker}")

    tables = list(data_client.list_tables(f"{DATA_PROJECT}.{DATASET}", max_results=10))
    print(f"\nSample tables in {DATASET} ({len(tables)} shown):")
    for t in tables:
        print(f"  - {t.table_id}")

    rows = list(query(f"SELECT 1 AS ok"))
    print(f"\nQuery test: ok={rows[0].ok}")


if __name__ == "__main__":
    main()
