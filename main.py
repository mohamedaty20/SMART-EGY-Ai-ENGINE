import io
import datetime
import os
import uuid
import re
import asyncio
import json
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import qrcode
from docxtpl import DocxTemplate
from docx import Document
from scipy import stats
from plotly.subplots import make_subplots

# Dotenv & FastAPI / NiceGUI
from dotenv import load_dotenv
from fastapi import FastAPI
from nicegui import app, ui, run

# Google GenAI SDK
from google import genai
from google.genai import types

# ReportLab
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
# I18N
# =====================================================================
TEXTS = {
    'en': {
        'app_title': 'SMART EGY-CIVIL AI AUDITOR',
        'app_sub': 'Concrete Cube Statistical Verifier – ECP 203 Compliant',
        'lead_auditor': 'Lead Technical Auditor: Eng. Mohamed Abd Al Aty',
        'tagline': 'Precision‑calibrated for Egyptian Code of Practice.',
        'project_metadata': '📋 PROJECT METADATA',
        'project_name': 'Project Name',
        'location': 'Structural Element / Chainage',
        'code_basis': 'Governing Design Code Basis',
        'code_hint': 'By default every AI output in this app is generated strictly per **ECP 203 / ECP 202 / ECP 104**. Change this to switch the primary basis.',
        'fcu': 'Specified 28-Day Grade f_cu (N/mm2)',
        'batch_plant': 'Batch Plant & Site Logs',
        'truck': 'Mixer Truck No.',
        'ticket': 'Batch Ticket ID',
        'mix_design': 'Mix Design Parameters',
        'cement': 'Cement Content (kg/m3)',
        'water': 'Free Water Content (kg/m3)',
        'engineer': 'Engineer Name',
        'logo': 'Logo: Not uploaded',
        'logo_upload': 'Upload Company Logo',
        'run_button': 'Run Statistical Calculation & Verification',
        'run_hint': 'Click "Run Statistical Calculation & Verification" to generate the report and charts.',
        '7day': '7-Day Cubes (comma separated, N/mm2)',
        '14day': '14-Day Cubes (comma separated, N/mm2)',
        '28day': '28-Day Cubes (comma separated, N/mm2)',
        'stage_filter': 'Select Stage Display Filter',
        'all_stages': 'All Stages',
        '7day_stage': '7-Day Stage',
        '14day_stage': '14-Day Stage',
        '28day_stage': '28-Day Stage',
        'detailed_calc': '📊 View Detailed Calculations (full math breakdown)',
        'download_pdf': '📄 Download Normal PDF',
        'download_word': '📝 Download Normal Word',
        'download_template': '📎 Download Filled Template',
        'download_calc_pdf': '📊 Download Calculations PDF',
        'download_calc_word': '📊 Download Calculations Word',
        'ask_results': '💬 Ask about Results',
        'ask_code': '📚 Ask about Egyptian Code',
        'dashboard': '📈 Dashboard',
        'batch_compare': '📊 Batch Comparison',
        'audit_trail': '📜 Audit Trail',
        'settings': '⚙️ Settings',
        'dark_mode': 'Dark Mode',
        'light_mode': 'Light Mode',
        'help_tour': '🎯 Start Tour',
        'contextual_help': '❓ Help',
        'load_example': '📥 Load Example',
        'save_state': '💾 Save State',
        'language': 'Language',
        'english': 'English',
        'arabic': 'العربية',
        'example_loaded': 'Example data loaded!',
        'state_saved': 'State saved to browser storage.',
        'not_enough_data': 'Not enough data for predictive charts (need at least 2 values).',
    },
    'ar': {
        'app_title': 'المدقق الذكي – الهندسة المدنية المصرية',
        'app_sub': 'مدقق المكعبات الخرسانية – متوافق مع الكود المصري ECP 203',
        'lead_auditor': 'المدقق الفني الرئيسي: مهندس محمد عبد العاطي',
        'tagline': 'معايرة دقيقة لكود الممارسة المصري.',
        'project_metadata': '📋 بيانات المشروع',
        'project_name': 'اسم المشروع',
        'location': 'العنصر الإنشائي / المقطع',
        'code_basis': 'أساس الكود التصميمي',
        'code_hint': 'افتراضيًا، يتم إنشاء كل مخرجات الذكاء الاصطناعي وفقًا لـ **ECP 203 / ECP 202 / ECP 104**. غيِّر هذا لتبديل الأساس الرئيسي.',
        'fcu': 'مقاومة الضغط المميزة f_cu (نيوتن/مم²)',
        'batch_plant': 'بيانات الخلاطة والموقع',
        'truck': 'رقم شاحنة الخلط',
        'ticket': 'رقم تذكرة الخلطة',
        'mix_design': 'بارامترات تصميم الخلطة',
        'cement': 'محتوى الأسمنت (كجم/م³)',
        'water': 'محتوى الماء الحر (كجم/م³)',
        'engineer': 'اسم المهندس',
        'logo': 'الشعار: لم يتم الرفع',
        'logo_upload': 'رفع شعار الشركة',
        'run_button': 'تشغيل التحليل الإحصائي والتحقق من المطابقة',
        'run_hint': 'انقر "تشغيل التحليل الإحصائي..." لإنشاء التقرير والرسوم البيانية.',
        '7day': 'مكعبات 7 أيام (مفصولة بفواصل، نيوتن/مم²)',
        '14day': 'مكعبات 14 يومًا (مفصولة بفواصل، نيوتن/مم²)',
        '28day': 'مكعبات 28 يومًا (مفصولة بفواصل، نيوتن/مم²)',
        'stage_filter': 'اختيار مرحلة العرض',
        'all_stages': 'كل المراحل',
        '7day_stage': 'مرحلة 7 أيام',
        '14day_stage': 'مرحلة 14 يومًا',
        '28day_stage': 'مرحلة 28 يومًا',
        'detailed_calc': '📊 عرض الحسابات التفصيلية (تفصيل كامل)',
        'download_pdf': '📄 تحميل PDF عادي',
        'download_word': '📝 تحميل Word عادي',
        'download_template': '📎 تحميل النموذج المملوء',
        'download_calc_pdf': '📊 تحميل حسابات PDF',
        'download_calc_word': '📊 تحميل حسابات Word',
        'ask_results': '💬 اسأل عن النتائج',
        'ask_code': '📚 اسأل عن الكود المصري',
        'dashboard': '📈 لوحة المعلومات',
        'batch_compare': '📊 مقارنة الدفعات',
        'audit_trail': '📜 سجل التدقيق',
        'settings': '⚙️ الإعدادات',
        'dark_mode': 'الوضع الداكن',
        'light_mode': 'الوضع الفاتح',
        'help_tour': '🎯 بدء الجولة',
        'contextual_help': '❓ مساعدة',
        'load_example': '📥 تحميل مثال',
        'save_state': '💾 حفظ الحالة',
        'language': 'اللغة',
        'english': 'English',
        'arabic': 'العربية',
        'example_loaded': 'تم تحميل بيانات المثال!',
        'state_saved': 'تم حفظ الحالة في المتصفح.',
        'not_enough_data': 'بيانات غير كافية للرسوم التنبؤية (يلزم قيمتان على الأقل).',
    }
}

