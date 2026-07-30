#!/usr/bin/env python3
"""Enrich warehouse badging gain with volume-weighted network (parent) contribution."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "safavieh"
GAIN_CSV = OUT / "safavieh_june_badging_gain_by_warehouse.csv"
SCEN_CSV = OUT / "safavieh_june_badging_scenarios.csv"
ENRICHED_CSV = OUT / "safavieh_june_badging_gain_volume_weighted.csv"

NETWORK_VOL_FALLBACK = 73294


def enrich_gain_table(network_vol: int | None = None) -> pd.DataFrame:
    df = pd.read_csv(GAIN_CSV)
    if network_vol is None:
        if SCEN_CSV.exists():
            scen = pd.read_csv(SCEN_CSV)
            network_vol = int(scen.loc[scen["scenario"] == "current", "volume"].iloc[0])
        else:
            network_vol = int(df["vol"].sum())

    df["warehouse"] = df["city_name"].str.strip() + ", " + df["state_name"]
    df["pct_network_vol"] = (df["vol"] / network_vol * 100).round(2)

    tiers = [
        ("1d", "1"),
        ("2d", "2"),
        ("3d", "3"),
        ("fast", "5"),
    ]
    for label, _ in tiers:
        cutoff_col = f"cutoff_new_{label}" if label != "fast" else "cutoff_new_fast"
        wknd_col = f"weekend_new_{label}" if label != "fast" else "weekend_new_fast"
        df[f"network_contrib_cutoff_{label}_pp"] = (
            df[cutoff_col] / network_vol * 100
        ).round(3)
        df[f"network_contrib_weekend_{label}_pp"] = (
            df[wknd_col] / network_vol * 100
        ).round(3)

    # Volume-weighted pp: share of vol × warehouse pp gain (approximate attribution)
    df["vol_weighted_weekend_3d_pp"] = (
        df["pct_network_vol"] / 100 * df["weekend_gain_3d_pp"]
    ).round(3)

    return df.sort_values("vol", ascending=False)


def main() -> None:
    df = enrich_gain_table()
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(ENRICHED_CSV, index=False)
    print(f"Saved {len(df)} rows → {ENRICHED_CSV}")
    print(
        df[
            [
                "warehouse",
                "vol",
                "pct_network_vol",
                "weekend_gain_3d_pp",
                "network_contrib_weekend_3d_pp",
                "weekend_new_3d",
            ]
        ].head(8).to_string(index=False)
    )


if __name__ == "__main__":
    main()
