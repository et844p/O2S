#!/usr/bin/env python3
"""Verify BigQuery connectivity."""

from gbq.client import get_client


def main() -> None:
    client = get_client()
    print(f"Connected to project: {client.project}")

    datasets = list(client.list_datasets(max_results=20))
    print(f"Datasets ({len(datasets)}):")
    for ds in datasets:
        print(f"  - {ds.dataset_id}")


if __name__ == "__main__":
    main()
