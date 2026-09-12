"""
main.py — Egypt ConTech Suite (Defect Notices MVP).
"""
import os
from dotenv import load_dotenv
from nicegui import app, ui

load_dotenv()

app.native.window_args = {"resizable": True}

from ui.defect_page import build_defect_ui


@ui.page('/')
def index():
    # Page-scoped configuration (must be inside @ui.page)
    ui.dark_mode(False)

    ui.add_head_html('''
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
body {
    background: #f1f5f9;
    color: #0f172a !important;
    font-family: 'Segoe UI', Tahoma, sans-serif;
}
/* Force dark text EVERYWHERE inside our own containers */
.card, .card *,
.defect-item, .defect-item *,
.q-field__native, .q-field__label,
.q-tab, .q-tab__label,
.q-btn__content,
.q-checkbox__label,
label, p, span, div {
    color: #0f172a !important;
}
/* But allow badge colors to win */
.badge, .badge * { color: inherit !important; }
.badge-low { background:#dbeafe; color:#1e40af !important; }
.badge-medium { background:#fef3c7; color:#92400e !important; }
.badge-high { background:#fed7aa; color:#9a3412 !important; }
.badge-critical { background:#fecaca; color:#991b1b !important; }
.badge-open { background:#dbeafe; color:#1e40af !important; }
.badge-closed { background:#d1fae5; color:#065f46 !important; }

.card { background:#ffffff; border-radius:14px;
        border:1px solid #e2e8f0; padding:24px; margin-bottom:16px; }
.defect-item { background:#f8fafc; border:1px solid #e2e8f0;
               border-radius:10px; padding:14px; margin-bottom:10px; }
.defect-name { font-weight:600; font-size:14px; margin:0; }
.defect-cite { font-size:12px; margin:6px 0 0 0; }
.defect-repair { font-size:12px; margin:4px 0 0 0; font-style:italic; }
.section-title { font-size:15px; font-weight:600; margin:0 0 4px 0; }
.section-sub { font-size:13px; margin:0 0 18px 0; }
.badge { display:inline-block; padding:2px 8px;
         border-radius:6px; font-size:11px; font-weight:600; }
</style>
    ''')

    with ui.element('div').classes('app-shell'):
        # ---------- Sidebar ----------
        with ui.element('div').classes('sidebar'):
            with ui.element('div').classes('sidebar-logo'):
                with ui.element('div').classes('sidebar-logo-icon'):
                    ui.html('🏗️')
                with ui.element('div'):
                    ui.html(
                        '<div class="sidebar-logo-text">Egypt ConTech</div>'
                        '<div class="sidebar-logo-sub">Defect Notices · ECP 203</div>'
                    )
            ui.label('QC Workflow').classes(
                'text-xs font-bold text-slate-500 mt-3'
            ).style('letter-spacing:0.08em;')
            ui.label('Photo → AI analysis → Notice PDF → Register').style(
                'font-size:12px;color:#94a3b8;line-height:1.6;'
            )

        # ---------- Main ----------
        with ui.element('div').classes('main-area'):
            with ui.element('div').classes('page-hero'):
                ui.html(
                    '<h1>Defect Notice Generator</h1>'
                    '<p>Photograph a site defect. Get MS + ECP clause '
                    'candidates. Issue a signed notice in under two minutes.</p>'
                )
            build_defect_ui()


ui.run(title='Egypt ConTech Suite', favicon='🏗️',
       host='0.0.0.0', port=int(os.getenv('PORT', 8080)))
