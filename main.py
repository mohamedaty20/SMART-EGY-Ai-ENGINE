"""
main.py — Egypt ConTech Suite (Defect Notices MVP).
"""
import os
from dotenv import load_dotenv
from nicegui import app, ui

load_dotenv()

app.native.window_args = {"resizable": True}

ui.add_head_html('''
<style>
    body { background-color: #f8fafc;
           font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    .custom-card {
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1),
                    0 2px 4px -2px rgb(0 0 0 / 0.1);
        background-color: white;
        padding: 24px;
    }
</style>
''', shared=True)

from ui.defect_page import build_defect_ui


@ui.page('/')
def index():
    with ui.row().classes(
        'w-full items-center justify-between bg-slate-900 text-white'
        ' px-6 py-4 shadow-md'
    ):
        with ui.row().classes('items-center gap-3'):
            ui.icon('engineering', size='2rem').classes('text-blue-400')
            ui.label('Egypt ConTech Suite').classes(
                'text-xl font-bold tracking-wide')
        ui.label('Defect Notices · ECP 203 · Egypt').classes(
            'bg-slate-800 px-3 py-1 rounded-full border border-slate-700'
            ' text-sm text-slate-300')

    with ui.column().classes('w-full max-w-5xl mx-auto p-6 gap-6'):
        with ui.column().classes(
            'custom-card w-full border-l-4 border-blue-500'
        ):
            ui.label('Defect Notice Generator').classes(
                'text-2xl font-bold text-slate-800')
            ui.label(
                'Photo a defect → get MS + ECP clause candidates → '
                'tick the real ones → generate a signed Notice PDF.'
            ).classes('text-slate-600')

        build_defect_ui()


ui.run(title='Egypt ConTech Suite', favicon='🏗️',
       host='0.0.0.0', port=int(os.getenv('PORT', 8080)))
