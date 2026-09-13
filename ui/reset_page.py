"""
ui/reset_page.py — Password reset (request + confirm).
"""
from nicegui import ui, app

from services import defect_db as db
from services import billing_db as bdb
from services import auth_service as auth


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
    border-radius: 3px !important;
    background: #1a1a1a !important;
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
  .link-box {
    background: #0b0b0b; border: 1px solid #262626;
    border-radius: 3px; padding: 12px;
    font-size: 11px; color: #5eead4;
    word-break: break-all; margin: 14px 0;
    font-family: 'JetBrains Mono',monospace;
  }
</style>
"""


def reset_request_page():
    ui.add_head_html(STYLE)
    with ui.column().classes("w-full min-h-screen items-center justify-center"):
        with ui.element('div').classes("auth-card"):
            ui.label("Reset password").classes("auth-title")
            ui.label("Enter your account email.").classes("auth-sub")

            email_in = ui.input("Email").style("width:100%;")
            msg_holder = ui.element('div').style("width:100%;")

            def _submit():
                msg_holder.clear()
                em = (email_in.value or "").strip().lower()
                if not em:
                    with msg_holder:
                        ui.label("Email required.").style(
                            "color:#f87171;font-size:12px;margin-top:8px;")
                    return
                u = db.get_user_by_email(em)
                if not u:
                    # don't leak whether account exists
                    with msg_holder:
                        ui.label("If that email is registered, a reset "
                                  "link was created.").style(
                            "color:#a3a3a3;font-size:11px;margin-top:10px;")
                    return
                token = auth.new_reset_token()
                bdb.create_reset_token(u["id"], token, hours=2)
                base = ""
                try:
                    base = str(app.storage.browser.get("window_location", ""))
                except Exception:
                    base = ""
                link = "/reset/confirm?token=" + token
                with msg_holder:
                    ui.label("Reset link (valid 2 hours):").style(
                        "color:#a3a3a3;font-size:11px;margin-top:10px;")
                    ui.html('<div class="link-box">' + link + '</div>')
                    ui.label("Email delivery not yet enabled — copy this link "
                              "and open it in your browser.").style(
                        "color:#5a5a5a;font-size:10px;margin-top:4px;")

            ui.button("Send reset link", on_click=_submit).classes("btn-primary")
            ui.element('div').style("height:10px;")
            ui.button("Back to sign in",
                      on_click=lambda: ui.navigate.to("/login")).classes(
                "btn-soft")
            msg_holder


def reset_confirm_page(token: str = ""):
    ui.add_head_html(STYLE)
    with ui.column().classes("w-full min-h-screen items-center justify-center"):
        with ui.element('div').classes("auth-card"):
            ui.label("New password").classes("auth-title")
            ui.label("Choose a new password for your account.").classes(
                "auth-sub")

            if not token:
                ui.label("Missing reset token.").style(
                    "color:#f87171;font-size:12px;margin-bottom:14px;")
                ui.button("Back to sign in",
                          on_click=lambda: ui.navigate.to("/login")).classes(
                    "btn-soft")
                return

            rec = bdb.get_reset_by_token(token)
            if not rec:
                ui.label("Invalid or expired link.").style(
                    "color:#f87171;font-size:12px;margin-bottom:14px;")
                ui.button("Back to sign in",
                          on_click=lambda: ui.navigate.to("/login")).classes(
                    "btn-soft")
                return
            if rec.get("used_at"):
                ui.label("This link has already been used.").style(
                    "color:#f87171;font-size:12px;margin-bottom:14px;")
                ui.button("Back to sign in",
                          on_click=lambda: ui.navigate.to("/login")).classes(
                    "btn-soft")
                return

            import datetime
            try:
                exp = datetime.datetime.strptime(rec["expires_at"][:19],
                                                  "%Y-%m-%d %H:%M:%S")
            except Exception:
                exp = None
            if exp and datetime.datetime.utcnow() > exp:
                ui.label("This link has expired.").style(
                    "color:#f87171;font-size:12px;margin-bottom:14px;")
                ui.button("Request a new one",
                          on_click=lambda: ui.navigate.to("/reset")).classes(
                    "btn-soft")
                return

            pw1 = ui.input("New password", password=True,
                            password_toggle_button=True).style("width:100%;")
            pw2 = ui.input("Confirm password", password=True).style(
                "width:100%;")
            err_holder = ui.element('div').style("width:100%;")

            def _save():
                err_holder.clear()
                p1 = pw1.value or ""
                p2 = pw2.value or ""
                ok, msg = auth.password_strength_ok(p1)
                if not ok:
                    with err_holder:
                        ui.label(msg).style(
                            "color:#f87171;font-size:12px;margin-top:8px;")
                    return
                if p1 != p2:
                    with err_holder:
                        ui.label("Passwords do not match.").style(
                            "color:#f87171;font-size:12px;margin-top:8px;")
                    return
                salt, h = auth.hash_password(p1)
                db.update_user_password(rec["user_id"], salt + ":" + h)
                bdb.mark_reset_used(rec["id"])
                with err_holder:
                    ui.label("Password updated. Redirecting...").style(
                        "color:#5eead4;font-size:12px;margin-top:8px;")
                ui.timer(1.0, lambda: ui.navigate.to("/login"), once=True)

            ui.button("Save password", on_click=_save).classes("btn-primary")
            ui.element('div').style("height:10px;")
            ui.button("Cancel", on_click=lambda: ui.navigate.to("/login")
                      ).classes("btn-soft")
            err_holder
