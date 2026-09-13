"""
ui/pricing_page.py — Public pricing page with checkout buttons.
"""
from nicegui import ui, app

from services import billing_db as bdb
from services import payment_service as pay
from services import auth_service as auth


STYLE = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Amiri:wght@400;700&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #0b0b0b; --surface: #101010; --surface-2: #161616;
    --border: #1e1e1e; --border-2: #262626;
    --text: #e8e8e8; --muted: #808080; --muted-2: #5a5a5a;
    --accent: #5eead4; --accent-dim: #14b8a6; --warn: #fbbf24;
  }
  html, body {
    background: var(--bg) !important; color: var(--text) !important;
    font-family: 'JetBrains Mono', 'Amiri', 'Courier New', monospace !important;
    margin: 0; padding: 0; -webkit-font-smoothing: antialiased;
  }
  .nicegui-content { padding: 0 !important; }
  .q-page, .q-layout { background: var(--bg) !important; }
  .q-btn {
    border-radius: 3px !important; text-transform: none !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 500 !important; min-height: 40px !important;
    padding: 0 20px !important; font-size: 12px !important;
    box-shadow: none !important;
  }
  .btn-primary { background: var(--accent) !important;
                 color: #0b0b0b !important; font-weight: 700 !important; }
  .btn-primary:hover { background: var(--accent-dim) !important; }
  .btn-soft { background: var(--surface-2) !important;
              color: var(--text) !important;
              border: 1px solid var(--border-2) !important; }
  .btn-soft:hover { background: #1c1c1c !important; }

  .nav {
    position: sticky; top: 0; z-index: 100;
    background: rgba(11,11,11,0.94);
    backdrop-filter: blur(10px);
    border-bottom: 1px solid var(--border);
    padding: 14px 24px;
    display: flex; align-items: center; justify-content: space-between;
  }
  .nav .brand { font-weight: 700; font-size: 13px; color: var(--text); }
  .nav .brand::before {
    content: '● '; color: var(--accent); font-size: 10px;
    vertical-align: middle; margin-right: 4px;
  }
  .nav-links { display: flex; align-items: center; gap: 8px; }
  .nav-links a {
    color: var(--muted); text-decoration: none; font-size: 12px;
    padding: 6px 10px; border-radius: 3px;
  }
  .nav-links a:hover { color: var(--text); }

  .head {
    padding: 60px 24px 30px; max-width: 1000px;
    margin: 0 auto; text-align: center;
  }
  .head h1 {
    font-size: 32px; font-weight: 800; letter-spacing: -0.03em;
    margin: 0 0 12px;
  }
  .head p { color: var(--muted); font-size: 13px; margin: 0 0 8px; }

  .plans {
    display: grid; grid-template-columns: repeat(3, 1fr);
    gap: 16px; max-width: 1000px;
    margin: 30px auto 60px; padding: 0 24px;
  }
  .plan {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 6px; padding: 28px; display: flex;
    flex-direction: column;
  }
  .plan.featured {
    border: 1px solid var(--accent);
    box-shadow: 0 0 0 1px rgba(94,234,212,0.15);
  }
  .plan .badge {
    display: inline-block; font-size: 9px; font-weight: 700;
    letter-spacing: 0.14em; text-transform: uppercase;
    color: var(--accent); margin-bottom: 12px;
  }
  .plan h2 {
    font-size: 18px; font-weight: 700; letter-spacing: -0.02em;
    margin: 0 0 8px;
  }
  .plan .price {
    font-size: 32px; font-weight: 700; letter-spacing: -0.03em;
    margin: 8px 0 4px;
  }
  .plan .price .unit {
    font-size: 12px; color: var(--muted); font-weight: 400;
    margin-left: 4px;
  }
  .plan .desc {
    color: var(--muted); font-size: 12px; line-height: 1.6;
    margin: 0 0 20px; padding-bottom: 20px;
    border-bottom: 1px solid var(--border);
  }
  .plan .features {
    list-style: none; padding: 0; margin: 0 0 24px;
    flex: 1;
  }
  .plan .features li {
    font-size: 12px; color: var(--text-soft); padding: 6px 0;
    padding-left: 18px; position: relative;
  }
  .plan .features li::before {
    content: '✓'; color: var(--accent); font-size: 11px;
    position: absolute; left: 0; top: 6px;
    font-weight: 700;
  }

  .faq {
    max-width: 720px; margin: 0 auto 60px; padding: 0 24px;
  }
  .faq h2 {
    font-size: 22px; font-weight: 700; letter-spacing: -0.02em;
    margin: 0 0 20px;
  }
  .faq-item {
    border-bottom: 1px solid var(--border); padding: 16px 0;
  }
  .faq-item h3 {
    font-size: 13px; font-weight: 600; margin: 0 0 8px;
    color: var(--text);
  }
  .faq-item p {
    font-size: 12px; color: var(--muted); line-height: 1.6;
    margin: 0;
  }

  .footer {
    padding: 30px 24px; text-align: center;
    color: var(--muted-2); font-size: 11px;
    border-top: 1px solid var(--border);
  }
  .footer a { color: var(--muted); text-decoration: none; }

  @media (max-width: 800px) {
    .plans { grid-template-columns: 1fr; }
    .head h1 { font-size: 24px; }
  }
</style>
"""


def pricing_page():
    ui.add_head_html(STYLE)

    with ui.element('div').classes("nav"):
        ui.label("DEFECT NOTICES").classes("brand")
        with ui.element('div').classes("nav-links"):
            ui.link("Home", "/")
            ui.link("Sign in", "/login")
            ui.button("Start free",
                      on_click=lambda: ui.navigate.to("/signup")).classes(
                "btn-primary").style("min-height:32px;padding:0 14px;"
                                      "font-size:11px;")

    with ui.element('div').classes("head"):
        ui.html('<h1>Simple pricing</h1>')
        ui.html('<p>Start free forever on one project. Upgrade when you '
                'need more.</p>')
        ui.html('<p style="color:var(--muted-2);font-size:11px;">'
                'Prices in EGP for Egypt. International cards billed in USD.'
                '</p>')

    with ui.element('div').classes("plans"):
        _plan_card("free", "Starter", "0", "EGP",
                    "For one site, one QC engineer.", [
                        "1 project",
                        "3 method statements",
                        "30 AI analyzes / month",
                        "Notice PDF + register",
                        "Excel export",
                        "Free forever",
                    ], featured=False)
        _plan_card("pro", "Pro", str(bdb.PLANS["pro"]["price_egp"]), "EGP",
                    "For a working QC engineer on 2-3 sites.", [
                        "3 projects",
                        "10 method statements",
                        "500 AI analyzes / month",
                        "Everything in Starter",
                        "Per-sub performance PDF",
                        "Priority email support",
                    ], featured=True)
        _plan_card("business", "Business",
                    str(bdb.PLANS["business"]["price_egp"]), "EGP",
                    "For a consultant office or large contractor.", [
                        "Unlimited projects",
                        "Unlimited method statements",
                        "5,000 AI analyzes / month",
                        "Everything in Pro",
                        "Multi-user workspace (coming)",
                        "Onboarding call",
                    ], featured=False)

    with ui.element('div').classes("faq"):
        ui.html('<h2>Questions</h2>')
        _faq("Do I need a credit card to start?",
             "No. The Starter plan is free forever for one project. "
             "No card required at signup.")
        _faq("Can I cancel anytime?",
             "Yes. Your plan runs to the end of the paid period. No "
             "auto-renewal unless you enable it.")
        _faq("What payment methods do you accept?",
             "In Egypt: Vodafone Cash, InstaPay, Fawry, and cards via "
             "Paymob. Internationally: any card via Stripe.")
        _faq("What happens when my trial ends?",
             "You drop to the Starter plan automatically. Your data is "
             "safe. You can upgrade at any time.")
        _faq("Can I use it for multiple companies?",
             "Yes — each account is separate. Log out and sign up with a "
             "different email for a different company.")

    with ui.element('div').classes("footer"):
        ui.html('<a href="/">Home</a> · <a href="/login">Sign in</a> · '
                '© 2026 Defect Notices')


def _plan_card(plan_id, name, price, currency, desc, features,
                featured=False):
    cls = "plan featured" if featured else "plan"
    with ui.element('div').classes(cls):
        if featured:
            ui.label("POPULAR").classes("badge")
        else:
            ui.label("").classes("badge")
        ui.html("<h2>" + name + "</h2>")
        ui.html('<div class="price">' + price +
                '<span class="unit">' + currency + ' / month</span></div>')
        ui.html('<p class="desc">' + desc + '</p>')
        with ui.element('ul').classes("features"):
            for f in features:
                ui.html("<li>" + f + "</li>")

        def _choose():
            uid = None
            token = app.storage.user.get("session")
            if token:
                uid = auth.read_session(token)
            if not uid:
                ui.navigate.to("/signup")
                return
            if plan_id == "free":
                ui.navigate.to("/")
                return
            _open_checkout(uid, plan_id)

        label = "Start free" if plan_id == "free" else "Choose " + name
        btn_cls = "btn-primary" if featured else "btn-soft"
        ui.button(label, on_click=_choose).classes(btn_cls).style(
            "width:100%;")


def _faq(q, a):
    with ui.element('div').classes("faq-item"):
        ui.html("<h3>" + q + "</h3>")
        ui.html("<p>" + a + "</p>")


def _open_checkout(user_id, plan_id):
    user = {"id": user_id}
    providers = pay.provider_available()

    with ui.dialog() as dlg, ui.card().style(
        "background:#101010;border:1px solid #262626;padding:24px;"
        "min-width:340px;max-width:95vw;width:460px;border-radius:6px;"
        "color:#e8e8e8;font-family:'JetBrains Mono',monospace;"
    ):
        plan = bdb.PLANS.get(plan_id, {})
        ui.label("Checkout — " + str(plan.get("name", plan_id))).style(
            "font-size:16px;font-weight:700;margin-bottom:6px;")
        ui.label(str(plan.get("price_egp", 0)) + " EGP / month").style(
            "font-size:13px;color:#5eead4;font-weight:600;"
            "margin-bottom:18px;")

        if providers["paymob"]:
            ui.label("Pay with Paymob (Vodafone Cash, InstaPay, Fawry, card):"
                      ).style("font-size:11px;color:#808080;"
                              "margin-bottom:6px;")

            def _pay_paymob():
                try:
                    url, _ = pay.checkout_url(user, plan_id, months=1,
                                                preferred="paymob")
                    dlg.close()
                    ui.navigate.to(url)
                except Exception as ex:
                    ui.notify("Checkout failed: " + str(ex),
                               type="negative")

            ui.button("Continue with Paymob", on_click=_pay_paymob).classes(
                "btn-primary").style("width:100%;margin-bottom:12px;")

        if providers["stripe"]:
            ui.label("Or pay with card (international):").style(
                "font-size:11px;color:#808080;margin-bottom:6px;")

            def _pay_stripe():
                try:
                    url, _ = pay.checkout_url(user, plan_id, months=1,
                                                preferred="stripe")
                    dlg.close()
                    ui.navigate.to(url)
                except Exception as ex:
                    ui.notify("Checkout failed: " + str(ex),
                               type="negative")

            ui.button("Continue with card", on_click=_pay_stripe).classes(
                "btn-soft").style("width:100%;margin-bottom:12px;")

        if not providers["paymob"] and not providers["stripe"]:
            ui.label("Payment gateway not yet configured.").style(
                "font-size:12px;color:#808080;margin-bottom:14px;")
            ui.label("Add PAYMOB_API_KEY / PAYMOB_INTEGRATION_ID / "
                      "PAYMOB_IFRAME_ID to enable Paymob.").style(
                "font-size:10px;color:#5a5a5a;margin-bottom:14px;")

            def _demo_pay():
                try:
                    url, _ = pay.checkout_url(user, plan_id, months=1,
                                                preferred="demo")
                    dlg.close()
                    ui.navigate.to(url)
                except Exception as ex:
                    ui.notify("Demo failed: " + str(ex), type="negative")

            ui.button("Continue in DEMO mode", on_click=_demo_pay).classes(
                "btn-soft").style("width:100%;margin-bottom:12px;")

        ui.button("Cancel", on_click=dlg.close).props("flat").style(
            "width:100%;color:#808080;font-size:11px;")

    dlg.open()
