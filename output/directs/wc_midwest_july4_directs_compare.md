# West Coast → Midwest: peak directs week vs July 4

Corridor: assigned **West Coast** → customer **Midwest**. Timebase: `msbd_su_week`.
Bucket: classified **`direct`** (candidate + gain ≥ 0.4, not misshipping/ghost/jumbo).

## Important finding

July 4 MSBD week is **high corridor volume** but **not** a directs week on this lane. Midwest induction / classified directs concentrated in **Memorial Day week `2026-05-24`** (~23k directs, ~33k Midwest inductions). By `2026-06-28` (July 4 week) directs fall to ~110–120 ops and Midwest inductions to ~75 — almost all WC→Midwest volume is long-haul via West Coast hubs again.

| MSBD week | Corridor vol | Direct vol | Midwest-induct vol |
|-----------|--------------|------------|--------------------|
| 2026-05-24 (Memorial Day peak) | 36,123 | 22,978 | 33,054 |
| 2026-06-28 (July 4 week) | 21,072 | 122 | 75 |
| 2026-07-05 (July 5 week (high network)) | 30,688 | 201 | 102 |

## Period metrics — classified directs

| Period | Vol | Suppliers | IFR | Del Rel | O2D stated | O2D actual | Gap |
|--------|-----|-----------|-----|---------|------------|------------|-----|
| peak_memorial_2026-05-24 | 22,978 | 3588 | 84.2% | 87.4% | 8.99 | 7.91 | -1.08 |
| july4_week_2026-06-28 | 122 | 77 | 76.2% | 91.8% | 9.68 | 5.82 | -3.86 |
| july5_week_2026-07-05 | 201 | 137 | 80.6% | 87.6% | 10.41 | 5.36 | -5.05 |

## Weekly directs (full window)

| MSBD week | Vol | Suppliers | IFR | Del Rel | O2D stated | O2D actual | Gap |
|-----------|-----|-----------|-----|---------|------------|------------|-----|
| 2026-04-26 | 26 | 24 | 53.8% | 61.5% | 8.31 | 13.96 | +5.65 |
| 2026-05-03 | 248 | 174 | 57.7% | 63.7% | 8.26 | 10.62 | +2.36 |
| 2026-05-10 | 1,489 | 760 | 77.0% | 57.6% | 7.61 | 8.58 | +0.98 |
| 2026-05-17 | 17,414 | 3177 | 91.3% | 92.1% | 9.03 | 7.34 | -1.68 |
| 2026-05-24 ← peak | 22,978 | 3588 | 84.2% | 87.4% | 8.99 | 7.91 | -1.08 |
| 2026-05-31 | 16,659 | 3277 | 88.5% | 81.4% | 7.76 | 7.15 | -0.61 |
| 2026-06-07 | 11,495 | 2741 | 93.0% | 80.2% | 7.82 | 6.99 | -0.83 |
| 2026-06-14 | 482 | 209 | 93.6% | 92.9% | 14.17 | 9.06 | -5.11 |
| 2026-06-21 | 278 | 105 | 88.1% | 92.1% | 12.68 | 7.77 | -4.91 |
| 2026-06-28 ← July 4 | 122 | 77 | 76.2% | 91.8% | 9.68 | 5.82 | -3.86 |
| 2026-07-05 ← July 5 | 201 | 137 | 80.6% | 87.6% | 10.41 | 5.36 | -5.05 |
| 2026-07-12 | 134 | 97 | 83.6% | 90.3% | 8.96 | 4.91 | -4.05 |
| 2026-07-19 | 204 | 148 | 86.8% | 85.8% | 8.33 | 4.60 | -3.72 |
| 2026-07-26 | 350 | 223 | 82.6% | 89.7% | 6.85 | 4.26 | -2.59 |
| 2026-08-02 | 237 | 156 | 87.8% | 84.8% | 6.99 | 4.24 | -2.75 |
| 2026-08-09 | 37 | 24 | 100.0% | 21.6% | 5.97 | 3.22 | -2.75 |

## Peak week supplier scorecard (Memorial Day, ≥30 directs)

Speed = O2D actual (lower better). Gap = actual − stated (negative = beat promise).

