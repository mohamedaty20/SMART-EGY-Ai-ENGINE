"""
services/defect_service.py — Complete file.
AI logic + PDF generation for the Defect Notice tool.
"""

import io
import re
import json
import uuid
import datetime
import asyncio


# =====================================================================
# UID
# =====================================================================
def generate_uid(prefix="NTC"):
    short = uuid.uuid4().hex[:4].upper()
    year = datetime.date.today().year
    seq = uuid.uuid4().int % 10000
    return prefix + "-" + short + "-" + str(year) + "-" + str(seq).zfill(4)


# =====================================================================
# PDF TEXT EXTRACTION
# =====================================================================
def extract_pdf_text(pdf_bytes, max_pages=30, max_chars=40000):
    try:
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        parts = []
        for i in range(min(max_pages, len(reader.pages))):
            try:
                parts.append(reader.pages[i].extract_text() or "")
            except Exception:
                pass
        return "\n".join(parts)[:max_chars]
    except Exception as e:
        print("[defect] pdf text extraction failed: " + repr(e))
        return ""


# =====================================================================
# MS CLAUSE EXTRACTION
# =====================================================================
_CLAUSE_PROMPT_TEMPLATE = """You are reading a construction Method Statement (MS).

Task: extract the CLAUSE STRUCTURE from the text below.

Return ONE JSON object with this exact shape:
{
  "clauses": [
    {"id": "3.1", "title": "Bar Spacing", "text": "as per approved shop drawings"},
    {"id": "3.2", "title": "Cover",       "text": "minimum 40mm for columns, 25mm for slabs"}
  ]
}

RULES:
- Return EVERY numbered clause you can find, no matter the numbering style.
- The "id" field is the clause number ONLY, as a string.
- The "title" is a short name (1-5 words).
- The "text" field is the clause body, trimmed to at most 200 characters.
- Ignore the MS title page, revision history, and signature blocks.
- MAX 60 clauses. Prioritize the ones with measurable requirements.
- Output ONLY the JSON object. No prose. No markdown fences.

Method Statement text starts below.
--------
{ms_text}
--------
"""


def _strip_fences(txt):
    t = (txt or "").strip()
    t = re.sub(r'^```json\s*', '', t)
    t = re.sub(r'^```\s*', '', t)
    t = re.sub(r'\s*```$', '', t)
    return t


def _parse_json_object(raw):
    if not raw:
        return None
    txt = _strip_fences(raw)
    start = txt.find('{')
    end = txt.rfind('}')
    if start == -1 or end == -1:
        return None
    try:
        return json.loads(txt[start:end + 1])
    except Exception as e:
        print("[defect] JSON parse failed: " + repr(e))
        return None


