import io
import datetime
import os
import uuid
import re
import asyncio
import json
import base64
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import qrcode
from docxtpl import DocxTemplate
from docx import Document
from scipy import stats

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
    }
}

current_lang = 'en'
current_theme = 'dark'

def _(key):
    return TEXTS[current_lang].get(key, key)

# =====================================================================
# STYLING (dynamic – dark/light)
# =====================================================================
def apply_theme():
    if current_theme == 'dark':
        ui.query('body').style('background: radial-gradient(circle at 10% 20%, #0a1a3a, #031338) !important; color: #E9EDF5;')
        # also set other classes
    else:
        ui.query('body').style('background: #f0f2f5 !important; color: #1a1a1a;')

app.native.window_args = {"resizable": True}

ui.add_head_html('''
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    /* base styles – will be overridden by theme */
    .dark-mode {
        background: radial-gradient(circle at 10% 20%, #0a1a3a, #031338) !important;
        color: #E9EDF5;
    }
    .light-mode {
        background: #f0f2f5 !important;
        color: #1a1a1a;
    }
    /* rest of styles – keep as before */
    ::-webkit-scrollbar { width: 8px !important; background: #031338 !important; }
    ::-webkit-scrollbar-thumb { background: #FF8C00 !important; border-radius: 10px; }
    .sidebar-container {
        background: #0b1a3a !important;
        border-right: 2px solid rgba(255, 140, 0, 0.4) !important;
        box-shadow: 8px 0 30px rgba(0,0,0,0.6) !important;
    }
    /* ... existing styles truncated for brevity – keep them all */
    .output-card { background: transparent !important; border: none !important; padding: 0 !important; }
    .input-card { background: rgba(13, 26, 53, 0.6); backdrop-filter: blur(8px); border: 1px solid rgba(255,140,0,0.2); border-radius: 16px; padding: 18px 22px; box-shadow: 0 8px 32px rgba(0,0,0,0.3); }
    .primary-btn { background: linear-gradient(135deg, #1a1a1a 0%, #333333 100%) !important; color: #FFFFFF !important; border: 1px solid #555 !important; font-weight: 600 !important; border-radius: 14px !important; padding: 10px 28px !important; }
    /* ... keep all other styles from original */
</style>
''', shared=True)

# ... (all helper functions: sanitize_ai_markdown, build_pdf_styles, etc.) – keep them as before.