| SUID | Supplier | Vol | IFR | Del Rel | O2D stated | O2D actual | Gap | Top hub |
|------|----------|-----|-----|---------|------------|------------|-----|---------|
| 237104 | Devion Furniture | 754 | 44.7% | 82.1% | 10.07 | 9.24 | -0.84 | Romeoville Rsf |
| 316872 | Heze Starfire Trading Co., Ltd CA 91761(5) | 280 | 66.8% | 90.4% | 11.01 | 9.44 | -1.57 | Romeoville Rsf |
| 28971 | NFusion CA 91761 Warehouse CA11 | 270 | 78.9% | 92.6% | 8.21 | 7.39 | -0.82 | Toledo |
| 238512 | CP HomeDecor CA 91761(2) | 212 | 66.5% | 86.8% | 9.00 | 8.34 | -0.67 | Romeoville Rsf |
| 280028 |  CHINO | 199 | 99.5% | 89.4% | 7.71 | 6.94 | -0.77 | Chicago |
| 17066 |   CA2 | 198 | 72.7% | 88.9% | 7.83 | 6.13 | -1.70 | Chicago |
| 322082 | Hangzhou Mengfeisi Home Furnishings Co., CA 92571  | 182 | 98.4% | 97.3% | 8.67 | 6.87 | -1.80 | Toledo |
| 119437 | Aosom LLC CA 92374 | 165 | 99.4% | 84.8% | 7.59 | 6.85 | -0.74 | Chicago |
| 39837 | Kingston CA | 151 | 88.1% | 89.4% | 9.57 | 8.68 | -0.89 | Chicago |
| 272805 | Karat Home Inc (14 Karat) CA 92880 | 149 | 57.7% | 84.6% | 9.96 | 8.64 | -1.32 | Chicago |
| 236498 | Oberon Dist | 143 | 80.4% | 93.0% | 9.68 | 8.55 | -1.13 | Toledo |
| 293214 | CIAO JING INC CA 92879  | 129 | 71.3% | 89.1% | 8.30 | 7.64 | -0.66 | Romeoville Ncpc |
| 292636 | Green Living Group INC CA 91762 | 122 | 86.1% | 84.4% | 8.52 | 7.76 | -0.75 | Toledo |
| 20530 | Million Dollar Baby CA 90660 | 121 | 96.7% | 90.9% | 8.05 | 7.60 | -0.45 | Chicago |
| 297318 | Eazeemats CA 91752 (4) | 120 | 95.0% | 85.8% | 8.15 | 7.85 | -0.30 | Chicago |
| 39283 | Design Imports WA 98390 | 105 | 94.3% | 72.4% | 8.45 | 8.16 | -0.29 | Chicago |
| 8833 | Lifetime Brands Inc.92376 | 104 | 70.2% | 75.0% | 8.12 | 7.86 | -0.26 | Chicago |
| 272846 | Pony Bros-2 | 104 | 37.5% | 91.3% | 8.97 | 8.28 | -0.69 | Chicago |
| 70741 | Westin Outdoor CA | 101 | 28.7% | 26.7% | 7.18 | 8.13 | +0.95 | Chicago |
| 408080 | Hangzhou Chuandiai Cultural Media Co., Ltd. CA 92337 | 99 | 98.0% | 96.0% | 12.90 | 7.74 | -5.16 | Chicago |
| 59119 | Safavieh CA 92518 | 99 | 99.0% | 83.8% | 7.56 | 6.92 | -0.64 | Romeoville Rsf |
| 126078 | Ideal Ventures - GGI International CA | 95 | 100.0% | 94.7% | 8.14 | 7.53 | -0.61 | Chicago |
| 27593 | NFusion CA El Monte | 91 | 86.8% | 92.3% | 8.19 | 7.42 | -0.77 | Chicago |
| 117518 | Winsome House CA 92881 | 88 | 98.9% | 92.0% | 7.92 | 7.34 | -0.58 | Greenwood |
| 348867 | JAFFE MURPHY HOUSE INC CA 91746 (2) | 88 | 100.0% | 100.0% | 9.35 | 7.34 | -2.01 | Toledo |

### Best / worst IFR in peak week (vol≥30)

**Best IFR:** Ideal Ventures - GGI International CA (100%, n=95), JAFFE MURPHY HOUSE INC CA 91746 (2) (100%, n=88), Andes Furniture CA 92870 (100%, n=74), AD ASTRA(Xiamen) E-Commerce Co.,LTD CA 92337 (100%, n=67), P and P Imports LLC CA92614 (100%, n=64), Gibson CA (100%, n=58), Amrapur Overseas Inc. CA (100%, n=52), Natus Sports & Recreation Inc WA 98421 (100%, n=51)

