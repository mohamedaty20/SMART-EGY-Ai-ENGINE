"""
ui/auth_page.py — Login / Signup screen.
"""
from nicegui import ui, app

from services import defect_db as db
from services import auth_service as auth


STYLE = """
<style>
  html, body {
    background: #0a0a0a !important; color: #fafafa !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI',
                 Roboto, Helvetica, Arial, sans-serif !important;
    overflow-x: hidden !important;
  }
  .nicegui-content { padding: 0 !important; }
  .q-page, .q-layout { background: #0a0a0a !important; }
  .auth-card {
    background: #141414; border: 1px solid #262626;
    border-radius: 16px; padding: 28px;
    width: 380px; max-width: 92vw;
  }
  .auth-title { font-size: 24px; font-weight: 800; color: #fafafa;
                letter-spacing: -0.02em; margin-bottom: 4px; }
  .auth-sub { font-size: 13px; color: #a3a3a3; margin-bottom: 22px; }
  .btn-primary {
    background: #a855f7 !important; color: #fff !important;
    font-weight: 600 !important; min-height: 44px !important;
    border-radius: 10px !important; text-transform: none !important;
    width: 100%;
  }
  .btn-soft {
    background: #1a1a1a !important; color: #fafafa !important;
    border: 1px solid #262626 !important;
    border-radius: 10px !important; text-transform: none !important;
    width: 100%; min-height: 42px !important;
  }
  .q-field--outlined .q-field__control {
    border-radius: 10px !important;
    background: #1a1a1a !important;
  }
  .q-field--outlined .q-field__control:before {
    border-color: #262626 !important;
  }
  .q-field--outlined.q-field--focused .q-field__control:after {
    border-color: #a855f7 !important;
  }
  .q-field__label, .q-field__native, .q-field__input {
    color: #fafafa !important;
  }
</style>
"""


def login_page():
    ui.add_head_html(STYLE)

    with ui.column().classes("w-full min-h-screen items-center justify-center"):
        with ui.element('div').classes("auth-card"):
            ui.label("Defect Notices").classes("auth-title")
            ui.label("Sign in to your workspace").classes("auth-sub")

            email_in = ui.input("Email").style("width:100%;")
            pass_in = ui.input("Password", password=True,
                                password_toggle_button=True).style("width:100%;")

            err_holder = ui.label("").style(
                "color:#ef4444;font-size:13px;margin-top:6px;"
                "min-height:18px;"
            )

            def do_login():
                err_holder.set_text("")
                em = (email_in.value or "").strip().lower()
                pw = pass_in.value or ""
                if not em or not pw:
                    err_holder.set_text("Email and password required.")
                    return
                u = db.get_user_by_email(em)
                if not u:
                    err_holder.set_text("No account with that email.")
                    return
                salt, h = (u.get("password_hash") or ":").split(":", 1)
                if not auth.verify_password(pw, salt, h):
                    err_holder.set_text("Wrong password.")
                    return
                token = auth.make_session(u["id"])
                app.storage.user["session"] = token
                ui.navigate.to("/")

            pass_in.on("keydown.enter", lambda _: do_login())
            ui.button("Sign in", on_click=do_login).classes("btn-primary")
            ui.element('div').style("height:10px;")
            ui.button("Create account", on_click=lambda: ui.navigate.to("/signup")
                      ).classes("btn-soft")


def signup_page():
    ui.add_head_html(STYLE)

    with ui.column().classes("w-full min-h-screen items-center justify-center"):
        with ui.element('div').classes("auth-card"):
            ui.label("Create account").classes("auth-title")
            ui.label("One workspace per user").classes("auth-sub")

            name_in = ui.input("Your name").style("width:100%;")
            email_in = ui.input("Email").style("width:100%;")
            pass_in = ui.input("Password (min 6 chars)", password=True,
                                password_toggle_button=True).style("width:100%;")
            pass2_in = ui.input("Confirm password", password=True).style(
                "width:100%;"
            )

            err_holder = ui.label("").style(
                "color:#ef4444;font-size:13px;margin-top:6px;"
                "min-height:18px;"
            )

            def do_signup():
                err_holder.set_text("")
                name = (name_in.value or "").strip()
                em = (email_in.value or "").strip().lower()
                pw = pass_in.value or ""
                pw2 = pass2_in.value or ""
                if not name:
                    err_holder.set_text("Name is required.")
                    return
                if not em or "@" not in em:
                    err_holder.set_text("Valid email required.")
                    return
                if len(pw) < 6:
                    err_holder.set_text("Password must be 6+ characters.")
                    return
                if pw != pw2:
                    err_holder.set_text("Passwords do not match.")
                    return
                salt, h = auth.hash_password(pw)
                uid, err = db.create_user(em, salt + ":" + h, name)
                if err:
                    err_holder.set_text(err)
                    return
                token = auth.make_session(uid)
                app.storage.user["session"] = token
                ui.navigate.to("/")

            ui.button("Create account", on_click=do_signup).classes("btn-primary")
            ui.element('div').style("height:10px;")
            ui.button("Back to sign in", on_click=lambda: ui.navigate.to("/login")
                      ).classes("btn-soft")
