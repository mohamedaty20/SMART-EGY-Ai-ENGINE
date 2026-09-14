"""
ui/auth_page.py — Login / Signup.
"""
from nicegui import ui, app
from ui.pwa import inject_pwa

from services import defect_db as db
from services import billing_db as bdb
from services import auth_service as auth
from ui.onboarding import show_onboarding


STYLE = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  html, body {
    background: #0b0b0b !important; color: #e8e8e8 !important;
    font-family: 'JetBrains Mono','Courier New',monospace !important;
    margin: 0; padding: 0;
  }
  .nicegui-content { padding: 0 !important; }
  .q-page, .q-layout { background: #0b0b0b !important; }
  .auth-card {
    background: #141414; border: 1px solid #262626;
    border-radius: 8px; padding: 28px;
    width: 400px; max-width: 92vw;
  }
  .auth-title { font-size: 20px; font-weight: 800; color: #e8e8e8;
                letter-spacing: -0.02em; margin-bottom: 4px; }
  .auth-sub { font-size: 12px; color: #a3a3a3; margin-bottom: 22px; }
  .btn-primary {
    background: #5eead4 !important; color: #0b0b0b !important;
    font-weight: 700 !important; min-height: 42px !important;
    border-radius: 3px !important; text-transform: none !important;
    width: 100%; font-family: 'JetBrains Mono',monospace !important;
    font-size: 12px !important;
  }
  .btn-soft {
    background: #1a1a1a !important; color: #e8e8e8 !important;
    border: 1px solid #262626 !important;
    border-radius: 3px !important; text-transform: none !important;
    width: 100%; min-height: 40px !important;
    font-family: 'JetBrains Mono',monospace !important;
    font-size: 12px !important;
  }
  .q-field--outlined .q-field__control {
    border-radius: 3px !important; background: #1a1a1a !important;
  }
  .q-field--outlined .q-field__control:before {
    border-color: #262626 !important;
  }
  .q-field--outlined.q-field--focused .q-field__control:after {
    border-color: #5eead4 !important;
  }
  .q-field__label, .q-field__native, .q-field__input {
    color: #e8e8e8 !important;
    font-family: 'JetBrains Mono',monospace !important;
    font-size: 12px !important;
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
                "color:#f87171;font-size:12px;margin-top:6px;"
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
                # Onboarding for first login
                if not bdb.has_onboarded(u["id"]):
                    show_onboarding(u["id"],
                                     on_done=lambda: ui.navigate.to("/app"))
                else:
                    ui.navigate.to("/app")

            pass_in.on("keydown.enter", lambda _: do_login())
            ui.button("Sign in", on_click=do_login).classes("btn-primary")
            ui.element('div').style("height:8px;")

            def _forgot():
                ui.navigate.to("/reset")

            ui.button("Forgot password?", on_click=_forgot).props(
                "flat").style("width:100%;color:#808080;font-size:11px;")

            ui.element('div').style("height:6px;")
            ui.button("Create account",
                      on_click=lambda: ui.navigate.to("/signup")).classes(
                "btn-soft")


def signup_page():
    ui.add_head_html(STYLE)

    with ui.column().classes("w-full min-h-screen items-center justify-center"):
        with ui.element('div').classes("auth-card"):
            ui.label("Create account").classes("auth-title")
            ui.label("14-day trial — no card required.").classes("auth-sub")

            name_in = ui.input("Your name").style("width:100%;")
            email_in = ui.input("Email").style("width:100%;")
            pass_in = ui.input("Password (min 6 chars)", password=True,
                                password_toggle_button=True).style("width:100%;")
            pass2_in = ui.input("Confirm password", password=True).style(
                "width:100%;"
            )

            err_holder = ui.label("").style(
                "color:#f87171;font-size:12px;margin-top:6px;"
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
                ok, msg = auth.password_strength_ok(pw)
                if not ok:
                    err_holder.set_text(msg)
                    return
                if pw != pw2:
                    err_holder.set_text("Passwords do not match.")
                    return
                salt, h = auth.hash_password(pw)
                uid, err = db.create_user(em, salt + ":" + h, name)
                if err:
                    err_holder.set_text(err)
                    return
                # Start the trial
                bdb.start_trial(uid)
                token = auth.make_session(uid)
                app.storage.user["session"] = token
                # Show onboarding
                show_onboarding(uid,
                                 on_done=lambda: ui.navigate.to("/app"))

            ui.button("Create account", on_click=do_signup).classes(
                "btn-primary")
            ui.element('div').style("height:10px;")
            ui.button("Back to sign in",
                      on_click=lambda: ui.navigate.to("/login")).classes(
                "btn-soft")
