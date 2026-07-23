# Pickup Pal Slack Bot Setup

Pickup Pal runs as a Slack Bolt app backed by BigQuery. Your friend can ask questions in a shared channel via `@Pickup Pal` or `/pickup-pal` without needing Cursor.

## 1. Create the Slack app

1. Go to [https://api.slack.com/apps](https://api.slack.com/apps) → **Create New App** → **From an app manifest**.
2. Select your workspace.
3. Paste the contents of `slack_app/manifest.yml`.
4. Create the app and install it to your workspace.

After install, collect these tokens from **Settings → Basic Information** and **Settings → Socket Mode**:

| Variable | Where to find it |
|----------|------------------|
| `SLACK_BOT_TOKEN` | OAuth & Permissions → Bot User OAuth Token (`xoxb-...`) |
| `SLACK_APP_TOKEN` | Basic Information → App-Level Token with `connections:write` (`xapp-...`) |
| `SLACK_SIGNING_SECRET` | Basic Information → Signing Secret (HTTP mode only) |

## 2. Create a channel and invite your friend

1. Create a channel (e.g. `#pickup-pal`).
2. Invite your friend and `@Pickup Pal`.
3. Optional: restrict the bot to specific channels by setting `PICKUP_PAL_ALLOWED_CHANNELS` to the channel ID (right-click channel → View channel details → copy ID).

## 3. GCP credentials

The bot needs read access to BigQuery tables used by Pickup Pal.

Set `GOOGLE_APPLICATION_CREDENTIALS` to either:

- A path to a service account JSON file, or
- Inline JSON (the `gbq` client writes it to `.gcp/credentials.json` automatically)

Required tables are listed in `docs/large_parcel/pickup_pal.md`.

## 4. Run locally (Socket Mode — recommended for testing)

Socket Mode avoids needing a public URL.

```bash
export SLACK_BOT_TOKEN=xoxb-...
export SLACK_APP_TOKEN=xapp-...
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

pip install -r requirements.txt
python slack_app/app.py
```

## 5. Deploy to Cloud Run (production)

Build and deploy:

```bash
gcloud builds submit --tag gcr.io/YOUR_PROJECT/pickup-pal -f slack_app/Dockerfile .
gcloud run deploy pickup-pal \
  --image gcr.io/YOUR_PROJECT/pickup-pal \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars SLACK_BOT_TOKEN=xoxb-...,SLACK_SIGNING_SECRET=...,GOOGLE_APPLICATION_CREDENTIALS='{"type":"service_account",...}'
```

For Cloud Run, **disable Socket Mode** in the Slack app settings and configure **Event Subscriptions**:

- Request URL: `https://YOUR_CLOUD_RUN_URL/slack/events`
- Subscribe to bot events: `app_mention`, `message.im`

Health check: `GET /health`

## 6. How to ask questions

**Natural language (channel mention):**

```
@Pickup Pal does Flash Furniture have enough volume for an extra pickup?
@Pickup Pal how many pickups does Fusion Furniture have this week?
@Pickup Pal what are the typical pickup days for Polywood?
```

**Slash commands:**

```
/pickup-pal extra-pickup Flash Furniture
/pickup-pal pickups Fusion Furniture
/pickup-pal typical-days Polywood
/pickup-pal help
```

**DMs:** Send the same natural-language questions directly to the bot.

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SLACK_BOT_TOKEN` | Yes | Bot OAuth token |
| `SLACK_APP_TOKEN` | Socket Mode | App-level token (`connections:write`) |
| `SLACK_SIGNING_SECRET` | HTTP mode | Request verification secret |
| `GOOGLE_APPLICATION_CREDENTIALS` | Yes | GCP service account JSON (path or inline) |
| `PICKUP_PAL_ALLOWED_CHANNELS` | No | Comma-separated channel IDs to allow |
| `PORT` | No | HTTP port (default 3000 local, 8080 in Docker) |

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Bot doesn't respond to mentions | Ensure bot is invited to channel; check `app_mention` event is subscribed |
| `not_in_channel` | `/invite @Pickup Pal` in the channel |
| Query failed | Verify GCP credentials and BigQuery table access |
| Slash command not found | Reinstall app after manifest changes |
