"""BigQuery project and dataset configuration."""

# Data project and dataset for O2S / speed team work.
DATA_PROJECT = "wf-gcp-us-ae-global-tnd-prod"
DATASET = "speed_and_reliability"

# Service account home project used for query job billing.
BILLING_PROJECT = "wf-gcp-us-ae-profit-prod"

# Shorthand aliases for datasets (e.g. wf-gcp-us-ae-global-tnd-prod.speed).
DATASET_ALIASES = {
    "speed": DATASET,
}

# Small Parcel monitoring table.
SP_TABLE = "HVE_perf_Monitoring"
SP_TABLE_FQN = f"`{DATA_PROJECT}.{DATASET}.{SP_TABLE}`"

# Large Parcel monitoring table.
LP_TABLE = "LP_dash_ET"
LP_TABLE_FQN = f"`{DATA_PROJECT}.{DATASET}.{LP_TABLE}`"

# OTR pickup tracking (join to LP for OTR-routed suppliers).
OTR_TRACKING_TABLE = "OTR_Tracking_ET"
OTR_TRACKING_TABLE_FQN = f"`{DATA_PROJECT}.{DATASET}.{OTR_TRACKING_TABLE}`"
