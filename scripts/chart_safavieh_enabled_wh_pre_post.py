#!/usr/bin/env python3
"""Pre (5/31–7/4) vs post-enable weekly — induction_dow_adj Sunday / weekend metrics."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

_default_creds = ROOT / ".gcp" / "credentials.json"
if _default_creds.exists():
    os.environ.setdefault("GOOGLE_APPLICATION_CREDENTIALS", str(_default_creds))

from gbq import query_df

OUT = ROOT / "output" / "safavieh"
CHARTS = ROOT / "docs" / "small_parcel" / "safavieh_charts"
SQL = ROOT / "sql" / "safavieh_enabled_wh_pre_post_sunday_adj.sql"

NAVY = "#1a365d"
ACCENT = "#2e86ab"
ORANGE = "#f39c12"
RED = "#c0392b"
GRAY = "#95a5a6"
GREEN = "#27ae60"

WAREHOUSES = [
    (93132, "Safavieh IN46075"),
    (223799, "Safavieh Texas"),
    (59119, "Safavieh CA 92518"),
    (34809, "Safavieh GA31407 B"),
]


def load() -> pd.DataFrame:
    return query_df(SQL.read_text())


def chart_pre_post_comparison(df: pd.DataFrame) -> None:
    """Stacked period bars: pre window vs post-enable avg, induction_dow_adj metrics."""
    CHARTS.mkdir(parents=True, exist_ok=True)
    pre = df[df["period"] == "pre_enable"].copy()
    post = df[df["period"] == "post_enable_weekly"].copy()

    fig, axes = plt.subplots(2, 2, figsize=(12, 9))
    axes = axes.flatten()

    for ax, (sid, name) in zip(axes, WAREHOUSES):
        p = pre[pre["supplier_id"] == sid].iloc[0]
        post_sub = post[post["supplier_id"] == sid].sort_values("week_start")
        post_sub["week_start"] = pd.to_datetime(post_sub["week_start"])

        pre_sun = p["pct_sun_adj1"] * 100
        pre_wk = p["pct_weekend_adj17"] * 100
        post_sun = post_sub["pct_sun_adj1"].mean() * 100 if len(post_sub) else 0
        post_wk = post_sub["pct_weekend_adj17"].mean() * 100 if len(post_sub) else 0

        x = [0, 1]
        width = 0.35
        ax.bar(x[0] - width / 2, pre_sun, width, label="Sun adj=1", color=ORANGE)
        ax.bar(x[0] + width / 2, pre_wk, width, label="Weekend adj 1+7", color=ACCENT)
        ax.bar(x[1] - width / 2, post_sun, width, color=ORANGE, alpha=0.85)
        ax.bar(x[1] + width / 2, post_wk, width, color=ACCENT, alpha=0.85)

        ax.text(x[0] - width / 2, pre_sun + 1, f"{pre_sun:.1f}%", ha="center", fontsize=8)
        ax.text(x[0] + width / 2, pre_wk + 1, f"{pre_wk:.1f}%", ha="center", fontsize=8)
        ax.text(x[1] - width / 2, post_sun + 1, f"{post_sun:.1f}%", ha="center", fontsize=8)
        ax.text(x[1] + width / 2, post_wk + 1, f"{post_wk:.1f}%", ha="center", fontsize=8)

        ax.set_xticks(x)
        ax.set_xticklabels(["Pre 5/31–7/4", "Post enable avg"], fontsize=9)
        ax.set_ylim(0, max(55, pre_wk + 10, post_wk + 10))
        ax.set_title(
            f"{sid} · {name}\n"
            f"Pre: n={int(p['fri_sat_vol']):,} · Sun adj1={int(p['sun_adj1_vol']):,} · "
            f"Wknd={int(p['weekend_adj17_vol']):,}",
            fontsize=9,
        )

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=2, bbox_to_anchor=(0.5, 1.02))
    fig.suptitle(
        "Safavieh enabled WHs — induction_dow_adj metrics (Fri/Sat placed)\n"
        "Sun = induction_dow_adj 1 · Sat = 7 · Weekend = induction_dow_adj 1 or 7",
        fontsize=12,
        y=1.06,
    )
    fig.tight_layout()
    fig.savefig(CHARTS / "17_enabled_wh_pre_post_induction_dow_adj.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def chart_post_weekly_with_pre_line(df: pd.DataFrame) -> None:
    """Week-over-week post-enable with pre-window reference lines (induction_dow_adj)."""
    pre = df[df["period"] == "pre_enable"]
    post = df[df["period"] == "post_enable_weekly"].copy()
    post["week_start"] = pd.to_datetime(post["week_start"])

    fig, axes = plt.subplots(2, 2, figsize=(12, 9), sharex=True)
    axes = axes.flatten()

    for ax, (sid, name) in zip(axes, WAREHOUSES):
        p = pre[pre["supplier_id"] == sid].iloc[0]
        sub = post[post["supplier_id"] == sid].sort_values("week_start")
        if sub.empty:
            continue

        ax.plot(
            sub["week_start"],
            sub["pct_sun_adj1"] * 100,
            marker="o",
            color=ORANGE,
            linewidth=2,
            label="Sun adj=1 (weekly)",
        )
        ax.plot(
            sub["week_start"],
            sub["pct_weekend_adj17"] * 100,
            marker="s",
            color=ACCENT,
            linewidth=2,
            label="Weekend adj 1+7 (weekly)",
        )
        ax.axhline(p["pct_sun_adj1"] * 100, color=ORANGE, linestyle="--", alpha=0.7,
                   label=f"Pre Sun ref ({p['pct_sun_adj1']*100:.1f}%)")
        ax.axhline(p["pct_weekend_adj17"] * 100, color=ACCENT, linestyle="--", alpha=0.7,
                   label=f"Pre wknd ref ({p['pct_weekend_adj17']*100:.1f}%)")
        ax.axvline(pd.Timestamp("2026-07-06"), color=RED, linewidth=1.2, alpha=0.8)
        ax.set_title(f"{sid} · {name}", fontsize=10)
        ax.set_ylabel("% of Fri/Sat orders")
        ax.set_ylim(0, 60)
        ax.legend(fontsize=7, loc="upper right")
        ax.tick_params(axis="x", rotation=30)

    fig.suptitle(
        "Post-enable weekly vs pre window (5/31–7/4) — induction_dow_adj definition",
        fontsize=12,
        y=1.02,
    )
    fig.tight_layout()
    fig.savefig(CHARTS / "18_enabled_wh_weekly_induction_dow_adj.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def chart_network_pre_post_bars(df: pd.DataFrame) -> None:
    """Network rollup: pre window vs post weekly for cohort badges style."""
    pre = df[df["period"] == "pre_enable"]
    post = df[df["period"] == "post_enable_weekly"]

    pre_sun = pre["sun_adj1_vol"].sum() / pre["fri_sat_vol"].sum() * 100
    pre_wk = pre["weekend_adj17_vol"].sum() / pre["fri_sat_vol"].sum() * 100
    post_sun = post["sun_adj1_vol"].sum() / post["fri_sat_vol"].sum() * 100
    post_wk = post["weekend_adj17_vol"].sum() / post["fri_sat_vol"].sum() * 100

    tiers = ["Sun adj=1", "Weekend adj 1+7"]
    pre_vals = [pre_sun, pre_wk]
    post_vals = [post_sun, post_wk]

    x = np.arange(len(tiers))
    w = 0.35
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(x - w / 2, pre_vals, w, label="Pre 5/31–7/4", color=GRAY)
    ax.bar(x + w / 2, post_vals, w, label="Post enable (all weeks)", color=ACCENT)
    ax.set_xticks(x)
    ax.set_xticklabels(tiers)
    ax.set_ylabel("% of Fri/Sat orders (4 enabled WHs combined)")
    ax.set_title(
        "Safavieh enabled WHs — Network pre vs post (induction_dow_adj)\n"
        f"Pre vol {int(pre['fri_sat_vol'].sum()):,} · Post vol {int(post['fri_sat_vol'].sum()):,}"
    )
    for i, (a, b) in enumerate(zip(pre_vals, post_vals)):
        ax.text(i - w / 2, a + 1, f"{a:.2f}%", ha="center", fontsize=10, fontweight="bold")
        ax.text(i + w / 2, b + 1, f"{b:.2f}%", ha="center", fontsize=10, fontweight="bold")
    ax.legend()
    fig.tight_layout()
    fig.savefig(CHARTS / "19_network_pre_post_induction_dow_adj.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    df = load()
    csv_path = OUT / "safavieh_enabled_wh_pre_post_sunday_adj.csv"
    df.to_csv(csv_path, index=False)
    print(f"Saved {csv_path}")

    pre = df[df["period"] == "pre_enable"]
    print("\n=== PRE 5/31–7/4 (induction_dow_adj: Sun=1, Sat=7) ===")
    print(
        pre[
            [
                "supplier_id",
                "su_name",
                "fri_sat_vol",
                "sun_adj1_vol",
                "weekend_adj17_vol",
                "pct_sun_adj1",
                "pct_weekend_adj17",
            ]
        ].to_string(index=False)
    )
    net_pre_sun = pre["sun_adj1_vol"].sum() / pre["fri_sat_vol"].sum() * 100
    net_pre_wk = pre["weekend_adj17_vol"].sum() / pre["fri_sat_vol"].sum() * 100
    print(f"Network combined: Sun adj1={net_pre_sun:.2f}%  Weekend adj17={net_pre_wk:.2f}%")

    chart_pre_post_comparison(df)
    chart_post_weekly_with_pre_line(df)
    chart_network_pre_post_bars(df)
    print(f"Charts → {CHARTS}")


if __name__ == "__main__":
    main()
