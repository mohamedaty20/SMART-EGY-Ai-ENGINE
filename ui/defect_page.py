"""
ui/defect_page.py
The entire defect tool UI. Four tabs.
"""

import io
from nicegui import ui

from services import defect_db as db
from services import defect_service as svc
from services.ai_service import call_gemini_json


ELEMENT_TYPES = ["column", "beam", "slab", "wall", "foundation", "finishing"]
DISCIPLINES = ["Structural", "Architectural", "MEP"]
ZONES = ["A", "B", "C", "D", "General"]

# -------- Shared inline styles (so text never disappears) --------
S_TITLE  = "font-size:15px;font-weight:600;color:#0f172a;margin:0 0 4px 0;"
S_SUB    = "font-size:13px;color:#64748b;margin:0 0 14px 0;line-height:1.5;"
S_LABEL  = "font-size:13px;color:#0f172a;font-weight:500;"
S_BODY   = "font-size:13px;color:#0f172a;"
S_MUTED  = "font-size:12px;color:#64748b;"
S_ITAL   = "font-size:12px;color:#64748b;font-style:italic;"
S_NAME   = "font-size:14px;font-weight:600;color:#0f172a;line-height:1.4;"

BTN_PRIMARY = "background:#2563eb;color:#ffffff;"
BTN_SUCCESS = "background:#059669;color:#ffffff;"
BTN_NEUTRAL = "background:#475569;color:#ffffff;"
BTN_SOFT    = "background:#e2e8f0;color:#0f172a;"


def build_defect_ui():
    state = {
        "project": db.get_project(),
        "photo_bytes": None,
        "photo_mime": None,
        "ai_candidates": [],
        "selected_flags": [],
    }

    with ui.tabs().classes("w-full") as tabs:
        t_setup = ui.tab("1 · Setup", icon="settings")
        t_ms = ui.tab("2 · Method Statements", icon="library_books")
        t_new = ui.tab("3 · New Defect", icon="add_a_photo")
        t_reg = ui.tab("4 · Register", icon="list_alt")

    default = t_new if state["project"] else t_setup
    tabs.value = default

    with ui.tab_panels(tabs, value=default).classes("w-full bg-transparent"):
        with ui.tab_panel(t_setup):
            _build_setup(state, tabs, t_new)
        with ui.tab_panel(t_ms):
            _build_ms(state)
        with ui.tab_panel(t_new):
            _build_new_defect(state)
        with ui.tab_panel(t_reg):
            _build_register(state)


def _card():
    return ui.column().style(
        "background:#ffffff;border:1px solid #e2e8f0;border-radius:14px;"
        "padding:24px;margin-bottom:16px;width:100%;gap:12px;"
    )


# =====================================================================
# SCREEN 1 — SETUP
# =====================================================================
def _build_setup(state, tabs, next_tab):
    with _card():
        ui.label("Project Setup").style(S_TITLE)
        ui.label("Fill once. Saved for every future defect notice.").style(S_SUB)

        proj = state["project"] or {}
        name_in = ui.input("Project Name",
                            value=proj.get("name", "")).style("width:100%;")
        contractor_in = ui.input("Contractor",
                                  value=proj.get("contractor", "")).style("width:100%;")
        consultant_in = ui.input("Consultant",
                                  value=proj.get("consultant", "")).style("width:100%;")
        location_in = ui.input("Location",
                                value=proj.get("location", "")).style("width:100%;")
        engineer_in = ui.input("QC Engineer Name",
                                value=proj.get("engineer_name", "")).style("width:100%;")

        logo_holder = {"bytes": proj.get("logo_bytes")}
        logo_status = ui.label(
            "Logo: " + ("loaded" if logo_holder["bytes"] else "not uploaded")
        ).style(S_MUTED)

        async def handle_logo(e):
            logo_holder["bytes"] = await e.file.read()
            logo_status.set_text(f"Logo loaded: {e.file.name}")

        ui.upload(on_upload=handle_logo, auto_upload=True).style(
            "width:100%;"
        ).props("flat bordered label='Upload Company Logo (PNG/JPG)'")

        def save():
            if not name_in.value.strip():
                ui.notify("Project name is required.", type="warning")
                return
            db.save_project(
                name=name_in.value.strip(),
                contractor=contractor_in.value.strip(),
                consultant=consultant_in.value.strip(),
                location=location_in.value.strip(),
                engineer_name=engineer_in.value.strip(),
                logo_bytes=logo_holder["bytes"],
            )
            state["project"] = db.get_project()
            ui.notify("Project saved.", type="positive")
            tabs.value = next_tab

        ui.button("Save Project", on_click=save).style(BTN_PRIMARY)


