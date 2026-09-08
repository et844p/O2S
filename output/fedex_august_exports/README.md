# FedEx August outreach exports

**Source:** `` `wf-gcp-us-ae-global-tnd-prod.speed_and_reliability.fedex_order_classfication_ET` ``  
**Window:** `delivery_date` 2026-08-01 → 2026-08-31  
**Runner:** `scripts/export_fedex_august_outreach.py`

## Goal

1. Cut **unexpected farther** volume (worse delivery).
2. Lift **IFR / delivery_rel** on **right hub** and **local hub swap** by targeting underperforming parents/SUIDs.

## Files

| File | Contents |
|------|----------|
| `01_farther_parents_august.csv` | Parents with ≥200 farther ops (misship farther + other_farther) |
| `01_farther_suids_august.csv` | SUIDs under top 20 farther parents (≥50 farther ops) |
| `01_farther_sample_trackings_august.csv` | Up to 25 trackings per SUID (farthest hub delta first) |
| `02_right_hub_underperformer_parents_august.csv` | Top 20 right-hub parents below bench (vol ≥2k; IFR −3pp or DR −5pp) |
| `02_right_hub_underperformer_suids_august.csv` | Underperforming SUIDs under those parents |
| `02_right_hub_sample_trackings_august.csv` | Up to 25 trackings per SUID (late DR/IFR first) |
| `03_local_swap_underperformer_parents_august.csv` | Top 20 local-swap parents below bench (vol ≥1.5k) |
| `03_local_swap_underperformer_suids_august.csv` | Underperforming SUIDs under those parents |
| `03_local_swap_sample_trackings_august.csv` | Up to 25 trackings per SUID (late DR/IFR first) |

## August benchmarks (bucket)

| Bucket | IFR | Delivery rel |
|--------|-----|--------------|
| Right hub | ~90.9% | ~83.1% |
| Local hub &lt;100 mi | ~90.3% | ~87.5% |
| Unexpected farther | — | ~61.1% |

Regenerate:

```bash
PYTHONPATH=/workspace python3 scripts/export_fedex_august_outreach.py
```
