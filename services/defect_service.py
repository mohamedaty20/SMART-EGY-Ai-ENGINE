"""
services/defect_service.py — Full file.
PDFs use JetBrains Mono for all Latin text; Arabic uses Amiri.
"""

import io
import os
import re
import json
import uuid
import datetime
import asyncio


# =====================================================================
# FONTS
# =====================================================================
_FONT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")

_FONT_REG_PATH = os.path.join(_FONT_DIR, "Amiri-Regular.ttf")
_FONT_BOLD_PATH = os.path.join(_FONT_DIR, "Amiri-Bold.ttf")
_FONT_REG_URLS = [
    "https://github.com/google/fonts/raw/main/ofl/amiri/Amiri-Regular.ttf",
    "https://github.com/aliftype/amiri/raw/main/Amiri-Regular.ttf",
]
_FONT_BOLD_URLS = [
    "https://github.com/google/fonts/raw/main/ofl/amiri/Amiri-Bold.ttf",
    "https://github.com/aliftype/amiri/raw/main/Amiri-Bold.ttf",
]

_MONO_REG_PATH = os.path.join(_FONT_DIR, "JetBrainsMono-Regular.ttf")
_MONO_BOLD_PATH = os.path.join(_FONT_DIR, "JetBrainsMono-Bold.ttf")
_MONO_REG_URLS = [
    "https://github.com/JetBrains/JetBrainsMono/raw/master/fonts/ttf/JetBrainsMono-Regular.ttf",
    "https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSansMono.ttf",
]
_MONO_BOLD_URLS = [
    "https://github.com/JetBrains/JetBrainsMono/raw/master/fonts/ttf/JetBrainsMono-Bold.ttf",
    "https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSansMono-Bold.ttf",
]

_FONT_NAME = "Helvetica"
_FONT_BOLD = "Helvetica-Bold"
_MONO_NAME = "Courier"
_MONO_BOLD = "Courier-Bold"


