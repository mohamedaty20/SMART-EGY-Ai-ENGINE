import io
import datetime
import os
import uuid
import re
import asyncio
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import qrcode
from docxtpl import DocxTemplate
from docx import Document

# Dotenv & FastAPI / NiceGUI
from dotenv import load_dotenv
from fastapi import FastAPI
from nicegui import app, ui, run

# Google GenAI SDK
from google import genai
from google.genai import types

# ReportLab for PDF Generation
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
    Image as ReportLabImage,
)

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

GEMINI_MODEL = "gemini-3.5-flash-lite"

PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN = 32
USABLE_WIDTH = PAGE_WIDTH - (2 * MARGIN)

# =====================================================================
# STYLING (full CSS – same as original)
# =====================================================================
app.native.window_args = {"resizable": True}

ui.add_head_html('''
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    ::-webkit-scrollbar { width: 8px !important; background: #031338 !important; }
    ::-webkit-scrollbar-thumb { background: #FF8C00 !important; border-radius: 10px; }

    html, body {
        background: radial-gradient(circle at 10% 20%, #0a1a3a, #031338) !important;
        color: #E9EDF5 !important;
        font-family: 'Inter', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
        margin: 0; padding: 0;
        width: 100vw; height: 100vh;
        overflow-x: hidden;
    }

    .sidebar-container {
        background: #0b1a3a !important;
        border-right: 2px solid rgba(255, 140, 0, 0.4) !important;
        box-shadow: 8px 0 30px rgba(0,0,0,0.6) !important;
    }
    .sidebar-container .q-field__control {
        background-color: rgba(13, 26, 53, 0.8) !important;
        border: 1px solid #2c3f6b !important;
        border-radius: 10px !important;
    }
    .sidebar-container .q-field__native,
    .sidebar-container .q-field__input,
    .sidebar-container .q-field__label {
        color: #E9EDF5 !important;
    }
    .sidebar-container .q-select .q-field__control {
        background-color: rgba(13, 26, 53, 0.8) !important;
    }

    .output-card {
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
        box-shadow: none !important;
        width: 100% !important;
        max-width: none !important;
        box-sizing: border-box;
    }

    .input-card {
        background: rgba(13, 26, 53, 0.6);
        backdrop-filter: blur(8px);
        border: 1px solid rgba(255, 140, 0, 0.2);
        border-radius: 16px;
        padding: 18px 22px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        margin-bottom: 20px;
        width: 100% !important;
        max-width: none !important;
        box-sizing: border-box;
    }

    .primary-btn, .q-btn {
        background: linear-gradient(135deg, #1a1a1a 0%, #333333 100%) !important;
        color: #FFFFFF !important;
        border: 1px solid #555 !important;
        font-weight: 600 !important;
        border-radius: 14px !important;
        padding: 10px 28px !important;
        letter-spacing: .4px;
        text-transform: none !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5) !important;
        transition: all 0.25s ease !important;
        min-height: 44px !important;
    }
    .primary-btn:hover, .q-btn:hover {
        background: linear-gradient(135deg, #2d2d2d 0%, #444444 100%) !important;
        transform: translateY(-3px) !important;
        box-shadow: 0 8px 25px rgba(0,0,0,0.7) !important;
        border-color: #FF8C00 !important;
    }
    .primary-btn:active, .q-btn:active {
        transform: translateY(0px) !important;
    }

    .q-uploader {
        background: rgba(13, 26, 53, 0.6) !important;
        backdrop-filter: blur(8px) !important;
        border-radius: 14px !important;
        border: 2px dashed rgba(255, 140, 0, 0.5) !important;
        color: #FFFFFF !important;
        padding: 8px !important;
    }
    .q-uploader .q-uploader__header {
        background: transparent !important;
        color: #FFFFFF !important;
    }
    .q-uploader .q-uploader__header-content {
        color: #FFFFFF !important;
    }
    .q-uploader .q-uploader__file {
        background: rgba(13, 26, 53, 0.8) !important;
        color: #FFFFFF !important;
        border-radius: 10px !important;
    }

    input, select, textarea, .q-field__control {
        background-color: rgba(13, 26, 53, 0.7) !important;
        color: #FFFFFF !important;
        border: 1px solid #2c3f6b !important;
        border-radius: 10px !important;
    }
    .q-field__native, .q-field__input, .q-field__label {
        color: #E9EDF5 !important;
    }
    .q-field--highlighted .q-field__label {
        color: #FF8C00 !important;
    }

    .q-menu, .q-popover, .q-virtual-scroll__content {
        background: rgba(13, 26, 53, 0.95) !important;
        backdrop-filter: blur(8px) !important;
        border: 1px solid #2c3f6b !important;
        border-radius: 10px !important;
    }
    .q-item {
        color: #FFFFFF !important;
        background: transparent !important;
        border-radius: 8px !important;
    }
    .q-item:hover {
        background: rgba(255, 140, 0, 0.15) !important;
        color: #FF8C00 !important;
    }

    .app-footer {
        width: 100%;
        background: rgba(13, 26, 53, 0.7);
        backdrop-filter: blur(8px);
        border-top: 2px solid rgba(255, 140, 0, 0.5);
        padding: 20px 24px;
        margin-top: 50px;
        text-align: center;
        color: #A9B6D0;
        font-size: 13px;
        box-sizing: border-box;
        border-radius: 16px 16px 0 0;
    }
    .app-footer a {
        color: #4FC3F7;
        text-decoration: none;
        transition: color 0.3s ease;
    }
    .app-footer a:hover {
        color: #FF8C00;
        text-decoration: underline;
    }

    .markdown-body {
        font-size: 14px;
        line-height: 1.7;
        color: #E9EDF5;
        background: transparent !important;
        padding: 0 !important;
    }
    .markdown-body h1, .markdown-body h2, .markdown-body h3,
    .markdown-body h4, .markdown-body h5, .markdown-body h6 {
        font-family: 'Inter', sans-serif !important;
        font-weight: 700 !important;
        color: #FF8C00 !important;
        margin: 20px 0 10px 0 !important;
        line-height: 1.35 !important;
    }
    .markdown-body h1 { font-size: 22px !important; border-bottom: 2px solid #FF8C00; padding-bottom: 8px; }
    .markdown-body h2 { font-size: 19px !important; }
    .markdown-body h3 { font-size: 17px !important; color: #4FC3F7 !important; }
    .markdown-body h4, .markdown-body h5, .markdown-body h6 { font-size: 15px !important; color: #4FC3F7 !important; }
    .markdown-body p { margin: 10px 0 !important; }
    .markdown-body strong { color: #FFFFFF; }
    .markdown-body ul, .markdown-body ol { padding-left: 25px !important; margin: 10px 0 !important; }
    .markdown-body li { margin: 5px 0 !important; }
    .markdown-body hr { border-color: #1f3355; margin: 16px 0; }
    .markdown-body code {
        background: rgba(3, 19, 56, 0.8);
        border: 1px solid #1f3355;
        border-radius: 4px;
        padding: 2px 6px;
        font-size: 12.5px;
        color: #4FC3F7;
    }
    .markdown-body table {
        border-collapse: collapse !important;
        width: 100% !important;
        margin: 16px 0 !important;
        font-size: 13px !important;
        table-layout: auto !important;
        border-radius: 12px !important;
        overflow: hidden !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3) !important;
    }
    .markdown-body th, .markdown-body td {
        border: 1px solid #1f3355 !important;
        padding: 10px 14px !important;
        text-align: left !important;
        word-wrap: break-word !important;
        white-space: normal !important;
    }
    .markdown-body th {
        background: linear-gradient(135deg, #1a1a1a 0%, #333333 100%) !important;
        color: #FF8C00 !important;
        font-weight: 700 !important;
    }
    .markdown-body tr:nth-child(even) td {
        background-color: rgba(10, 26, 58, 0.5);
    }
    .markdown-body tr:hover td {
        background-color: rgba(255, 140, 0, 0.08);
    }

    .stat-chip {
        background: rgba(13, 26, 53, 0.6);
        backdrop-filter: blur(8px);
        border: 1px solid #1f3355;
        border-radius: 12px;
        padding: 14px 20px;
        text-align: center;
        min-width: 140px;
        transition: all 0.3s ease;
    }
    .stat-chip:hover {
        border-color: #FF8C00;
        transform: translateY(-3px);
        box-shadow: 0 6px 20px rgba(255,140,0,0.15);
    }
    .stat-chip .val {
        font-size: 24px;
        font-weight: 800;
        color: #FF8C00;
    }
    .stat-chip .lbl {
        font-size: 11px;
        color: #A9B6D0;
        text-transform: uppercase;
        letter-spacing: .05em;
        margin-top: 4px;
    }

    .main-title {
        font-size: 3.8rem !important;
        font-weight: 900 !important;
        letter-spacing: -0.02em;
    }
    .sub-title {
        color: #FFFFFF !important;
        font-weight: 500;
    }
    @media (max-width: 768px) {
        .main-title {
            font-size: 2.2rem !important;
        }
        .sub-title {
            font-size: 1rem !important;
        }
        .stat-chip {
            min-width: 100px !important;
            padding: 10px 14px !important;
        }
        .stat-chip .val {
            font-size: 18px !important;
        }
        .input-card {
            padding: 12px 14px !important;
        }
        .primary-btn, .q-btn {
            padding: 8px 16px !important;
            font-size: 13px !important;
            min-height: 36px !important;
            border-radius: 10px !important;
        }
        .app-footer {
            font-size: 11px !important;
            padding: 14px 12px !important;
        }
        .markdown-body table {
            font-size: 11px !important;
        }
        .markdown-body th, .markdown-body td {
            padding: 6px 8px !important;
        }
    }
</style>
''', shared=True)

