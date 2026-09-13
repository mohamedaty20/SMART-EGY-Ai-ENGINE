"""
main.py — Entry with auth, billing, admin, reset, PWA.
"""
import os
import io
import json as _json
from nicegui import ui, app
from fastapi import Request
from fastapi.responses import Response, RedirectResponse

from services import auth_service as auth
from services import billing_db as bdb
from services import payment_service as pay
from ui.auth_page import login_page, signup_page
from ui.landing_page import landing_page
from ui.pricing_page import pricing_page
from ui.reset_page import reset_request_page, reset_confirm_page
from ui.admin_page import admin_page


BASE_URL = os.environ.get("APP_BASE_URL",
                           "https://smart-egy-ai-engine.onrender.com")


def _current_user_id():
    token = app.storage.user.get("session")
    if not token:
        return None
    return auth.read_session(token)


# =====================================================================
# PWA — manifest, service worker, icons
# =====================================================================
MANIFEST = {
    "name": "Defect Notices",
    "short_name": "Defects",
    "description": "AI-powered defect notices for QC engineers",
    "start_url": "/app",
    "scope": "/",
    "display": "standalone",
    "orientation": "portrait",
    "background_color": "#0b0b0b",
    "theme_color": "#0b0b0b",
    "icons": [
        {"src": "/icon-192.png", "sizes": "192x192",
         "type": "image/png", "purpose": "any maskable"},
        {"src": "/icon-512.png", "sizes": "512x512",
         "type": "image/png", "purpose": "any maskable"},
    ],
}


SERVICE_WORKER = """
self.addEventListener('install', function(e) {
  self.skipWaiting();
});
self.addEventListener('activate', function(e) {
  e.waitUntil(self.clients.claim());
});
self.addEventListener('fetch', function(e) {
  // Pass-through
});
"""


