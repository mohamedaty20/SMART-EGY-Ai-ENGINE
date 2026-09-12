"""
ui/defect_page.py — DIAGNOSTIC VERSION
"""
import io
from nicegui import ui

from services import defect_db as db
from services import defect_service as svc
from services.ai_service import call_gemini_json


ELEMENT_TYPES = ["column", "beam", "slab", "wall", "foundation", "finishing"]
ZONES = ["A", "B", "C", "D", "General"]


def build_defect_ui():
    state = {
        "project": db.get_project(),
        "photo_bytes": None,
        "photo_mime": None,
        "selected_flags": [],
    }

    with ui.column().style("width:100%;max-width:900px;margin:auto;padding:20px;gap:16px;"):

        # ---------- SETUP ----------
        ui.label("STEP 1 — PROJECT SETUP").style(
            "font-size:18px;font-weight:700;color:#000;background:#FFFF00;"
            "padding:8px 12px;display:block;"
        )
        proj = state["project"] or {}
        name_in = ui.input("Project Name", value=proj.get("name", ""))
        ui.button("Save Project", on_click=lambda: (
            db.save_project(
                name=name_in.value or "Test",
                contractor="", consultant="", location="",
                engineer_name="", logo_bytes=None,
            ),
            state.update({"project": db.get_project()}),
            ui.notify("Saved", type="positive"),
        )).style("background:#2563eb;color:#fff;")

        ui.separator()

        # ---------- NEW DEFECT ----------
        ui.label("STEP 2 — NEW DEFECT").style(
            "font-size:18px;font-weight:700;color:#000;background:#FFFF00;"
            "padding:8px 12px;display:block;"
        )

        photo_holder = {"bytes": None, "mime": None}

        async def handle_photo(e):
            data = await e.file.read()
            photo_holder["bytes"] = data
            photo_holder["mime"] = ("image/jpeg"
                if e.file.name.lower().endswith((".jpg", ".jpeg"))
                else "image/png")
            photo_status.set_text("Photo loaded: " + e.file.name)

        ui.upload(on_upload=handle_photo, auto_upload=True).props(
            "flat bordered accept=image/* label='Upload photo'"
        )
        photo_status = ui.label("No photo").style("color:#000;")

        note_in = ui.textarea(label="Note").style("width:100%;")
        element_in = ui.select(ELEMENT_TYPES, value="column", label="Element")

        # ---------- OUTPUT BOX ----------
        output = ui.column().style(
            "width:100%;background:#FFFFFF;border:3px solid #000000;"
            "padding:16px;margin-top:12px;min-height:100px;"
        )

        async def analyze():
            output.clear()

            if not photo_holder["bytes"]:
                with output:
                    ui.label("NO PHOTO UPLOADED").style(
                        "color:#FF0000;font-size:20px;font-weight:700;"
                    )
                return
            if not state.get("project"):
                with output:
                    ui.label("NO PROJECT").style(
                        "color:#FF0000;font-size:20px;font-weight:700;"
                    )
                return

            with output:
                ui.label("Calling AI...").style(
                    "color:#000;font-size:14px;"
                )

            ms_clauses = db.get_clauses_for_element(
                state["project"]["id"], element_in.value
            )
            result = await svc.analyze_defect_photo(
                photo_bytes=photo_holder["bytes"],
                mime_type=photo_holder["mime"],
                note=note_in.value or "",
                ms_clauses=ms_clauses,
                element_type=element_in.value,
                call_gemini_json_fn=call_gemini_json,
            )
            output.clear()

            with output:
                if result.get("error"):
                    ui.label("ERROR: " + str(result["error"])).style(
                        "color:#FF0000;font-size:16px;font-weight:700;"
                    )
                    return

                candidates = result.get("defects", [])

                # HEADER — huge, red, unmissable
                ui.label(f"CANDIDATES: {len(candidates)}").style(
                    "color:#FFFFFF;background:#DC2626;font-size:20px;"
                    "font-weight:700;padding:8px 12px;display:block;"
                    "width:100%;"
                )

                if not candidates:
                    ui.label("Empty list").style("color:#000;font-size:16px;")
                    return

                # DUMP THE FIRST CANDIDATE AS PLAIN TEXT
                first = candidates[0]
                ui.label("FIRST CANDIDATE RAW DATA:").style(
                    "color:#000;font-weight:700;font-size:14px;margin-top:12px;"
                )
                ui.label(str(first)).style(
                    "color:#000;font-size:13px;background:#F3F4F6;"
                    "padding:12px;display:block;width:100%;"
                    "word-wrap:break-word;font-family:monospace;"
                )

                # Now render each candidate one at a time
                for i, c in enumerate(candidates):
                    ui.label(f"--- Candidate {i+1} ---").style(
                        "color:#000;font-weight:700;font-size:15px;"
                        "margin-top:16px;"
                    )
                    ui.label("Name: " + str(c.get("name", "?"))).style(
                        "color:#000;font-size:14px;"
                    )
                    ui.label("Severity: " + str(c.get("severity", "?"))).style(
                        "color:#000;font-size:14px;"
                    )
                    ui.label("Location: " + str(c.get("location_hint", "-"))).style(
                        "color:#000;font-size:14px;"
                    )
                    ui.label("MS: " + str(c.get("ms_violations", []))).style(
                        "color:#000;font-size:14px;"
                    )
                    ui.label("Code: " + str(c.get("code_violations", []))).style(
                        "color:#000;font-size:14px;"
                    )
                    ui.label("Repair: " + str(c.get("repair_action", "-"))).style(
                        "color:#000;font-size:14px;"
                    )

        ui.button("ANALYZE", on_click=analyze).style(
            "background:#2563eb;color:#fff;font-size:16px;font-weight:700;"
            "padding:12px 24px;"
        )