current_lang = 'en'
current_theme = 'dark'

def _(key):
    return TEXTS[current_lang].get(key, key)

# =====================================================================
# STYLING
# =====================================================================
def apply_theme():
    if current_theme == 'dark':
        ui.query('body').style('background: radial-gradient(circle at 10% 20%, #0a1a3a, #031338) !important; color: #E9EDF5;')
    else:
        ui.query('body').style('background: #f0f2f5 !important; color: #1a1a1a;')

app.native.window_args = {"resizable": True}
ui.add_head_html('''
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    ::-webkit-scrollbar { width: 8px !important; background: #031338 !important; }
    ::-webkit-scrollbar-thumb { background: #FF8C00 !important; border-radius: 10px; }
    html, body { margin: 0; padding: 0; width: 100vw; height: 100vh; overflow-x: hidden; font-family: 'Inter', sans-serif; }
    .sidebar-container { background: #0b1a3a !important; border-right: 2px solid rgba(255,140,0,0.4); box-shadow: 8px 0 30px rgba(0,0,0,0.6); }
    .output-card { background: transparent !important; border: none !important; padding: 0 !important; }
    .input-card { background: rgba(13,26,53,0.6); backdrop-filter: blur(8px); border: 1px solid rgba(255,140,0,0.2); border-radius: 16px; padding: 18px 22px; box-shadow: 0 8px 32px rgba(0,0,0,0.3); }
    .primary-btn { background: linear-gradient(135deg, #1a1a1a 0%, #333333 100%) !important; color: #FFFFFF !important; border: 1px solid #555 !important; font-weight: 600 !important; border-radius: 14px !important; padding: 10px 28px !important; transition: 0.25s; }
    .primary-btn:hover { background: linear-gradient(135deg, #2d2d2d 0%, #444444 100%) !important; transform: translateY(-3px); box-shadow: 0 8px 25px rgba(0,0,0,0.7); border-color: #FF8C00; }
    .stat-chip { background: rgba(13,26,53,0.6); backdrop-filter: blur(8px); border: 1px solid #1f3355; border-radius: 12px; padding: 14px 20px; text-align: center; min-width: 140px; }
    .stat-chip .val { font-size: 24px; font-weight: 800; color: #FF8C00; }
    .stat-chip .lbl { font-size: 11px; color: #A9B6D0; text-transform: uppercase; letter-spacing: .05em; margin-top: 4px; }
    .markdown-body { font-size: 14px; line-height: 1.7; color: #E9EDF5; background: transparent !important; padding: 0 !important; }
    .markdown-body table { border-collapse: collapse; width: 100%; margin: 16px 0; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
    .markdown-body th { background: linear-gradient(135deg, #1a1a1a 0%, #333333 100%) !important; color: #FF8C00 !important; font-weight: 700; padding: 10px 14px; border: 1px solid #1f3355; }
    .markdown-body td { padding: 10px 14px; border: 1px solid #1f3355; }
    .app-footer { width: 100%; background: rgba(13,26,53,0.7); backdrop-filter: blur(8px); border-top: 2px solid rgba(255,140,0,0.5); padding: 20px 24px; margin-top: 50px; text-align: center; color: #A9B6D0; font-size: 13px; border-radius: 16px 16px 0 0; }
    .main-title { font-size: 3.8rem !important; font-weight: 900 !important; letter-spacing: -0.02em; }
    .sub-title { color: #FFFFFF !important; font-weight: 500; }
    @media (max-width: 768px) { .main-title { font-size: 2.2rem !important; } .sub-title { font-size: 1rem !important; } .stat-chip { min-width: 100px; padding: 10px 14px; } .input-card { padding: 12px 14px; } }
</style>
''', shared=True)

