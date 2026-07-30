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
GAIN_CSV = OUT / "safavieh_june_badging_gain_by_warehouse.csv"
GAIN_VW_CSV = OUT / "safavieh_june_badging_gain_volume_weighted.csv"
FRI_SAT_SUN_CSV = OUT / "safavieh_june_fri_sat_sunday_induction_by_wh.csv"
FRI_SAT_WKND_CSV = OUT / "safavieh_june_fri_sat_weekend_shipping_by_wh.csv"
FRI_SAT_LIFT_CSV = OUT / "safavieh_june_fri_sat_badging_lift.csv"
L6W_WKND_CSV = OUT / "safavieh_l6w_msbd_weekend_shipping_by_wh.csv"
GAIN_ACCOUNT_CSV = OUT / "safavieh_june_badging_gain_account.csv"

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


def _stacked_opportunity_lifts(scen: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Current + weekend (Fri/Sat −1 vs current) + cutoff additional → full policy stack."""
    cols = ["badge_1d_pct", "badge_2d_pct", "badge_3d_pct", "badge_5d_fast_pct"]
    cur = scen.loc[scen["scenario"] == "current", cols].iloc[0].values.astype(float)
    fri = scen.loc[scen["scenario"] == "fri_sat_o2d_minus1", cols].iloc[0].values.astype(float)
    full = scen.loc[scen["scenario"] == "policy_plus_weekend", cols].iloc[0].values.astype(float)
    weekend_lift = fri - cur
    cutoff_lift = full - fri
    return cur, weekend_lift, cutoff_lift, full


def chart_network_cohort_current_and_lifts(scen: pd.DataFrame) -> None:
    """Stacked bars: current + weekend (Fri/Sat −1 vs current) + cutoff additional → full stack."""
    if "fri_sat_o2d_minus1" not in scen["scenario"].values:
        return

    tiers = ["1-day", "2-day", "3-day", "Fast (≤5d)"]
    cur, weekend_lift, cutoff_lift, full = _stacked_opportunity_lifts(scen)

    x = np.arange(len(tiers))
    width = 0.55
    edge = {"edgecolor": "white", "linewidth": 1.2}

    fig, ax = plt.subplots(figsize=(10, 6.5))
    ax.bar(x, cur, width, label="Current (June stated)", color=GRAY, **edge)
    ax.bar(
        x,
        weekend_lift,
        width,
        bottom=cur,
        label="Weekend opportunity (Fri/Sat −1 vs current)",
        color=ORANGE,
        **edge,
    )
    ax.bar(
        x,
        cutoff_lift,
        width,
        bottom=cur + weekend_lift,
        label="Cutoff opportunity (2pm / no cushion, additional)",
        color=ACCENT,
        **edge,
    )

    ax.set_ylabel("Badge coverage (%)")
    ax.set_title(
        "Safavieh Network — Weekend + Cutoff Badge Opportunity (stacked)\n"
        "June MSBD · Fri/Sat −1 vs current, then additional cushion / 2pm cutoff to full stack"
    )
    ax.set_xticks(x)
    ax.set_xticklabels(tiers)
    ax.set_ylim(0, 100)
    ax.set_xlim(-0.6, len(tiers) - 0.4)

    for i in range(len(tiers)):
        total = cur[i] + weekend_lift[i] + cutoff_lift[i]
        ax.text(
            x[i],
            total + 1.5,
            f"{total:.1f}%",
            ha="center",
            va="bottom",
            fontsize=11,
            fontweight="bold",
            color=NAVY,
        )
        if cur[i] >= 3.0:
            ax.text(
                x[i],
                cur[i] / 2,
                f"{cur[i]:.1f}%",
                ha="center",
                va="center",
                fontsize=9,
                color="white",
                fontweight="bold",
            )
        if weekend_lift[i] >= 0.8:
            ax.text(
                x[i],
                cur[i] + weekend_lift[i] / 2,
                f"+{weekend_lift[i]:.1f} pp",
                ha="center",
                va="center",
                fontsize=9,
                color="white",
                fontweight="bold",
            )
        if cutoff_lift[i] >= 1.0:
            ax.text(
                x[i],
                cur[i] + weekend_lift[i] + cutoff_lift[i] / 2,
                f"+{cutoff_lift[i]:.1f} pp",
                ha="center",
                va="center",
                fontsize=9,
                color="white",
                fontweight="bold",
            )

    ax.legend(loc="upper left", framealpha=0.95)
    ax.text(
        0.99,
        0.02,
        "73,294 ops · weekend slice = Fri/Sat −1 vs current stated (matches chart 08)",
        transform=ax.transAxes,
        ha="right",
        fontsize=9,
        color=GRAY,
    )
    fig.tight_layout()
    out13 = CHARTS / "13_network_cohort_current_and_lift.png"
    out24 = CHARTS / "24_cutoff_weekend_opportunity_stacked.png"
    fig.savefig(out13, dpi=150, bbox_inches="tight")
    fig.savefig(out24, dpi=150, bbox_inches="tight")
    plt.close(fig)


def chart_stacked_opportunity_pp_only(scen: pd.DataFrame) -> None:
    """Stacked: current (base) + weekend (Fri/Sat −1 vs current) + cutoff additional."""
    if "fri_sat_o2d_minus1" not in scen["scenario"].values:
        return

    tiers = ["1-day", "2-day", "3-day", "Fast (≤5d)"]
    cur, weekend_lift, cutoff_lift, full = _stacked_opportunity_lifts(scen)

    x = np.arange(len(tiers))
    width = 0.55
    edge = {"edgecolor": "white", "linewidth": 1.2}

    fig, ax = plt.subplots(figsize=(10, 6.5))
    ax.bar(x, cur, width, label="Current (June stated)", color=GRAY, **edge)
    ax.bar(
        x,
        weekend_lift,
        width,
        bottom=cur,
        label="Weekend opportunity (Fri/Sat −1 vs current)",
        color=ORANGE,
        **edge,
    )
    ax.bar(
        x,
        cutoff_lift,
        width,
        bottom=cur + weekend_lift,
        label="Cutoff opportunity (2pm / no cushion, additional)",
        color=ACCENT,
        **edge,
    )

    ax.set_ylabel("Badge coverage (%)")
    ax.set_title(
        "Safavieh Network — Weekend + Cutoff Opportunity (stacked pp)\n"
        "June MSBD · Fri/Sat −1 vs current, then additional cushion / 2pm cutoff"
    )
    ax.set_xticks(x)
    ax.set_xticklabels(tiers)
    ax.set_ylim(0, 100)
    ax.set_xlim(-0.6, len(tiers) - 1 + 0.4)

    for i in range(len(tiers)):
        total = cur[i] + weekend_lift[i] + cutoff_lift[i]
        ax.text(
            x[i],
            total + 1.5,
            f"{total:.1f}%",
            ha="center",
            va="bottom",
            fontsize=11,
            fontweight="bold",
            color=NAVY,
        )
        if cur[i] >= 1.0:
            ax.text(
                x[i],
                cur[i] / 2,
                f"{cur[i]:.1f}%",
                ha="center",
                va="center",
                fontsize=9,
                color="white",
                fontweight="bold",
            )
        if weekend_lift[i] >= 0.5:
            ax.text(
                x[i],
                cur[i] + weekend_lift[i] / 2,
                f"+{weekend_lift[i]:.1f} pp",
                ha="center",
                va="center",
                fontsize=9,
                color="white",
                fontweight="bold",
            )
        if cutoff_lift[i] >= 0.5:
            ax.text(
                x[i],
                cur[i] + weekend_lift[i] + cutoff_lift[i] / 2,
                f"+{cutoff_lift[i]:.1f} pp",
                ha="center",
                va="center",
                fontsize=9,
                color="white",
                fontweight="bold",
            )

    ax.legend(loc="upper left")
    fig.tight_layout()
    fig.savefig(CHARTS / "25_cutoff_weekend_opportunity_pp_stacked.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def chart_network_current_vs_fri_sat_minus1(scen: pd.DataFrame) -> None:
    """Grouped bars: current stated vs Fri/Sat −1 only (parallel policy, not stacked)."""
    if "fri_sat_o2d_minus1" not in scen["scenario"].values:
        return

    tiers = ["1-day", "2-day", "3-day", "Fast (≤5d)"]
    cols = ["badge_1d_pct", "badge_2d_pct", "badge_3d_pct", "badge_5d_fast_pct"]
    cur = scen.loc[scen["scenario"] == "current", cols].iloc[0].values.astype(float)
    fri = scen.loc[scen["scenario"] == "fri_sat_o2d_minus1", cols].iloc[0].values.astype(float)
    lift = fri - cur

    x = np.arange(len(tiers))
    width = 0.35
    fig, ax = plt.subplots(figsize=(9, 6))
    b1 = ax.bar(x - width / 2, cur, width, label="Current (June stated)", color=GRAY)
    b2 = ax.bar(x + width / 2, fri, width, label="Fri/Sat −1 o2d only", color=ORANGE)

    ax.set_ylabel("Badge coverage (%)")
    ax.set_title(
        "Safavieh Network — Current vs Fri/Sat −1 o2d (standalone)\n"
        "Not stacked with cutoff — weekend promise vs current stated"
    )
    ax.set_xticks(x)
    ax.set_xticklabels(tiers)
    ax.set_ylim(0, 100)
    for bars in (b1, b2):
        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, h + 1, f"{h:.1f}%", ha="center", fontsize=9)
    for i, l in enumerate(lift):
        ax.annotate(f"+{l:.1f} pp", xy=(i, max(cur[i], fri[i]) + 6), ha="center",
                    fontsize=10, color=GREEN, fontweight="bold")
    ax.legend(loc="upper left")
    fig.tight_layout()
    fig.savefig(CHARTS / "23_network_current_vs_fri_sat_minus1.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def chart_weekend_incremental(scen: pd.DataFrame) -> None:
    """Fri/Sat −1 o2d vs current stated badges."""
    if "fri_sat_o2d_minus1" not in scen["scenario"].values:
        return
    current = scen.loc[scen["scenario"] == "current"].iloc[0]
    fri = scen.loc[scen["scenario"] == "fri_sat_o2d_minus1"].iloc[0]
    tiers = ["1-day", "2-day", "3-day", "Fast ≤5d"]
    cols = ["badge_1d_pct", "badge_2d_pct", "badge_3d_pct", "badge_5d_fast_pct"]
    uplifts = [fri[c] - current[c] for c in cols]
    newly = [int(fri[f"newly_fast_{t}"]) for t in ["1d", "2d", "3d", "5d"]]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    colors = [ORANGE, ORANGE, ACCENT, GRAY]
    ax1.bar(tiers, uplifts, color=colors)
    ax1.set_ylabel("Incremental uplift (pp)")
    ax1.set_title("Sunday MSBD promise (Fri/Sat placed) — after 2pm + no cushion")
    for i, v in enumerate(uplifts):
        ax1.text(i, v + 0.15, f"+{v:.1f}", ha="center", fontweight="bold")

    ax2.bar(tiers, newly, color=colors)
    ax2.set_ylabel("Additional newly badged orders")
    ax2.set_title("Orders gaining badge from weekend (incremental)")
    for i, v in enumerate(newly):
        ax2.text(i, v + 150, f"{v:,}", ha="center", fontsize=9)

    fig.suptitle(
        "Safavieh parent account — Sunday MSBD badge lift (Fri/Sat placed, June MSBD)",
        fontsize=13,
    )
    fig.tight_layout()
    fig.savefig(CHARTS / "08_weekend_incremental_by_tier.png", dpi=150, bbox_inches="tight")
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


def _load_gain_volume_weighted() -> pd.DataFrame:
    if GAIN_VW_CSV.exists():
        df = pd.read_csv(GAIN_VW_CSV)
    else:
        from scripts.enrich_safavieh_gain_volume_weighted import enrich_gain_table

        df = enrich_gain_table()
        df.to_csv(GAIN_VW_CSV, index=False)
    df = df[df["vol"] >= 200].copy()
    df["warehouse"] = df["city_name"].str.strip() + ", " + df["state_name"]
    return df.sort_values("vol", ascending=True)


def chart_wh_pp_vs_network_contribution_3d(df: pd.DataFrame) -> None:
    """Warehouse 3-day pp gain vs contribution to parent account pp (volume-weighted)."""
    sub = df.sort_values("vol", ascending=True)
    y = np.arange(len(sub))
    h = 0.35

    fig, ax = plt.subplots(figsize=(11, 7))
    wh_pp = sub["weekend_gain_3d_pp"].values
    net_pp = sub["network_contrib_weekend_3d_pp"].values
    cutoff_wh = sub["cutoff_gain_3d_pp"].values
    cutoff_net = sub["network_contrib_cutoff_3d_pp"].values

    ax.barh(y - h / 2, cutoff_wh, h, label="Cutoff: warehouse pp gain", color=GRAY, alpha=0.85)
    ax.barh(y + h / 2, cutoff_net, h, label="Cutoff: parent account pp", color=ACCENT, alpha=0.9)

    ax.set_yticks(y)
    ax.set_yticklabels(sub["warehouse"], fontsize=9)
    ax.set_xlabel("Percentage points (3-day badge)")
    ax.set_title(
        "Safavieh — 3-Day Badge: Warehouse Gain vs Parent Account Contribution\n"
        "(parent pp = newly badged orders ÷ network volume)"
    )
    ax.legend(loc="lower right", fontsize=9)

    for i, (w, n, vol_pct) in enumerate(
        zip(cutoff_wh, cutoff_net, sub["pct_network_vol"])
    ):
        if w > 1:
            ax.text(w + 0.3, i - h / 2, f"+{w:.1f} wh", va="center", fontsize=7, color=GRAY)
        ax.text(n + 0.15, i + h / 2, f"+{n:.2f} net ({vol_pct:.0f}% vol)", va="center", fontsize=7)

    fig.tight_layout()
    fig.savefig(CHARTS / "09_3d_cutoff_wh_vs_network_pp.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(11, 7))
    ax.barh(y - h / 2, wh_pp, h, label="Weekend: warehouse pp gain", color=ORANGE, alpha=0.85)
    ax.barh(y + h / 2, net_pp, h, label="Weekend: parent account pp", color=GREEN, alpha=0.9)
    ax.set_yticks(y)
    ax.set_yticklabels(sub["warehouse"], fontsize=9)
    ax.set_xlabel("Percentage points (3-day badge)")
    ax.set_title(
        "Safavieh — 3-Day Badge: Sunday MSBD Warehouse Gain vs Parent Account Contribution"
    )
    ax.legend(loc="lower right", fontsize=9)
    for i, (w, n, vol_pct) in enumerate(zip(wh_pp, net_pp, sub["pct_network_vol"])):
        if w > 2:
            ax.text(w + 0.3, i - h / 2, f"+{w:.1f} wh", va="center", fontsize=7, color=ORANGE)
        ax.text(n + 0.15, i + h / 2, f"+{n:.2f} net ({vol_pct:.0f}% vol)", va="center", fontsize=7)
    fig.tight_layout()
    fig.savefig(CHARTS / "10_3d_weekend_wh_vs_network_pp.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def chart_network_contrib_stacked_3d(df: pd.DataFrame) -> None:
    """Stacked bar: each warehouse's slice of parent +9pp weekend 3-day uplift (Fri/Sat −1 vs current)."""
    sub = df.sort_values("network_contrib_weekend_3d_pp", ascending=True)
    contrib = sub["network_contrib_weekend_3d_pp"]
    total = contrib.sum()

    fig, ax = plt.subplots(figsize=(10, 5))
    colors = plt.cm.Blues(np.linspace(0.35, 0.9, len(sub)))
    left = 0.0
    for _, row in sub.iterrows():
        v = row["network_contrib_weekend_3d_pp"]
        if v < 0.05:
            continue
        ax.barh(0, v, left=left, height=0.5, color=colors[sub.index.get_loc(row.name)])
        if v >= 0.25:
            ax.text(
                left + v / 2,
                0,
                f"{row['warehouse'].split(',')[0]}\n+{v:.2f}pp",
                ha="center",
                va="center",
                fontsize=8,
                color="white",
                fontweight="bold",
            )
        left += v

    ax.set_xlim(0, total + 0.5)
    ax.set_yticks([])
    ax.set_xlabel("Parent account 3-day badge uplift from weekend (pp)")
    ax.set_title(
        f"Safavieh parent — Sunday MSBD 3-day gain decomposed by warehouse "
        f"(total +{total:.2f} pp · {int(sub['weekend_new_3d'].sum()):,} orders)"
    )
    ax.axvline(total, color=NAVY, linestyle="--", alpha=0.5)
    fig.tight_layout()
    fig.savefig(CHARTS / "11_parent_weekend_3d_contrib_by_wh.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def chart_gain_volume_scatter(df: pd.DataFrame) -> None:
    """Warehouse pp gain vs % network volume — bubble size = newly badged orders."""
    sub = df[df["vol"] >= 500].copy()
    fig, ax = plt.subplots(figsize=(9, 7))

    x = sub["pct_network_vol"]
    y_cut = sub["cutoff_gain_3d_pp"]
    y_wk = sub["weekend_gain_3d_pp"]
    s_cut = sub["cutoff_new_3d"] / 15
    s_wk = sub["weekend_new_3d"] / 15

    ax.scatter(x, y_cut, s=s_cut, c=ACCENT, alpha=0.65, edgecolors="white", label="Cutoff policy")
    ax.scatter(x, y_wk, s=s_wk, c=ORANGE, alpha=0.65, edgecolors="white", label="Weekend")
    for _, row in sub.iterrows():
        ax.annotate(
            row["warehouse"].replace(", ", "\n"),
            (row["pct_network_vol"], max(row["cutoff_gain_3d_pp"], row["weekend_gain_3d_pp"])),
            fontsize=7,
            ha="center",
            xytext=(0, 8),
            textcoords="offset points",
        )
    ax.set_xlabel("% of Safavieh June MSBD volume at this warehouse")
    ax.set_ylabel("Warehouse-level 3-day badge pp gain")
    ax.set_title("Safavieh — 3-Day Gain vs Warehouse Volume Share\n(bubble size = newly badged orders)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(CHARTS / "12_3d_gain_vs_volume_share.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def chart_fri_sat_sunday_induction_by_wh(df: pd.DataFrame) -> None:
    """Fri/Sat placed orders inducting on Sunday — % and count by warehouse."""
    df = df.copy()
    df["label"] = df.apply(
        lambda r: (
            f"{int(r['supplier_id'])} · {r['su_name']} · "
            f"{str(r['city_name']).strip()}, {r['state_name']}"
        ),
        axis=1,
    )
    df = df.sort_values("fri_sat_vol", ascending=True)
    pct = df["pct_fri_sat_induct_sunday"] * 100
    n_sun = df["fri_sat_induct_sunday"]
    fri_sat = df["fri_sat_vol"]

    fig, ax = plt.subplots(figsize=(11, 7))
    colors = [
        GREEN if p >= 0.25 else ORANGE if p >= 0.15 else RED
        for p in pct
    ]
    bars = ax.barh(df["label"], pct, color=colors, height=0.72)
    ax.axvline(
        (df["pct_fri_sat_induct_sunday"] * 100).mean(),
        color=NAVY,
        linestyle="--",
        linewidth=1.2,
        label=f"Network avg ({(df['pct_fri_sat_induct_sunday'] * 100).mean():.0f}%)",
    )
    ax.set_xlabel("% of Fri/Sat-placed orders inducted on Sunday (induction_dow_adj = 1)")
    ax.set_title(
        "Safavieh — Fri/Sat Orders Inducting on Sunday by Warehouse\n"
        "June 2026 MSBD · order_dow 5–6 (Fri/Sat placed) · Sun = induction_dow_adj 1"
    )
    ax.set_xlim(0, max(pct.max() + 8, 35))
    ax.tick_params(axis="y", labelsize=8)
    for bar, p, ns, fs in zip(bars, pct, n_sun, fri_sat):
        ax.text(
            bar.get_width() + 0.8,
            bar.get_y() + bar.get_height() / 2,
            f"{p:.0f}%  ({int(ns):,} / {int(fs):,})",
            va="center",
            fontsize=8,
        )
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(CHARTS / "14_fri_sat_sunday_induction_by_wh.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def chart_fri_sat_weekend_shipping_by_wh(june_df: pd.DataFrame, l6w_df: pd.DataFrame | None = None) -> None:
    """Fri/Sat placed — % inducted Sat/Sun (induction_dow_adj 1 or 7)."""
    df = june_df.copy()
    if l6w_df is not None and len(l6w_df):
        l6w = l6w_df[["supplier_id", "pct_fri_sat_weekend_ship"]].rename(
            columns={"pct_fri_sat_weekend_ship": "pct_l6w"}
        )
        df = df.merge(l6w, on="supplier_id", how="left")

    df["label"] = df.apply(
        lambda r: (
            f"{int(r['supplier_id'])} · {r['su_name']} · "
            f"{str(r['city_name']).strip()}, {r['state_name']}"
        ),
        axis=1,
    )
    df = df.sort_values("fri_sat_vol", ascending=True)
    pct_june = df["pct_fri_sat_weekend_ship"] * 100

    fig, ax = plt.subplots(figsize=(11, 7))
    y = np.arange(len(df))
    h = 0.35
    ax.barh(y - h / 2, pct_june, h, label="June MSBD", color=ACCENT)
    if "pct_l6w" in df.columns:
        pct_l6w = df["pct_l6w"].fillna(0) * 100
        ax.barh(y + h / 2, pct_l6w, h, label="L6W MSBD", color=NAVY, alpha=0.85)
    net_june = pct_june.mean()
    ax.axvline(net_june, color=ORANGE, linestyle="--", linewidth=1.2,
               label=f"June avg ({net_june:.0f}%)")
    ax.axvline(70, color=GREEN, linestyle=":", linewidth=1, alpha=0.65, label="70% threshold")
    ax.set_yticks(y)
    ax.set_yticklabels(df["label"], fontsize=8)
    ax.set_xlabel("% Fri/Sat placed inducted Sat/Sun (induction_dow_adj 1 or 7)")
    ax.set_title(
        "Safavieh — Weekend Shipping % by Warehouse (Fri/Sat placed)\n"
        "Correct DOW: Sun=1, Sat=7 · BQ weekend table ~50% used old adj IN (6,7) until refresh"
    )
    ax.set_xlim(0, max(pct_june.max() + 12, 45))
    for i, row in df.iterrows():
        idx = df.index.get_loc(i)
        ax.text(pct_june.iloc[idx] + 0.8, idx - h / 2,
                f"{pct_june.iloc[idx]:.0f}% ({int(row['fri_sat_induct_weekend']):,}/{int(row['fri_sat_vol']):,})",
                va="center", fontsize=7)
    ax.legend(loc="lower right", fontsize=8)
    fig.tight_layout()
    fig.savefig(CHARTS / "20_fri_sat_weekend_shipping_by_wh.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def chart_account_sunday_msbd_lift(scen: pd.DataFrame, lift_df: pd.DataFrame | None = None) -> None:
    """Parent account — Fri/Sat −1 o2d vs current stated badges."""
    if lift_df is not None and len(lift_df):
        row = lift_df[lift_df["level"] == "account"].iloc[0]
        tiers = ["1-day", "2-day", "3-day", "Fast (≤5d)"]
        uplifts = [row["lift_1d_pp"], row["lift_2d_pp"], row["lift_3d_pp"], row["lift_fast_pp"]]
        newly = [int(row["new_1d"]), int(row["new_2d"]), int(row["new_3d"]), int(row["new_fast"])]
        fri_sat_vol = int(row["fri_sat_vol"])
    elif "fri_sat_o2d_minus1" in scen["scenario"].values:
        current = scen.loc[scen["scenario"] == "current"].iloc[0]
        fri = scen.loc[scen["scenario"] == "fri_sat_o2d_minus1"].iloc[0]
        tiers = ["1-day", "2-day", "3-day", "Fast (≤5d)"]
        cols = ["badge_1d_pct", "badge_2d_pct", "badge_3d_pct", "badge_5d_fast_pct"]
        uplifts = [fri[c] - current[c] for c in cols]
        newly = [int(fri[f"newly_fast_{t}"]) for t in ["1d", "2d", "3d", "5d"]]
        fri_sat_vol = None
    else:
        return

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    colors = [ORANGE, ORANGE, ACCENT, GRAY]
    ax1.bar(tiers, uplifts, color=colors)
    ax1.set_ylabel("Incremental lift (pp)")
    ax1.set_title("Parent account — Sunday MSBD promise lift by tier")
    for i, v in enumerate(uplifts):
        ax1.text(i, v + 0.2, f"+{v:.1f}", ha="center", fontweight="bold")

    ax2.bar(tiers, newly, color=colors)
    ax2.set_ylabel("Additional newly badged orders")
    ax2.set_title("Orders gaining badge (incremental after cutoff policy)")
    for i, v in enumerate(newly):
        ax2.text(i, v + 120, f"{v:,}", ha="center", fontsize=9)

    fig.suptitle(
        "Safavieh parent — Fri/Sat placed: subtract 1 from o2d_stated vs current"
        + (f" · {fri_sat_vol:,} Fri/Sat orders" if fri_sat_vol else ""),
        fontsize=12,
        y=1.02,
    )
    fig.tight_layout()
    fig.savefig(CHARTS / "21_account_sunday_msbd_lift.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def chart_warehouse_sunday_msbd_lift(gain: pd.DataFrame, lift_df: pd.DataFrame | None = None) -> None:
    """Warehouse-level Fri/Sat −1 o2d lift (pp) by badge tier."""
    if lift_df is not None and len(lift_df):
        wh = lift_df[lift_df["level"] == "warehouse"].copy()
        wh = wh[wh["vol"] >= 200]
        wh["warehouse"] = wh["city_name"].str.strip() + ", " + wh["state_name"].fillna("")
        cols = ["lift_1d_pp", "lift_2d_pp", "lift_3d_pp", "lift_fast_pp"]
    else:
        wh = gain[gain["vol"] >= 200].copy()
        wh["warehouse"] = wh["city_name"].str.strip() + ", " + wh["state_name"]
        cols = [
            "weekend_gain_1d_pp",
            "weekend_gain_2d_pp",
            "weekend_gain_3d_pp",
            "weekend_gain_fast_pp",
        ]
    wh = wh.sort_values("vol", ascending=True)
    tiers = ["1-day", "2-day", "3-day", "Fast ≤5d"]
    tier_colors = [ORANGE, ORANGE, ACCENT, GRAY]

    y = np.arange(len(wh))
    n = len(tiers)
    h = 0.8 / n
    fig, ax = plt.subplots(figsize=(11, max(6, len(wh) * 0.45)))

    for i, (tier, col, color) in enumerate(zip(tiers, cols, tier_colors)):
        offset = (i - (n - 1) / 2) * h
        vals = wh[col].values
        ax.barh(y + offset, vals, height=h * 0.92, label=tier, color=color, alpha=0.9)
        for j, v in enumerate(vals):
            if v >= 1.5:
                ax.text(v + 0.15, y[j] + offset, f"+{v:.1f}", va="center", fontsize=6, color=color)

    ax.set_yticks(y)
    ax.set_yticklabels(wh["warehouse"], fontsize=9)
    ax.set_xlabel("Fri/Sat −1 o2d lift (pp) vs current stated")
    ax.set_title(
        "Safavieh — Badge Lift by Warehouse (Fri/Sat placed −1 o2d_stated)\n"
        "June MSBD · vs current stated speed"
    )
    ax.legend(loc="lower right", fontsize=8, ncol=2)
    fig.tight_layout()
    fig.savefig(CHARTS / "22_warehouse_sunday_msbd_lift.png", dpi=150, bbox_inches="tight")
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
    chart_network_cohort_current_and_lifts(scen)
    chart_stacked_opportunity_pp_only(scen)
    chart_network_current_vs_fri_sat_minus1(scen)
    chart_weekend_incremental(scen)
    account_df = None
    lift_df = pd.read_csv(FRI_SAT_LIFT_CSV) if FRI_SAT_LIFT_CSV.exists() else None
    chart_account_sunday_msbd_lift(scen, lift_df)
    chart_badging_uplift(scen)
    chart_volume_by_warehouse(wh)

    if WH_SIM_CSV.exists():
        chart_3d_badge_by_warehouse(pd.read_csv(WH_SIM_CSV))

    if GAIN_CSV.exists():
        from scripts.enrich_safavieh_gain_volume_weighted import enrich_gain_table

        gain_vw = enrich_gain_table()
        gain_vw.to_csv(GAIN_VW_CSV, index=False)
        chart_warehouse_sunday_msbd_lift(gain_vw, lift_df)
        chart_wh_pp_vs_network_contribution_3d(gain_vw)
        chart_network_contrib_stacked_3d(gain_vw)
        chart_gain_volume_scatter(gain_vw)

    if FRI_SAT_SUN_CSV.exists():
        chart_fri_sat_sunday_induction_by_wh(pd.read_csv(FRI_SAT_SUN_CSV))
    elif (ROOT / "sql/safavieh_june_fri_sat_sunday_induction_by_wh.sql").exists():
        from gbq import query_df

        sql = (ROOT / "sql/safavieh_june_fri_sat_sunday_induction_by_wh.sql").read_text()
        fri_sat = query_df(sql)
        fri_sat.to_csv(FRI_SAT_SUN_CSV, index=False)
        chart_fri_sat_sunday_induction_by_wh(fri_sat)

    l6w_wknd = pd.read_csv(L6W_WKND_CSV) if L6W_WKND_CSV.exists() else None
    if FRI_SAT_WKND_CSV.exists():
        chart_fri_sat_weekend_shipping_by_wh(pd.read_csv(FRI_SAT_WKND_CSV), l6w_wknd)
    elif (ROOT / "sql/safavieh_june_fri_sat_weekend_shipping_by_wh.sql").exists():
        from gbq import query_df

        sql = (ROOT / "sql/safavieh_june_fri_sat_weekend_shipping_by_wh.sql").read_text()
        fri_wk = query_df(sql)
        fri_wk.to_csv(FRI_SAT_WKND_CSV, index=False)
        chart_fri_sat_weekend_shipping_by_wh(fri_wk, None)

    print(f"Charts saved to {CHARTS}")
    for p in sorted(CHARTS.glob("*.png")):
        print(f"  {p.name}")


if __name__ == "__main__":
    main()
