# LP add/cancel recommendations — week of 2026-09-07

As of **2026-09-09 13:30 UTC**. Monday-start week `2026-09-07`.

Consolidated from live MSOD (`fm_msod_dropnew`) into the Combined tab shape of
[FM LP WDN Add/Cancel](https://docs.google.com/spreadsheets/d/19epubeBb3ohHO10UVUJUhd13MTECq_khKhAVQLRU9SI/edit?gid=710144122#gid=710144122)
(`LaneID`, `SuName`, `PoolPoint`, `PlannedDate`, `PlannedPickups`, `Add`, `Cancel`).

The Google Sheet Combined tab is also registered in BigQuery as
`tnd_planning.FM_LP_WDN_Add_Cancel_Sheet`. Planner completion notes
(`WasCompleted`, `TLPReasonCodes`, comments) live only on the sheet.

## Snapshot

| Metric | Value |
| --- | --- |
| Supplier / lane recs | 143 |
| Distinct lanes | 77 |
| Pool points | 11 |
| Add recs (loads) | 76 recs / **114** loads |
| Cancel recs (loads) | 67 recs / **85** loads |
| Net loads | **+29** |
| Days with recs | 2026-09-09, 2026-09-10, 2026-09-11 |

`Add` / `Cancel` use capacity-capped `Recommendation`. Uncapped need is in the detail CSV.

## By day and routing type

| PlannedDate | RoutingType | Lanes | Add | Cancel |
| --- | --- | --- | --- | --- |
| 2026-09-09 | Drop Pooled | 27 | 30 | 14 |
| 2026-09-09 | OTR | 18 | 19 | 2 |
| 2026-09-10 | Drop Pooled | 28 | 25 | 21 |
| 2026-09-10 | OTR | 16 | 17 | 3 |
| 2026-09-11 | Drop Pooled | 40 | 12 | 39 |
| 2026-09-11 | OTR | 14 | 11 | 6 |

## By pool point

| PoolPoint | Lanes | Recs | Add | Cancel |
| --- | --- | --- | --- | --- |
| Wayfair - McDonough | 11 | 21 | 27 | 4 |
| Wayfair - Cranbury 3 | 10 | 21 | 21 | 10 |
| Wayfair - South Elgin | 11 | 20 | 17 | 5 |
| Wayfair - Perris | 27 | 51 | 15 | 55 |
| Wayfair - Lathrop | 3 | 6 | 15 | 2 |
| Wayfair - Greensboro | 5 | 10 | 12 | 2 |
| Wayfair - Lancaster | 5 | 8 | 4 | 4 |
| Wayfair - Mississauga | 1 | 2 | 2 | 0 |
| Wayfair - Kent | 1 | 1 | 1 | 0 |
| Wayfair - Jacksonville | 2 | 2 | 0 | 2 |
| Wayfair - Pompano | 1 | 1 | 0 | 1 |

## Today's actions (2026-09-09)

45 lanes — **49 add** / **16 cancel** loads.

| Add | Cancel | PoolPoint | SuName | PlannedPickups | TotalOutstandingPOs | RoutingType |
| --- | --- | --- | --- | --- | --- | --- |
| 5 | 0 | Wayfair - Cranbury 3 | Elegant Lighting B Street Multistop | 6 | 214 | Drop Pooled |
| 3 | 0 | Wayfair - Greensboro | Hooker Furniture VA Multistop | 1 | 391 | Drop Pooled |
| 3 | 0 | Wayfair - Lathrop | Lexicon Home LLC CA 94538 to Wayfair - Lathrop | 5 | 315 | Drop Pooled |
| 3 | 0 | Wayfair - McDonough | Flash Furniture MS 38654 to Moe's Home Collection MS 30114 to Crestview Collection TN to Wayfair - McDonough | 2 | 312 | OTR |
| 2 | 0 | Wayfair - Cranbury 3 | Elegant Lighting Erie to Cranbury | 1 | 48 | Drop Pooled |
| 2 | 0 | Wayfair - McDonough | CharBroil GA 31904 to Wayfair - McDonough | 0 | 52 | Drop Pooled |
| 2 | 0 | Wayfair - South Elgin | Polywood IN 46567-Wayfair - South Elgin | 0 | 36 | OTR |
| 1 | 0 | Wayfair - Cranbury 3 | Elegant Lighting PA 19140 Glenwood to Wayfair - Cranbury 3 | 4 | 79 | Drop Pooled |
| 1 | 0 | Wayfair - Cranbury 3 | MUSEM INC. NJ 08016 (2) to Wayfair - Cranbury 3 | 1 | 33 | Drop Pooled |
| 1 | 0 | Wayfair - Cranbury 3 | Meridian Furniture NJ 08638 to Cran | 2 | 178 | Drop Pooled |
| 1 | 0 | Wayfair - Cranbury 3 | Modway NJ 08520 to Create comfort NJ 08520 to Wayfair - Cranbury 3 | 1 | 131 | Drop Pooled |
| 1 | 0 | Wayfair - Greensboro | Jofran SC to Greensboro NC | 0 | 27 | OTR |
| 1 | 0 | Wayfair - Kent | Emerald Home Furnishings WA to Wayfair - Kent | 0 | 56 | Drop Pooled |
| 1 | 0 | Wayfair - Lancaster | Elements International TX to Wayfair - Lancaster | 1 | 71 | Drop Pooled |
| 1 | 0 | Wayfair - Lancaster | Home Trends Design Ltd -Wayfair - Lancaster | 0 | 72 | OTR |
| 1 | 0 | Wayfair - Lancaster | Steve Silver Company TX to Wayfair - Lancaster | 1 | 203 | Drop Pooled |
| 1 | 0 | Wayfair - Lancaster | Vanity Art TX75234 to Betsy Trading LLC TX 75234 to Wayfair - Lancaster  | 1 | 40 | Drop Pooled |
| 1 | 0 | Wayfair - McDonough | American Heartland-Wayfair - McDonough | 0 | 15 | OTR |
| 1 | 0 | Wayfair - McDonough | Catnapper MS 38855-Wayfair - McDonough | 0 | 8 | OTR |
| 1 | 0 | Wayfair - McDonough | Liberty Furniture GA 31320 to Wayfair - McDonough | 0 | 71 | OTR |
| 1 | 0 | Wayfair - McDonough | Net Direct Merchants AL 35630 to Wayfair - McDonough | 0 | 28 | OTR |
| 1 | 0 | Wayfair - Mississauga | Vanity Art_1 ON L5S 2A4 to Wayfair - Missasauga | 2 | 27 | Drop Pooled |
| 1 | 0 | Wayfair - Perris | Intercon Inc. UT 84116 to Westwood Design UT 84116 to Wayfair - Perris | 0 | 15 | OTR |
| 1 | 0 | Wayfair - Perris | LifetimeUT84016-Wayfair - Perris 1 | 0 | 2 | OTR |
| 1 | 0 | Wayfair - Perris | Martin Furniture CA-Wayfair - Perris 1 | 2 | 122 | Drop Pooled |
| 1 | 0 | Wayfair - Perris | Megabrand Kitchen Bath Inc. CA to Wayfair - Perris | 2 | 121 | Drop Pooled |
| 1 | 0 | Wayfair - Perris | Modus Furniture International Inc. CA to Wayfair - Perris | 2 | 151 | Drop Pooled |
| 1 | 0 | Wayfair - Perris | New Classic CA to Perris 1 | 1 | 91 | Drop Pooled |
| 1 | 0 | Wayfair - Perris | Sorara Outdoor Living USA, Inc. CA 91746 to Wayfair - Perris | 0 | 21 | Drop Pooled |
| 1 | 0 | Wayfair - Perris | Wyndham Collection CA to Wayfair - Perris | 1 | 51 | Drop Pooled |
| 1 | 0 | Wayfair - South Elgin | Crafters and Weavers IL-Wayfair - South Elgin | 0 | 21 | OTR |
| 1 | 0 | Wayfair - South Elgin | Escalade Sports IN 47711-Wayfair - South Elgin | 2 | 164 | OTR |
| 1 | 0 | Wayfair - South Elgin | Flexsteel KS-Wayfair - South Elgin | 1 | 71 | OTR |
| 1 | 0 | Wayfair - South Elgin | HomeStylesIN to South Elgin | 0 | 52 | OTR |
| 1 | 0 | Wayfair - South Elgin | MMI Door OH 45246 to Simmons Mattress OH 45050 to Serta National OH 45050 to Wayfair - South Elgin | 0 | 62 | OTR |
| 1 | 0 | Wayfair - South Elgin | The Stock Market OH 45822 to Wayfair - South Elgin | 0 | 13 | OTR |
| 0 | 4 | Wayfair - Perris | Kingway Inc CA 91761 (2) to Wayfair - Perris | 4 | 5 | Drop Pooled |
| 0 | 4 | Wayfair - Perris | Star Home Living Corp. CA 92337 to Wayfair - Perris | 4 | 9 | Drop Pooled |
| 0 | 2 | Wayfair - Perris | Inspyre WH LLC CA 90040(2) to Perris | 2 | 0 | Drop Pooled |
| 0 | 1 | Wayfair - Cranbury 3 | M S International NJ 08817 to Cranbury | 2 | 38 | Drop Pooled |
| 0 | 1 | Wayfair - Cranbury 3 | SOHO Studio NJ 08075 to Wayfair - Cranbury 3 | 1 | 2 | Drop Pooled |
| 0 | 1 | Wayfair - Greensboro | Cottage Creek NC 28504 to Edgecombe Furniture WH Level to Wayfair - Greensboro | 1 | 3 | OTR |
| 0 | 1 | Wayfair - Lathrop | LY Home Living Inc CA 95691 to Wayfair - Lathrop | 1 | 1 | Drop Pooled |
| 0 | 1 | Wayfair - McDonough | Atlas International GA 31302 to Wayfair - McDonough | 6 | 104 | OTR |
| 0 | 1 | Wayfair - Perris | VIG Furniture CA 90058 Slauson to Wayfair - Perris | 2 | 69 | Drop Pooled |

## Top add lanes (week)

| LaneID | SuName | PoolPoint | RoutingType | Add | Cancel | Net | OutstandingPOs |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 3503 | Lexicon Home LLC CA 94538 to Wayfair - Lathrop | Wayfair - Lathrop | Drop Pooled | 14 | 0 | 14 | 315 |
| 3998 | Elegant Lighting B Street Multistop | Wayfair - Cranbury 3 | Drop Pooled | 11 | 0 | 11 | 218 |
| 4159 | Flash Furniture MS 38654 to Moe's Home Collection MS 30114 to Crestview Collection TN to Wayfair - McDonough | Wayfair - McDonough | OTR | 9 | 0 | 9 | 414 |
| 3893 | Hooker Furniture VA Multistop | Wayfair - Greensboro | Drop Pooled | 7 | 0 | 7 | 406 |
| 3535 | Liberty Furniture GA 31320 to Wayfair - McDonough | Wayfair - McDonough | OTR | 5 | 0 | 5 | 94 |
| 1783 | Martin Furniture CA-Wayfair - Perris 1 | Wayfair - Perris | Drop Pooled | 4 | 0 | 4 | 126 |
| 2791 | Polywood IN 46567-Wayfair - South Elgin | Wayfair - South Elgin | OTR | 4 | 0 | 4 | 36 |
| 3487 | CharBroil GA 31904 to Wayfair - McDonough | Wayfair - McDonough | Drop Pooled | 4 | 0 | 4 | 55 |
| 2342 | Elegant Lighting Erie to Cranbury | Wayfair - Cranbury 3 | Drop Pooled | 3 | 0 | 3 | 48 |
| 2607 | Creative Co-Op TN-Wayfair - McDonough | Wayfair - McDonough | OTR | 3 | 0 | 3 | 54 |
| 4085 | HomeStylesIN to South Elgin | Wayfair - South Elgin | OTR | 3 | 0 | 3 | 53 |
| 2345 | SOHO Studio NJ 08075 to Wayfair - Cranbury 3 | Wayfair - Cranbury 3 | Drop Pooled | 2 | 1 | 1 | 76 |

## Top cancel lanes (week)

| LaneID | SuName | PoolPoint | RoutingType | Add | Cancel | Net | OutstandingPOs |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 3802 | Kingway Inc CA 91761 (2) to Wayfair - Perris | Wayfair - Perris | Drop Pooled | 0 | 12 | -12 | 5 |
| 2453 | Star Home Living Corp. CA 92337 to Wayfair - Perris | Wayfair - Perris | Drop Pooled | 0 | 7 | -7 | 21 |
| 3617 | Inspyre WH LLC CA 90040(2) to Perris | Wayfair - Perris | Drop Pooled | 0 | 5 | -5 | 0 |
| 2343 | M S International NJ 08817 to Cranbury | Wayfair - Cranbury 3 | Drop Pooled | 0 | 3 | -3 | 47 |
| 2394 | VIG Furniture CA 90058 Slauson to Wayfair - Perris | Wayfair - Perris | Drop Pooled | 0 | 3 | -3 | 85 |
| 2786 | Andes Furniture Fontana C 92335 to Wayfair - Perris | Wayfair - Perris | Drop Pooled | 0 | 3 | -3 | 49 |
| 2620 | Atlas International CA 92649 to Wayfair - Perris | Wayfair - Perris | Drop Pooled | 0 | 3 | -3 | 161 |
| 3657 | Parker House CA 91761 to Wayfair - Perris 1 | Wayfair - Perris | Drop Pooled | 0 | 2 | -2 | 37 |
| 2627 | Andes Furniture CA 92870 to Wayfair - Perris | Wayfair - Perris | Drop Pooled | 0 | 2 | -2 | 22 |
| 3459 |  AlpineFurniture CA 92507 to Wayfair - Perris  | Wayfair - Perris | Drop Pooled | 0 | 2 | -2 | 92 |
| 3423 | Glass Warehouse CA 92056 - Wayfair - Perris | Wayfair - Perris | Drop Pooled | 0 | 2 | -2 | 38 |
| 3604 | Angle Industries NJ 07823 to Cranbury 3 | Wayfair - Cranbury 3 | Drop Pooled | 0 | 2 | -2 | 36 |

## Capacity-capped (uncapped need is higher)

| PlannedDate | PoolPoint | SuName | NetRecommendation | UncappedRecommendation |
| --- | --- | --- | --- | --- |
| 2026-09-09 | Wayfair - Cranbury 3 | Elegant Lighting PA 19140 Glenwood to Wayfair - Cranbury 3 | 1 | 2 |
| 2026-09-09 | Wayfair - Greensboro | Hooker Furniture VA Multistop | 3 | 5 |
| 2026-09-09 | Wayfair - Lathrop | Lexicon Home LLC CA 94538 to Wayfair - Lathrop | 3 | 8 |
| 2026-09-09 | Wayfair - McDonough | Flash Furniture MS 38654 to Moe's Home Collection MS 30114 to Crestview Collection TN to Wayfair - McDonough | 3 | 8 |
| 2026-09-09 | Wayfair - Perris | Martin Furniture CA-Wayfair - Perris 1 | 1 | 4 |
| 2026-09-09 | Wayfair - South Elgin | Escalade Sports IN 47711-Wayfair - South Elgin | 1 | 3 |
| 2026-09-09 | Wayfair - South Elgin | Flexsteel KS-Wayfair - South Elgin | 1 | 2 |
| 2026-09-10 | Wayfair - Greensboro | Hooker Furniture VA Multistop | 2 | 3 |
| 2026-09-10 | Wayfair - McDonough | Flash Furniture MS 38654 to Moe's Home Collection MS 30114 to Crestview Collection TN to Wayfair - McDonough | 3 | 9 |
| 2026-09-10 | Wayfair - Perris | Martin Furniture CA-Wayfair - Perris 1 | 2 | 3 |
| 2026-09-11 | Wayfair - McDonough | Flash Furniture MS 38654 to Moe's Home Collection MS 30114 to Crestview Collection TN to Wayfair - McDonough | 3 | 7 |

## Files

- Combined-format paste: `output/add_cancel/this_week_combined.csv`
- Full detail: `output/add_cancel/this_week_detail.csv`
- Lane rollup: `output/add_cancel/this_week_lane_summary.csv`
- SQL: `sql/large_parcel/add_cancel_this_week.sql`

Re-run: `python scripts/consolidate_add_cancel_recs.py`