def _download_font(url, dest):
    import urllib.request
    try:
        os.makedirs(_FONT_DIR, exist_ok=True)
    except Exception:
        pass
    try:
        print("[defect] fetching font: " + url)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = r.read()
        if data and len(data) > 10000:
            with open(dest, "wb") as f:
                f.write(data)
            print("[defect] font saved: " + str(len(data) // 1024) +
                  " KB -> " + dest)
            return True
    except Exception as e:
        print("[defect] font fetch failed: " + repr(e))
    return False


def _ensure_fonts():
    global _FONT_NAME, _FONT_BOLD, _MONO_NAME, _MONO_BOLD
    if _FONT_NAME != "Helvetica" and _MONO_NAME != "Courier":
        return
    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
    except Exception as e:
        print("[defect] reportlab font import failed: " + repr(e))
        return

    if not os.path.exists(_FONT_REG_PATH):
        for u in _FONT_REG_URLS:
            if _download_font(u, _FONT_REG_PATH):
                break
    if not os.path.exists(_FONT_BOLD_PATH):
        for u in _FONT_BOLD_URLS:
            if _download_font(u, _FONT_BOLD_PATH):
                break
    try:
        if os.path.exists(_FONT_REG_PATH):
            pdfmetrics.registerFont(TTFont("ArReg", _FONT_REG_PATH))
            _FONT_NAME = "ArReg"
        if os.path.exists(_FONT_BOLD_PATH):
            pdfmetrics.registerFont(TTFont("ArBold", _FONT_BOLD_PATH))
            _FONT_BOLD = "ArBold"
        else:
            _FONT_BOLD = _FONT_NAME
    except Exception as e:
        print("[defect] Amiri registration failed: " + repr(e))

    if not os.path.exists(_MONO_REG_PATH):
        for u in _MONO_REG_URLS:
            if _download_font(u, _MONO_REG_PATH):
                break
    if not os.path.exists(_MONO_BOLD_PATH):
        for u in _MONO_BOLD_URLS:
            if _download_font(u, _MONO_BOLD_PATH):
                break
    try:
        if os.path.exists(_MONO_REG_PATH):
            pdfmetrics.registerFont(TTFont("MonoReg", _MONO_REG_PATH))
            _MONO_NAME = "MonoReg"
        if os.path.exists(_MONO_BOLD_PATH):
            pdfmetrics.registerFont(TTFont("MonoBold", _MONO_BOLD_PATH))
            _MONO_BOLD = "MonoBold"
        else:
            _MONO_BOLD = _MONO_NAME
    except Exception as e:
        print("[defect] Mono registration failed: " + repr(e))

    print("[defect] fonts ready: body=" + _FONT_NAME + " mono=" + _MONO_NAME)


_ensure_fonts()


def _has_arabic(text):
    return any('\u0600' <= ch <= '\u06FF' for ch in str(text or ""))


def _fix(text):
    if text is None:
        return ""
    s = str(text)
    if not s:
        return s
    try:
        if not _has_arabic(s):
            return s
        import arabic_reshaper
        from bidi.algorithm import get_display
        return get_display(arabic_reshaper.reshape(s))
    except Exception as e:
        print("[defect] arabic shaping failed: " + repr(e))
        return s


def _font_for(text, bold=False):
    if _has_arabic(text):
        return _FONT_BOLD if bold else _FONT_NAME
    return _MONO_BOLD if bold else _MONO_NAME


_style_counter = [0]


def _style_for(text, base_style, bold=False):
    _style_counter[0] += 1
    try:
        from reportlab.lib.styles import ParagraphStyle
    except Exception:
        return base_style
    return ParagraphStyle(
        "s" + str(_style_counter[0]),
        parent=base_style,
        fontName=_font_for(text, bold=bold))


def _para(text, base_style, bold=False):
    from reportlab.platypus import Paragraph
    t = _fix(text or "")
    return Paragraph(t, _style_for(t, base_style, bold=bold))


# =====================================================================
# UID
# =====================================================================
def generate_uid(prefix="NTC"):
    short = uuid.uuid4().hex[:4].upper()
    year = datetime.date.today().year
    seq = uuid.uuid4().int % 10000
    return prefix + "-" + short + "-" + str(year) + "-" + str(seq).zfill(4)


# =====================================================================
# IMAGE COMPRESSION
# =====================================================================
def _shrink_image(photo_bytes, max_side=1024):
    try:
        from PIL import Image
        img = Image.open(io.BytesIO(photo_bytes))
        if img.mode != "RGB":
            img = img.convert("RGB")
        w, h = img.size
        if max(w, h) > max_side:
            ratio = max_side / float(max(w, h))
            img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)
        out = io.BytesIO()
        img.save(out, format="JPEG", quality=80, optimize=True)
        out.seek(0)
        return out.read()
    except Exception as e:
        print("[defect] image shrink failed: " + repr(e))
        return photo_bytes


def _detect_image_type(data):
    if not data or len(data) < 8:
        return None
    if data[:3] == b'\xff\xd8\xff':
        return "jpeg"
    if data[:8] == b'\x89PNG\r\n\x1a\n':
        return "png"
    return None


# =====================================================================
# DOCUMENT TEXT EXTRACTION
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


def extract_docx_text(docx_bytes, max_chars=40000):
    try:
        from docx import Document
        doc = Document(io.BytesIO(docx_bytes))
        parts = []
        for para in doc.paragraphs:
            if para.text and para.text.strip():
                parts.append(para.text)
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    if cell.text and cell.text.strip():
                        parts.append(cell.text)
        return "\n".join(parts)[:max_chars]
    except Exception as e:
        print("[defect] docx text extraction failed: " + repr(e))
        return ""


def extract_txt_text(txt_bytes, max_chars=40000):
    for enc in ("utf-8", "utf-16", "latin-1"):
        try:
            return txt_bytes.decode(enc)[:max_chars]
        except Exception:
            continue
    return ""


def extract_document_text(file_bytes, filename=None, max_chars=40000):
    name = (filename or "").lower().strip()
    if name.endswith(".pdf"):
        return extract_pdf_text(file_bytes, max_chars=max_chars)
    if name.endswith(".docx"):
        return extract_docx_text(file_bytes, max_chars=max_chars)
    if name.endswith(".doc"):
        print("[defect] .doc legacy format is not supported; use .docx")
        return ""
    if name.endswith(".txt") or name.endswith(".md"):
        return extract_txt_text(file_bytes, max_chars=max_chars)
    t = extract_pdf_text(file_bytes, max_chars=max_chars)
    if t and len(t) > 100:
        return t
    return extract_txt_text(file_bytes, max_chars=max_chars)


