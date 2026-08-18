#!/usr/bin/env python3
"""Run directs supplier cohort analysis against HVE_perf_Monitoring."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

_default_creds = ROOT / ".gcp" / "credentials.json"
if _default_creds.exists():
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(_default_creds)

from gbq import query_df

SQL_PATH = ROOT / "sql" / "directs_supplier_cohorts.sql"
OUTPUT_DIR = ROOT / "output" / "directs"

COHORT_EXPORTS = {
    "consistently_builds_directs": "consistently_builds_directs.csv",
    "sometimes_builds_directs": "sometimes_builds_directs.csv",
    "ghost_warehouses": "ghost_warehouses.csv",
    "misshipping": "misshipping.csv",
    "no_directs": "no_directs.csv",
}

WINDOW_LABELS = {
    "pdd_10w": "10-week promised delivery date",
    "msbd_2w": "2-week MSBD",
}


def _write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def _weighted_avg(series_val: pd.Series, series_wt: pd.Series) -> float | None:
    mask = series_val.notna() & series_wt.notna() & (series_wt > 0)
    if not mask.any():
        return None
    w = series_wt[mask].astype(float)
    v = series_val[mask].astype(float)
    return float((v * w).sum() / w.sum())


def _summary_frame(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for window, wdf in df.groupby("lookback_window", sort=False):
        for cohort, cdf in wdf.groupby("direct_cohort", sort=False):
            rows.append(
                {
                    "lookback_window": window,
                    "window_label": WINDOW_LABELS.get(window, window),
                    "direct_cohort": cohort,
                    "suppliers": len(cdf),
                    "total_vol": int(cdf["total_vol"].sum()),
                    "candidate_vol": int(cdf["candidate_vol"].sum()),
                    "direct_vol": int(cdf["direct_vol"].sum()),
                    "sparse_far_vol": int(cdf["sparse_far_vol"].sum()),
                    "jumbo_vol": int(cdf["jumbo_vol"].sum()),
                    "ghost_vol": int(cdf["ghost_vol"].sum()),
                    "misshipping_vol": int(cdf["misshipping_vol"].sum()),
                    "candidate_partition_ok": bool(cdf["candidate_partition_ok"].all()),
                    "ifr": _weighted_avg(cdf["ifr"], cdf["total_vol"]),
                    "delivery_rel": _weighted_avg(cdf["delivery_rel"], cdf["total_vol"]),
                    "ifr_candidate": _weighted_avg(
                        cdf["ifr_candidate"], cdf["candidate_vol"]
                    ),
                    "delivery_rel_candidate": _weighted_avg(
                        cdf["delivery_rel_candidate"], cdf["candidate_vol"]
                    ),
                    "ifr_direct": _weighted_avg(cdf["ifr_direct"], cdf["direct_vol"]),
                    "delivery_rel_direct": _weighted_avg(
                        cdf["delivery_rel_direct"], cdf["direct_vol"]
                    ),
                    "ifr_sparse_far": _weighted_avg(
                        cdf["ifr_sparse_far"], cdf["sparse_far_vol"]
                    ),
                    "delivery_rel_sparse_far": _weighted_avg(
                        cdf["delivery_rel_sparse_far"], cdf["sparse_far_vol"]
                    ),
                    "ifr_jumbo": _weighted_avg(cdf["ifr_jumbo"], cdf["jumbo_vol"]),
                    "delivery_rel_jumbo": _weighted_avg(
                        cdf["delivery_rel_jumbo"], cdf["jumbo_vol"]
                    ),
                    "ifr_ghost": _weighted_avg(cdf["ifr_ghost"], cdf["ghost_vol"]),
                    "delivery_rel_ghost": _weighted_avg(
                        cdf["delivery_rel_ghost"], cdf["ghost_vol"]
                    ),
                    "ifr_misshipping": _weighted_avg(
                        cdf["ifr_misshipping"], cdf["misshipping_vol"]
                    ),
                    "delivery_rel_misshipping": _weighted_avg(
                        cdf["delivery_rel_misshipping"], cdf["misshipping_vol"]
                    ),
                    "missing_actual_hub_vol": int(cdf["missing_actual_hub_vol"].sum()),
                }
            )
    return pd.DataFrame(rows).sort_values(
        ["lookback_window", "suppliers"], ascending=[True, False]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=OUTPUT_DIR,
        help="Directory for CSV exports",
    )
    parser.add_argument(
        "--window",
        choices=["pdd_10w", "msbd_2w", "all"],
        default="all",
        help="Which lookback window to export",
    )
    parser.add_argument(
        "--cohort",
        choices=[*COHORT_EXPORTS.keys(), "all"],
        default="all",
        help="Export a single cohort or all cohorts",
    )
    args = parser.parse_args()

    df = query_df(SQL_PATH.read_text())
    if args.window != "all":
        df = df[df["lookback_window"] == args.window].copy()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    full_path = args.output_dir / "directs_supplier_cohorts.csv"
    _write_csv(df, full_path)

    summary = _summary_frame(df)
    summary_path = args.output_dir / "directs_supplier_cohorts_summary.csv"
    _write_csv(summary, summary_path)

    print(f"Wrote {len(df):,} supplier-window rows to {full_path}")
    print(f"Wrote summary to {summary_path}")
    print()
    print(summary.to_string(index=False))
    print()

    examples = df[
        df["su_name"].astype(str).str.contains(
            "Edecor Center Inc._1 NJ 08110|Nathan James NV 89434|"
            "JLA Home GA 31407 - SV2|Unique Loom SC29707",
            regex=True,
            na=False,
        )
    ][
        [
            "lookback_window",
            "su_name",
            "direct_cohort",
            "parent_warehouse_states",
            "total_vol",
            "candidate_vol",
            "direct_vol",
            "jumbo_vol",
            "ghost_vol",
            "misshipping_vol",
            "candidate_partition_ok",
            "ifr",
            "delivery_rel",
            "ifr_candidate",
            "delivery_rel_candidate",
            "top_direct_hubs",
            "misshipping_hubs",
            "ghost_hubs",
        ]
    ]
    if not examples.empty:
        print("Calibration examples:")
        print(examples.to_string(index=False))
        print()

    cohorts = COHORT_EXPORTS.keys() if args.cohort == "all" else [args.cohort]
    windows = (
        sorted(df["lookback_window"].unique())
        if args.window == "all"
        else [args.window]
    )

    # Remove obsolete cohort files from prior schema
    for stale_pattern in (
        "*_ghost_warehouses_no_directs.csv",
        "*_non_compliant_shipping.csv",
    ):
        for stale in args.output_dir.glob(stale_pattern):
            stale.unlink(missing_ok=True)

    for window in windows:
        wdf = df[df["lookback_window"] == window]
        for cohort in cohorts:
            cdf = wdf[wdf["direct_cohort"] == cohort]
            out = args.output_dir / f"{window}_{COHORT_EXPORTS[cohort]}"
            _write_csv(cdf, out)
            print(f"  {window} / {cohort}: {len(cdf):,} -> {out.name}")


if __name__ == "__main__":
    main()
