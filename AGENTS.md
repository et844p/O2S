# AGENTS.md

## Cursor Cloud specific instructions

### What this repo is
Python toolkit (no server/UI) for querying and analyzing Wayfair Speed & Reliability
supply-chain data in **Google BigQuery**. The `gbq/` package wraps auth + query
(`query`, `query_df`), `scripts/` holds runnable analyses, `sql/` holds queries, and
`docs/small_parcel/HVE_perf_Monitoring.md` documents the Small Parcel table/columns.
BigQuery is the only backend — there are no local services, databases, or containers to start.

### Running scripts (PYTHONPATH gotcha)
The `gbq` package is imported by top-level name but is not installed as a package, so the
repo root must be on `PYTHONPATH`. `scripts/run_weekend_shipping_analysis.py` and
`scripts/validate_get_clean_dates.py` insert the root themselves, but
`scripts/connect_gbq.py` and ad-hoc `python3 -c` snippets do not. Run from the repo root with:

```bash
PYTHONPATH=/workspace python3 scripts/connect_gbq.py
```

- Connectivity smoke test: `scripts/connect_gbq.py` (lists datasets/tables, runs `SELECT 1`).
- Weekend shipping analysis: `scripts/run_weekend_shipping_analysis.py` (writes CSV to `output/`; `output/*.csv` is committed, so use `--output /tmp/...` when only demoing).
- Small Parcel pulls are programmatic via `from gbq import query_df` against `HVE_perf_Monitoring` (follow the defaults in `.cursor/rules/small-parcel-gbq.mdc`).

### Credentials (important, non-obvious)
Auth uses the `GOOGLE_APPLICATION_CREDENTIALS` secret, which is injected as **inline
service-account JSON** (not a path). `gbq.client.ensure_credentials()` materializes that
JSON to `.gcp/credentials.json` (gitignored) on first use and points the env var at it.

Quirk: once `.gcp/credentials.json` already exists, `ensure_credentials()` uses
`os.environ.setdefault(...)`, which does **not** overwrite the still-inline-JSON env var, so
the BigQuery client then tries to open the inline JSON as a file path and fails with
`DefaultCredentialsError: File ... was not found`. On a fresh VM the file does not exist, so
the first invocation succeeds and creates it; **subsequent** invocations in the same VM can
hit this error. Fix by pointing the env var at the materialized file before running:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="$PWD/.gcp/credentials.json"
```

(Equivalently, delete `.gcp/credentials.json` to force re-materialization.) Do not commit
`.gcp/`.

### Lint / test
There is no lint config and no test suite in this repo. `python3 -m compileall gbq scripts`
is a quick syntax sanity check.
