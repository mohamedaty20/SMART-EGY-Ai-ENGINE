"""
services/inspection_service.py — Daily quality inspection plans.

OCR + AI extracts a table from an uploaded inspection plan, produces a
downloadable PDF, and carries suspended/rejected rows forward to the
next day. Table data is stored as JSON: {columns:[...], rows:[{cells,
status, note, defect_uid}]}.
"""
import io
import re
import json
import asyncio
import datetime

from services import defect_service as svc


_TABLE_PROMPT = """You are a QC data extraction specialist. You are reading a Daily Quality Inspection Plan (or similar site inspection sheet).

Extract the COMPLETE table exactly as it appears. Return ONE JSON object:

{
  "table_title": "Daily Quality Inspection Plan",
  "date_on_document": "YYYY-MM-DD or empty string if not shown",
  "columns": ["Floor", "Inspection", "Location", "Spec", "..."],
  "rows": [
    ["GF", "Column rebar inspection", "Axis 1-4", "ECP 203 §6.3"],
    ["1F", "Slab rebar inspection", "Grid A-C", ""]
  ]
}

RULES:
- Preserve column headers EXACTLY as they appear on the sheet.
- Every row MUST have the same number of values as `columns`. Pad with "" if missing.
- Do NOT invent data. If a cell is empty, use "".
- Do NOT add a status column — the app adds that later.
- MAX 300 rows.
- Output ONLY the JSON object. No prose. No markdown fences.

INSPECTION PLAN TEXT STARTS BELOW
--------
__TEXT__
--------
"""


def _parse_json(raw):
    if not raw:
        return None
    t = (raw or "").strip()
    t = re.sub(r'^```json\s*', '', t)
    t = re.sub(r'^```\s*', '', t)
    t = re.sub(r'\s*```$', '', t)
    s = t.find('{')
    e = t.rfind('}')
    if s == -1 or e == -1:
        return None
    try:
        return json.loads(t[s:e + 1])
    except Exception:
        return None


async def extract_inspection_table(file_bytes, filename, ocr_fn,
                                    call_gemini_json_fn):
    """Return {table_title, date_on_document, columns, rows, error}."""
    name = (filename or "").lower()
    text = ""
    try:
        if name.endswith(".pdf"):
            text = await asyncio.to_thread(
                svc.extract_pdf_text, file_bytes)
        elif name.endswith((".jpg", ".jpeg", ".png")):
            mime = ("image/jpeg" if name.endswith((".jpg", ".jpeg"))
                    else "image/png")
            text, err = await ocr_fn(file_bytes, mime)
            if err and not text:
                return {"error": "OCR failed: " + str(err)}
        else:
            text = await asyncio.to_thread(
                svc.extract_document_text, file_bytes, filename)
    except Exception as e:
        return {"error": "Extract failed: " + repr(e)}

    if not text or len(text.strip()) < 30:
        return {"error": "No readable text in the file."}

    prompt = _TABLE_PROMPT.replace("__TEXT__", text[:30000])
    try:
        raw = await call_gemini_json_fn(prompt, temperature=0.0,
                                          timeout=90, max_tokens=8192)
    except Exception as e:
        return {"error": "AI call failed: " + repr(e)}

    data = _parse_json(raw)
    if not data:
        return {"error": "AI returned unparseable output.",
                "raw": (raw or "")[:1000]}

    cols = [str(c) for c in (data.get("columns") or [])]
    raw_rows = data.get("rows") or []
    if not cols or not raw_rows:
        return {"error": "AI returned no table."}

    nc = len(cols)
    norm = []
    for r in raw_rows:
        r = list(r or [])
        if len(r) < nc:
            r = r + [""] * (nc - len(r))
        elif len(r) > nc:
            r = r[:nc]
        norm.append([str(x) for x in r])

    return {
        "table_title": str(data.get("table_title") or
                            "Quality Inspection Plan"),
        "date_on_document": str(data.get("date_on_document") or ""),
        "columns": cols,
        "rows": norm,
        "error": None,
    }


