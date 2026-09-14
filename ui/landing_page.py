"""
ui/landing_page.py — Public landing page.
"""
from nicegui import ui, app
from services import auth_service as auth
from ui.pwa import inject_pwa


STYLE = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Amiri:wght@400;700&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #0b0b0b; --surface: #101010; --surface-2: #161616;
    --border: #1e1e1e; --border-2: #262626;
    --text: #e8e8e8; --text-soft: #b8b8b8; --muted: #808080;
    --muted-2: #5a5a5a; --accent: #5eead4; --accent-dim: #14b8a6;
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
    transition: color 0.12s;
  }
  .nav-links a:hover { color: var(--text); }

  .hero {
    padding: 80px 24px 60px;
    max-width: 900px; margin: 0 auto; text-align: center;
  }
  .hero h1 {
    font-size: 40px; font-weight: 800; line-height: 1.15;
    letter-spacing: -0.03em; margin: 0 0 16px;
  }
  .hero h1 .accent { color: var(--accent); }
  .hero p {
    font-size: 15px; color: var(--muted); max-width: 620px;
    margin: 0 auto 32px; line-height: 1.6;
  }
  .hero-buttons { display: flex; gap: 12px; justify-content: center;
                  flex-wrap: wrap; }

  .section {
    padding: 60px 24px; max-width: 900px; margin: 0 auto;
  }
  .section-title {
    font-size: 24px; font-weight: 700; letter-spacing: -0.02em;
    margin: 0 0 12px;
  }
  .section-sub {
    color: var(--muted); font-size: 13px; margin-bottom: 40px;
  }

  .feature-grid {
    display: grid; grid-template-columns: repeat(2, 1fr);
    gap: 16px;
  }
  .feature {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 4px; padding: 24px;
  }
  .feature h3 {
    font-size: 13px; font-weight: 700; color: var(--text);
    margin: 0 0 8px;
  }
  .feature p {
    font-size: 12px; color: var(--muted); line-height: 1.6;
    margin: 0;
  }
  .feature .num {
    color: var(--accent); font-size: 11px; font-weight: 700;
    letter-spacing: 0.14em; margin-bottom: 10px;
  }

  .steps {
    display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px;
    counter-reset: step;
  }
  .step {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 4px; padding: 24px;
    position: relative;
  }
  .step .step-num {
    font-size: 11px; font-weight: 700; color: var(--accent);
    letter-spacing: 0.14em; margin-bottom: 10px;
  }
  .step h3 { font-size: 13px; font-weight: 700; margin: 0 0 8px; }
  .step p { font-size: 12px; color: var(--muted); margin: 0;
            line-height: 1.6; }

  .cta {
    text-align: center; padding: 80px 24px;
    border-top: 1px solid var(--border);
    border-bottom: 1px solid var(--border);
    background: var(--surface);
    margin-top: 60px;
  }
  .cta h2 {
    font-size: 28px; font-weight: 700; letter-spacing: -0.02em;
    margin: 0 0 12px;
  }
  .cta p { color: var(--muted); font-size: 13px; margin: 0 0 24px; }

  .footer {
    padding: 30px 24px; text-align: center;
    color: var(--muted-2); font-size: 11px;
    border-top: 1px solid var(--border);
  }
  .footer a { color: var(--muted); text-decoration: none; }

  @media (max-width: 640px) {
    .hero h1 { font-size: 28px; }
    .feature-grid { grid-template-columns: 1fr; }
    .steps { grid-template-columns: 1fr; }
    .nav { padding: 10px 16px; }
    .nav-links a { padding: 4px 6px; font-size: 11px; }
    .hero { padding: 50px 16px 40px; }
    .section { padding: 40px 16px; }
  }
