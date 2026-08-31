#!/usr/bin/env python3
"""Pre vs post weekend-MSBD enablement: speed, IFR, and delivery reliability."""

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
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(_default_creds)

from gbq import query_df

SQL_DIR = ROOT / "sql"
OUT = ROOT / "output" / "weekend_shipping_pre_post"
CHARTS = ROOT / "docs" / "small_parcel" / "weekend_shipping_pre_post_charts"
DOC = ROOT / "docs" / "small_parcel" / "weekend_shipping_pre_post_impact.md"

NAVY = "#1a365d"
ACCENT = "#2e86ab"
ORANGE = "#e67e22"
RED = "#c0392b"
GREEN = "#1e8449"
GRAY = "#7f8c8d"
GOLD = "#d4a017"

POST_CUTOFF = pd.Timestamp("2026-08-17")


def load_sql(name: str) -> str:
    return (SQL_DIR / name).read_text()


def with_cte(select_file: str) -> str:
    return load_sql("weekend_shipping_pre_post_cte.sql") + "\n" + load_sql(select_file)


def prep_orders(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["order_complete_date"] = pd.to_datetime(df["order_complete_date"])
    df["msbd_su"] = pd.to_datetime(df["msbd_su"])
    df["enable_week"] = pd.to_datetime(df["enable_week"])
    df["week_start"] = pd.to_datetime(df["week_start"])
    df["delivery_date"] = pd.to_datetime(df["delivery_date"])
    # pandas dayofweek: Mon=0 … Sun=6. Weekend MSBD = Sat/Sun = 5, 6.
    df["is_weekend_msbd"] = df["msbd_su"].dt.dayofweek.isin([5, 6]).astype(float)
    df["is_weekend_ship"] = df["induction_dow_adj"].isin([1, 7]).astype(float)
    df["is_sat_ship"] = (df["induction_dow_adj"] == 7).astype(float)
    df["is_sun_ship"] = (df["induction_dow_adj"] == 1).astype(float)
    df["ifr"] = pd.to_numeric(df["inducted_on_time_or_early"], errors="coerce")
    df["o2d_stated"] = pd.to_numeric(df["o2d_stated"], errors="coerce")
    df["o2d_actual"] = pd.to_numeric(df["o2d_actual"], errors="coerce")
    df["o2s_actual"] = pd.to_numeric(df["o2s_actual"], errors="coerce")
    df["fast_badge"] = pd.to_numeric(df["o2d_stated_5"], errors="coerce")
    df["delivery_rel"] = pd.to_numeric(df["delivery_rel"], errors="coerce")
    return df[df["period"].notna() & df["order_bucket"].notna()].copy()


def summarize(g: pd.DataFrame) -> pd.Series:
    delivered = g["delivery_date"].notna()
    vol = int(g["ops"].nunique()) if "ops" in g.columns else int(len(g))
    n_suppliers = int(g["supplier_id"].nunique()) if "supplier_id" in g.columns else 1
    ifr = float(g["ifr"].mean()) if vol else np.nan
    return pd.Series(
        {
            "n_suppliers": n_suppliers,
            "vol": vol,
            "weekend_msbd": float(g["is_weekend_msbd"].mean()) if vol else np.nan,
            "weekend_ship": float(g["is_weekend_ship"].mean()) if vol else np.nan,
            "sat_ship": float(g["is_sat_ship"].mean()) if vol else np.nan,
            "sun_ship": float(g["is_sun_ship"].mean()) if vol else np.nan,
            "ifr": ifr,
            "late_orders": vol * (1 - ifr) if vol and pd.notna(ifr) else np.nan,
            "o2d_stated": float(g["o2d_stated"].mean()) if vol else np.nan,
            "o2d_actual": float(g["o2d_actual"].mean()) if vol else np.nan,
            "o2s_actual": float(g["o2s_actual"].mean()) if vol else np.nan,
            "fast_badge": float(g["fast_badge"].mean()) if vol else np.nan,
            "del_rel": float(g.loc[delivered, "delivery_rel"].mean()) if delivered.any() else np.nan,
            "delivered_vol": int(g.loc[delivered, "ops"].nunique()),
        }
    )


def pct(x: float | None, digits: int = 1) -> str:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "—"
    return f"{x * 100:.{digits}f}%"


def num(x: float | None, digits: int = 2) -> str:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "—"
    return f"{x:.{digits}f}"


def pp(post: float, pre: float, digits: int = 1) -> str:
    if any(pd.isna(v) for v in (post, pre)):
        return "—"
    d = (post - pre) * 100
    sign = "+" if d >= 0 else ""
    return f"{sign}{d:.{digits}f} pp"


def days(post: float, pre: float, digits: int = 2) -> str:
    if any(pd.isna(v) for v in (post, pre)):
        return "—"
    d = post - pre
    sign = "+" if d >= 0 else ""
    return f"{sign}{d:.{digits}f}d"


def slice_pair(rollup: pd.DataFrame, wave: str, bucket: str) -> tuple[pd.Series, pd.Series]:
    sub = rollup[(rollup["wave"] == wave) & (rollup["order_bucket"] == bucket)]
    pre = sub[sub["period"] == "pre"].iloc[0]
    post = sub[sub["period"] == "post"].iloc[0]
    return pre, post


def metric_table_md(pre: pd.Series, post: pd.Series) -> str:
    rows = [
        ("Volume (distinct ops)", f"{int(pre['vol']):,}", f"{int(post['vol']):,}", "—"),
        ("Weekend MSBD share", pct(pre["weekend_msbd"]), pct(post["weekend_msbd"]), pp(post["weekend_msbd"], pre["weekend_msbd"])),
        ("Weekend ship (Sat+Sun adj)", pct(pre["weekend_ship"]), pct(post["weekend_ship"]), pp(post["weekend_ship"], pre["weekend_ship"])),
        ("Saturday induction", pct(pre["sat_ship"]), pct(post["sat_ship"]), pp(post["sat_ship"], pre["sat_ship"])),
        ("Sunday induction", pct(pre["sun_ship"]), pct(post["sun_ship"]), pp(post["sun_ship"], pre["sun_ship"])),
        ("IFR (on-time vs supplier MSBD)", pct(pre["ifr"]), pct(post["ifr"]), pp(post["ifr"], pre["ifr"])),
        ("Late orders", f"{pre['late_orders']:,.0f}", f"{post['late_orders']:,.0f}", f"{post['late_orders'] - pre['late_orders']:+,.0f}"),
        ("Stated O2D (days)", num(pre["o2d_stated"]), num(post["o2d_stated"]), days(post["o2d_stated"], pre["o2d_stated"])),
        ("Actual O2D (days)", num(pre["o2d_actual"]), num(post["o2d_actual"]), days(post["o2d_actual"], pre["o2d_actual"])),
        ("Actual O2S (days)", num(pre["o2s_actual"]), num(post["o2s_actual"]), days(post["o2s_actual"], pre["o2s_actual"])),
        ("Fast badge (stated O2D ≤ 5)", pct(pre["fast_badge"]), pct(post["fast_badge"]), pp(post["fast_badge"], pre["fast_badge"])),
        ("Delivery reliability", pct(pre["del_rel"]), pct(post["del_rel"]), pp(post["del_rel"], pre["del_rel"])),
    ]
    lines = [
        "| Metric | Pre | Post | Change |",
        "| --- | ---: | ---: | ---: |",
    ]
    for label, a, b, c in rows:
        lines.append(f"| {label} | {a} | {b} | {c} |")
    return "\n".join(lines)


def chart_grouped_bars(wave1: pd.DataFrame) -> None:
    pre, post = slice_pair(wave1, "wave1_jun_jul", "fri_sat")
    labels = ["Weekend\nMSBD", "Weekend\nship", "IFR", "Fast\nbadge", "Delivery\nrel"]
    keys = ["weekend_msbd", "weekend_ship", "ifr", "fast_badge", "del_rel"]
    pre_v = [pre[k] * 100 for k in keys]
    post_v = [post[k] * 100 for k in keys]

    fig, ax = plt.subplots(figsize=(10, 5.5))
    x = np.arange(len(labels))
    w = 0.36
    ax.bar(x - w / 2, pre_v, w, label="Pre (6w before enable)", color=GRAY)
    ax.bar(x + w / 2, post_v, w, label="Post (enable week through 8/16)", color=ACCENT)
    for i, (a, b) in enumerate(zip(pre_v, post_v)):
        ax.text(i - w / 2, a + 1.2, f"{a:.1f}%", ha="center", va="bottom", fontsize=8)
        ax.text(i + w / 2, b + 1.2, f"{b:.1f}%", ha="center", va="bottom", fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 110)
    ax.set_ylabel("Percent")
    ax.set_title(
        "Wave 1 (12 suppliers, June 21 / July 5 enablement)\n"
        "Friday–Saturday placed orders — reliability vs promised speed mix"
    )
    ax.legend(frameon=False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(CHARTS / "01_wave1_fri_sat_rates.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5))
    speed_labels = ["Stated O2D", "Actual O2D", "Actual O2S"]
    speed_keys = ["o2d_stated", "o2d_actual", "o2s_actual"]
    pre_s = [pre[k] for k in speed_keys]
    post_s = [post[k] for k in speed_keys]
    x = np.arange(len(speed_labels))
    ax.bar(x - w / 2, pre_s, w, label="Pre", color=GRAY)
    ax.bar(x + w / 2, post_s, w, label="Post", color=GREEN)
    for i, (a, b) in enumerate(zip(pre_s, post_s)):
        ax.text(i - w / 2, a + 0.05, f"{a:.2f}", ha="center", fontsize=8)
        ax.text(i + w / 2, b + 0.05, f"{b:.2f}", ha="center", fontsize=8)
        ax.annotate(
            f"{b - a:+.2f}d",
            xy=(i + w / 2, b),
            xytext=(18, 8),
            textcoords="offset points",
            fontsize=8,
            color=GREEN if b < a else RED,
        )
    ax.set_xticks(x)
    ax.set_xticklabels(speed_labels)
    ax.set_ylabel("Days")
    ax.set_title("Wave 1 Fri/Sat orders — speed gain (lower is faster)")
    ax.legend(frameon=False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(CHARTS / "02_wave1_fri_sat_speed.png", dpi=150)
    plt.close(fig)


def chart_weekday_vs_weekend(rollup: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    for ax, metric, title in (
        (axes[0], "ifr", "IFR"),
        (axes[1], "del_rel", "Delivery reliability"),
    ):
        x = np.arange(2)
        w = 0.35
        for i, bucket, color in ((0, "fri_sat", ACCENT), (1, "weekday", NAVY)):
            pre, post = slice_pair(rollup, "wave1_jun_jul", bucket)
            vals = [pre[metric] * 100, post[metric] * 100]
            offset = -w / 2 if bucket == "fri_sat" else w / 2
            label = "Fri/Sat placed" if bucket == "fri_sat" else "Mon–Thu placed"
            ax.plot(
                x,
                vals,
                marker="o",
                linewidth=2.4,
                color=color,
                label=label,
            )
            for xi, v in zip(x, vals):
                ax.text(xi, v + 0.8, f"{v:.1f}%", ha="center", fontsize=8, color=color)
        ax.set_xticks(x)
        ax.set_xticklabels(["Pre", "Post"])
        ax.set_title(title)
        ax.set_ylim(70, 100)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.legend(frameon=False, loc="lower left")
    fig.suptitle(
        "Wave 1 — reliability hit is isolated to weekend-placed orders\n"
        "Same 12 enabled warehouses; weekday IFR/del-rel held or improved",
        y=1.03,
    )
    fig.tight_layout()
    fig.savefig(CHARTS / "03_wave1_weekday_vs_weekend_reliability.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def chart_sat_sun(rollup: pd.DataFrame) -> None:
    pre, post = slice_pair(rollup, "wave1_jun_jul", "fri_sat")
    fig, ax = plt.subplots(figsize=(8, 5))
    x = np.arange(2)
    w = 0.35
    sat = [pre["sat_ship"] * 100, post["sat_ship"] * 100]
    sun = [pre["sun_ship"] * 100, post["sun_ship"] * 100]
    ax.bar(x - w / 2, sat, w, label="Saturday induction", color=ORANGE)
    ax.bar(x + w / 2, sun, w, label="Sunday induction", color=NAVY)
    for i, (a, b) in enumerate(zip(sat, sun)):
        ax.text(i - w / 2, a + 1, f"{a:.1f}%", ha="center", fontsize=8)
        ax.text(i + w / 2, b + 1, f"{b:.1f}%", ha="center", fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels(["Pre", "Post"])
    ax.set_ylabel("% of Fri/Sat placed orders")
    ax.set_ylim(0, 85)
    ax.set_title(
        "Wave 1 Fri/Sat orders — still almost no Saturday induction\n"
        "Sunday ship held (~65%); Saturday MSBD is what IFR is missing"
    )
    ax.legend(frameon=False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(CHARTS / "04_wave1_sat_vs_sun_induction.png", dpi=150)
    plt.close(fig)


def chart_supplier_lollipop(supplier: pd.DataFrame) -> None:
    sub = supplier[
        (supplier["wave"] == "wave1_jun_jul")
        & (supplier["order_bucket"] == "fri_sat")
    ].copy()
    pre = sub[sub["period"] == "pre"].set_index("supplier_id")
    post = sub[sub["period"] == "post"].set_index("supplier_id")
    names = post["su_name"].to_dict()
    rows = []
    for sid in post.index:
        if sid not in pre.index:
            continue
        rows.append(
            {
                "name": names[sid],
                "ifr_delta": (post.loc[sid, "ifr"] - pre.loc[sid, "ifr"]) * 100,
                "o2d_act_delta": post.loc[sid, "o2d_actual"] - pre.loc[sid, "o2d_actual"],
                "del_delta": (post.loc[sid, "del_rel"] - pre.loc[sid, "del_rel"]) * 100,
                "post_vol": post.loc[sid, "vol"],
            }
        )
    plot = pd.DataFrame(rows).sort_values("ifr_delta")
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = [RED if v < 0 else GREEN for v in plot["ifr_delta"]]
    ax.hlines(plot["name"], 0, plot["ifr_delta"], color=colors, linewidth=2)
    ax.scatter(plot["ifr_delta"], plot["name"], color=colors, zorder=3)
    ax.axvline(0, color="#333", linewidth=0.8)
    ax.set_xlabel("IFR change (pp), Fri/Sat placed")
    ax.set_title("Wave 1 warehouses — IFR change on weekend-placed orders")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(CHARTS / "05_wave1_supplier_ifr_change.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = [GREEN if v < 0 else RED for v in plot["o2d_act_delta"]]
    plot2 = plot.sort_values("o2d_act_delta")
    ax.hlines(plot2["name"], 0, plot2["o2d_act_delta"], color=colors, linewidth=2)
    ax.scatter(plot2["o2d_act_delta"], plot2["name"], color=colors, zorder=3)
    ax.axvline(0, color="#333", linewidth=0.8)
    ax.set_xlabel("Actual O2D change (days); negative = faster")
    ax.set_title("Wave 1 warehouses — actual speed change on weekend-placed orders")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(CHARTS / "06_wave1_supplier_o2d_actual_change.png", dpi=150)
    plt.close(fig)


def chart_weekly(orders: pd.DataFrame) -> None:
    w1 = orders[(orders["wave"] == "wave1_jun_jul") & (orders["order_bucket"] == "fri_sat")]
    weekly = (
        w1.groupby("weeks_from_enable", dropna=True)
        .apply(summarize)
        .reset_index()
    )
    weekly = weekly[weekly["vol"] >= 50]
    fig, axes = plt.subplots(2, 1, figsize=(11, 8), sharex=True)
    axes[0].plot(weekly["weeks_from_enable"], weekly["ifr"] * 100, marker="o", color=RED, label="IFR")
    axes[0].plot(
        weekly["weeks_from_enable"], weekly["del_rel"] * 100, marker="s", color=NAVY, label="Delivery rel"
    )
    axes[0].axvline(0, color=ORANGE, linestyle="--", label="Enable week")
    axes[0].set_ylabel("Percent")
    axes[0].set_ylim(50, 100)
    axes[0].legend(frameon=False)
    axes[0].set_title("Wave 1 Fri/Sat — IFR and delivery reliability by weeks from enablement")
    axes[1].plot(
        weekly["weeks_from_enable"], weekly["o2d_stated"], marker="o", color=ACCENT, label="Stated O2D"
    )
    axes[1].plot(
        weekly["weeks_from_enable"], weekly["o2d_actual"], marker="s", color=GREEN, label="Actual O2D"
    )
    axes[1].axvline(0, color=ORANGE, linestyle="--")
    axes[1].set_ylabel("Days")
    axes[1].set_xlabel("Weeks from supplier enablement week (0 = first weekend-MSBD week)")
    axes[1].legend(frameon=False)
    axes[1].set_title("Wave 1 Fri/Sat — stated vs actual O2D")
    for ax in axes:
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(CHARTS / "07_wave1_weekly_relative.png", dpi=150)
    plt.close(fig)


def chart_wave2(rollup: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    w = 0.35
    for ax, bucket, title in (
        (axes[0], "fri_sat", "Fri/Sat placed"),
        (axes[1], "weekday", "Mon–Thu placed"),
    ):
        pre, post = slice_pair(rollup, "wave2_aug", bucket)
        labels = ["IFR", "Del rel", "Fast badge"]
        keys = ["ifr", "del_rel", "fast_badge"]
        x = np.arange(len(labels))
        ax.bar(x - w / 2, [pre[k] * 100 for k in keys], w, color=GRAY, label="Pre")
        ax.bar(x + w / 2, [post[k] * 100 for k in keys], w, color=GOLD, label="Post (early)")
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.set_ylim(0, 110)
        ax.set_title(title)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.legend(frameon=False)
    fig.suptitle("Wave 2 (August 2 Q3 sprint, ~70 suppliers) — early 2-week post window")
    fig.tight_layout()
    fig.savefig(CHARTS / "08_wave2_early_read.png", dpi=150)
    plt.close(fig)


def supplier_md(supplier: pd.DataFrame, wave: str) -> str:
    sub = supplier[(supplier["wave"] == wave) & (supplier["order_bucket"] == "fri_sat")].copy()
    pre = sub[sub["period"] == "pre"].set_index("supplier_id")
    post = sub[sub["period"] == "post"].set_index("supplier_id")
    lines = [
        "| Warehouse | Enable week | Pre vol | Post vol | IFR pre → post | Del rel pre → post | Stated O2D | Actual O2D | Sat ship post | Sun ship post |",
        "| --- | --- | ---: | ---: | --- | --- | --- | --- | ---: | ---: |",
    ]
    for sid in post.sort_values("vol", ascending=False).index:
        if sid not in pre.index:
            continue
        p, t = pre.loc[sid], post.loc[sid]
        enable = pd.to_datetime(t["enable_week"]).date()
        lines.append(
            "| {name} | {en} | {pv:,} | {tv:,} | {ip} → {it} ({idlt}) | {dp} → {dt} ({dd}) | "
            "{sp} → {st} ({sd}) | {ap} → {at} ({ad}) | {sat} | {sun} |".format(
                name=t["su_name"],
                en=enable,
                pv=int(p["vol"]),
                tv=int(t["vol"]),
                ip=pct(p["ifr"]),
                it=pct(t["ifr"]),
                idlt=pp(t["ifr"], p["ifr"]),
                dp=pct(p["del_rel"]),
                dt=pct(t["del_rel"]),
                dd=pp(t["del_rel"], p["del_rel"]),
                sp=num(p["o2d_stated"]),
                st=num(t["o2d_stated"]),
                sd=days(t["o2d_stated"], p["o2d_stated"]),
                ap=num(p["o2d_actual"]),
                at=num(t["o2d_actual"]),
                ad=days(t["o2d_actual"], p["o2d_actual"]),
                sat=pct(t["sat_ship"]),
                sun=pct(t["sun_ship"]),
            )
        )
    return "\n".join(lines)


def write_report(
    roster: pd.DataFrame,
    rollup: pd.DataFrame,
    supplier: pd.DataFrame,
    control: pd.DataFrame,
) -> None:
    w1_fs_pre, w1_fs_post = slice_pair(rollup, "wave1_jun_jul", "fri_sat")
    w1_wd_pre, w1_wd_post = slice_pair(rollup, "wave1_jun_jul", "weekday")
    w2_fs_pre, w2_fs_post = slice_pair(rollup, "wave2_aug", "fri_sat")

    ctrl = control.copy()
    ctrl_fs = ctrl[ctrl["order_bucket"] == "fri_sat"].set_index("period")

    n_w1 = int(roster[roster["wave"] == "wave1_jun_jul"]["supplier_id"].nunique())
    n_w2 = int(roster[roster["wave"] == "wave2_aug"]["supplier_id"].nunique())

    md = f"""# Weekend shipping enablement — pre vs post impact

Generated: 2026-08-31

June–July Wave 1 enabled **weekend Must Ship By Date** for 24-hour dropship warehouses that were already inducting Fri/Sat orders over the weekend. This rerun measures whether those warehouses are performing, the speed gain, and delivery reliability on **Friday–Saturday placed orders**.

An August 2 Q3 sprint wave is included as an early read (short post window).

## Bottom line

Wave 1 (12 warehouses; nuLOOM NJ on **2026-06-21**, then Safavieh / Aosom / GigaCloud / SLM / WINADO / nuLOOM CA on **2026-07-05 / 07-12**):

- **Setting took:** Fri/Sat weekend MSBD share went from {pct(w1_fs_pre['weekend_msbd'])} to {pct(w1_fs_post['weekend_msbd'])}.
- **Speed improved, but less than the promise:** stated O2D {num(w1_fs_pre['o2d_stated'])} → {num(w1_fs_post['o2d_stated'])} days ({days(w1_fs_post['o2d_stated'], w1_fs_pre['o2d_stated'])}); actual O2D {num(w1_fs_pre['o2d_actual'])} → {num(w1_fs_post['o2d_actual'])} ({days(w1_fs_post['o2d_actual'], w1_fs_pre['o2d_actual'])}). Fast badge {pct(w1_fs_pre['fast_badge'])} → {pct(w1_fs_post['fast_badge'])} ({pp(w1_fs_post['fast_badge'], w1_fs_pre['fast_badge'])}).
- **Reliability got worse on weekend-placed orders:** IFR {pct(w1_fs_pre['ifr'])} → {pct(w1_fs_post['ifr'])} ({pp(w1_fs_post['ifr'], w1_fs_pre['ifr'])}); delivery reliability {pct(w1_fs_pre['del_rel'])} → {pct(w1_fs_post['del_rel'])} ({pp(w1_fs_post['del_rel'], w1_fs_pre['del_rel'])}).
- **Operations did not move to Saturday:** weekend induction held ({pct(w1_fs_pre['weekend_ship'])} → {pct(w1_fs_post['weekend_ship'])}), but it is almost all **Sunday** ({pct(w1_fs_post['sun_ship'])}) vs **Saturday** ({pct(w1_fs_post['sat_ship'])}). Friday orders with a Saturday MSBD that induct Sunday miss IFR.
- **Weekdays for the same warehouses improved:** IFR {pct(w1_wd_pre['ifr'])} → {pct(w1_wd_post['ifr'])}; delivery reliability {pct(w1_wd_pre['del_rel'])} → {pct(w1_wd_post['del_rel'])}. The miss is weekend-order specific.

Wave 2 ({n_w2} warehouses, enable week **2026-08-02**; post is only ~2 weeks through 8/16) shows the same pattern: promised speed and fast-badge up, IFR and delivery reliability down on Fri/Sat orders.

## Wave 1 — Friday/Saturday placed orders

{n_w1} 24-hour DS warehouses. Pre = 6 weeks before each warehouse’s first weekend-MSBD week. Post = enable week through 2026-08-16 (14-day delivery lag).

{metric_table_md(w1_fs_pre, w1_fs_post)}

### Same warehouses, Monday–Thursday placed (within-supplier control)

{metric_table_md(w1_wd_pre, w1_wd_post)}

## Wave 1 warehouse detail (Fri/Sat)

{supplier_md(supplier, "wave1_jun_jul")}

WINADO’s post weekend-MSBD share did not stay high after the first week — treat as not sustained.

## Wave 2 early read (August 2 Q3 sprint)

Post window is 2026-08-02 through 2026-08-16 only. Directionally the same as Wave 1 on Fri/Sat orders: weekend MSBD {pct(w2_fs_pre['weekend_msbd'])} → {pct(w2_fs_post['weekend_msbd'])}; IFR {pct(w2_fs_pre['ifr'])} → {pct(w2_fs_post['ifr'])}; delivery reliability {pct(w2_fs_pre['del_rel'])} → {pct(w2_fs_post['del_rel'])}; stated O2D {num(w2_fs_pre['o2d_stated'])} → {num(w2_fs_post['o2d_stated'])}; actual O2D {num(w2_fs_pre['o2d_actual'])} → {num(w2_fs_post['o2d_actual'])}. Saturday induction is higher than Wave 1 ({pct(w2_fs_post['sat_ship'])}) but still minority vs Sunday ({pct(w2_fs_post['sun_ship'])}).

{metric_table_md(w2_fs_pre, w2_fs_post)}

Full Wave 2 warehouse file: `output/weekend_shipping_pre_post/supplier_pre_post.csv`.

## 24hr control (not enabled)

24-hour DS suppliers with **no** Fri/Sat weekend MSBD on/after 2026-06-21. Calendar windows: pre 5/03–6/21, post 7/05–8/16.

"""

    if "pre" in ctrl_fs.index and "post" in ctrl_fs.index:
        cpre, cpost = ctrl_fs.loc["pre"], ctrl_fs.loc["post"]
        md += (
            f"Fri/Sat control: IFR {pct(cpre['ifr'])} → {pct(cpost['ifr'])} "
            f"({pp(cpost['ifr'], cpre['ifr'])}); delivery reliability "
            f"{pct(cpre['del_rel'])} → {pct(cpost['del_rel'])} "
            f"({pp(cpost['del_rel'], cpre['del_rel'])}); actual O2D "
            f"{num(cpre['o2d_actual'])} → {num(cpost['o2d_actual'])} "
            f"({days(cpost['o2d_actual'], cpre['o2d_actual'])}). "
            "Control reliability did not drop the way enabled Fri/Sat orders did.\n"
        )

    md += """
## What this means

1. **Enablement worked in the promise:** weekend MSBD is on; stated O2D and 5-day badging improved on Fri/Sat orders.
2. **Warehouses are not failing to ship weekends** — they still induct ~65% of Fri/Sat orders on Sunday. They are failing **Saturday** induction, which is what the new MSBD requires for Friday orders.
3. **Do not read IFR as “they stopped trying.”** Tighter Saturday MSBD converted prior Sunday-early (vs Monday MSBD) into Sunday-late (vs Saturday MSBD).
4. **Delivery reliability followed IFR down** on weekend-placed orders only. Weekday del-rel for the same buildings is stable/up.
5. **Next lever:** Saturday FedEx pickup / Saturday induction at Wave 1 buildings (especially Safavieh IN/TX/CA and NFusion El Monte) before adding more weekend-MSBD enablement. nuLOOM CA is the closest to a Saturday-ship success case.

## Methodology

| Item | Rule |
| --- | --- |
| Table | `` `wf-gcp-us-ae-global-tnd-prod.speed_and_reliability.HVE_perf_Monitoring` `` |
| Fulfillment | `fulfillment_type = 'DS'`, `sp_lt = 24` |
| Weekend-placed cohort | Friday + Saturday orders: `order_dow IN (6, 7)` |
| Weekday control | Monday–Thursday: `order_dow IN (2, 3, 4, 5)` |
| Day-of-week | **Sunday = 1 … Saturday = 7** for `order_dow` and `induction_dow_adj` (verified vs calendar dates) |
| Weekend ship | `induction_dow_adj IN (1, 7)` — not `inducted_over_weekend` (that flag undercounts Sunday scans) |
| Weekend MSBD | `EXTRACT(DAYOFWEEK FROM msbd_su) IN (1, 7)` |
| Enabled | First week on/after 2026-06-21 with ≥20 Fri/Sat ops and ≥10% weekend MSBD; prior 6-week weekend-MSBD average < 5% |
| Pre / post | Supplier-specific: 6 weeks before enable week vs enable week through 2026-08-16 |
| Volume | `COUNT(DISTINCT ops)` |
| IFR | `AVG(inducted_on_time_or_early)` |
| Delivery reliability | `AVG(delivery_rel)` among rows with `delivery_date IS NOT NULL` |
| Speed | `AVG(o2d_stated)`, `AVG(o2d_actual)`, `AVG(o2s_actual)`; fast badge = `o2d_stated_5` |

The July 2026 candidate finder (`sql/weekend_shipping_supplier_analysis.sql`) treated `order_dow IN (5, 6)` as Fri/Sat. Empirically that is **Thursday + Friday**. This impact rerun uses the corrected Friday + Saturday filter.

## Charts

![Wave 1 rates](weekend_shipping_pre_post_charts/01_wave1_fri_sat_rates.png)

![Wave 1 speed](weekend_shipping_pre_post_charts/02_wave1_fri_sat_speed.png)

![Weekday vs weekend reliability](weekend_shipping_pre_post_charts/03_wave1_weekday_vs_weekend_reliability.png)

![Sat vs Sun induction](weekend_shipping_pre_post_charts/04_wave1_sat_vs_sun_induction.png)

![Warehouse IFR change](weekend_shipping_pre_post_charts/05_wave1_supplier_ifr_change.png)

![Warehouse actual O2D change](weekend_shipping_pre_post_charts/06_wave1_supplier_o2d_actual_change.png)

![Weekly relative](weekend_shipping_pre_post_charts/07_wave1_weekly_relative.png)

![Wave 2 early](weekend_shipping_pre_post_charts/08_wave2_early_read.png)
"""
    DOC.write_text(md)


def fetch() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    cache = Path("/tmp/weekend_shipping_pre_post_cache.pkl")
    if cache.exists():
        print(f"Loading cached extracts from {cache}")
        return pd.read_pickle(cache)
    print("Querying enabled roster…")
    roster = query_df(with_cte("weekend_shipping_pre_post_roster.sql"))
    print("Querying enabled orders…")
    orders = prep_orders(query_df(with_cte("weekend_shipping_pre_post_orders.sql")))
    print("Querying 24hr control…")
    control = query_df(load_sql("weekend_shipping_pre_post_control.sql"))
    pd.to_pickle((roster, orders, control), cache)
    return roster, orders, control


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    CHARTS.mkdir(parents=True, exist_ok=True)

    roster, orders, control = fetch()

    rollup = (
        orders.groupby(["wave", "order_bucket", "period"], dropna=True)
        .apply(summarize)
        .reset_index()
    )
    supplier = (
        orders.groupby(
            ["wave", "supplier_id", "su_name", "parent_su_name", "sto", "srm", "enable_week", "order_bucket", "period"],
            dropna=True,
        )
        .apply(summarize)
        .reset_index()
    )
    weekly = (
        orders.groupby(["wave", "order_bucket", "weeks_from_enable", "week_start"], dropna=True)
        .apply(summarize)
        .reset_index()
    )

    roster.to_csv(OUT / "enabled_roster.csv", index=False)
    rollup.to_csv(OUT / "cohort_rollup.csv", index=False)
    supplier.to_csv(OUT / "supplier_pre_post.csv", index=False)
    weekly.to_csv(OUT / "weekly_relative.csv", index=False)
    control.to_csv(OUT / "control_rollup.csv", index=False)

    print("Building charts…")
    chart_grouped_bars(rollup)
    chart_weekday_vs_weekend(rollup)
    chart_sat_sun(rollup)
    chart_supplier_lollipop(supplier)
    chart_weekly(orders)
    chart_wave2(rollup)

    write_report(roster, rollup, supplier, control)

    print(f"Roster: {len(roster)} enabled warehouses")
    print(roster.groupby("wave").size().to_string())
    print(f"Wrote CSVs to {OUT}")
    print(f"Wrote charts to {CHARTS}")
    print(f"Wrote {DOC}")


if __name__ == "__main__":
    main()
