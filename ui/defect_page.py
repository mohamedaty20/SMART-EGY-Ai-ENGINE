"""
ui/defect_page.py — Full file.
Supports PDF / DOCX / TXT + manual defect add/remove + EN/AR toggle.
"""
import io
from nicegui import ui

from services import defect_db as db
from services import defect_service as svc
from services.ai_service import call_gemini_json


# =====================================================================
# LANGUAGE STATE (per-process demo; swap to app.storage for multi-user)
# =====================================================================
LANG = {"code": "en"}


T = {
    "en": {
        "app_title": "Defect Notices",
        "lang_button": "العربية",
        "tab_setup": "Setup",
        "tab_ms": "Method Statements",
        "tab_new": "New Defect",
        "tab_register": "Register",

        "setup_title": "Project Setup",
        "setup_sub": "Fill once. Saved for every future defect notice.",
        "project_name": "Project Name",
        "contractor": "Contractor",
        "consultant": "Consultant",
        "location": "Location",
        "engineer_name": "QC Engineer Name",
        "upload_logo": "Upload Company Logo (PNG/JPG)",
        "logo_loaded": "Logo loaded: ",
        "logo_loaded_flag": "loaded",
        "logo_missing_flag": "not uploaded",
        "logo_label": "Logo: ",
        "save_project": "Save Project",
        "project_saved": "Project saved.",
        "project_name_required": "Project name is required.",

        "ms_title": "Method Statements",
        "ms_sub": "Upload an MS as PDF, DOCX, or TXT. The tool extracts "
                  "clauses once, then cites them in every defect report.",
        "ms_file_label": "File: not uploaded",
        "ms_file_loaded": "File loaded: ",
        "ms_upload": "Upload MS (PDF / DOCX / TXT)",
        "ms_number": "MS Number",
        "ms_doc_title": "Title",
        "element_type": "Element Type",
        "discipline": "Discipline",
        "extract_clauses": "Extract Clauses via AI",
        "extracting": "Extracting clauses via AI...",
        "extracted_prefix": "Extracted ",
        "extracted_suffix": " clauses — confirm to save:",
        "confirm_save_ms": "Confirm & Save MS",
        "ms_saved": "MS saved to library.",
        "saved_ms_title": "Saved Method Statements",
        "no_project": "No project set up yet.",
        "no_ms": "No method statements yet.",
        "complete_setup_first": "Complete Setup first.",
        "upload_ms_first": "Upload the MS file first.",
        "clauses_word": " clauses",

        "new_defect_title": "New Defect",
        "new_defect_sub": "Take a photo, add a note, let AI propose the "
                          "defects, then tick the real ones. Add more "
                          "manually if needed.",
        "photo_label": "Photo: not uploaded",
        "photo_upload": "Upload site photo",
        "note_label": "Note (optional)",
        "note_placeholder": "e.g. crack at column C3 base",
        "zone": "Zone",
        "element": "Element",
        "analyze": "Analyze with AI",
        "analyzing": "Analyzing photo... ",
        "ms_clauses_loaded": " MS clauses loaded.",
        "ai_found_prefix": "AI found ",
        "ai_found_suffix": " candidate(s). Tick the real ones:",
        "ai_found_none": "AI found no defects. Add one manually below.",
        "add_manual": "+ Add defect manually",
        "notice_details": "Notice details",
        "notice_details_sub": "Who gets the notice, and by when.",
        "send_to_sub": "Send to Subcontractor",
        "send_to_sub_placeholder": "e.g. Al-Ahram Steel Fixing",
        "deadline": "Deadline (days)",
        "raised_as": "Raised as",
        "raised_qc": "QC Internal",
        "raised_consultant": "Consultant / NCR",
        "generate_pdf": "Generate Notice PDF",
        "tick_at_least_one": "Tick at least one defect.",
        "enter_sub": "Enter the subcontractor name.",
        "notice_saved": "Notice saved: ",
        "upload_photo_first": "Upload a photo first.",
        "raw_debug": "Raw AI output (debug):",
        "error_prefix": "Error: ",

        "add_title": "Add defect manually",
        "add_sub": "AI missed something? Add it here.",
        "add_name": "Defect name",
        "add_location": "Location hint (optional)",
        "add_severity": "Severity",
        "add_ms": "MS clause id (optional)",
        "add_ecp": "ECP code (optional)",
        "add_repair": "Repair action (optional)",
        "add_button": "Add",
        "cancel_button": "Cancel",
        "name_required": "Defect name required.",
        "tag_ai": "AI",
        "tag_manual": "MANUAL",

        "reg_title": "Defect Register",
        "reg_sub": "Every notice you have issued. Filter by source, click "
                   "a row for detail, export the register or the closure "
                   "report.",
        "source": "Source",
        "source_all": "All",
        "source_qc": "QC Internal",
        "source_consultant": "Consultant / NCR",
        "export_register": "Export Register",
        "closure_report": "Closure Report",
        "refresh": "Refresh",
        "no_defects_filter": "No defects for this filter.",
        "shown": "Shown: ",
        "open_label": "Open: ",
        "closed_label": "Closed: ",
        "no_rows_export": "No rows to export.",
        "col_uid": "UID",
        "col_zone": "Zone",
        "col_sub": "Subcontractor",
        "col_count": "#",
        "col_source": "Source",
        "col_status": "Status",
        "col_created": "Created",

        "dialog_notice": "Notice ",
        "dialog_zone": "Zone ",
        "dialog_ncr": "Consultant NCR: ",
        "dialog_note": "Note: ",
        "dialog_none": "(none)",
        "dialog_repair": "Repair: ",
        "dialog_download": "Download Notice PDF",
        "dialog_close": "Mark Closed",
        "dialog_dismiss": "Close",
        "dialog_ncr_input": "Consultant NCR Number (required to close)",
        "dialog_ncr_required": "Enter the consultant NCR number first.",
        "dialog_closed_msg": "Defect marked closed.",
        "dialog_not_found": "Defect not found.",

        "sev_low": "Low",
        "sev_medium": "Medium",
        "sev_high": "High",
        "sev_critical": "Critical",

        "el_column": "column",
        "el_beam": "beam",
        "el_slab": "slab",
        "el_wall": "wall",
        "el_foundation": "foundation",
        "el_finishing": "finishing",
        "disc_structural": "Structural",
        "disc_arch": "Architectural",
        "disc_mep": "MEP",
        "zone_general": "General",
    },
    "ar": {
        "app_title": "إشعارات العيوب",
        "lang_button": "English",
        "tab_setup": "الإعداد",
        "tab_ms": "بيانات الطريقة",
        "tab_new": "عيب جديد",
        "tab_register": "السجل",

        "setup_title": "إعداد المشروع",
        "setup_sub": "يُملأ مرة واحدة. يُحفظ لكل إشعار عيب.",
        "project_name": "اسم المشروع",
        "contractor": "المقاول",
        "consultant": "الاستشاري",
        "location": "الموقع",
        "engineer_name": "اسم مهندس الجودة",
        "upload_logo": "تحميل شعار الشركة (PNG/JPG)",
        "logo_loaded": "تم تحميل الشعار: ",
        "logo_loaded_flag": "محمل",
        "logo_missing_flag": "غير محمل",
        "logo_label": "الشعار: ",
        "save_project": "حفظ المشروع",
        "project_saved": "تم حفظ المشروع.",
        "project_name_required": "اسم المشروع مطلوب.",

        "ms_title": "بيانات طريقة العمل",
        "ms_sub": "حمّل ملف MS بصيغة PDF أو DOCX أو TXT. يستخرج "
                  "البرنامج البنود مرة واحدة ثم يستشهد بها في كل إشعار.",
        "ms_file_label": "الملف: غير محمل",
        "ms_file_loaded": "تم تحميل الملف: ",
        "ms_upload": "تحميل ملف MS (PDF / DOCX / TXT)",
        "ms_number": "رقم MS",
        "ms_doc_title": "العنوان",
        "element_type": "نوع العنصر",
        "discipline": "التخصص",
        "extract_clauses": "استخراج البنود بالذكاء الاصطناعي",
        "extracting": "جاري استخراج البنود...",
        "extracted_prefix": "تم استخراج ",
        "extracted_suffix": " بند — أكد للحفظ:",
        "confirm_save_ms": "تأكيد وحفظ MS",
        "ms_saved": "تم حفظ MS في المكتبة.",
        "saved_ms_title": "بيانات الطريقة المحفوظة",
        "no_project": "لا يوجد مشروع بعد.",
        "no_ms": "لا توجد بيانات طريقة بعد.",
        "complete_setup_first": "أكمل الإعداد أولاً.",
        "upload_ms_first": "حمّل ملف MS أولاً.",
        "clauses_word": " بند",

        "new_defect_title": "عيب جديد",
        "new_defect_sub": "التقط صورة، أضف ملاحظة، ودع الذكاء الاصطناعي "
                          "يقترح العيوب، ثم اختر الحقيقية منها. أضف يدوياً "
                          "عند الحاجة.",
        "photo_label": "الصورة: غير محملة",
        "photo_upload": "تحميل صورة الموقع",
        "note_label": "ملاحظة (اختياري)",
        "note_placeholder": "مثال: شرخ عند قاعدة العمود C3",
        "zone": "المنطقة",
        "element": "العنصر",
        "analyze": "تحليل بالذكاء الاصطناعي",
        "analyzing": "جاري تحليل الصورة... ",
        "ms_clauses_loaded": " بند MS محمّل.",
        "ai_found_prefix": "وجد الذكاء الاصطناعي ",
        "ai_found_suffix": " عيب محتمل. اختر الصحيح:",
        "ai_found_none": "لم يجد الذكاء الاصطناعي عيوباً. أضف عيباً يدوياً أدناه.",
        "add_manual": "+ إضافة عيب يدوياً",
        "notice_details": "تفاصيل الإشعار",
        "notice_details_sub": "من يستلم الإشعار، ومتى.",
        "send_to_sub": "إرسال إلى المقاول الفرعي",
        "send_to_sub_placeholder": "مثال: الأهرام لتثبيت الحديد",
        "deadline": "المهلة (أيام)",
        "raised_as": "مصدر الإشعار",
        "raised_qc": "داخلي QC",
        "raised_consultant": "استشاري / NCR",
        "generate_pdf": "إنشاء إشعار PDF",
        "tick_at_least_one": "اختر عيباً واحداً على الأقل.",
        "enter_sub": "أدخل اسم المقاول الفرعي.",
        "notice_saved": "تم حفظ الإشعار: ",
        "upload_photo_first": "حمّل صورة أولاً.",
        "raw_debug": "الناتج الخام للذكاء الاصطناعي (تصحيح):",
        "error_prefix": "خطأ: ",

        "add_title": "إضافة عيب يدوياً",
        "add_sub": "فات الذكاء الاصطناعي شيء؟ أضفه هنا.",
        "add_name": "اسم العيب",
        "add_location": "الموقع (اختياري)",
        "add_severity": "الخطورة",
        "add_ms": "رقم بند MS (اختياري)",
        "add_ecp": "كود ECP (اختياري)",
        "add_repair": "إجراء الإصلاح (اختياري)",
        "add_button": "إضافة",
        "cancel_button": "إلغاء",
        "name_required": "اسم العيب مطلوب.",
        "tag_ai": "ذكاء اصطناعي",
        "tag_manual": "يدوي",

        "reg_title": "سجل العيوب",
        "reg_sub": "كل إشعار صادرته. صفِّ حسب المصدر، اضغط على صف "
                   "للتفاصيل، صدّر السجل أو تقرير الإغلاق.",
        "source": "المصدر",
        "source_all": "الكل",
        "source_qc": "داخلي QC",
        "source_consultant": "استشاري / NCR",
        "export_register": "تصدير السجل",
        "closure_report": "تقرير الإغلاق",
        "refresh": "تحديث",
        "no_defects_filter": "لا توجد عيوب لهذا الفلتر.",
        "shown": "المعروض: ",
        "open_label": "مفتوح: ",
        "closed_label": "مغلق: ",
        "no_rows_export": "لا توجد صفوف للتصدير.",
        "col_uid": "الرقم",
        "col_zone": "المنطقة",
        "col_sub": "المقاول الفرعي",
        "col_count": "#",
        "col_source": "المصدر",
        "col_status": "الحالة",
        "col_created": "التاريخ",

        "dialog_notice": "إشعار ",
        "dialog_zone": "المنطقة ",
        "dialog_ncr": "رقم NCR الاستشاري: ",
        "dialog_note": "ملاحظة: ",
        "dialog_none": "(لا يوجد)",
        "dialog_repair": "الإصلاح: ",
        "dialog_download": "تحميل إشعار PDF",
        "dialog_close": "تعليم كمغلق",
        "dialog_dismiss": "إغلاق",
        "dialog_ncr_input": "رقم NCR الاستشاري (مطلوب للإغلاق)",
        "dialog_ncr_required": "أدخل رقم NCR الاستشاري أولاً.",
        "dialog_closed_msg": "تم تعليم العيب كمغلق.",
        "dialog_not_found": "العيب غير موجود.",

        "sev_low": "منخفض",
        "sev_medium": "متوسط",
        "sev_high": "عالي",
        "sev_critical": "حرج",

        "el_column": "عمود",
        "el_beam": "كمرة",
        "el_slab": "بلاطة",
        "el_wall": "حائط",
        "el_foundation": "أساس",
        "el_finishing": "تشطيبات",
        "disc_structural": "إنشائي",
        "disc_arch": "معماري",
        "disc_mep": "كهروميكانيكي",
        "zone_general": "عام",
    },
}