</style>
"""


def landing_page():
    ui.add_head_html(STYLE)

    # Nav
    with ui.element('div').classes("nav"):
        ui.label("DEFECT NOTICES").classes("brand")
        with ui.element('div').classes("nav-links"):
            ui.link("Features", "#features")
            ui.link("How it works", "#how")
            ui.link("Pricing", "/pricing")
            ui.link("Sign in", "/login")
            ui.button("Start free", on_click=lambda: ui.navigate.to("/signup")
                      ).classes("btn-primary").style(
                "min-height:32px;padding:0 14px;font-size:11px;")

    # Hero
    with ui.element('div').classes("hero"):
        ui.html('<h1>Defect notices in <span class="accent">90 seconds</span>, '
                'not 30 minutes.</h1>')
        ui.html('<p>Snap a photo of a site defect. AI suggests the defects, '
                'matches them to your Method Statement and ECP codes, and '
                'generates a signed Notice to Subcontractor PDF — saved to a '
                'register you can search, filter, and export.</p>')
        with ui.element('div').classes("hero-buttons"):
            ui.button("Start free — no card", on_click=lambda: ui.navigate.to(
                "/signup")).classes("btn-primary")
            ui.button("See pricing", on_click=lambda: ui.navigate.to(
                "/pricing")).classes("btn-soft")

    # Features
    with ui.element('div').classes("section").props('id="features"'):
        ui.label("What it does").classes("section-title")
        ui.label("Built for Egyptian QC engineers and consultant offices.").classes(
            "section-sub")
        with ui.element('div').classes("feature-grid"):
            _feature("01", "AI defect detection",
                     "Take a site photo. AI proposes real defects — not a "
                     "paragraph, a checklist you tick.")
            _feature("02", "MS + ECP citations",
                     "Every defect cites the clause from your Method Statement "
                     "and the matching ECP 203 code. Never invents a match.")
            _feature("03", "Signed notice PDF",
                     "One tap generates a Notice to Subcontractor with photos, "
                     "citations, deadline, QR verification, and signature block.")
            _feature("04", "Register + closure",
                     "Every notice is logged. Filter by subcontractor, export "
                     "to Excel, generate a closure report at handover.")
            _feature("05", "Per-sub scorecard",
                     "Open, overdue, and closed defects per subcontractor. "
                     "Download a performance PDF for any sub in one tap.")
            _feature("06", "Photo or no photo",
                     "Snap it now, or raise a text-only defect from something "
                     "you saw earlier. Same workflow, same register.")

    # How
    with ui.element('div').classes("section").props('id="how"'):
        ui.label("How it works").classes("section-title")
        ui.label("Three steps, one workflow.").classes("section-sub")
        with ui.element('div').classes("steps"):
            _step("01", "Upload your MS",
                  "Drop in a Method Statement once. The tool extracts the "
                  "clause structure and stores it as your citation library.")
            _feature_placeholder()

    with ui.element('div').classes("section"):
        with ui.element('div').classes("steps"):
            _step("02", "Snap the defect",
                  "Open the app on your phone. Take a photo. AI suggests "
                  "3-6 candidate defects with MS + ECP citations.")
            _step("03", "Tick and send",
                  "Untick the false positives. Add any AI missed. Generate "
                  "the PDF. Send to the subcontractor. Logged forever.")

    # CTA
    with ui.element('div').classes("cta"):
        ui.html('<h2>Try it on one project this week.</h2>')
        ui.html('<p>Free forever for one project. No card required.</p>')
        ui.button("Create account", on_click=lambda: ui.navigate.to("/signup")
                  ).classes("btn-primary").style("min-height:44px;"
                                                   "padding:0 28px;"
                                                   "font-size:13px;")

    # Footer
    with ui.element('div').classes("footer"):
        ui.html('Built in Egypt · <a href="/pricing">Pricing</a> · '
                '<a href="/login">Sign in</a> · '
                '© 2026 Defect Notices')


def _feature(num, title, body):
    with ui.element('div').classes("feature"):
        ui.label(num).classes("num")
        ui.html("<h3>" + title + "</h3>")
        ui.html("<p>" + body + "</p>")


def _step(num, title, body):
    with ui.element('div').classes("step"):
        ui.label(num).classes("step-num")
        ui.html("<h3>" + title + "</h3>")
        ui.html("<p>" + body + "</p>")


def _feature_placeholder():
    pass
