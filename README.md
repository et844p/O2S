# O2S

Small-parcel order-to-ship analysis (BigQuery / HVE_perf_Monitoring).

**GitHub:** [et844p_wayfair/O2S](https://github.com/et844p_wayfair/O2S)

## Git remotes

This repo should use **`et844p_wayfair/O2S`** as the primary remote (not `et844p/O2S`).

```bash
# After creating github.com/et844p_wayfair/O2S, set origin and push:
git remote set-url origin https://github.com/et844p_wayfair/O2S.git
git push -u origin main
git push origin cursor/jla-savannah-fedex-analysis-0c61
```

To mirror all branches from a local clone that still points at `et844p/O2S`:

```bash
./scripts/push_to_wayfair.sh
```

## Cursor Cloud Agent

Link the Cloud Agent environment to `https://github.com/et844p_wayfair/O2S` (Settings → Cloud → Environment → Repository).
