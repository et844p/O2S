# Midwest dest: directs vs SoCal-induct non-directs

Same destination region (**Midwest**), West Coast assigned origin.

| Path | Definition |
|------|------------|
| `midwest_direct` | Classified **direct** bucket (gain ≥ 0.4) |
| `socal_nondirect` | Actual induction at **SoCal** hub (Chino/Rialto/Industry/LA/…; not NorCal), **not** classified direct |

Metrics: IFR, delivery_rel, O2D stated vs actual. Timebase: `msbd_su_week`.

## Period totals

| Period | Path | Vol | Suppliers | IFR | Del Rel | O2D stated | O2D actual | Gap | Mi to cust |
|--------|------|-----|-----------|-----|---------|------------|------------|-----|------------|
| peak_memorial | midwest_direct | 22,978 | 3588 | 84.2% | 87.4% | 8.99 | 7.91 | -1.08 | 68 |
| peak_memorial | socal_nondirect | 209 | 92 | 70.8% | 64.1% | 13.04 | 16.87 | +3.83 | 1971 |
| july4 | midwest_direct | 122 | 77 | 76.2% | 91.8% | 9.68 | 5.82 | -3.86 | 497 |
| july4 | socal_nondirect | 17,258 | 3048 | 87.5% | 87.4% | 8.38 | 7.37 | -1.01 | 1996 |
| july5 | midwest_direct | 201 | 137 | 80.6% | 87.6% | 10.41 | 5.36 | -5.05 | 590 |
| july5 | socal_nondirect | 24,820 | 3665 | 89.3% | 87.8% | 8.06 | 7.01 | -1.06 | 2000 |
| all_weeks_may_aug | midwest_direct | 72,354 | 6386 | 88.1% | 85.3% | 8.53 | 7.43 | -1.10 | 83 |
| all_weeks_may_aug | socal_nondirect | 222,082 | 8794 | 90.8% | 81.6% | 7.73 | 6.99 | -0.74 | 1995 |

## Headline: peak Memorial Day week

- Direct: **22,978** ops — IFR 84.2%, Del 87.4%, O2D 8.99→7.91 (-1.08), ~68 mi after induction
- SoCal nondirect: **209** ops — IFR 70.8%, Del 64.1%, O2D 13.04→16.87 (+3.83), ~1971 mi after induction
- **Delta (direct − SoCal):** IFR +13.3 pp, Del +23.3 pp, O2D actual -8.96d

## Headline: July 4 week (mostly SoCal long-haul)

- Direct (thin): **122** — IFR 76.2%, Del 91.8%, O2D 9.68→5.82
- SoCal nondirect: **17,258** — IFR 87.5%, Del 87.4%, O2D 8.38→7.37 (-1.01)

**Cross-period:** July 4 SoCal nondirect O2D actual **7.37d** vs Memorial Day direct **7.91d** (-0.54d). IFR 87.5% vs direct peak 84.2%.

## Weekly side-by-side

| Week | Direct vol | SoCal vol | Direct IFR | SoCal IFR | Direct Del | SoCal Del | Direct O2D act | SoCal O2D act | O2D Δ |
|------|------------|-----------|------------|-----------|------------|-----------|----------------|---------------|-------|
| 2026-04-26 | 26 | 2830 | 53.8% | 93.4% | 61.5% | 90.8% | 13.96 | 6.76 | 7.20 |
| 2026-05-03 | 248 | 20875 | 57.7% | 90.8% | 63.7% | 87.0% | 10.62 | 6.86 | 3.76 |
| 2026-05-10 | 1489 | 19368 | 77.0% | 93.5% | 57.6% | 85.3% | 8.58 | 6.95 | 1.63 |
| 2026-05-17 | 17414 | 1429 | 91.3% | 97.6% | 92.1% | 94.8% | 7.34 | 7.39 | -0.05 |
| 2026-05-24 ← peak | 22978 | 209 | 84.2% | 70.8% | 87.4% | 64.1% | 7.91 | 16.87 | -8.96 |
| 2026-05-31 | 16659 | 262 | 88.5% | 51.1% | 81.4% | 44.3% | 7.15 | 18.77 | -11.62 |
| 2026-06-07 | 11495 | 4698 | 93.0% | 86.0% | 80.2% | 80.7% | 6.99 | 7.62 | -0.62 |
| 2026-06-14 | 482 | 21924 | 93.6% | 91.7% | 92.9% | 84.7% | 9.06 | 6.92 | 2.14 |
| 2026-06-21 | 278 | 18996 | 88.1% | 91.7% | 92.1% | 81.4% | 7.77 | 7.15 | 0.62 |
| 2026-06-28 ← July4 | 122 | 17258 | 76.2% | 87.5% | 91.8% | 87.4% | 5.82 | 7.37 | -1.55 |
| 2026-07-05 ← July5 | 201 | 24820 | 80.6% | 89.3% | 87.6% | 87.8% | 5.36 | 7.01 | -1.64 |
| 2026-07-12 | 134 | 18541 | 83.6% | 91.5% | 90.3% | 86.7% | 4.91 | 6.90 | -1.99 |
| 2026-07-19 | 204 | 19879 | 86.8% | 91.2% | 85.8% | 85.5% | 4.60 | 6.82 | -2.22 |
| 2026-07-26 | 350 | 26633 | 82.6% | 88.4% | 89.7% | 84.9% | 4.26 | 6.92 | -2.67 |
| 2026-08-02 | 237 | 19494 | 87.8% | 91.9% | 84.8% | 61.0% | 4.24 | 6.53 | -2.29 |
| 2026-08-09 | 37 | 4866 | 100.0% | 99.7% | 21.6% | 2.7% | 3.22 | 8.05 | -4.83 |

