# Directs corridors (PDD last 10w, DS)

Total direct volume: **581,541** ops

Origin = assigned station state → logistics region. Dest = customer `destination_state` → region.

## Where directs are built

**40% of all directs originate from West Coast assigned hubs** (almost entirely **CA** — 39.2% of network directs). Next origins: Southeast 24%, Northeast 19%.

Largest single corridor:

| Origin → Dest | Vol | % of directs | Notes |
|---------------|-----|--------------|-------|
| **West Coast → Midwest** | 48,112 | **8.3%** | Top lane; 98% CA origin; inducts Chicago/Toledo/Romeoville |
| West Coast → Southeast | 37,176 | 6.4% | |
| Southeast → Midwest | 35,321 | 6.1% | |
| Northeast → Midwest | 34,372 | 5.9% | |
| West Coast → West Coast | 31,242 | 5.4% | Intra-West (e.g. SoCal↔NorCal style) |
| West Coast → Northeast | 26,596 | 4.6% | |
| Northeast → Southeast | 26,321 | 4.5% | |
| West Coast → Florida | 25,634 | 4.4% | |
| West Coast → Mid-Atlantic | 23,994 | 4.1% | |

**Broader isolate (recommended for supplier compare):** West Coast → East/Central (Midwest + Southeast + Northeast + Florida + Mid-Atlantic + South Central) = **181,053 ops (31.1% of all directs)**.

## Isolate A: West Coast → Midwest

- **48,112** ops, **5,541** suppliers (long tail); **159** suppliers with ≥50 directs cover **19,473** ops
- Origin: CA 98.4%, WA 1.3%, OR 0.3%
- Top actual hubs: Chicago 21%, Toledo 12%, Romeoville Rsf 7%, Columbus 6%
- Top dest states: IL 28%, OH 19%, MI 14%, IN 10%, WI 9%
- Corridor IFR (vol≥50 suppliers): median **93%**, P25 **80%**, P10 **70%** — wide spread for peer compare

### Top volume suppliers on WC → Midwest

| SUID | Supplier | Vol | IFR | Del Rel | O2D act | Gain |
|------|----------|-----|-----|---------|---------|------|
| 237104 | Devion Furniture | 1,484 | 65.8% | 84.1% | 8.62 | 0.96 |
| 316872 | Heze Starfire CA 91761(5) | 512 | 75.6% | 90.0% | 8.86 | 0.97 |
| 238512 | CP HomeDecor CA 91761(2) | 414 | 76.6% | 86.5% | 7.74 | 0.95 |
| 28971 | NFusion CA11 (GigaCloud) | 376 | 76.6% | 76.3% | 7.07 | 0.96 |
| 39837 | Kingston CA | 311 | 92.9% | 91.3% | 8.07 | 0.97 |
| 236498 | Oberon Dist | 310 | 85.2% | 93.2% | 8.25 | 0.97 |
| 272805 | Karat Home CA 92880 | 299 | 75.3% | 89.0% | 8.49 | 0.97 |
| 280028 | CHINO (Ningbo Meigao) | 289 | 97.6% | 89.3% | 6.45 | 0.96 |

High-vol with weak IFR vs peers: **Devion (66%)**, Heze/CP/NFusion/Karat (~75%). Strong peers on same lane: Kingston, CHINO, Green Living (~93–98%).

### Weak IFR examples (vol≥50)

Curtis International CA (0%), BNF Home (14%), TarHong (14%), Pony Bros-2 (39%), ColourTree (45%).

## Isolate B: West Coast → East/Central (broader)

Same CA exporters, all non-West/Mountain dests — better for “who builds CA long-haul directs well.”

Top by vol: Devion (5,744, IFR 66%), CP HomeDecor (1,885, 79%), Heze (1,722, 81%), Kingston (1,643, **93%**), Green Living (1,155, **94%**), California Umbrella (807, **99.5%** but slow O2D ~11.6d).

## Files

| File | Contents |
|------|----------|
| `directs_corridors_analysis.xlsx` | Region corridors + WC→Midwest / East-Central supplier tabs |
| `directs_corridors_region_to_region.csv` | Full origin→dest region matrix |
| `directs_corridors_region_to_state.csv` | Origin region → dest state |
| `directs_corridor_west_coast_to_midwest_suppliers.csv` | Supplier compare on top corridor |
| `directs_corridor_west_coast_to_east_central_suppliers.csv` | Broader CA long-haul supplier compare |
| `scripts/run_directs_corridors.py` | Re-run script |

## Suggested next cut

Hold **West Coast → Midwest** (or East/Central) fixed; rank suppliers on IFR / delivery_rel / O2D actual among those with material vol (≥50 or ≥100). That isolates “same lane” peers instead of mixing ghost/jumbo/misshipping or unrelated geographies.
