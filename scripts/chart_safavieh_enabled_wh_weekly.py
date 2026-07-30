#!/usr/bin/env python3
"""Week-over-week Sunday induction trend for enabled Safavieh weekend warehouses."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

_default_creds = ROOT / ".gcp" / "credentials.json"
if _default_creds.exists():
    os.environ.setdefault("GOOGLE_APPLICATION_CREDENTIALS", str(_default_creds))

from gbq import query_df

OUT = ROOT / "output" / "safavieh"
CHARTS = ROOT / "docs" / "small_parcel" / "safavieh_charts"
SQL = ROOT / "sql" / "safavieh_enabled_wh_sunday_induction_weekly.sql"
ENABLE_DATE = pd.Timestamp("2026-07-07")
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


def load_weekly() -> pd.DataFrame:
    df = query_df(SQL.read_text())
    df["week_start"] = pd.to_datetime(df["week_start"])
    return df


def chart_weekly_sunday_trend(df: pd.DataFrame) -> None:
    CHARTS.mkdir(parents=True, exist_ok=True)
    plt.style.use("seaborn-v0_8-whitegrid")

    enable_week = pd.Timestamp("2026-07-06")  # Sunday start of week containing Jul 7

    fig, axes = plt.subplots(2, 2, figsize=(12, 9), sharex=True)
    axes = axes.flatten()

    for ax, (sid, name) in zip(axes, WAREHOUSES):
        sub = df[df["supplier_id"] == sid].sort_values("week_start")
        if sub.empty:
            ax.set_title(f"{sid} · {name} (no data)")
            continue

        pct = sub["pct_sun_adj1"] * 100
        ax.plot(sub["week_start"], pct, marker="o", color=ACCENT, linewidth=2, markersize=5)
        ax.fill_between(sub["week_start"], pct, alpha=0.12, color=ACCENT)

        l6w = sub["l6w_pre_pct_sun"].iloc[0]
        if pd.notna(l6w):
            ax.axhline(l6w * 100, color=ORANGE, linestyle="--", linewidth=1.2,
                       label=f"L6W pre-enable avg ({l6w*100:.0f}% Sun)")

        ax.axvline(enable_week, color=RED, linestyle="-", linewidth=1.5, alpha=0.85)
        ax.text(
            enable_week,
            ax.get_ylim()[1] * 0.92,
            "Enabled\nJul 7",
            color=RED,
            fontsize=8,
            ha="left",
            va="top",
        )

        post = sub[sub["post_enable_week"] == 1]
        pre = sub[sub["post_enable_week"] == 0]
        pre_avg = pre["pct_sun_adj1"].mean() * 100 if len(pre) else 0
        post_avg = post["pct_sun_adj1"].mean() * 100 if len(post) else 0
        delta = post_avg - pre_avg
        trend = "▼ worsened" if delta < -2 else ("▲ improved" if delta > 2 else "≈ flat")

        ax.set_title(
            f"{sid} · {name}\nPre avg {pre_avg:.0f}% → Post avg {post_avg:.0f}% ({trend})",
            fontsize=10,
        )
        ax.set_ylabel("% Fri/Sat inducted Sun")
        ax.set_ylim(0, max(45, pct.max() + 8))
        ax.legend(loc="upper right", fontsize=7)

        for _, row in sub.iterrows():
            if row["fri_sat_vol"] < 80:
                ax.annotate(
                    "low n",
                    (row["week_start"], row["pct_sun_adj1"] * 100),
                    fontsize=6,
                    color=GRAY,
                    ha="center",
                    xytext=(0, 6),
                    textcoords="offset points",
                )

    for ax in axes[2:]:
        ax.tick_params(axis="x", rotation=35)
    fig.suptitle(
        "Safavieh enabled weekend WHs — % Fri/Sat orders inducted on Sunday (induction_dow_adj=1)\n"
        "Sunday-start weeks · dashed = L6W avg before Jul 7 enablement",
        fontsize=12,
        y=1.02,
    )
    fig.tight_layout()
    fig.savefig(
        CHARTS / "15_enabled_wh_sunday_induction_weekly.png",
        dpi=150,
        bbox_inches="tight",
    )
    plt.close(fig)


def chart_weekly_weekend_trend(df: pd.DataFrame) -> None:
    """Sat+Sun weekend induction % — closer to 70% enablement criterion."""
    enable_week = pd.Timestamp("2026-07-06")
    fig, axes = plt.subplots(2, 2, figsize=(12, 9), sharex=True)
    axes = axes.flatten()

    for ax, (sid, name) in zip(axes, WAREHOUSES):
        sub = df[df["supplier_id"] == sid].sort_values("week_start")
        pct = sub["pct_weekend_adj17"] * 100
        ax.plot(sub["week_start"], pct, marker="o", color=NAVY, linewidth=2, markersize=5)
        l6w = sub["l6w_pre_pct_weekend"].iloc[0]
        if pd.notna(l6w):
            ax.axhline(l6w * 100, color=ORANGE, linestyle="--", linewidth=1.2,
                       label=f"L6W pre-enable ({l6w*100:.0f}%)")
        ax.axhline(70, color=GREEN, linestyle=":", linewidth=1, alpha=0.7, label="70% enable threshold")
        ax.axvline(enable_week, color=RED, linestyle="-", linewidth=1.5, alpha=0.85)
        post_avg = sub[sub["post_enable_week"] == 1]["pct_weekend_adj17"].mean() * 100
        pre_avg = sub[sub["post_enable_week"] == 0]["pct_weekend_adj17"].mean() * 100
        ax.set_title(f"{sid} · {name}\nWeekend Sat+Sun: pre {pre_avg:.0f}% → post {post_avg:.0f}%", fontsize=10)
        ax.set_ylabel("% Fri/Sat inducted Sat/Sun")
        ax.set_ylim(0, 85)
        ax.legend(loc="upper right", fontsize=7)

    fig.suptitle(
        "Safavieh enabled WHs — % Fri/Sat inducted Sat/Sun (induction_dow_adj 7 or 1)",
        fontsize=12,
        y=1.02,
    )
    fig.tight_layout()
    fig.savefig(CHARTS / "16_enabled_wh_weekend_induction_weekly.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    df = load_weekly()
    csv_path = OUT / "safavieh_enabled_wh_sunday_induction_weekly.csv"
    df.to_csv(csv_path, index=False)
    print(f"Saved {csv_path} ({len(df)} rows)")

    chart_weekly_sunday_trend(df)
    chart_weekly_weekend_trend(df)
    print(f"Charts → {CHARTS}")


if __name__ == "__main__":
    main()