def _lang():
    return LANG["code"]


def _t(key):
    return T[_lang()].get(key, key)


def _toggle_lang():
    LANG["code"] = "ar" if LANG["code"] == "en" else "en"
    ui.run_javascript('window.location.reload()')


# ---- Display helpers (English values in DB, translated for the UI) ----
def _element_options():
    return {
        "column": _t("el_column"),
        "beam": _t("el_beam"),
        "slab": _t("el_slab"),
        "wall": _t("el_wall"),
        "foundation": _t("el_foundation"),
        "finishing": _t("el_finishing"),
    }


def _discipline_options():
    return {
        "Structural": _t("disc_structural"),
        "Architectural": _t("disc_arch"),
        "MEP": _t("disc_mep"),
    }


def _zone_options():
    return {
        "A": "A", "B": "B", "C": "C", "D": "D",
        "General": _t("zone_general"),
    }


def _severity_options():
    return {
        "Low": _t("sev_low"),
        "Medium": _t("sev_medium"),
        "High": _t("sev_high"),
        "Critical": _t("sev_critical"),
    }


# =====================================================================
# Styles
# =====================================================================
TXT_TITLE  = "color:#0f172a;font-size:16px;font-weight:700;margin-bottom:4px;"
TXT_SUB    = "color:#64748b;font-size:13px;margin-bottom:16px;"
TXT_MUTED  = "color:#64748b;font-size:13px;"
CARD       = ("background:#ffffff;border:1px solid #e2e8f0;border-radius:12px;"
              "padding:22px;margin-bottom:16px;width:100%;display:block;"
              "box-sizing:border-box;")