# =====================================================================
# MAIN PAGE
# =====================================================================
@ui.page('/')
def main_page():
    ui.query('body').style('width: 100vw; height: 100vh; overflow-x: hidden;')
    # Apply theme
    apply_theme()

    # ---- State management with localStorage ----
    # Use ui.storage (per browser) to save/load state
    # We'll store a dict with keys: project_name, pour_location, fcu, etc.
    # Also store results: latest stats, reports.

    # ---- Load example function ----
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

    # ---- Save state function ----
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
        ui.storage.user['app_state'] = state
        ui.notify(_('state_saved'), type='positive')

    # ---- Load saved state on start ----
    if 'app_state' in ui.storage.user:
        state = ui.storage.user['app_state']
        # set inputs
        project_name_input.value = state.get('project_name', '')
        pour_location_input.value = state.get('pour_location', '')
        fcu_input.value = state.get('fcu', 30.0)
        truck_input.value = state.get('truck', '')
        ticket_input.value = state.get('ticket', '')
        cement_input.value = state.get('cement', '')
        water_input.value = state.get('water', '')
        engineer_input.value = state.get('engineer', '')
        c7_input.value = state.get('c7', '')
        c14_input.value = state.get('c14', '')
        c28_input.value = state.get('c28', '')
        # lang and theme will be handled by toggles

    # ---- SIDEBAR ----
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

    ui.button('☰', on_click=sidebar.toggle).classes(
        'fixed top-4 left-4 z-50 bg-[#10203f] text-white border border-[#FF8C00] p-3 rounded-full shadow-lg hover:bg-[#1a2a4a]'
    ).style('font-size: 20px; min-width: 48px; min-height: 48px;')

    # ---- MAIN CONTENT ----
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
                # Inputs
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

                # Buttons: Load Example, Save State
                with ui.row().classes('w-full gap-4 mb-4'):
                    ui.button(_('load_example'), on_click=load_example).classes('primary-btn')
                    ui.button(_('save_state'), on_click=save_state).classes('primary-btn')

                # Stage filter
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

                # ---- Audit trail ----
                def log_action(action, details):
                    if 'audit_log' not in ui.storage.user:
                        ui.storage.user['audit_log'] = []
                    log = ui.storage.user['audit_log']
                    log.append({
                        'timestamp': datetime.datetime.now().isoformat(),
                        'action': action,
                        'details': details,
                        'user': engineer_input.value or 'anonymous'
                    })
                    ui.storage.user['audit_log'] = log

                # ---- Process Capability ----
                def compute_capability(values, target, tolerance=5):
                    # assume USL = target + tolerance, LSL = target - tolerance
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

                # ---- Outlier detection ----
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

                # ---- Predictive forecast ----
                def forecast(values, steps=3):
                    if len(values) < 2:
                        return None, None
                    x = np.arange(1, len(values)+1)
                    y = np.array(values)
                    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
                    # prediction intervals
                    future_x = np.array(range(len(values)+1, len(values)+steps+1))
                    pred_y = slope * future_x + intercept
                    # simple prediction interval (approx)
                    se = std_err
                    return pred_y.tolist(), se

                # ---- Main run function ----
                async def run_verification():
                    # Clear outputs
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

                        # ---- Dashboard data ----
                        all_vals = []
                        all_labels = []
                        for label, values, s in stage_stats:
                            if s:
                                all_vals.extend(values)
                                all_labels.extend([label]*len(values))

                        # ---- Capability ----
                        tolerance = 5  # could be user-defined later
                        cap_results = {}
                        for label, values, s in stage_stats:
                            if s:
                                cap = compute_capability(values, target_fcu, tolerance)
                                cap_results[label] = cap

                        # ---- Outliers ----
                        outliers = {}
                        for label, values, s in stage_stats:
                            if s:
                                out = detect_outliers(values, s['mean'], s['std'])
                                outliers[label] = out

                        # ---- Confidence intervals ----
                        ci_results = {}
                        for label, values, s in stage_stats:
                            if s:
                                ci = conf_interval(values)
                                ci_results[label] = ci

                        # ---- Forecast ----
                        forecast_results = {}
                        for label, values, s in stage_stats:
                            if s and len(values) > 1:
                                pred, se = forecast(values)
                                forecast_results[label] = (pred, se)

                        # ---- Stats chips ----
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
                                    if label in cap_results and cap_results[label]:
                                        cpk = cap_results[label]['cpk']
                                        color = '#22C55E' if cpk >= 1.33 else '#FF8C00' if cpk >= 1.0 else '#FF0000'
                                        with ui.column().classes('stat-chip'):
                                            ui.label(f"{cpk:.2f}").classes('val').style(f'color: {color}')
                                            ui.label(f'{label} Cpk').classes('lbl')

                        # ---- Build prompt for AI ----
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

                        # ---- Chart (mean comparison) ----
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

                        # ---- Detailed Calculations ----
                        calc_panel.clear()
                        with calc_panel:
                            with ui.expansion(_('detailed_calc'), icon='calculate', value=True).classes('w-full bg-[#0d1a35] rounded-lg mt-4'):
                                md = build_detailed_calculations_md(stage_stats)
                                ui.markdown(md).classes('markdown-body')

                        # ---- Predictive Analysis & Charts ----
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
                                            ui.label('Forecast not available (need at least 2 data points).').classes('text-amber-400')
                            else:
                                ui.label('Not enough data for predictive charts. Please provide at least one value per stage.').classes('text-amber-400')

                        # ---- Export Buttons ----
                        with export_buttons_area:
                            def download_normal_pdf():
                                try:
                                    meta = current_meta('ECP-AI')
                                    pdf_bytes = build_report_pdf(
                                        "CONCRETE CUBE CALCULATION & VERIFICATION REPORT",
                                        f"Governing Standard: {basis} | Filter: {stage_filter}",
                                        ai_cube_result_holder['text'], meta, logo_bytes_holder['bytes'],
                                        extra_flowables_before_body=[
                                            Paragraph("Deterministic Statistics", build_pdf_styles()['h2']),
                                            build_stats_table(stage_stats, USABLE_WIDTH),
                                        ],
                                    )
                                    ui.download(pdf_bytes, filename=f"Concrete_Report_{ticket_input.value}.pdf")
                                    ui.notify('PDF downloaded!', type='positive')
                                    log_action('Download PDF', f'ticket={ticket_input.value}')
                                except Exception as ex:
                                    ui.notify(f'PDF Error: {str(ex)}', type='negative')

                            # ... other download functions (same as before, with log_action)

                        # ---- Chatbots ----
                        # (same as before, but with i18n)

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
                # We'll display summary cards, gauges, trend indicators based on latest run
                # This requires keeping latest stats in storage
                # We'll show a placeholder if no data
                ui.markdown('Dashboard will display summary statistics, gauges, and trend indicators after you run a calculation.').classes('text-[#A9B6D0]')

            # ---- Batch Comparison Tab ----
            with ui.tab_panel(t_batch):
                ui.label('📊 Batch Comparison').classes('text-2xl font-bold text-white mb-4')
                ui.markdown('Compare multiple batch tickets. Select previously saved reports from audit trail.').classes('text-[#A9B6D0]')
                # Implementation can be added later

            # ---- Audit Trail Tab ----
            with ui.tab_panel(t_audit):
                ui.label('📜 Audit Trail').classes('text-2xl font-bold text-white mb-4')
                # Display audit log from storage
                if 'audit_log' in ui.storage.user:
                    log = ui.storage.user['audit_log']
                    if log:
                        # show as table
                        with ui.column().classes('w-full'):
                            for entry in reversed(log[-20:]):  # last 20
                                ui.markdown(f"**{entry['timestamp']}** – {entry['user']}: {entry['action']} ({entry['details']})").classes('text-sm text-[#A9B6D0] border-b border-[#1f3355] py-1')
                    else:
                        ui.label('No audit logs yet.').classes('text-[#A9B6D0]')
                else:
                    ui.label('No audit logs yet.').classes('text-[#A9B6D0]')

            # ---- Settings Tab ----
            with ui.tab_panel(t_settings):
                ui.label('⚙️ Settings').classes('text-2xl font-bold text-white mb-4')
                # Language toggle
                ui.label('Language / اللغة').classes('text-white font-bold')
                lang_radio = ui.radio(['English', 'العربية'], value='English').classes('text-white').on('change', lambda e: switch_lang(e.value))
                # Theme toggle
                ui.label('Theme').classes('text-white font-bold mt-4')
                theme_radio = ui.radio(['Dark', 'Light'], value='Dark').classes('text-white').on('change', lambda e: switch_theme(e.value))

                def switch_lang(val):
                    global current_lang
                    current_lang = 'en' if val == 'English' else 'ar'
                    ui.notify(f'Language switched to {val}', type='positive')
                    # Refresh page to apply new texts (or we could dynamically update, but simple reload)
                    ui.open('/')

                def switch_theme(val):
                    global current_theme
                    current_theme = 'dark' if val == 'Dark' else 'light'
                    apply_theme()
                    ui.notify(f'Theme switched to {val}', type='positive')
                    # we need to reapply styles – we'll reload
                    ui.open('/')

                # Buttons for tour and help
                ui.button('🎯 Start Interactive Tour', on_click=lambda: start_tour()).classes('primary-btn mt-4')
                ui.button('❓ Contextual Help', on_click=lambda: toggle_help()).classes('primary-btn mt-2')

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


# =====================================================================
# Helper functions (unchanged but used)
# =====================================================================
def build_detailed_calculations_md(stage_stats):
    # (same as before)
    pass

def create_predictive_charts(stage_stats, target):
    # (same as before)
    pass

def current_meta(uid_prefix):
    # (same as before)
    pass

# ... all other helper functions (sanitize, PDF, QR, etc.) remain unchanged.

# =====================================================================
# RUN
# =====================================================================
if __name__ == '__main__':
    ui.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 8080)),
        title='Concrete Cube Verifier',
        favicon='🏗️',
        reload=False,
        reconnect_timeout=30.0,
    )
