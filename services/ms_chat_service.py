"""
services/ms_chat_service.py — Chat with your Method Statement.

Two modes:
  1. ask_ms_question(...) — Q&A over uploaded MS clauses, with citations.
  2. check_document_against_ms(...) — OCR a document (batch ticket, delivery
     note, test result...) and check it against the MS. Returns a verdict.

Uses the existing Gemini wrapper (call_gemini_json) and the OCR helper in
defect_page.py is passed in by the caller to avoid a circular import.
"""
import re
import json

from services import defect_db as db


_QA_PROMPT = """You are a QC assistant for a construction site. Answer the
user's question using the FULL Method Statement text below.

RULES:
- Answer in the same language as the question (Arabic or English).
- If the MS contains the answer, give it clearly and cite the clause
  ID(s) in the form [S<id>] when you can.
- If you can't find an exact match, give the closest relevant clause(s)
  from the full text and explain briefly. Do NOT invent clause IDs.
- Only say "Not found in the uploaded MS." if there is genuinely
  nothing relevant to the question anywhere in the text.
- Be as thorough as the question requires. Short lookups: 1–3 sentences.
  Procedural / "how" / "why" / "list" / multi-part questions: give a
  full answer — cover every relevant clause, cite each one with [S<id>],
  and quote exact numbers/limits/tolerances from the MS. Up to ~12
  sentences is fine for a procedural question.
- Do NOT pad, do NOT repeat yourself, do NOT invent clause IDs.

MS CLAUSE INDEX (available IDs — cite only these):
__CLAUSE_INDEX__

FULL METHOD STATEMENT TEXT:
__FULL_TEXT__

USER QUESTION:
__QUESTION__

Reply with the plain answer only. No JSON. No markdown."""


_DOC_CHECK_PROMPT = """You are a QC engineer checking a document (batch
ticket, delivery note, test result, or similar) against a Method Statement.

DOCUMENT TEXT (OCR output, may contain small errors):
__DOC_TEXT__

MS CLAUSE INDEX (use these IDs when citing):
__CLAUSES__

MS FULL TEXT (source of truth — read this carefully):
__FULL_TEXT__

Return ONE JSON object with this exact shape:
{
  "doc_type": "Concrete batch ticket",
  "extracted": {
    "grade": "C30/37",
    "wc_ratio": "0.52",
    "slump_mm": "120"
  },
  "checks": [
    {
      "field": "W/C ratio",
      "value": "0.52",
      "ms_requirement": "max 0.50",
      "verdict": "ok" | "warn" | "fail",
      "clause_id": "4.2",
      "note": "short explanation"
    }
  ],
  "overall": "compliant" | "conditional" | "non_compliant",
  "summary": "One sentence verdict."
}

RULES:
- Only cite clause IDs that exist in the MS clause index above.
- If MS doesn't cover a field, use verdict "warn" and clause_id "".
- Output ONLY the JSON object. No prose."""


def _format_clauses_for_prompt(clauses, limit=60):
    if not clauses:
        return "(no MS clauses uploaded for this project)"
    lines = []
    for c in clauses[:limit]:
        cid = str(c.get("id", "?")).strip()
        title = str(c.get("title", "")).strip()[:80]
        text = str(c.get("text", "")).strip()[:220]
        lines.append("S" + cid + " | " + title + " | " + text)
    return "\n".join(lines)


_CHAPTERS_PROMPT = """You are reading a construction Method Statement (MS).
Extract the CHAPTER / SECTION structure (headings only).

Return ONE JSON object with this exact shape:
{
  "chapters": [
    {"id": "1", "title": "Scope"},
    {"id": "2", "title": "Materials"},
    {"id": "2.1", "title": "Concrete"},
    {"id": "2.2", "title": "Reinforcement"},
    {"id": "3", "title": "Execution"}
  ]
}

RULES:
- "id" is the section number as a string ("1", "2.1", "3.4.2"), or "" if
  the heading has no number.
- "title" is the heading text, max 120 chars.
- Include ALL headings you can find: numbered sections, sub-sections,
  appendix, revision history, references, tables of contents.
- Do NOT invent headings. Only headings that actually appear in the text.
- Max 200 items.
- Order as they appear in the document.
- Output ONLY the JSON object. No prose. No markdown.

MS TEXT STARTS BELOW
--------
__MS_TEXT__
--------
"""


def _find_chapter_line(lines, cid, title, used):
    """Find the 0-based line index where a chapter heading appears.
    Prefers a line that starts with the chapter number; falls back to a
    substring match against the title."""
    cid_pat = None
    if cid:
        try:
            cid_pat = re.compile(r"^\s*" + re.escape(str(cid)) +
                                  r"[\s\.\)\-:]")
        except Exception:
            cid_pat = None
    if cid_pat:
        for i, ln in enumerate(lines):
            if i in used:
                continue
            s = ln.strip()
            if not s or len(s) > 200:
                continue
            if cid_pat.match(s):
                used.add(i)
                return i
    title_low = (title or "").strip().lower()
    if title_low:
        for i, ln in enumerate(lines):
            if i in used:
                continue
            s = ln.strip().lower()
            if not s or len(s) > 200:
                continue
            if title_low in s:
                used.add(i)
                return i
    return -1