# =====================================================================
# SCREEN 2 — METHOD STATEMENTS
# =====================================================================
def _build_ms(state):
    with _card():
        ui.label("Method Statements").style(S_TITLE)
        ui.label(
            "Upload an MS PDF. The tool extracts clauses once, "
            "then cites them in every defect report."
        ).style(S_SUB)

        pdf_holder = {"bytes": None}
        pdf_status = ui.label("PDF: not uploaded").style(S_MUTED)

        async def handle_pdf(e):
            pdf_holder["bytes"] = await e.file.read()
            pdf_status.set_text(
                f"PDF loaded: {e.file.name} "
                f"({len(pdf_holder['bytes'])//1024} KB)"
            )

        ui.upload(on_upload=handle_pdf, auto_upload=True).style(
            "width:100%;"
        ).props("flat bordered accept=.pdf label='Upload MS PDF'")

        with ui.row().style("width:100%;gap:12px;"):
            ms_num_in = ui.input("MS Number", value="MS-01").style("flex:1;")
            title_in = ui.input("Title", value="Reinforcement").style("flex:1;")
        with ui.row().style("width:100%;gap:12px;"):
            element_in = ui.select(ELEMENT_TYPES, value="column",
                                    label="Element Type").style("flex:1;")
            disc_in = ui.select(DISCIPLINES, value="Structural",
                                 label="Discipline").style("flex:1;")

        clause_preview = ui.column().style("width:100%;")

        async def extract():
            if not pdf_holder["bytes"]:
                ui.notify("Upload the MS PDF first.", type="warning")
                return
            clause_preview.clear()
            with clause_preview:
                with ui.row().style("gap:12px;align-items:center;padding:8px 0;"):
                    ui.spinner("dots", size="md", color="primary")
                    ui.label("Extracting clauses via AI...").style(S_BODY)

            result = await svc.extract_clauses_from_pdf(
                pdf_holder["bytes"], call_gemini_json
            )
            clause_preview.clear()

            if result.get("error"):
                with clause_preview:
                    ui.label(f"Error: {result['error']}").style(
                        "color:#dc2626;font-size:13px;"
                    )
                return

            clauses = result["clauses"]
            state["pending_clauses"] = clauses

            with clause_preview:
                ui.label(
                    f"Extracted {len(clauses)} clauses — confirm to save:"
                ).style(S_TITLE)
                for cl in clauses:
                    with ui.element('div').style(
                        "background:#f8fafc;border:1px solid #e2e8f0;"
                        "border-radius:8px;padding:10px 12px;margin-bottom:6px;"
                    ):
                        ui.label(f"§{cl['id']} — {cl['title']}").style(S_NAME)
                        ui.label(cl["text"][:180]).style(S_MUTED)

                def confirm_save():
                    if not state.get("project"):
                        ui.notify("Complete Setup first.", type="warning")
                        return
                    db.save_ms(
                        project_id=state["project"]["id"],
                        ms_number=ms_num_in.value.strip(),
                        title=title_in.value.strip(),
                        element_type=element_in.value,
                        discipline=disc_in.value,
                        pdf_bytes=pdf_holder["bytes"],
                        clauses=clauses,
                    )
                    ui.notify("MS saved to library.", type="positive")
                    clause_preview.clear()
                    _refresh_ms_list(state)

                ui.button("Confirm & Save MS", on_click=confirm_save).style(
                    BTN_SUCCESS
                )

        ui.button("Extract Clauses via AI", on_click=extract).style(BTN_PRIMARY)

        ui.separator()
        ui.label("Saved Method Statements").style(S_TITLE)
        state["ms_list_container"] = ui.column().style("width:100%;")
        _refresh_ms_list(state)