INPUT_ROW  = "display:flex;gap:12px;width:100%;margin-bottom:10px;"
ITEM_BOX   = ("background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;"
              "padding:14px 16px;margin-bottom:10px;display:block;width:100%;"
              "box-sizing:border-box;")
BTN_PRIMARY = "background:#2563eb;color:#ffffff;font-weight:600;"
BTN_SUCCESS = "background:#059669;color:#ffffff;font-weight:600;"
BTN_FLAT    = "background:#f1f5f9;color:#0f172a;font-weight:600;"
BTN_DANGER  = "background:#fee2e2;color:#b91c1c;font-weight:700;min-width:36px;"


def build_defect_ui():
    # Flip page direction for Arabic
    if _lang() == "ar":
        try:
            ui.query('body').style('direction: rtl; text-align: right;')
        except Exception:
            pass

    state = {
        "project": db.get_project(),
        "photo_bytes": None,
        "photo_mime": None,
    }

    # ---- Header with toggle ----
    with ui.element('div').style(
        "display:flex;justify-content:space-between;align-items:center;"
        "width:100%;margin-bottom:12px;"
    ):
        ui.label(_t("app_title")).style(
            "color:#0f172a;font-size:20px;font-weight:800;"
        )
        ui.button(_t("lang_button"), on_click=_toggle_lang).style(BTN_FLAT)

    with ui.tabs().style("width:100%;") as tabs:
        t_setup = ui.tab(_t("tab_setup"), icon="settings")
        t_ms = ui.tab(_t("tab_ms"), icon="menu_book")
        t_new = ui.tab(_t("tab_new"), icon="add_a_photo")
        t_reg = ui.tab(_t("tab_register"), icon="list_alt")

    default = t_new if state["project"] else t_setup
    tabs.value = default

    with ui.tab_panels(tabs, value=default).style("width:100%;"):
        with ui.tab_panel(t_setup):
            _build_setup(state, tabs, t_new)
        with ui.tab_panel(t_ms):
            _build_ms(state)
        with ui.tab_panel(t_new):
            _build_new_defect(state)
        with ui.tab_panel(t_reg):
            _build_register(state)


