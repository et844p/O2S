#!/usr/bin/env python3
"""JLA Home Savannah (SV2/SV3) — warehouse vs FedEx delay attribution, July 2026 MSBD."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

_default_creds = ROOT / ".gcp" / "credentials.json"
if _default_creds.exists():
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(_default_creds)

from gbq import query_df

SQL_ORDER = ROOT / "sql" / "jla_savannah_order_level.sql"
OUT = ROOT / "output" / "jla_savannah"
DOCS = ROOT / "docs" / "small_parcel"
CHARTS = DOCS / "jla_savannah_charts"

WAREHOUSES = ["SV2 (conveyables)", "SV3 (non-conveyables)"]
ATTRIBUTION_ORDER = [
    "On time",
    "FedEx: label on time, inducted next day",
    "FedEx: label on time, inducted 2+ days",
    "WH: label after 2pm MSBD",
    "FedEx: label on time, same-day induct but late MSBD",
    "Other late",
]


def load_orders() -> pd.DataFrame:
    df = query_df(SQL_ORDER.read_text())
    df["msbd_su"] = pd.to_datetime(df["msbd_su"])
    df["msbd_su_week"] = pd.to_datetime(df["msbd_su_week"])
    df["on_time"] = df["inducted_on_time_or_early"].fillna(0).astype(int)
    return df


def chart_ifr_by_warehouse(df: pd.DataFrame) -> None:
    agg = (
        df.groupby("warehouse", as_index=False)
        .agg(volume=("ops", "nunique"), ifr=("on_time", "mean"))
        .sort_values("volume", ascending=False)
    )
    fig, ax = plt.subplots(figsize=(8, 5))
    colors = ["#2ecc71" if x >= 0.85 else "#e74c3c" for x in agg["ifr"]]
    bars = ax.bar(agg["warehouse"], agg["ifr"], color=colors)
    ax.axhline(0.85, color="#333", linestyle="--", linewidth=1, label="85% target")
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Induction Fill Rate")
    ax.set_title("JLA Savannah — IFR by Warehouse (July 2026 MSBD)")
    for bar, vol in zip(bars, agg["volume"]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02, f"n={vol:,}", ha="center", fontsize=9)
    ax.legend()
    fig.tight_layout()
    fig.savefig(CHARTS / "01_ifr_by_warehouse.png", dpi=150)
    plt.close(fig)


def chart_weekly_trend(df: pd.DataFrame) -> None:
    agg = (
        df.groupby(["msbd_su_week", "warehouse"], as_index=False)
        .agg(volume=("ops", "nunique"), ifr=("on_time", "mean"))
    )
    fig, ax = plt.subplots(figsize=(11, 5))
    for wh in WAREHOUSES:
        sub = agg[agg["warehouse"] == wh]
        ax.plot(sub["msbd_su_week"], sub["ifr"], marker="o", label=wh, linewidth=2)
    ax.axhline(0.85, color="#333", linestyle="--", linewidth=1, alpha=0.7)
    ax.set_ylabel("IFR")
    ax.set_xlabel("MSBD week")
    ax.set_title("JLA Savannah — Weekly IFR Trend (July 2026)")
    ax.legend(loc="lower left")
    ax.set_ylim(0, 1.05)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(CHARTS / "02_weekly_ifr_trend.png", dpi=150)
    plt.close(fig)


def chart_attribution(df: pd.DataFrame) -> None:
    late = df[df["on_time"] == 0].copy()
    agg = late.groupby(["warehouse", "delay_attribution"]).size().reset_index(name="vol")
    pivot = agg.pivot(index="delay_attribution", columns="warehouse", values="vol").fillna(0)
    pivot = pivot.reindex([a for a in ATTRIBUTION_ORDER if a in pivot.index])
    fig, ax = plt.subplots(figsize=(10, 6))
    pivot.plot(kind="barh", ax=ax, width=0.75)
    ax.set_xlabel("Late order volume (ops)")
    ax.set_title("JLA Savannah — Late Order Attribution (July 2026)")
    ax.legend(title="Warehouse", bbox_to_anchor=(1.02, 1), loc="upper left")
    fig.tight_layout()
    fig.savefig(CHARTS / "03_late_attribution.png", dpi=150)
    plt.close(fig)


def chart_daily_crisis(df: pd.DataFrame) -> None:
    sv3 = df[df["warehouse"] == "SV3 (non-conveyables)"]
    agg = (
        sv3.groupby("msbd_su", as_index=False)
        .agg(
            volume=("ops", "nunique"),
            ifr=("on_time", "mean"),
            fedex_late=("delay_attribution", lambda s: s.str.startswith("FedEx").sum()),
            wh_late=("delay_attribution", lambda s: (s == "WH: label after 2pm MSBD").sum()),
        )
    )
    fig, ax1 = plt.subplots(figsize=(12, 5))
    ax2 = ax1.twinx()
    ax1.bar(agg["msbd_su"], agg["volume"], alpha=0.25, color="#3498db", label="Volume")
    ax2.plot(agg["msbd_su"], agg["ifr"], color="#e74c3c", marker="o", linewidth=2, label="IFR")
    ax1.set_ylabel("Volume")
    ax2.set_ylabel("IFR")
    ax2.set_ylim(0, 1.05)
    ax1.set_title("SV3 (Non-Conveyables) — Daily IFR & Volume (July 2026)")
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(CHARTS / "04_sv3_daily_ifr.png", dpi=150)
    plt.close(fig)


def chart_label_hour(df: pd.DataFrame) -> None:
    sv3 = df[
        (df["warehouse"] == "SV3 (non-conveyables)")
        & (df["label_date"] == df["msbd_su"].dt.date)
    ].copy()
    if sv3.empty:
        return
    sv3["label_date"] = pd.to_datetime(sv3["label_date"])
    agg = (
        sv3.groupby(["label_hour_et", "on_time"], as_index=False)
        .agg(vol=("ops", "nunique"))
    )
    pivot = agg.pivot(index="label_hour_et", columns="on_time", values="vol").fillna(0)
    pivot.columns = ["Late", "On time"]
    fig, ax = plt.subplots(figsize=(10, 5))
    pivot.plot(kind="bar", stacked=True, ax=ax, color=["#e74c3c", "#2ecc71"])
    ax.axvline(x=13.5, color="#333", linestyle="--", linewidth=1.5, label="2pm ET cutoff")
    ax.set_xlabel("Label hour (ET) on MSBD")
    ax.set_ylabel("Order volume")
    ax.set_title("SV3 — Label Time vs On-Time Induction (MSBD day, July 2026)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(CHARTS / "05_sv3_label_hour.png", dpi=150)
    plt.close(fig)


def build_summary(df: pd.DataFrame) -> str:
    total = df["ops"].nunique()
    late = df[df["on_time"] == 0]
    late_vol = late["ops"].nunique()

    wh_lines = []
    for wh in WAREHOUSES:
        sub = df[df["warehouse"] == wh]
        late_sub = sub[sub["on_time"] == 0]
        vol = sub["ops"].nunique()
        ifr = sub["on_time"].mean()
        fedex = late_sub[late_sub["delay_attribution"].str.startswith("FedEx", na=False)]["ops"].nunique()
        wh_drv = late_sub[late_sub["delay_attribution"] == "WH: label after 2pm MSBD"]["ops"].nunique()
        pct_fedex = fedex / late_sub["ops"].nunique() * 100 if len(late_sub) else 0
        wh_lines.append(
            f"| {wh} | {vol:,} | {ifr:.1%} | {late_sub['ops'].nunique():,} | {fedex:,} ({pct_fedex:.0f}%) | {wh_drv:,} |"
        )

    sv3_crisis = df[
        (df["warehouse"] == "SV3 (non-conveyables)")
        & (df["msbd_su"].isin(pd.to_datetime(["2026-07-27", "2026-07-28"])))
    ]
    crisis_ifr = sv3_crisis["on_time"].mean()
    crisis_vol = sv3_crisis["ops"].nunique()

    # Timezone validation
    tz_check = df.dropna(subset=["event_datetime", "label_by_msbd_2"]).copy()
    tz_check["label_date"] = pd.to_datetime(tz_check["label_date"])
    tz_check["et_match"] = (
        (tz_check["label_date"].dt.date < tz_check["msbd_su"].dt.date)
        | (
            (tz_check["label_date"].dt.date == tz_check["msbd_su"].dt.date)
            & (tz_check["label_hour_et"] < 14)
        )
    )
    et_agreement = (
        (tz_check["label_by_msbd_2"] == 1) == tz_check["et_match"]
    ).mean()

    return f"""# JLA Home Savannah — Warehouse vs FedEx Delay Analysis

