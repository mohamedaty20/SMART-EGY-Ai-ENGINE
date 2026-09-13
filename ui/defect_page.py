"""
ui/defect_page.py — Full redesign.
Off-white theme, mobile-first, collapsible left drawer, 2-tab wizard.
"""
import io
from nicegui import ui

from services import defect_db as db
from services import defect_service as svc
from services.ai_service import call_gemini_json


# =====================================================================
# LANGUAGE STATE
# =====================================================================
LANG = {"code": "en"}

T = {
    "en": {
        "app_title": "Defect Notices",
        "menu": "Menu",
        "new_defect": "New Defect",
        "logs": "Logs",
        "project_info": "Project",
        "no_project": "No project yet",
        "setup_project": "Set up project",
        "edit_project": "Edit",
        "contractor": "Contractor",
        "subcontractor": "Subcontractor",
        "consultant": "Consultant",
        "location": "Location",
        "engineer": "QC Engineer",
        "logo": "Company Logo",
        "upload_logo": "Upload logo",
        "logo_loaded": "Logo loaded",
        "ms_section": "Method Statements",
        "upload_ms": "Upload MS",
        "no_ms": "No method statements yet",
        "clauses_count": "clauses",
        "delete": "Delete",
        "confirm_delete_ms": "Delete this method statement?",
        "yes": "Yes", "no": "No",

        "photo_title": "Take a photo of the defect",
        "photo_sub": "Upload a site photo to begin.",
        "choose_photo": "Choose photo",
        "change_photo": "Change photo",
        "note_label": "Note (optional)",
        "note_placeholder": "e.g. crack at column C3 base",
        "zone": "Zone",
        "element": "Element",
        "analyze": "Analyze with AI",
        "analyzing": "Analyzing photo...",
        "back": "Back",
        "reset": "Start over",

        "ai_found": "AI found these defects. Untick false ones, add any missed:",
        "ai_found_none": "AI found no defects. Add one manually below.",
        "add_manual": "+ Add defect",
        "notice_details": "Notice details",
        "send_to": "Send to subcontractor",
        "send_to_placeholder": "e.g. Al-Ahram Steel Fixing",
        "deadline": "Deadline",
        "days": "days",
        "raised_as": "Raised as",
        "qc_internal": "QC Internal",
        "consultant_ncr": "Consultant / NCR",
        "generate_pdf": "Generate Notice PDF",
        "tick_one": "Tick at least one defect.",
        "enter_sub": "Enter the subcontractor name.",
        "notice_saved": "Notice saved",
        "upload_photo_first": "Upload a photo first.",
        "setup_first": "Set up the project first.",

        "add_defect_title": "Add defect manually",
        "name": "Defect name",
        "location_hint": "Location hint",
        "severity": "Severity",
        "ms_clause": "MS clause id",
        "ecp_code": "ECP code",
        "repair": "Repair action",
        "add": "Add", "cancel": "Cancel",
        "name_required": "Defect name is required.",
        "tag_ai": "AI", "tag_manual": "MANUAL",

        "logs_title": "Defect Logs",
        "logs_sub": "Every notice issued. Tap to view.",
        "no_logs": "No notices yet.",
        "filter_source": "Source",
        "filter_all": "All",
        "filter_qc": "QC Internal",
        "filter_consultant": "Consultant / NCR",
        "export_register": "Export Register",
        "closure_report": "Closure Report",
        "refresh": "Refresh",
        "open": "Open", "closed": "Closed",
        "no_rows": "Nothing here yet.",

        "notice": "Notice",
        "download_pdf": "Download PDF",
        "mark_closed": "Mark Closed",
        "close": "Close",
        "ncr_input": "Consultant NCR number",
        "ncr_required": "Enter the NCR number first.",
        "marked_closed": "Marked as closed.",
        "not_found": "Not found.",
        "repair_label": "Repair",

        "save": "Save", "cancel_btn": "Cancel",

        "setup_title": "Project Setup",
        "project_name": "Project name",
        "save_project": "Save",

        "ms_dialog_title": "Upload Method Statement",
        "ms_number": "MS number",
        "ms_title": "Title",
        "element_type": "Element type",
        "discipline": "Discipline",
        "extract": "Extract clauses",
        "extracting": "Extracting...",
        "extracted": "Extracted",
        "confirm_save": "Confirm & save",
        "ms_saved": "Saved",
        "ms_upload_file": "Choose file (PDF/DOCX/TXT)",
        "upload_first": "Choose a file first.",
        "error_prefix": "Error: ",

        "severity_low": "Low", "severity_medium": "Medium",
        "severity_high": "High", "severity_critical": "Critical",
        "element_column": "Column", "element_beam": "Beam",
        "element_slab": "Slab", "element_wall": "Wall",
        "element_foundation": "Foundation", "element_finishing": "Finishing",
        "discipline_structural": "Structural",
        "discipline_arch": "Architectural",
        "discipline_mep": "MEP",
        "zone_general": "General",
        "lang_button": "العربية",
    },
    "ar": {
        "app_title": "إشعارات العيوب",
        "menu": "القائمة",
        "new_defect": "عيب جديد",
        "logs": "السجل",
        "project_info": "المشروع",
        "no_project": "لا يوجد مشروع بعد",
        "setup_project": "إعداد المشروع",
        "edit_project": "تعديل",
        "contractor": "المقاول",
        "subcontractor": "المقاول الفرعي",
        "consultant": "الاستشاري",
        "location": "الموقع",
        "engineer": "مهندس الجودة",
        "logo": "شعار الشركة",
        "upload_logo": "تحميل الشعار",
        "logo_loaded": "تم تحميل الشعار",
        "ms_section": "بيانات طريقة العمل",
        "upload_ms": "تحميل MS",
        "no_ms": "لا توجد بيانات طريقة بعد",
        "clauses_count": "بند",
        "delete": "حذف",
        "confirm_delete_ms": "حذف بند الطريقة؟",
        "yes": "نعم", "no": "لا",

        "photo_title": "التقط صورة للعيب",
        "photo_sub": "حمّل صورة الموقع للبدء.",
        "choose_photo": "اختر صورة",
        "change_photo": "تغيير الصورة",
        "note_label": "ملاحظة (اختياري)",
        "note_placeholder": "مثال: شرخ عند قاعدة العمود C3",
        "zone": "المنطقة",
        "element": "العنصر",
        "analyze": "تحليل بالذكاء الاصطناعي",
        "analyzing": "جاري التحليل...",
        "back": "رجوع",
        "reset": "البدء من جديد",

        "ai_found": "وجد الذكاء الاصطناعي هذه العيوب. أزل غير الصحيحة وأضف أي مفقود:",
        "ai_found_none": "لم يجد الذكاء الاصطناعي عيوباً. أضف عيباً يدوياً أدناه.",
        "add_manual": "+ إضافة عيب",
        "notice_details": "تفاصيل الإشعار",
        "send_to": "إرسال إلى المقاول الفرعي",
        "send_to_placeholder": "مثال: الأهرام لتثبيت الحديد",
        "deadline": "المهلة",
        "days": "أيام",
        "raised_as": "مصدر الإشعار",
        "qc_internal": "داخلي QC",
        "consultant_ncr": "استشاري / NCR",
        "generate_pdf": "إنشاء إشعار PDF",
        "tick_one": "اختر عيباً واحداً على الأقل.",
        "enter_sub": "أدخل اسم المقاول الفرعي.",
        "notice_saved": "تم حفظ الإشعار",
        "upload_photo_first": "حمّل صورة أولاً.",
        "setup_first": "أعدّ المشروع أولاً.",

        "add_defect_title": "إضافة عيب يدوياً",
        "name": "اسم العيب",
        "location_hint": "الموقع التقريبي",
        "severity": "الخطورة",
        "ms_clause": "رقم بند MS",
        "ecp_code": "كود ECP",
        "repair": "إجراء الإصلاح",
        "add": "إضافة", "cancel": "إلغاء",
        "name_required": "اسم العيب مطلوب.",
        "tag_ai": "ذكاء اصطناعي", "tag_manual": "يدوي",

        "logs_title": "سجل العيوب",
        "logs_sub": "كل إشعار صدر. اضغط للعرض.",
        "no_logs": "لا توجد إشعارات بعد.",
        "filter_source": "المصدر",
        "filter_all": "الكل",
        "filter_qc": "داخلي QC",
        "filter_consultant": "استشاري / NCR",
        "export_register": "تصدير السجل",
        "closure_report": "تقرير الإغلاق",
        "refresh": "تحديث",
        "open": "مفتوح", "closed": "مغلق",
        "no_rows": "لا يوجد شيء بعد.",

        "notice": "إشعار",
        "download_pdf": "تحميل PDF",
        "mark_closed": "تعليم كمغلق",
        "close": "إغلاق",
        "ncr_input": "رقم NCR الاستشاري",
        "ncr_required": "أدخل رقم NCR أولاً.",
        "marked_closed": "تم التعليم كمغلق.",
        "not_found": "غير موجود.",
        "repair_label": "الإصلاح",

        "save": "حفظ", "cancel_btn": "إلغاء",

        "setup_title": "إعداد المشروع",
        "project_name": "اسم المشروع",
        "save_project": "حفظ",

        "ms_dialog_title": "تحميل بند طريقة عمل",
        "ms_number": "رقم MS",
        "ms_title": "العنوان",
        "element_type": "نوع العنصر",
        "discipline": "التخصص",
        "extract": "استخراج البنود",
        "extracting": "جاري الاستخراج...",
        "extracted": "تم استخراج",
        "confirm_save": "تأكيد وحفظ",
        "ms_saved": "تم الحفظ",
        "ms_upload_file": "اختر ملف (PDF/DOCX/TXT)",
        "upload_first": "اختر ملفاً أولاً.",
        "error_prefix": "خطأ: ",

        "severity_low": "منخفض", "severity_medium": "متوسط",
        "severity_high": "عالي", "severity_critical": "حرج",
        "element_column": "عمود", "element_beam": "كمرة",
        "element_slab": "بلاطة", "element_wall": "حائط",
        "element_foundation": "أساس", "element_finishing": "تشطيبات",
        "discipline_structural": "إنشائي",
        "discipline_arch": "معماري",
        "discipline_mep": "كهروميكانيكي",
        "zone_general": "عام",
        "lang_button": "English",
    },
}