def _card():
    return ui.element('div').style(CARD)


# =====================================================================
# SCREEN 1 — SETUP
# =====================================================================
def _build_setup(state, tabs, next_tab):
    with _card():
        ui.label(_t("setup_title")).style(TXT_TITLE)
        ui.label(_t("setup_sub")).style(TXT_SUB)

        proj = state["project"] or {}
        name_in = ui.input(_t("project_name"),
                            value=proj.get("name", "")).style("width:100%;")
        with ui.element('div').style(INPUT_ROW):
            contractor_in = ui.input(_t("contractor"),
                                      value=proj.get("contractor", "")).style("flex:1;")
            consultant_in = ui.input(_t("consultant"),
                                      value=proj.get("consultant", "")).style("flex:1;")
        location_in = ui.input(_t("location"),
                                value=proj.get("location", "")).style("width:100%;")
        engineer_in = ui.input(_t("engineer_name"),
                                value=proj.get("engineer_name", "")).style("width:100%;")

        logo_holder = {"bytes": proj.get("logo_bytes")}
        flag = _t("logo_loaded_flag") if logo_holder["bytes"] else _t("logo_missing_flag")
        logo_status = ui.label(_t("logo_label") + flag).style(TXT_MUTED)

        async def handle_logo(e):
            logo_holder["bytes"] = await e.file.read()
            logo_status.set_text(_t("logo_loaded") + e.file.name)

        ui.upload(on_upload=handle_logo, auto_upload=True).style(
            "width:100%;"
        ).props("flat bordered label='" + _t("upload_logo") + "'")

        def save():
            if not name_in.value.strip():
                ui.notify(_t("project_name_required"), type="warning")
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
            ui.notify(_t("project_saved"), type="positive")
            tabs.value = next_tab

        ui.button(_t("save_project"), on_click=save).style(BTN_PRIMARY)