def _refresh_ms_list(state):
    container = state.get("ms_list_container")
    if not container:
        return
    container.clear()
    if not state.get("project"):
        with container:
            ui.label("No project set up yet.").style(S_MUTED)
        return
    ms_list = db.list_ms(state["project"]["id"])
    with container:
        if not ms_list:
            ui.label("No method statements yet.").style(S_MUTED)
            return
        for m in ms_list:
            with ui.element('div').style(
                "background:#f8fafc;border:1px solid #e2e8f0;"
                "border-radius:8px;padding:10px 12px;margin-bottom:6px;"
            ):
                ui.label(f"{m['ms_number']} — {m['title']}").style(S_NAME)
                ui.label(
                    f"{m['element_type']} · {m['discipline']} · "
                    f"{len(m['clauses'])} clauses"
                ).style(S_MUTED)


# =====================================================================
# SCREEN 3 — NEW DEFECT
# =====================================================================
def _build_new_defect(state):
    with _card():
        ui.label("New Defect").style(S_TITLE)
        ui.label(
            "Take a photo, add a note, let AI propose the defects, "
            "then tick the ones that are real."
        ).style(S_SUB)

        photo_holder = {"bytes": None, "mime": None}
        photo_status = ui.label("Photo: not uploaded").style(S_MUTED)

        async def handle_photo(e):
            data = await e.file.read()
            photo_holder["bytes"] = data
            photo_holder["mime"] = (
                "image/jpeg"
                if e.file.name.lower().endswith((".jpg", ".jpeg"))
                else "image/png"
            )
            state["photo_bytes"] = data
            state["photo_mime"] = photo_holder["mime"]
            photo_status.set_text(f"Photo: {e.file.name}")

        ui.upload(on_upload=handle_photo, auto_upload=True).style(
            "width:100%;"
        ).props("flat bordered accept=image/* label='Upload site photo'")

        note_in = ui.textarea(
            label="Note (optional)",
            placeholder="e.g. crack at column C3 base"
        ).style("width:100%;")

        with ui.row().style("width:100%;gap:12px;"):
            zone_in = ui.select(ZONES, value="A",
                                 label="Zone").style("flex:1;")
            element_in = ui.select(ELEMENT_TYPES, value="column",
                                    label="Element").style("flex:1;")

        candidates_container = ui.column().style("width:100%;margin-top:16px;")

        async def analyze():
            if not photo_holder["bytes"]:
                ui.notify("Upload a photo first.", type="warning")
                return
            if not state.get("project"):
                ui.notify("Complete Setup first.", type="warning")
                return

            ms_clauses = db.get_clauses_for_element(
                state["project"]["id"], element_in.value
            )
            candidates_container.clear()
            with candidates_container:
                with ui.row().style("gap:12px;align-items:center;padding:8px 0;"):
                    ui.spinner("dots", size="md", color="primary")
                    ui.label(
                        f"Analyzing photo... {len(ms_clauses)} MS clauses loaded."
                    ).style(S_BODY)

            result = await svc.analyze_defect_photo(
                photo_bytes=photo_holder["bytes"],
                mime_type=photo_holder["mime"],
                note=note_in.value or "",
                ms_clauses=ms_clauses,
                element_type=element_in.value,
                call_gemini_json_fn=call_gemini_json,
            )
            candidates_container.clear()

            if result.get("error"):
                with candidates_container:
                    ui.label(f"Error: {result['error']}").style(
                        "color:#dc2626;font-size:13px;"
                    )
                return

            candidates = result["defects"]
            state["ai_candidates"] = candidates
            state["selected_flags"] = [True] * len(candidates)

            with candidates_container:
                if not candidates:
                    ui.label(
                        "AI found no defects in this photo."
                    ).style(S_MUTED)
                else:
                    ui.label(
                        f"AI found {len(candidates)} candidate(s). "
                        f"Tick the ones that apply:"
                    ).style(S_TITLE)

                    for i, c in enumerate(candidates):
                        with ui.element('div').style(
                            "background:#FEF08A;border:2px solid #000000;"
                            "border-radius:10px;padding:14px;"
                            "margin-bottom:12px;width:100%;display:block;"
                        ):
                            with ui.row().style(
                                "width:100%;display:flex;"
                                "align-items:flex-start;gap:12px;"
                            ):
                                cb = ui.checkbox(value=True)
                                cb.bind_value(state["selected_flags"], i)
                                with ui.element('div').style(
                                    "flex:1;display:block;min-width:0;"
                                ):
                                    ui.label("NAME: " + str(c.get("name", ""))).style(
                                        "color:#000000 !important;font-size:16px;"
                                        "font-weight:700;display:block;"
                                    )
                                    ui.label("LOCATION: " + str(c.get("location_hint", ""))).style(
                                        "color:#000000 !important;font-size:13px;"
                                        "display:block;margin-top:4px;"
                                    )
                                    ui.label("MS: " + ", ".join(c.get("ms_violations", []))).style(
                                        "color:#000000 !important;font-size:13px;"
                                        "display:block;margin-top:4px;"
                                    )
                                    ui.label("CODE: " + ", ".join(c.get("code_violations", []))).style(
                                        "color:#000000 !important;font-size:13px;"
                                        "display:block;margin-top:4px;"
                                    )
                                    ui.label("REPAIR: " + str(c.get("repair_action", ""))).style(
                                        "color:#000000 !important;font-size:13px;"
                                        "display:block;margin-top:4px;"
                                    )
                                    ui.label("SEVERITY: " + str(c.get("severity", ""))).style(
                                        "color:#000000 !important;font-size:13px;"
                                        "display:block;margin-top:4px;font-weight:700;"
                                    )

                # ---- Notice details ----
                ui.separator().style("margin:20px 0;")

                ui.label("Notice details").style(S_TITLE)
                ui.label("Who gets the notice, and by when.").style(S_SUB)

                sub_in = ui.input(
                    "Send to Subcontractor",
                    placeholder="e.g. Al-Ahram Steel Fixing"
                ).style("width:100%;")

                with ui.row().style("width:100%;gap:12px;"):
                    deadline_in = ui.select(
                        [1, 2, 3, 5, 7, 14], value=3,
                        label="Deadline (days)"
                    ).style("flex:1;")
                    raise_in = ui.select(
                        {"qc_internal": "QC Internal",
                         "consultant": "Consultant / NCR"},
                        value="qc_internal",
                        label="Raised as"
                    ).style("flex:1;")

                def generate():
                    selected = [
                        c for i, c in enumerate(candidates)
                        if state["selected_flags"][i]
                    ]
                    if not selected:
                        ui.notify("Tick at least one defect.", type="warning")
                        return
                    if not sub_in.value.strip():
                        ui.notify("Enter the subcontractor name.", type="warning")
                        return

                    notice_uid = svc.generate_uid("NTC")
                    for s in selected:
                        s["zone"] = zone_in.value

                    pdf_bytes = svc.build_notice_pdf(
                        project=state["project"],
                        defects=selected,
                        notice_uid=notice_uid,
                        subcontractor=sub_in.value.strip(),
                        deadline_days=int(deadline_in.value),
                        raise_type=raise_in.value,
                        logo_bytes=state["project"].get("logo_bytes"),
                    )

                    db.save_defect(
                        project_id=state["project"]["id"],
                        uid=notice_uid,
                        zone=zone_in.value,
                        subcontractor=sub_in.value.strip(),
                        deadline_days=int(deadline_in.value),
                        raise_type=raise_in.value,
                        photo_bytes=photo_holder["bytes"],
                        note=note_in.value or "",
                        selected=selected,
                        notice_pdf=pdf_bytes,
                    )
                    ui.notify(f"Notice {notice_uid} saved.", type="positive")
                    ui.download(pdf_bytes, filename=f"{notice_uid}.pdf")

                ui.button("Generate Notice PDF", on_click=generate).style(
                    BTN_SUCCESS + "margin-top:12px;"
                )

        ui.button("Analyze with AI", on_click=analyze).style(
            BTN_PRIMARY + "margin-top:12px;"
        )


