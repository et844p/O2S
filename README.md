# O2S

Small-parcel / O2S analytics helpers (BigQuery + Cursor skills).

## Wrong LT monitor

Daily check for DS orders receiving an incorrect lead time:

```bash
python scripts/run_wrong_lt_monitor.py
```

See `docs/small_parcel/wrong_lt_monitor.md` and the Cursor skill `.cursor/skills/wrong-lt-monitor/`.
