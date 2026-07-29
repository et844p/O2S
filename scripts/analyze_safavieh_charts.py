#!/usr/bin/env python3
"""Safavieh June MSBD charts — performance and badging opportunity visualizations."""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

OUT = ROOT / "output" / "safavieh"
CHARTS = ROOT / "docs" / "small_parcel" / "safavieh_charts"
WH_CSV = OUT / "safavieh_june_warehouse_analysis.csv"
SCEN_CSV = OUT / "safavieh_june_badging_scenarios.csv"
WH_SIM_CSV = OUT / "safavieh_june_wh_badging_sim.csv"

NAVY = "#1a365d"
ACCENT = "#2e86ab"
GREEN = "#27ae60"
ORANGE = "#f39c12"
RED = "#c0392b"
GRAY = "#95a5a6"


def _wh_label(row: pd.Series) -> str:
    city = str(row["city_name"]).strip()
    return f"{city}, {row['state_name']}"


def load_warehouse() -> pd.DataFrame:
    df = pd.read_csv(WH_CSV)
    df = df[df["june_msbd_vol"] >= 200].copy()
    df["warehouse"] = df.apply(_wh_label, axis=1)
    return df.sort_values("june_msbd_vol", ascending=True)


def chart_ifr_by_warehouse(df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = [
        GREEN if x >= 0.9 else ORANGE if x >= 0.85 else RED
        for x in df["june_IFR"]
    ]
    bars = ax.barh(df["warehouse"], df["june_IFR"], color=colors, height=0.7)
    ax.axvline(0.85, color=NAVY, linestyle="--", linewidth=1.2, label="85% target")
    ax.axvline(0.9, color=GREEN, linestyle=":", linewidth=1, alpha=0.7, label="90%")
    ax.set_xlim(0.65, 1.02)
    ax.set_xlabel("Induction Fill Rate (June MSBD)")
    ax.set_title("Safavieh — IFR by Warehouse (June 2026 MSBD)")
    for bar, vol in zip(bars, df["june_msbd_vol"]):
        ax.text(
            bar.get_width() + 0.01,
            bar.get_y() + bar.get_height() / 2,
            f"{bar.get_width():.0%}  (n={vol:,})",
            va="center",
            fontsize=9,
        )
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(CHARTS / "01_ifr_by_warehouse.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def chart_before_2pm_induction(df: pd.DataFrame) -> None:
    sub = df.dropna(subset=["pct_same_day_induct_before_2pm"]).copy()
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = [
        GREEN if x >= 0.8 else ORANGE if x >= 0.6 else RED
        for x in sub["pct_same_day_induct_before_2pm"]
    ]
    bars = ax.barh(sub["warehouse"], sub["pct_same_day_induct_before_2pm"], color=colors, height=0.7)
    ax.axvline(0.68, color=NAVY, linestyle="--", linewidth=1.2, label="Network avg (68%)")
    ax.axvline(0.85, color=GREEN, linestyle=":", linewidth=1, alpha=0.6, label="85% opportunity bar")
    ax.set_xlim(0, 1.05)
    ax.set_xlabel("Same-day induction rate (orders placed before 2pm)")
    ax.set_title("Safavieh — Before-2pm Same-Day Induction by Warehouse")
    ax.text(
        0.02, 0.02,
        "Toolkit hourly · Mon–Fri (excl. Sun/Sat) · June 2026",
        transform=ax.transAxes,
        fontsize=9,
        color=GRAY,
    )
    for bar, pct in zip(bars, sub["pct_same_day_induct_before_2pm"]):
        ax.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height() / 2,
                f"{pct:.0%}", va="center", fontsize=9)
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(CHARTS / "02_before_2pm_same_day_induction.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def chart_opportunity_gap(df: pd.DataFrame) -> None:
    """IFR vs before-2pm induction — shows ops vs promise gap."""
    sub = df.dropna(subset=["pct_same_day_induct_before_2pm"]).copy()
    fig, ax = plt.subplots(figsize=(9, 7))
    x = sub["pct_same_day_induct_before_2pm"] * 100
    y = sub["june_IFR"] * 100
    sizes = sub["june_msbd_vol"] / 30
    ax.scatter(x, y, s=sizes, c=NAVY, alpha=0.65, edgecolors="white", linewidth=0.8)
    for _, row in sub.iterrows():
        ax.annotate(
            row["warehouse"].replace(", ", "\n"),
            (row["pct_same_day_induct_before_2pm"] * 100, row["june_IFR"] * 100),
            fontsize=7,
            ha="center",
            va="bottom",
            xytext=(0, 6),
            textcoords="offset points",
        )
    ax.axhline(90, color=GREEN, linestyle="--", alpha=0.5)
    ax.axvline(68, color=NAVY, linestyle="--", alpha=0.5)
    ax.set_xlabel("Same-day induction before 2pm (%)")
    ax.set_ylabel("IFR (%)")
    ax.set_title("Safavieh — Performance vs Before-2pm Induction Opportunity")
    ax.set_xlim(35, 100)
    ax.set_ylim(72, 102)
    ax.text(72, 73, "Gap zone:\nhigh IFR but low\nbefore-2pm induct", fontsize=9, color=RED, alpha=0.8)
    fig.tight_layout()
    fig.savefig(CHARTS / "03_ifr_vs_before_2pm_scatter.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def chart_badging_tiers(scen: pd.DataFrame) -> None:
    tiers = ["1-day", "2-day", "3-day", "Fast (≤5d)"]
    cols = ["badge_1d_pct", "badge_2d_pct", "badge_3d_pct", "badge_5d_fast_pct"]
    current = scen.loc[scen["scenario"] == "current", cols].iloc[0].values
    full = scen.loc[scen["scenario"] == "policy_plus_weekend", cols].iloc[0].values

    x = np.arange(len(tiers))
    width = 0.35
    fig, ax = plt.subplots(figsize=(9, 5.5))
    b1 = ax.bar(x - width / 2, current, width, label="June actual", color=GRAY)
    b2 = ax.bar(x + width / 2, full, width, label="Full simulation", color=ACCENT)
    ax.set_ylabel("Badge coverage (%)")
    ax.set_title("Safavieh — Badging Coverage by Speed Tier (June MSBD)")
    ax.set_xticks(x)
    ax.set_xticklabels(tiers)
    ax.set_ylim(0, 100)
    for bars in (b1, b2):
        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, h + 1, f"{h:.1f}%", ha="center", fontsize=9)
    # uplift annotations
    for i, (c, f) in enumerate(zip(current, full)):
        uplift = f - c
        ax.annotate(f"+{uplift:.1f} pp", xy=(i, max(c, f) + 8), ha="center", fontsize=10,
                    color=GREEN, fontweight="bold")
    ax.legend()
    fig.tight_layout()
    fig.savefig(CHARTS / "04_badging_tiers_current_vs_sim.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def chart_badging_uplift(scen: pd.DataFrame) -> None:
    full = scen.loc[scen["scenario"] == "policy_plus_weekend"].iloc[0]
    current = scen.loc[scen["scenario"] == "current"].iloc[0]
    tiers = ["1-day", "2-day", "3-day", "Fast ≤5d"]
    newly = [
        full["newly_fast_1d"],
        full["newly_fast_2d"],
        full["newly_fast_3d"],
        full["newly_fast_5d"],
    ]
    uplifts = [
        full["badge_1d_pct"] - current["badge_1d_pct"],
        full["badge_2d_pct"] - current["badge_2d_pct"],
        full["badge_3d_pct"] - current["badge_3d_pct"],
        full["badge_5d_fast_pct"] - current["badge_5d_fast_pct"],
    ]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    colors = [ACCENT, ACCENT, ACCENT, ORANGE]
    ax1.barh(tiers, uplifts, color=colors)
    ax1.set_xlabel("Uplift (percentage points)")
    ax1.set_title("Badge uplift — full simulation vs June")
    for i, v in enumerate(uplifts):
        ax1.text(v + 0.3, i, f"+{v:.1f} pp", va="center", fontsize=10)

    ax2.barh(tiers, newly, color=[GREEN, GREEN, GREEN, ORANGE])
    ax2.set_xlabel("Newly badged orders")
    ax2.set_title("New orders gaining badge (June volume)")
    for i, v in enumerate(newly):
        ax2.text(v + 200, i, f"{int(v):,}", va="center", fontsize=10)

    fig.suptitle("Safavieh — Badging Opportunity (2pm + no cushion + weekend)", fontsize=13, y=1.02)
    fig.tight_layout()
    fig.savefig(CHARTS / "05_badging_opportunity_uplift.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def chart_3d_badge_by_warehouse(sim_df: pd.DataFrame) -> None:
    sim_df = sim_df.copy()
    sim_df["warehouse"] = sim_df.apply(
        lambda r: f"{str(r['city_name']).strip()}, {r['state_name']}", axis=1
    )
    sim_df = sim_df.sort_values("vol", ascending=True)
    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(sim_df))
    w = 0.35
    ax.barh(x - w / 2, sim_df["current_3d"] * 100, w, label="June 3-day badge", color=GRAY)
    ax.barh(x + w / 2, sim_df["sim_3d"] * 100, w, label="Simulated 3-day", color=ACCENT)
    ax.set_yticks(x)
    ax.set_yticklabels(sim_df["warehouse"], fontsize=9)
    ax.set_xlabel("3-day badge coverage (%)")
    ax.set_title("Safavieh — 3-Day Badge by Warehouse (June MSBD)")
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(CHARTS / "06_3d_badge_by_warehouse.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def chart_volume_by_warehouse(df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    colors = plt.cm.Blues(np.linspace(0.35, 0.85, len(df)))
    ax.barh(df["warehouse"], df["june_msbd_vol"], color=colors)
    ax.set_xlabel("June MSBD volume (distinct ops)")
    ax.set_title("Safavieh — Volume by Warehouse (June 2026)")
    for i, (wh, vol) in enumerate(zip(df["warehouse"], df["june_msbd_vol"])):
        ax.text(vol + 100, i, f"{vol:,}", va="center", fontsize=9)
    fig.tight_layout()
    fig.savefig(CHARTS / "07_volume_by_warehouse.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    CHARTS.mkdir(parents=True, exist_ok=True)
    plt.style.use("seaborn-v0_8-whitegrid")

    wh = load_warehouse()
    scen = pd.read_csv(SCEN_CSV)

    chart_ifr_by_warehouse(wh)
    chart_before_2pm_induction(wh)
    chart_opportunity_gap(wh)
    chart_badging_tiers(scen)
    chart_badging_uplift(scen)
    chart_volume_by_warehouse(wh)

    if WH_SIM_CSV.exists():
        chart_3d_badge_by_warehouse(pd.read_csv(WH_SIM_CSV))

    print(f"Charts saved to {CHARTS}")
    for p in sorted(CHARTS.glob("*.png")):
        print(f"  {p.name}")


if __name__ == "__main__":
    main()