def _lang():
    return LANG["code"]


def _t(key):
    return T[_lang()].get(key, key)


def _is_rtl():
    return _lang() == "ar"


def _toggle_lang():
    LANG["code"] = "ar" if LANG["code"] == "en" else "en"
    ui.run_javascript('window.location.reload()')


def _element_options():
    return {
        "column": _t("element_column"),
        "beam": _t("element_beam"),
        "slab": _t("element_slab"),
        "wall": _t("element_wall"),
        "foundation": _t("element_foundation"),
        "finishing": _t("element_finishing"),
    }


def _discipline_options():
    return {
        "Structural": _t("discipline_structural"),
        "Architectural": _t("discipline_arch"),
        "MEP": _t("discipline_mep"),
    }


def _zone_options():
    return {"A": "A", "B": "B", "C": "C", "D": "D",
            "General": _t("zone_general")}


def _severity_options():
    return {
        "Low": _t("severity_low"),
        "Medium": _t("severity_medium"),
        "High": _t("severity_high"),
        "Critical": _t("severity_critical"),
    }


# =====================================================================
# THEME + GLOBAL CSS
# =====================================================================
def _inject_theme():
    rtl = "rtl" if _is_rtl() else "ltr"
    html = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">

<style>
  :root {
    --bg: #f7f7f5;
    --surface: #ffffff;
    --text: #0a0a0a;
    --text-soft: #525252;
    --muted: #8b8b8b;
    --border: #ececec;
    --primary: #0a0a0a;
    --primary-hover: #1f1f1f;
    --success: #059669;
    --danger: #dc2626;
    --warn: #d97706;
    --radius: 14px;
    --shadow-sm: 0 1px 2px rgba(0,0,0,0.04), 0 1px 3px rgba(0,0,0,0.06);
    --shadow: 0 2px 4px rgba(0,0,0,0.04), 0 4px 12px rgba(0,0,0,0.06);
  }

  html, body {
    background: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI',
                 Roboto, Helvetica, Arial, sans-serif !important;
    font-size: 15px;
    line-height: 1.5;
    -webkit-font-smoothing: antialiased;
    letter-spacing: -0.005em;
    overflow-x: hidden !important;
    direction: __DIR__;
  }

  .nicegui-content {
    padding: 0 !important;
    max-width: 100vw !important;
    overflow-x: hidden !important;
  }

  .q-page, .q-layout, .q-page-container {
    max-width: 100vw !important;
    overflow-x: hidden !important;
    background: var(--bg) !important;
  }

  /* ---- Buttons ---- */
  .q-btn {
    border-radius: 12px !important;
    box-shadow: var(--shadow-sm) !important;
    text-transform: none !important;
    font-weight: 600 !important;
    letter-spacing: -0.01em !important;
    min-height: 44px !important;
    padding: 0 18px !important;
    font-size: 14px !important;
    transition: all 0.15s ease !important;
  }
  .q-btn:hover {
    box-shadow: var(--shadow) !important;
    transform: translateY(-1px);
  }

  .btn-primary {
    background: var(--primary) !important;
    color: #ffffff !important;
  }
  .btn-primary:hover { background: var(--primary-hover) !important; }

  .btn-soft {
    background: #ffffff !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
  }

  .btn-success {
    background: var(--success) !important;
    color: #ffffff !important;
  }

  /* ---- Inputs ---- */
  .q-field--outlined .q-field__control {
    border-radius: 12px !important;
    background: #ffffff !important;
  }
  .q-field--outlined .q-field__control:before {
    border-color: var(--border) !important;
  }
  .q-field--outlined.q-field--focused .q-field__control:after {
    border-color: var(--primary) !important;
  }
  .q-field__label { color: var(--muted) !important; font-weight: 500; }

  /* ---- Cards / surfaces ---- */
  .card {
    background: var(--surface);
    border-radius: var(--radius);
    box-shadow: var(--shadow-sm);
    border: 1px solid var(--border);
    padding: 20px;
    width: 100%;
    box-sizing: border-box;
  }

  .item-box {
    background: #ffffff;
    border-radius: 12px;
    border: 1px solid var(--border);
    padding: 14px 16px;
    margin-bottom: 10px;
    width: 100%;
    box-sizing: border-box;
  }

  /* ---- Typography ---- */
  .h1 { font-size: 22px; font-weight: 800; color: var(--text);
        letter-spacing: -0.02em; }
  .h2 { font-size: 17px; font-weight: 700; color: var(--text);
        letter-spacing: -0.01em; }
  .h3 { font-size: 15px; font-weight: 600; color: var(--text); }
  .muted { color: var(--muted); font-size: 13px; }
  .soft { color: var(--text-soft); font-size: 13px; }

  /* ---- Drawer ---- */
  .q-drawer {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
  }

  /* ---- Tabs (bottom nav) ---- */
  .bottom-nav {
    position: fixed;
    bottom: 0; left: 0; right: 0;
    background: var(--surface);
    border-top: 1px solid var(--border);
    display: flex;
    justify-content: space-around;
    padding: 6px 0 calc(6px + env(safe-area-inset-bottom, 0px)) 0;
    z-index: 1000;
  }
  .bottom-nav-item {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 8px 4px;
    color: var(--muted);
    cursor: pointer;
    border: none;
    background: transparent;
    font-size: 11px;
    font-weight: 600;
    gap: 3px;
    transition: color 0.15s;
  }
  .bottom-nav-item.active {
    color: var(--primary);
  }
  .bottom-nav-item .q-icon { font-size: 22px; }

  /* Main content padding for bottom nav */
  .main-content {
    padding: 16px;
    padding-bottom: 100px;
    max-width: 720px;
    margin: 0 auto;
    width: 100%;
    box-sizing: border-box;
  }

  /* Header */
  .app-header {
    position: sticky;
    top: 0;
    background: rgba(247,247,245,0.9);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border-bottom: 1px solid var(--border);
    padding: 12px 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    z-index: 900;
    width: 100%;
    box-sizing: border-box;
  }
  .app-header .brand {
    font-weight: 800;
    font-size: 17px;
    letter-spacing: -0.02em;
    color: var(--text);
  }

  /* Drop zone */
  .drop-zone {
    border: 2px dashed #d4d4d4;
    border-radius: 16px;
    padding: 40px 20px;
    text-align: center;
    background: #ffffff;
    transition: border-color 0.2s, background 0.2s;
    cursor: pointer;
  }
  .drop-zone:hover {
    border-color: var(--primary);
    background: #fafafa;
  }

  /* Notification */
  .q-notification {
    border-radius: 12px !important;
    box-shadow: var(--shadow) !important;
    font-weight: 600 !important;
  }
