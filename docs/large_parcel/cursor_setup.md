# Pickup Pal — Cursor + BigQuery Setup (Windows)

Adapted from the internal Cursor Set Up guide. Use this to query Large Parcel pickup data **inside Cursor** (no local Python bot required for IDE use).

For **Slack** (`@Pickup Pal` in a channel), see [slack_setup.md](./slack_setup.md) — that requires a hosted bot or Cloud Run deploy.

---

## Prerequisites

- [ ] Cursor installed (request access if needed)
- [ ] Python installed ([python.org](https://www.python.org/downloads/) — check **Add to PATH** on Windows)
- [ ] GitHub account with access to the O2S repo
- [ ] Wayfair Google account with BigQuery access

---

## Part 1: Install & Configure Google Cloud CLI

### Step 1: Install Google Cloud CLI

1. Download from [cloud.google.com/sdk](https://cloud.google.com/sdk)
2. Run the installer
3. When complete, the **Google Cloud SDK Shell** opens automatically

### Step 2: Authenticate with GCP

In the Google Cloud SDK Shell:

```bash
gcloud init
```

This will:

- Open a browser to log in with your Wayfair Google account
- Set your default project (`wf-gcp-us-ae-global-tnd-prod`)
- Confirm with:

```bash
gcloud config get-value project
```

Expected: `wf-gcp-us-ae-global-tnd-prod`

### Step 3: Add gcloud to your PATH

Cursor's terminal won't find `gcloud` until it's on your PATH.

1. Windows key + S → search **environment variables**
2. **Edit environment variables for your account**
3. **Environment Variables** → under **System variables**, select **Path** → **Edit**
4. **New** → add:

```
C:\Users\YOUR_USERNAME\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin
```

(Replace `YOUR_USERNAME`, e.g. `ka083h`)

5. OK all dialogs
6. **Fully close and reopen Cursor**

Verify in Cursor's terminal:

```bash
gcloud version
bq version
```

If PowerShell blocks scripts:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Step 4: Application Default Credentials

In Cursor's terminal, use **cmd** (not PowerShell):

```bash
gcloud auth application-default login
```

Browser opens → log in with Wayfair account → credentials saved locally.

> If PowerShell blocks this, click the **+** dropdown in the terminal panel and select **Command Prompt (cmd)**.

### Step 5: BigQuery Runner extension (optional)

1. `Ctrl+Shift+X` → search **BigQuery Runner** → install (by minodisk)
2. `Ctrl+Shift+P` → **Open User Settings (JSON)**
3. Add:

```json
"bigqueryRunner.projectId": "wf-gcp-us-ae-global-tnd-prod"
```

### Step 6: Test connection

1. Create `test.sql` with:

```sql
SELECT CURRENT_DATE()
```

2. `Ctrl+Shift+P` → **BigQuery Runner: Run**
3. Results should appear in the panel

**Terminal alternative (cmd, double quotes):**

```bash
bq query --use_legacy_sql=false "SELECT CURRENT_DATE()"
```

---

## Part 2: Clone the O2S repo

### Step 1 — Get the repo URL

Your Pickup Pal code lives in the **O2S** repo (not `transportation_and_delivery`).

```bash
git clone https://github.com/et844p/O2S.git
```

(Use your team's fork URL if different.)

### Step 2 — Open in Cursor

1. **File → Open Folder**
2. Select the cloned `O2S` folder
3. You should see `pickup_pal/`, `sql/large_parcel/`, `docs/large_parcel/`

### Step 3 — Install Python dependencies (one time)

In Cursor terminal (cmd):

```bash
cd O2S
pip install -r requirements.txt
```

---

## Part 3: Use Pickup Pal in Cursor

No Slack or local bot needed for IDE queries.

### Option A — CLI

```bash
python scripts/pickup_pal_query.py extra_pickup --supplier "Flash Furniture"
python scripts/pickup_pal_query.py pickups_this_week --supplier "Fusion Furniture"
python scripts/pickup_pal_query.py typical_days --supplier "Polywood"
```

### Option B — Ask Cursor Agent

Open **Agent** chat and ask naturally, e.g.:

- *Does Flash Furniture have enough volume for an extra pickup?*
- *How many pickups does Fusion Furniture have this week?*
- *What are the typical pickup days for Polywood?*

The `.cursor/rules/pickup-pal-gbq.mdc` rule guides the agent to the right tables and SQL.

Authentication uses your `gcloud auth application-default login` credentials — no service account JSON file needed for local Cursor use.

---

## Part 4: Git sync

Before working:

```bash
git pull
```

After changes:

```bash
git add .
git commit -m "your message"
git push
```

Cursor shows sync indicators in the bottom-left status bar (`↓ 1` / `↑ 1`).

---

## Cursor vs Slack vs n8n

| Method | What you set up | Who can use it |
|--------|-----------------|----------------|
| **This guide (Cursor + gcloud)** | gcloud + clone repo | You (in Cursor IDE) |
| **@cursor in Slack** | Cursor org Slack integration | Team (Cursor product) |
| **n8n-bot** | n8n cloud workflows | Team (n8n hosted) |
| **Pickup Pal Slack bot** | Cloud Run deploy | Team (needs hosting) |

Following **this PDF does not** by itself enable `@Pickup Pal` in Slack. It enables **you** to ask pickup questions inside Cursor with live BigQuery data.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `gcloud` not found | Add SDK to PATH; restart Cursor |
| BigQuery permission denied | Confirm project `wf-gcp-us-ae-global-tnd-prod` and table access |
| `python` not found | Install Python; use `python3` on Mac |
| Pickup Pal rule not applied | Open files under `docs/large_parcel/` or mention "Pickup Pal" in chat |
