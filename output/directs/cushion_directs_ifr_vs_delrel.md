# Directs → IFR → cushions vs det delivery reliability

## Hypothesis

Direct volume disproportionately tanks **IFR**, triggering **cushions**, even though **deterministic delivery reliability** is still hit — including when subtracting one day for the cushion (`delivery_date <= det_delivery_date - 1`).

## Metric definitions

| Metric | Definition |
|--------|------------|
| IFR | `inducted_on_time_or_early` |
| delivery_rel | Existing HVE delivery reliability |
| **det_on_time** | `delivery_date <= det_delivery_date` (corrected reliability) |
| **det_hits_minus_1** | `delivery_date <= det_delivery_date - 1` (still hits if 1 cushion day removed from det end) |
| stored `det_del_rel` | Your column: `EndDate <= delivery_date` (flips early/late vs typical on-time) |
| stored `det_one_more_day_del_early` | Your column: `EndDate - 1 <= delivery_date` |

Det date coverage: **97.1%** of ops. Primary prove metrics below use **det_on_time** / **det_hits_minus_1**.

## Verdict

On **cushioned** volume: directs are **6.6%** of vol but **7.7%** of IFR-late orders (IFR **70.0%** vs local **75.1%**).

Same direct arm delivery_rel **83.1%**, det_on_time **88.4%**, det_hits_minus_1 **67.1%** (local: del 83.6%, det 82.7%, det−1 64.2%).

Cushioned suppliers with IFR&lt;80%, delivery_rel≥85%, direct_share≥10%: **109**. With det_on_time≥70%: **272**. With det_hits_minus_1≥50%: **228**.

## 1) Cushioned vs not

| Segment | Vol | IFR | Del rel | Det on-time | Det hits end−1 | IFR−Del pp | % direct |
|---------|-----|-----|---------|-------------|----------------|------------|----------|
| cushion>=1 | 1,001,449 | 74.1% | 83.0% | 82.9% | 63.9% | -8.9 | 6.6% |
| no cushion | 6,675,993 | 91.4% | 85.9% | 74.1% | 33.2% | +5.6 | 7.6% |

## 2) Within cushioned — by path

| Path | % vol | IFR | Del rel | Det on-time | Det end−1 | % IFR lates | % del misses | % det misses |
|------|-------|-----|---------|-------------|-----------|-------------|--------------|--------------|
| local | 86.5% | 75.1% | 83.6% | 82.7% | 64.2% | 83.1% | 83.2% | 87.3% |
| other | 6.9% | 65.5% | 74.9% | 80.2% | 57.4% | 9.2% | 10.2% | 8.1% |
| direct | 6.6% | 70.0% | 83.1% | 88.4% | 67.1% | 7.7% | 6.6% | 4.6% |

## 3) Network-wide by path (context)

| Path | % vol | IFR | Del rel | Det on-time | Det end−1 | % IFR lates |
|------|-------|-----|---------|-------------|-----------|-------------|
| local | 86.4% | 89.5% | 86.1% | 74.8% | 36.5% | 84.1% |
| direct | 7.4% | 88.5% | 85.0% | 80.8% | 41.9% | 7.9% |
| other | 6.1% | 85.9% | 76.8% | 73.8% | 41.5% | 8.0% |

## 4) Example cushioned directors — IFR low, delivery still high

| SUID | Supplier | Vol | Direct % | IFR | Del rel | Det on-time | Det end−1 | Direct IFR | Local IFR |
|------|----------|-----|----------|-----|---------|-------------|-----------|------------|-----------|
| 79383 | ColourTree CA | 3,437 | 21% | 59.4% | 91.2% | 75.8% | 52.5% | 43.1% | 65.0% |
| 295509 | Freestyle Outdoor Living Co., Ltd GA 31405(2) | 2,258 | 12% | 68.7% | 85.7% | 78.8% | 65.9% | 68.3% | 69.8% |
| 32159 | Classic Home CA | 1,429 | 17% | 79.8% | 86.3% | 87.2% | 71.1% | 75.5% | 81.7% |
| 19463 | Conair, Inc AZ 85307 | 1,264 | 16% | 77.3% | 87.5% | 97.2% | 89.1% | 89.5% | 73.9% |
| 93793 | Farfarview CA 92337 | 1,163 | 14% | 77.6% | 85.4% | 82.1% | 60.2% | 69.3% | 80.5% |
| 460617 | FUJIAN VIITION INTERNET DEVELOPMENT CO LTD CA 92571 | 1,060 | 11% | 63.1% | 85.9% | 90.8% | 70.0% | 74.1% | 61.4% |
| 146557 | A298 CA01 | 874 | 23% | 73.3% | 88.8% | 86.7% | 56.0% | 48.8% | 71.4% |
| 316345 | Sinda Furniture CA 91761 | 854 | 15% | 73.2% | 87.2% | 72.5% | 50.7% | 77.3% | 72.8% |
| 94641 | Shenzhenshi xiangdeyizhang keji youxiang CA 92337 | 845 | 15% | 78.8% | 87.5% | 82.9% | 59.3% | 70.4% | 79.8% |
| 341753 | Zhejiang On Leap Furnishing Co.,Ltd. GA 31322 | 761 | 10% | 70.0% | 86.6% | 72.1% | 40.6% | 58.4% | 74.7% |
| 77785 | LTmate Global LLC CA 91761 | 734 | 12% | 54.8% | 93.5% | 87.2% | 72.5% | 48.3% | 52.1% |
| 369977 | Lancai (Shenzhen) Technology Co., Ltd NJ 07008 | 732 | 12% | 75.5% | 89.5% | 85.9% | 62.0% | 76.4% | 75.4% |
| 351158 | Hermes and Fesius LLC GA 31308 | 700 | 14% | 77.1% | 86.3% | 74.0% | 49.0% | 59.4% | 83.2% |
| 316680 | Casa Fine Arts TX 78753 | 680 | 10% | 68.8% | 85.1% | 82.0% | 53.0% | 73.5% | 68.2% |
| 25770 | Jamie Young Company 331 West Victoria | 633 | 16% | 79.6% | 88.5% | 85.5% | 67.4% | 81.0% | 79.1% |
| 247870 | GOLD TREE INC. GA 30519 | 593 | 15% | 69.3% | 91.1% | 74.9% | 49.1% | 59.1% | 72.7% |
| 370331 | North American Country Home CA 92336 | 563 | 24% | 77.8% | 87.7% | 89.9% | 84.1% | 77.9% | 77.8% |
| 299125 | EVE AY CORP CA 91789 | 541 | 51% | 44.5% | 89.1% | 82.7% | 67.5% | 41.5% | 49.0% |
| 147209 | New Decor LLC CA(7) | 515 | 14% | 76.3% | 87.0% | 83.3% | 62.2% | 94.5% | 71.9% |
| 6218 | Emissary | 450 | 15% | 69.3% | 86.7% | 80.9% | 60.7% | 58.8% | 71.6% |

## 5) Among cushioned — IFR≪del gap vs not

| Segment | Suppliers | Vol | Direct share | IFR | Del | Det on-time | Det end−1 |
|---------|-----------|-----|--------------|-----|-----|-------------|-----------|
| IFR << del (≥10pp) | 1010 | 373,393 | 7.6% | 58.1% | 81.2% | 78.8% | 53.4% |
| IFR not << del | 1606 | 540,536 | 6.1% | 84.6% | 84.2% | 85.8% | 70.7% |

## Files

| File | Contents |
|------|----------|
| `cushion_directs_ifr_vs_delrel.xlsx` | All tabs |
| `scripts/run_cushion_directs_ifr_del.py` | Re-run |
