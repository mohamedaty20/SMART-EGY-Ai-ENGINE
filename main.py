"""
main.py — entry point.
"""
from nicegui import ui
from ui.defect_page import build_defect_ui


@ui.page('/')
def index():
    build_defect_ui()


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        host="0.0.0.0",
        port=10000,
        title="Defect Notices",
        reload=False,
        reconnect_timeout=60.0,
        ws_ping_interval=30,
        ws_ping_timeout=120,
    )
