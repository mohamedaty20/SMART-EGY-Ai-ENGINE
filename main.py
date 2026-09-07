import io
import datetime
import os
import uuid
import re
import asyncio
import numpy as np
import pandas as pd
import plotly.graph_objects as go
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
# STYLING (identical to original)
# =====================================================================
app.native.window_args = {"resizable": True}

ui.add_head_html('''
<style>
    /* ... (full CSS from previous, omitted for brevity but must be included) ... */
</style>
''', shared=True)

# =====================================================================
# HELPER FUNCTIONS (same as before)
# =====================================================================
_LATEX_SIMPLE = { ... }  # include all macros

def sanitize_ai_markdown(text: str) -> str:
    # ... (keep as before)
    pass

def inline_md_to_reportlab(text: str) -> str:
    # ...
    pass

def build_pdf_styles():
    # ...
    pass

def markdown_to_pdf_flowables(raw_text: str, styles: dict, avail_width: float = USABLE_WIDTH):
    # ...
    pass

def generate_qr_code(data_str):
    # ...
    pass

def build_pdf_header(...):
    # ...
    pass

def build_pdf_footer_and_signatures(...):
    # ...
    pass

def build_report_pdf(...):
    # ...
    pass

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
    # ...
    pass

NO_LATEX_RULE = "..."
async def call_gemini(contents, system_instruction=None, temperature=0.1, timeout=60):
    # ...
    pass

# =====================================================================
# MAIN PAGE
# =====================================================================
@ui.page('/')
def main_page():
    ui.query('body').style('width: 100vw; height: 100vh; overflow-x: hidden;')

    # ---- SIDEBAR (unchanged) ----
    sidebar = ui.left_drawer().classes('sidebar-container').style('width: 380px;')
    with sidebar:
        # ... (same as before)

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
        # Title block, marquee (same as before)

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

        # ---- Template upload handling (optional) ----
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

        # ---- Fill template helper ----
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

        # ---- Build detailed calculations markdown ----
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

        # ---- Main run function ----
        async def run_verification():
            # Clear outputs (except chat panels which are recreated)
            result_output_area.clear()
            export_buttons_area.clear()
            chart_area.clear()
            stats_area.clear()
            calc_panel.clear()

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
                        ui.label('AI Statistical Evaluation & Compliance Verdict').classes('text-xl font-bold text-white mb-2')
                        ui.markdown(res_text).classes('markdown-body')

                # Chart
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
                    with ui.expansion('📊 View Detailed Calculations (full math breakdown)', icon='calculate').classes('w-full bg-[#0d1a35] rounded-lg mt-4').expand():
                        md = build_detailed_calculations_md(stage_stats)
                        ui.markdown(md).classes('markdown-body')

                # ---- EXPORT BUTTONS ----
                with export_buttons_area:
                    def download_normal_pdf():
                        try:
                            meta = current_meta('ECP-AI')
                            pdf_bytes = build_report_pdf(
                                "AI CONCRETE CUBE CALCULATION & VERIFICATION REPORT",
                                f"Governing Standard: {basis} | Filter: {stage_filter}",
                                ai_cube_result_holder['text'], meta, logo_bytes_holder['bytes'],
                                extra_flowables_before_body=[
                                    Paragraph("Deterministic Statistics", build_pdf_styles()['h2']),
                                    build_stats_table(stage_stats, USABLE_WIDTH),
                                ],
                            )
                            ui.download(pdf_bytes, filename=f"AI_Concrete_Report_{ticket_input.value}.pdf")
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
                            doc.add_heading('AI Concrete Cube Verification Report', 0)
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
                            doc.add_heading('AI Compliance Evaluation', level=1)
                            doc.add_paragraph(ai_cube_result_holder['text'])
                            out = io.BytesIO()
                            doc.save(out)
                            out.seek(0)
                            ui.download(out.getvalue(), filename=f"AI_Concrete_Report_{ticket_input.value}.docx")
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
                                    Paragraph("AI Evaluation Summary", styles['h2']),
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
                            doc.add_heading('AI Compliance Verdict', level=1)
                            doc.add_paragraph(ai_cube_result_holder['text'])
                            out = io.BytesIO()
                            doc.save(out)
                            out.seek(0)
                            ui.download(out.getvalue(), filename=f"Detailed_Calculations_{ticket_input.value}.docx")
                            ui.notify('Calculations Word downloaded!', type='positive')
                        except Exception as ex:
                            ui.notify(f'Calc Word error: {str(ex)}', type='negative')

                    # Buttons row
                    with ui.row().classes('w-full gap-4 flex-wrap'):
                        ui.button('📄 Download Normal PDF', on_click=download_normal_pdf).classes('primary-btn')
                        ui.button('📝 Download Normal Word', on_click=download_normal_word).classes('primary-btn')
                        if template_bytes_holder['bytes']:
                            ui.button('📎 Download Filled Template', on_click=download_filled_template).classes('primary-btn')
                        ui.button('📊 Download Calculations PDF', on_click=download_calc_pdf).classes('primary-btn')
                        ui.button('📊 Download Calculations Word', on_click=download_calc_word).classes('primary-btn')

                # ---- Chatbots (toggled) ----
                chat_result_visible = {'show': False}
                chat_code_visible = {'show': False}

                def toggle_result_chat():
                    chat_result_visible['show'] = not chat_result_visible['show']
                    chat_result_panel.set_visibility(chat_result_visible['show'])

                def toggle_code_chat():
                    chat_code_visible['show'] = not chat_code_visible['show']
                    chat_code_panel.set_visibility(chat_code_visible['show'])

                with ui.row().classes('w-full gap-4 mt-4'):
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
                            context += f"\nAI Verdict:\n{ai_cube_result_holder['text']}"
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

        # Template upload section (optional)
        with ui.row().classes('w-full gap-4 items-center mb-4'):
            ui.upload(label='Upload Company Template (DOCX with placeholders)',
                      auto_upload=True,
                      on_upload=handle_template_upload).props('flat dark').classes('flex-1')
            template_status

        ui.button('Run AI Statistical Calculation & Verification', on_click=run_verification).classes('primary-btn q-my-md')
        with result_output_area:
            ui.markdown('*Click "Run AI Statistical Calculation & Verification" to generate the report.*').classes('text-sm text-[#A9B6D0]')

        # ---- FOOTER ----
        ui.html('''
        <div class="app-footer">
            <b>Multi-Standard Engineering Quality Assurance Portal</b> &nbsp;|&nbsp; Automated compliance verification across ECP 203, ECP 202, ECP 104, ASTM, AASHTO, BS, EN, and ISO standards.<br>
            <b>Official Direct Contacts:</b>
            LinkedIn: <a href="https://www.linkedin.com/in/mohamed-abd-al-aty-a326a1214/" target="_blank">Mohamed Abd Al Aty</a> &nbsp;|&nbsp;
            Email: <a href="mailto:mohamedabdalaty63@gmail.com">mohamedabdalaty63@gmail.com</a><br>
            <i>Specialized in QA/QC, Civil Engineering Standards &amp; Automated Compliance.</i> &copy; 2026 Eng. Mohamed Abd Al Aty. All rights reserved.<br>
            <span style="color: #FFFFFF; font-weight: 600;">Disclaimer:</span> These AI modules have high accuracy and are specified for the Egyptian codes, but results should be rechecked by a qualified engineer before any decision-making.
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
