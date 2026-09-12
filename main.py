"""
main.py — Egypt ConTech Suite (Defect Notices MVP).
"""
import os
from dotenv import load_dotenv
from nicegui import app, ui

load_dotenv()

app.native.window_args = {"resizable": True}

# Force light mode — otherwise NiceGUI renders text in white on our light UI
ui.dark_mode(False)

ui.add_head_html('''
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
    html, body {
        background: #f1f5f9;
        color: #0f172a;
        font-family: 'Inter', 'Segoe UI', Tahoma, sans-serif;
        margin: 0;
        padding: 0;
    }
    .app-shell {
        display: flex;
        min-height: 100vh;
    }
    .sidebar {
        width: 260px;
        background: #0f172a;
        color: #e2e8f0;
        padding: 24px 18px;
        display: flex;
        flex-direction: column;
        gap: 8px;
        flex-shrink: 0;
    }
    .sidebar-logo {
        display: flex;
        align-items: center;
        gap: 10px;
        padding-bottom: 20px;
        border-bottom: 1px solid #1e293b;
        margin-bottom: 16px;
    }
    .sidebar-logo-icon {
        width: 36px; height: 36px;
        border-radius: 10px;
        background: linear-gradient(135deg, #3b82f6, #06b6d4);
        display: flex; align-items: center; justify-content: center;
        font-size: 18px;
    }
    .sidebar-logo-text {
        font-weight: 700;
        font-size: 15px;
        color: #f8fafc;
        letter-spacing: -0.01em;
    }
    .sidebar-logo-sub {
        font-size: 11px;
        color: #94a3b8;
    }
    .main-area {
        flex: 1;
        padding: 28px 36px;
        max-width: 1400px;
    }
    .page-hero {
        margin-bottom: 24px;
    }
    .page-hero h1 {
        font-size: 26px;
        font-weight: 700;
        color: #0f172a;
        margin: 0 0 6px 0;
        letter-spacing: -0.02em;
    }
    .page-hero p {
        font-size: 14px;
        color: #64748b;
        margin: 0;
    }
    .card {
        background: #ffffff;
        border-radius: 14px;
        border: 1px solid #e2e8f0;
        padding: 24px;
        margin-bottom: 16px;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
    }
    .card-tight {
        padding: 18px 20px;
    }
    .section-title {
        font-size: 15px;
        font-weight: 600;
        color: #0f172a;
        margin: 0 0 4px 0;
    }
    .section-sub {
        font-size: 13px;
        color: #64748b;
        margin: 0 0 18px 0;
        line-height: 1.5;
    }
    .defect-item {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 14px 16px;
        margin-bottom: 10px;
        transition: border-color 0.15s;
    }
    .defect-item:hover {
        border-color: #cbd5e1;
    }
    .defect-name {
        font-weight: 600;
        color: #0f172a;
        font-size: 14px;
        margin: 0;
    }
    .defect-cite {
        font-size: 12px;
        color: #475569;
        margin: 6px 0 0 0;
    }
    .defect-repair {
        font-size: 12px;
        color: #64748b;
        margin: 4px 0 0 0;
        font-style: italic;
    }
    .badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.02em;
    }
    .badge-low      { background: #dbeafe; color: #1e40af; }
    .badge-medium   { background: #fef3c7; color: #92400e; }
    .badge-high     { background: #fed7aa; color: #9a3412; }
    .badge-critical { background: #fecaca; color: #991b1b; }
    .badge-open     { background: #dbeafe; color: #1e40af; }
    .badge-closed   { background: #d1fae5; color: #065f46; }
    .q-field--outlined .q-field__control {
        border-radius: 10px !important;
    }
    .q-btn {
        border-radius: 10px !important;
        text-transform: none !important;
        font-weight: 600 !important;
        letter-spacing: 0 !important;
    }
    .q-tab {
        text-transform: none !important;
        font-weight: 600 !important;
        font-size: 13px !important;
    }
    @media (max-width: 900px) {
        .app-shell { flex-direction: column; }
        .sidebar { width: 100%; padding: 16px; flex-direction: row; align-items: center; }
        .sidebar > * { display: none; }
        .sidebar-logo { display: flex !important; padding: 0; border: none; margin: 0; }
        .main-area { padding: 16px; }
    }
</style>
''', shared=True)

from ui.defect_page import build_defect_ui


@ui.page('/')
def index():
    with ui.element('div').classes('app-shell'):
        # ---------- Sidebar ----------
        with ui.element('div').classes('sidebar'):
            with ui.element('div').classes('sidebar-logo'):
                with ui.element('div').classes('sidebar-logo-icon'):
                    ui.html('🏗️')
                with ui.element('div'):
                    ui.html('<div class="sidebar-logo-text">Egypt ConTech</div>'
                            '<div class="sidebar-logo-sub">Defect Notices · ECP 203</div>')
            ui.label('QC Workflow').classes('text-xs font-bold text-slate-500 mt-3').style(
                'letter-spacing:0.08em;'
            )
            ui.label('Photo → AI analysis → Notice PDF → Register').style(
                'font-size:12px;color:#94a3b8;line-height:1.6;'
            )
            ui.element('div').style('flex:1;')

        # ---------- Main ----------
        with ui.element('div').classes('main-area'):
            with ui.element('div').classes('page-hero'):
                ui.html('<h1>Defect Notice Generator</h1>'
                        '<p>Photograph a site defect. Get MS + ECP clause candidates. '
                        'Issue a signed notice in under two minutes.</p>')
            build_defect_ui()


ui.run(title='Egypt ConTech Suite', favicon='🏗️',
       host='0.0.0.0', port=int(os.getenv('PORT', 8080)))