# =====================================================================
# HELPER FUNCTIONS (full definitions)
# =====================================================================
_LATEX_SIMPLE = {
    r'\times': ' x ', r'\cdot': ' . ', r'\div': ' / ',
    r'\geq': ' >= ', r'\ge': ' >= ', r'\leq': ' <= ', r'\le': ' <= ',
    r'\pm': ' +/- ', r'\approx': ' ~= ', r'\neq': ' != ',
    r'\infty': 'infinity', r'\text': '', r'\mathrm': '', r'\mathbf': '',
    r'\left': '', r'\right': '', r'\,': ' ', r'\;': ' ', r'\!': '',
    r'\Delta': 'Delta ', r'\delta': 'delta ', r'\sigma': 'sigma ', r'\Sigma': 'Sigma ',
    r'\phi': 'phi ', r'\gamma': 'gamma ', r'\theta': 'theta ', r'\mu': 'mu ',
    r'\pi': 'pi ', r'\alpha': 'alpha ', r'\beta': 'beta ', r'\rho': 'rho ',
    r'\max': 'Max', r'\min': 'Min', r'\sum': 'Sum', r'\bar': '',
}

def sanitize_ai_markdown(text: str) -> str:
    if not text:
        return ""
    text = str(text)
    for macro, repl in _LATEX_SIMPLE.items():
        text = text.replace(macro, repl)
    for _ in range(2):
        text = re.sub(r'\\frac\s*\{([^{}]*)\}\s*\{([^{}]*)\}', r'(\1 / \2)', text)
        text = re.sub(r'\\sqrt\s*\{([^{}]*)\}', r'sqrt(\1)', text)
    text = re.sub(r'_\{([^{}]*)\}', r'_\1', text)
    text = re.sub(r'\^\{([^{}]*)\}', r'^\1', text)
    text = re.sub(r'\\([a-zA-Z]+)', r'\1', text)
    text = text.replace('$$', '').replace('$', '')
    text = re.sub(r'(?<!\w)\{([^{}]{0,40})\}(?!\w)', r'\1', text)
    text = re.sub(r'\*{3,}', '**', text)
    text = re.sub(r'([^\n])\n(#{1,6}\s)', r'\1\n\n\2', text)
    text = re.sub(r'([^\n|])\n(\|)', r'\1\n\n\2', text)
    text = re.sub(r'(?<![\w#*`|])[&$%^~?/\\]{2,}(?![\w#*`|])', '', text)
    text = re.sub(r'[ \t]+\n', '\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def inline_md_to_reportlab(text: str) -> str:
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'(?<!\*)\*([^*\n]+?)\*(?!\*)', r'<i>\1</i>', text)
    text = re.sub(r'`([^`]+)`', r'<font face="Courier">\1</font>', text)
    return text

def build_pdf_styles():
    base = getSampleStyleSheet()
    return {
        'h1': ParagraphStyle('PdfH1', parent=base['Heading1'], fontSize=13.5, leading=17,
                              textColor=colors.HexColor('#1B2A4A'), spaceBefore=10, spaceAfter=5,
                              fontName='Helvetica-Bold'),
        'h2': ParagraphStyle('PdfH2', parent=base['Heading2'], fontSize=11.5, leading=15,
                              textColor=colors.HexColor('#B45309'), spaceBefore=8, spaceAfter=4,
                              fontName='Helvetica-Bold'),
        'h3': ParagraphStyle('PdfH3', parent=base['Heading3'], fontSize=10.5, leading=14,
                              textColor=colors.HexColor('#1B2A4A'), spaceBefore=6, spaceAfter=3,
                              fontName='Helvetica-Bold'),
        'body': ParagraphStyle('PdfBody', parent=base['Normal'], fontSize=9.5, leading=13.5,
                                textColor=colors.HexColor('#1E293B'), spaceAfter=4, fontName='Helvetica'),
        'bullet': ParagraphStyle('PdfBullet', parent=base['Normal'], fontSize=9.5, leading=13,
                                  leftIndent=12, textColor=colors.HexColor('#1E293B'), spaceAfter=2),
        'tablecell': ParagraphStyle('PdfCell', parent=base['Normal'], fontSize=8.5, leading=11,
                                     textColor=colors.HexColor('#1E293B')),
        'tablehead': ParagraphStyle('PdfCellHead', parent=base['Normal'], fontSize=8.5, leading=11,
                                     textColor=colors.white, fontName='Helvetica-Bold'),
    }

def markdown_to_pdf_flowables(raw_text: str, styles: dict, avail_width: float = USABLE_WIDTH):
    text = sanitize_ai_markdown(raw_text)
    lines = text.split('\n')
    flowables = []
    para_buffer = []
    i, n = 0, len(lines)

    def flush_para():
        if para_buffer:
            joined = ' '.join(l.strip() for l in para_buffer if l.strip())
            if joined:
                flowables.append(Paragraph(inline_md_to_reportlab(joined), styles['body']))
            para_buffer.clear()

    while i < n:
        raw_line = lines[i]
        stripped = raw_line.strip()
        if not stripped:
            flush_para()
            i += 1
            continue
        h_match = re.match(r'^(#{1,6})\s+(.*)', stripped)
        if h_match:
            flush_para()
            level = len(h_match.group(1))
            content = h_match.group(2).strip('* ').strip()
            key = 'h1' if level <= 2 else ('h2' if level == 3 else 'h3')
            flowables.append(Paragraph(inline_md_to_reportlab(content), styles[key]))
            i += 1
            continue
        if stripped.startswith('|'):
            flush_para()
            table_lines = []
            while i < n and lines[i].strip().startswith('|'):
                table_lines.append(lines[i].strip())
                i += 1
            rows = []
            for tl in table_lines:
                if re.match(r'^\|?[\s:|-]+\|?$', tl):
                    continue
                cells = [c.strip() for c in tl.strip('|').split('|')]
                rows.append(cells)
            if rows:
                ncols = max(len(r) for r in rows)
                rows = [r + [''] * (ncols - len(r)) for r in rows]
                table_data = []
                for ridx, row in enumerate(rows):
                    style_key = 'tablehead' if ridx == 0 else 'tablecell'
                    table_data.append([Paragraph(inline_md_to_reportlab(c), styles[style_key]) for c in row])
                colw = avail_width / ncols
                t = Table(table_data, colWidths=[colw] * ncols, repeatRows=1)
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1B2A4A')),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#94A3B8')),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F1F5F9')]),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ('LEFTPADDING', (0, 0), (-1, -1), 5),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                ]))
                flowables.append(t)
                flowables.append(Spacer(1, 6))
            continue
        b_match = re.match(r'^[-*•]\s+(.*)', stripped)
        n_match = re.match(r'^(\d+)[.)]\s+(.*)', stripped)
        if b_match or n_match:
            flush_para()
            while i < n:
                s2 = lines[i].strip()
                bm = re.match(r'^[-*•]\s+(.*)', s2)
                nm = re.match(r'^(\d+)[.)]\s+(.*)', s2)
                if bm:
                    flowables.append(Paragraph(f"&#8226; {inline_md_to_reportlab(bm.group(1))}", styles['bullet']))
                    i += 1
                elif nm:
                    flowables.append(Paragraph(f"{nm.group(1)}. {inline_md_to_reportlab(nm.group(2))}", styles['bullet']))
                    i += 1
                else:
                    break
            flowables.append(Spacer(1, 4))
            continue
        para_buffer.append(stripped)
        i += 1
    flush_para()
    return flowables