# =====================================================================
# SCREEN 4 — REGISTER
# =====================================================================
def _build_register(state):
    with _card():
        ui.label("Defect Register").style(S_TITLE)
        ui.label(
            "Every notice you have issued. Click a row to see full detail."
        ).style(S_SUB)

        table_container = ui.column().style("width:100%;")

        def refresh():
            table_container.clear()
            if not state.get("project"):
                with table_container:
                    ui.label("No project set up yet.").style(S_MUTED)
                return
            rows = db.list_defects(state["project"]["id"])
            with table_container:
                if not rows:
                    ui.label("No defects yet.").style(S_MUTED)
                    return

                open_count = sum(1 for r in rows if r["status"] == "open")
                ui.label(
                    f"Total: {len(rows)}  ·  Open: {open_count}  ·  "
                    f"Closed: {len(rows) - open_count}"
                ).style(S_TITLE)

                table = ui.table(
                    columns=[
                        {"name": "uid", "label": "UID",
                         "field": "uid", "align": "left"},
                        {"name": "zone", "label": "Zone", "field": "zone"},
                        {"name": "sub", "label": "Subcontractor",
                         "field": "subcontractor", "align": "left"},
                        {"name": "count", "label": "#", "field": "count"},
                        {"name": "status", "label": "Status",
                         "field": "status"},
                        {"name": "created", "label": "Created",
                         "field": "created_at"},
                    ],
                    rows=rows,
                    row_key="id",
                ).style("width:100%;").props("flat bordered")

                def on_row_click(e):
                    row = e.args[1]
                    defect_id = row.get("id")
                    if defect_id:
                        _show_defect_dialog(defect_id, refresh)

                table.on("rowClick", on_row_click)

        ui.button("Refresh", on_click=refresh).style(BTN_NEUTRAL)
        refresh()