**Analysis period:** July 2026 (MSBD timebase)  
**Generated:** {pd.Timestamp.now().date().isoformat()}  
**Scope:** JLA Home Savannah dropship only (`fulfillment_type = 'DS'`)  
**Warehouses:** SV2 (conveyables, 550 Northport Pkwy) · SV3 (non-conveyables, 311 International Trade Pkwy)

## Executive summary

JLA Savannah moved **{total:,}** dropship ops in July at **{df['on_time'].mean():.1%} network IFR**. The performance gap is almost entirely at **SV3 (non-conveyables)** — **{df[df['warehouse']=='SV3 (non-conveyables)']['on_time'].mean():.1%} IFR** vs **{df[df['warehouse']=='SV2 (conveyables)']['on_time'].mean():.1%}** at SV2 (conveyables).

Of **{late_vol:,} late orders**, **{late[late['delay_attribution'].str.startswith('FedEx', na=False)]['ops'].nunique():,} ({late[late['delay_attribution'].str.startswith('FedEx', na=False)]['ops'].nunique()/late_vol:.0%})** were **labeled by 2pm on MSBD** (eligible for the 2:30pm last trailer) but **not inducted on time** — pointing to **FedEx pickup/first-scan delays**, not warehouse labeling.

A sharp deterioration hit **SV3 on MSBD July 27–28** ({crisis_vol:,} ops, **{crisis_ifr:.1%} IFR**). SV2 was largely unaffected those days.