def _make_icon(size):
    try:
        from PIL import Image, ImageDraw, ImageFont
        img = Image.new("RGB", (size, size), "#0b0b0b")
        d = ImageDraw.Draw(img)
        pad = int(size * 0.14)
        d.rounded_rectangle(
            [pad, pad, size - pad, size - pad],
            radius=int(size * 0.14), fill="#5eead4")
        try:
            font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                int(size * 0.34))
        except Exception:
            font = ImageFont.load_default()
        txt = "DN"
        bbox = d.textbbox((0, 0), txt, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        d.text(((size - tw) / 2 - bbox[0], (size - th) / 2 - bbox[1]),
               txt, fill="#0b0b0b", font=font)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return buf.read()
    except Exception as e:
        print("[pwa] icon gen failed: " + repr(e))
        return b""


@app.get('/manifest.json')
def manifest_route():
    return Response(content=_json.dumps(MANIFEST),
                     media_type="application/manifest+json")


@app.get('/service-worker.js')
def sw_route():
    return Response(content=SERVICE_WORKER,
                     media_type="application/javascript")


@app.get('/icon-192.png')
def icon_192():
    return Response(content=_make_icon(192), media_type="image/png")


@app.get('/icon-512.png')
def icon_512():
    return Response(content=_make_icon(512), media_type="image/png")


# =====================================================================
# PUBLIC
# =====================================================================
@ui.page('/')
def landing_route():
    landing_page()


@ui.page('/pricing')
def pricing_route():
    pricing_page()


# =====================================================================
# AUTH
# =====================================================================
@ui.page('/login')
def login_route():
    if _current_user_id():
        ui.navigate.to('/app')
        return
    login_page()


@ui.page('/signup')
def signup_route():
    if _current_user_id():
        ui.navigate.to('/app')
        return
    signup_page()


@ui.page('/logout')
def logout_route():
    app.storage.user.clear()
    ui.navigate.to('/')


@ui.page('/reset')
def reset_route():
    reset_request_page()


@ui.page('/reset/confirm')
def reset_confirm_route(token: str = ""):
    reset_confirm_page(token)


# =====================================================================
# APP
# =====================================================================
@ui.page('/app')
def app_route():
    uid = _current_user_id()
    if not uid:
        ui.navigate.to('/login')
        return
    active, plan, reason = bdb.is_active(uid)
    if not active:
        _render_expired(plan, reason)
        return
    from ui.defect_page import build_defect_ui
    build_defect_ui(uid)


def _render_expired(plan, reason):
    with ui.column().classes("w-full min-h-screen items-center "
                              "justify-center").style(
        "background:#0b0b0b;color:#e8e8e8;"
        "font-family:'JetBrains Mono',monospace;"
    ):
        ui.icon("lock_clock").style("font-size:52px;color:#fbbf24;")
        ui.label("Subscription expired").style(
            "font-size:22px;font-weight:700;margin-top:16px;")
        ui.label("Your " + str(plan) + " plan has ended "
                  "(" + str(reason) + ").").style(
            "color:#b8b8b8;font-size:13px;margin-top:6px;")
        ui.label("Your data is safe. Renew to continue.").style(
            "color:#808080;font-size:11px;margin-top:2px;")
        ui.element('div').style("height:22px;")
        with ui.row().style("gap:8px;"):
            ui.button("View plans",
                      on_click=lambda: ui.navigate.to("/pricing")).style(
                "background:#5eead4;color:#0b0b0b;font-weight:700;"
                "border-radius:3px;padding:0 22px;min-height:40px;"
                "font-size:12px;text-transform:none;")
            ui.button("Log out",
                      on_click=lambda: ui.navigate.to("/logout")).style(
                "background:#161616;color:#e8e8e8;"
                "border:1px solid #262626;border-radius:3px;"
                "padding:0 22px;min-height:40px;font-size:12px;"
                "text-transform:none;")


# =====================================================================
# ADMIN
# =====================================================================
@ui.page('/admin')
def admin_route():
    uid = _current_user_id()
    if not uid:
        ui.navigate.to('/login')
        return
    admin_page(uid)


# =====================================================================
# PAYMENTS
# =====================================================================
@ui.page('/payment/ok')
def payment_ok(provider: str = "", plan: str = "", uid: str = ""):
    if not uid or not plan:
        ui.navigate.to('/pricing')
        return
    try:
        user_id = int(uid)
    except Exception:
        ui.navigate.to('/pricing')
        return

    if provider == "demo":
        pay.complete_demo_payment(user_id, plan, months=1)
        _render_paid("Demo", plan)
        return

    # Paymob activates via /payment/paymob/callback (HMAC-verified).
    # Stripe requires a server-side session lookup — do NOT trust this URL.
    if provider in ("stripe", "paymob"):
        _render_pending(provider, plan)
        return

    _render_paid(provider, plan)


def _render_pending(provider, plan_id):
    """Shown when a payment is awaiting server-side confirmation."""
    plan = bdb.PLANS.get(plan_id, {})
    with ui.column().classes("w-full min-h-screen items-center "
                              "justify-center").style(
        "background:#0b0b0b;color:#e8e8e8;"
        "font-family:'JetBrains Mono',monospace;"
    ):
        ui.icon("hourglass_top").style("font-size:52px;color:#fbbf24;")
        ui.label("Confirming payment...").style(
            "font-size:22px;font-weight:700;margin-top:16px;")
        ui.label("Plan: " + str(plan.get("name", plan_id))).style(
            "color:#b8b8b8;font-size:13px;margin-top:4px;")
        ui.label("Provider: " + str(provider)).style(
            "color:#808080;font-size:11px;margin-top:2px;")
        ui.label("Your plan will activate when the provider confirms.").style(
            "color:#808080;font-size:11px;margin-top:8px;")
        ui.element('div').style("height:20px;")
        ui.button("Open app",
                  on_click=lambda: ui.navigate.to("/app")).style(
            "background:#5eead4;color:#0b0b0b;font-weight:700;"
            "border-radius:3px;padding:0 24px;min-height:40px;"
            "font-size:12px;text-transform:none;")


def _render_paid(provider, plan_id):
    plan = bdb.PLANS.get(plan_id, {})
    with ui.column().classes("w-full min-h-screen items-center "
                              "justify-center").style(
        "background:#0b0b0b;color:#e8e8e8;"
        "font-family:'JetBrains Mono',monospace;"
    ):
        ui.icon("check_circle").style("font-size:52px;color:#5eead4;")
        ui.label("Payment received").style(
            "font-size:22px;font-weight:700;margin-top:16px;")
        ui.label("Plan: " + str(plan.get("name", plan_id))).style(
            "color:#b8b8b8;font-size:13px;margin-top:4px;")
        ui.label("Provider: " + str(provider)).style(
            "color:#808080;font-size:11px;margin-top:2px;")
        ui.element('div').style("height:20px;")
        ui.button("Open app",
                  on_click=lambda: ui.navigate.to("/app")).style(
            "background:#5eead4;color:#0b0b0b;font-weight:700;"
            "border-radius:3px;padding:0 24px;min-height:40px;"
            "font-size:12px;text-transform:none;")


@ui.page('/payment/demo')
def payment_demo(plan: str = "", months: str = "1", uid: str = ""):
    if not uid or not plan:
        ui.navigate.to('/pricing')
        return
    try:
        user_id = int(uid)
        m = int(months)
    except Exception:
        ui.navigate.to('/pricing')
        return
    ok = pay.complete_demo_payment(user_id, plan, months=m)
    if not ok:
        ui.navigate.to('/pricing')
        return
    _render_paid("Demo", plan)


# ---------------------------------------------------------------------
# PAYMOB CALLBACK — real FastAPI route (NOT a NiceGUI page)
# ---------------------------------------------------------------------
@app.get('/payment/paymob/callback')
def paymob_callback(request: Request):
    try:
        params = dict(request.query_params)
    except Exception:
        params = {}

    if not pay.paymob_verify_hmac(params):
        return Response(content="Signature check failed.", status_code=403,
                         media_type="text/plain")

    success = str(params.get("success", "")).lower() in ("true", "1")
    if not success:
        return RedirectResponse(url="/pricing?cancel=1")

    moid = str(params.get("merchant_order_id", ""))
    plan_id = ""
    user_id = None
    try:
        if moid.startswith("u"):
            parts = moid[1:].split("-", 1)
            user_id = int(parts[0])
            plan_id = parts[1] if len(parts) > 1 else ""
    except Exception:
        pass

    if not user_id or plan_id not in bdb.PLANS:
        return RedirectResponse(url="/pricing")

    bdb.apply_payment(
        user_id, plan_id, provider="paymob",
        provider_ref=str(params.get("id", "")),
        months=1,
        amount=float(params.get("amount_cents", 0)) / 100.0,
        currency=str(params.get("currency", "EGP")))

    # Paymob expects a 200 on the callback; send them to the success page.
    return RedirectResponse(url="/payment/ok?provider=paymob&plan=" +
                                 plan_id + "&uid=" + str(user_id))


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        host="0.0.0.0",
        port=10000,
        title="Defect Notices",
        reload=False,
        reconnect_timeout=60.0,
        storage_secret=os.environ.get("SESSION_SECRET", "change-me-now"),
    )
