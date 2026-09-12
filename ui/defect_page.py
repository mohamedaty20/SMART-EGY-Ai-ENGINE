"""
ui/defect_page.py

The entire defect tool UI. Four tabs:
  1. Setup          — one-time project information
  2. Method Statements — upload PDFs, review extracted clauses
  3. New Defect     — photo + note → AI candidates → notice PDF
  4. Register       — all defects, close actions
"""

import io
from nicegui import ui, run

from services import defect_db as db
from services import defect_service as svc
from services.ai_service import call_gemini_json


ELEMENT_TYPES = ["column", "beam", "slab", "wall", "foundation", "finishing"]
DISCIPLINES = ["Structural", "Architectural", "MEP"]
ZONES = ["A", "B", "C", "D", "General"]
SEVERITIES = ["Low", "Medium", "High", "Critical"]


def build_defect_ui():
    """Main entry — called from main.py inside @ui.page('/')."""
    state = {
        "project": db.get_project(),
        "photo_bytes": None,
        "photo_mime": None,
        "ai_candidates": [],
        "selected_flags": [],
    }

    with ui.tabs().classes("w-full text-blue-700") as tabs:
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


# =====================================================================
# SCREEN 1 — SETUP
# =====================================================================
def _build_setup(state, tabs, next_tab):
    with ui.column().classes("custom-card w-full gap-3"):
        ui.label("Project Setup").classes("text-lg font-semibold text-slate-800")
        ui.label(
            "Fill once. Saved for every future defect notice."
        ).classes("text-sm text-slate-500")

        proj = state["project"] or {}
        name_in = ui.input(
            "Project Name", value=proj.get("name", "")
        ).classes("w-full")
        contractor_in = ui.input(
            "Contractor", value=proj.get("contractor", "")
        ).classes("w-full")
        consultant_in = ui.input(
            "Consultant", value=proj.get("consultant", "")
        ).classes("w-full")
        location_in = ui.input(
            "Location", value=proj.get("location", "")
        ).classes("w-full")
        engineer_in = ui.input(
            "QC Engineer Name", value=proj.get("engineer_name", "")
        ).classes("w-full")

        logo_holder = {"bytes": proj.get("logo_bytes")}
        logo_status = ui.label(
            "Logo: " + ("loaded" if logo_holder["bytes"] else "not uploaded")
        ).classes("text-xs text-slate-500")

        async def handle_logo(e):
            logo_holder["bytes"] = await e.file.read()
            logo_status.set_text(f"Logo loaded: {e.file.name}")

        ui.upload(on_upload=handle_logo, auto_upload=True).classes(
            "w-full"
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

        ui.button("Save Project", on_click=save).classes(
            "bg-blue-600 text-white mt-2"
        )


# =====================================================================
# SCREEN 2 — METHOD STATEMENTS
# =====================================================================
def _build_ms(state):
    with ui.column().classes("custom-card w-full gap-3"):
        ui.label("Method Statements").classes("text-lg font-semibold text-slate-800")
        ui.label(
            "Upload an MS PDF. The tool extracts clauses once, "
            "then cites them in every defect report."
        ).classes("text-sm text-slate-500")

        pdf_holder = {"bytes": None}

        async def handle_pdf(e):
            pdf_holder["bytes"] = await e.file.read()
            pdf_status.set_text(f"PDF loaded: {e.file.name} ({len(pdf_holder['bytes'])//1024} KB)")

        pdf_status = ui.label("PDF: not uploaded").classes("text-xs text-slate-500")
        ui.upload(on_upload=handle_pdf, auto_upload=True).classes(
            "w-full"
        ).props("flat bordered accept=.pdf label='Upload MS PDF'")

        with ui.row().classes("w-full gap-3"):
            ms_num_in = ui.input("MS Number", value="MS-01").classes("flex-1")
            title_in = ui.input("Title", value="Reinforcement").classes("flex-1")
        with ui.row().classes("w-full gap-3"):
            element_in = ui.select(ELEMENT_TYPES, value="column",
                                    label="Element Type").classes("flex-1")
            disc_in = ui.select(DISCIPLINES, value="Structural",
                                 label="Discipline").classes("flex-1")

        clause_preview = ui.column().classes("w-full")

        async def extract():
            if not pdf_holder["bytes"]:
                ui.notify("Upload the MS PDF first.", type="warning")
                return
            clause_preview.clear()
            with clause_preview:
                ui.spinner("ios", size="lg")
                ui.label("Extracting clauses via AI...").classes("text-sm")
            result = await svc.extract_clauses_from_pdf(
                pdf_holder["bytes"], call_gemini_json
            )
            clause_preview.clear()
            if result.get("error"):
                with clause_preview:
                    ui.label(f"Error: {result['error']}").classes(
                        "text-red-600 text-sm"
                    )
                return

            clauses = result["clauses"]
            state["pending_clauses"] = clauses
            with clause_preview:
                ui.label(f"Extracted {len(clauses)} clauses — confirm to save:").classes(
                    "text-sm font-semibold text-slate-700 mt-2"
                )
                for cl in clauses:
                    ui.label(
                        f"§{cl['id']} — {cl['title']}: {cl['text'][:100]}"
                    ).classes("text-xs text-slate-600")

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

                ui.button("Confirm & Save MS", on_click=confirm_save).classes(
                    "bg-emerald-600 text-white mt-2"
                )

        ui.button("Extract Clauses via AI", on_click=extract).classes(
            "bg-blue-600 text-white"
        )

        # ---- Existing MSs ----
        ui.separator()
        ui.label("Saved Method Statements").classes("font-semibold text-slate-700 mt-2")
        state["ms_list_container"] = ui.column().classes("w-full")
        _refresh_ms_list(state)


def _refresh_ms_list(state):
    container = state.get("ms_list_container")
    if not container:
        return
    container.clear()
    if not state.get("project"):
        with container:
            ui.label("No project set up yet.").classes("text-xs text-slate-500")
        return
    ms_list = db.list_ms(state["project"]["id"])
    with container:
        if not ms_list:
            ui.label("No method statements yet.").classes("text-xs text-slate-500")
            return
        for m in ms_list:
            with ui.row().classes("w-full gap-2 items-center py-1 border-b"):
                ui.label(f"{m['ms_number']} — {m['title']}").classes(
                    "font-medium text-slate-700 flex-1"
                )
                ui.label(f"{m['element_type']} · {m['discipline']}").classes(
                    "text-xs text-slate-500"
                )
                ui.label(f"{len(m['clauses'])} clauses").classes(
                    "text-xs bg-slate-100 px-2 py-0.5 rounded"
                )


# =====================================================================
# SCREEN 3 — NEW DEFECT
# =====================================================================
def _build_new_defect(state):
    with ui.column().classes("custom-card w-full gap-3"):
        ui.label("New Defect").classes("text-lg font-semibold text-slate-800")
        ui.label(
            "Take a photo, add a note, let AI propose the defects, "
            "then tick the ones that are real."
        ).classes("text-sm text-slate-500")

        # Photo upload
        photo_holder = {"bytes": None, "mime": None}
        photo_status = ui.label("Photo: not uploaded").classes(
            "text-xs text-slate-500"
        )

        async def handle_photo(e):
            data = await e.file.read()
            photo_holder["bytes"] = data
            photo_holder["mime"] = "image/jpeg" if e.file.name.lower().endswith(
                (".jpg", ".jpeg")
            ) else "image/png"
            state["photo_bytes"] = data
            state["photo_mime"] = photo_holder["mime"]
            photo_status.set_text(f"Photo: {e.file.name}")

        ui.upload(on_upload=handle_photo, auto_upload=True).classes(
            "w-full"
        ).props("flat bordered accept=image/* label='Upload site photo'")

        note_in = ui.textarea(
            label="Note (optional)",
            placeholder="e.g. crack at column C3 base"
        ).classes("w-full")

        with ui.row().classes("w-full gap-3"):
            zone_in = ui.select(ZONES, value="A", label="Zone").classes("flex-1")
            element_in = ui.select(ELEMENT_TYPES, value="column",
                                    label="Element").classes("flex-1")

        analyze_btn = ui.button("Analyze with AI").classes(
            "bg-blue-600 text-white"
        )

        # Candidate list container
        candidates_container = ui.column().classes("w-full")

        async def analyze():
            if not photo_holder["bytes"]:
                ui.notify("Upload a photo first.", type="warning")
                return
            if not state.get("project"):
                ui.notify("Complete Setup first.", type="warning")
                return
            # Load relevant clauses for this element
            ms_clauses = db.get_clauses_for_element(
                state["project"]["id"], element_in.value
            )
            candidates_container.clear()
            with candidates_container:
                ui.spinner("ios", size="lg")
                ui.label(
                    f"Analyzing photo… {len(ms_clauses)} MS clauses loaded."
                ).classes("text-sm")

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
                    ui.label(f"Error: {result['error']}").classes(
                        "text-red-600 text-sm"
                    )
                return

            candidates = result["defects"]
            state["ai_candidates"] = candidates
            state["selected_flags"] = [True] * len(candidates)

            with candidates_container:
                if not candidates:
                    ui.label(
                        "AI found no defects. "
                        "You can still add lines manually below."
                    ).classes("text-sm text-slate-500")
                else:
                    ui.label(
                        f"AI found {len(candidates)} candidate(s). "
                        "Tick the ones that apply:"
                    ).classes("text-sm font-semibold text-slate-700 mt-2")

                    for i, c in enumerate(candidates):
                        with ui.card().classes(
                            "w-full bg-slate-50 border border-slate-200"
                        ):
                            with ui.row().classes("items-start gap-2"):
                                cb = ui.checkbox(value=True)
                                cb.bind_value(state["selected_flags"], i)
                                with ui.column().classes("flex-1 gap-0"):
                                    ui.label(c["name"]).classes(
                                        "font-semibold text-slate-800"
                                    )
                                    cit = []
                                    if c["ms_violations"]:
                                        cit.append("MS: " + ", ".join(c["ms_violations"]))
                                    if c["code_violations"]:
                                        cit.append("Code: " + ", ".join(c["code_violations"]))
                                    if cit:
                                        ui.label(" | ".join(cit)).classes(
                                            "text-xs text-slate-600 italic"
                                        )
                                    if c["repair_action"]:
                                        ui.label(
                                            f"Repair: {c['repair_action']}"
                                        ).classes("text-xs text-slate-600")
                                    ui.label(
                                        f"Severity: {c['severity']}"
                                    ).classes("text-xs text-slate-500")

                # Subcontractor + deadline + generate
                ui.separator().classes("my-3")
                sub_in = ui.input(
                    "Send to Subcontractor",
                    value=""
                ).classes("w-full")
                with ui.row().classes("w-full gap-3"):
                    deadline_in = ui.select(
                        [1, 2, 3, 5, 7, 14], value=3, label="Deadline (days)"
                    ).classes("flex-1")
                    raise_in = ui.select(
                        {"qc_internal": "QC Internal",
                         "consultant": "Consultant / NCR"},
                        value="qc_internal",
                        label="Raised as"
                    ).classes("flex-1")

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
                    # Attach zone to each selected defect
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
                    candidates_container.clear()

                ui.button("Generate Notice PDF", on_click=generate).classes(
                    "bg-emerald-600 text-white mt-2"
                )

        analyze_btn.on("click", analyze)


# =====================================================================
# SCREEN 4 — REGISTER
# =====================================================================
def _build_register(state):
    with ui.column().classes("custom-card w-full gap-3"):
        ui.label("Defect Register").classes("text-lg font-semibold text-slate-800")
        ui.label(
            "Every notice you have issued. Click a row to see full detail."
        ).classes("text-sm text-slate-500")

        table_container = ui.column().classes("w-full")
        state["register_container"] = table_container

        def refresh():
            table_container.clear()
            if not state.get("project"):
                with table_container:
                    ui.label("No project set up yet.").classes("text-xs text-slate-500")
                return
            rows = db.list_defects(state["project"]["id"])
            with table_container:
                if not rows:
                    ui.label("No defects yet.").classes("text-xs text-slate-500")
                    return

                open_count = sum(1 for r in rows if r["status"] == "open")
                ui.label(
                    f"Total: {len(rows)}   ·   Open: {open_count}   ·   "
                    f"Closed: {len(rows) - open_count}"
                ).classes("text-sm font-semibold text-slate-700 mb-2")

                table = ui.table(
                    columns=[
                        {"name": "uid", "label": "UID", "field": "uid",
                         "align": "left"},
                        {"name": "zone", "label": "Zone", "field": "zone"},
                        {"name": "sub", "label": "Subcontractor",
                         "field": "subcontractor", "align": "left"},
                        {"name": "count", "label": "#", "field": "count"},
                        {"name": "status", "label": "Status", "field": "status"},
                        {"name": "created", "label": "Created",
                         "field": "created_at"},
                    ],
                    rows=rows,
                ).classes("w-full")

                def on_row_click(e):
                    row = e.args[1]
                    defect_id = row.get("id")
                    if defect_id:
                        _show_defect_dialog(defect_id, refresh)

                table.on("rowClick", on_row_click)

        ui.button("Refresh", on_click=refresh).classes("bg-slate-700 text-white")
        refresh()


def _show_defect_dialog(defect_id, on_close_cb):
    d = db.get_defect(defect_id)
    if not d:
        ui.notify("Defect not found.", type="negative")
        return

    with ui.dialog() as dialog, ui.card().classes("w-[800px] max-w-full"):
        ui.label(f"Notice {d['uid']}").classes("text-lg font-bold text-slate-800")
        ui.label(
            f"Zone {d['zone']} · {d['subcontractor']} · {d['status'].upper()}"
        ).classes("text-sm text-slate-600")
        ui.separator()

        with ui.row().classes("gap-4 items-start"):
            if d["photo_bytes"]:
                ui.image(io.BytesIO(d["photo_bytes"])).classes(
                    "w-64 rounded border"
                )
            with ui.column().classes("flex-1"):
                ui.label(f"Note: {d['note'] or '(none)'}").classes(
                    "text-xs text-slate-500"
                )
                for i, s in enumerate(d["selected"], 1):
                    ui.label(f"{i}. {s.get('name','')}").classes(
                        "text-sm font-medium text-slate-800 mt-1"
                    )
                    cit = []
                    if s.get("ms_violations"):
                        cit.append("MS: " + ", ".join(s["ms_violations"]))
                    if s.get("code_violations"):
                        cit.append("Code: " + ", ".join(s["code_violations"]))
                    if cit:
                        ui.label(" | ".join(cit)).classes(
                            "text-xs text-slate-600 italic"
                        )

        ui.separator()

        with ui.row().classes("gap-2 mt-2"):
            if d.get("notice_pdf"):
                ui.button(
                    "Download PDF",
                    on_click=lambda: ui.download(
                        d["notice_pdf"], filename=f"{d['uid']}.pdf"
                    )
                ).classes("bg-blue-600 text-white")

            if d["status"] == "open":
                def do_close():
                    db.close_defect(defect_id)
                    ui.notify("Defect marked closed.", type="positive")
                    dialog.close()
                    on_close_cb()

                ui.button("Mark Closed", on_click=do_close).classes(
                    "bg-emerald-600 text-white"
                )

            ui.button("Close", on_click=dialog.close).classes(
                "bg-slate-400 text-white"
            )

    dialog.open()