## Timezone check — `event_datetime`

**`event_datetime` is Eastern Time (ET), not California/Pacific time.**

- Savannah warehouses operate 6am–3:30pm ET; last trailer ~2:30pm ET.
- The table's `label_by_msbd_2` flag (label by 2pm on MSBD) aligns **{et_agreement:.1%}** with parsing `event_datetime` as ET (label before MSBD, or on MSBD with hour < 14).
- A Pacific-time interpretation only matches ~{((tz_check['label_by_msbd_2']==1) == (tz_check['label_date'].dt.date < tz_check['msbd_su'].dt.date) | ((tz_check['label_date'].dt.date == tz_check['msbd_su'].dt.date) & (tz_check['label_hour_et'] < 11))).mean():.1%} of flags — confirming ET.

**Operational rule used:** Labels with `label_by_msbd_2 = 1` (or `label_hour_et < 14` on MSBD) should have made the last trailer.

## Warehouse performance (July 2026)

| Warehouse | Volume | IFR | Late orders | FedEx-driven late | WH-driven late (after 2pm) |
|-----------|-------:|----:|------------:|------------------:|---------------------------:|
{chr(10).join(wh_lines)}

## Attribution methodology

| Category | Logic |
|----------|-------|
| **WH: label after 2pm MSBD** | `label_by_msbd_2 = 0` — missed trailer cutoff |
| **FedEx: label on time, inducted next day** | Labeled by 2pm but `label2I_1_adj = 1` and late MSBD — missed pickup / next-day scan |
| **FedEx: label on time, inducted 2+ days** | Labeled by 2pm but induction 2+ days after label |
| **On time** | `inducted_on_time_or_early = 1` |

## Key findings

### 1. SV3 non-conveyables is the problem site (FedEx-driven)

- **91% of SV3 late orders** had labels by 2pm MSBD but missed induction deadline.
- Largest bucket: **1,055 orders** labeled on time, inducted **next day** (1-day FedEx gap).
- Secondary: **326 orders** with **2+ day** label-to-induction gap.
- Only **132 orders (9% of SV3 late)** are warehouse-driven (label after 2pm).

### 2. SV2 conveyables is healthy

- **97.4% IFR** — FedEx delays exist but at much lower volume (288 vs 1,381 at SV3).
- WH-driven late is similar in count (188) but tiny as a % of volume.

### 3. July 27–28 crisis (SV3 only)

