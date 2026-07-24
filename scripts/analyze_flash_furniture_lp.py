#!/usr/bin/env python3
"""Flash Furniture large-parcel analysis — routing-aware pickup metrics."""

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

SQL_ORDER = ROOT / "sql" / "flash_furniture_lp_order_level.sql"
OUT = ROOT / "output" / "flash_furniture_lp"
DOCS = ROOT / "docs" / "large_parcel"
CHARTS = DOCS / "flash_furniture_lp_charts"
GITHUB_REPO = "https://github.com/et844p/O2S/blob/main"

WAREHOUSE_MAP = {
    14765: "Canton, GA",
    17059: "Olive Branch, MS",
    58199: "Chino, CA",
    119961: "Columbus, OH",
}

ROUTING_COLORS = {
    "Live Load Pooled": "#3498db",
    "OTR": "#e67e22",
    "LTL to PP": "#95a5a6",
}


def load_orders() -> pd.DataFrame:
    df = query_df(SQL_ORDER.read_text())
    df["warehouse"] = df["ChildSuID"].map(WAREHOUSE_MAP).fillna(df["suname"])
    df["on_time_pickup"] = df["pickup_on_time"].fillna(0).astype(int)
    df["on_time_induction"] = df["inducted_on_time_or_early"].fillna(0).astype(int)
    df["msbd"] = pd.to_datetime(df["supplier_must_ship_by_date"])
    df["msbd_week"] = pd.to_datetime(df["msbd_week"])
    df["rfpd_new"] = pd.to_datetime(df["rfpd_new"], errors="coerce")
    return df


def chart_pickup_by_warehouse(df: pd.DataFrame) -> None:
    agg = (
        df.groupby(["warehouse", "Routingtype"], as_index=False)
        .agg(volume=("opid", "nunique"), pickup_ot=("on_time_pickup", "mean"))
        .sort_values("volume", ascending=False)
    )
    fig, ax = plt.subplots(figsize=(9, 5))
    warehouses = agg["warehouse"].unique()
    x = range(len(warehouses))
    width = 0.35
    for i, routing in enumerate(agg["Routingtype"].unique()):
        sub = agg[agg["Routingtype"] == routing].set_index("warehouse").reindex(warehouses)
        offset = (i - 0.5) * width
        bars = ax.bar(
            [xi + offset for xi in x],
            sub["pickup_ot"].fillna(0),
            width,
            label=routing,
            color=ROUTING_COLORS.get(routing, "#7f8c8d"),
        )
        for bar, vol in zip(bars, sub["volume"].fillna(0)):
            if vol > 0:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.02,
                    f"n={int(vol)}",
                    ha="center",
                    fontsize=8,
                )
    ax.set_xticks(list(x))
    ax.set_xticklabels(warehouses, rotation=15, ha="right")
    ax.axhline(0.85, color="#333", linestyle="--", linewidth=1, label="85% target")
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Pickup On-Time Rate")
    ax.set_title("Flash Furniture LP — Routing-Aware Pickup Performance (L3M)")
    ax.legend(loc="lower right", fontsize=8)
    fig.tight_layout()
    fig.savefig(CHARTS / "01_pickup_by_warehouse.png", dpi=150)
    plt.close(fig)


def chart_ifr_by_warehouse(df: pd.DataFrame) -> None:
    agg = (
        df.groupby("warehouse", as_index=False)
        .agg(volume=("opid", "nunique"), ifr=("on_time_induction", "mean"))
        .sort_values("volume", ascending=False)
    )
    fig, ax = plt.subplots(figsize=(8, 5))
    colors = ["#2ecc71" if x >= 0.85 else "#e74c3c" if x < 0.3 else "#f39c12" for x in agg["ifr"]]
    bars = ax.bar(agg["warehouse"], agg["ifr"], color=colors)
    ax.axhline(0.85, color="#333", linestyle="--", linewidth=1)
    ax.set_ylim(0, 1)
    ax.set_ylabel("Induction Fill Rate")
    ax.set_title("Flash Furniture LP — IFR by Warehouse (L3M)")
    for bar, vol in zip(bars, agg["volume"]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02, f"n={vol}", ha="center", fontsize=9)
    fig.tight_layout()
    fig.savefig(CHARTS / "02_ifr_by_warehouse.png", dpi=150)
    plt.close(fig)


