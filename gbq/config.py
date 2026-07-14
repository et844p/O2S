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