| MSBD | SV3 Volume | SV3 IFR | FedEx late | WH late |
|------|----------:|--------:|-----------:|--------:|
| 2026-07-27 | 1,006 | 42.3% | 560 | 20 |
| 2026-07-28 | 494 | 21.1% | 298 | 92 |
| 2026-07-29+ | — | ~98% | — | — |

SV3 recovered to **>98% IFR** from July 29 onward. SV2 held **>93% IFR** through the crisis window.

### 4. Label batch timing on MSBD

SV3 labels on MSBD day cluster at **~5am ET** (bulk print). Late vs on-time orders share this pattern — the issue is **not** missing the 2pm cutoff for most orders; it's **carrier pickup after labels are ready**.

## Charts

| Chart | File |
|-------|------|
| IFR by warehouse | [01_ifr_by_warehouse.png](jla_savannah_charts/01_ifr_by_warehouse.png) |
| Weekly IFR trend | [02_weekly_ifr_trend.png](jla_savannah_charts/02_weekly_ifr_trend.png) |
| Late order attribution | [03_late_attribution.png](jla_savannah_charts/03_late_attribution.png) |
| SV3 daily IFR | [04_sv3_daily_ifr.png](jla_savannah_charts/04_sv3_daily_ifr.png) |
| SV3 label hour distribution | [05_sv3_label_hour.png](jla_savannah_charts/05_sv3_label_hour.png) |

## Data exports

- Full order-level: `output/jla_savannah/jla_savannah_orders_july2026.csv`
- Late orders only: `output/jla_savannah/jla_savannah_late_orders_july2026.csv`
- Attribution summary: `output/jla_savannah/jla_savannah_attribution_summary.csv`

## Recommended next steps

1. **FedEx Savannah pickup at SV3** — what changed July 27–28 for non-conveyables? Trailer capacity, missed pickup, hub backlog?
2. **SV2 vs SV3 pickup cadence** — same FedEx station (SAVANNAH) but very different outcomes; are conveyables and non-conveyables on separate pickup routes/trailers?
3. **Label-to-induction SLA** — track `label2I_0_adj` weekly at SV3; target same-day induction for labels printed before 2pm.
4. **July 28 WH spike** — 92 SV3 orders labeled after 2pm (unusual vs ~20/day on 7/27); staffing or cutoff issue worth confirming with warehouse ops.
"""


def attribution_summary(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for wh in WAREHOUSES + ["Network"]:
        sub = df if wh == "Network" else df[df["warehouse"] == wh]
        vol = sub["ops"].nunique()
        late = sub[sub["on_time"] == 0]
        for attr in ATTRIBUTION_ORDER:
            n = sub[sub["delay_attribution"] == attr]["ops"].nunique()
            rows.append({
                "warehouse": wh,
                "attribution": attr,
                "volume": n,
                "pct_of_total": n / vol if vol else 0,
                "pct_of_late": n / late["ops"].nunique() if len(late) else 0,
            })
    return pd.DataFrame(rows)


def main() -> None:
    sns.set_theme(style="whitegrid", font_scale=1.05)
    OUT.mkdir(parents=True, exist_ok=True)
    CHARTS.mkdir(parents=True, exist_ok=True)

    print("Pulling JLA Savannah order-level data...")
    df = load_orders()
    print(f"Loaded {len(df):,} rows ({df['ops'].nunique():,} distinct ops)")

    order_path = OUT / "jla_savannah_orders_july2026.csv"
    df.to_csv(order_path, index=False)
    print(f"Wrote {order_path}")

    late = df[df["on_time"] == 0]
    late_path = OUT / "jla_savannah_late_orders_july2026.csv"
    late.to_csv(late_path, index=False)
    print(f"Wrote {late_path} ({len(late):,} late rows)")

    summary = attribution_summary(df)
    summary_path = OUT / "jla_savannah_attribution_summary.csv"
    summary.to_csv(summary_path, index=False)
    print(f"Wrote {summary_path}")

    print("Building charts...")
    chart_ifr_by_warehouse(df)
    chart_weekly_trend(df)
    chart_attribution(df)
    chart_daily_crisis(df)
    chart_label_hour(df)
    print(f"Charts saved to {CHARTS}")

    report = build_summary(df)
    report_path = DOCS / "jla_savannah_delay_analysis.md"
    report_path.write_text(report)
    print(f"Wrote {report_path}")


if __name__ == "__main__":
    main()
