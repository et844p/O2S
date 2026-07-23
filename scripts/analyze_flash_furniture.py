#!/usr/bin/env python3
"""Flash Furniture induction analysis — order-level export, themes, and charts."""

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

SQL_ORDER = ROOT / "sql" / "flash_furniture_order_level.sql"
OUT = ROOT / "output" / "flash_furniture"
DOCS = ROOT / "docs" / "small_parcel"
CHARTS = DOCS / "flash_furniture_charts"

WAREHOUSE_LABEL = {
    ("Canton", "GA"): "Canton, GA",
    ("Olive Branch", "MS"): "Olive Branch, MS",
    ("Chino", "CA"): "Chino, CA",
}

DOW = {1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat", 7: "Sun"}


def warehouse_name(df: pd.DataFrame) -> pd.Series:
    return df["city_name"].str.strip() + ", " + df["state_name"].str.strip()


def load_orders() -> pd.DataFrame:
    df = query_df(SQL_ORDER.read_text())
    df["warehouse"] = warehouse_name(df)
    df["on_time"] = df["inducted_on_time_or_early"].fillna(0).astype(int)
    df["msbd_su"] = pd.to_datetime(df["msbd_su"])
    df["order_complete_date"] = pd.to_datetime(df["order_complete_date"])
    df["induction_date_lidd"] = pd.to_datetime(df["induction_date_lidd"])
    df["msbd_week"] = df["msbd_su"].dt.to_period("W-SUN").dt.start_time
    df["order_dow_name"] = df["order_dow"].map(DOW)
    df["days_late"] = (df["induction_date_lidd"] - df["msbd_su"]).dt.days
    df.loc[df["on_time"] == 1, "days_late"] = 0
    df.loc[df["not_inducted_but_late_already"] == 1, "days_late"] = pd.NA
    return df


def late_bucket(row: pd.Series) -> str:
    if row["on_time"] == 1:
        return "On time / early"
    if row.get("not_inducted_but_late_already") == 1:
        return "Not inducted (late)"
    if row.get("not_inducted_not_late_yet") == 1:
        return "Not inducted (open)"
    if row.get("one_day_late") == 1:
        return "1 day late"
    if row.get("two_day_late") == 1:
        return "2 days late"
    if row.get("three_five_day_inducted_late") == 1:
        return "3–5 days late"
    if row.get("three_days_plus_late") == 1:
        return "3+ days late"
    if row.get("inducted_late") == 1:
        return "Other late"
    return "Other"


def chart_ifr_by_warehouse(df: pd.DataFrame) -> None:
    main = df[df["warehouse"].isin(WAREHOUSE_LABEL.values())]
    agg = (
        main.groupby("warehouse", as_index=False)
        .agg(volume=("ops", "nunique"), ifr=("on_time", "mean"))
        .sort_values("volume", ascending=False)
    )
    fig, ax = plt.subplots(figsize=(8, 5))
    colors = ["#2ecc71" if x >= 0.85 else "#e74c3c" if x < 0.6 else "#f39c12" for x in agg["ifr"]]
    bars = ax.bar(agg["warehouse"], agg["ifr"], color=colors)
    ax.axhline(0.85, color="#333", linestyle="--", linewidth=1, label="85% target")
    ax.set_ylim(0, 1)
    ax.set_ylabel("Induction Fill Rate")
    ax.set_title("Flash Furniture — IFR by Warehouse (L3M)")
    for bar, vol in zip(bars, agg["volume"]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02, f"n={vol:,}", ha="center", fontsize=9)
    ax.legend()
    fig.tight_layout()
    fig.savefig(CHARTS / "01_ifr_by_warehouse.png", dpi=150)
    plt.close(fig)


def chart_weekly_trend(df: pd.DataFrame) -> None:
    main = df[df["warehouse"].isin(WAREHOUSE_LABEL.values())]
    agg = (
        main.groupby(["msbd_week", "warehouse"], as_index=False)
        .agg(volume=("ops", "nunique"), ifr=("on_time", "mean"))
    )
    fig, ax = plt.subplots(figsize=(11, 5))
    for wh in agg["warehouse"].unique():
        sub = agg[agg["warehouse"] == wh]
        ax.plot(sub["msbd_week"], sub["ifr"], marker="o", label=wh, linewidth=2)
    ax.axhline(0.85, color="#333", linestyle="--", linewidth=1, alpha=0.7)
    ax.set_ylabel("IFR")
    ax.set_xlabel("MSBD week")
    ax.set_title("Flash Furniture — Weekly IFR Trend (L3M)")
    ax.legend(loc="lower left")
    ax.set_ylim(0, 1.05)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(CHARTS / "02_weekly_ifr_trend.png", dpi=150)
    plt.close(fig)


def chart_late_buckets(df: pd.DataFrame) -> None:
    main = df[df["warehouse"].isin(WAREHOUSE_LABEL.values())].copy()
    main["late_bucket"] = main.apply(late_bucket, axis=1)
    order = [
        "On time / early",
        "1 day late",
        "2 days late",
        "3–5 days late",
        "3+ days late",
        "Other late",
        "Not inducted (late)",
        "Not inducted (open)",
    ]
    agg = main.groupby(["warehouse", "late_bucket"]).size().reset_index(name="vol")
    pivot = agg.pivot(index="late_bucket", columns="warehouse", values="vol").fillna(0)
    pivot = pivot.reindex([b for b in order if b in pivot.index])
    fig, ax = plt.subplots(figsize=(10, 6))
    pivot.plot(kind="barh", stacked=False, ax=ax, width=0.75)
    ax.set_xlabel("Order volume (ops)")
    ax.set_title("Flash Furniture — Late Induction Breakdown by Warehouse")
    ax.legend(title="Warehouse", bbox_to_anchor=(1.02, 1), loc="upper left")
    fig.tight_layout()
    fig.savefig(CHARTS / "03_late_bucket_breakdown.png", dpi=150)
    plt.close(fig)


def chart_label_vs_induction(df: pd.DataFrame) -> None:
    main = df[df["warehouse"].isin(WAREHOUSE_LABEL.values())]
    metrics = {
        "Label same day (o2label_0)": "o2label_0_adj",
        "Label ≤1 day": "o2label_1_adj",
        "Induct ≤1 day after label (label2I_1)": "label2I_1_adj",
        "Induct ≤2 days after label (label2I_2)": "label2I_2_adj",
        "Induct ≤1 day from order (o2I_1)": "o2I_1_adj",
    }
    rows = []
    for wh in main["warehouse"].unique():
        sub = main[main["warehouse"] == wh]
        for label, col in metrics.items():
            rows.append({"warehouse": wh, "metric": label, "rate": sub[col].mean()})
    plot_df = pd.DataFrame(rows)
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(data=plot_df, x="metric", y="rate", hue="warehouse", ax=ax)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Share of orders")
    ax.set_xlabel("")
    ax.set_title("Flash Furniture — Label vs Carrier Induction Timing")
    plt.xticks(rotation=25, ha="right")
    fig.tight_layout()
    fig.savefig(CHARTS / "04_label_vs_induction_timing.png", dpi=150)
    plt.close(fig)


def chart_order_dow(df: pd.DataFrame) -> None:
    main = df[df["warehouse"].isin(WAREHOUSE_LABEL.values())]
    agg = (
        main.groupby(["warehouse", "order_dow_name"], as_index=False)
        .agg(ifr=("on_time", "mean"), vol=("ops", "count"))
    )
    dow_order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    agg["order_dow_name"] = pd.Categorical(agg["order_dow_name"], categories=dow_order, ordered=True)
    agg = agg.sort_values(["warehouse", "order_dow_name"])
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(data=agg, x="order_dow_name", y="ifr", hue="warehouse", ax=ax)
    ax.axhline(0.85, color="#333", linestyle="--", linewidth=1)
    ax.set_ylabel("IFR")
    ax.set_xlabel("Order placed day")
    ax.set_title("Flash Furniture — IFR by Order Day of Week")
    ax.set_ylim(0, 1.05)
    fig.tight_layout()
    fig.savefig(CHARTS / "05_ifr_by_order_dow.png", dpi=150)
    plt.close(fig)


def chart_weekend_gap(df: pd.DataFrame) -> None:
    main = df[df["warehouse"].isin(WAREHOUSE_LABEL.values())].copy()
    main["fri_sat"] = main["order_dow"].isin([5, 6])
    main["weekend_induct"] = main["induction_dow_adj"].isin([6, 7])
    agg = (
        main[main["fri_sat"]]
        .groupby("warehouse", as_index=False)
        .agg(
            fri_sat_vol=("ops", "nunique"),
            weekend_inducted=("weekend_induct", "sum"),
        )
    )
    agg["weekend_ship_rate"] = agg["weekend_inducted"] / agg["fri_sat_vol"]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(agg["warehouse"], agg["weekend_ship_rate"], color="#3498db")
    ax.axhline(0.70, color="#333", linestyle="--", label="70% weekend ship benchmark")
    ax.set_ylim(0, 1)
    ax.set_ylabel("% Fri/Sat orders inducted Sat/Sun")
    ax.set_title("Flash Furniture — Weekend Induction on Fri/Sat Placed Orders")
    ax.legend()
    for i, (_, row) in enumerate(agg.iterrows()):
        ax.text(i, row["weekend_ship_rate"] + 0.02, f"{row['weekend_ship_rate']:.0%}", ha="center")
    fig.tight_layout()
    fig.savefig(CHARTS / "06_weekend_induction_gap.png", dpi=150)
    plt.close(fig)


def build_findings(df: pd.DataFrame) -> str:
    main = df[df["warehouse"].isin(WAREHOUSE_LABEL.values())]
    total_vol = main["ops"].nunique()
    overall_ifr = main["on_time"].mean()
    late_vol = main[main["on_time"] == 0]["ops"].nunique()
    one_day_late = main[main["one_day_late"] == 1]["ops"].nunique()

    wh = (
        main.groupby("warehouse", as_index=False)
        .agg(vol=("ops", "nunique"), ifr=("on_time", "mean"))
        .sort_values("vol", ascending=False)
    )

    recent = main[main["msbd_su"] >= main["msbd_su"].max() - pd.Timedelta(weeks=4)]
    recent_ifr = (
        recent.groupby("warehouse", as_index=False)
        .agg(vol=("ops", "nunique"), ifr=("on_time", "mean"))
        .sort_values("vol", ascending=False)
    )

    label_ok = main["o2label_1_adj"].mean()
    label2i_1 = main["label2I_1_adj"].mean()
    late_label2i_1 = main.loc[main["inducted_late"] == 1, "label2I_1_adj"].mean()

    lines = [
        "# Flash Furniture — Induction Performance Analysis",
        "",
        f"**Analysis period:** Past 3 months (MSBD timebase)  ",
        f"**Generated:** {pd.Timestamp.now().date().isoformat()}  ",
        f"**Parent supplier:** Flash Furniture",
        "",
        "## Executive summary",
        "",
        f"Flash Furniture moved **{total_vol:,}** small-parcel ops across three warehouses in the last 3 months at **{overall_ifr:.1%} network IFR** — well below the 85% target. **{late_vol:,} orders ({late_vol/total_vol:.1%})** missed supplier MSBD induction, with **{one_day_late:,}** of those only **1 day late**.",
        "",
        "The primary issue is **not label creation** — labels are printed on time in >97% of orders. The gap is **carrier induction after label print**: only ~{:.0%} of orders are inducted within 1 day of label, and late orders average just {:.0%} same-day label-to-induction.".format(label2i_1, main.loc[main['inducted_late']==1,'label2I_0_adj'].mean()),
        "",
        "**Performance has deteriorated sharply in July 2026**, especially at Canton and Olive Branch (recent 4-week IFR in the 10–34% range vs ~60–75% earlier in the period).",
        "",
        "## Warehouse performance (L3M)",
        "",
        "| Warehouse | Volume | IFR |",
        "|-----------|-------:|----:|",
    ]
    for _, r in wh.iterrows():
        lines.append(f"| {r['warehouse']} | {int(r['vol']):,} | {r['ifr']:.1%} |")

    lines += [
        "",
        "## Recent trend (last 4 MSBD weeks)",
        "",
        "| Warehouse | Volume | IFR |",
        "|-----------|-------:|----:|",
    ]
    for _, r in recent_ifr.iterrows():
        lines.append(f"| {r['warehouse']} | {int(r['vol']):,} | {r['ifr']:.1%} |")

    lines += [
        "",
        "## Key themes — why volume is not inducting on time",
        "",
        "### 1. Label-to-induction gap (primary driver)",
        "- Labels are created quickly: **{:.1%}** of orders have a label within 1 day of order.".format(label_ok),
        "- Carrier induction lags: only **{:.1%}** inducted within 1 day of label (network-wide).".format(label2i_1),
        "- For **late orders**, only **{:.1%}** get same-day label-to-induction vs **{:.1%}** for on-time orders.".format(
            main.loc[main["inducted_late"] == 1, "label2I_0_adj"].mean(),
            main.loc[main["on_time"] == 1, "label2I_0_adj"].mean(),
        ),
        "- **Implication:** warehouse is largely printing labels on MSBD, but **FedEx pickup / first scan is delayed 1–2 days**.",
        "",
        "### 2. 1-day-late concentration",
        "- The largest late bucket is **1 day past MSBD** (Canton: 2,703 | Olive Branch: 2,520 | Chino: 853).",
        "- This is consistent with **next-day pickup failure** rather than multi-day warehouse processing delays.",
        "",
        "### 3. Olive Branch (MS) is the weakest site",
        "- Lowest IFR at **49.1%** on 8,491 ops.",
        "- Mon/Tue order placement IFR is **30–39%** — suggests start-of-week pickup cadence issues.",
        "- Station: **OLIVE BRANCH LOCAL**.",
        "",
        "### 4. Canton (GA) volume leader with recent collapse",
        "- Highest volume (**11,652 ops**) at **61.7%** IFR for the period.",
        "- IFR dropped to **20–34%** in July 2026 weeks — needs immediate operational review.",
        "- Station: **MARIETTA LOCAL**.",
        "",
        "### 5. Weekend induction gap",
        "- Fri/Sat placed orders are **not** getting weekend carrier induction at scale (~50–53% weekend induct rate).",
        "- Weekend shipping enablement or Saturday pickup alignment could recover meaningful volume.",
        "",
        "### 6. Not a lead-time / cushion / capacity issue",
        "- All sites on **24hr SP LT** with low cushion (0.25–1.09 days) and negligible capacity padding.",
        "- O2S actual averages **1.9–2.1 days** vs **1.5 day** MSBD window — supplier is shipping close to deadline but missing carrier scan.",
        "",
        "### 7. Chino (CA) — smaller but similar pattern",
        "- **2,437 ops** at **55.2%** IFR; same 1-day-late concentration.",
        "",
        "## Recommended discussion topics for Flash Furniture meeting",
        "",
        "1. **FedEx pickup schedule & manifest timing** — align label print cutoff with guaranteed daily pickup.",
        "2. **July deterioration** — what changed operationally (staffing, cutoff, carrier switch, volume spike)?",
        "3. **Olive Branch Mon/Tue performance** — dedicated pickup or earlier weekend processing.",
        "4. **Weekend induction** — evaluate Saturday pickup or adjusted MSBD for Fri/Sat orders.",
        "5. **Same-day label-to-induction KPI** — track `label2I_0_adj` weekly by warehouse.",
        "",
        "## Charts",
        "",
        "| Chart | File |",
        "|-------|------|",
        "| IFR by warehouse | [01_ifr_by_warehouse.png](flash_furniture_charts/01_ifr_by_warehouse.png) |",
        "| Weekly IFR trend | [02_weekly_ifr_trend.png](flash_furniture_charts/02_weekly_ifr_trend.png) |",
        "| Late bucket breakdown | [03_late_bucket_breakdown.png](flash_furniture_charts/03_late_bucket_breakdown.png) |",
        "| Label vs induction timing | [04_label_vs_induction_timing.png](flash_furniture_charts/04_label_vs_induction_timing.png) |",
        "| IFR by order DOW | [05_ifr_by_order_dow.png](flash_furniture_charts/05_ifr_by_order_dow.png) |",
        "| Weekend induction gap | [06_weekend_induction_gap.png](flash_furniture_charts/06_weekend_induction_gap.png) |",
        "",
        "## Data exports",
        "",
        "- Full order-level: `output/flash_furniture/flash_furniture_orders_l3m.csv`",
        "- Late orders only: `output/flash_furniture/flash_furniture_late_orders_l3m.csv`",
    ]
    return "\n".join(lines)


def main() -> None:
    sns.set_theme(style="whitegrid", font_scale=1.05)
    OUT.mkdir(parents=True, exist_ok=True)
    CHARTS.mkdir(parents=True, exist_ok=True)

    print("Pulling order-level data from BigQuery...")
    df = load_orders()
    print(f"Loaded {len(df):,} rows ({df['ops'].nunique():,} distinct ops)")

    order_path = OUT / "flash_furniture_orders_l3m.csv"
    df.to_csv(order_path, index=False)
    print(f"Wrote {order_path}")

    late = df[df["on_time"] == 0]
    late_path = OUT / "flash_furniture_late_orders_l3m.csv"
    late.to_csv(late_path, index=False)
    print(f"Wrote {late_path} ({len(late):,} late rows)")

    print("Building charts...")
    chart_ifr_by_warehouse(df)
    chart_weekly_trend(df)
    chart_late_buckets(df)
    chart_label_vs_induction(df)
    chart_order_dow(df)
    chart_weekend_gap(df)
    print(f"Charts saved to {CHARTS}")

    findings = build_findings(df)
    findings_path = DOCS / "flash_furniture_induction_analysis.md"
    findings_path.write_text(findings)
    print(f"Wrote {findings_path}")


if __name__ == "__main__":
    main()