# =====================================================================
# SCREEN 2 — METHOD STATEMENTS
# =====================================================================
def _build_ms(state):
    with _card():
        ui.label(_t("ms_title")).style(TXT_TITLE)
        ui.label(_t("ms_sub")).style(TXT_SUB)

        doc_holder = {"bytes": None, "name": ""}
        doc_status = ui.label(_t("ms_file_label")).style(TXT_MUTED)

        async def handle_doc(e):
            doc_holder["bytes"] = await e.file.read()
            doc_holder["name"] = e.file.name
            doc_status.set_text(
                _t("ms_file_loaded") + e.file.name + " (" +
                str(len(doc_holder["bytes"]) // 1024) + " KB)"
            )

        ui.upload(on_upload=handle_doc, auto_upload=True).style(
            "width:100%;"
        ).props("flat bordered accept=.pdf,.docx,.doc,.txt,.md "
                "label='" + _t("ms_upload") + "'")

        with ui.element('div').style(INPUT_ROW):
            ms_num_in = ui.input(_t("ms_number"), value="MS-01").style("flex:1;")
            title_in = ui.input(_t("ms_doc_title"),
                                 value="Reinforcement").style("flex:1;")
        with ui.element('div').style(INPUT_ROW):
            element_in = ui.select(_element_options(), value="column",
                                    label=_t("element_type")).style("flex:1;")
            disc_in = ui.select(_discipline_options(), value="Structural",
                                 label=_t("discipline")).style("flex:1;")

        clause_preview = ui.element('div').style("width:100%;")

        async def extract():
            if not doc_holder["bytes"]:
                ui.notify(_t("upload_ms_first"), type="warning")
                return
            clause_preview.clear()
            with clause_preview:
                ui.label(_t("extracting")).style(TXT_MUTED)
            result = await svc.extract_clauses_from_pdf(
                doc_holder["bytes"], call_gemini_json, doc_holder["name"]
            )
            clause_preview.clear()

            if result.get("error"):
                with clause_preview:
                    ui.label(_t("error_prefix") + str(result["error"])).style(
                        "color:#dc2626;font-size:13px;"
                    )
                return

            clauses = result["clauses"]
            state["pending_clauses"] = clauses

            with clause_preview:
                ui.label(
                    _t("extracted_prefix") + str(len(clauses)) +
                    _t("extracted_suffix")
                ).style(TXT_TITLE)
                for cl in clauses:
                    with ui.element('div').style(ITEM_BOX):
                        ui.label("§" + cl["id"] + " — " + cl["title"]).style(
                            "color:#0f172a;font-weight:600;font-size:14px;"
                        )
                        ui.label(cl["text"][:180]).style(TXT_MUTED)

                def confirm_save():
                    if not state.get("project"):
                        ui.notify(_t("complete_setup_first"), type="warning")
                        return
                    db.save_ms(
                        project_id=state["project"]["id"],
                        ms_number=ms_num_in.value.strip(),
                        title=title_in.value.strip(),
                        element_type=element_in.value,
                        discipline=disc_in.value,
                        pdf_bytes=doc_holder["bytes"],
                        clauses=clauses,
                    )
                    ui.notify(_t("ms_saved"), type="positive")
                    clause_preview.clear()
                    _refresh_ms_list(state)

                ui.button(_t("confirm_save_ms"),
                          on_click=confirm_save).style(BTN_SUCCESS)

        ui.button(_t("extract_clauses"), on_click=extract).style(BTN_PRIMARY)

    with _card():
        ui.label(_t("saved_ms_title")).style(TXT_TITLE)
        state["ms_list_container"] = ui.element('div').style("width:100%;")
        _refresh_ms_list(state)


def _refresh_ms_list(state):
    container = state.get("ms_list_container")
    if not container:
        return
    container.clear()
    if not state.get("project"):
        with container:
            ui.label(_t("no_project")).style(TXT_MUTED)
        return
    ms_list = db.list_ms(state["project"]["id"])
    with container:
        if not ms_list:
            ui.label(_t("no_ms")).style(TXT_MUTED)
            return
        for m in ms_list:
            with ui.element('div').style(ITEM_BOX):
                ui.label(m["ms_number"] + " — " + m["title"]).style(
                    "color:#0f172a;font-weight:600;font-size:14px;"
                )
                ui.label(
                    m["element_type"] + " · " + m["discipline"] + " · " +
                    str(len(m["clauses"])) + _t("clauses_word")
                ).style(TXT_MUTED)


# =====================================================================
# SCREEN 3 — NEW DEFECT
# =====================================================================
def _build_new_defect(state):
    with _card():
        ui.label(_t("new_defect_title")).style(TXT_TITLE)
        ui.label(_t("new_defect_sub")).style(TXT_SUB)

        photo_holder = {"bytes": None, "mime": None}
        photo_status = ui.label(_t("photo_label")).style(TXT_MUTED)

        async def handle_photo(e):
            data = await e.file.read()
            photo_holder["bytes"] = data
            photo_holder["mime"] = ("image/jpeg"
                if e.file.name.lower().endswith((".jpg", ".jpeg"))
                else "image/png")
            state["photo_bytes"] = data
            state["photo_mime"] = photo_holder["mime"]
            photo_status.set_text(_t("photo_label") + " " + e.file.name)

        ui.upload(on_upload=handle_photo, auto_upload=True).style(
            "width:100%;"
        ).props("flat bordered accept=image/* label='" + _t("photo_upload") + "'")

        note_in = ui.textarea(
            label=_t("note_label"),
            placeholder=_t("note_placeholder")
        ).style("width:100%;")

        with ui.element('div').style(INPUT_ROW):
            zone_in = ui.select(_zone_options(), value="A",
                                 label=_t("zone")).style("flex:1;")
            element_in = ui.select(_element_options(), value="column",
                                    label=_t("element")).style("flex:1;")

        candidates_container = ui.element('div').style(
            "width:100%;margin-top:16px;"
        )

        def _render_card(item, list_ref, refresh_fn):
            with ui.element('div').style(ITEM_BOX):
                with ui.element('div').style(
                    "display:flex;gap:12px;align-items:flex-start;width:100%;"
                ):
                    def _make_toggle(it):
                        def _h(e):
                            it["_sel"] = bool(e.value)
                        return _h
                    ui.checkbox(value=item.get("_sel", True),
                                 on_change=_make_toggle(item))
                    with ui.element('div').style("flex:1;min-width:0;"):
                        if item.get("_manual"):
                            tag, tag_color = _t("tag_manual"), "#059669"
                        else:
                            tag, tag_color = _t("tag_ai"), "#2563eb"
                        ui.label(tag).style(
                            "color:" + tag_color + ";font-size:10px;"
                            "font-weight:700;display:inline-block;"
                            "background:#f1f5f9;padding:1px 6px;"
                            "border-radius:4px;margin-bottom:4px;"
                        )
                        ui.label(str(item.get("name", ""))).style(
                            "color:#0f172a;font-weight:700;"
                            "font-size:15px;display:block;"
                            "margin-bottom:6px;"
                        )
                        if item.get("location_hint"):
                            ui.label(str(item["location_hint"])).style(
                                "color:#475569;font-size:13px;"
                                "display:block;margin-bottom:3px;"
                            )
                        cit = []
                        if item.get("ms_violations"):
                            cit.append("MS: " + ", ".join(item["ms_violations"]))
                        if item.get("code_violations"):
                            cit.append("Code: " + ", ".join(item["code_violations"]))
                        if cit:
                            ui.label(" | ".join(cit)).style(
                                "color:#475569;font-size:13px;"
                                "font-style:italic;display:block;"
                                "margin-bottom:3px;"
                            )
                        if item.get("repair_action"):
                            ui.label(_t("dialog_repair") +
                                     str(item["repair_action"])).style(
                                "color:#64748b;font-size:13px;"
                                "display:block;margin-bottom:3px;"
                            )
                        sev_display = _severity_options().get(
                            item.get("severity", "Medium"),
                            item.get("severity", "Medium")
                        )
                        ui.label(sev_display).style(
                            "color:#64748b;font-size:12px;display:block;"
                        )
                    def _make_remove(it, lst, fn):
                        def _do():
                            if it in lst:
                                lst.remove(it)
                            fn()
                        return _do
                    ui.button("✕",
                              on_click=_make_remove(item, list_ref, refresh_fn)
                              ).style(BTN_DANGER)

        def _open_add_dialog(manual_list, refresh_fn):
            with ui.dialog() as dlg, ui.card().style(
                "background:#ffffff;padding:22px;min-width:420px;max-width:95vw;"
            ):
                ui.label(_t("add_title")).style(TXT_TITLE)
                ui.label(_t("add_sub")).style(TXT_SUB)

                name_in = ui.input(_t("add_name")).style("width:100%;")
                loc_in = ui.input(_t("add_location")).style("width:100%;")
                sev_in = ui.select(_severity_options(), value="Medium",
                                    label=_t("add_severity")).style("width:100%;")
                ms_in = ui.input(_t("add_ms")).style("width:100%;")
                ecp_in = ui.input(_t("add_ecp")).style("width:100%;")
                rep_in = ui.input(_t("add_repair")).style("width:100%;")

                def _save():
                    if not name_in.value.strip():
                        ui.notify(_t("name_required"), type="warning")
                        return
                    manual_list.append({
                        "name": name_in.value.strip(),
                        "location_hint": loc_in.value.strip(),
                        "severity": sev_in.value,
                        "ms_violations": ([ms_in.value.strip()]
                                          if ms_in.value.strip() else []),
                        "code_violations": ([ecp_in.value.strip()]
                                            if ecp_in.value.strip() else []),
                        "repair_action": rep_in.value.strip(),
                        "_sel": True,
                        "_manual": True,
                    })
                    dlg.close()
                    refresh_fn()

                with ui.element('div').style(
                    "display:flex;gap:8px;margin-top:16px;"
                ):
                    ui.button(_t("add_button"), on_click=_save).style(BTN_SUCCESS)
                    ui.button(_t("cancel_button"), on_click=dlg.close).style(BTN_FLAT)
            dlg.open()

        async def analyze():
            if not photo_holder["bytes"]:
                ui.notify(_t("upload_photo_first"), type="warning")
                return
            if not state.get("project"):
                ui.notify(_t("complete_setup_first"), type="warning")
                return

            ms_clauses = db.get_clauses_for_element(
                state["project"]["id"], element_in.value
            )
            candidates_container.clear()
            with candidates_container:
                ui.label(
                    _t("analyzing") + str(len(ms_clauses)) +
                    _t("ms_clauses_loaded")
                ).style(TXT_MUTED)

            result = await svc.analyze_defect_photo(
                photo_bytes=photo_holder["bytes"],
                mime_type=photo_holder["mime"],
                note=note_in.value or "",
                ms_clauses=ms_clauses,
                element_type=element_in.value,
                call_gemini_json_fn=call_gemini_json,
            )

            if result.get("error"):
                candidates_container.clear()
                with candidates_container:
                    ui.label(_t("error_prefix") + str(result["error"])).style(
                        "color:#dc2626;font-size:13px;"
                    )
                    raw_txt = result.get("raw", "")
                    if raw_txt:
                        ui.label(_t("raw_debug")).style(TXT_MUTED)
                        ui.label(raw_txt).style(
                            "color:#7c2d12;font-size:11px;"
                            "font-family:monospace;white-space:pre-wrap;"
                            "background:#fef3c7;padding:8px;"
                            "border-radius:6px;width:100%;"
                        )
                return

            candidates = list(result["defects"])
            for c in candidates:
                c["_sel"] = True
                c["_manual"] = False
            manual_list = []

            def render_all():
                candidates_container.clear()
                all_items = candidates + manual_list
                with candidates_container:
                    if not all_items:
                        ui.label(_t("ai_found_none")).style(TXT_MUTED)
                    else:
                        ui.label(
                            _t("ai_found_prefix") + str(len(candidates)) +
                            _t("ai_found_suffix")
                        ).style(TXT_TITLE)
                        for c in candidates:
                            _render_card(c, candidates, render_all)
                        for m in manual_list:
                            _render_card(m, manual_list, render_all)

                    def _add_click():
                        _open_add_dialog(manual_list, render_all)

                    ui.button(_t("add_manual"),
                              on_click=_add_click).style(
                        BTN_FLAT + "margin-top:8px;"
                    )

                    ui.label(_t("notice_details")).style(
                        TXT_TITLE + "margin-top:24px;"
                    )
                    ui.label(_t("notice_details_sub")).style(TXT_SUB)

                    sub_in = ui.input(
                        _t("send_to_sub"),
                        placeholder=_t("send_to_sub_placeholder")
                    ).style("width:100%;")

                    with ui.element('div').style(INPUT_ROW):
                        deadline_in = ui.select(
                            [1, 2, 3, 5, 7, 14], value=3,
                            label=_t("deadline")
                        ).style("flex:1;")
                        raise_in = ui.select(
                            {"qc_internal": _t("raised_qc"),
                             "consultant": _t("raised_consultant")},
                            value="qc_internal",
                            label=_t("raised_as")
                        ).style("flex:1;")

                    def generate():
                        selected = [c for c in all_items
                                    if c.get("_sel", True)]
                        if not selected:
                            ui.notify(_t("tick_at_least_one"),
                                       type="warning")
                            return
                        if not sub_in.value.strip():
                            ui.notify(_t("enter_sub"), type="warning")
                            return

                        clean_selected = []
                        for s in selected:
                            clean_selected.append({
                                "name": s.get("name", ""),
                                "location_hint": s.get("location_hint", ""),
                                "severity": s.get("severity", "Medium"),
                                "ms_violations": s.get("ms_violations", []),
                                "code_violations": s.get("code_violations", []),
                                "repair_action": s.get("repair_action", ""),
                                "zone": zone_in.value,
                            })

                        notice_uid = svc.generate_uid("NTC")
                        pdf_bytes = svc.build_notice_pdf(
                            project=state["project"],
                            defects=clean_selected,
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
                            selected=clean_selected,
                            notice_pdf=pdf_bytes,
                        )
                        ui.notify(_t("notice_saved") + notice_uid,
                                   type="positive")
                        ui.download(pdf_bytes, filename=notice_uid + ".pdf")

                    ui.button(_t("generate_pdf"),
                              on_click=generate).style(
                        BTN_SUCCESS + "margin-top:12px;"
                    )

            render_all()

        ui.button(_t("analyze"), on_click=analyze).style(
            BTN_PRIMARY + "margin-top:12px;"
        )


# =====================================================================
# SCREEN 4 — REGISTER
# =====================================================================
def _build_register(state):
    with _card():
        ui.label(_t("reg_title")).style(TXT_TITLE)
        ui.label(_t("reg_sub")).style(TXT_SUB)

        table_container = ui.element('div').style("width:100%;")
        fstate = {"raise_filter": "all"}

        def refresh():
            table_container.clear()
            if not state.get("project"):
                with table_container:
                    ui.label(_t("no_project")).style(TXT_MUTED)
                return

            rf = fstate["raise_filter"]
            rows = db.list_defects(
                state["project"]["id"],
                raise_filter=None if rf == "all" else rf,
            )

            with table_container:
                with ui.element('div').style(
                    "display:flex;gap:10px;align-items:center;"
                    "width:100%;margin-bottom:12px;flex-wrap:wrap;"
                ):
                    ui.label(_t("source")).style(TXT_MUTED)
                    filt = ui.select(
                        {"all": _t("source_all"),
                         "qc_internal": _t("source_qc"),
                         "consultant": _t("source_consultant")},
                        value=rf,
                    ).style("min-width:180px;")

                    def on_filter(e):
                        fstate["raise_filter"] = e.value
                        refresh()

                    filt.on("update:model-value", on_filter)

                    ui.space()

                    def export_register():
                        if not rows:
                            ui.notify(_t("no_rows_export"), type="warning")
                            return
                        pdf = svc.build_register_pdf(
                            state["project"], rows,
                            logo_bytes=state["project"].get("logo_bytes"),
                        )
                        ui.download(pdf, filename="defect_register.pdf")

                    def export_closure():
                        if not rows:
                            ui.notify(_t("no_rows_export"), type="warning")
                            return
                        pdf = svc.build_closure_pdf(
                            state["project"], rows,
                            logo_bytes=state["project"].get("logo_bytes"),
                        )
                        ui.download(pdf, filename="closure_report.pdf")

                    ui.button(_t("export_register"),
                              on_click=export_register).style(BTN_FLAT)
                    ui.button(_t("closure_report"),
                              on_click=export_closure).style(BTN_PRIMARY)

                if not rows:
                    ui.label(_t("no_defects_filter")).style(TXT_MUTED)
                    return

                open_count = sum(1 for r in rows if r["status"] == "open")
                ui.label(
                    _t("shown") + str(len(rows)) +
                    "  ·  " + _t("open_label") + str(open_count) +
                    "  ·  " + _t("closed_label") + str(len(rows) - open_count)
                ).style(TXT_TITLE)

                table = ui.table(
                    columns=[
                        {"name": "uid", "label": _t("col_uid"),
                         "field": "uid", "align": "left"},
                        {"name": "zone", "label": _t("col_zone"),
                         "field": "zone"},
                        {"name": "sub", "label": _t("col_sub"),
                         "field": "subcontractor", "align": "left"},
                        {"name": "count", "label": _t("col_count"),
                         "field": "count"},
                        {"name": "raise_type", "label": _t("col_source"),
                         "field": "raise_type"},
                        {"name": "status", "label": _t("col_status"),
                         "field": "status"},
                        {"name": "created", "label": _t("col_created"),
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

        ui.button(_t("refresh"), on_click=refresh).style(BTN_FLAT)
        refresh()


def _show_defect_dialog(defect_id, on_close_cb):
    d = db.get_defect(defect_id)
    if not d:
        ui.notify(_t("dialog_not_found"), type="negative")
        return

    is_consultant = (d.get("raise_type") or "qc_internal") == "consultant"
    source_label = _t("source_consultant") if is_consultant else _t("source_qc")

    with ui.dialog() as dialog, ui.card().style(
        "background:#ffffff;padding:24px;max-width:880px;width:100%;"
    ):
        ui.label(_t("dialog_notice") + d["uid"]).style(
            "color:#0f172a;font-size:18px;font-weight:700;"
        )
        ui.label(
            _t("dialog_zone") + str(d["zone"]) + " · " +
            str(d["subcontractor"]) + " · " +
            source_label + " · " +
            d["status"].upper()
        ).style(TXT_MUTED)

        if d.get("consultant_ncr"):
            ui.label(_t("dialog_ncr") + str(d["consultant_ncr"])).style(
                "color:#b45309;font-size:13px;font-weight:600;"
            )

        ui.separator()

        with ui.element('div').style(
            "display:flex;gap:20px;align-items:flex-start;width:100%;"
        ):
            if d.get("photo_bytes"):
                ui.image(io.BytesIO(d["photo_bytes"])).style(
                    "width:280px;border-radius:10px;border:1px solid #e2e8f0;"
                )
            with ui.element('div').style("flex:1;"):
                ui.label(_t("dialog_note") +
                         str(d["note"] or _t("dialog_none"))).style(TXT_MUTED)
                for i, s in enumerate(d["selected"], 1):
                    with ui.element('div').style(ITEM_BOX):
                        ui.label(
                            str(i) + ". " + str(s.get("name", ""))
                        ).style("color:#0f172a;font-weight:600;")
                        cit = []
                        if s.get("ms_violations"):
                            cit.append("MS: " + ", ".join(s["ms_violations"]))
                        if s.get("code_violations"):
                            cit.append("Code: " +
                                       ", ".join(s["code_violations"]))
                        if cit:
                            ui.label(" | ".join(cit)).style(
                                "color:#475569;font-size:13px;font-style:italic;"
                            )
                        if s.get("repair_action"):
                            ui.label(_t("dialog_repair") +
                                     str(s["repair_action"])).style(
                                "color:#64748b;font-size:13px;"
                            )

        ui.separator()

        ncr_in = None
        if is_consultant and d["status"] == "open":
            ncr_in = ui.input(_t("dialog_ncr_input")).style(
                "width:100%;margin-top:6px;"
            )

        with ui.element('div').style(
            "display:flex;gap:8px;margin-top:12px;flex-wrap:wrap;"
        ):
            if d.get("notice_pdf"):
                ui.button(
                    _t("dialog_download"),
                    on_click=lambda: ui.download(
                        d["notice_pdf"], filename=d["uid"] + ".pdf"
                    )
                ).style(BTN_PRIMARY)

            if d["status"] == "open":
                def do_close():
                    if is_consultant:
                        if not ncr_in or not ncr_in.value.strip():
                            ui.notify(_t("dialog_ncr_required"),
                                       type="warning")
                            return
                        db.close_defect(
                            defect_id,
                            consultant_ncr=ncr_in.value.strip()
                        )
                    else:
                        db.close_defect(defect_id)
                    ui.notify(_t("dialog_closed_msg"), type="positive")
                    dialog.close()
                    on_close_cb()

                ui.button(_t("dialog_close"), on_click=do_close).style(BTN_SUCCESS)

            ui.button(_t("dialog_dismiss"),
                      on_click=dialog.close).style(BTN_FLAT)

    dialog.open()
