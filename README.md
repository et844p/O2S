# O2S

Analytics toolkit for Small Parcel and Large Parcel (Pickup Pal) operations.

## Pickup Pal (Large Parcel)

```bash
python scripts/pickup_pal_query.py extra_pickup --supplier "Flash Furniture"
python scripts/pickup_pal_query.py pickups_this_week --supplier "Fusion Furniture"
python scripts/pickup_pal_query.py typical_days --supplier "Polywood"
```

See `docs/large_parcel/pickup_pal.md` for query rules and table references.

### Slack bot

```bash
export SLACK_BOT_TOKEN=xoxb-...
export SLACK_APP_TOKEN=xapp-...
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
python slack_app/app.py
```

Full setup: `docs/large_parcel/slack_setup.md`