# =====================================================================
# JSON HELPERS
# =====================================================================
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


# =====================================================================
# MS CLAUSE EXTRACTION
# =====================================================================
_CLAUSE_PROMPT_TEMPLATE = """You are reading a construction Method Statement (MS).

Task: extract the CLAUSE STRUCTURE from the text below.

Return ONE JSON object with this exact shape:
{
  "clauses": [
    {"id": "3.1", "title": "Bar Spacing", "text": "as per approved shop drawings"},
    {"id": "3.2", "title": "Cover", "text": "minimum 40mm for columns, 25mm for slabs"}
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
__MS_TEXT__
--------
"""


async def extract_clauses_from_pdf(pdf_bytes, call_gemini_json_fn,
                                    filename=None):
    print("[defect] MS extraction started, bytes=" +
          str(len(pdf_bytes) // 1024) + " KB, file=" + str(filename))

    try:
        text = await asyncio.to_thread(
            extract_document_text, pdf_bytes, filename)
    except Exception as e:
        print("[defect] document parse failed: " + repr(e))
        return {"clauses": [], "raw_text_length": 0,
                "error": "Document parse failed: " + repr(e)}

    if not text or len(text) < 100:
        return {"clauses": [], "raw_text_length": len(text),
                "error": "File has no readable text. If this is a .doc "
                         "(legacy), save it as .docx and re-upload."}

    text = text[:15000]
    prompt = _CLAUSE_PROMPT_TEMPLATE.replace("__MS_TEXT__", text)

    try:
        raw = await call_gemini_json_fn(prompt, temperature=0.0, timeout=40)
    except Exception as e:
        print("[defect] AI call failed: " + repr(e))
        return {"clauses": [], "raw_text_length": len(text),
                "error": "AI call failed: " + repr(e)}

    data = _parse_json_object(raw)
    if not data:
        return {"clauses": [], "raw_text_length": len(text),
                "error": "AI returned unparseable output."}

    clauses = []
    for c in data.get("clauses", []):
        cid = str(c.get("id", "")).strip()
        title = str(c.get("title", "")).strip()[:80]
        body = str(c.get("text", "")).strip()[:300]
        if not cid or not title:
            continue
        clauses.append({"id": cid, "title": title, "text": body})

    print("[defect] extracted " + str(len(clauses)) + " clauses")
    return {"clauses": clauses, "raw_text_length": len(text), "error": None}


# =====================================================================
# ECP EXCERPTS
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


# =====================================================================
# DEFECT ANALYSIS — PHOTO
# =====================================================================
_DEFECT_PROMPT = """You are a senior QC engineer inspecting a construction site photo.

Your job: identify visible defects in the photo, and cite MS clauses / ECP
codes ONLY when they truly apply to what the photo shows.

CRITICAL — MATCHING RULE (read this before citing anything):
Before citing any MS clause, ask yourself: does this clause describe work
that relates to the ACTUAL content of the photo?

Examples of NON-matches (DO NOT cite any clause in these cases):
- MS is about masonry walls but the photo shows an asphalt pavement crack
- MS is about column reinforcement but the photo shows a floor slab
- MS is about concrete works but the photo shows electrical conduit
- MS is about steel structure but the photo shows plaster finishing

When the MS clauses do NOT match the photo content:
- STILL describe the defect(s) you see, in plain language
- Set "ms_violations" to an empty array []
- Set "code_violations" to an empty array []
- Set "context_mismatch" to true on that defect

When the MS clauses DO match the photo:
- Cite 1-3 MS clause ids that appear in the provided list
- Cite 1-3 ECP codes that appear in the provided list
- Set "context_mismatch" to false

NEVER invent a clause match. It is far better to return zero citations than
a wrong one.

OBSERVATION CHECKLIST — look for these in the photo:
- Cracks (any pattern, direction, width)
- Honeycombing / voids / poor compaction
- Exposed or corroded reinforcement
- Insufficient concrete cover
- Poor formwork (bulging, misalignment, seepage marks)
- Cold joints, segregation, aggregate exposure
- Water stains, efflorescence, damp patches
- Spalling, chips, broken edges
- Poor finishing, uneven surfaces
- Missing or misplaced spacers/chairs
- Rust stains on concrete surface
- Missing mortar joints, damaged masonry units

If the photo shows no construction defect at all, return an empty list.

USER NOTE (may be empty): __NOTE__

ELEMENT TYPE (from the app): __ELEMENT__

METHOD STATEMENT CLAUSES AVAILABLE (cite by id only):
__MS_CLAUSES__

ECP CODE EXCERPTS AVAILABLE (cite by code string only):
__ECP__

Return ONE JSON object with this exact shape:
{
  "defects": [
    {
      "name": "Honeycomb on column face",
      "location_hint": "column base",
      "severity": "Medium",
      "ms_violations": ["3.5"],
      "code_violations": ["ECP 203 §6.3.1"],
      "repair_action": "Chip back to sound concrete, apply bonding agent, patch with non-shrink mortar.",
      "context_mismatch": false
    }
  ]
}

RULES:
- Report 1-6 defects. Aim for at least 1 if any structure is visible.
- Only cite MS clause ids that appear in the list above.
- Only cite ECP codes that appear in the list above.
- Severity must be one of: Low, Medium, High, Critical.
- Output ONLY the JSON. No prose. No markdown fences.
"""


def _build_defect_prompt(note, element_type, ms_clauses, ecp_excerpts):
    return (_DEFECT_PROMPT
            .replace("__NOTE__", note or "(none)")
            .replace("__ELEMENT__", (element_type or "column").lower())
            .replace("__MS_CLAUSES__", _format_ms_clauses(ms_clauses))
            .replace("__ECP__", _format_ecp(ecp_excerpts)))


async def analyze_defect_photo(photo_bytes,
                                mime_type,
                                note,
                                ms_clauses,
                                element_type,
                                call_gemini_json_fn):
    from google.genai import types

    img_type = _detect_image_type(photo_bytes)
    if img_type is None:
        return {"defects": [], "error": "Uploaded file is not a JPEG or PNG "
                                        "photo. Please upload a site photo."}

    ecp_excerpts = get_ecp_excerpts(element_type)
    prompt = _build_defect_prompt(note, element_type, ms_clauses, ecp_excerpts)

    shrunk = _shrink_image(photo_bytes, max_side=1024)

    try:
        img_part = types.Part.from_bytes(data=shrunk, mime_type="image/jpeg")
    except Exception as e:
        return {"defects": [], "error": "Image load failed: " + repr(e)}

    contents = [prompt, img_part]

    try:
        raw = await call_gemini_json_fn(contents, temperature=0.0, timeout=40)
    except Exception as e:
        return {"defects": [], "error": "AI call failed: " + repr(e)}

    data = _parse_json_object(raw)
    if not data:
        return {"defects": [], "error": "AI returned unparseable output.",
                "raw": (raw or "")[:1500]}

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
        mismatch = bool(d.get("context_mismatch", False))
        if not ms_v and not ecp_v:
            mismatch = True
        defects.append({
            "name": name,
            "location_hint": str(d.get("location_hint", "")).strip()[:60],
            "severity": severity,
            "ms_violations": ms_v,
            "code_violations": ecp_v,
            "repair_action": str(d.get("repair_action", "")).strip()[:180],
            "context_mismatch": mismatch,
        })

    return {"defects": defects, "error": None, "raw": (raw or "")[:1500]}


# =====================================================================
# DEFECT ANALYSIS — TEXT ONLY
# =====================================================================
_DEFECT_TEXT_PROMPT = """You are a senior QC engineer reviewing a defect description
that a site engineer wrote in the field. There is no photo — the engineer
saw the defect and typed a description.

Your job: turn that description into a structured defect, and match it
against the available MS clauses / ECP codes.

CRITICAL — MATCHING RULE:
Before citing any MS clause, ask: does this clause describe work that relates
to the ACTUAL content of the description?

When the MS clauses do NOT match the description:
- STILL return the defect as the engineer described
- Set "ms_violations" to an empty array []
- Set "code_violations" to an empty array []
- Set "context_mismatch" to true

When the MS clauses DO match:
- Cite 1-3 MS clause ids that appear in the provided list
- Cite 1-3 ECP codes that appear in the provided list
- Set "context_mismatch" to false

NEVER invent a clause match. Empty citations are far better than wrong ones.

ENGINEER'S DEFECT DESCRIPTION (this is the source of truth):
__DESC__

OPTIONAL EXTRA NOTE: __NOTE__

ELEMENT TYPE (from the app): __ELEMENT__

METHOD STATEMENT CLAUSES AVAILABLE (cite by id only):
__MS_CLAUSES__

ECP CODE EXCERPTS AVAILABLE (cite by code string only):
__ECP__

Return ONE JSON object with this exact shape:
{
  "defects": [
    {
      "name": "Clean short name of the defect",
      "location_hint": "where on site (from the description)",
      "severity": "Medium",
      "ms_violations": ["3.5"],
      "code_violations": ["ECP 203 §6.3.1"],
      "repair_action": "Suggested repair if the MS covers it, else a general suggestion.",
      "context_mismatch": false
    }
  ]
}

RULES:
- Return exactly 1 defect that matches the engineer's description.
- Do NOT invent a different defect — stick to what was written.
- Only cite MS clause ids that appear in the list above.
- Only cite ECP codes that appear in the list above.
- If nothing in the MS matches, use empty arrays and context_mismatch=true.
- Severity must be one of: Low, Medium, High, Critical.
- Output ONLY the JSON. No prose. No markdown fences.
"""


async def analyze_defect_text(description,
                               note,
                               ms_clauses,
                               element_type,
                               call_gemini_json_fn):
    if not (description or "").strip():
        return {"defects": [], "error": "Defect description is required."}

    ecp_excerpts = get_ecp_excerpts(element_type)

    prompt = (_DEFECT_TEXT_PROMPT
              .replace("__DESC__", description.strip())
              .replace("__NOTE__", note or "(none)")
              .replace("__ELEMENT__", (element_type or "column").lower())
              .replace("__MS_CLAUSES__", _format_ms_clauses(ms_clauses))
              .replace("__ECP__", _format_ecp(ecp_excerpts)))

    try:
        raw = await call_gemini_json_fn(prompt, temperature=0.0, timeout=40)
    except Exception as e:
        return {"defects": [], "error": "AI call failed: " + repr(e)}

    data = _parse_json_object(raw)
    if not data:
        return {"defects": [], "error": "AI returned unparseable output.",
                "raw": (raw or "")[:1500]}

    allowed_ms = {str(c.get("id", "")).strip() for c in (ms_clauses or [])}
    allowed_ecp = {e["code"] for e in ecp_excerpts}

    defects = []
    for d in data.get("defects", [])[:3]:
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
        mismatch = bool(d.get("context_mismatch", False))
        if not ms_v and not ecp_v:
            mismatch = True
        defects.append({
            "name": name,
            "location_hint": str(d.get("location_hint", "")).strip()[:60],
            "severity": severity,
            "ms_violations": ms_v,
            "code_violations": ecp_v,
            "repair_action": str(d.get("repair_action", "")).strip()[:180],
            "context_mismatch": mismatch,
        })

    return {"defects": defects, "error": None, "raw": (raw or "")[:1500]}


# =====================================================================
# QR
# =====================================================================
def _make_qr_buffer(text):
    try:
        from services.pdf_service import generate_qr_code
        return generate_qr_code(text)
    except Exception as e:
        print("[defect] QR generation failed: " + repr(e))
        return None


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
    _ensure_fonts()
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

    NAVY = colors.HexColor("#0a0a0a")
    ORANGE = colors.HexColor("#14b8a6")
    GREY = colors.HexColor("#525252")
    LINE = colors.HexColor("#d4d4d4")

    title_style = ParagraphStyle("Title", fontName=_MONO_BOLD,
                                  fontSize=14, textColor=NAVY,
                                  spaceAfter=2, leading=17)
    sub_style = ParagraphStyle("Sub", fontName=_MONO_NAME,
                                fontSize=9, textColor=ORANGE,
                                spaceAfter=6, leading=12)
    label_style = ParagraphStyle("Label", fontName=_MONO_BOLD,
                                  fontSize=8, textColor=NAVY, leading=11)
    meta_style = ParagraphStyle("Meta", fontName=_MONO_NAME, fontSize=8.5,
                                 textColor=GREY, leading=12)
    body_style = ParagraphStyle("Body", fontName=_MONO_NAME, fontSize=8.5,
                                 textColor=colors.black, leading=12)
    mono_head_style = ParagraphStyle("MonoHead", fontName=_MONO_BOLD,
                                      fontSize=9.5, textColor=NAVY,
                                      leading=12, spaceAfter=2)
    mono_cite_style = ParagraphStyle("MonoCite", fontName=_MONO_NAME,
                                      fontSize=8, textColor=GREY, leading=10)
    small_style = ParagraphStyle("Small", fontName=_MONO_NAME, fontSize=7,
                                  textColor=GREY, leading=9)

    story = []

    logo_img = ""
    if logo_bytes:
        try:
            logo_img = ReportLabImage(io.BytesIO(logo_bytes),
                                       width=26 * mm, height=13 * mm)
        except Exception:
            logo_img = ""

    header_text = [
        _para("NOTICE TO SUBCONTRACTOR", title_style, bold=True),
        _para("NOTICE NO: " + notice_uid, sub_style),
    ]
    if logo_img:
        t_head = Table([[logo_img, header_text]],
                       colWidths=[32 * mm, 148 * mm])
    else:
        t_head = Table([[header_text]], colWidths=[180 * mm])
    t_head.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(t_head)
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=0.8, color=ORANGE,
                             spaceAfter=10))

    meta_rows = [
        [_para("PROJECT", label_style, bold=True),
         _para(project.get("name", ""), meta_style),
         _para("DATE", label_style, bold=True),
         _para(datetime.date.today().strftime("%Y-%m-%d"), meta_style)],
        [_para("CONTRACTOR", label_style, bold=True),
         _para(project.get("contractor", ""), meta_style),
         _para("LOCATION", label_style, bold=True),
         _para(project.get("location", ""), meta_style)],
        [_para("CONSULTANT", label_style, bold=True),
         _para(project.get("consultant", ""), meta_style),
         _para("RAISED AS", label_style, bold=True),
         _para("QC Internal" if raise_type == "qc_internal"
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

    story.append(_para("TO:", label_style, bold=True))
    story.append(_para(subcontractor, body_style))
    story.append(Spacer(1, 4))
    story.append(_para(
        "DEADLINE: " + str(deadline_days) + " working day" +
        ("s" if deadline_days != 1 else "") + " from receipt of this notice.",
        body_style))
    story.append(Spacer(1, 10))
    story.append(_para(
        "You are required to remedy the following defects. "
        "This notice is a permanent record and must be acknowledged on site.",
        body_style))
    story.append(Spacer(1, 12))

    for idx, d in enumerate(defects, start=1):
        raw_name = d.get("name", "Defect")
        name = _fix(raw_name)
        zone = _fix(d.get("zone", "") or "")
        loc = _fix(d.get("location_hint", "") or "")
        severity = d.get("severity", "Medium")
        ms_v = [_fix(v) for v in (d.get("ms_violations") or [])]
        ecp_v = [_fix(v) for v in (d.get("code_violations") or [])]
        repair = _fix(d.get("repair_action", "") or "")
        mismatch = bool(d.get("context_mismatch", False))

        head = str(idx).zfill(2) + ".  " + name
        if zone or loc:
            head += "   //   " + ", ".join(p for p in [zone, loc] if p)
        story.append(_para(head, mono_head_style, bold=True))

        cit_bits = []
        if ms_v:
            cit_bits.append("MS: " + ", ".join(ms_v))
        if ecp_v:
            cit_bits.append("ECP: " + ", ".join(ecp_v))
        if mismatch and not cit_bits:
            cit_bits.append("MS: (no matching clause in the uploaded MS)")
        if cit_bits:
            story.append(_para("    " + "   |   ".join(cit_bits),
                                mono_cite_style))
        if repair:
            story.append(_para("    REPAIR: " + repair, mono_cite_style))
        story.append(_para("    SEVERITY: " + severity, mono_cite_style))
        story.append(Spacer(1, 8))

    story.append(Spacer(1, 18))

    sig_data = [
        [_para("ISSUED BY (QC)", label_style, bold=True),
         _para("ACKNOWLEDGED BY (SUBCONTRACTOR)", label_style, bold=True)],
        [_para("_" * 32, body_style),
         _para("_" * 32, body_style)],
        [_para(project.get("engineer_name", ""), meta_style),
         _para("Name / Date / Signature", small_style)],
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

    qr_buf = _make_qr_buffer(
        "UID: " + notice_uid + " | Defect Notice | " +
        project.get("name", ""))
    if qr_buf:
        try:
            qr_img = ReportLabImage(qr_buf, width=18 * mm, height=18 * mm)
            t_qr = Table([[qr_img,
                           _para("UID: " + notice_uid, meta_style)]],
                          colWidths=[22 * mm, 158 * mm])
            t_qr.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ]))
            story.append(t_qr)
        except Exception as e:
            print("[defect] QR embed failed: " + repr(e))
            story.append(_para("UID: " + notice_uid, meta_style))
    else:
        story.append(_para("UID: " + notice_uid, meta_style))

    doc.build(story)
    buf.seek(0)
    return buf.read()


# =====================================================================
# REGISTER PDF
# =====================================================================
def build_register_pdf(project, rows, logo_bytes=None):
    _ensure_fonts()
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable,
    )
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.units import mm

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=landscape(A4),
        leftMargin=14 * mm, rightMargin=14 * mm,
        topMargin=14 * mm, bottomMargin=14 * mm,
    )

    NAVY = colors.HexColor("#0a0a0a")
    ORANGE = colors.HexColor("#14b8a6")
    GREY = colors.HexColor("#525252")

    title_style = ParagraphStyle("Title", fontName=_MONO_BOLD,
                                  fontSize=13, textColor=NAVY, spaceAfter=2)
    sub_style = ParagraphStyle("Sub", fontName=_MONO_NAME,
                                fontSize=8.5, textColor=ORANGE, spaceAfter=6)
    cell_style = ParagraphStyle("Cell", fontName=_MONO_NAME, fontSize=8,
                                 textColor=GREY, leading=10)
    head_style = ParagraphStyle("Head", fontName=_MONO_BOLD,
                                 fontSize=8, textColor=colors.white,
                                 leading=10)
    small_style = ParagraphStyle("Small", fontName=_MONO_NAME, fontSize=7,
                                  textColor=GREY, leading=9)

    story = []
    story.append(_para("DEFECT REGISTER", title_style, bold=True))
    story.append(_para(project.get("name", ""), sub_style))
    story.append(HRFlowable(width="100%", thickness=0.8, color=ORANGE,
                             spaceAfter=10))

    head = ["UID", "DEFECT", "ZONE", "SUBCONTRACTOR",
            "SOURCE", "STATUS", "CREATED"]
    data = [[_para(h, head_style, bold=True) for h in head]]
    for r in rows:
        data.append([
            _para(r.get("uid", ""), cell_style),
            _para(r.get("first_defect", "") or "-", cell_style),
            _para(r.get("zone", ""), cell_style),
            _para(r.get("subcontractor", ""), cell_style),
            _para("CONSULTANT" if r.get("raise_type") == "consultant"
                  else "QC", cell_style),
            _para(str(r.get("status", "")).upper(), cell_style),
            _para(str(r.get("created_at", ""))[:10], cell_style),
        ])

    t = Table(data, colWidths=[36*mm, 60*mm, 15*mm, 45*mm, 26*mm, 24*mm, 24*mm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
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
    story.append(_para(
        "GENERATED " + datetime.date.today().strftime("%Y-%m-%d") +
        "  ·  " + str(len(rows)) + " RECORD(S)", small_style))

    doc.build(story)
    buf.seek(0)
    return buf.read()


# =====================================================================
# CLOSURE REPORT PDF
# =====================================================================
def build_closure_pdf(project, rows, report_uid=None, logo_bytes=None):
    _ensure_fonts()
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        Image as ReportLabImage, HRFlowable,
    )
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm

    if report_uid is None:
        report_uid = generate_uid("CLR")

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=18 * mm, bottomMargin=18 * mm,
    )

    NAVY = colors.HexColor("#0a0a0a")
    ORANGE = colors.HexColor("#14b8a6")
    GREY = colors.HexColor("#525252")
    GREEN = colors.HexColor("#16a34a")
    RED = colors.HexColor("#dc2626")

    title_style = ParagraphStyle("Title", fontName=_MONO_BOLD,
                                  fontSize=14, textColor=NAVY, spaceAfter=2)
    sub_style = ParagraphStyle("Sub", fontName=_MONO_NAME,
                                fontSize=9, textColor=ORANGE, spaceAfter=6)
    label_style = ParagraphStyle("Label", fontName=_MONO_BOLD,
                                  fontSize=8, textColor=NAVY, leading=11)
    meta_style = ParagraphStyle("Meta", fontName=_MONO_NAME, fontSize=8.5,
                                 textColor=GREY, leading=11)
    body_style = ParagraphStyle("Body", fontName=_MONO_NAME, fontSize=8.5,
                                 textColor=colors.black, leading=12)
    mono_head_style = ParagraphStyle("MonoHead", fontName=_MONO_BOLD,
                                      fontSize=9, textColor=NAVY,
                                      spaceAfter=2, leading=11)
    small_style = ParagraphStyle("Small", fontName=_MONO_NAME, fontSize=7,
                                  textColor=GREY, leading=9)

    open_rows = [r for r in rows if r.get("status") != "closed"]
    closed_rows = [r for r in rows if r.get("status") == "closed"]

    story = []

    logo_img = ""
    if logo_bytes:
        try:
            logo_img = ReportLabImage(io.BytesIO(logo_bytes),
                                       width=26 * mm, height=13 * mm)
        except Exception:
            logo_img = ""

    header_text = [
        _para("DEFECT CLOSURE REPORT", title_style, bold=True),
        _para("REPORT NO: " + report_uid, sub_style),
    ]
    if logo_img:
        t_head = Table([[logo_img, header_text]],
                       colWidths=[32 * mm, 148 * mm])
    else:
        t_head = Table([[header_text]], colWidths=[180 * mm])
    t_head.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(t_head)
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=0.8, color=ORANGE,
                             spaceAfter=10))

    meta_rows = [
        [_para("PROJECT", label_style, bold=True),
         _para(project.get("name", ""), meta_style),
         _para("DATE", label_style, bold=True),
         _para(datetime.date.today().strftime("%Y-%m-%d"), meta_style)],
        [_para("CONTRACTOR", label_style, bold=True),
         _para(project.get("contractor", ""), meta_style),
         _para("CONSULTANT", label_style, bold=True),
         _para(project.get("consultant", ""), meta_style)],
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

    summary = [
        [_para("TOTAL DEFECTS", label_style, bold=True),
         _para(str(len(rows)), meta_style)],
        [_para("CLOSED", label_style, bold=True),
         _para(str(len(closed_rows)), meta_style)],
        [_para("STILL OPEN", label_style, bold=True),
         _para(str(len(open_rows)), meta_style)],
    ]
    t_sum = Table(summary, colWidths=[50 * mm, 30 * mm])
    t_sum.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#F5F5F5")),
        ('BOX', (0, 0), (-1, -1), 0.3, colors.HexColor("#BFBFBF")),
        ('INNERGRID', (0, 0), (-1, -1), 0.3, colors.HexColor("#BFBFBF")),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(t_sum)
    story.append(Spacer(1, 14))

    if not rows:
        story.append(_para("No defects recorded.", body_style))
    else:
        for idx, r in enumerate(rows, start=1):
            status = str(r.get("status", "")).upper()
            color = GREEN if status == "CLOSED" else RED
            head = (str(idx).zfill(2) + ".  " + _fix(r.get("uid", "")) +
                    "   //   " + _fix(r.get("first_defect", "") or "-") +
                    "   ·   ZONE " + _fix(r.get("zone", "")))
            story.append(_para(head, mono_head_style, bold=True))

            st_style = ParagraphStyle("St" + str(idx), parent=meta_style,
                                       textColor=color, fontName=_MONO_BOLD)
            story.append(_para("STATUS: " + status, st_style, bold=True))
            story.append(_para("SOURCE: " +
                                ("CONSULTANT" if r.get("raise_type") ==
                                 "consultant" else "QC INTERNAL"),
                                meta_style))
            story.append(_para("CREATED: " +
                                str(r.get("created_at", ""))[:19],
                                meta_style))
            if r.get("closed_at"):
                story.append(_para("CLOSED: " +
                                    str(r["closed_at"])[:19], meta_style))

            story.append(Spacer(1, 6))

    story.append(Spacer(1, 18))

    sig_data = [
        [_para("QC ENGINEER", label_style, bold=True),
         _para("CONSULTANT", label_style, bold=True)],
        [_para("_" * 32, body_style),
         _para("_" * 32, body_style)],
        [_para(project.get("engineer_name", ""), meta_style),
         _para("Name / Date / Signature", small_style)],
    ]
    t_sig = Table(sig_data, colWidths=[90 * mm, 90 * mm])
    t_sig.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(t_sig)

    doc.build(story)
    buf.seek(0)
    return buf.read()