def generate_qr_code(data_str):
    qr = qrcode.QRCode(version=1, box_size=5, border=1)
    qr.add_data(data_str)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

def build_pdf_header(story, styles, doc_title, subtitle, logo_bytes, engineer, project, location, rep_date, ticket_id, unique_hash):
    title_style = ParagraphStyle("DocTitle", fontSize=14, textColor=colors.HexColor("#1B2A4A"),
                                  spaceAfter=3, fontName="Helvetica-Bold", leading=17)
    sub_style = ParagraphStyle("DocSub", fontSize=9, textColor=colors.HexColor("#B45309"),
                                spaceAfter=6, fontName="Helvetica-Bold")
    meta_style = ParagraphStyle("MetaStyle", fontSize=8, textColor=colors.HexColor("#334155"),
                                 leading=11.5, fontName="Helvetica")
    meta_html = f"""
    <b>Project:</b> {project} &nbsp;|&nbsp; <b>Location:</b> {location}<br/>
    <b>Engineer in Charge:</b> {engineer} &nbsp;|&nbsp; <b>Date:</b> {rep_date}<br/>
    <b>Batch Ticket ID:</b> {ticket_id} &nbsp;|&nbsp; <b>Verification UID:</b> <font color="#CC0000"><b>{unique_hash}</b></font>
    """
    right_cell = ReportLabImage(io.BytesIO(logo_bytes), width=70, height=32) if logo_bytes else ""
    try:
        header_table_data = [
            [Paragraph(f"<b>{doc_title}</b>", title_style), right_cell],
            [Paragraph(subtitle, sub_style), ""],
            [Paragraph(meta_html, meta_style), ""],
        ]
        t_head = Table(header_table_data, colWidths=[USABLE_WIDTH - 100, 100])
        t_head.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        story.append(t_head)
    except Exception:
        story.append(Paragraph(doc_title, title_style))
        story.append(Paragraph(subtitle, sub_style))
        story.append(Paragraph(meta_html, meta_style))
    story.append(Spacer(1, 5))
    story.append(HRFlowable(width="100%", thickness=1.3, color=colors.HexColor("#FF8C00"), spaceAfter=8))

def build_pdf_footer_and_signatures(story, styles, qr_img_buffer):
    body_style = ParagraphStyle("SigBody", fontSize=8, textColor=colors.HexColor("#334155"), leading=11)
    sec_style = ParagraphStyle("SecTitle", fontSize=9.5, textColor=colors.HexColor("#1B2A4A"),
                                spaceBefore=8, spaceAfter=4, fontName="Helvetica-Bold")
    story.append(Spacer(1, 6))
    story.append(Paragraph("Engineering Approvals &amp; Compliance Sign-Off", sec_style))
    qr_lab_img = ReportLabImage(qr_img_buffer, width=38, height=38)
    sign_cell_1 = Paragraph("<b>Prepared By</b><br/>QA/QC Engineer<br/><br/>_________________", body_style)
    sign_cell_2 = Paragraph("<b>Technical Director</b><br/>Chief Engineer<br/><br/>_________________", body_style)
    sign_cell_3 = Paragraph("<b>Client / Consultant</b><br/>Official Stamp<br/><br/>_________________", body_style)
    qr_cell = [Paragraph("<b>QR Verify</b>", body_style), qr_lab_img]
    w = USABLE_WIDTH
    t_sign = Table([[sign_cell_1, sign_cell_2, sign_cell_3, qr_cell]],
                    colWidths=[w * 0.28, w * 0.28, w * 0.28, w * 0.16])
    t_sign.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("ALIGN", (3, 0), (3, 0), "CENTER"),
    ]))
    story.append(t_sign)

def build_report_pdf(doc_title, subtitle, body_markdown, meta, logo_bytes, extra_flowables_before_body=None):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=MARGIN, leftMargin=MARGIN,
                             topMargin=MARGIN, bottomMargin=MARGIN)
    styles = build_pdf_styles()
    story = []
    unique_uid = meta['uid']
    qr_buf = generate_qr_code(f"UID: {unique_uid} | {doc_title} - {meta['project']}")
    build_pdf_header(story, styles, doc_title, subtitle, logo_bytes, meta['engineer'],
                      meta['project'], meta['location'], meta['date'], meta['ticket'], unique_uid)
    if extra_flowables_before_body:
        story.extend(extra_flowables_before_body)
        story.append(Spacer(1, 6))
    story.extend(markdown_to_pdf_flowables(body_markdown, styles))
    story.append(Spacer(1, 8))
    build_pdf_footer_and_signatures(story, styles, qr_buf)
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# =====================================================================
# CODE-COMPLIANCE DIRECTIVE
# =====================================================================
CODE_BASIS_OPTIONS = [
    "Egyptian Codes: ECP 203 / ECP 202 / ECP 104 (Default Core Basis)",
    "ACI 318-25 — Structural Concrete (Primary)",
    "Eurocode 2 — BS EN 1992 + UK Annex (Primary)",
    "AASHTO LRFD Bridge & Pavement Design (Primary)",
    "IBC — International Building Code (Primary)",
]

def get_code_directive(basis: str) -> str:
    if not basis or basis.startswith("Egyptian Codes"):
        return (
            "GOVERNING STANDARD (MANDATORY): Base every clause reference, formula, allowable limit and "
            "pass/fail verdict strictly on the Egyptian Codes — ECP 203 (Reinforced Concrete Structures), "
            "ECP 202 (Soil Mechanics & Foundations) and ECP 104 (Roads, Highways & Airfields), as applicable "
            "to the topic. Do NOT substitute ACI, Eurocode or AASHTO limits. Where relevant, cite the specific "
            "ECP clause, table or article number."
        )
    return (
        f"GOVERNING STANDARD (MANDATORY): The user has selected an alternative primary design basis: "
        f"\"{basis}\". Use that standard as the PRIMARY source for formulas, limits, and clause citations. "
        "Mention the equivalent Egyptian Code (ECP 203 / 202 / 104) clause only as a secondary cross-reference."
    )

NO_LATEX_RULE = (
    "OUTPUT FORMAT (MANDATORY): Write in clean GitHub-flavoured Markdown only. "
    "Never use LaTeX, dollar-sign math delimiters ($ or $$), backslash commands (\\frac, \\times, \\ge ...), "
    "or curly-brace variable syntax. Write formulas in plain readable text, e.g. 'f_cu = 30 N/mm2', "
    "'Standard Deviation = 2.1 N/mm2'. Use real Markdown tables (with a header row and a --- separator row) "
    "for any tabular data — never hand-draw tables with dashes or asterisks. Use ## / ### for section headings, "
    "never #### or deeper. Use single asterisks pairs (**bold**) and never stack more than two."
)

async def call_gemini(contents, system_instruction=None, temperature=0.1, timeout=60):
    cfg_kwargs = {"temperature": temperature}
    if system_instruction:
        cfg_kwargs["system_instruction"] = system_instruction
    config = types.GenerateContentConfig(**cfg_kwargs)
    try:
        response = await asyncio.wait_for(
            run.io_bound(
                client.models.generate_content,
                model=GEMINI_MODEL,
                contents=contents,
                config=config,
            ),
            timeout=timeout
        )
        return sanitize_ai_markdown(response.text)
    except asyncio.TimeoutError:
        raise Exception("AI request timed out. Please try with a smaller file or simplify your query.")

