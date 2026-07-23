# Pickup Pal — 2-Minute Quickstart

Everything in the repo is pre-configured. You only need **one browser login** on your computer.

---

## For you (Cursor — no Slack bot needed)

### Option A — Run the setup script (Windows)

1. Open **PowerShell** in the `O2S` folder
2. Run:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\scripts\setup_windows.ps1
```

3. Complete the Google login in your browser when prompted
4. Open the `O2S` folder in **Cursor**
5. Ask Agent: *"How many pickups does Fusion Furniture have this week?"*

### Option B — Manual (if script fails)

1. Install [gcloud](https://cloud.google.com/sdk) and [Python](https://python.org)
2. In **cmd** (not PowerShell):

```bash
gcloud config set project wf-gcp-us-ae-global-tnd-prod
gcloud auth application-default login
pip install -r requirements.txt
python scripts/validate_setup.py --skip-slack
```

3. Open `O2S` in Cursor → ask Pickup Pal questions in Agent

**No service account JSON file needed** if you use `gcloud auth application-default login`.

---

## For your friend (Slack — needs hosting)

Slack won't work until the bot is **running on a server**. Two options:

### Option 1 — Add secrets to Cursor Cloud (for testing)

1. Go to [cursor.com/dashboard](https://cursor.com) → **Cloud Agents** → **Secrets**
2. Add:
   - `SLACK_BOT_TOKEN` = your `xoxb-...` token
   - `SLACK_APP_TOKEN` = your `xapp-...` token
3. Ask a Cloud Agent to run: `python slack_app/app.py`

> Note: Cloud agents stop when the session ends. For 24/7 Slack, use Cloud Run.

### Option 2 — Cloud Run (always on, like n8n)

See [slack_setup.md](./slack_setup.md) — requires someone with GCP deploy access.

---

## Verify everything works

```bash
python scripts/validate_setup.py --skip-slack
python scripts/pickup_pal_query.py pickups_this_week --supplier "Fusion Furniture"
```

---

## What was already done for you

- ✅ Pickup Pal SQL queries and formatters
- ✅ Cursor rules for Agent (`pickup-pal-gbq.mdc`)
- ✅ Cloud environment config (`.cursor/environment.json`)
- ✅ BigQuery works with `gcloud login` (no JSON file required)
- ✅ Slack bot code ready (needs tokens + hosting)

## What only you can do

| Action | Why |
|--------|-----|
| `gcloud auth application-default login` | Requires your Wayfair Google login in a browser |
| Add Slack tokens to secrets | Only you have the tokens |
| Deploy to Cloud Run | Requires your GCP project access |