</style>
""".replace("__DIR__", rtl)
    ui.add_head_html(html)


# Button style constants
BTN_PRIMARY = "btn-primary"
BTN_SOFT = "btn-soft"
BTN_SUCCESS = "btn-success"


# =====================================================================
# MAIN BUILDER
# =====================================================================
def build_defect_ui():
    _inject_theme()

    state = {
        "project": db.get_project(),
        "tab": {"value": "new"},
    }

    # ---- Left drawer ----
    with ui.left_drawer(value=False, bordered=False).style(
        "background:#ffffff;width:320px;max-width:90vw;"
    ) as drawer:
        _build_drawer(state, drawer)

    # ---- Header ----
    with ui.element('div').style(
        "position:sticky;top:0;z-index:900;width:100%;"
    ).classes("app-header"):
        with ui.element('div').style(
            "display:flex;align-items:center;gap:10px;"
        ):
            ui.button(icon="menu",
                      on_click=drawer.toggle).props(
                "flat round dense"
            ).style("color:#0a0a0a;")
            ui.label(_t("app_title")).classes("brand")
        ui.button(_t("lang_button"), on_click=_toggle_lang).props(
            "flat dense no-caps"
        ).style("color:#0a0a0a;font-weight:600;min-height:36px;"
                "font-size:13px;")

    # ---- Main content ----
    content = ui.element('div').classes("main-content")

    def render_main():
        content.clear()
        with content:
            if state["tab"]["value"] == "new":
                _build_new_defect(state)
            else:
                _build_logs(state)

    state["render_main"] = render_main
    render_main()

    # ---- Bottom navigation ----
    with ui.element('div').classes("bottom-nav"):
        _nav_item("new", "add_a_photo", _t("new_defect"),
                  state, render_main)
        _nav_item("logs", "list_alt", _t("logs"),
                  state, render_main)


def _nav_item(key, icon, label, state, render_fn):
    active = state["tab"]["value"] == key
    cls = "bottom-nav-item active" if active else "bottom-nav-item"
    btn = ui.element('button').classes(cls)
    with btn:
        ui.icon(icon)
        ui.label(label)

    def _click():
        state["tab"]["value"] = key
        render_fn()
        # Rebuild nav highlight
        ui.run_javascript(
            "document.querySelectorAll('.bottom-nav-item').forEach"
            "(function(el,i){el.classList.remove('active');});"
        )

    btn.on("click", lambda: _click())


# =====================================================================
# DRAWER — project info + MS manager
# =====================================================================
def _build_drawer(state, drawer):
    holder = ui.element('div').style(
        "padding:16px;width:100%;box-sizing:border-box;"
    )

    def refresh():
        holder.clear()
        with holder:
            proj = state.get("project") or {}
            # Logo
            if proj.get("logo_bytes"):
                ui.image(io.BytesIO(proj["logo_bytes"])).style(
                    "width:56px;height:56px;object-fit:contain;"
                    "border-radius:12px;border:1px solid #ececec;"
                    "background:#fff;padding:6px;"
                )
            else:
                ui.element('div').style(
                    "width:56px;height:56px;border-radius:12px;"
                    "background:#f3f3f1;display:flex;align-items:center;"
                    "justify-content:center;color:#8b8b8b;"
                    "font-weight:700;font-size:18px;"
                )
                with holder:
                    pass

            if proj.get("name"):
                ui.label(proj.get("name", "")).classes("h2").style(
                    "margin-top:12px;margin-bottom:2px;"
                )
                ui.label(_t("project_info")).classes("muted")
            else:
                ui.label(_t("no_project")).classes("h2").style(
                    "margin-top:12px;"
                )

            ui.separator().style("margin:16px 0;")

            if proj.get("name"):
                _info_row(_t("contractor"), proj.get("contractor", ""))
                _info_row(_t("consultant"), proj.get("consultant", ""))
                _info_row(_t("location"), proj.get("location", ""))
                _info_row(_t("engineer"), proj.get("engineer_name", ""))
                ui.separator().style("margin:16px 0;")

            def open_setup():
                _open_setup_dialog(state, refresh, drawer)

            ui.button(_t("edit_project") if proj.get("name")
                      else _t("setup_project"),
                      on_click=open_setup,
                      icon="settings").classes(BTN_SOFT).style(
                "width:100%;"
            )

            ui.separator().style("margin:16px 0;")

            # MS section
            with ui.element('div').style(
                "display:flex;justify-content:space-between;"
                "align-items:center;margin-bottom:10px;"
            ):
                ui.label(_t("ms_section")).classes("h3")

                def open_ms():
                    _open_ms_dialog(state, refresh, drawer)

                ui.button(icon="add",
                          on_click=open_ms).props(
                    "flat round dense"
                ).style("color:#0a0a0a;")

            if not state.get("project"):
                ui.label(_t("setup_first")).classes("muted")
            else:
                ms_list = db.list_ms(state["project"]["id"])
                if not ms_list:
                    ui.label(_t("no_ms")).classes("muted")
                else:
                    for m in ms_list:
                        with ui.element('div').classes("item-box"):
                            ui.label(
                                m["ms_number"] + " — " + m["title"]
                            ).classes("h3").style("margin-bottom:2px;")
                            ui.label(
                                m["element_type"] + " · " +
                                m["discipline"] + " · " +
                                str(len(m["clauses"])) + " " +
                                _t("clauses_count")
                            ).classes("muted")

    refresh()


def _info_row(label, value):
    if not value:
        return
    with ui.element('div').style("margin-bottom:8px;"):
        ui.label(label).classes("muted").style("font-size:11px;"
                                                "text-transform:uppercase;"
                                                "letter-spacing:0.05em;")
        ui.label(str(value)).classes("h3")


# =====================================================================
# SETUP DIALOG
# =====================================================================
def _open_setup_dialog(state, refresh_drawer, drawer):
    proj = state.get("project") or {}

    with ui.dialog() as dlg, ui.card().style(
        "background:#fff;padding:24px;min-width:320px;max-width:95vw;"
        "width:440px;border-radius:20px;"
    ):
        ui.label(_t("setup_title")).classes("h1").style("margin-bottom:16px;")

        name_in = ui.input(_t("project_name"),
                            value=proj.get("name", "")).style("width:100%;")
        contractor_in = ui.input(_t("contractor"),
                                  value=proj.get("contractor", "")).style("width:100%;")
        sub_in = ui.input(_t("subcontractor"),
                           value=proj.get("subcontractor", "")).style("width:100%;")
        consultant_in = ui.input(_t("consultant"),
                                  value=proj.get("consultant", "")).style("width:100%;")
        location_in = ui.input(_t("location"),
                                value=proj.get("location", "")).style("width:100%;")
        engineer_in = ui.input(_t("engineer"),
                                value=proj.get("engineer_name", "")).style("width:100%;")

        logo_holder = {"bytes": proj.get("logo_bytes")}
        logo_lbl = ui.label(_t("logo_loaded") if logo_holder["bytes"]
                             else _t("upload_logo")).classes("muted")

        async def handle_logo(e):
            logo_holder["bytes"] = await e.file.read()
            logo_lbl.set_text(_t("logo_loaded"))

        ui.upload(on_upload=handle_logo, auto_upload=True).style(
            "width:100%;"
        ).props("flat bordered accept=image/* label='" +
                _t("upload_logo") + "'")
        logo_lbl

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
            # Also save subcontractor separately if the DB supports it
            try:
                db.save_subcontractor(sub_in.value.strip())
            except Exception:
                pass
            state["project"] = db.get_project()
            ui.notify("Saved.", type="positive")
            dlg.close()
            refresh_drawer()
            state["render_main"]()

        with ui.element('div').style(
            "display:flex;gap:8px;margin-top:16px;"
        ):
            ui.button(_t("save_project"), on_click=save).classes(
                BTN_PRIMARY
            ).style("flex:1;")
            ui.button(_t("cancel_btn"), on_click=dlg.close).classes(
                BTN_SOFT
            )

    dlg.open()


# =====================================================================
# MS UPLOAD DIALOG
# =====================================================================
def _open_ms_dialog(state, refresh_drawer, drawer):
    if not state.get("project"):
        ui.notify(_t("setup_first"), type="warning")
        return

    with ui.dialog() as dlg, ui.card().style(
        "background:#fff;padding:24px;min-width:320px;max-width:95vw;"
        "width:480px;border-radius:20px;"
    ):
        ui.label(_t("ms_dialog_title")).classes("h1").style(
            "margin-bottom:16px;"
        )

        holder = {"bytes": None, "name": ""}
        file_lbl = ui.label(_t("ms_upload_file")).classes("muted")

        async def handle_file(e):
            holder["bytes"] = await e.file.read()
            holder["name"] = e.file.name
            file_lbl.set_text(e.file.name + " (" +
                              str(len(holder["bytes"]) // 1024) + " KB)")

        ui.upload(on_upload=handle_file, auto_upload=True).style(
            "width:100%;"
        ).props("flat bordered accept=.pdf,.docx,.doc,.txt,.md "
                "label='" + _t("ms_upload_file") + "'")
        file_lbl

        ms_num_in = ui.input(_t("ms_number"), value="MS-01").style(
            "width:100%;"
        )
        title_in = ui.input(_t("ms_title")).style("width:100%;")
        element_in = ui.select(_element_options(), value="column",
                                label=_t("element_type")).style("width:100%;")
        disc_in = ui.select(_discipline_options(), value="Structural",
                             label=_t("discipline")).style("width:100%;")

        preview = ui.element('div').style("width:100%;margin-top:12px;")

        async def extract():
            if not holder["bytes"]:
                ui.notify(_t("upload_first"), type="warning")
                return
            preview.clear()
            with preview:
                ui.label(_t("extracting")).classes("muted")
            result = await svc.extract_clauses_from_pdf(
                holder["bytes"], call_gemini_json, holder["name"]
            )
            preview.clear()

            if result.get("error"):
                with preview:
                    ui.label(_t("error_prefix") +
                             str(result["error"])).style(
                        "color:#dc2626;font-size:13px;"
                    )
                return

            clauses = result["clauses"]

            with preview:
                ui.label(_t("extracted") + " " + str(len(clauses)) +
                          " " + _t("clauses_count")).classes("h3")
                for cl in clauses[:6]:
                    with ui.element('div').classes("item-box"):
                        ui.label("§" + cl["id"] + " — " + cl["title"]).style(
                            "font-weight:600;font-size:13px;"
                        )
                        ui.label(cl["text"][:120]).classes("muted")
                if len(clauses) > 6:
                    ui.label("... +" + str(len(clauses) - 6)).classes("muted")

                def confirm():
                    db.save_ms(
                        project_id=state["project"]["id"],
                        ms_number=ms_num_in.value.strip(),
                        title=title_in.value.strip(),
                        element_type=element_in.value,
                        discipline=disc_in.value,
                        pdf_bytes=holder["bytes"],
                        clauses=clauses,
                    )
                    ui.notify(_t("ms_saved"), type="positive")
                    dlg.close()
                    refresh_drawer()

                ui.button(_t("confirm_save"), on_click=confirm).classes(
                    BTN_SUCCESS
                ).style("width:100%;margin-top:8px;")

        with ui.element('div').style(
            "display:flex;gap:8px;margin-top:16px;"
        ):
            ui.button(_t("extract"), on_click=extract).classes(
                BTN_PRIMARY
            ).style("flex:1;")
            ui.button(_t("cancel_btn"), on_click=dlg.close).classes(
                BTN_SOFT
            )

        preview

    dlg.open()


# =====================================================================
# NEW DEFECT — wizard
# =====================================================================
def _build_new_defect(state):
    stage = {
        "photo": None,
        "mime": None,
        "candidates": None,
        "manual": [],
    }

    container = ui.element('div').style("width:100%;")
    state["_wizard_stage"] = stage
    state["_wizard_container"] = container

    def render():
        container.clear()
        with container:
            _render_wizard(state, stage, render)

    render()


def _render_wizard(state, stage, render_fn):
    if not state.get("project"):
        with ui.element('div').classes("card").style("text-align:center;"):
            ui.icon("info").style("font-size:36px;color:#8b8b8b;")
            ui.label(_t("setup_first")).classes("h3").style(
                "margin-top:8px;"
            )
            ui.label(_t("no_project")).classes("muted")
        return

    # ---- Header card (always visible) ----
    with ui.element('div').classes("card").style("margin-bottom:14px;"):
        ui.label(_t("photo_title")).classes("h1").style("margin-bottom:4px;")
        ui.label(_t("photo_sub")).classes("muted").style(
            "margin-bottom:14px;"
        )

        photo_holder = {"bytes": stage["photo"], "mime": stage["mime"]}

        if not stage["photo"]:
            # Drop zone
            with ui.element('div').classes("drop-zone").on(
                "click", lambda: None
            ):
                ui.icon("add_a_photo").style(
                    "font-size:44px;color:#0a0a0a;display:block;"
                    "margin-bottom:8px;"
                )
                ui.label(_t("choose_photo")).classes("h3")
        else:
            ui.image(io.BytesIO(stage["photo"])).style(
                "width:100%;max-height:340px;object-fit:cover;"
                "border-radius:14px;border:1px solid #ececec;"
            )
            ui.button(_t("change_photo"), icon="edit",
                      on_click=lambda: _reset_photo(stage, render_fn)
                      ).classes(BTN_SOFT).style(
                "margin-top:10px;"
            )

        # File input (always present, hidden behind the drop zone)
        async def handle_photo(e):
            data = await e.file.read()
            stage["photo"] = data
            stage["mime"] = ("image/jpeg"
                             if e.file.name.lower().endswith((".jpg", ".jpeg"))
                             else "image/png")
            stage["candidates"] = None
            stage["manual"] = []
            render_fn()

        ui.upload(on_upload=handle_photo, auto_upload=True).style(
            "width:100%;margin-top:10px;"
        ).props("flat bordered accept=image/* label='" +
                (_t("change_photo") if stage["photo"]
                 else _t("choose_photo")) + "'")

    # ---- Stage 2 — note + analyze ----
    if stage["photo"] and stage["candidates"] is None:
        with ui.element('div').classes("card"):
            note_in = ui.textarea(
                label=_t("note_label"),
                placeholder=_t("note_placeholder")
            ).style("width:100%;")
            with ui.element('div').style(
                "display:grid;grid-template-columns:1fr 1fr;gap:10px;"
                "margin-top:10px;"
            ):
                zone_in = ui.select(_zone_options(), value="A",
                                     label=_t("zone"))
                element_in = ui.select(_element_options(), value="column",
                                        label=_t("element"))

            analyze_btn = ui.button(_t("analyze"), icon="auto_awesome")

            async def do_analyze():
                ms_clauses = db.get_clauses_for_element(
                    state["project"]["id"], element_in.value
                )
                analyze_btn.props("loading")
                analyze_btn.set_text(_t("analyzing"))
                result = await svc.analyze_defect_photo(
                    photo_bytes=stage["photo"],
                    mime_type=stage["mime"],
                    note=note_in.value or "",
                    ms_clauses=ms_clauses,
                    element_type=element_in.value,
                    call_gemini_json_fn=call_gemini_json,
                )
                analyze_btn.props(remove="loading")
                analyze_btn.set_text(_t("analyze"))

                if result.get("error"):
                    ui.notify(result["error"], type="negative")
                    return
                stage["candidates"] = list(result["defects"])
                stage["manual"] = []
                stage["note"] = note_in.value or ""
                stage["zone"] = zone_in.value
                stage["element"] = element_in.value
                for c in stage["candidates"]:
                    c["_sel"] = True
                    c["_manual"] = False
                render_fn()

            analyze_btn.on("click", lambda: None)
            analyze_btn.classes(BTN_PRIMARY).style(
                "width:100%;margin-top:14px;"
            )
            # Reattach click handler properly
            analyze_btn._props["onClick"] = None
            analyze_btn.on("click", do_analyze, [])

    # ---- Stage 3 — candidates + notice ----
    if stage["photo"] and stage["candidates"] is not None:
        _render_candidates(state, stage, render_fn)


def _reset_photo(stage, render_fn):
    stage["photo"] = None
    stage["mime"] = None
    stage["candidates"] = None
    stage["manual"] = []
    render_fn()


def _render_candidates(state, stage, render_fn):
    all_items = stage["candidates"] + stage["manual"]

    with ui.element('div').classes("card").style("margin-bottom:14px;"):
        if stage["candidates"]:
            ui.label(_t("ai_found")).classes("h3").style(
                "margin-bottom:14px;"
            )
        else:
            ui.label(_t("ai_found_none")).classes("h3").style(
                "margin-bottom:14px;"
            )

        for c in list(all_items):
            _render_defect_card(c, stage, render_fn)

        def _open_add():
            _open_add_dialog(stage, render_fn)

        ui.button(_t("add_manual"), icon="add",
                  on_click=_open_add).classes(BTN_SOFT).style(
            "width:100%;margin-top:6px;"
        )

    # Notice details
    with ui.element('div').classes("card"):
        ui.label(_t("notice_details")).classes("h1").style(
            "margin-bottom:14px;"
        )

        sub_in = ui.input(
            _t("send_to"),
            value=state["project"].get("subcontractor", "") or "",
            placeholder=_t("send_to_placeholder")
        ).style("width:100%;")

        with ui.element('div').style(
            "display:grid;grid-template-columns:1fr 1fr;gap:10px;"
            "margin-top:10px;"
        ):
            deadline_in = ui.select(
                {"1": "1 " + _t("days"),
                 "2": "2 " + _t("days"),
                 "3": "3 " + _t("days"),
                 "5": "5 " + _t("days"),
                 "7": "7 " + _t("days"),
                 "14": "14 " + _t("days")},
                value="3", label=_t("deadline")
            )
            raise_in = ui.select(
                {"qc_internal": _t("qc_internal"),
                 "consultant": _t("consultant_ncr")},
                value="qc_internal", label=_t("raised_as")
            )

        gen_btn = ui.button(_t("generate_pdf"), icon="picture_as_pdf")

        def do_generate():
            selected = [c for c in all_items if c.get("_sel", True)]
            if not selected:
                ui.notify(_t("tick_one"), type="warning")
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
                    "zone": stage.get("zone", "A"),
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
                zone=stage.get("zone", "A"),
                subcontractor=sub_in.value.strip(),
                deadline_days=int(deadline_in.value),
                raise_type=raise_in.value,
                photo_bytes=stage["photo"],
                note=stage.get("note", ""),
                selected=clean_selected,
                notice_pdf=pdf_bytes,
            )
            ui.notify(_t("notice_saved") + " " + notice_uid,
                       type="positive")
            ui.download(pdf_bytes, filename=notice_uid + ".pdf")

            # Reset wizard
            stage["photo"] = None
            stage["mime"] = None
            stage["candidates"] = None
            stage["manual"] = []
            render_fn()

        gen_btn.on("click", lambda: None)
        gen_btn.classes(BTN_PRIMARY).style(
            "width:100%;margin-top:16px;"
        )
        gen_btn.on("click", do_generate, [])


def _render_defect_card(item, stage, render_fn):
    with ui.element('div').classes("item-box"):
        with ui.element('div').style(
            "display:flex;gap:10px;align-items:flex-start;"
        ):
            def _toggle(e):
                item["_sel"] = bool(e.value)
            ui.checkbox(value=item.get("_sel", True),
                         on_change=_toggle)
            with ui.element('div').style("flex:1;min-width:0;"):
                if item.get("_manual"):
                    tag, color = _t("tag_manual"), "#059669"
                else:
                    tag, color = _t("tag_ai"), "#2563eb"
                ui.label(tag).style(
                    "color:#fff;background:" + color + ";"
                    "font-size:9px;font-weight:800;padding:2px 7px;"
                    "border-radius:6px;letter-spacing:0.05em;"
                    "display:inline-block;margin-bottom:6px;"
                )
                ui.label(str(item.get("name", ""))).classes("h3").style(
                    "margin-bottom:4px;"
                )
                if item.get("location_hint"):
                    ui.label(str(item["location_hint"])).classes("muted")
                cit = []
                if item.get("ms_violations"):
                    cit.append("MS: " + ", ".join(item["ms_violations"]))
                if item.get("code_violations"):
                    cit.append("ECP: " + ", ".join(item["code_violations"]))
                if cit:
                    ui.label(" · ".join(cit)).classes("muted").style(
                        "font-style:italic;margin-top:2px;"
                    )
                if item.get("repair_action"):
                    ui.label(_t("repair_label") + ": " +
                             str(item["repair_action"])).classes("muted")
                sev = _severity_options().get(
                    item.get("severity", "Medium"),
                    item.get("severity", "Medium")
                )
                ui.label(sev).classes("muted").style("margin-top:4px;")

            def _remove():
                if item in stage["candidates"]:
                    stage["candidates"].remove(item)
                if item in stage["manual"]:
                    stage["manual"].remove(item)
                render_fn()

            ui.button(icon="close", on_click=_remove).props(
                "flat round dense"
            ).style("color:#8b8b8b;")


def _open_add_dialog(stage, render_fn):
    with ui.dialog() as dlg, ui.card().style(
        "background:#fff;padding:24px;min-width:320px;max-width:95vw;"
        "width:440px;border-radius:20px;"
    ):
        ui.label(_t("add_defect_title")).classes("h1").style(
            "margin-bottom:14px;"
        )
        name_in = ui.input(_t("name")).style("width:100%;")
        loc_in = ui.input(_t("location_hint")).style("width:100%;")
        sev_in = ui.select(_severity_options(), value="Medium",
                            label=_t("severity")).style("width:100%;")
        ms_in = ui.input(_t("ms_clause")).style("width:100%;")
        ecp_in = ui.input(_t("ecp_code")).style("width:100%;")
        rep_in = ui.input(_t("repair")).style("width:100%;")

        def _save():
            if not name_in.value.strip():
                ui.notify(_t("name_required"), type="warning")
                return
            stage["manual"].append({
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
            render_fn()

        with ui.element('div').style(
            "display:flex;gap:8px;margin-top:16px;"
        ):
            ui.button(_t("add"), on_click=_save).classes(
                BTN_PRIMARY
            ).style("flex:1;")
            ui.button(_t("cancel"), on_click=dlg.close).classes(BTN_SOFT)

    dlg.open()


# =====================================================================
# LOGS
# =====================================================================
def _build_logs(state):
    if not state.get("project"):
        with ui.element('div').classes("card").style("text-align:center;"):
            ui.icon("info").style("font-size:36px;color:#8b8b8b;")
            ui.label(_t("setup_first")).classes("h3").style(
                "margin-top:8px;"
            )
        return

    ui.label(_t("logs_title")).classes("h1").style("margin-bottom:4px;")
    ui.label(_t("logs_sub")).classes("muted").style("margin-bottom:16px;")

    fstate = {"filter": "all"}
    holder = ui.element('div').style("width:100%;")

    def refresh():
        holder.clear()
        rows = db.list_defects(
            state["project"]["id"],
            raise_filter=None if fstate["filter"] == "all"
            else fstate["filter"],
        )

        with holder:
            # Filter + actions
            with ui.element('div').style(
                "display:flex;gap:8px;align-items:center;"
                "margin-bottom:14px;flex-wrap:wrap;"
            ):
                filt = ui.select(
                    {"all": _t("filter_all"),
                     "qc_internal": _t("filter_qc"),
                     "consultant": _t("filter_consultant")},
                    value=fstate["filter"]
                ).style("flex:1;min-width:140px;")

                def on_filter(e):
                    fstate["filter"] = e.value
                    refresh()

                filt.on("update:model-value", on_filter)

                ui.button(icon="refresh", on_click=refresh).props(
                    "flat round dense"
                ).style("color:#0a0a0a;")

            # Counts
            if rows:
                open_count = sum(1 for r in rows
                                 if r["status"] == "open")
                ui.label(
                    str(len(rows)) + " · " + _t("open") + " " +
                    str(open_count) + " · " + _t("closed") + " " +
                    str(len(rows) - open_count)
                ).classes("muted").style("margin-bottom:12px;")

            # Export buttons
            with ui.element('div').style(
                "display:grid;grid-template-columns:1fr 1fr;"
                "gap:8px;margin-bottom:16px;"
            ):
                def export_register():
                    if not rows:
                        ui.notify(_t("no_rows"), type="warning")
                        return
                    pdf = svc.build_register_pdf(
                        state["project"], rows,
                        logo_bytes=state["project"].get("logo_bytes"),
                    )
                    ui.download(pdf, filename="defect_register.pdf")

                def export_closure():
                    if not rows:
                        ui.notify(_t("no_rows"), type="warning")
                        return
                    pdf = svc.build_closure_pdf(
                        state["project"], rows,
                        logo_bytes=state["project"].get("logo_bytes"),
                    )
                    ui.download(pdf, filename="closure_report.pdf")

                ui.button(_t("export_register"),
                          on_click=export_register).classes(
                    BTN_SOFT
                ).style("width:100%;")
                ui.button(_t("closure_report"),
                          on_click=export_closure).classes(
                    BTN_PRIMARY
                ).style("width:100%;")

            # List
            if not rows:
                ui.label(_t("no_logs")).classes("muted").style(
                    "text-align:center;padding:30px 0;"
                )
                return

            for r in rows:
                _render_log_card(r, refresh)


def _render_log_card(row, refresh_fn):
    status = row.get("status", "open")
    is_open = status == "open"
    badge_color = "#d97706" if is_open else "#059669"

    with ui.element('div').classes("card").style(
        "padding:16px;margin-bottom:10px;cursor:pointer;"
    ) as card:
        with ui.element('div').style(
            "display:flex;justify-content:space-between;"
            "align-items:flex-start;gap:10px;"
        ):
            with ui.element('div').style("flex:1;min-width:0;"):
                ui.label(row.get("uid", "")).classes("h3")
                ui.label(
                    "Zone " + str(row.get("zone", "")) + " · " +
                    str(row.get("subcontractor", ""))
                ).classes("muted")
            ui.label(
                _t("open") if is_open else _t("closed")
            ).style(
                "background:" + badge_color + ";color:#fff;"
                "font-size:10px;font-weight:800;padding:3px 9px;"
                "border-radius:20px;text-transform:uppercase;"
                "letter-spacing:0.05em;white-space:nowrap;"
            )

        def _click():
            _show_defect_dialog(row.get("id"), refresh_fn)

        card.on("click", _click)


def _show_defect_dialog(defect_id, on_close_cb):
    d = db.get_defect(defect_id)
    if not d:
        ui.notify(_t("not_found"), type="negative")
        return

    is_consultant = (d.get("raise_type") or "qc_internal") == "consultant"

    with ui.dialog() as dialog, ui.card().style(
        "background:#fff;padding:0;max-width:560px;width:95vw;"
        "border-radius:20px;overflow:hidden;"
    ):
        # Header
        with ui.element('div').style(
            "padding:20px 20px 16px;border-bottom:1px solid #ececec;"
        ):
            ui.label(_t("notice") + " " + d["uid"]).classes("h2")
            ui.label(
                "Zone " + str(d["zone"]) + " · " +
                str(d["subcontractor"])
            ).classes("muted")
            if d.get("consultant_ncr"):
                ui.label(_t("ncr_input") + ": " +
                          str(d["consultant_ncr"])).style(
                    "color:#d97706;font-size:12px;font-weight:700;"
                    "margin-top:4px;"
                )

        # Body
        with ui.element('div').style(
            "padding:20px;max-height:60vh;overflow-y:auto;"
        ):
            if d.get("photo_bytes"):
                ui.image(io.BytesIO(d["photo_bytes"])).style(
                    "width:100%;max-height:260px;object-fit:cover;"
                    "border-radius:12px;margin-bottom:14px;"
                )
            if d.get("note"):
                ui.label("📝 " + str(d["note"])).classes("soft").style(
                    "margin-bottom:14px;font-style:italic;"
                )

            for i, s in enumerate(d["selected"], 1):
                with ui.element('div').classes("item-box"):
                    ui.label(str(i) + ". " + str(s.get("name", ""))).classes(
                        "h3"
                    )
                    cit = []
                    if s.get("ms_violations"):
                        cit.append("MS: " + ", ".join(s["ms_violations"]))
                    if s.get("code_violations"):
                        cit.append("ECP: " +
                                    ", ".join(s["code_violations"]))
                    if cit:
                        ui.label(" · ".join(cit)).classes("muted").style(
                            "font-style:italic;"
                        )
                    if s.get("repair_action"):
                        ui.label(_t("repair_label") + ": " +
                                  str(s["repair_action"])).classes("muted")

        # Actions
        with ui.element('div').style(
            "padding:14px 20px 20px;border-top:1px solid #ececec;"
            "display:flex;flex-direction:column;gap:8px;"
        ):
            if d.get("notice_pdf"):
                ui.button(
                    _t("download_pdf"), icon="download",
                    on_click=lambda: ui.download(
                        d["notice_pdf"], filename=d["uid"] + ".pdf"
                    )
                ).classes(BTN_SOFT).style("width:100%;")

            if d["status"] == "open":
                ncr_in = None
                if is_consultant:
                    ncr_in = ui.input(_t("ncr_input")).style("width:100%;")

                def do_close():
                    if is_consultant:
                        if not ncr_in or not ncr_in.value.strip():
                            ui.notify(_t("ncr_required"), type="warning")
                            return
                        db.close_defect(defect_id,
                                         consultant_ncr=ncr_in.value.strip())
                    else:
                        db.close_defect(defect_id)
                    ui.notify(_t("marked_closed"), type="positive")
                    dialog.close()
                    on_close_cb()

                ui.button(_t("mark_closed"), icon="check",
                          on_click=do_close).classes(
                    BTN_PRIMARY
                ).style("width:100%;")

            ui.button(_t("close"), on_click=dialog.close).props(
                "flat"
            ).style("width:100%;color:#8b8b8b;")

    dialog.open()