def merge_tables(existing, new_rows):
    """Append new_rows to existing table data, skipping exact dupes."""
    base_cols = list(existing.get("columns") or [])
    new_cols = list(existing.get("columns") or [])
    old_rows = list(existing.get("rows") or [])
    seen = set()
    for r in old_rows:
        key = tuple(str(c) for c in (r.get("cells") or []))
        seen.add(key)
    added = 0
    for cells in new_rows:
        key = tuple(str(c) for c in cells)
        if key in seen:
            continue
        old_rows.append({"cells": [str(c) for c in cells],
                          "status": "", "note": "", "defect_uid": ""})
        seen.add(key)
        added += 1
    return {"columns": base_cols or new_cols, "rows": old_rows,
            "added": added}


# ---------------------------------------------------------------------
# PDF EXPORT
# ---------------------------------------------------------------------
def _ensure():
    try:
        svc._ensure_fonts()
    except Exception:
        pass


def _esc(s):
    return (str(s or "").replace("&", "&amp;")
            .replace("<", "&lt;").replace(">", "&gt;"))


def build_inspection_pdf(project, date_str, table_data):
    _ensure()
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                     Table, TableStyle, HRFlowable)
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.units import mm

    mono = getattr(svc, "_MONO_NAME", "Courier")
    mono_b = getattr(svc, "_MONO_BOLD", "Courier-Bold")

    NAVY = colors.HexColor("#0a0a0a")
    ACCENT = colors.HexColor("#14b8a6")
    GREEN = colors.HexColor("#16a34a")
    AMBER = colors.HexColor("#d97706")
    RED = colors.HexColor("#dc2626")
    GREY = colors.HexColor("#525252")

    title_style = ParagraphStyle("T", fontName=mono_b, fontSize=13,
                                  textColor=NAVY, spaceAfter=2)
    sub_style = ParagraphStyle("S", fontName=mono, fontSize=9,
                                textColor=ACCENT, spaceAfter=6)
    cell_style = ParagraphStyle("C", fontName=mono, fontSize=8,
                                 textColor=colors.black, leading=10)
    head_style = ParagraphStyle("H", fontName=mono_b, fontSize=8,
                                 textColor=colors.white, leading=10)
    small_style = ParagraphStyle("Sm", fontName=mono, fontSize=7,
                                  textColor=GREY, leading=9)

    cols = list(table_data.get("columns") or [])
    rows = list(table_data.get("rows") or [])

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4),
                            leftMargin=14 * mm, rightMargin=14 * mm,
                            topMargin=14 * mm, bottomMargin=14 * mm)

    story = []
    story.append(Paragraph("DAILY QUALITY INSPECTION PLAN", title_style))
    story.append(Paragraph(
        _esc(str(project.get("name") or "")) + "  ·  Date: " +
        _esc(date_str), sub_style))
    story.append(HRFlowable(width="100%", thickness=0.8, color=ACCENT,
                             spaceAfter=10))

    head = [Paragraph("<b>" + _esc(c) + "</b>", head_style) for c in cols]
    head += [Paragraph("<b>Status</b>", head_style),
             Paragraph("<b>Note</b>", head_style)]

    data = [head]
    for r in rows:
        cells = list(r.get("cells") or [])
        if len(cells) < len(cols):
            cells = cells + [""] * (len(cols) - len(cells))
        elif len(cells) > len(cols):
            cells = cells[:len(cols)]
        status = str(r.get("status") or "").upper()
        note = str(r.get("note") or "")
        row_p = [Paragraph(_esc(c), cell_style) for c in cells]
        st_style = cell_style
        if status == "ACCEPTED":
            st_style = ParagraphStyle("sa", parent=cell_style,
                                       textColor=GREEN, fontName=mono_b)
        elif status == "SUSPENDED":
            st_style = ParagraphStyle("ss", parent=cell_style,
                                       textColor=AMBER, fontName=mono_b)
        elif status == "REJECTED":
            st_style = ParagraphStyle("sr", parent=cell_style,
                                       textColor=RED, fontName=mono_b)
        row_p.append(Paragraph(status or "—", st_style))
        row_p.append(Paragraph(_esc(note), cell_style))
        data.append(row_p)

    ncols = len(cols) + 2
    total_mm = 268
    if len(cols) > 0:
        each = max(20, int((total_mm - 60) / len(cols)))
    else:
        each = 40
    col_w = [each * mm] * len(cols) + [26 * mm, 60 * mm]

    t = Table(data, colWidths=col_w, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#F5F5F5")]),
        ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor("#BFBFBF")),
    ]))
    story.append(t)
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "Generated " + datetime.date.today().strftime("%Y-%m-%d"),
        small_style))

    doc.build(story)
    buf.seek(0)
    return buf.read()