## Suppliers with both paths in peak week (≥20 each)

None at this threshold.

## Top July 4 SoCal nondirect suppliers (vs their Memorial Day direct, if any)

| SUID | Supplier | July4 SoCal vol | IFR | Del | O2D stated | O2D actual | Peak direct vol | Peak direct O2D | O2D Δ |
|------|----------|-----------------|-----|-----|------------|------------|-----------------|-----------------|-------|
| 237104 | Devion Furniture | 522 | 94.6% | 96.7% | 9.81 | 8.24 | 754 | 9.24 | -1.00 |
| 238512 | CP HomeDecor CA 91761(2) | 166 | 91.6% | 87.3% | 8.29 | 7.16 | 212 | 8.34 | -1.18 |
| 272805 | Karat Home Inc (14 Karat) CA 92880 | 135 | 100.0% | 94.8% | 9.13 | 7.33 | 149 | 8.64 | -1.31 |
| 39837 | Kingston CA | 130 | 100.0% | 93.8% | 8.99 | 7.81 | 151 | 8.68 | -0.87 |
| 267302 | Karat Home Inc (14 Karat) CA 90249 | 129 | 24.0% | 88.4% | 8.02 | 7.26 | 78 | 8.01 | -0.75 |
| 20530 | Million Dollar Baby CA 90660 | 129 | 98.4% | 80.6% | 7.22 | 7.25 | 121 | 7.60 | -0.35 |
| 119437 | Aosom LLC CA 92374 | 128 | 100.0% | 91.4% | 6.58 | 5.88 | 165 | 6.85 | -0.97 |
| 292636 | Green Living Group INC CA 91762 | 124 | 100.0% | 98.4% | 8.08 | 6.40 | 122 | 7.76 | -1.36 |
| 316872 | Heze Starfire Trading Co., Ltd CA 91761(5) | 111 | 97.3% | 97.3% | 10.73 | 8.16 | 280 | 9.44 | -1.28 |
| 100167 | NingBo KaiMeiChen DianZiShangWu You CA 92571 | 110 | 82.7% | 80.9% | 6.55 | 6.60 | 46 | 7.46 | -0.86 |
| 280028 |  CHINO | 109 | 97.2% | 91.7% | 7.25 | 6.42 | 199 | 6.94 | -0.52 |
| 105765 | Andes Furniture CA 92870 | 106 | 84.9% | 97.2% | 9.10 | 7.82 | 74 | 8.34 | -0.52 |
| 338215 | Bedshe International Co.,LTD CA 91761 | 102 | 68.6% | 81.4% | 7.59 | 7.06 | 72 | 7.35 | -0.29 |
| 149170 | Alphamarts 007-F CA 91789 | 100 | 99.0% | 72.0% | 7.27 | 6.67 | 31 | 7.39 | -0.72 |
| 348867 | JAFFE MURPHY HOUSE INC CA 91746 (2) | 94 | 95.7% | 90.4% | 8.19 | 6.53 | 88 | 7.34 | -0.81 |
| 60106 | Winado CA 91762 | 92 | 67.4% | 71.7% | 6.80 | 6.85 | 65 | 7.23 | -0.38 |
| 117518 | Winsome House CA 92881 | 91 | 68.1% | 86.8% | 7.31 | 6.63 | 88 | 7.34 | -0.71 |
| 288245 | Xiamen MDM CA 91761 | 89 | 92.1% | 89.9% | 9.63 | 8.35 | 74 | 8.41 | -0.06 |
| 79733 | MKAY GROUP CORP | 88 | 100.0% | 96.6% | 9.36 | 7.59 | 81 | 8.19 | -0.59 |
| 497107 | Greenland Home Fashions CA 91710 | 85 | 89.4% | 97.6% | 8.66 | 6.72 | — | — | — |

## Files

| File | Contents |
|------|----------|
| `wc_midwest_direct_vs_socal_compare.xlsx` | All tabs |
| `wc_midwest_direct_vs_socal_weekly_sidebyside.csv` | Weekly metrics |
| `wc_midwest_direct_vs_socal_suppliers_peak.csv` | Peak week supplier paths |
| `scripts/run_wc_midwest_direct_vs_socal.py` | Re-run |