# =====================================================================
# MAIN PAGE
# =====================================================================
@ui.page('/')
def main_page():
    ui.query('body').style('width: 100vw; height: 100vh; overflow-x: hidden;')

    # ---- SIDEBAR ----
    sidebar = ui.left_drawer().classes('sidebar-container').style('width: 380px;')
    with sidebar:
        with ui.row().classes('w-full items-center justify-between mb-4 p-2'):
            ui.label('📋 PROJECT METADATA').classes('text-white font-bold text-base tracking-wide')
            ui.button('✕', on_click=sidebar.toggle).classes(
                'bg-transparent text-white text-xl hover:text-[#FF8C00] p-1 min-w-[36px] !shadow-none !rounded-full !bg-transparent'
            ).style('font-size: 20px; line-height: 1;')

        project_name_input = ui.input(label='Project Name', value='Highway Expansion Project').classes('w-full mb-3')
        pour_location_input = ui.input(label='Structural Element / Chainage', value='Highway Section Ch. 12+500').classes('w-full mb-4')

        ui.label('Governing Design Code Basis').classes('text-white font-bold text-sm mb-1')
        ui.markdown('By default every AI output in this app is generated strictly per **ECP 203 / ECP 202 / ECP 104**. Change this to switch the primary basis.').classes('text-xs text-[#A9B6D0] mb-2')
        code_basis_select = ui.select(
            label='Code Type (applies app-wide)',
            options=CODE_BASIS_OPTIONS,
            value=CODE_BASIS_OPTIONS[0],
        ).classes('w-full mb-4')

        fcu_input = ui.number(label='Specified 28-Day Grade f_cu (N/mm2)', value=30.0, step=5.0).classes('w-full mb-4')

        ui.label('Batch Plant & Site Logs').classes('text-white font-bold text-sm mb-2')
        truck_input = ui.input(label='Mixer Truck No.', value='TRK-104').classes('w-full mb-2')
        ticket_input = ui.input(label='Batch Ticket ID', value='BT-99482').classes('w-full mb-4')

        ui.label('Mix Design Parameters').classes('text-white font-bold text-sm mb-2')
        cement_input = ui.input(label='Cement Content (kg/m3)', value='350.0').classes('w-full mb-2')
        water_input = ui.input(label='Free Water Content (kg/m3)', value='150.0').classes('w-full mb-4')

        engineer_input = ui.input(label='Engineer Name', value='Eng. Mohamed Abd Al Aty').classes('w-full mb-2')

        logo_status = ui.label('Logo: Not uploaded').classes('text-xs text-amber-400 mb-1')
        logo_bytes_holder = {'bytes': None}

        async def handle_logo_upload(e):
            try:
                logo_bytes_holder['bytes'] = await e.file.read()
                logo_status.set_text(f'Logo Loaded: {e.file.name}')
                logo_status.classes(replace='text-xs text-emerald-400 mb-1')
                ui.notify('Company logo loaded successfully!', type='positive')
            except Exception as ex:
                ui.notify(f'Error reading logo: {str(ex)}', type='negative')

        ui.upload(label='Upload Company Logo', auto_upload=True, on_upload=handle_logo_upload).props('flat dark').classes('w-full mb-2')

    ui.button('☰', on_click=sidebar.toggle).classes(
        'fixed top-4 left-4 z-50 bg-[#10203f] text-white border border-[#FF8C00] p-3 rounded-full shadow-lg hover:bg-[#1a2a4a]'
    ).style('font-size: 20px; min-width: 48px; min-height: 48px;')

    def current_meta(uid_prefix):
        return {
            'uid': f"{uid_prefix}-{uuid.uuid4().hex[:8].upper()}",
            'project': project_name_input.value,
            'location': pour_location_input.value,
            'engineer': engineer_input.value,
            'date': datetime.date.today().strftime('%Y-%m-%d'),
            'ticket': ticket_input.value,
        }

    # ---- MAIN CONTENT ----
    with ui.column().classes('w-full min-h-screen p-4 bg-[#031338]'):
        # Title block
        with ui.column().classes('w-full bg-[#0d1a35] px-6 py-4 rounded-xl border border-[#FF8C00] shadow-lg mb-4'):
            ui.label('SMART EGY-CIVIL AI AUDITOR').classes('main-title text-white')
            ui.label('Concrete Cube Statistical Verifier – ECP 203 Compliant').classes('sub-title text-lg font-medium mt-1')
            ui.label('Lead Technical Auditor: Eng. Mohamed Abd Al Aty').classes('text-base text-[#A9B6D0] font-semibold mt-1')
            ui.label('Precision‑calibrated for Egyptian Code of Practice.').classes('text-sm text-[#A9B6D0] mt-1 italic')

        # Marquee
        ui.add_head_html('''
        <style>@keyframes marquee { 0% { transform: translate(0, 0); } 100% { transform: translate(-100%, 0); } }</style>
        ''')
        ui.html('''
        <div style="width: 100%; overflow: hidden; white-space: nowrap; background-color: rgba(13,26,53,0.6); backdrop-filter: blur(8px); color: #FFFFFF; padding: 10px 0; font-weight: 600; font-size: 13px; margin-bottom: 15px; border-radius: 8px; border: 1px solid rgba(255,140,0,0.3);">
          <div style="display: inline-block; padding-left: 100%; animation: marquee 28s linear infinite;">
            <span style="color: #FF8C00;">[CORE ACTIVE]</span> ECP 203 &middot; ECP 202 &middot; ECP 104 &middot; ASTM &middot; AASHTO &middot; BS EN &middot; ISO
            &nbsp;&nbsp;|&nbsp;&nbsp; Advanced Geotechnical & Concrete Calculation Sheet &nbsp;&nbsp;|&nbsp;&nbsp; Active Site Inspection Portal
          </div>
        </div>
        ''')

        # ---- CUBE INPUT SECTION ----
        ui.label('Concrete Cube Calculation Sheet & Statistical Verifier').classes('text-2xl font-bold text-white mb-4')

        with ui.row().classes('w-full gap-4 mb-4'):
            with ui.column().classes('input-card flex-1'):
                ui.label('7-Day Cubes (comma separated, N/mm2)').classes('font-bold text-white text-sm')
                c7_input = ui.input(value='21.0, 22.5, 20.5').classes('w-full')
            with ui.column().classes('input-card flex-1'):
                ui.label('14-Day Cubes (comma separated, N/mm2)').classes('font-bold text-white text-sm')
                c14_input = ui.input(value='26.0, 27.2, 25.8').classes('w-full')
            with ui.column().classes('input-card flex-1'):
                ui.label('28-Day Cubes (comma separated, N/mm2)').classes('font-bold text-white text-sm')
                c28_input = ui.input(value='32.5, 34.0, 31.0, 35.5, 29.0, 33.0').classes('w-full')

        # ---- Results placeholders ----
        ai_cube_result_holder = {'text': ''}
        stage_stats_holder = []
        current_meta_data = {}

        # ---- Helper functions ----
        def parse_vals(txt):
            try:
                return [float(x.strip()) for x in txt.split(',') if x.strip() != '']
            except Exception:
                return []

        def compute_stats(values):
            if not values:
                return None
            arr = np.array(values, dtype=float)
            n = len(arr)
            mean = float(arr.mean())
            std = float(arr.std(ddof=1)) if n > 1 else 0.0
            return {
                'n': n,
                'mean': mean,
                'std': std,
                'min': float(arr.min()),
                'max': float(arr.max()),
                'cov': (std / mean * 100.0) if mean > 0 else 0.0,
                'sum': float(arr.sum()),
                'sum_sq': float((arr**2).sum()),
                'values': arr.tolist(),
            }

        def get_selected_stages(stage_filter):
            all_stages = [
                ('7-Day', c7_input, parse_vals(c7_input.value)),
                ('14-Day', c14_input, parse_vals(c14_input.value)),
                ('28-Day', c28_input, parse_vals(c28_input.value)),
            ]
            mapping = {'7-Day Stage': [0], '14-Day Stage': [1], '28-Day Stage': [2]}
            if stage_filter in mapping:
                idxs = mapping[stage_filter]
                return [all_stages[i] for i in idxs]
            return all_stages

        # ---- Template upload (optional) ----
        template_bytes_holder = {'bytes': None, 'name': None}
        template_status = ui.label('Template: Not uploaded').classes('text-xs text-amber-400 mb-1')

        async def handle_template_upload(e):
            try:
                template_bytes_holder['bytes'] = await e.file.read()
                template_bytes_holder['name'] = e.file.name
                template_status.set_text(f'Template: {e.file.name}')
                template_status.classes(replace='text-xs text-emerald-400 mb-1')
                ui.notify('Template uploaded successfully!', type='positive')
            except Exception as ex:
                ui.notify(f'Error: {str(ex)}', type='negative')

        def fill_template(template_bytes, data_dict):
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp:
                tmp.write(template_bytes)
                tmp_path = tmp.name
            doc = DocxTemplate(tmp_path)
            doc.render(data_dict)
            out_bytes = io.BytesIO()
            doc.save(out_bytes)
            out_bytes.seek(0)
            os.unlink(tmp_path)
            return out_bytes.getvalue()

        def build_detailed_calculations_md(stage_stats):
            md_lines = []
            for label, values, stats in stage_stats:
                if not stats:
                    continue
                md_lines.append(f"### {label} Stage")
                md_lines.append("**Raw Data (N/mm²):** " + ", ".join(f"{v:.1f}" for v in values))
                n = stats['n']
                sum_vals = stats['sum']
                sum_sq = stats['sum_sq']
                mean = stats['mean']
                std = stats['std']
                cov = stats['cov']
                md_lines.append("")
                md_lines.append("**Calculations:**")
                md_lines.append(f"- Number of specimens (n) = {n}")
                md_lines.append(f"- Sum (Σx) = {sum_vals:.2f}")
                md_lines.append(f"- Sum of squares (Σx²) = {sum_sq:.2f}")
                md_lines.append(f"- Mean (x̄) = Σx / n = {sum_vals:.2f} / {n} = **{mean:.2f}** N/mm²")
                md_lines.append(f"- Standard deviation (s) = sqrt((Σx² - (Σx)²/n) / (n-1)) = **{std:.2f}** N/mm²")
                md_lines.append(f"- Coefficient of variation (COV) = (s / x̄) × 100 = **{cov:.1f}%**")
                md_lines.append(f"- Minimum = {stats['min']:.1f} N/mm²")
                md_lines.append(f"- Maximum = {stats['max']:.1f} N/mm²")
                md_lines.append("")
                md_lines.append("**Individual Deviations from Mean:**")
                dev_table = "| Specimen | Strength | Deviation (x - x̄) |"
                dev_table += "\n|----------|----------|-------------------|"
                for idx, v in enumerate(values):
                    dev = v - mean
                    dev_table += f"\n| #{idx+1} | {v:.1f} | {dev:+.2f} |"
                md_lines.append(dev_table)
                md_lines.append("")
            return "\n".join(md_lines)

        # ---- Predictive Analysis & Charts (new) ----
        def create_predictive_charts(stage_stats):
            if not stage_stats:
                return None, None, None, None
            # Combine all values with stage labels for histogram
            all_vals = []
            all_labels = []
            for label, values, stats in stage_stats:
                if stats:
                    all_vals.extend(values)
                    all_labels.extend([label]*len(values))
            if not all_vals:
                return None, None, None, None

            # Histogram
            hist_fig = go.Figure()
            hist_fig.add_trace(go.Histogram(
                x=all_vals,
                nbinsx=10,
                marker_color='#FF8C00',
                opacity=0.7,
                name='Strengths'
            ))
            hist_fig.update_layout(
                title='Distribution of All Cube Strengths',
                xaxis_title='Strength (N/mm²)',
                yaxis_title='Frequency',
                template='plotly_dark',
                paper_bgcolor='#0d1a35',
                plot_bgcolor='#0d1a35',
                height=300
            )

            # Time series (assuming order: 7-day, 14-day, 28-day within each)
            # We'll create a sequence index and plot values
            seq_vals = []
            seq_labels = []
            for label, values, stats in stage_stats:
                if stats:
                    seq_vals.extend(values)
                    seq_labels.extend([label]*len(values))
            x_seq = list(range(1, len(seq_vals)+1))
            time_fig = go.Figure()
            time_fig.add_trace(go.Scatter(
                x=x_seq,
                y=seq_vals,
                mode='lines+markers',
                marker=dict(color='#4FC3F7', size=8),
                line=dict(color='#FF8C00', width=2),
                name='Strengths'
            ))
            # Add trend line (linear regression)
            if len(x_seq) > 1:
                from scipy import stats as scipy_stats
                slope, intercept, r_value, p_value, std_err = scipy_stats.linregress(x_seq, seq_vals)
                trend_y = [slope*x + intercept for x in x_seq]
                time_fig.add_trace(go.Scatter(
                    x=x_seq,
                    y=trend_y,
                    mode='lines',
                    line=dict(color='#22C55E', width=2, dash='dash'),
                    name=f'Trend (R²={r_value**2:.3f})'
                ))
            time_fig.update_layout(
                title='Strength Progression (Sequential)',
                xaxis_title='Sample Index',
                yaxis_title='Strength (N/mm²)',
                template='plotly_dark',
                paper_bgcolor='#0d1a35',
                plot_bgcolor='#0d1a35',
                height=300
            )

            # Control chart (X-bar) – using overall mean and moving range
            # For simplicity, we use overall mean and standard deviation for UCL/LCL
            overall_mean = np.mean(seq_vals)
            overall_std = np.std(seq_vals)
            ucl = overall_mean + 3 * overall_std
            lcl = overall_mean - 3 * overall_std
            control_fig = go.Figure()
            control_fig.add_trace(go.Scatter(
                x=x_seq,
                y=seq_vals,
                mode='lines+markers',
                marker=dict(color='#4FC3F7', size=8),
                line=dict(color='#FF8C00', width=2),
                name='Values'
            ))
            control_fig.add_hline(y=overall_mean, line_dash="solid", line_color="#22C55E", annotation_text="Mean")
            control_fig.add_hline(y=ucl, line_dash="dash", line_color="#FF0000", annotation_text="UCL")
            control_fig.add_hline(y=lcl, line_dash="dash", line_color="#FF0000", annotation_text="LCL")
            control_fig.update_layout(
                title='Control Chart (X-bar)',
                xaxis_title='Sample Index',
                yaxis_title='Strength (N/mm²)',
                template='plotly_dark',
                paper_bgcolor='#0d1a35',
                plot_bgcolor='#0d1a35',
                height=300
            )

            # Simple forecast – linear regression for next 3 points
            if len(x_seq) > 1:
                slope, intercept, r_value, p_value, std_err = scipy_stats.linregress(x_seq, seq_vals)
                future_x = list(range(len(x_seq)+1, len(x_seq)+4))
                future_y = [slope*x + intercept for x in future_x]
                forecast_fig = go.Figure()
                forecast_fig.add_trace(go.Scatter(
                    x=x_seq,
                    y=seq_vals,
                    mode='lines+markers',
                    marker=dict(color='#4FC3F7', size=8),
                    line=dict(color='#FF8C00', width=2),
                    name='Historical'
                ))
                forecast_fig.add_trace(go.Scatter(
                    x=future_x,
                    y=future_y,
                    mode='lines+markers+text',
                    text=[f"{y:.1f}" for y in future_y],
                    textposition="top center",
                    marker=dict(color='#22C55E', size=10),
                    line=dict(color='#22C55E', width=2, dash='dot'),
                    name='Forecast'
                ))
                forecast_fig.update_layout(
                    title='Predictive Forecast (Next 3 Tests)',
                    xaxis_title='Sample Index',
                    yaxis_title='Strength (N/mm²)',
                    template='plotly_dark',
                    paper_bgcolor='#0d1a35',
                    plot_bgcolor='#0d1a35',
                    height=300
                )
                return hist_fig, time_fig, control_fig, forecast_fig
            else:
                return hist_fig, time_fig, control_fig, None

        # ---- Main run function ----
        async def run_verification():
            result_output_area.clear()
            export_buttons_area.clear()
            chart_area.clear()
            stats_area.clear()
            calc_panel.clear()
            # Predictive tab will be filled after calculation
            predictive_charts_area.clear()

            nonlocal stage_stats_holder, current_meta_data

            if not client:
                ui.notify('GEMINI_API_KEY missing in .env!', type='negative')
                return

            with result_output_area:
                ui.spinner('ios', size='lg').classes('self-center text-[#4FC3F7]')
                ui.label('Running AI statistical evaluation & code compliance verification...').classes('self-center text-sm')

            try:
                stage_filter = stage_selector.value
                stages = get_selected_stages(stage_filter)
                target_fcu = float(fcu_input.value) if fcu_input.value else 30.0
                basis = code_basis_select.value

                stage_stats = []
                for label, _inp, values in stages:
                    s = compute_stats(values)
                    stage_stats.append((label, values, s))
                stage_stats_holder = stage_stats

                meta = current_meta('ECP-AI')
                current_meta_data = meta

                # Stats chips
                stats_area.clear()
                with stats_area:
                    with ui.row().classes('w-full gap-4 flex-wrap mb-2'):
                        for label, values, s in stage_stats:
                            if not s:
                                continue
                            with ui.column().classes('stat-chip'):
                                ui.label(f"{s['mean']:.2f}").classes('val')
                                ui.label(f'{label} Mean (N/mm2)').classes('lbl')
                            with ui.column().classes('stat-chip'):
                                ui.label(f"{s['std']:.2f}").classes('val')
                                ui.label(f'{label} Std Dev').classes('lbl')
                            with ui.column().classes('stat-chip'):
                                ui.label(f"{s['min']:.1f} / {s['max']:.1f}").classes('val')
                                ui.label(f'{label} Min / Max').classes('lbl')

                stage_data_text = "\n".join(
                    f"- {label} Crushing Values (N/mm2): {', '.join(str(v) for v in values) if values else 'No data provided'} "
                    f"(n={s['n'] if s else 0}, mean={s['mean']:.2f} if s else 'n/a')"
                    for label, values, s in stage_stats
                )

                prompt = f"""
You are an elite Senior Concrete Quality Assurance and Structural Engineering Expert.
Perform a complete, professional statistical evaluation and code-compliance verification
for the concrete cube test results below. Only evaluate the stage(s) actually provided.

{get_code_directive(basis)}

{NO_LATEX_RULE}

DISPLAY FILTER SELECTED BY USER: {stage_filter}
(Only discuss the stage(s) listed below in detail; do not invent data for stages not listed.)

PROJECT PARAMETERS:
- Specified 28-Day Characteristic Compressive Strength (f_cu): {target_fcu} N/mm2
{stage_data_text}
- Mix Details: Cement = {cement_input.value} kg/m3, Water = {water_input.value} kg/m3
- Truck No: {truck_input.value} | Ticket ID: {ticket_input.value}

REQUIRED REPORT STRUCTURE:
1. A Markdown table per stage: Specimen ID, Crushing Strength, Deviation from Mean, Individual Limit Check.
2. A short statistical commentary (mean, standard deviation, coefficient of variation) referencing the numbers above.
3. A clear final compliance verdict (PASS / FAIL) with the specific ECP 203 (or selected code) clause used to judge it.
"""

                res_text = await call_gemini(prompt)
                ai_cube_result_holder['text'] = res_text

                result_output_area.clear()
                with result_output_area:
                    with ui.column().classes('output-card w-full'):
                        ui.label('Statistical Evaluation & Compliance Verdict').classes('text-xl font-bold text-white mb-2')
                        ui.markdown(res_text).classes('markdown-body')

                # Chart (main)
                with chart_area:
                    labels = [label for label, _v, _s in stage_stats] + ['Target Grade']
                    means = [(s['mean'] if s else 0) for _l, _v, s in stage_stats] + [target_fcu]
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=labels, y=means, mode='lines+markers+text',
                        text=[f"{v:.1f}" for v in means], textposition="top center",
                        line=dict(color='#4FC3F7', width=3), marker=dict(size=10, color='#FF8C00'),
                    ))
                    fig.add_hline(y=target_fcu, line_dash="dash", line_color="#22C55E",
                                  annotation_text=f"Target f_cu ({target_fcu} N/mm2)", annotation_position="bottom right")
                    fig.update_layout(
                        title=f'Compressive Strength — {stage_filter}',
                        template='plotly_dark', paper_bgcolor='#0d1a35', plot_bgcolor='#0d1a35',
                        margin=dict(t=40, b=20, l=40, r=20), height=340,
                    )
                    ui.plotly(fig).classes('w-full mt-2')

                # ---- Detailed Calculations Panel ----
                calc_panel.clear()
                with calc_panel:
                    with ui.expansion('📊 View Detailed Calculations (full math breakdown)', icon='calculate', value=True).classes('w-full bg-[#0d1a35] rounded-lg mt-4'):
                        md = build_detailed_calculations_md(stage_stats)
                        ui.markdown(md).classes('markdown-body')

                # ---- Predictive Analysis & Charts (populate the new tab) ----
                predictive_charts_area.clear()
                with predictive_charts_area:
                    ui.label('Predictive Analysis & Advanced Charts').classes('text-xl font-bold text-white mb-2')
                    hist_fig, time_fig, control_fig, forecast_fig = create_predictive_charts(stage_stats)
                    if hist_fig:
                        with ui.row().classes('w-full flex-wrap'):
                            with ui.column().classes('w-full md:w-1/2 p-2'):
                                ui.plotly(hist_fig).classes('w-full')
                            with ui.column().classes('w-full md:w-1/2 p-2'):
                                ui.plotly(time_fig).classes('w-full')
                        with ui.row().classes('w-full flex-wrap'):
                            with ui.column().classes('w-full md:w-1/2 p-2'):
                                ui.plotly(control_fig).classes('w-full')
                            with ui.column().classes('w-full md:w-1/2 p-2'):
                                if forecast_fig:
                                    ui.plotly(forecast_fig).classes('w-full')
                                else:
                                    ui.label('Forecast not available (need at least 2 data points).').classes('text-amber-400')
                    else:
                        ui.label('Not enough data for predictive charts. Please provide at least one value per stage.').classes('text-amber-400')

                # ---- EXPORT BUTTONS (updated titles without "AI") ----
                with export_buttons_area:
                    def download_normal_pdf():
                        try:
                            meta = current_meta('ECP-AI')
                            pdf_bytes = build_report_pdf(
                                "CONCRETE CUBE CALCULATION & VERIFICATION REPORT",  # removed "AI"
                                f"Governing Standard: {basis} | Filter: {stage_filter}",
                                ai_cube_result_holder['text'], meta, logo_bytes_holder['bytes'],
                                extra_flowables_before_body=[
                                    Paragraph("Deterministic Statistics", build_pdf_styles()['h2']),
                                    build_stats_table(stage_stats, USABLE_WIDTH),
                                ],
                            )
                            ui.download(pdf_bytes, filename=f"Concrete_Report_{ticket_input.value}.pdf")
                            ui.notify('PDF downloaded!', type='positive')
                        except Exception as ex:
                            ui.notify(f'PDF Error: {str(ex)}', type='negative')

                    def build_stats_table(stage_stats, width):
                        styles = build_pdf_styles()
                        stat_rows = [["Stage", "n", "Mean (N/mm2)", "Std Dev", "Min", "Max", "COV %"]]
                        for label, values, s in stage_stats:
                            if s:
                                stat_rows.append([label, str(s['n']), f"{s['mean']:.2f}", f"{s['std']:.2f}",
                                                   f"{s['min']:.1f}", f"{s['max']:.1f}", f"{s['cov']:.1f}"])
                        colw = width / len(stat_rows[0])
                        table_data = [[Paragraph(c, styles['tablehead'] if r == 0 else styles['tablecell'])
                                       for c in row] for r, row in enumerate(stat_rows)]
                        t = Table(table_data, colWidths=[colw] * len(stat_rows[0]))
                        t.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1B2A4A')),
                            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#94A3B8')),
                            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F1F5F9')]),
                            ('TOPPADDING', (0, 0), (-1, -1), 4),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                        ]))
                        return t

                    def download_normal_word():
                        try:
                            doc = Document()
                            doc.add_heading('Concrete Cube Verification Report', 0)  # removed "AI"
                            doc.add_paragraph(f'Project: {project_name_input.value}')
                            doc.add_paragraph(f'Location: {pour_location_input.value}')
                            doc.add_paragraph(f'Engineer: {engineer_input.value}')
                            doc.add_paragraph(f'Date: {datetime.date.today().strftime("%Y-%m-%d")}')
                            doc.add_paragraph(f'Ticket ID: {ticket_input.value}')
                            doc.add_paragraph(f'Code Basis: {basis}')
                            doc.add_paragraph(f'Target f_cu: {fcu_input.value} N/mm2')
                            doc.add_heading('Statistical Summary', level=1)
                            table = doc.add_table(rows=1, cols=7)
                            hdr_cells = table.rows[0].cells
                            headers = ['Stage', 'n', 'Mean', 'Std Dev', 'Min', 'Max', 'COV %']
                            for i, h in enumerate(headers):
                                hdr_cells[i].text = h
                            for label, values, s in stage_stats:
                                if s:
                                    row_cells = table.add_row().cells
                                    row_cells[0].text = label
                                    row_cells[1].text = str(s['n'])
                                    row_cells[2].text = f"{s['mean']:.2f}"
                                    row_cells[3].text = f"{s['std']:.2f}"
                                    row_cells[4].text = f"{s['min']:.1f}"
                                    row_cells[5].text = f"{s['max']:.1f}"
                                    row_cells[6].text = f"{s['cov']:.1f}"
                            doc.add_heading('Compliance Evaluation', level=1)  # removed "AI"
                            doc.add_paragraph(ai_cube_result_holder['text'])
                            out = io.BytesIO()
                            doc.save(out)
                            out.seek(0)
                            ui.download(out.getvalue(), filename=f"Concrete_Report_{ticket_input.value}.docx")
                            ui.notify('Word document downloaded!', type='positive')
                        except Exception as ex:
                            ui.notify(f'Word export error: {str(ex)}', type='negative')

                    def download_filled_template():
                        if template_bytes_holder['bytes'] is None:
                            ui.notify('No template uploaded.', type='warning')
                            return
                        try:
                            data = {}
                            meta = current_meta('TEMPLATE')
                            data['project_name'] = meta['project']
                            data['location'] = meta['location']
                            data['engineer'] = meta['engineer']
                            data['date'] = meta['date']
                            data['ticket_id'] = meta['ticket']
                            data['target_fcu'] = fcu_input.value
                            data['basis'] = code_basis_select.value
                            for label, values, s in stage_stats:
                                if s:
                                    key = label.lower().replace('-', '_')
                                    data[f'stage_{key}_mean'] = f"{s['mean']:.2f}"
                                    data[f'stage_{key}_std'] = f"{s['std']:.2f}"
                                    data[f'stage_{key}_min'] = f"{s['min']:.1f}"
                                    data[f'stage_{key}_max'] = f"{s['max']:.1f}"
                                    data[f'stage_{key}_n'] = s['n']
                                    data[f'stage_{key}_cov'] = f"{s['cov']:.1f}"
                                    data[f'stage_{key}_values'] = ', '.join(str(v) for v in values)
                            data['ai_verdict'] = ai_cube_result_holder['text']
                            filled_bytes = fill_template(template_bytes_holder['bytes'], data)
                            ui.download(filled_bytes, filename=f"Filled_Template_{ticket_input.value}.docx")
                            ui.notify('Filled template downloaded!', type='positive')
                        except Exception as ex:
                            ui.notify(f'Error filling template: {str(ex)}', type='negative')

                    def download_calc_pdf():
                        try:
                            meta = current_meta('CALC')
                            styles = build_pdf_styles()
                            calc_rows = [["Stage", "Specimen", "Strength", "Deviation"]]
                            for label, values, s in stage_stats:
                                if s:
                                    mean = s['mean']
                                    for idx, val in enumerate(values):
                                        dev = val - mean
                                        calc_rows.append([label, f"#{idx+1}", f"{val:.1f}", f"{dev:+.2f}"])
                                    calc_rows.append([label, "Mean", f"{mean:.2f}", ""])
                                    calc_rows.append([label, "Std Dev", f"{s['std']:.2f}", ""])
                                    calc_rows.append([label, "Min", f"{s['min']:.1f}", ""])
                                    calc_rows.append([label, "Max", f"{s['max']:.1f}", ""])
                                    calc_rows.append([label, "COV %", f"{s['cov']:.1f}", ""])
                                    calc_rows.append([label, "n", str(s['n']), ""])
                                    calc_rows.append([label, "Σx", f"{s['sum']:.2f}", ""])
                                    calc_rows.append([label, "Σx²", f"{s['sum_sq']:.2f}", ""])
                            colw = USABLE_WIDTH / 4
                            table_data = [[Paragraph(c, styles['tablehead'] if r == 0 else styles['tablecell'])
                                           for c in row] for r, row in enumerate(calc_rows)]
                            t = Table(table_data, colWidths=[colw]*4)
                            t.setStyle(TableStyle([
                                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1B2A4A')),
                                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#94A3B8')),
                                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F1F5F9')]),
                                ('TOPPADDING', (0, 0), (-1, -1), 4),
                                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                            ]))
                            formula_flowables = []
                            for label, values, s in stage_stats:
                                if s:
                                    formula_flowables.append(Paragraph(f"{label} Stage Calculations", styles['h3']))
                                    formula_flowables.append(Paragraph(f"n = {s['n']}, Σx = {s['sum']:.2f}, Σx² = {s['sum_sq']:.2f}", styles['body']))
                                    formula_flowables.append(Paragraph(f"Mean = {s['sum']:.2f} / {s['n']} = {s['mean']:.2f}", styles['body']))
                                    formula_flowables.append(Paragraph(f"Std Dev = sqrt(({s['sum_sq']:.2f} - ({s['sum']:.2f})²/{s['n']}) / ({s['n']-1})) = {s['std']:.2f}", styles['body']))
                                    formula_flowables.append(Spacer(1, 6))
                            pdf_bytes = build_report_pdf(
                                "DETAILED CONCRETE CUBE CALCULATIONS",
                                f"Calculations for {meta['project']}",
                                "", meta, logo_bytes_holder['bytes'],
                                extra_flowables_before_body=[
                                    Paragraph("Complete Calculation Breakdown", styles['h2']),
                                    t,
                                    Spacer(1, 6),
                                    Paragraph("Formulas & Intermediate Values", styles['h2']),
                                    *formula_flowables,
                                    Spacer(1, 6),
                                    Paragraph("Compliance Evaluation Summary", styles['h2']),
                                    *markdown_to_pdf_flowables(ai_cube_result_holder['text'], styles),
                                ]
                            )
                            ui.download(pdf_bytes, filename=f"Detailed_Calculations_{ticket_input.value}.pdf")
                            ui.notify('Calculations PDF downloaded!', type='positive')
                        except Exception as ex:
                            ui.notify(f'Calc PDF error: {str(ex)}', type='negative')

                    def download_calc_word():
                        try:
                            doc = Document()
                            doc.add_heading('Detailed Concrete Cube Calculations', 0)
                            doc.add_paragraph(f'Project: {project_name_input.value}')
                            doc.add_paragraph(f'Ticket ID: {ticket_input.value}')
                            doc.add_heading('Individual Specimen Data', level=1)
                            table = doc.add_table(rows=1, cols=4)
                            hdr = table.rows[0].cells
                            hdr[0].text = 'Stage'
                            hdr[1].text = 'Specimen'
                            hdr[2].text = 'Strength (N/mm2)'
                            hdr[3].text = 'Deviation'
                            for label, values, s in stage_stats:
                                if s:
                                    mean = s['mean']
                                    for idx, val in enumerate(values):
                                        row = table.add_row().cells
                                        row[0].text = label
                                        row[1].text = f"#{idx+1}"
                                        row[2].text = f"{val:.1f}"
                                        row[3].text = f"{val - mean:+.2f}"
                                    row = table.add_row().cells
                                    row[0].text = label
                                    row[1].text = 'Mean'
                                    row[2].text = f"{mean:.2f}"
                                    row[3].text = ''
                                    row = table.add_row().cells
                                    row[0].text = label
                                    row[1].text = 'Std Dev'
                                    row[2].text = f"{s['std']:.2f}"
                                    row[3].text = ''
                                    row = table.add_row().cells
                                    row[0].text = label
                                    row[1].text = 'Min'
                                    row[2].text = f"{s['min']:.1f}"
                                    row[3].text = ''
                                    row = table.add_row().cells
                                    row[0].text = label
                                    row[1].text = 'Max'
                                    row[2].text = f"{s['max']:.1f}"
                                    row[3].text = ''
                                    row = table.add_row().cells
                                    row[0].text = label
                                    row[1].text = 'COV %'
                                    row[2].text = f"{s['cov']:.1f}"
                                    row[3].text = ''
                                    row = table.add_row().cells
                                    row[0].text = label
                                    row[1].text = 'n'
                                    row[2].text = str(s['n'])
                                    row[3].text = ''
                                    row = table.add_row().cells
                                    row[0].text = label
                                    row[1].text = 'Σx'
                                    row[2].text = f"{s['sum']:.2f}"
                                    row[3].text = ''
                                    row = table.add_row().cells
                                    row[0].text = label
                                    row[1].text = 'Σx²'
                                    row[2].text = f"{s['sum_sq']:.2f}"
                                    row[3].text = ''
                            doc.add_heading('Compliance Verdict', level=1)
                            doc.add_paragraph(ai_cube_result_holder['text'])
                            out = io.BytesIO()
                            doc.save(out)
                            out.seek(0)
                            ui.download(out.getvalue(), filename=f"Detailed_Calculations_{ticket_input.value}.docx")
                            ui.notify('Calculations Word downloaded!', type='positive')
                        except Exception as ex:
                            ui.notify(f'Calc Word error: {str(ex)}', type='negative')

                    # Buttons
                    with ui.row().classes('w-full gap-4 flex-wrap'):
                        ui.button('📄 Download Normal PDF', on_click=download_normal_pdf).classes('primary-btn')
                        ui.button('📝 Download Normal Word', on_click=download_normal_word).classes('primary-btn')
                        if template_bytes_holder['bytes']:
                            ui.button('📎 Download Filled Template', on_click=download_filled_template).classes('primary-btn')
                        ui.button('📊 Download Calculations PDF', on_click=download_calc_pdf).classes('primary-btn')
                        ui.button('📊 Download Calculations Word', on_click=download_calc_word).classes('primary-btn')

                # ---- Chatbots (recreated each run) ----
                chat_toggle_row = ui.row().classes('w-full gap-4 mt-4')
                with chat_toggle_row:
                    chat_result_visible = {'show': False}
                    chat_code_visible = {'show': False}

                    def toggle_result_chat():
                        chat_result_visible['show'] = not chat_result_visible['show']
                        chat_result_panel.set_visibility(chat_result_visible['show'])

                    def toggle_code_chat():
                        chat_code_visible['show'] = not chat_code_visible['show']
                        chat_code_panel.set_visibility(chat_code_visible['show'])

                    ui.button('💬 Ask about Results', on_click=toggle_result_chat).classes('primary-btn')
                    ui.button('📚 Ask about Egyptian Code', on_click=toggle_code_chat).classes('primary-btn')

                # Result Chat Panel
                chat_result_panel = ui.column().classes('output-card w-full mt-4')
                chat_result_panel.set_visibility(False)
                with chat_result_panel:
                    with ui.column().classes('input-card w-full'):
                        ui.label('Chat about these cube results').classes('text-lg font-bold text-white')
                        result_chat_container = ui.column().classes('w-full h-[300px] overflow-y-auto')
                        result_chat_messages = [{"role": "assistant", "content": "Ask me anything about the cube test results above."}]
                        def render_result_chat():
                            result_chat_container.clear()
                            with result_chat_container:
                                for msg in result_chat_messages:
                                    is_ai = msg['role'] == 'assistant'
                                    with ui.column().classes('chat-message'):
                                        role_label = 'Assistant' if is_ai else 'You'
                                        label_class = 'assistant' if is_ai else 'user'
                                        ui.label(role_label).classes(f'role-label {label_class}')
                                        ui.markdown(msg['content']).classes('content markdown-body')
                        render_result_chat()
                        result_chat_input = ui.input(placeholder='Ask about these results...').classes('w-full mb-2')
                        result_chat_input.on('keydown.enter', lambda: send_result_chat())
                        async def send_result_chat():
                            q = result_chat_input.value
                            if not q or not q.strip():
                                return
                            result_chat_messages.append({"role": "user", "content": q})
                            result_chat_input.value = ''
                            render_result_chat()
                            context = f"""
Project: {project_name_input.value}
Location: {pour_location_input.value}
Target f_cu: {fcu_input.value} N/mm2
Code Basis: {code_basis_select.value}
Stages:
"""
                            for label, values, s in stage_stats:
                                if s:
                                    context += f"- {label}: n={s['n']}, mean={s['mean']:.2f}, std={s['std']:.2f}, min={s['min']:.1f}, max={s['max']:.1f}, COV={s['cov']:.1f}%\n"
                            context += f"\nCompliance Verdict:\n{ai_cube_result_holder['text']}"
                            system_prompt = f"You are an expert concrete engineer. Answer the user's question based on the following cube test results. Provide clear, professional advice. Results:\n{context}"
                            try:
                                resp = await call_gemini(q, system_instruction=system_prompt)
                                result_chat_messages.append({"role": "assistant", "content": resp})
                            except Exception as e:
                                result_chat_messages.append({"role": "assistant", "content": f"Error: {str(e)}"})
                            render_result_chat()
                        ui.button('Send', on_click=send_result_chat).classes('primary-btn')

                # Code Chat Panel
                chat_code_panel = ui.column().classes('output-card w-full mt-4')
                chat_code_panel.set_visibility(False)
                with chat_code_panel:
                    with ui.column().classes('input-card w-full'):
                        ui.label('Chat about Egyptian Codes (ECP 203, 202, 104)').classes('text-lg font-bold text-white')
                        code_chat_container = ui.column().classes('w-full h-[300px] overflow-y-auto')
                        code_chat_messages = [{"role": "assistant", "content": "Ask me about Egyptian code requirements for concrete, soil, or pavements."}]
                        def render_code_chat():
                            code_chat_container.clear()
                            with code_chat_container:
                                for msg in code_chat_messages:
                                    is_ai = msg['role'] == 'assistant'
                                    with ui.column().classes('chat-message'):
                                        role_label = 'Assistant' if is_ai else 'You'
                                        label_class = 'assistant' if is_ai else 'user'
                                        ui.label(role_label).classes(f'role-label {label_class}')
                                        ui.markdown(msg['content']).classes('content markdown-body')
                        render_code_chat()
                        code_chat_input = ui.input(placeholder='Ask about Egyptian codes...').classes('w-full mb-2')
                        code_chat_input.on('keydown.enter', lambda: send_code_chat())
                        async def send_code_chat():
                            q = code_chat_input.value
                            if not q or not q.strip():
                                return
                            code_chat_messages.append({"role": "user", "content": q})
                            code_chat_input.value = ''
                            render_code_chat()
                            system_prompt = f"""
You are an expert in Egyptian construction codes (ECP 203, ECP 202, ECP 104).
Answer the user's question accurately, referencing specific clauses where possible.
Governing standard: {code_basis_select.value}
{get_code_directive(code_basis_select.value)}
{NO_LATEX_RULE}
"""
                            try:
                                resp = await call_gemini(q, system_instruction=system_prompt)
                                code_chat_messages.append({"role": "assistant", "content": resp})
                            except Exception as e:
                                code_chat_messages.append({"role": "assistant", "content": f"Error: {str(e)}"})
                            render_code_chat()
                        ui.button('Send', on_click=send_code_chat).classes('primary-btn')

            except Exception as ex:
                result_output_area.clear()
                with result_output_area:
                    ui.notify(f'Calculation Error: {str(ex)}', type='negative')
                    ui.markdown(f'**Error:** {str(ex)}').classes('text-red-400')

        # ---- UI Elements ----
        stage_selector = ui.select(
            label='Select Stage Display Filter',
            options=['All Stages', '7-Day Stage', '14-Day Stage', '28-Day Stage'],
            value='All Stages',
            on_change=run_verification,
        ).classes('w-full md:w-1/3 mb-4')

        stats_area = ui.column().classes('w-full')
        result_output_area = ui.column().classes('w-full')
        chart_area = ui.column().classes('w-full')
        export_buttons_area = ui.row().classes('w-full gap-4 flex-wrap mt-4')
        calc_panel = ui.column().classes('w-full mt-4')
        # New predictive area – we'll show it after calculation
        predictive_charts_area = ui.column().classes('w-full mt-4')

        # Template upload (optional)
        with ui.row().classes('w-full gap-4 items-center mb-4'):
            ui.upload(label='Upload Company Template (DOCX with placeholders)',
                      auto_upload=True,
                      on_upload=handle_template_upload).props('flat dark').classes('flex-1')
            template_status

        ui.button('Run Statistical Calculation & Verification', on_click=run_verification).classes('primary-btn q-my-md')
        with result_output_area:
            ui.markdown('*Click "Run Statistical Calculation & Verification" to generate the report and charts.*').classes('text-sm text-[#A9B6D0]')

        # ---- FOOTER ----
        ui.html('''
        <div class="app-footer">
            <b>Multi-Standard Engineering Quality Assurance Portal</b> &nbsp;|&nbsp; Automated compliance verification across ECP 203, ECP 202, ECP 104, ASTM, AASHTO, BS, EN, and ISO standards.<br>
            <b>Official Direct Contacts:</b>
            LinkedIn: <a href="https://www.linkedin.com/in/mohamed-abd-al-aty-a326a1214/" target="_blank">Mohamed Abd Al Aty</a> &nbsp;|&nbsp;
            Email: <a href="mailto:mohamedabdalaty63@gmail.com">mohamedabdalaty63@gmail.com</a><br>
            <i>Specialized in QA/QC, Civil Engineering Standards &amp; Automated Compliance.</i> &copy; 2026 Eng. Mohamed Abd Al Aty. All rights reserved.<br>
            <span style="color: #FFFFFF; font-weight: 600;">Disclaimer:</span> These modules have high accuracy and are specified for the Egyptian codes, but results should be rechecked by a qualified engineer before any decision-making.
        </div>
        ''')


if __name__ == '__main__':
    ui.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 8080)),
        title='Concrete Cube Verifier',
        favicon='🏗️',
        reload=False,
        reconnect_timeout=30.0,
    )