def _show_defect_dialog(defect_id, on_close_cb):
    d = db.get_defect(defect_id)
    if not d:
        ui.notify("Defect not found.", type="negative")
        return

    with ui.dialog() as dialog, ui.card().style(
        "background:#ffffff;padding:24px;max-width:880px;width:100%;"
    ):
        ui.label(f"Notice {d['uid']}").style(
            "font-size:18px;font-weight:700;color:#0f172a;"
        )
        ui.label(
            f"Zone {d['zone']} · {d['subcontractor']} · {d['status'].upper()}"
        ).style(S_MUTED)

        ui.separator()

        with ui.row().style("gap:20px;align-items:flex-start;width:100%;"):
            if d["photo_bytes"]:
                ui.image(io.BytesIO(d["photo_bytes"])).style(
                    "width:280px;border-radius:10px;border:1px solid #e2e8f0;"
                )
            with ui.column().style("flex:1;gap:6px;"):
                ui.label(f"Note: {d['note'] or '(none)'}").style(S_MUTED)
                for i, s in enumerate(d["selected"], 1):
                    with ui.element('div').style(
                        "background:#f8fafc;border:1px solid #e2e8f0;"
                        "border-radius:8px;padding:10px 12px;margin-bottom:6px;"
                    ):
                        ui.label(f"{i}. {s.get('name','')}").style(S_NAME)
                        cit = []
                        if s.get("ms_violations"):
                            cit.append("MS: " + ", ".join(s["ms_violations"]))
                        if s.get("code_violations"):
                            cit.append("Code: " + ", ".join(s["code_violations"]))
                        if cit:
                            ui.label(" | ".join(cit)).style(S_ITAL)

        ui.separator()

        with ui.row().style("gap:8px;margin-top:8px;"):
            if d.get("notice_pdf"):
                ui.button(
                    "Download PDF",
                    on_click=lambda: ui.download(
                        d["notice_pdf"], filename=f"{d['uid']}.pdf"
                    )
                ).style(BTN_PRIMARY)

            if d["status"] == "open":
                def do_close():
                    db.close_defect(defect_id)
                    ui.notify("Defect marked closed.", type="positive")
                    dialog.close()
                    on_close_cb()

                ui.button("Mark Closed", on_click=do_close).style(BTN_SUCCESS)

            ui.button("Close", on_click=dialog.close).style(BTN_SOFT)

    dialog.open()
