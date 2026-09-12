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
    ui.dark_mode(False)

    ui.add_head_html('''
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        html, body {
            background: #f1f5f9 !important;
            color: #0f172a !important;
            font-family: 'Inter', 'Segoe UI', Tahoma, sans-serif;
            margin: 0;
            padding: 0;
        }
        /* Force dark text on every text-bearing element */
        .q-page, .q-page *,
        .nicegui-content, .nicegui-content *,
        .q-field__native, .q-field__label, .q-field__marginal,
        .q-tab, .q-tab__label,
        .q-btn__content,
        .q-checkbox__label,
        .q-item__label, .q-item,
        label, p, span, div, h1, h2, h3, h4, h5, h6, b, i, small {
            color: #0f172a !important;
        }
        /* Badges override the dark text */
        .badge, .badge * { color: inherit !important; }
        .badge-low      { background:#dbeafe; color:#1e40af !important; }
        .badge-medium   { background:#fef3c7; color:#92400e !important; }
        .badge-high     { background:#fed7aa; color:#9a3412 !important; }
        .badge-critical { background:#fecaca; color:#991b1b !important; }
        .badge-open     { background:#dbeafe; color:#1e40af !important; }
        .badge-closed   { background:#d1fae5; color:#065f46 !important; }

        .app-shell { display: flex; min-height: 100vh; }

        .sidebar {
            width: 260px;
            background: #0f172a !important;
            padding: 24px 18px;
            flex-shrink: 0;
        }
        .sidebar * { color: #e2e8f0 !important; }
        .sidebar .sidebar-logo {
            display: flex; align-items: center; gap: 10px;
            padding-bottom: 20px;
            border-bottom: 1px solid #1e293b;
            margin-bottom: 16px;
        }
        .sidebar .sidebar-logo-icon {
            width: 36px; height: 36px;
            border-radius: 10px;
            background: linear-gradient(135deg, #3b82f6, #06b6d4);
            display: flex; align-items: center; justify-content: center;
            font-size: 18px;
        }
        .sidebar .sidebar-logo-text {
            font-weight: 700; font-size: 15px; color: #f8fafc !important;
        }
        .sidebar .sidebar-logo-sub {
            font-size: 11px; color: #94a3b8 !important;
        }

        .main-area { flex: 1; padding: 28px 36px; max-width: 1400px; }

        .page-hero h1 {
            font-size: 26px; font-weight: 700; margin: 0 0 6px 0;
        }
        .page-hero p {
            font-size: 14px; color: #64748b !important; margin: 0 0 24px 0;
        }

        .card {
            background: #ffffff;
            border-radius: 14px;
            border: 1px solid #e2e8f0;
            padding: 24px;
            margin-bottom: 16px;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
        }
        .card .section-title {
            font-size: 15px; font-weight: 600; margin: 0 0 4px 0;
        }
        .card .section-sub {
            font-size: 13px; color: #64748b !important;
            margin: 0 0 18px 0; line-height: 1.5;
        }

        .defect-item {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 14px 16px;
            margin-bottom: 10px;
        }
        .defect-item .defect-name {
            font-weight: 600; font-size: 14px; margin: 0;
        }
        .defect-item .defect-cite {
            font-size: 12px; color: #475569 !important;
            margin: 6px 0 0 0;
        }
        .defect-item .defect-repair {
            font-size: 12px; color: #64748b !important;
            margin: 4px 0 0 0; font-style: italic;
        }

        .badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 600;
        }

        /* Quasar input text */
        .q-field__native, .q-field__prefix, .q-field__suffix {
            color: #0f172a !important;
        }
        .q-field__label { color: #475569 !important; }
        .q-field--outlined .q-field__control {
            border-radius: 10px !important;
            background: #ffffff !important;
        }
        .q-btn {
            border-radius: 10px !important;
            text-transform: none !important;
            font-weight: 600 !important;
        }
        .q-tab {
            text-transform: none !important;
            font-weight: 600 !important;
            font-size: 13px !important;
        }
        .q-table { background: #ffffff !important; }
        .q-table th, .q-table td {
            color: #0f172a !important;
            background: #ffffff !important;
        }
        .q-table tbody tr:hover td {
            background: #f8fafc !important;
        }
        .q-dialog .q-card { background: #ffffff !important; }

        @media (max-width: 900px) {
            .app-shell { flex-direction: column; }
            .sidebar { width: 100%; padding: 16px; }
            .main-area { padding: 16px; }
        }
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
            ui.html(
                '<div style="font-size:11px;font-weight:700;'
                'letter-spacing:0.08em;color:#64748b;margin-top:12px;">'
                'QC WORKFLOW</div>'
            )
            ui.html(
                '<div style="font-size:12px;line-height:1.6;'
                'color:#94a3b8;margin-top:8px;">'
                'Photo &rarr; AI analysis &rarr; Notice PDF &rarr; Register</div>'
            )

        # ---------- Main ----------
        with ui.element('div').classes('main-area'):
            with ui.element('div').classes('page-hero'):
                ui.html('<h1>Defect Notice Generator</h1>')
                ui.html(
                    '<p>Photograph a site defect. Get MS + ECP clause '
                    'candidates. Issue a signed notice in under two minutes.</p>'
                )
            build_defect_ui()


ui.run(title='Egypt ConTech Suite', favicon='🏗️',
       host='0.0.0.0', port=int(os.getenv('PORT', 8080)))
