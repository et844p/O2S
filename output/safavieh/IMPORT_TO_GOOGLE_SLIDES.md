# Import Safavieh deck to Google Slides

The deck is generated as PowerPoint (`.pptx`) because Google Drive/Slides APIs are not enabled on the GCP service account project.

## Option A — Import into existing presentation (recommended)

1. Open [Google Slides](https://slides.google.com)
2. Create a blank presentation (or open one you want to add to)
3. **File → Import slides**
4. **Upload** tab → select `Safavieh_CEO_June_MSBD.pptx`
5. Choose **Replace slides** or **Append** → **Import slides**

## Option B — Upload to Drive

1. Open [Google Drive](https://drive.google.com)
2. Upload `Safavieh_CEO_June_MSBD.pptx`
3. Double-click the file → **Open with → Google Slides**
4. Drive converts PPTX to a native Google Slides file

## Download PPTX

- **GitHub (this branch):** [Safavieh_CEO_June_MSBD.pptx](https://github.com/et844p/O2S/raw/cursor/safavieh-ceo-preread-b7d6/output/safavieh/Safavieh_CEO_June_MSBD.pptx)
- **Local path:** `output/safavieh/Safavieh_CEO_June_MSBD.pptx`

## Regenerate deck

```bash
python scripts/create_safavieh_google_slides.py
```

## Auto-upload to Google Slides (optional)

Enable these APIs on project `wf-gcp-us-ae-profit-prod`:

- [Google Drive API](https://console.developers.google.com/apis/api/drive.googleapis.com/overview?project=865714439416)
- [Google Slides API](https://console.developers.google.com/apis/api/slides.googleapis.com/overview?project=865714439416)

Then re-run the script; it uploads and returns a shareable `docs.google.com` link.

## Slide outline (10 slides)

1. Title — Safavieh CEO In-Office
2. Executive summary
3. June MSBD parent snapshot
4. Same-day induction before 2pm — ops gap
5. Warehouse table (≤2pm same-day %)
6. Fast-badge simulation scenarios
7. Three policy levers
8. Discussion questions
9. Data & resources