async def extract_chapters_from_full_text(full_text, call_gemini_json_fn):
    """Return [{id, title, line}] where line is 0-based line index in
    full_text. Returns [] on any failure."""
    text = (full_text or "").strip()
    if len(text) < 200:
        return []
    prompt = _CHAPTERS_PROMPT.replace("__MS_TEXT__", text[:40000])
    try:
        raw = await call_gemini_json_fn(prompt, temperature=0.0,
                                          timeout=45, max_tokens=2048)
    except Exception as e:
        print("[ms] chapters AI failed: " + repr(e))
        return []
    data = _parse_json_object(raw)
    if not data:
        return []
    items = []
    for c in (data.get("chapters") or [])[:200]:
        cid = str(c.get("id") or "").strip()
        title = str(c.get("title") or "").strip()[:120]
        if not cid and not title:
            continue
        items.append({"id": cid, "title": title})
    lines = text.split("\n")
    used = set()
    out = []
    for c in items:
        ln = _find_chapter_line(lines, c["id"], c["title"], used)
        if ln >= 0:
            out.append({"id": c["id"], "title": c["title"], "line": ln})
    out.sort(key=lambda x: x["line"])
    return out


def _strip_fences(txt):
    t = (txt or "").strip()
    t = re.sub(r'^```json\s*', '', t)
    t = re.sub(r'^```\s*', '', t)
    t = re.sub(r'\s*```$', '', t)
    return t


def _parse_json_object(raw):
    if not raw:
        return None
    t = _strip_fences(raw)
    start = t.find('{')
    end = t.rfind('}')
    if start == -1 or end == -1:
        return None
    try:
        return json.loads(t[start:end + 1])
    except Exception:
        return None


async def ask_ms_question(project_id, question, call_gemini_json_fn):
    """Answer a question from the full MS text. Returns {answer, error}."""
    q = (question or "").strip()
    if not q:
        return {"answer": "", "error": "Question is empty."}

    clauses = db.get_clauses_for_element(project_id)
    full_text = db.get_ms_full_text(project_id)

    if not full_text and not clauses:
        return {"answer": "", "error":
                "No MS uploaded for this project. Upload one first."}

    index_lines = []
    for c in (clauses or [])[:200]:
        cid = str(c.get("id", "?")).strip()
        title = str(c.get("title", "")).strip()[:80]
        index_lines.append("S" + cid + " | " + title)
    clause_index = "\n".join(index_lines) or "(no clause index available)"

    if full_text:
        ft = full_text[:120000]
    else:
        ft = ("(full text not stored for this upload — "
              "using clause list only)\n" +
              _format_clauses_for_prompt(clauses))

    prompt = (_QA_PROMPT
              .replace("__CLAUSE_INDEX__", clause_index)
              .replace("__FULL_TEXT__", ft)
              .replace("__QUESTION__", q))
    try:
        raw = await call_gemini_json_fn(prompt, temperature=0.1,
                                          timeout=90, max_tokens=3072)
    except Exception as e:
        return {"answer": "", "error": "AI call failed: " + str(e)}
    text = (raw or "").strip()
    if not text:
        return {"answer": "", "error": "Empty response from AI."}
    return {"answer": text, "error": None}


async def check_document_against_ms(file_bytes, mime_type, project_id,
                                     ocr_fn, call_gemini_json_fn):
    """OCR the doc and check it against the MS.
    Returns dict with ocr_text, doc_type, extracted, checks, overall,
    summary, error."""
    if not file_bytes:
        return {"error": "Empty file."}
    clauses = db.get_clauses_for_element(project_id)
    if not clauses:
        return {"error": "No MS uploaded for this project."}
    ocr_text, ocr_err = await ocr_fn(file_bytes, mime_type)
    if ocr_err and not ocr_text:
        return {"error": "OCR failed: " + str(ocr_err)}
    if not ocr_text:
        return {"error": "No readable text in the document."}

    full_text = db.get_ms_full_text(project_id) or ""
    ft = full_text[:100000] if full_text else "(no full text)"
    prompt = (_DOC_CHECK_PROMPT
              .replace("__DOC_TEXT__", ocr_text[:4000])
              .replace("__CLAUSES__", _format_clauses_for_prompt(clauses))
              .replace("__FULL_TEXT__", ft))
    try:
        raw = await call_gemini_json_fn(prompt, temperature=0.0, timeout=45)
    except Exception as e:
        return {"error": "AI check failed: " + str(e),
                "ocr_text": ocr_text}
    data = _parse_json_object(raw)
    if not data:
        return {"error": "AI returned unparseable output.",
                "ocr_text": ocr_text, "raw": (raw or "")[:1500]}
    return {
        "ocr_text": ocr_text,
        "doc_type": str(data.get("doc_type", "")).strip(),
        "extracted": data.get("extracted") or {},
        "checks": data.get("checks") or [],
        "overall": str(data.get("overall", "")).strip(),
        "summary": str(data.get("summary", "")).strip(),
        "error": None,
    }
