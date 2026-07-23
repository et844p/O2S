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

# Large Parcel OTR tracking (Pickup Pal primary PO-level table).
LP_OTR_TABLE = "OTR_Tracking_ET"
LP_OTR_TABLE_FQN = f"`{DATA_PROJECT}.{DATASET}.{LP_OTR_TABLE}`"

# Large Parcel pickup planning and execution tables.
LP_FTL_VARIANCE_FQN = "`wf-gcp-us-ae-global-tnd-prod.tnd_reporting.FM_LP_FTL_Variance`"
LP_FTL_MILESTONES_FQN = "`wf-gcp-us-ae-gbl-prf-mgmt-prod.reporting.FTL_Milestones`"
LP_ROUTING_MASTER_FQN = "`wf-gcp-us-ae-global-tnd-prod.tnd_reporting.FM_Routing_Master`"