def chart_rfpd_vs_pickup(df: pd.DataFrame) -> None:
    live = df[df["Routingtype"] == "Live Load Pooled"]
    agg = (
        live.groupby("warehouse", as_index=False)
        .agg(
            volume=("opid", "nunique"),
            rfpd_ot=("rfpd_early_ontime_SU_new", "mean"),
            pu_on_rfpd=("pu_onrfpd_new", "mean"),
            pu_sla=("pu_withinSLA_new", "mean"),
        )
        .sort_values("volume", ascending=False)
    )
    fig, ax = plt.subplots(figsize=(9, 5))
    x = range(len(agg))
    width = 0.25
    metrics = [
        ("rfpd_ot", "RFPD on-time", "#e74c3c"),
        ("pu_on_rfpd", "Pickup on RFPD", "#3498db"),
        ("pu_sla", "Pickup within SLA", "#2ecc71"),
    ]
    for i, (col, label, color) in enumerate(metrics):
        ax.bar([xi + (i - 1) * width for xi in x], agg[col], width, label=label, color=color)
    ax.set_xticks(list(x))
    ax.set_xticklabels(agg["warehouse"], rotation=15, ha="right")
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Rate")
    ax.set_title("Flash Furniture LP — Live Load: RFPD vs Carrier Pickup (L3M)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(CHARTS / "03_live_load_rfpd_vs_pickup.png", dpi=150)
    plt.close(fig)


def chart_otr_pickup_trucks(df: pd.DataFrame) -> None:
    otr = df[df["Routingtype"] == "OTR"].copy()
    if otr.empty:
        return
    agg = (
        otr.groupby("warehouse", as_index=False)
        .agg(
            volume=("opid", "nunique"),
            pu_on_msbd=("otr_pu_on_msbd", "mean"),
            pu_on_or_before_msbd=("otr_pu_on_or_before_msbd", "mean"),
            pu_sla=("otr_pu_within_sla", "mean"),
            rfpd_ot=("otr_rfpd_ontime", "mean"),
            truck_eff=("otr_truck_efficiency", "mean"),
        )
    )
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    ax = axes[0]
    x = range(len(agg))
    width = 0.2
    for i, (col, label, color) in enumerate(
        [
            ("rfpd_ot", "RFPD on-time", "#e74c3c"),
            ("pu_on_msbd", "Pickup on MSBD", "#3498db"),
            ("pu_on_or_before_msbd", "Pickup on/before MSBD", "#2ecc71"),
            ("pu_sla", "Pickup within SLA", "#9b59b6"),
        ]
    ):
        ax.bar([xi + (i - 1.5) * width for xi in x], agg[col], width, label=label, color=color)
    ax.set_xticks(list(x))
    ax.set_xticklabels(agg["warehouse"])
    ax.set_ylim(0, 1.05)
    ax.set_title("OTR Pickup Alignment to MSBD")
    ax.legend(fontsize=7, loc="upper right")

    ax2 = axes[1]
    ax2.bar(agg["warehouse"], agg["truck_eff"].fillna(0), color="#e67e22")
    ax2.axhline(1.0, color="#333", linestyle="--", linewidth=1, label="100% execution")
    ax2.set_title("OTR Truck Efficiency (executed / planned)")
    ax2.set_ylabel("Ratio")
    ax2.legend(fontsize=8)

    fig.suptitle("Flash Furniture — Olive Branch OTR Operations (L3M)", fontsize=12)
    fig.tight_layout()
    fig.savefig(CHARTS / "04_otr_pickup_and_trucks.png", dpi=150)
    plt.close(fig)


def chart_weekly_trend(df: pd.DataFrame) -> None:
    main = df[df["warehouse"].isin(WAREHOUSE_MAP.values())]
    agg = (
        main.groupby(["msbd_week", "warehouse"], as_index=False)
        .agg(volume=("opid", "nunique"), pickup_ot=("on_time_pickup", "mean"), ifr=("on_time_induction", "mean"))
        .sort_values("msbd_week")
    )
    fig, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    for wh in agg["warehouse"].unique():
        sub = agg[agg["warehouse"] == wh]
        axes[0].plot(sub["msbd_week"], sub["pickup_ot"], marker="o", label=wh, linewidth=2)
        axes[1].plot(sub["msbd_week"], sub["ifr"], marker="s", label=wh, linewidth=2)
    axes[0].axhline(0.85, color="#999", linestyle="--", linewidth=1)
    axes[0].set_ylabel("Pickup On-Time")
    axes[0].set_title("Weekly Pickup On-Time by Warehouse")
    axes[0].legend(fontsize=8)
    axes[1].axhline(0.85, color="#999", linestyle="--", linewidth=1)
    axes[1].set_ylabel("IFR")
    axes[1].set_title("Weekly IFR by Warehouse")
    axes[1].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(CHARTS / "05_weekly_trend.png", dpi=150)
    plt.close(fig)


def chart_pickup_to_induction_gap(df: pd.DataFrame) -> None:
    scored = df[df["on_time_pickup"].notna() & df["on_time_induction"].notna()].copy()
    scored["gap_bucket"] = scored.apply(
        lambda r: "Pickup OK, inducted late"
        if r["on_time_pickup"] == 1 and r["on_time_induction"] == 0
        else "Pickup late, inducted on time"
        if r["on_time_pickup"] == 0 and r["on_time_induction"] == 1
        else "Both on time"
        if r["on_time_pickup"] == 1 and r["on_time_induction"] == 1
        else "Both late",
        axis=1,
    )
    agg = (
        scored.groupby(["warehouse", "gap_bucket"], as_index=False)
        .agg(volume=("opid", "nunique"))
    )
    pivot = agg.pivot(index="warehouse", columns="gap_bucket", values="volume").fillna(0)
    fig, ax = plt.subplots(figsize=(9, 5))
    pivot.plot(kind="bar", stacked=True, ax=ax, colormap="Set2")
    ax.set_title("Flash Furniture LP — Pickup vs Induction Gap (L3M)")
    ax.set_ylabel("Order volume")
    ax.legend(title="", fontsize=8, bbox_to_anchor=(1.02, 1))
    fig.tight_layout()
    fig.savefig(CHARTS / "06_pickup_induction_gap.png", dpi=150)
    plt.close(fig)


def _metrics(df: pd.DataFrame) -> dict:
    main = df[df["warehouse"].isin(WAREHOUSE_MAP.values())]
    wh = (
        main.groupby(["warehouse", "Routingtype"], as_index=False)
        .agg(
            vol=("opid", "nunique"),
            pickup_ot=("on_time_pickup", "mean"),
            ifr=("on_time_induction", "mean"),
            rfpd_ot=("rfpd_early_ontime_SU_new", "mean"),
            pu_sla=("pu_withinSLA_new", "mean"),
        )
        .sort_values("vol", ascending=False)
    )
    live = main[main["Routingtype"] == "Live Load Pooled"]
    otr = main[main["Routingtype"] == "OTR"]
    return {
        "main": main,
        "total_vol": main["opid"].nunique(),
        "overall_pickup": main["on_time_pickup"].mean(),
        "overall_ifr": main["on_time_induction"].mean(),
        "late_pickup_vol": main[main["on_time_pickup"] == 0]["opid"].nunique(),
        "late_ifr_vol": main[main["on_time_induction"] == 0]["opid"].nunique(),
        "wh": wh,
        "live_rfpd_ot": live["rfpd_early_ontime_SU_new"].mean() if len(live) else 0,
        "live_pu_on_rfpd": live["pu_onrfpd_new"].mean() if len(live) else 0,
        "otr_pu_on_msbd": otr["otr_pu_on_msbd"].mean() if len(otr) else 0,
        "otr_pu_on_or_before_msbd": otr["otr_pu_on_or_before_msbd"].mean() if len(otr) else 0,
        "otr_truck_eff": otr["otr_truck_efficiency"].mean() if len(otr) else 0,
    }


def build_findings(df: pd.DataFrame) -> str:
    m = _metrics(df)
    wh = m["wh"]
    total = m["total_vol"]

    wh_lines = "\n".join(
        f"| {r['warehouse']} | {r['Routingtype']} | {int(r['vol']):,} | {r['pickup_ot']:.1%} | {r['ifr']:.1%} |"
        for _, r in wh.iterrows()
    )

    return f"""# Flash Furniture — Large Parcel Performance Analysis

**Analysis period:** Past 3 months (supplier MSBD timebase)  
**Generated:** {pd.Timestamp.now().date().isoformat()}  
**Parent supplier:** Flash Furniture  
**Scope:** Large parcel (`LP_dash_ET` + `OTR_Tracking_ET` for OTR)

## Executive summary

Flash Furniture moved **{total:,}** large-parcel ops in the last 3 months at **{m['overall_pickup']:.1%} routing-aware pickup on-time** and **{m['overall_ifr']:.1%} induction fill rate (IFR)**. Warehouses run **different routing setups**, so pickup is measured differently by site:

| Warehouse | Routing | Pickup metric |
|-----------|---------|---------------|
| Canton, GA | Live Load Pooled | RFPD on-time (`rfpd_early_ontime_SU_new`) |
| Chino, CA | Live Load Pooled | RFPD on-time |
| Olive Branch, MS | OTR | Pickup on/before MSBD (`OTR_Tracking_ET`) |

**{m['late_pickup_vol']:,} orders ({m['late_pickup_vol']/total:.1%})** missed pickup on-time. **{m['late_ifr_vol']:,} orders ({m['late_ifr_vol']/total:.1%})** missed induction on-time.

## Warehouse performance (L3M)

| Warehouse | Routing | Volume | Pickup OT | IFR |
|-----------|---------|-------:|----------:|----:|
{wh_lines}

## Key themes — how to improve

### 1. Live Load sites (Canton, Chino): RFPD registration is the bottleneck

- Network RFPD on-time: **{m['live_rfpd_ot']:.1%}** across Live Load warehouses.
- Carrier pickup on RFPD day is much stronger: **{m['live_pu_on_rfpd']:.1%}** — carriers are showing up once freight is staged.
- **Canton (GA)** is the weakest Live Load site at only **{wh.loc[wh['warehouse']=='Canton, GA', 'rfpd_ot'].iloc[0]:.1%}** RFPD on-time despite **{wh.loc[wh['warehouse']=='Canton, GA', 'pu_sla'].iloc[0]:.1%}** pickup-within-SLA.
- **Implication:** focus supplier conversation on **earlier RFPD registration / warehouse staging**, not carrier scheduling.

### 2. Olive Branch (MS) OTR: pickups not aligning to MSBD days

- Only **{m['otr_pu_on_msbd']:.1%}** of OTR orders have carrier pickup on the exact MSBD.
- **{m['otr_pu_on_or_before_msbd']:.1%}** picked up on or before MSBD.
- RFPD on-time at **{wh.loc[wh['warehouse']=='Olive Branch, MS', 'rfpd_ot'].iloc[0]:.1%}** — better than Canton but still weak.
- OTR truck execution ratio: **{m['otr_truck_eff']:.1%}** (executed / planned trucks).
- **Implication:** review **OTR pickup schedule vs MSBD calendar**, confirm orders are loaded onto the correct daily pickup, and validate `OTR_Tracking_ET` load depart dates against MSBD.

### 3. Pickup-on-time does not guarantee induction

- Some orders pass pickup but still miss IFR — see pickup vs induction gap chart.
- For Live Load, late RFPD pushes induction past MSBD even when carrier pickup SLA is met.

### 4. Chino (CA) is the strongest LP performer

- Highest IFR at **{wh.loc[wh['warehouse']=='Chino, CA', 'ifr'].iloc[0]:.1%}** with **{wh.loc[wh['warehouse']=='Chino, CA', 'rfpd_ot'].iloc[0]:.1%}** RFPD on-time.
- Use Chino as benchmark for RFPD staging practices at Canton.

## Recommended discussion topics

1. **Canton RFPD process** — what prevents staging on MSBD? Partner Home registration timing?
2. **Olive Branch OTR schedule** — align pickup days to MSBD; review truck loading and `Load_Depart_Date` vs MSBD.
3. **Cross-site playbook** — replicate Chino RFPD staging at Canton.
4. **Weekly KPIs** — track routing-aware pickup on-time and IFR by warehouse.

## Charts

| Chart | File |
|-------|------|
| Pickup on-time by warehouse | [01_pickup_by_warehouse.png](flash_furniture_lp_charts/01_pickup_by_warehouse.png) |
| IFR by warehouse | [02_ifr_by_warehouse.png](flash_furniture_lp_charts/02_ifr_by_warehouse.png) |
| Live Load RFPD vs pickup | [03_live_load_rfpd_vs_pickup.png](flash_furniture_lp_charts/03_live_load_rfpd_vs_pickup.png) |
| OTR pickup & trucks | [04_otr_pickup_and_trucks.png](flash_furniture_lp_charts/04_otr_pickup_and_trucks.png) |
| Weekly trend | [05_weekly_trend.png](flash_furniture_lp_charts/05_weekly_trend.png) |
| Pickup vs induction gap | [06_pickup_induction_gap.png](flash_furniture_lp_charts/06_pickup_induction_gap.png) |

## Data exports

- Full order-level: [flash_furniture_lp_orders_l3m.csv](../../output/flash_furniture_lp/flash_furniture_lp_orders_l3m.csv)
- Late pickup orders: [flash_furniture_lp_late_pickup_l3m.csv](../../output/flash_furniture_lp/flash_furniture_lp_late_pickup_l3m.csv)
"""


def main() -> None:
    sns.set_theme(style="whitegrid", font_scale=1.05)
    OUT.mkdir(parents=True, exist_ok=True)
    CHARTS.mkdir(parents=True, exist_ok=True)

    print("Pulling Flash Furniture LP order-level data...")
    df = load_orders()
    print(f"Loaded {len(df):,} rows ({df['opid'].nunique():,} distinct opids)")

    order_path = OUT / "flash_furniture_lp_orders_l3m.csv"
    df.to_csv(order_path, index=False)
    print(f"Wrote {order_path}")

    late_pickup = df[df["on_time_pickup"] == 0]
    late_path = OUT / "flash_furniture_lp_late_pickup_l3m.csv"
    late_pickup.to_csv(late_path, index=False)
    print(f"Wrote {late_path} ({len(late_pickup):,} rows)")

    print("Building charts...")
    chart_pickup_by_warehouse(df)
    chart_ifr_by_warehouse(df)
    chart_rfpd_vs_pickup(df)
    chart_otr_pickup_trucks(df)
    chart_weekly_trend(df)
    chart_pickup_to_induction_gap(df)
    print(f"Charts saved to {CHARTS}")

    findings = build_findings(df)
    findings_path = DOCS / "flash_furniture_lp_analysis.md"
    findings_path.write_text(findings)
    print(f"Wrote {findings_path}")


if __name__ == "__main__":
    main()
