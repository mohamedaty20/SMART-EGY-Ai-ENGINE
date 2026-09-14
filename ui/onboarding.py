"""
ui/onboarding.py — First-login walkthrough.
"""
from nicegui import ui

from services import billing_db as bdb
from ui.pwa import inject_pwa


STEPS = [
    ("01", "Welcome",
     "This app helps you issue defect notices to subcontractors. "
     "Three tabs at the top: New Defect, Defect Logs, Subs, Dashboard. "
     "The menu on the left holds your project info."),
    ("02", "Set up the project",
     "Open the menu (top-left) → Edit. Fill in project name, contractor, "
     "consultant, and QC engineer name. Add your company logo if you have one."),
    ("03", "Upload a Method Statement",
     "In the same menu, tap the + next to Method Statements. Drop in a PDF, "
     "DOCX, or TXT. The tool extracts clause numbers once and reuses them "
     "in every defect notice you issue."),
    ("04", "Raise a defect",
     "Open New Defect. Take a photo — AI suggests 3-6 candidate defects with "
     "MS + ECP citations. Tick the real ones, untick false positives, add "
     "anything AI missed, then generate the Notice PDF."),
    ("05", "Track and close",
     "Every notice is logged. Filter by subcontractor, export to Excel, "
     "attach closure photos when defects are fixed. Open Dashboard to see "
     "open/overdue counts at a glance."),
]


def show_onboarding(user_id, on_done=None):
    """Open the onboarding dialog. Call mark_onboarded when finished."""
    state = {"step": 0}

    with ui.dialog() as dlg, ui.card().style(
        "background:#141414;border:1px solid #262626;padding:28px;"
        "min-width:380px;max-width:95vw;width:520px;border-radius:8px;"
        "color:#e8e8e8;font-family:'JetBrains Mono',monospace;"
    ):
        content = ui.element('div').style("width:100%;")

        def render():
            content.clear()
            with content:
                num, title, body = STEPS[state["step"]]
                ui.label("STEP " + num + " OF " + str(len(STEPS)).zfill(2)
                          ).style("font-size:9px;font-weight:700;"
                                   "letter-spacing:0.14em;color:#5eead4;"
                                   "margin-bottom:8px;")
                ui.label(title).style(
                    "font-size:18px;font-weight:700;letter-spacing:-0.02em;"
                    "color:#e8e8e8;margin-bottom:10px;")
                ui.label(body).style(
                    "font-size:12px;line-height:1.6;color:#b8b8b8;"
                    "margin-bottom:22px;white-space:pre-wrap;")

                with ui.element('div').style(
                    "display:flex;justify-content:space-between;"
                    "align-items:center;gap:8px;"
                ):
                    if state["step"] > 0:
                        def _back():
                            state["step"] -= 1
                            render()
                        ui.button("← Back", on_click=_back).props("flat").style(
                            "color:#808080;font-size:11px;")
                    else:
                        ui.label("").style("width:60px;")

                    def _next():
                        if state["step"] >= len(STEPS) - 1:
                            bdb.mark_onboarded(user_id)
                            dlg.close()
                            if on_done:
                                on_done()
                            return
                        state["step"] += 1
                        render()

                    label = ("Finish" if state["step"] >= len(STEPS) - 1
                             else "Next →")
                    ui.button(label, on_click=_next).style(
                        "background:#5eead4;color:#0b0b0b;font-weight:700;"
                        "border-radius:3px;padding:0 20px;"
                        "min-height:38px;font-size:12px;"
                        "text-transform:none;")

                with ui.element('div').style("margin-top:14px;"
                                              "text-align:center;"):
                    def _skip():
                        bdb.mark_onboarded(user_id)
                        dlg.close()
                        if on_done:
                            on_done()
                    ui.button("Skip tour", on_click=_skip).props(
                        "flat").style("color:#5a5a5a;font-size:10px;")

        render()

    dlg.open()