# =====================================================================
# HELPER FUNCTIONS (Full)
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
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1B2A4A')),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#94A3B8')),
                    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F1F5F9')]),
                    ('TOPPADDING', (0,0), (-1,-1), 4),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                    ('LEFTPADDING', (0,0), (-1,-1), 5),
                    ('RIGHTPADDING', (0,0), (-1,-1), 5),
                ]))
                flowables.append(t)
                flowables.append(Spacer(1,6))
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
            flowables.append(Spacer(1,4))
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
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('ALIGN', (1,0), (1,-1), 'RIGHT'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ]))
        story.append(t_head)
    except Exception:
        story.append(Paragraph(doc_title, title_style))
        story.append(Paragraph(subtitle, sub_style))
        story.append(Paragraph(meta_html, meta_style))
    story.append(Spacer(1,5))
    story.append(HRFlowable(width="100%", thickness=1.3, color=colors.HexColor("#FF8C00"), spaceAfter=8))

def build_pdf_footer_and_signatures(story, styles, qr_img_buffer):
    body_style = ParagraphStyle("SigBody", fontSize=8, textColor=colors.HexColor("#334155"), leading=11)
    sec_style = ParagraphStyle("SecTitle", fontSize=9.5, textColor=colors.HexColor("#1B2A4A"),
                                spaceBefore=8, spaceAfter=4, fontName="Helvetica-Bold")
    story.append(Spacer(1,6))
    story.append(Paragraph("Engineering Approvals &amp; Compliance Sign-Off", sec_style))
    qr_lab_img = ReportLabImage(qr_img_buffer, width=38, height=38)
    sign_cell_1 = Paragraph("<b>Prepared By</b><br/>QA/QC Engineer<br/><br/>_________________", body_style)
    sign_cell_2 = Paragraph("<b>Technical Director</b><br/>Chief Engineer<br/><br/>_________________", body_style)
    sign_cell_3 = Paragraph("<b>Client / Consultant</b><br/>Official Stamp<br/><br/>_________________", body_style)
    qr_cell = [Paragraph("<b>QR Verify</b>", body_style), qr_lab_img]
    w = USABLE_WIDTH
    t_sign = Table([[sign_cell_1, sign_cell_2, sign_cell_3, qr_cell]],
                    colWidths=[w*0.28, w*0.28, w*0.28, w*0.16])
    t_sign.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("ALIGN", (3,0), (3,0), "CENTER"),
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
        story.append(Spacer(1,6))
    story.extend(markdown_to_pdf_flowables(body_markdown, styles))
    story.append(Spacer(1,8))
    build_pdf_footer_and_signatures(story, styles, qr_buf)
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# =====================================================================
# CODE COMPLIANCE
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
    apply_theme()

    # ---- Load saved state from app.storage ----
    if 'app_state' in app.storage.user:
        state = app.storage.user['app_state']
        # We'll set inputs later after they are defined

    # ---- Sidebar ----
    sidebar = ui.left_drawer().classes('sidebar-container').style('width: 380px;')
    with sidebar:
        with ui.row().classes('w-full items-center justify-between mb-4 p-2'):
            ui.label(_('project_metadata')).classes('text-white font-bold text-base tracking-wide')
            ui.button('✕', on_click=sidebar.toggle).classes(
                'bg-transparent text-white text-xl hover:text-[#FF8C00] p-1 min-w-[36px] !shadow-none !rounded-full !bg-transparent'
            ).style('font-size: 20px; line-height: 1;')

        project_name_input = ui.input(label=_('project_name'), value='Highway Expansion Project').classes('w-full mb-3').props('helper="Enter the project name"')
        pour_location_input = ui.input(label=_('location'), value='Highway Section Ch. 12+500').classes('w-full mb-4').props('helper="Chainage or element location"')

        ui.label(_('code_basis')).classes('text-white font-bold text-sm mb-1')
        ui.markdown(_('code_hint')).classes('text-xs text-[#A9B6D0] mb-2')
        code_basis_select = ui.select(
            label='',
            options=CODE_BASIS_OPTIONS,
            value=CODE_BASIS_OPTIONS[0],
        ).classes('w-full mb-4').props('helper="Select the governing design code"')

        fcu_input = ui.number(label=_('fcu'), value=30.0, step=5.0).classes('w-full mb-4').props('helper="Characteristic compressive strength at 28 days"')

        ui.label(_('batch_plant')).classes('text-white font-bold text-sm mb-2')
        truck_input = ui.input(label=_('truck'), value='TRK-104').classes('w-full mb-2').props('helper="Mixer truck identification"')
        ticket_input = ui.input(label=_('ticket'), value='BT-99482').classes('w-full mb-4').props('helper="Batch ticket number"')

        ui.label(_('mix_design')).classes('text-white font-bold text-sm mb-2')
        cement_input = ui.input(label=_('cement'), value='350.0').classes('w-full mb-2').props('helper="Cement content in kg/m3"')
        water_input = ui.input(label=_('water'), value='150.0').classes('w-full mb-4').props('helper="Free water content in kg/m3"')

        engineer_input = ui.input(label=_('engineer'), value='Eng. Mohamed Abd Al Aty').classes('w-full mb-2').props('helper="Name of the responsible engineer"')

        logo_status = ui.label(_('logo')).classes('text-xs text-amber-400 mb-1')
        logo_bytes_holder = {'bytes': None}

        async def handle_logo_upload(e):
            try:
                logo_bytes_holder['bytes'] = await e.file.read()
                logo_status.set_text(f'Logo Loaded: {e.file.name}')
                logo_status.classes(replace='text-xs text-emerald-400 mb-1')
                ui.notify('Company logo loaded successfully!', type='positive')
            except Exception as ex:
                ui.notify(f'Error reading logo: {str(ex)}', type='negative')

        ui.upload(label=_('logo_upload'), auto_upload=True, on_upload=handle_logo_upload).props('flat dark').classes('w-full mb-2').props('helper="Upload company logo for reports"')

    # ---- Open sidebar button ----
    ui.button('☰', on_click=sidebar.toggle).classes(
        'fixed top-4 left-4 z-50 bg-[#10203f] text-white border border-[#FF8C00] p-3 rounded-full shadow-lg hover:bg-[#1a2a4a]'
    ).style('font-size: 20px; min-width: 48px; min-height: 48px;')

    # ---- Restore saved state ----
    if 'app_state' in app.storage.user:
        state = app.storage.user['app_state']
        project_name_input.value = state.get('project_name', '')
        pour_location_input.value = state.get('pour_location', '')
        fcu_input.value = state.get('fcu', 30.0)
        truck_input.value = state.get('truck', '')
        ticket_input.value = state.get('ticket', '')
        cement_input.value = state.get('cement', '')
        water_input.value = state.get('water', '')
        engineer_input.value = state.get('engineer', '')
        # c7, c14, c28 inputs not yet defined – will be set later

    def current_meta(uid_prefix):
        return {
            'uid': f"{uid_prefix}-{uuid.uuid4().hex[:8].upper()}",
            'project': project_name_input.value,
            'location': pour_location_input.value,
            'engineer': engineer_input.value,
            'date': datetime.date.today().strftime('%Y-%m-%d'),
            'ticket': ticket_input.value,
        }

    # ---- Main content ----
    with ui.column().classes('w-full min-h-screen p-4'):
        # Title block
        with ui.column().classes('w-full bg-[#0d1a35] px-6 py-4 rounded-xl border border-[#FF8C00] shadow-lg mb-4'):
            ui.label(_('app_title')).classes('main-title text-white')
            ui.label(_('app_sub')).classes('sub-title text-lg font-medium mt-1')
            ui.label(_('lead_auditor')).classes('text-base text-[#A9B6D0] font-semibold mt-1')
            ui.label(_('tagline')).classes('text-sm text-[#A9B6D0] mt-1 italic')

        # Marquee
        ui.html('''
        <div style="width: 100%; overflow: hidden; white-space: nowrap; background-color: rgba(13,26,53,0.6); backdrop-filter: blur(8px); color: #FFFFFF; padding: 10px 0; font-weight: 600; font-size: 13px; margin-bottom: 15px; border-radius: 8px; border: 1px solid rgba(255,140,0,0.3);">
          <div style="display: inline-block; padding-left: 100%; animation: marquee 28s linear infinite;">
            <span style="color: #FF8C00;">[CORE ACTIVE]</span> ECP 203 &middot; ECP 202 &middot; ECP 104 &middot; ASTM &middot; AASHTO &middot; BS EN &middot; ISO
          </div>
        </div>
        ''')

        # ---- Tabs ----
        with ui.tabs().classes('w-full text-white bg-[#0d1a35] rounded-lg') as tabs:
            t_calc = ui.tab('Calculator').classes('text-white font-bold')
            t_dash = ui.tab(_('dashboard')).classes('text-white font-bold')
            t_batch = ui.tab(_('batch_compare')).classes('text-white font-bold')
            t_audit = ui.tab(_('audit_trail')).classes('text-white font-bold')
            t_settings = ui.tab(_('settings')).classes('text-white font-bold')

        with ui.tab_panels(tabs, value=t_calc).classes('w-full bg-transparent mt-4'):
            # ---- Calculator Tab ----
            with ui.tab_panel(t_calc):
                ui.label('Concrete Cube Calculation Sheet & Statistical Verifier').classes('text-2xl font-bold text-white mb-4')

                with ui.row().classes('w-full gap-4 mb-4'):
                    with ui.column().classes('input-card flex-1'):
                        ui.label(_('7day')).classes('font-bold text-white text-sm')
                        c7_input = ui.input(value='21.0, 22.5, 20.5').classes('w-full').props('helper="Comma-separated values"')
                    with ui.column().classes('input-card flex-1'):
                        ui.label(_('14day')).classes('font-bold text-white text-sm')
                        c14_input = ui.input(value='26.0, 27.2, 25.8').classes('w-full').props('helper="Comma-separated values"')
                    with ui.column().classes('input-card flex-1'):
                        ui.label(_('28day')).classes('font-bold text-white text-sm')
                        c28_input = ui.input(value='32.5, 34.0, 31.0, 35.5, 29.0, 33.0').classes('w-full').props('helper="Comma-separated values"')

                # ---- Restore c7/c14/c28 from storage ----
                if 'app_state' in app.storage.user:
                    state = app.storage.user['app_state']
                    c7_input.value = state.get('c7', '')
                    c14_input.value = state.get('c14', '')
                    c28_input.value = state.get('c28', '')

                # ---- Load Example & Save State ----
                def load_example():
                    project_name_input.value = 'Highway Expansion Project'
                    pour_location_input.value = 'Highway Section Ch. 12+500'
                    fcu_input.value = 30.0
                    truck_input.value = 'TRK-104'
                    ticket_input.value = 'BT-99482'
                    cement_input.value = '350.0'
                    water_input.value = '150.0'
                    engineer_input.value = 'Eng. Mohamed Abd Al Aty'
                    c7_input.value = '21.0, 22.5, 20.5'
                    c14_input.value = '26.0, 27.2, 25.8'
                    c28_input.value = '32.5, 34.0, 31.0, 35.5, 29.0, 33.0'
                    ui.notify(_('example_loaded'), type='positive')
                    save_state()

                def save_state():
                    state = {
                        'project_name': project_name_input.value,
                        'pour_location': pour_location_input.value,
                        'fcu': fcu_input.value,
                        'truck': truck_input.value,
                        'ticket': ticket_input.value,
                        'cement': cement_input.value,
                        'water': water_input.value,
                        'engineer': engineer_input.value,
                        'c7': c7_input.value,
                        'c14': c14_input.value,
                        'c28': c28_input.value,
                        'lang': current_lang,
                        'theme': current_theme,
                    }
                    app.storage.user['app_state'] = state
                    ui.notify(_('state_saved'), type='positive')

                with ui.row().classes('w-full gap-4 mb-4'):
                    ui.button(_('load_example'), on_click=load_example).classes('primary-btn')
                    ui.button(_('save_state'), on_click=save_state).classes('primary-btn')

                # ---- Stage filter ----
                stage_selector = ui.select(
                    label=_('stage_filter'),
                    options=['All Stages', '7-Day Stage', '14-Day Stage', '28-Day Stage'],
                    value='All Stages',
                ).classes('w-full md:w-1/3 mb-4').props('helper="Choose which stage to display"')

                stats_area = ui.column().classes('w-full')
                result_output_area = ui.column().classes('w-full')
                chart_area = ui.column().classes('w-full')
                export_buttons_area = ui.row().classes('w-full gap-4 flex-wrap mt-4')
                calc_panel = ui.column().classes('w-full mt-4')
                predictive_charts_area = ui.column().classes('w-full mt-4')

                # ---- Helper functions (local) ----
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

                # ---- Audit log ----
                def log_action(action, details):
                    if 'audit_log' not in app.storage.user:
                        app.storage.user['audit_log'] = []
                    log = app.storage.user['audit_log']
                    log.append({
                        'timestamp': datetime.datetime.now().isoformat(),
                        'action': action,
                        'details': details,
                        'user': engineer_input.value or 'anonymous'
                    })
                    app.storage.user['audit_log'] = log

                # ---- Capability ----
                def compute_capability(values, target, tolerance=5):
                    if not values:
                        return None
                    arr = np.array(values)
                    n = len(arr)
                    mean = arr.mean()
                    std = arr.std(ddof=1) if n > 1 else 0
                    if std == 0:
                        return None
                    usl = target + tolerance
                    lsl = target - tolerance
                    cpu = (usl - mean) / (3*std)
                    cpl = (mean - lsl) / (3*std)
                    cp = (usl - lsl) / (6*std)
                    cpk = min(cpu, cpl)
                    pp = (usl - lsl) / (6*arr.std(ddof=0)) if arr.std(ddof=0) > 0 else None
                    ppk = min((usl - mean)/(3*arr.std(ddof=0)), (mean - lsl)/(3*arr.std(ddof=0))) if arr.std(ddof=0) > 0 else None
                    return {'cp': cp, 'cpk': cpk, 'pp': pp, 'ppk': ppk, 'usl': usl, 'lsl': lsl}

                # ---- Outlier ----
                def detect_outliers(values, mean, std):
                    if not values or std == 0:
                        return []
                    arr = np.array(values)
                    return [(i, v) for i, v in enumerate(arr) if abs(v - mean) > 3*std]

                # ---- Confidence interval ----
                def conf_interval(values, confidence=0.95):
                    if not values or len(values) < 2:
                        return None
                    arr = np.array(values)
                    mean = arr.mean()
                    std = arr.std(ddof=1)
                    n = len(arr)
                    t = stats.t.ppf((1+confidence)/2, n-1)
                    margin = t * std / np.sqrt(n)
                    return (mean - margin, mean + margin)

                # ---- Forecast ----
                def forecast(values, steps=3):
                    if len(values) < 2:
                        return None, None
                    x = np.arange(1, len(values)+1)
                    y = np.array(values)
                    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
                    future_x = np.array(range(len(values)+1, len(values)+steps+1))
                    pred_y = slope * future_x + intercept
                    return pred_y.tolist(), std_err

                # ---- Build detailed calc markdown ----
                def build_detailed_calculations_md(stage_stats):
                    md_lines = []
                    for label, values, s in stage_stats:
                        if not s:
                            continue
                        md_lines.append(f"### {label} Stage")
                        md_lines.append("**Raw Data (N/mm²):** " + ", ".join(f"{v:.1f}" for v in values))
                        n = s['n']
                        sum_vals = s['sum']
                        sum_sq = s['sum_sq']
                        mean = s['mean']
                        std = s['std']
                        cov = s['cov']
                        md_lines.append("")
                        md_lines.append("**Calculations:**")
                        md_lines.append(f"- Number of specimens (n) = {n}")
                        md_lines.append(f"- Sum (Σx) = {sum_vals:.2f}")
                        md_lines.append(f"- Sum of squares (Σx²) = {sum_sq:.2f}")
                        md_lines.append(f"- Mean (x̄) = Σx / n = {sum_vals:.2f} / {n} = **{mean:.2f}** N/mm²")
                        md_lines.append(f"- Standard deviation (s) = sqrt((Σx² - (Σx)²/n) / (n-1)) = **{std:.2f}** N/mm²")
                        md_lines.append(f"- Coefficient of variation (COV) = (s / x̄) × 100 = **{cov:.1f}%**")
                        md_lines.append(f"- Minimum = {s['min']:.1f} N/mm²")
                        md_lines.append(f"- Maximum = {s['max']:.1f} N/mm²")
                        # Confidence interval
                        ci = conf_interval(values)
                        if ci:
                            md_lines.append(f"- 95% Confidence Interval for the mean: [{ci[0]:.2f}, {ci[1]:.2f}]")
                        # Capability
                        cap = compute_capability(values, target_fcu)
                        if cap:
                            md_lines.append(f"- Process Capability: Cpk = {cap['cpk']:.2f}, Pp = {cap['pp']:.2f} (USL={cap['usl']:.1f}, LSL={cap['lsl']:.1f})")
                        # Outliers
                        out = detect_outliers(values, mean, std)
                        if out:
                            md_lines.append(f"- ⚠️ Outliers detected (|x - mean| > 3σ): " + ", ".join(f"#{i+1}={v:.1f}" for i,v in out))
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

                # ---- Create predictive charts ----
                def create_predictive_charts(stage_stats, target):
                    # combine all values
                    all_vals = []
                    all_labels = []
                    for label, values, stats in stage_stats:
                        if stats:
                            all_vals.extend(values)
                            all_labels.extend([label]*len(values))
                    if len(all_vals) < 2:
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
                    hist_fig.add_vline(x=target, line_dash="dash", line_color="#22C55E", annotation_text="Target")
                    hist_fig.update_layout(
                        title='Distribution of All Cube Strengths',
                        xaxis_title='Strength (N/mm²)',
                        yaxis_title='Frequency',
                        template='plotly_dark',
                        paper_bgcolor='#0d1a35',
                        plot_bgcolor='#0d1a35',
                        height=300
                    )

                    # Time series
                    x_seq = list(range(1, len(all_vals)+1))
                    time_fig = go.Figure()
                    time_fig.add_trace(go.Scatter(
                        x=x_seq,
                        y=all_vals,
                        mode='lines+markers',
                        marker=dict(color='#4FC3F7', size=8),
                        line=dict(color='#FF8C00', width=2),
                        name='Strengths'
                    ))
                    if len(x_seq) > 1:
                        slope, intercept, r2, _, _ = stats.linregress(x_seq, all_vals)
                        trend_y = [slope*x + intercept for x in x_seq]
                        time_fig.add_trace(go.Scatter(
                            x=x_seq,
                            y=trend_y,
                            mode='lines',
                            line=dict(color='#22C55E', width=2, dash='dash'),
                            name=f'Trend (R²={r2**2:.3f})'
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

                    # Control chart (X-bar with UCL/LCL)
                    overall_mean = np.mean(all_vals)
                    overall_std = np.std(all_vals) if len(all_vals)>1 else 0
                    ucl = overall_mean + 3 * overall_std
                    lcl = overall_mean - 3 * overall_std
                    control_fig = go.Figure()
                    control_fig.add_trace(go.Scatter(
                        x=x_seq,
                        y=all_vals,
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

                    # Forecast
                    if len(all_vals) > 1:
                        slope, intercept, _, _, _ = stats.linregress(x_seq, all_vals)
                        future_x = list(range(len(all_vals)+1, len(all_vals)+4))
                        future_y = [slope*x + intercept for x in future_x]
                        forecast_fig = go.Figure()
                        forecast_fig.add_trace(go.Scatter(
                            x=x_seq,
                            y=all_vals,
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

                # ---- AI results holder ----
                ai_cube_result_holder = {'text': ''}
                stage_stats_holder = []

                # ---- Run function ----
                async def run_verification():
                    result_output_area.clear()
                    export_buttons_area.clear()
                    chart_area.clear()
                    stats_area.clear()
                    calc_panel.clear()
                    predictive_charts_area.clear()

                    if not client:
                        ui.notify('GEMINI_API_KEY missing in .env!', type='negative')
                        return

                    with result_output_area:
                        ui.spinner('ios', size='lg').classes('self-center text-[#4FC3F7]')
                        ui.label('Running statistical evaluation & code compliance verification...').classes('self-center text-sm')

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

                        # ---- Stats chips with capability ----
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
                                    # Capability
                                    cap = compute_capability(values, target_fcu)
                                    if cap:
                                        cpk = cap['cpk']
                                        color = '#22C55E' if cpk >= 1.33 else '#FF8C00' if cpk >= 1.0 else '#FF0000'
                                        with ui.column().classes('stat-chip'):
                                            ui.label(f"{cpk:.2f}").classes('val').style(f'color: {color}')
                                            ui.label(f'{label} Cpk').classes('lbl')
                                    # Confidence interval
                                    ci = conf_interval(values)
                                    if ci:
                                        with ui.column().classes('stat-chip'):
                                            ui.label(f"{ci[0]:.2f} – {ci[1]:.2f}").classes('val')
                                            ui.label('95% CI').classes('lbl')

                        # ---- AI prompt ----
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

                        # ---- Chart (means) ----
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

                        # ---- Detailed calculations ----
                        calc_panel.clear()
                        with calc_panel:
                            with ui.expansion(_('detailed_calc'), icon='calculate', value=True).classes('w-full bg-[#0d1a35] rounded-lg mt-4'):
                                md = build_detailed_calculations_md(stage_stats)
                                ui.markdown(md).classes('markdown-body')

                        # ---- Predictive charts ----
                        predictive_charts_area.clear()
                        with predictive_charts_area:
                            ui.label('Predictive Analysis & Advanced Charts').classes('text-xl font-bold text-white mb-2')
                            hist_fig, time_fig, control_fig, forecast_fig = create_predictive_charts(stage_stats, target_fcu)
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
                                            ui.label(_('not_enough_data')).classes('text-amber-400')
                            else:
                                ui.label(_('not_enough_data')).classes('text-amber-400')

                        # ---- Export buttons ----
                        with export_buttons_area:
                            def download_normal_pdf():
                                try:
                                    meta = current_meta('ECP-AI')
                                    # Build stats table
                                    styles = build_pdf_styles()
                                    stat_rows = [["Stage", "n", "Mean", "Std Dev", "Min", "Max", "COV %", "Cpk"]]
                                    for label, values, s in stage_stats:
                                        if s:
                                            cap = compute_capability(values, target_fcu)
                                            cpk_str = f"{cap['cpk']:.2f}" if cap else '-'
                                            stat_rows.append([label, str(s['n']), f"{s['mean']:.2f}", f"{s['std']:.2f}",
                                                               f"{s['min']:.1f}", f"{s['max']:.1f}", f"{s['cov']:.1f}", cpk_str])
                                    colw = USABLE_WIDTH / len(stat_rows[0])
                                    table_data = [[Paragraph(c, styles['tablehead'] if r==0 else styles['tablecell'])
                                                   for c in row] for r, row in enumerate(stat_rows)]
                                    stat_table = Table(table_data, colWidths=[colw]*len(stat_rows[0]))
                                    stat_table.setStyle(TableStyle([
                                        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1B2A4A')),
                                        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#94A3B8')),
                                        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F1F5F9')]),
                                        ('TOPPADDING', (0,0), (-1,-1), 4),
                                        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                                    ]))
                                    pdf_bytes = build_report_pdf(
                                        "CONCRETE CUBE CALCULATION & VERIFICATION REPORT",
                                        f"Governing Standard: {basis} | Filter: {stage_filter}",
                                        ai_cube_result_holder['text'], meta, logo_bytes_holder['bytes'],
                                        extra_flowables_before_body=[Paragraph("Statistical Summary", styles['h2']), stat_table],
                                    )
                                    ui.download(pdf_bytes, filename=f"Concrete_Report_{ticket_input.value}.pdf")
                                    ui.notify('PDF downloaded!', type='positive')
                                    log_action('Download PDF', f'ticket={ticket_input.value}')
                                except Exception as ex:
                                    ui.notify(f'PDF Error: {str(ex)}', type='negative')

                            def download_normal_word():
                                try:
                                    doc = Document()
                                    doc.add_heading('Concrete Cube Verification Report', 0)
                                    doc.add_paragraph(f'Project: {project_name_input.value}')
                                    doc.add_paragraph(f'Location: {pour_location_input.value}')
                                    doc.add_paragraph(f'Engineer: {engineer_input.value}')
                                    doc.add_paragraph(f'Date: {datetime.date.today().strftime("%Y-%m-%d")}')
                                    doc.add_paragraph(f'Ticket ID: {ticket_input.value}')
                                    doc.add_paragraph(f'Code Basis: {basis}')
                                    doc.add_paragraph(f'Target f_cu: {fcu_input.value} N/mm2')
                                    doc.add_heading('Statistical Summary', level=1)
                                    table = doc.add_table(rows=1, cols=8)
                                    hdr = table.rows[0].cells
                                    headers = ['Stage','n','Mean','Std Dev','Min','Max','COV %','Cpk']
                                    for i,h in enumerate(headers):
                                        hdr[i].text = h
                                    for label, values, s in stage_stats:
                                        if s:
                                            cap = compute_capability(values, target_fcu)
                                            cpk_str = f"{cap['cpk']:.2f}" if cap else '-'
                                            row = table.add_row().cells
                                            row[0].text = label
                                            row[1].text = str(s['n'])
                                            row[2].text = f"{s['mean']:.2f}"
                                            row[3].text = f"{s['std']:.2f}"
                                            row[4].text = f"{s['min']:.1f}"
                                            row[5].text = f"{s['max']:.1f}"
                                            row[6].text = f"{s['cov']:.1f}"
                                            row[7].text = cpk_str
                                    doc.add_heading('Compliance Evaluation', level=1)
                                    doc.add_paragraph(ai_cube_result_holder['text'])
                                    out = io.BytesIO()
                                    doc.save(out)
                                    out.seek(0)
                                    ui.download(out.getvalue(), filename=f"Concrete_Report_{ticket_input.value}.docx")
                                    ui.notify('Word document downloaded!', type='positive')
                                    log_action('Download Word', f'ticket={ticket_input.value}')
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
                                            cap = compute_capability(values, float(fcu_input.value))
                                            if cap:
                                                data[f'stage_{key}_cpk'] = f"{cap['cpk']:.2f}"
                                    data['ai_verdict'] = ai_cube_result_holder['text']
                                    filled_bytes = fill_template(template_bytes_holder['bytes'], data)
                                    ui.download(filled_bytes, filename=f"Filled_Template_{ticket_input.value}.docx")
                                    ui.notify('Filled template downloaded!', type='positive')
                                    log_action('Download Filled Template', f'ticket={ticket_input.value}')
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
                                    table_data = [[Paragraph(c, styles['tablehead'] if r==0 else styles['tablecell'])
                                                   for c in row] for r, row in enumerate(calc_rows)]
                                    t = Table(table_data, colWidths=[colw]*4)
                                    t.setStyle(TableStyle([
                                        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1B2A4A')),
                                        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#94A3B8')),
                                        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F1F5F9')]),
                                        ('TOPPADDING', (0,0), (-1,-1), 4),
                                        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                                    ]))
                                    formula_flowables = []
                                    for label, values, s in stage_stats:
                                        if s:
                                            formula_flowables.append(Paragraph(f"{label} Stage Calculations", styles['h3']))
                                            formula_flowables.append(Paragraph(f"n = {s['n']}, Σx = {s['sum']:.2f}, Σx² = {s['sum_sq']:.2f}", styles['body']))
                                            formula_flowables.append(Paragraph(f"Mean = {s['sum']:.2f} / {s['n']} = {s['mean']:.2f}", styles['body']))
                                            formula_flowables.append(Paragraph(f"Std Dev = sqrt(({s['sum_sq']:.2f} - ({s['sum']:.2f})²/{s['n']}) / ({s['n']-1})) = {s['std']:.2f}", styles['body']))
                                            formula_flowables.append(Spacer(1,6))
                                    pdf_bytes = build_report_pdf(
                                        "DETAILED CONCRETE CUBE CALCULATIONS",
                                        f"Calculations for {meta['project']}",
                                        "", meta, logo_bytes_holder['bytes'],
                                        extra_flowables_before_body=[
                                            Paragraph("Complete Calculation Breakdown", styles['h2']),
                                            t,
                                            Spacer(1,6),
                                            Paragraph("Formulas & Intermediate Values", styles['h2']),
                                            *formula_flowables,
                                            Spacer(1,6),
                                            Paragraph("Compliance Evaluation Summary", styles['h2']),
                                            *markdown_to_pdf_flowables(ai_cube_result_holder['text'], styles),
                                        ]
                                    )
                                    ui.download(pdf_bytes, filename=f"Detailed_Calculations_{ticket_input.value}.pdf")
                                    ui.notify('Calculations PDF downloaded!', type='positive')
                                    log_action('Download Calculations PDF', f'ticket={ticket_input.value}')
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
                                    log_action('Download Calculations Word', f'ticket={ticket_input.value}')
                                except Exception as ex:
                                    ui.notify(f'Calc Word error: {str(ex)}', type='negative')

                            # Buttons
                            with ui.row().classes('w-full gap-4 flex-wrap'):
                                ui.button(_('download_pdf'), on_click=download_normal_pdf).classes('primary-btn')
                                ui.button(_('download_word'), on_click=download_normal_word).classes('primary-btn')
                                if template_bytes_holder['bytes']:
                                    ui.button(_('download_template'), on_click=download_filled_template).classes('primary-btn')
                                ui.button(_('download_calc_pdf'), on_click=download_calc_pdf).classes('primary-btn')
                                ui.button(_('download_calc_word'), on_click=download_calc_word).classes('primary-btn')

                        # ---- Chatbots ----
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
                            ui.button(_('ask_results'), on_click=toggle_result_chat).classes('primary-btn')
                            ui.button(_('ask_code'), on_click=toggle_code_chat).classes('primary-btn')

                        # Result Chat
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

                        # Code Chat
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

                # ---- Run button ----
                ui.button(_('run_button'), on_click=run_verification).classes('primary-btn q-my-md')
                with result_output_area:
                    ui.markdown('*' + _('run_hint') + '*').classes('text-sm text-[#A9B6D0]')

            # ---- Dashboard Tab ----
            with ui.tab_panel(t_dash):
                ui.label('📈 Dashboard').classes('text-2xl font-bold text-white mb-4')
                # Show summary cards if we have data
                if 'audit_log' in app.storage.user and len(app.storage.user['audit_log']) > 0:
                    ui.markdown('*Latest results summary (from last run):*').classes('text-white')
                    # We can load last run stats from storage if we saved them
                    ui.label('Dashboard will display real-time metrics after each run.').classes('text-[#A9B6D0]')
                else:
                    ui.label('Run a calculation first to see dashboard metrics.').classes('text-[#A9B6D0]')

            # ---- Batch Comparison Tab ----
            with ui.tab_panel(t_batch):
                ui.label('📊 Batch Comparison').classes('text-2xl font-bold text-white mb-4')
                ui.markdown('Compare multiple batch tickets. This feature is under development.').classes('text-[#A9B6D0]')

            # ---- Audit Trail Tab ----
            with ui.tab_panel(t_audit):
                ui.label('📜 Audit Trail').classes('text-2xl font-bold text-white mb-4')
                if 'audit_log' in app.storage.user:
                    log = app.storage.user['audit_log']
                    if log:
                        with ui.column().classes('w-full'):
                            for entry in reversed(log[-50:]):
                                ui.markdown(f"**{entry['timestamp']}** – {entry['user']}: {entry['action']} ({entry['details']})").classes('text-sm text-[#A9B6D0] border-b border-[#1f3355] py-1')
                    else:
                        ui.label('No audit logs yet.').classes('text-[#A9B6D0]')
                else:
                    ui.label('No audit logs yet.').classes('text-[#A9B6D0]')

            # ---- Settings Tab ----
            with ui.tab_panel(t_settings):
                ui.label('⚙️ Settings').classes('text-2xl font-bold text-white mb-4')
                # Language
                ui.label('Language / اللغة').classes('text-white font-bold')
                lang_radio = ui.radio(['English', 'العربية'], value='English' if current_lang=='en' else 'العربية').classes('text-white').on('change', lambda e: switch_lang(e.value))
                # Theme
                ui.label('Theme').classes('text-white font-bold mt-4')
                theme_radio = ui.radio(['Dark', 'Light'], value='Dark' if current_theme=='dark' else 'Light').classes('text-white').on('change', lambda e: switch_theme(e.value))

                def switch_lang(val):
                    global current_lang
                    current_lang = 'en' if val == 'English' else 'ar'
                    ui.notify(f'Language switched to {val}', type='positive')
                    ui.open('/')

                def switch_theme(val):
                    global current_theme
                    current_theme = 'dark' if val == 'Dark' else 'light'
                    apply_theme()
                    ui.notify(f'Theme switched to {val}', type='positive')
                    ui.open('/')

                ui.button('🎯 Start Interactive Tour', on_click=lambda: ui.notify('Tour started! (placeholder)', type='info')).classes('primary-btn mt-4')
                ui.button('❓ Contextual Help', on_click=lambda: ui.notify('Help panel will be displayed here.', type='info')).classes('primary-btn mt-2')

        # ---- Footer ----
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
