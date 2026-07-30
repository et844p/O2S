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


def chart_network_cohort_current_and_lifts(scen: pd.DataFrame) -> None:
    """One stacked bar per cohort: current (base) + cutoff lift + weekend lift."""
    if "policy_2pm_no_cushion" not in scen["scenario"].values:
        return

    tiers = ["1-day", "2-day", "3-day", "Fast (≤5d)"]
    cols = ["badge_1d_pct", "badge_2d_pct", "badge_3d_pct", "badge_5d_fast_pct"]
    cur = scen.loc[scen["scenario"] == "current", cols].iloc[0].values.astype(float)
    pol = scen.loc[scen["scenario"] == "policy_2pm_no_cushion", cols].iloc[0].values.astype(float)
    full = scen.loc[scen["scenario"] == "policy_plus_weekend", cols].iloc[0].values.astype(float)
    cutoff_lift = pol - cur
    weekend_lift = full - pol

    x = np.arange(len(tiers))
    width = 0.5
    edge = {"edgecolor": "white", "linewidth": 1.2}

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.bar(x, cur, width, label="Current (June)", color=GRAY, **edge)
    ax.bar(x, cutoff_lift, width, bottom=cur, label="+ Cutoff to 2pm", color=ACCENT, **edge)
    ax.bar(
        x,
        weekend_lift,
        width,
        bottom=cur + cutoff_lift,
        label="+ Weekend",
        color=ORANGE,
        **edge,
    )

    ax.set_ylabel("Badge coverage (%)")
    ax.set_title("Safavieh Network — Badge Coverage by Cohort (June MSBD)")
    ax.set_xticks(x)
    ax.set_xticklabels(tiers)
    ax.set_ylim(0, 100)
    ax.set_xlim(-0.6, len(tiers) - 0.4)

    for i in range(len(tiers)):
        total = cur[i] + cutoff_lift[i] + weekend_lift[i]
        ax.text(
            x[i],
            total + 2,
            f"{total:.1f}%",
            ha="center",
            va="bottom",
            fontsize=11,
            fontweight="bold",
            color=NAVY,
        )

    ax.legend(loc="upper left", framealpha=0.95)
    ax.text(
        0.99,
        0.02,
        "Each bar = current + cutoff lift + weekend lift · 73,294 ops",
        transform=ax.transAxes,
        ha="right",
        fontsize=9,
        color=GRAY,
    )
    fig.tight_layout()
    fig.savefig(CHARTS / "13_network_cohort_current_and_lift.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def chart_weekend_incremental(scen: pd.DataFrame) -> None:
    """Incremental pp from weekend only, after policy (2pm + no cushion)."""
    if "policy_2pm_no_cushion" not in scen["scenario"].values:
        return
    policy = scen.loc[scen["scenario"] == "policy_2pm_no_cushion"].iloc[0]
    full = scen.loc[scen["scenario"] == "policy_plus_weekend"].iloc[0]
    tiers = ["1-day", "2-day", "3-day", "Fast ≤5d"]
    cols = ["badge_1d_pct", "badge_2d_pct", "badge_3d_pct", "badge_5d_fast_pct"]
    wknd_cols = ["wknd_incr_1d", "wknd_incr_2d", "wknd_incr_3d", "wknd_incr_5d"]
    uplifts = [full[c] - policy[c] for c in cols]
    if all(c in full.index for c in wknd_cols):
        newly = [int(full[c]) for c in wknd_cols]
    else:
        new_cols = ["newly_fast_1d", "newly_fast_2d", "newly_fast_3d", "newly_fast_5d"]
        newly = [int(full[n] - policy[n]) for n in new_cols]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    colors = [ORANGE, ORANGE, ACCENT, GRAY]
    ax1.bar(tiers, uplifts, color=colors)
    ax1.set_ylabel("Incremental uplift (pp)")
    ax1.set_title("Weekend shipping only — after 2pm + no cushion")
    for i, v in enumerate(uplifts):
        ax1.text(i, v + 0.15, f"+{v:.1f}", ha="center", fontweight="bold")

    ax2.bar(tiers, newly, color=colors)
    ax2.set_ylabel("Additional newly badged orders")
    ax2.set_title("Orders gaining badge from weekend (incremental)")
    for i, v in enumerate(newly):
        ax2.text(i, v + 150, f"{v:,}", ha="center", fontsize=9)

    fig.suptitle("Safavieh — Weekend shipping incremental impact (June MSBD)", fontsize=13)
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
        "Safavieh — 3-Day Badge: Weekend Warehouse Gain vs Parent Account Contribution"
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
    """Stacked bar: each warehouse's slice of parent +7.4pp weekend 3-day uplift."""
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
        f"Safavieh parent — weekend 3-day gain decomposed by warehouse "
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
    chart_weekend_incremental(scen)
    chart_badging_uplift(scen)
    chart_volume_by_warehouse(wh)

    if WH_SIM_CSV.exists():
        chart_3d_badge_by_warehouse(pd.read_csv(WH_SIM_CSV))

    if GAIN_CSV.exists():
        from scripts.enrich_safavieh_gain_volume_weighted import enrich_gain_table

        gain_vw = enrich_gain_table()
        gain_vw.to_csv(GAIN_VW_CSV, index=False)
        chart_wh_pp_vs_network_contribution_3d(gain_vw)
        chart_network_contrib_stacked_3d(gain_vw)
        chart_gain_volume_scatter(gain_vw)

    print(f"Charts saved to {CHARTS}")
    for p in sorted(CHARTS.glob("*.png")):
        print(f"  {p.name}")


if __name__ == "__main__":
    main()
