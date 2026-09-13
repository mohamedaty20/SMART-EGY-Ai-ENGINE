"""
main.py — entry with auth.
"""
import os
from nicegui import ui, app

from services import auth_service as auth
from ui.auth_page import login_page, signup_page
from ui.defect_page import build_defect_ui


def _current_user_id():
    token = app.storage.user.get("session")
    if not token:
        return None
    return auth.read_session(token)


@ui.page('/login')
def login_route():
    if _current_user_id():
        ui.navigate.to('/')
        return
    login_page()


@ui.page('/signup')
def signup_route():
    if _current_user_id():
        ui.navigate.to('/')
        return
    signup_page()


@ui.page('/logout')
def logout_route():
    app.storage.user.clear()
    ui.navigate.to('/login')


@ui.page('/')
def index():
    uid = _current_user_id()
    if not uid:
        ui.navigate.to('/login')
        return
    build_defect_ui(uid)


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        host="0.0.0.0",
        port=10000,
        title="Defect Notices",
        reload=False,
        reconnect_timeout=60.0,
        storage_secret=os.environ.get("SESSION_SECRET", "change-me-now"),
    )