async def extract_clauses_from_pdf(pdf_bytes, call_gemini_json_fn):
    import asyncio

    print("[defect] MS extraction started, pdf_bytes=" +
          str(len(pdf_bytes) // 1024) + " KB")

    # Run PDF parsing in a thread — never blocks the event loop
    try:
        text = await asyncio.to_thread(extract_pdf_text, pdf_bytes)
    except Exception as e:
        print("[defect] pdf parse failed: " + repr(e))
        return {
            "clauses": [],
            "raw_text_length": 0,
            "error": "PDF parse failed: " + repr(e),
        }

    print("[defect] extracted " + str(len(text)) + " chars from PDF")

    if not text or len(text) < 100:
        return {
            "clauses": [],
            "raw_text_length": len(text),
            "error": "PDF has no readable text (may be scanned image).",
        }

    # Cap the text so we don't send a 40KB monster prompt
    text = text[:15000]
    print("[defect] sending " + str(len(text)) + " chars to Gemini")

    prompt = _CLAUSE_PROMPT_TEMPLATE.replace("{ms_text}", text)

    try:
        raw = await call_gemini_json_fn(prompt, temperature=0.0, timeout=40)
    except Exception as e:
        print("[defect] AI call failed: " + repr(e))
        return {
            "clauses": [],
            "raw_text_length": len(text),
            "error": "AI call failed: " + repr(e),
        }

    print("[defect] AI responded, " + str(len(raw or "")) + " chars")

    data = _parse_json_object(raw)
    if not data:
        return {
            "clauses": [],
            "raw_text_length": len(text),
            "error": "AI returned unparseable output.",
        }

    clauses = []
    for c in data.get("clauses", []):
        cid = str(c.get("id", "")).strip()
        title = str(c.get("title", "")).strip()[:80]
        body = str(c.get("text", "")).strip()[:300]
        if not cid or not title:
            continue
        clauses.append({"id": cid, "title": title, "text": body})

    print("[defect] extracted " + str(len(clauses)) + " clauses from MS")
    return {
        "clauses": clauses,
        "raw_text_length": len(text),
        "error": None,
    }


# =====================================================================
# HARDCODED ECP EXCERPTS
# =====================================================================
_ECP_BY_ELEMENT = {
    "column": [
        {"code": "ECP 203 §6.3.1",
         "text": "Minimum concrete cover for columns is 40 mm."},
        {"code": "ECP 203 §6.3.4",
         "text": "Lap length for tension bars is 40 x bar diameter minimum."},
        {"code": "ECP 203 §7.2.1",
         "text": "Column ties spacing shall not exceed the least of: 16x longitudinal bar dia, 48x tie dia, or the least column dimension."},
        {"code": "ECP 203 §4.5.2",
         "text": "Concrete shall be compacted by mechanical vibration. Honeycombing or voids are not permitted."},
    ],
    "beam": [
        {"code": "ECP 203 §6.3.1",
         "text": "Minimum concrete cover for beams is 25 mm (slabs) or 40 mm (exposed to weather)."},
        {"code": "ECP 203 §6.3.4",
         "text": "Lap length for tension bars is 40 x bar diameter minimum."},
        {"code": "ECP 203 §4.5.2",
         "text": "Concrete shall be compacted by mechanical vibration. Honeycombing or voids are not permitted."},
    ],
    "slab": [
        {"code": "ECP 203 §6.3.1",
         "text": "Minimum concrete cover for slabs is 25 mm."},
        {"code": "ECP 203 §6.3.4",
         "text": "Lap length for tension bars is 40 x bar diameter minimum."},
        {"code": "ECP 203 §6.5.1",
         "text": "Slab thickness shall not be less than 100 mm for solid slabs."},
    ],
    "wall": [
        {"code": "ECP 203 §6.3.1",
         "text": "Minimum cover for walls is 25 mm."},
        {"code": "ECP 203 §4.5.2",
         "text": "Concrete shall be compacted by mechanical vibration. Honeycombing or voids are not permitted."},
    ],
    "foundation": [
        {"code": "ECP 203 §8.2.1",
         "text": "Minimum cover for foundation elements is 50 mm."},
        {"code": "ECP 203 §8.3.4",
         "text": "Reinforcement in footings shall be placed on chairs at the designed level before concreting."},
    ],
    "finishing": [
        {"code": "ECP 203 §9.1",
         "text": "Plaster thickness shall be uniform and not less than 15 mm."},
    ],
}


def get_ecp_excerpts(element_type):
    key = (element_type or "").lower().strip()
    return _ECP_BY_ELEMENT.get(key, _ECP_BY_ELEMENT.get("column", []))


# =====================================================================
# DEFECT ANALYSIS
# =====================================================================
_DEFECT_PROMPT = """You are a senior QC engineer inspecting a construction site photo.

Your job: identify defects visible in the photo, and cite ONLY the
provided MS clauses and ECP codes. Never invent clause numbers.

USER NOTE (may be empty): {note}

ELEMENT TYPE: {element_type}

METHOD STATEMENT CLAUSES AVAILABLE (cite by id only):
{ms_clauses}

ECP CODE EXCERPTS AVAILABLE (cite by code string only):
{ecp_excerpts}

Return ONE JSON object with this exact shape:
{{
  "defects": [
    {{
      "name": "Honeycomb on column face",
      "location_hint": "column base",
      "severity": "Medium",
      "ms_violations": ["3.5"],
      "code_violations": ["ECP 203 §6.3.1"],
      "repair_action": "Chip back to sound concrete, apply bonding agent, patch with non-shrink mortar."
    }}
  ]
}}

RULES:
- MAX 6 defects.
- Only cite MS clause ids that appear in the list above.
- Only cite ECP codes that appear in the list above.
- If the photo shows no clear defect, return {"defects": []}.
- Severity must be one of: Low, Medium, High, Critical.
- Output ONLY the JSON. No prose. No markdown fences.
"""


def _format_ms_clauses(ms_clauses):
    if not ms_clauses:
        return "(none provided)"
    lines = []
    for c in ms_clauses[:30]:
        lines.append("  id=" + str(c.get("id", "?")) +
                     " - " + str(c.get("title", "")) +
                     " : " + str(c.get("text", ""))[:120])
    return "\n".join(lines)


def _format_ecp(ecp_excerpts):
    if not ecp_excerpts:
        return "(none provided)"
    return "\n".join("  " + e["code"] + " - " + e["text"]
                     for e in ecp_excerpts[:10])


async def analyze_defect_photo(photo_bytes,
                                mime_type,
                                note,
                                ms_clauses,
                                element_type,
                                call_gemini_json_fn):
    from google.genai import types

    ecp_excerpts = get_ecp_excerpts(element_type)

    prompt = _DEFECT_PROMPT.format(
        note=note or "(none)",
        element_type=(element_type or "column").lower(),
        ms_clauses=_format_ms_clauses(ms_clauses),
        ecp_excerpts=_format_ecp(ecp_excerpts),
    )

    try:
        img_part = types.Part.from_bytes(data=photo_bytes, mime_type=mime_type)
    except Exception as e:
        return {"defects": [], "error": "Image load failed: " + repr(e)}

    contents = [prompt, img_part]

    try:
        raw = await call_gemini_json_fn(contents, temperature=0.0, timeout=180)
    except Exception as e:
        return {"defects": [], "error": "AI call failed: " + repr(e)}

    print("[defect] RAW AI RESPONSE:")
    print((raw or "")[:2500])

    data = _parse_json_object(raw)
    if not data:
        return {"defects": [], "error": "AI returned unparseable output."}

    allowed_ms = {str(c.get("id", "")).strip() for c in (ms_clauses or [])}
    allowed_ecp = {e["code"] for e in ecp_excerpts}

    defects = []
    for d in data.get("defects", [])[:6]:
        name = str(d.get("name", "")).strip()[:120]
        if not name:
            continue
        ms_v = [str(v).strip() for v in (d.get("ms_violations") or [])]
        ms_v = [v for v in ms_v if v in allowed_ms][:3]
        ecp_v = [str(v).strip() for v in (d.get("code_violations") or [])]
        ecp_v = [v for v in ecp_v if v in allowed_ecp][:3]
        severity = str(d.get("severity", "Medium")).strip().title()
        if severity not in ("Low", "Medium", "High", "Critical"):
            severity = "Medium"
        defects.append({
            "name": name,
            "location_hint": str(d.get("location_hint", "")).strip()[:60],
            "severity": severity,
            "ms_violations": ms_v,
            "code_violations": ecp_v,
            "repair_action": str(d.get("repair_action", "")).strip()[:180],
        })

    print("[defect] parsed " + str(len(defects)) + " valid defects")
    return {"defects": defects, "error": None}


# =====================================================================
# NOTICE PDF
# =====================================================================
def build_notice_pdf(project,
                     defects,
                     notice_uid,
                     subcontractor,
                     deadline_days,
                     raise_type="qc_internal",
                     logo_bytes=None):
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        Image as ReportLabImage, HRFlowable,
    )
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=18 * mm, bottomMargin=18 * mm,
    )

    NAVY = colors.HexColor("#1B2A4A")
    ORANGE = colors.HexColor("#B45309")
    GREY = colors.HexColor("#334155")

    title_style = ParagraphStyle("Title", fontName="Helvetica-Bold",
                                  fontSize=16, textColor=NAVY,
                                  spaceAfter=4, leading=20)
    sub_style = ParagraphStyle("Sub", fontName="Helvetica-Bold",
                                fontSize=10, textColor=ORANGE, spaceAfter=8)
    meta_style = ParagraphStyle("Meta", fontName="Helvetica", fontSize=9,
                                 textColor=GREY, leading=13)
    body_style = ParagraphStyle("Body", fontName="Helvetica", fontSize=9.5,
                                 textColor=colors.black, leading=13)
    label_style = ParagraphStyle("Label", fontName="Helvetica-Bold",
                                  fontSize=9, textColor=NAVY)

    story = []

    if logo_bytes:
        try:
            logo_img = ReportLabImage(io.BytesIO(logo_bytes),
                                       width=30 * mm, height=15 * mm)
        except Exception:
            logo_img = ""
    else:
        logo_img = ""

    header_text = [
        Paragraph("NOTICE TO SUBCONTRACTOR", title_style),
        Paragraph("Notice No: " + notice_uid, sub_style),
    ]

    if logo_img:
        t_head = Table([[logo_img, header_text]],
                       colWidths=[35 * mm, 145 * mm])
    else:
        t_head = Table([[header_text]], colWidths=[180 * mm])
    t_head.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(t_head)
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=1.2, color=ORANGE,
                             spaceAfter=10))

    meta_rows = [
        [Paragraph("<b>Project:</b>", label_style),
         Paragraph(project.get("name", ""), meta_style),
         Paragraph("<b>Date:</b>", label_style),
         Paragraph(datetime.date.today().strftime("%Y-%m-%d"), meta_style)],
        [Paragraph("<b>Contractor:</b>", label_style),
         Paragraph(project.get("contractor", ""), meta_style),
         Paragraph("<b>Location:</b>", label_style),
         Paragraph(project.get("location", ""), meta_style)],
        [Paragraph("<b>Consultant:</b>", label_style),
         Paragraph(project.get("consultant", ""), meta_style),
         Paragraph("<b>Raised as:</b>", label_style),
         Paragraph("QC Internal" if raise_type == "qc_internal"
                   else "Consultant / NCR", meta_style)],
    ]
    t_meta = Table(meta_rows,
                   colWidths=[22 * mm, 68 * mm, 25 * mm, 65 * mm])
    t_meta.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>To:</b> " + subcontractor, body_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "<b>Deadline:</b> " + str(deadline_days) + " working day" +
        ("s" if deadline_days != 1 else "") + " from receipt of this notice.",
        body_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "You are required to remedy the following defects. "
        "This notice is a permanent record and must be acknowledged on site.",
        body_style))
    story.append(Spacer(1, 12))

    for idx, d in enumerate(defects, start=1):
        name = d.get("name", "Defect")
        zone = d.get("zone", "") or ""
        loc = d.get("location_hint", "") or ""
        severity = d.get("severity", "Medium")
        ms_v = d.get("ms_violations") or []
        ecp_v = d.get("code_violations") or []
        repair = d.get("repair_action", "") or ""

        head = str(idx) + ". " + name
        if zone or loc:
            head += "  (" + ", ".join(p for p in [zone, loc] if p) + ")"
        story.append(Paragraph("<b>" + head + "</b>", body_style))

        cit_bits = []
        if ms_v:
            cit_bits.append("MS: " + ", ".join(ms_v))
        if ecp_v:
            cit_bits.append("Code: " + ", ".join(ecp_v))
        if cit_bits:
            story.append(Paragraph("  <i>" + "  |  ".join(cit_bits) + "</i>",
                                    meta_style))
        if repair:
            story.append(Paragraph("  Repair: " + repair, meta_style))
        story.append(Paragraph("  Severity: " + severity, meta_style))
        story.append(Spacer(1, 8))

    story.append(Spacer(1, 20))

    sig_data = [
        [Paragraph("<b>Issued by (QC):</b>", label_style),
         Paragraph("<b>Acknowledged by (Subcontractor):</b>", label_style)],
        [Paragraph("_" * 30, body_style),
         Paragraph("_" * 30, body_style)],
        [Paragraph(project.get("engineer_name", ""), meta_style),
         Paragraph("Name / Date / Signature", meta_style)],
    ]
    t_sig = Table(sig_data, colWidths=[90 * mm, 90 * mm])
    t_sig.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(t_sig)
    story.append(Spacer(1, 14))

    try:
        from services.pdf_service import generate_qr_code
        qr_buf = generate_qr_code(
            "UID: " + notice_uid + " | Defect Notice | " +
            project.get("name", "")
        )
        qr_img = ReportLabImage(qr_buf, width=20 * mm, height=20 * mm)
        t_qr = Table([[qr_img,
                       Paragraph("<b>UID:</b> " + notice_uid + "<br/>" +
                                 "This notice can be verified by scanning " +
                                 "the QR code.", meta_style)]],
                      colWidths=[25 * mm, 155 * mm])
        t_qr.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ]))
        story.append(t_qr)
    except Exception as e:
        print("[defect] QR embed failed: " + repr(e))
        story.append(Paragraph("UID: " + notice_uid, meta_style))

    doc.build(story)
    buf.seek(0)
    return buf.read()
