#!/usr/bin/env python3
"""Build Safavieh CEO deck as PPTX and upload to Google Slides when Drive API is enabled."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt

OUT_DIR = ROOT / "output" / "safavieh"
PPTX_PATH = OUT_DIR / "Safavieh_CEO_June_MSBD.pptx"
CREDS_PATH = ROOT / ".gcp" / "credentials.json"

NAVY = RGBColor(0x1a, 0x36, 0x5d)
WHITE = RGBColor(0xff, 0xff, 0xff)
DARK = RGBColor(0x33, 0x33, 0x33)
ACCENT = RGBColor(0x2e, 0x86, 0xab)
RED = RGBColor(0xc0, 0x39, 0x2b)
GREEN = RGBColor(0x27, 0xae, 0x60)


def _textbox(slide, left, top, width, height, text, size=18, bold=False, color=DARK, align=PP_ALIGN.LEFT):
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(size)
    p.font.bold = bold
    p.font.color.rgb = color
    p.alignment = align
    return box


def _title_slide(prs, title, subtitle):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = NAVY
    _textbox(slide, Inches(0.8), Inches(2.0), Inches(11.5), Inches(1.2), title, 36, True, WHITE, PP_ALIGN.LEFT)
    _textbox(slide, Inches(0.8), Inches(3.3), Inches(11.5), Inches(1.5), subtitle, 20, False, WHITE, PP_ALIGN.LEFT)
    _textbox(slide, Inches(0.8), Inches(6.5), Inches(11.5), Inches(0.5), "Wayfair · Small Parcel · July 2026", 14, False, WHITE)


def _section_slide(prs, title, bullets: list[str]):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _textbox(slide, Inches(0.6), Inches(0.4), Inches(12), Inches(0.8), title, 28, True, NAVY)
    y = Inches(1.3)
    for bullet in bullets:
        _textbox(slide, Inches(0.8), y, Inches(11.5), Inches(0.55), f"• {bullet}", 16, False, DARK)
        y += Inches(0.5)


def _metric_slide(prs, title, rows: list[tuple[str, str]]):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _textbox(slide, Inches(0.6), Inches(0.4), Inches(12), Inches(0.8), title, 28, True, NAVY)
    n = len(rows) + 1
    tbl = slide.shapes.add_table(n, 2, Inches(1.2), Inches(1.5), Inches(10.5), Inches(0.45 * n)).table
    tbl.columns[0].width = Inches(6.5)
    tbl.columns[1].width = Inches(4.0)
    hdr = tbl.rows[0].cells
    hdr[0].text = "Metric"
    hdr[1].text = "Value"
    for c in hdr:
        c.fill.solid()
        c.fill.fore_color.rgb = NAVY
        for p in c.text_frame.paragraphs:
            p.font.bold = True
            p.font.color.rgb = WHITE
            p.font.size = Pt(14)
    for i, (label, val) in enumerate(rows, 1):
        tbl.rows[i].cells[0].text = label
        tbl.rows[i].cells[1].text = val
        for c in tbl.rows[i].cells:
            for p in c.text_frame.paragraphs:
                p.font.size = Pt(14)


def _warehouse_table_slide(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _textbox(slide, Inches(0.4), Inches(0.25), Inches(12), Inches(0.6),
             "Same-day induction before 2pm by warehouse (June)", 22, True, NAVY)
    _textbox(slide, Inches(0.4), Inches(0.75), Inches(12), Inches(0.4),
             "Toolkit hourly · Tue–Sat orders · order_hour ≤ 14 local · June 2026", 11, False, DARK)

    headers = ["Location", "Vol", "IFR", "Fast badge", "≤2pm same-day"]
    data = [
        ("Carlisle, PA", "1,475", "89%", "91%", "94%"),
        ("Riverside, CA", "7,967", "99%", "73%", "84%"),
        ("Savannah, GA", "6,483", "95%", "90%", "84%"),
        ("Whitestown, IN", "13,757", "93%", "91%", "73%"),
        ("Patterson, CA", "5,271", "93%", "64%", "73%"),
        ("Baytown, TX", "12,824", "89%", "91%", "66%"),
        ("Midway, GA", "5,975", "95%", "90%", "67%"),
        ("Port Wentworth, GA", "1,665", "90%", "87%", "51%"),
        ("Lebanon, NJ", "9,377", "82%", "81%", "50%"),
        ("Flemington, NJ", "4,446", "76%", "84%", "50%"),
        ("Easton, PA", "2,855", "83%", "82%", "42%"),
    ]
    rows = len(data) + 1
    tbl = slide.shapes.add_table(rows, 5, Inches(0.35), Inches(1.15), Inches(12.5), Inches(0.32 * rows)).table
    widths = [Inches(2.8), Inches(1.0), Inches(0.9), Inches(1.2), Inches(1.5)]
    for i, w in enumerate(widths):
        tbl.columns[i].width = w
    for j, h in enumerate(headers):
        cell = tbl.rows[0].cells[j]
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = NAVY
        for p in cell.text_frame.paragraphs:
            p.font.bold = True
            p.font.color.rgb = WHITE
            p.font.size = Pt(11)
    for ri, row in enumerate(data, 1):
        for ci, val in enumerate(row):
            cell = tbl.rows[ri].cells[ci]
            cell.text = val
            for p in cell.text_frame.paragraphs:
                p.font.size = Pt(10)
            if ci == 4 and val in ("42%", "50%", "51%"):
                for p in cell.text_frame.paragraphs:
                    p.font.color.rgb = RED
            if ci == 4 and val == "94%":
                for p in cell.text_frame.paragraphs:
                    p.font.color.rgb = GREEN


def _scenario_slide(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _textbox(slide, Inches(0.4), Inches(0.25), Inches(12), Inches(0.6),
             "Badging simulation — all speed tiers (June MSBD)", 24, True, NAVY)
    headers = ["Scenario", "1-day", "2-day", "3-day", "Fast ≤5d"]
    data = [
        ("June actual", "0.5%", "9.5%", "42.5%", "84.7%"),
        ("2pm + no cushion", "5.1%", "24.1%", "55.7%", "85.8%"),
        ("+ Weekend shipping", "6.3%", "26.4%", "59.5%", "86.9%"),
        ("Uplift (full vs June)", "+5.8 pp", "+17.1 pp", "+17.0 pp", "+2.2 pp"),
    ]
    rows = len(data) + 1
    tbl = slide.shapes.add_table(rows, 5, Inches(0.5), Inches(1.0), Inches(12.3), Inches(0.38 * rows)).table
    for j, h in enumerate(headers):
        c = tbl.rows[0].cells[j]
        c.text = h
        c.fill.solid()
        c.fill.fore_color.rgb = NAVY
        for p in c.text_frame.paragraphs:
            p.font.bold = True
            p.font.color.rgb = WHITE
            p.font.size = Pt(12)
    for ri, row in enumerate(data, 1):
        for ci, val in enumerate(row):
            tbl.rows[ri].cells[ci].text = val
            for p in tbl.rows[ri].cells[ci].text_frame.paragraphs:
                p.font.size = Pt(12)
                if ri == 4 and ci > 0:
                    p.font.color.rgb = GREEN
    _textbox(slide, Inches(0.5), Inches(3.5), Inches(12), Inches(1.2),
             "Newly badged (full sim): 4,260 · 1-day | 12,406 · 2-day | 12,479 · 3-day | 1,644 · fast",
             13, False, DARK)
    _textbox(slide, Inches(0.5), Inches(4.5), Inches(12), Inches(2.0),
             "Rules: remove cushion (−1d) · 2pm cutoff (−1d) · weekend ship (−1d). "
             "Badge tier = sim O2D ≤ N days.",
             12, False, DARK)


def build_presentation() -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    _title_slide(
        prs,
        "Safavieh CEO In-Office",
        "June MSBD performance · Badging simulation · Same-day induction before 2pm\n"
        "Dropship · Rugs STO · 73k ops",
    )

    _section_slide(
        prs,
        "Executive summary",
        [
            "~73k dropship rug ops in June MSBD across 13 US warehouses",
            "90.3% induction fill rate (IFR) — strong month vs recent trend",
            "Badging today: 0.5% 1-day · 9.5% 2-day · 42.5% 3-day · 84.7% fast",
            "Full policy sim: 6.3% 1-day · 26.4% 2-day · 59.5% 3-day · 86.9% fast",
            "+17 pp uplift at 2- and 3-day tiers — bigger than fast badge (+2 pp)",
            "68.3% same-day induction before 2pm — operational proof point",
        ],
    )

    _metric_slide(
        prs,
        "June MSBD — parent snapshot",
        [
            ("Volume (distinct ops)", "73,253"),
            ("Induction Fill Rate", "90.3%"),
            ("Fast-badge % (o2d_stated ≤ 5)", "84.7%"),
            ("Same-day induct before 2pm (toolkit)", "68.3%"),
            ("Orders before 2pm (toolkit)", "23,237"),
            ("Warehouses (US)", "13"),
        ],
    )

    _section_slide(
        prs,
        "Same-day induction before 2pm — the ops gap",
        [
            "Only 68% of before-2pm orders inducted same day network-wide",
            "Best: Carlisle PA 94% · Riverside CA 84% · Savannah GA 84%",
            "Worst: Easton PA 42% · NJ sites ~50% · Port Wentworth GA 51%",
            "Toolkit o2i_0 (business day) — not HVE 8am-adjusted metric",
            "2pm cutoff commitment requires FedEx pickup + warehouse processing alignment",
        ],
    )

    _warehouse_table_slide(prs)

    _scenario_slide(prs)

    _section_slide(
        prs,
        "Three policy levers",
        [
            "Zero cushion — lifts all tiers; largest at 2- and 3-day (+~14 pp)",
            "2:00 PM cutoff everywhere — Easton & Port Wentworth biggest uplift",
            "Weekend shipping — +4 pp at 3-day tier on top of policy",
            "Combined: ~12.5k newly 2-day and 3-day badged orders in June",
            "Fast badge (≤5d) only +2.2 pp — lead with 2/3-day story for CEO",
        ],
    )

    _section_slide(
        prs,
        "Discussion questions for the CEO",
        [
            "Can every DC match Carlisle's 94% same-day induction before 2pm?",
            "Will Safavieh standardize 2:00 PM cutoff and zero cushion network-wide?",
            "Is weekend shipping feasible at NJ and PA nodes?",
            "What FedEx pickup schedule runs at Easton, Lebanon, Port Wentworth today?",
            "What's driving NJ IFR weakness (Flemington 76%, Lebanon 82%)?",
        ],
    )

    _section_slide(
        prs,
        "Data & resources",
        [
            "Pre-read: github.com/et844p/O2S/blob/cursor/safavieh-ceo-preread-b7d6/docs/small_parcel/safavieh_ceo_meeting_preread.md",
            "Warehouse CSV: output/safavieh/safavieh_june_warehouse_analysis.csv",
            "SQL: sql/safavieh_june_msbd_warehouse_analysis.sql",
            "PR #16: github.com/et844p/O2S/pull/16",
        ],
    )

    prs.save(PPTX_PATH)
    return PPTX_PATH


def upload_to_google_slides(pptx_path: Path) -> str | None:
    if not CREDS_PATH.exists():
        return None
    os.environ.setdefault("GOOGLE_APPLICATION_CREDENTIALS", str(CREDS_PATH))
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    scopes = [
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/presentations",
    ]
    creds = service_account.Credentials.from_service_account_file(str(CREDS_PATH), scopes=scopes)
    drive = build("drive", "v3", credentials=creds)

    media = MediaFileUpload(
        str(pptx_path),
        mimetype="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        resumable=True,
    )
    meta = {
        "name": "Safavieh CEO — June MSBD Analysis",
        "mimeType": "application/vnd.google-apps.presentation",
    }
    file = drive.files().create(body=meta, media_body=media, fields="id,webViewLink").execute()
    file_id = file["id"]
    drive.permissions().create(
        fileId=file_id,
        body={"type": "anyone", "role": "reader"},
    ).execute()
    return file.get("webViewLink") or f"https://docs.google.com/presentation/d/{file_id}/edit"


def main() -> None:
    path = build_presentation()
    print(f"Created {path}")
    try:
        link = upload_to_google_slides(path)
        if link:
            print(f"Google Slides: {link}")
            (OUT_DIR / "google_slides_link.txt").write_text(link)
        else:
            raise RuntimeError("upload skipped")
    except Exception as e:
        print(f"Google upload not available ({e})")
        print(
            "Import to Google Slides:\n"
            "  1. Go to https://slides.google.com → Blank presentation\n"
            "  2. File → Import slides → Upload → select Safavieh_CEO_June_MSBD.pptx\n"
            "  Or: upload PPTX to Google Drive → Open with Google Slides"
        )


if __name__ == "__main__":
    main()