**Worst IFR:** BNF Home CA 91761 (0%, n=47), Curtis International CA (0%, n=36), TarHong CA 91748 (19%, n=53), Sorara Outdoor Living USA, Inc. CA 91746 (19%, n=52), Unique Loom CA 93725 (23%, n=57), NUU GARDEN CORPORATION CA 91730 (26%, n=70), Ledel Lighting INC CA92841 (28%, n=47), Westin Outdoor CA (29%, n=101)

## July 4 week — who still built directs

**77** suppliers, **122** ops total (vs ~23k in peak week).

| SUID | Supplier | July4 vol | IFR | Del Rel | O2D stated | O2D actual | Gap | Peak vol | Peak IFR |
|------|----------|-----------|-----|---------|------------|------------|-----|----------|----------|
| 433182 | NUU GARDEN CORPORATION CA 91730 | 10 | 100.0% | 100.0% | 16.90 | 8.80 | -8.10 | 70 | 25.7% |
| 408999 | Freestyle Outdoor Living Co., Ltd CA 91761 (4) | 7 | 100.0% | 100.0% | 9.86 | 7.14 | -2.71 | — | — |
| 25980 | California Umbrella CA | 6 | 100.0% | 100.0% | 17.83 | 8.67 | -9.17 | 16 | 100.0% |
| 375337 | ZHENGZHOU OUQUN TRADE CO.,LTD CA 92316 | 4 | 100.0% | 100.0% | 9.25 | 5.25 | -4.00 | 3 | 33.3% |
| 182959 | Brightech Inc. CA | 3 | 66.7% | 100.0% | 7.67 | 3.00 | -4.67 | 68 | 83.8% |
| 354420 | GigaCloud Trading, Inc. CA 92337 (5)  | 3 | 33.3% | 100.0% | 8.67 | 4.67 | -4.00 | 5 | 20.0% |
| 148929 | Grove NA, INC. dba Chicology CA | 3 | 100.0% | 100.0% | 12.00 | 5.67 | -6.33 | 11 | 72.7% |
| 295613 | Shenzhen Oumeifeng Fashion Design CA 91752 | 3 | 100.0% | 100.0% | 6.67 | 3.67 | -3.00 | 1 | 0.0% |
| 288856 | Tradeber E-marketing Inc CA 92337 | 3 | 66.7% | 100.0% | 7.00 | 4.67 | -2.33 | 1 | 100.0% |
| 204275 | US_HK LOST HORIZON INTERNATIONAL ELECTRONIC COMMERCE LIMITED CA 92337 | 2 | 0.0% | 50.0% | 7.00 | 7.00 | 0.00 | 3 | 100.0% |
| 249783 | BeatiNeon Irvine Warehouse | 2 | 0.0% | 100.0% | 8.00 | 0.00 | -8.00 | 18 | 88.9% |
| 255050 | JOYIN US CORP. CA 91730 | 2 | 100.0% | 100.0% | 8.00 | 5.00 | -3.00 | 46 | 100.0% |
| 313259 | AM-CA | 2 | 100.0% | 100.0% | 9.50 | 3.50 | -6.00 | 67 | 44.8% |
| 254770 | PRIMESTOK Jersey CA 91730 | 2 | 0.0% | 0.0% | 8.50 | 13.00 | 4.50 | 12 | 83.3% |
| 109665 | Peakhome Furnishings Inc CA 92337 | 2 | 100.0% | 100.0% | 11.00 | 6.00 | -5.00 | 14 | 100.0% |
| 267938 | EVERGREEN DECOR INC CA 91761 | 2 | 100.0% | 100.0% | 8.00 | 5.00 | -3.00 | — | — |
| 449657 | Moe's Home Collection MS 30114 | 2 | 100.0% | 100.0% | 7.00 | 3.00 | -4.00 | — | — |
| 326360 | Freestyle Outdoor Living Co., Ltd GA 31407  | 2 | 50.0% | 100.0% | 18.00 | 5.50 | -12.50 | — | — |
| 313815 | Hangzhou Mengfeisi Home Furnishings Co., Ltd GA 31326 | 2 | 100.0% | 0.0% | 4.00 | 5.00 | 1.00 | — | — |
| 243335 | Dewenwils Network Technology Co., Ltd NJ 08817 | 2 | 100.0% | 100.0% | 7.00 | 3.00 | -4.00 | — | — |

## Files

| File | Contents |
|------|----------|
| `wc_midwest_july4_directs_compare.xlsx` | All tabs |
| `wc_midwest_peak_week_supplier_scorecard.csv` | Memorial Day supplier metrics |
| `wc_midwest_peak_vs_july4_suppliers.csv` | Peak ↔ July 4/5 merge |
| `scripts/run_wc_midwest_july4_compare.py` | Re-run |
