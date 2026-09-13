"""
ui/defect_page.py — Dark theme, multi-user, project switcher,
no-photo defect entry, Dashboard tab, Subcontractor master + scorecard.
"""
import io
import base64
from nicegui import ui, app

from services import defect_db as db
from services import defect_service as svc
from services.ai_service import call_gemini_json


LANG = {"code": "en"}

T = {
    "en": {
        "app_title": "Defect Notices",
        "new_defect": "New Defect", "logs": "Logs",
        "dashboard": "Dashboard", "subs": "Subs",
        "project": "Project", "no_project": "No project yet",
        "setup_project": "Set up project", "edit": "Edit",
        "contractor": "Contractor", "subcontractor": "Subcontractor",
        "consultant": "Consultant", "location": "Location",
        "engineer": "QC Engineer", "upload_logo": "Upload logo",
        "ms_section": "Method Statements", "no_ms": "No method statements yet",
        "clauses_count": "clauses",
        "photo_title": "Take a photo of the defect",
        "photo_sub": "Tap below to pick a site photo.",
        "choose_photo": "Choose photo",
        "no_photo_btn": "Raise defect without photo",
        "no_photo_title": "Defect without photo",
        "no_photo_sub": "Describe the defect you saw. AI will match it to the MS.",
        "defect_desc": "Defect description",
        "defect_desc_placeholder": "e.g. exposed rebar at column C3 base, Zone B",
        "extra_note": "Extra note (optional)",
        "extra_note_placeholder": "any additional context",
        "analyze": "Analyze with AI", "analyzing": "Analyzing...",
        "note_label": "Note (optional)",
        "note_placeholder": "e.g. crack at column C3 base",
        "zone": "Zone", "element": "Element",
        "ai_found": "AI found these defects. Untick false ones, add any missed:",
        "ai_found_none": "AI found no defects. Add one manually below.",
        "add_manual": "+ Add defect",
        "notice_details": "Notice details",
        "send_to": "Send to subcontractor",
        "send_to_placeholder": "e.g. Al-Ahram Steel Fixing",
        "deadline": "Deadline", "days": "days", "raised_as": "Raised as",
        "qc_internal": "QC Internal", "consultant_ncr": "Consultant / NCR",
        "generate_pdf": "Generate Notice PDF",
        "tick_one": "Tick at least one defect.",
        "enter_sub": "Enter the subcontractor name.",
        "notice_saved": "Notice saved",
        "setup_first": "Set up the project first.",
        "add_defect_title": "Add defect manually",
        "name": "Defect name", "location_hint": "Location hint",
        "severity": "Severity", "ms_clause": "MS clause id",
        "ecp_code": "ECP code", "repair": "Repair action",
        "add": "Add", "cancel": "Cancel",
        "name_required": "Defect name required.",
        "desc_required": "Description required.",
        "tag_ai": "AI", "tag_manual": "MANUAL",
        "tag_nophoto": "NO PHOTO",
        "mismatch_warn": "No matching MS clause",
        "logs_title": "Defect Logs", "logs_sub": "Every notice issued. Tap to view.",
        "no_logs": "No notices yet.",
        "filter_all": "All", "filter_qc": "QC Internal",
        "filter_consultant": "Consultant / NCR",
        "export_register": "Export Register", "closure_report": "Closure Report",
        "open": "Open", "closed": "Closed", "no_rows": "Nothing here yet.",
        "notice": "Notice", "download_pdf": "Download PDF",
        "mark_closed": "Mark Closed", "close": "Close",
        "ncr_input": "Consultant NCR number",
        "ncr_required": "Enter the NCR number first.",
        "marked_closed": "Marked as closed.", "not_found": "Not found.",
        "repair_label": "Repair",
        "save": "Save", "cancel_btn": "Cancel",
        "setup_title": "Project Setup", "project_name": "Project name",
        "save_project": "Save",
        "ms_dialog_title": "Upload Method Statement",
        "ms_number": "MS number", "ms_title": "Title",
        "element_type": "Element", "discipline": "Discipline",
        "extract": "Extract clauses", "extracting": "Extracting...",
        "extracted": "Extracted", "confirm_save": "Confirm & save",
        "ms_saved": "Saved", "ms_upload_file": "Choose file (PDF/DOCX/TXT)",
        "upload_first": "Choose a file first.", "error_prefix": "Error: ",
        "severity_low": "Low", "severity_medium": "Medium",
        "severity_high": "High", "severity_critical": "Critical",
        "element_column": "Column", "element_beam": "Beam",
        "element_slab": "Slab", "element_wall": "Wall",
        "element_foundation": "Foundation", "element_finishing": "Finishing",
        "discipline_structural": "Structural",
        "discipline_arch": "Architectural", "discipline_mep": "MEP",
        "zone_general": "General", "lang_button": "AR",
        "upload_failed": "Upload failed: ", "empty_file": "Empty file received.",
        "photo_received": "Photo received", "file_loaded": "File loaded: ",
        "projects_title": "Your Projects",
        "switch_project": "Switch project",
        "new_project": "New project",
        "create_first": "Create your first project",
        "no_projects_hint": "You haven't created any project yet.",
        "delete_project": "Delete project",
        "delete_confirm": "Delete this project and all its data?",
        "logout": "Log out", "signed_in_as": "Signed in as",
        "or_divider": "— OR —",
        "dash_title": "Dashboard",
        "dash_sub": "Live view of your defect register.",
        "kpi_total": "Total", "kpi_open": "Open", "kpi_closed": "Closed",
        "kpi_overdue": "Overdue", "kpi_closed_7d": "Closed 7d",
        "kpi_avg_days": "Avg days",
        "dash_zones": "Open by Zone", "dash_weeks": "Raised per Week",
        "dash_subs": "By Subcontractor",
        "dash_empty": "No defects yet — raise one from the New Defect tab.",
        "no_data": "No data yet.",
        "col_name": "Name", "col_open": "Open", "col_overdue": "Overdue",
        "col_closed": "Closed", "col_total": "Total",
        "unassigned": "(unassigned)",
        "subs_title": "Subcontractors",
        "subs_sub": "Master list and live scorecard per subcontractor.",
        "add_sub": "Add subcontractor",
        "add_sub_title": "Add subcontractor",
        "sub_name": "Subcontractor name",
        "sub_trade": "Trade (e.g. steel fixing, masonry)",
        "sub_phone": "Phone (optional)",
        "sub_notes": "Notes (optional)",
        "sub_saved": "Subcontractor saved.",
        "sub_deleted": "Subcontractor deleted.",
        "delete_sub_confirm": "Remove this subcontractor from the master list?",
        "no_subs": "No subcontractors yet.",
        "no_subs_hint": "Add one to track their performance.",
        "view_defects": "View their defects",
        "filtered_by": "Filtered:",
        "clear_filter": "Clear",
        "from_defects": "Seen in notices",
        "sub_open": "Open", "sub_overdue": "Overdue",
        "sub_closed": "Closed", "sub_total": "Total",
        "delete_sub": "Remove",
    },
    "ar": {
        "app_title": "إشعارات العيوب", "new_defect": "عيب جديد", "logs": "السجل",
        "dashboard": "الرئيسية", "subs": "المقاولون",
        "project": "المشروع", "no_project": "لا يوجد مشروع بعد",
        "setup_project": "إعداد المشروع", "edit": "تعديل",
        "contractor": "المقاول", "subcontractor": "المقاول الفرعي",
        "consultant": "الاستشاري", "location": "الموقع",
        "engineer": "مهندس الجودة", "upload_logo": "تحميل الشعار",
        "ms_section": "بيانات طريقة العمل", "no_ms": "لا توجد بيانات طريقة بعد",
        "clauses_count": "بند",
        "photo_title": "التقط صورة للعيب",
        "photo_sub": "اضغط أدناه لاختيار صورة الموقع.",
        "choose_photo": "اختر صورة",
        "no_photo_btn": "إصدار عيب بدون صورة",
        "no_photo_title": "عيب بدون صورة",
        "no_photo_sub": "صف العيب الذي رأيته. سيطابقه الذكاء الاصطناعي مع الـ MS.",
        "defect_desc": "وصف العيب",
        "defect_desc_placeholder": "مثال: حديد مكشوف عند قاعدة العمود C3، منطقة B",
        "extra_note": "ملاحظة إضافية (اختياري)",
        "extra_note_placeholder": "أي سياق إضافي",
        "analyze": "تحليل بالذكاء الاصطناعي", "analyzing": "جاري التحليل...",
        "note_label": "ملاحظة (اختياري)",
        "note_placeholder": "مثال: شرخ عند قاعدة العمود C3",
        "zone": "المنطقة", "element": "العنصر",
        "ai_found": "وجد الذكاء الاصطناعي هذه العيوب. أزل غير الصحيحة وأضف أي مفقود:",
        "ai_found_none": "لم يجد الذكاء الاصطناعي عيوباً. أضف عيباً يدوياً أدناه.",
        "add_manual": "+ إضافة عيب", "notice_details": "تفاصيل الإشعار",
        "send_to": "إرسال إلى المقاول الفرعي",
        "send_to_placeholder": "مثال: الأهرام لتثبيت الحديد",
        "deadline": "المهلة", "days": "أيام", "raised_as": "مصدر الإشعار",
        "qc_internal": "داخلي QC", "consultant_ncr": "استشاري / NCR",
        "generate_pdf": "إنشاء إشعار PDF",
        "tick_one": "اختر عيباً واحداً على الأقل.",
        "enter_sub": "أدخل اسم المقاول الفرعي.",
        "notice_saved": "تم حفظ الإشعار", "setup_first": "أعدّ المشروع أولاً.",
        "add_defect_title": "إضافة عيب يدوياً", "name": "اسم العيب",
        "location_hint": "الموقع التقريبي", "severity": "الخطورة",
        "ms_clause": "رقم بند MS", "ecp_code": "كود ECP",
        "repair": "إجراء الإصلاح", "add": "إضافة", "cancel": "إلغاء",
        "name_required": "اسم العيب مطلوب.",
        "desc_required": "الوصف مطلوب.",
        "tag_ai": "ذكاء اصطناعي", "tag_manual": "يدوي",
        "tag_nophoto": "بدون صورة",
        "mismatch_warn": "لا يوجد بند MS مطابق",
        "logs_title": "سجل العيوب", "logs_sub": "كل إشعار صدر. اضغط للعرض.",
        "no_logs": "لا توجد إشعارات بعد.",
        "filter_all": "الكل", "filter_qc": "داخلي QC",
        "filter_consultant": "استشاري / NCR",
        "export_register": "تصدير السجل", "closure_report": "تقرير الإغلاق",
        "open": "مفتوح", "closed": "مغلق", "no_rows": "لا يوجد شيء بعد.",
        "notice": "إشعار", "download_pdf": "تحميل PDF",
        "mark_closed": "تعليم كمغلق", "close": "إغلاق",
        "ncr_input": "رقم NCR الاستشاري",
        "ncr_required": "أدخل رقم NCR أولاً.",
        "marked_closed": "تم التعليم كمغلق.", "not_found": "غير موجود.",
        "repair_label": "الإصلاح", "save": "حفظ", "cancel_btn": "إلغاء",
        "setup_title": "إعداد المشروع", "project_name": "اسم المشروع",
        "save_project": "حفظ", "ms_dialog_title": "تحميل بند طريقة عمل",
        "ms_number": "رقم MS", "ms_title": "العنوان", "element_type": "العنصر",
        "discipline": "التخصص", "extract": "استخراج البنود",
        "extracting": "جاري الاستخراج...", "extracted": "تم استخراج",
        "confirm_save": "تأكيد وحفظ", "ms_saved": "تم الحفظ",
        "ms_upload_file": "اختر ملف (PDF/DOCX/TXT)",
        "upload_first": "اختر ملفاً أولاً.", "error_prefix": "خطأ: ",
        "severity_low": "منخفض", "severity_medium": "متوسط",
        "severity_high": "عالي", "severity_critical": "حرج",
        "element_column": "عمود", "element_beam": "كمرة",
        "element_slab": "بلاطة", "element_wall": "حائط",
        "element_foundation": "أساس", "element_finishing": "تشطيبات",
        "discipline_structural": "إنشائي", "discipline_arch": "معماري",
        "discipline_mep": "كهروميكانيكي", "zone_general": "عام",
        "lang_button": "EN",
        "upload_failed": "فشل التحميل: ", "empty_file": "الملف فارغ.",
        "photo_received": "تم استلام الصورة", "file_loaded": "تم تحميل الملف: ",
        "projects_title": "مشاريعك", "switch_project": "تبديل المشروع",
        "new_project": "مشروع جديد",
        "create_first": "أنشئ مشروعك الأول",
        "no_projects_hint": "لم تنشئ أي مشروع بعد.",
        "delete_project": "حذف المشروع",
        "delete_confirm": "حذف هذا المشروع وكل بياناته؟",
        "logout": "تسجيل الخروج", "signed_in_as": "مسجل الدخول كـ",
        "or_divider": "— أو —",
        "dash_title": "الرئيسية",
        "dash_sub": "عرض مباشر لسجل العيوب.",
        "kpi_total": "الإجمالي", "kpi_open": "مفتوح", "kpi_closed": "مغلق",
        "kpi_overdue": "متأخر", "kpi_closed_7d": "أُغلق ٧ أيام",
        "kpi_avg_days": "متوسط الأيام",
        "dash_zones": "المفتوح حسب المنطقة", "dash_weeks": "المُصدر أسبوعياً",
        "dash_subs": "حسب المقاول الفرعي",
        "dash_empty": "لا توجد عيوب بعد — أصدر واحداً من تاب عيب جديد.",
        "no_data": "لا توجد بيانات بعد.",
        "col_name": "الاسم", "col_open": "مفتوح", "col_overdue": "متأخر",
        "col_closed": "مغلق", "col_total": "الإجمالي",
        "unassigned": "(غير معين)",
        "subs_title": "المقاولون الفرعيون",
        "subs_sub": "القائمة الرئيسية ولوحة الأداء لكل مقاول فرعي.",
        "add_sub": "إضافة مقاول فرعي",
        "add_sub_title": "إضافة مقاول فرعي",
        "sub_name": "اسم المقاول الفرعي",
        "sub_trade": "التخصص (مثال: تثبيت حديد، مباني)",
        "sub_phone": "هاتف (اختياري)",
        "sub_notes": "ملاحظات (اختياري)",
        "sub_saved": "تم حفظ المقاول الفرعي.",
        "sub_deleted": "تم حذف المقاول الفرعي.",
        "delete_sub_confirm": "حذف هذا المقاول الفرعي من القائمة الرئيسية؟",
        "no_subs": "لا يوجد مقاولون فرعيون بعد.",
        "no_subs_hint": "أضف واحداً لتتبع أدائه.",
        "view_defects": "عرض عيوبه",
        "filtered_by": "مفلتر بـ:",
        "clear_filter": "مسح",
        "from_defects": "ظهر في الإشعارات",
        "sub_open": "مفتوح", "sub_overdue": "متأخر",
        "sub_closed": "مغلق", "sub_total": "الإجمالي",
        "delete_sub": "حذف",
    },
}


def _lang(): return LANG["code"]
def _t(k): return T[_lang()].get(k, k)
def _is_rtl(): return _lang() == "ar"


def _toggle_lang():
    LANG["code"] = "ar" if LANG["code"] == "en" else "en"
    ui.run_javascript('window.location.reload()')


def _element_options():
    return {"column": _t("element_column"), "beam": _t("element_beam"),
            "slab": _t("element_slab"), "wall": _t("element_wall"),
            "foundation": _t("element_foundation"),
            "finishing": _t("element_finishing")}


def _discipline_options():
    return {"Structural": _t("discipline_structural"),
            "Architectural": _t("discipline_arch"),
            "MEP": _t("discipline_mep")}


def _zone_options():
    return {"A": "A", "B": "B", "C": "C", "D": "D",
            "General": _t("zone_general")}


def _severity_options():
    return {"Low": _t("severity_low"), "Medium": _t("severity_medium"),
            "High": _t("severity_high"), "Critical": _t("severity_critical")}


# =====================================================================
# THEME
# =====================================================================
def _inject_theme():
    rtl = "rtl" if _is_rtl() else "ltr"
    html = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #0a0a0a; --surface: #141414; --surface-2: #1a1a1a;
    --border: #262626; --border-soft: #1f1f1f;
    --text: #fafafa; --text-soft: #d4d4d4;
    --muted: #a3a3a3; --muted-2: #737373;
    --violet: #a855f7; --violet-soft: #7c3aed;
    --green: #10b981; --amber: #f59e0b; --red: #ef4444;
  }
  html, body { background: var(--bg) !important; color: var(--text) !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI',
                 Roboto, Helvetica, Arial, sans-serif !important;
    font-size: 15px; line-height: 1.55; -webkit-font-smoothing: antialiased;
    overflow-x: hidden !important; direction: __DIR__; }
  .nicegui-content { padding: 0 !important; max-width: 100vw !important;
                     overflow-x: hidden !important; }
  .q-page, .q-layout, .q-page-container { max-width: 100vw !important;
    overflow-x: hidden !important; background: var(--bg) !important; }
  .q-btn { border-radius: 10px !important; text-transform: none !important;
           font-weight: 600 !important; min-height: 42px !important;
           padding: 0 16px !important; font-size: 14px !important; }
  .btn-primary { background: var(--violet) !important; color: #fff !important; }
  .btn-soft { background: var(--surface-2) !important; color: var(--text) !important;
              border: 1px solid var(--border) !important; }
  .btn-success { background: var(--green) !important; color: #fff !important; }
  .btn-outline { background: transparent !important; color: var(--text) !important;
                 border: 1px dashed #3a3a3a !important; }
  .btn-outline:hover { border-color: var(--violet) !important;
                       background: #1c1a1f !important; }
  .q-field--outlined .q-field__control { border-radius: 10px !important;
    background: var(--surface-2) !important; }
  .q-field--outlined .q-field__control:before { border-color: var(--border) !important; }
  .q-field--outlined.q-field--focused .q-field__control:after { border-color: var(--violet) !important; }
  .q-field__label, .q-field__native, .q-field__input { color: var(--text) !important; }
  .q-field__label { color: var(--muted) !important; }
  .card { background: var(--surface); border-radius: 12px; border: 1px solid var(--border);
          padding: 20px; width: 100%; box-sizing: border-box; }
  .item-box { background: var(--surface-2); border-radius: 10px;
              border: 1px solid var(--border-soft); padding: 14px 16px;
              margin-bottom: 10px; width: 100%; box-sizing: border-box; }
  .h1 { font-size: 22px; font-weight: 800; color: var(--text); letter-spacing: -0.025em; }
  .h2 { font-size: 17px; font-weight: 700; color: var(--text); }
  .h3 { font-size: 14px; font-weight: 600; color: var(--text); }
  .muted { color: var(--muted); font-size: 13px; }
  .soft { color: var(--text-soft); font-size: 13px; }
  .mono-lg { font-family: 'JetBrains Mono', monospace !important; font-weight: 600 !important;
             font-size: 14px !important; color: var(--text) !important; }
  .mono-sm { font-family: 'JetBrains Mono', monospace !important; font-weight: 400 !important;
             font-size: 11.5px !important; color: var(--muted) !important; }
  .q-drawer { background: var(--bg) !important; border-right: 1px solid var(--border) !important; }
  .bottom-nav { position: fixed; bottom: 0; left: 0; right: 0;
                background: rgba(10,10,10,0.95); backdrop-filter: blur(14px);
                -webkit-backdrop-filter: blur(14px); border-top: 1px solid var(--border);
                display: flex; justify-content: space-around;
                padding: 6px 0 calc(6px + env(safe-area-inset-bottom, 0px)) 0; z-index: 1000; }
  .bottom-nav-item { flex: 1; display: flex; flex-direction: column; align-items: center;
                     padding: 8px 4px; color: var(--muted-2); cursor: pointer;
                     border: none; background: transparent; font-size: 11px;
                     font-weight: 600; gap: 3px; font-family: inherit; }
  .bottom-nav-item.active { color: var(--text); }
  .bottom-nav-item.active .q-icon { color: var(--violet); }
  .bottom-nav-item .q-icon { font-size: 22px; }
  .main-content { padding: 16px; padding-bottom: 100px; max-width: 720px;
                  margin: 0 auto; width: 100%; box-sizing: border-box; }
  .app-header { position: sticky; top: 0; background: rgba(10,10,10,0.85);
                backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
                border-bottom: 1px solid var(--border); padding: 12px 16px;
                display: flex; align-items: center; justify-content: space-between;
                z-index: 900; width: 100%; box-sizing: border-box; }
  .app-header .brand { font-weight: 700; font-size: 15px; color: var(--text); }
  .q-uploader { background: var(--surface-2) !important; border: 1.5px dashed #333 !important;
                border-radius: 14px !important; width: 100% !important;
                max-width: 100% !important; color: var(--text) !important; }
  .q-uploader__header { background: transparent !important; color: var(--text) !important; }
  .q-uploader__title { color: var(--text) !important; }
  .q-uploader__subtitle { color: var(--muted) !important; }
  .q-uploader .q-btn { color: var(--text) !important; }
  .q-uploader__list { background: transparent !important; }
  .q-uploader__list .q-item { background: var(--surface) !important;
                              color: var(--text) !important;
                              border-radius: 8px !important; margin: 4px !important; }
  .q-uploader__list .q-item__label { color: var(--text) !important; }
  .badge-open { display: inline-block; background: rgba(245,158,11,0.12);
                color: #fbbf24; border: 1px solid rgba(245,158,11,0.3);
                font-size: 10px; font-weight: 700; padding: 2px 8px;
                border-radius: 20px; text-transform: uppercase; }
  .badge-closed { display: inline-block; background: rgba(16,185,129,0.12);
                  color: #34d399; border: 1px solid rgba(16,185,129,0.3);
                  font-size: 10px; font-weight: 700; padding: 2px 8px;
                  border-radius: 20px; text-transform: uppercase; }
  .badge-overdue { display: inline-block; background: rgba(239,68,68,0.12);
                   color: #fca5a5; border: 1px solid rgba(239,68,68,0.3);
                   font-size: 10px; font-weight: 700; padding: 2px 8px;
                   border-radius: 20px; text-transform: uppercase; }
  .badge-ai { display: inline-block; background: rgba(168,85,247,0.15);
              color: #c4b5fd; font-size: 9px; font-weight: 800;
              padding: 2px 7px; border-radius: 6px; }
  .badge-manual { display: inline-block; background: rgba(16,185,129,0.15);
                  color: #6ee7b7; font-size: 9px; font-weight: 800;
                  padding: 2px 7px; border-radius: 6px; }
  .badge-nophoto { display: inline-block; background: rgba(59,130,246,0.15);
                   color: #93c5fd; font-size: 9px; font-weight: 800;
                   padding: 2px 7px; border-radius: 6px; letter-spacing: 0.03em; }
  .badge-mismatch { display: inline-block; background: rgba(245,158,11,0.15);
                    color: #fbbf24; font-size: 9px; font-weight: 800;
                    padding: 2px 7px; border-radius: 6px; letter-spacing: 0.03em; }
  .badge-seen { display: inline-block; background: rgba(115,115,115,0.2);
                color: #a3a3a3; font-size: 9px; font-weight: 800;
                padding: 2px 7px; border-radius: 6px; letter-spacing: 0.03em; }
  .q-notification { border-radius: 10px !important; font-weight: 600 !important;
                    background: var(--surface-2) !important; color: var(--text) !important;
                    border: 1px solid var(--border) !important; }
  .section-label { font-size: 11px; font-weight: 700; color: var(--muted-2);
                   text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 6px; }
  .q-separator { background: var(--border) !important; }
  .scroll-box { max-height: 280px; overflow-y: auto; border: 1px solid var(--border);
                border-radius: 10px; padding: 8px; margin-top: 8px;
                background: var(--surface-2); }
  .or-divider { display: flex; align-items: center; gap: 10px;
                color: var(--muted-2); font-size: 11px; font-weight: 700;
                letter-spacing: 0.1em; text-transform: uppercase;
                margin: 14px 0; }
  .or-divider::before, .or-divider::after {
    content: ''; flex: 1; height: 1px; background: var(--border);
  }
  .kpi-grid { display: grid; grid-template-columns: repeat(2, 1fr);
              gap: 10px; margin-bottom: 14px; }
  .kpi-card { background: var(--surface); border: 1px solid var(--border);
              border-radius: 12px; padding: 16px;
              display: flex; flex-direction: column; gap: 4px; }
  .kpi-num { font-family: 'JetBrains Mono', monospace !important;
             font-size: 28px; font-weight: 700; color: var(--text);
             line-height: 1; letter-spacing: -0.03em; }
  .kpi-lbl { font-size: 11px; font-weight: 700; color: var(--muted-2);
             text-transform: uppercase; letter-spacing: 0.08em; }
  .kpi-num.open { color: #fbbf24; }
  .kpi-num.closed { color: #34d399; }
  .kpi-num.overdue { color: #ef4444; }
  .kpi-num.primary { color: var(--violet); }
  .zone-row { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
  .zone-name { font-family: 'JetBrains Mono', monospace; font-weight: 600;
               font-size: 13px; color: var(--text); width: 40px; }
  .zone-bar-wrap { flex: 1; height: 8px; background: var(--surface-2);
                   border-radius: 4px; overflow: hidden; }
  .zone-bar { height: 100%; background: var(--violet);
              border-radius: 4px; transition: width 0.3s ease; }
  .zone-count { font-family: 'JetBrains Mono', monospace; font-size: 12px;
                color: var(--muted); min-width: 24px; text-align: right; }
  .week-bars { display: flex; align-items: flex-end; gap: 6px;
               height: 100px; padding: 8px 0; margin-top: 8px; }
  .week-col { flex: 1; display: flex; flex-direction: column;
              align-items: center; gap: 6px; height: 100%;
              justify-content: flex-end; }
  .week-bar { width: 100%; background: linear-gradient(180deg,
              #a855f7 0%, #7c3aed 100%); border-radius: 4px 4px 0 0;
              min-height: 2px; transition: height 0.3s ease; }
  .week-lbl { font-size: 10px; color: var(--muted-2);
              font-family: 'JetBrains Mono', monospace; }
  .week-count { font-size: 11px; font-weight: 700; color: var(--text);
                font-family: 'JetBrains Mono', monospace; }
  .sub-card { background: var(--surface); border: 1px solid var(--border);
              border-radius: 12px; padding: 16px; margin-bottom: 10px; }
  .sub-badges { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 10px; }
  .chip { display: inline-flex; align-items: center; gap: 6px;
          background: var(--surface-2); border: 1px solid var(--border);
          color: var(--text); font-size: 12px; font-weight: 600;
          padding: 4px 10px; border-radius: 20px; }
  .chip .q-icon { font-size: 14px; }
</style>
""".replace("__DIR__", rtl)
    ui.add_head_html(html)


BTN_PRIMARY = "btn-primary"
BTN_SOFT = "btn-soft"
BTN_SUCCESS = "btn-success"
BTN_OUTLINE = "btn-outline"


# =====================================================================
# MAIN
# =====================================================================
def build_defect_ui(user_id):
    _inject_theme()

    user = db.get_user(user_id)

    state = {
        "user_id": user_id,
        "user": user,
        "project_id": app.storage.user.get("project_id"),
        "project": None,
        "tab": {"value": "new"},
        "sub_filter": None,
    }

    if state["project_id"]:
        p = db.get_project(state["project_id"])
        if not p or p.get("user_id") != user_id:
            state["project_id"] = None
            state["project"] = None
            app.storage.user.pop("project_id", None)
        else:
            state["project"] = p

    if not state["project_id"]:
        projects = db.list_projects(user_id)
        if projects:
            state["project_id"] = projects[0]["id"]
            state["project"] = projects[0]
            app.storage.user["project_id"] = projects[0]["id"]

    with ui.left_drawer(value=False, bordered=False).style(
        "background:#0a0a0a;width:320px;max-width:88vw;"
    ) as drawer:
        _build_drawer(state, drawer)

    with ui.element('div').classes("app-header"):
        with ui.element('div').style("display:flex;align-items:center;gap:10px;"):
            ui.button(icon="menu", on_click=drawer.toggle).props(
                "flat round dense").style("color:#fafafa;")
            ui.label(_t("app_title")).classes("brand")
        ui.button(_t("lang_button"), on_click=_toggle_lang).props(
            "flat dense no-caps").style(
            "color:#fafafa;font-weight:600;min-height:36px;font-size:13px;"
            "border:1px solid #262626;border-radius:8px;padding:0 12px;")

    content = ui.element('div').classes("main-content")

    def render_main():
        content.clear()
        with content:
            if not state.get("project_id"):
                _render_no_project(state, render_main)
                return
            tab = state["tab"]["value"]
            if tab == "new":
                _build_new_defect(state)
            elif tab == "logs":
                _build_logs(state)
            elif tab == "subs":
                _build_subs(state)
            else:
                _build_dashboard(state)

    state["render_main"] = render_main
    render_main()

    with ui.element('div').classes("bottom-nav"):
        _nav_item("new", "add_a_photo", _t("new_defect"),
                  state, render_main, 0)
        _nav_item("logs", "list_alt", _t("logs"),
                  state, render_main, 1)
        _nav_item("subs", "engineering", _t("subs"),
                  state, render_main, 2)
        _nav_item("dashboard", "insights", _t("dashboard"),
                  state, render_main, 3)


def _render_no_project(state, refresh_fn):
    with ui.element('div').classes("card").style("text-align:center;"):
        ui.icon("add_business").style("font-size:44px;color:#a855f7;")
        ui.label(_t("create_first")).classes("h1").style(
            "margin-top:12px;margin-bottom:6px;")
        ui.label(_t("no_projects_hint")).classes("muted")
        ui.element('div').style("height:14px;")

        def _open():
            _open_setup_dialog(state, None, is_new=True,
                                on_created=refresh_fn)

        ui.button(_t("new_project"), icon="add", on_click=_open).classes(
            BTN_PRIMARY).style("width:100%;")


def _nav_item(key, icon, label, state, render_fn, idx):
    active = state["tab"]["value"] == key
    cls = "bottom-nav-item active" if active else "bottom-nav-item"
    btn = ui.element('button').classes(cls)
    with btn:
        ui.icon(icon)
        ui.label(label)

    def _click():
        state["tab"]["value"] = key
        render_fn()
        ui.run_javascript(
            "var items=document.querySelectorAll('.bottom-nav-item');"
            "items.forEach(function(el){el.classList.remove('active');});"
            "if(items[" + str(idx) + "]){items[" + str(idx) +
            "].classList.add('active');}")

    btn.on("click", _click)


# =====================================================================
# SUBCONTRACTORS
# =====================================================================
def _build_subs(state):
    if not state.get("project_id"):
        _render_no_project(state, state["render_main"])
        return

    pid = state["project_id"]
    masters = db.list_subcontractors(pid)
    scores = db.subcontractor_scores(pid)
    scores_by_name = {s["name"]: s for s in scores}

    ui.label(_t("subs_title")).classes("h1").style("margin-bottom:4px;")
    ui.label(_t("subs_sub")).classes("muted").style("margin-bottom:16px;")

    def _open_add():
        _open_add_sub_dialog(state, state["render_main"])

    ui.button(_t("add_sub"), icon="add", on_click=_open_add).classes(
        BTN_PRIMARY).style("width:100%;margin-bottom:16px;")

    if not masters:
        with ui.element('div').classes("card").style("text-align:center;"):
            ui.icon("engineering").style("font-size:40px;color:#737373;")
            ui.label(_t("no_subs")).classes("h3").style("margin-top:10px;")
            ui.label(_t("no_subs_hint")).classes("muted").style(
                "margin-top:4px;")
        return

    for m in masters:
        name = m.get("name") or ""
        score = scores_by_name.get(name) or {
            "open": 0, "closed": 0, "overdue": 0, "total": 0}

        with ui.element('div').classes("sub-card"):
            with ui.element('div').style(
                "display:flex;justify-content:space-between;"
                "align-items:flex-start;gap:10px;"
            ):
                with ui.element('div').style("flex:1;min-width:0;"):
                    ui.label(str(name)).classes("h2").style(
                        "margin-bottom:4px;word-break:break-word;")
                    meta_bits = []
                    if m.get("trade"):
                        meta_bits.append(str(m["trade"]))
                    if m.get("phone"):
                        meta_bits.append("📞 " + str(m["phone"]))
                    if meta_bits:
                        ui.label(" · ".join(meta_bits)).classes("muted").style(
                            "font-size:12px;")
                    if not m.get("from_master"):
                        ui.html('<span class="badge-seen">' +
                                _t("from_defects") + '</span>').style(
                            "margin-top:6px;display:inline-block;")

                if m.get("id"):
                    def _del(sub_id=m["id"]):
                        _confirm_delete_sub(state, sub_id,
                                             state["render_main"])

                    ui.button(icon="delete", on_click=_del).props(
                        "flat round dense size=sm").style(
                        "color:#737373;")

            # Score badges
            with ui.element('div').classes("sub-badges"):
                if score["open"]:
                    ui.html('<span class="badge-open">' +
                            str(score["open"]) + ' ' +
                            _t("sub_open") + '</span>')
                if score["overdue"]:
                    ui.html('<span class="badge-overdue">' +
                            str(score["overdue"]) + ' ' +
                            _t("sub_overdue") + '</span>')
                if score["closed"]:
                    ui.html('<span class="badge-closed">' +
                            str(score["closed"]) + ' ' +
                            _t("sub_closed") + '</span>')
                if score["total"] == 0:
                    ui.label(_t("no_data")).classes("muted").style(
                        "font-size:11px;")

            if score["total"]:
                def _view(nm=name):
                    state["sub_filter"] = nm
                    state["tab"]["value"] = "logs"
                    state["render_main"]()
                    ui.run_javascript(
                        "var items=document.querySelectorAll("
                        "'.bottom-nav-item');"
                        "items.forEach(function(el){"
                        "el.classList.remove('active');});"
                        "if(items[1]){items[1].classList.add('active');}")

                ui.button(_t("view_defects"), icon="list_alt",
                          on_click=_view).classes(BTN_SOFT).style(
                    "width:100%;margin-top:10px;font-size:13px;"
                    "min-height:36px;")


def _open_add_sub_dialog(state, refresh_fn):
    if not state.get("project_id"):
        ui.notify(_t("setup_first"), type="warning")
        return

    with ui.dialog() as dlg, ui.card().style(
        "background:#141414;padding:24px;min-width:320px;"
        "max-width:95vw;width:440px;border-radius:16px;"
        "border:1px solid #262626;"
    ):
        ui.label(_t("add_sub_title")).classes("h1").style(
            "margin-bottom:14px;")

        name_in = ui.input(_t("sub_name")).style("width:100%;")
        trade_in = ui.input(_t("sub_trade")).style("width:100%;")
        phone_in = ui.input(_t("sub_phone")).style("width:100%;")
        notes_in = ui.input(_t("sub_notes")).style("width:100%;")

        def _save():
            if not name_in.value.strip():
                ui.notify(_t("sub_name"), type="warning")
                return
            db.add_subcontractor(
                project_id=state["project_id"],
                name=name_in.value.strip(),
                trade=trade_in.value.strip(),
                phone=phone_in.value.strip(),
                notes=notes_in.value.strip())
            ui.notify(_t("sub_saved"), type="positive")
            dlg.close()
            ui.timer(0.05, refresh_fn, once=True)

        with ui.element('div').style("display:flex;gap:8px;margin-top:16px;"):
            ui.button(_t("add"), on_click=_save).classes(
                BTN_PRIMARY).style("flex:1;")
            ui.button(_t("cancel"), on_click=dlg.close).classes(BTN_SOFT)

    dlg.open()


def _confirm_delete_sub(state, sub_id, refresh_fn):
    with ui.dialog() as dlg, ui.card().style(
        "background:#141414;padding:24px;min-width:300px;"
        "max-width:95vw;width:400px;border-radius:16px;"
        "border:1px solid #262626;"
    ):
        ui.label(_t("delete_sub_confirm")).classes("h3").style(
            "margin-bottom:14px;")

        def _yes():
            db.delete_subcontractor(sub_id)
            ui.notify(_t("sub_deleted"), type="positive")
            dlg.close()
            ui.timer(0.05, refresh_fn, once=True)

        with ui.element('div').style("display:flex;gap:8px;"):
            ui.button(_t("delete_sub"), on_click=_yes).classes(
                BTN_PRIMARY).style(
                "flex:1;background:#ef4444 !important;")
            ui.button(_t("cancel_btn"), on_click=dlg.close).classes(BTN_SOFT)

    dlg.open()


# =====================================================================
# DASHBOARD
# =====================================================================
def _build_dashboard(state):
    if not state.get("project_id"):
        _render_no_project(state, state["render_main"])
        return

    pid = state["project_id"]
    kpis = db.kpi_summary(pid)
    zones = db.kpi_per_zone(pid)
    weeks = db.kpi_per_week(pid, weeks=8)
    subs = db.subcontractor_scores(pid)

    ui.label(_t("dash_title")).classes("h1").style("margin-bottom:4px;")
    ui.label(_t("dash_sub")).classes("muted").style("margin-bottom:16px;")

    if kpis.get("total", 0) == 0:
        with ui.element('div').classes("card").style("text-align:center;"):
            ui.icon("insights").style("font-size:40px;color:#737373;")
            ui.label(_t("dash_empty")).classes("muted").style(
                "margin-top:10px;")
        return

    with ui.element('div').classes("kpi-grid"):
        _kpi_card(str(kpis["total"]), _t("kpi_total"), "")
        _kpi_card(str(kpis["open"]), _t("kpi_open"), "open")
        _kpi_card(str(kpis["closed"]), _t("kpi_closed"), "closed")
        _kpi_card(str(kpis["overdue"]), _t("kpi_overdue"), "overdue")
        _kpi_card(str(kpis["closed_7d"]), _t("kpi_closed_7d"), "closed")
        _kpi_card(str(kpis["avg_days"]), _t("kpi_avg_days"), "primary")

    if zones:
        with ui.element('div').classes("card").style("margin-bottom:14px;"):
            ui.label(_t("dash_zones")).classes("h3").style("margin-bottom:14px;")
            max_z = max(z["count"] for z in zones) or 1
            for z in zones:
                pct = int((z["count"] / float(max_z)) * 100)
                with ui.element('div').classes("zone-row"):
                    ui.label(str(z["zone"])).classes("zone-name")
                    with ui.element('div').classes("zone-bar-wrap"):
                        ui.element('div').classes("zone-bar").style(
                            "width:" + str(pct) + "%;")
                    ui.label(str(z["count"])).classes("zone-count")

    with ui.element('div').classes("card").style("margin-bottom:14px;"):
        ui.label(_t("dash_weeks")).classes("h3").style("margin-bottom:4px;")
        max_w = max((w["count"] for w in weeks), default=0) or 1
        with ui.element('div').classes("week-bars"):
            for w in weeks:
                pct = int((w["count"] / float(max_w)) * 100)
                with ui.element('div').classes("week-col"):
                    ui.label(str(w["count"])).classes("week-count")
                    ui.element('div').classes("week-bar").style(
                        "height:" + str(max(pct, 3)) + "%;")
                    ui.label(w["label"]).classes("week-lbl")

    if subs:
        with ui.element('div').classes("card"):
            ui.label(_t("dash_subs")).classes("h3").style("margin-bottom:14px;")
            for s in subs[:8]:
                name = s["name"] or _t("unassigned")
                with ui.element('div').style(
                    "display:flex;align-items:center;gap:10px;"
                    "padding:10px 0;border-bottom:1px solid #1f1f1f;"
                ):
                    with ui.element('div').style("flex:1;min-width:0;"):
                        ui.label(str(name)).classes("mono-lg").style(
                            "white-space:nowrap;overflow:hidden;"
                            "text-overflow:ellipsis;")
                    ui.html(
                        '<span class="badge-open">' + str(s["open"]) +
                        ' ' + _t("col_open") + '</span>'
                    )
                    if s["overdue"]:
                        ui.html(
                            '<span class="badge-overdue">' +
                            str(s["overdue"]) + ' ' + _t("col_overdue") +
                            '</span>'
                        )
                    ui.html(
                        '<span class="badge-closed">' + str(s["closed"]) +
                        ' ' + _t("col_closed") + '</span>'
                    )


def _kpi_card(number, label, variant):
    cls = "kpi-num"
    if variant:
        cls += " " + variant
    with ui.element('div').classes("kpi-card"):
        ui.label(str(number)).classes(cls)
        ui.label(label).classes("kpi-lbl")


# =====================================================================
# DRAWER
# =====================================================================
def _build_drawer(state, drawer):
    holder = ui.element('div').style(
        "padding:20px;width:100%;box-sizing:border-box;")

    def refresh():
        holder.clear()
        with holder:
            proj = state.get("project") or {}
            user = state.get("user") or {}

            with ui.element('div').style(
                "display:flex;align-items:center;gap:12px;margin-bottom:8px;"):
                if proj.get("logo_bytes"):
                    ui.image(io.BytesIO(proj["logo_bytes"])).style(
                        "width:44px;height:44px;object-fit:contain;"
                        "border-radius:10px;border:1px solid #262626;"
                        "background:#141414;padding:4px;")
                else:
                    with ui.element('div').style(
                        "width:44px;height:44px;border-radius:10px;"
                        "background:#1a1a1a;border:1px solid #262626;"
                        "display:flex;align-items:center;justify-content:center;"
                        "color:#737373;"):
                        ui.icon("business").style("font-size:20px;")
                with ui.element('div').style("flex:1;min-width:0;"):
                    if proj.get("name"):
                        ui.label(proj.get("name", "")).style(
                            "font-size:15px;font-weight:700;color:#fafafa;"
                            "white-space:nowrap;overflow:hidden;"
                            "text-overflow:ellipsis;")
                        ui.label(_t("project")).classes("muted").style(
                            "font-size:11px;")
                    else:
                        ui.label(_t("no_project")).style(
                            "font-size:14px;font-weight:600;color:#a3a3a3;")

            def _open_chooser():
                _open_project_chooser(state, refresh, state["render_main"])

            ui.button(_t("switch_project"), icon="swap_horiz",
                      on_click=_open_chooser).classes(BTN_SOFT).style(
                "width:100%;margin-bottom:12px;")

            if proj.get("name"):
                ui.separator().style("margin:14px 0;")
                _info_row(_t("contractor"), proj.get("contractor", ""))
                _info_row(_t("subcontractor"), proj.get("subcontractor", ""))
                _info_row(_t("consultant"), proj.get("consultant", ""))
                _info_row(_t("location"), proj.get("location", ""))
                _info_row(_t("engineer"), proj.get("engineer_name", ""))
                ui.separator().style("margin:14px 0;")

                def open_setup():
                    _open_setup_dialog(state, refresh, is_new=False)

                ui.button(_t("edit"), icon="settings",
                          on_click=open_setup).classes(BTN_SOFT).style(
                    "width:100%;")

                ui.separator().style("margin:18px 0;")

                with ui.element('div').style(
                    "display:flex;justify-content:space-between;"
                    "align-items:center;margin-bottom:10px;"):
                    ui.label(_t("ms_section")).classes("section-label")

                    def open_ms():
                        _open_ms_dialog(state, refresh)
                    ui.button(icon="add", on_click=open_ms).props(
                        "flat round dense size=sm").style("color:#a855f7;")

                ms_list = db.list_ms(state["project_id"])
                if not ms_list:
                    ui.label(_t("no_ms")).classes("muted").style("font-size:12px;")
                else:
                    for m in ms_list:
                        with ui.element('div').classes("item-box"):
                            ui.label(m["ms_number"] + " — " + m["title"]).style(
                                "font-size:13px;font-weight:600;"
                                "color:#fafafa;margin-bottom:2px;")
                            ui.label(
                                m["element_type"] + " · " + m["discipline"] +
                                " · " + str(len(m["clauses"])) + " " +
                                _t("clauses_count")
                            ).classes("muted").style("font-size:11px;")

            ui.separator().style("margin:18px 0;")
            if user:
                ui.label(_t("signed_in_as")).classes("muted").style(
                    "font-size:10px;text-transform:uppercase;"
                    "letter-spacing:0.08em;")
                ui.label(user.get("name") or user.get("email") or "").style(
                    "font-size:13px;color:#fafafa;font-weight:500;"
                    "margin-bottom:8px;")
            ui.button(_t("logout"), icon="logout",
                      on_click=lambda: ui.navigate.to("/logout")).classes(
                BTN_SOFT).style("width:100%;")

    state["refresh_drawer"] = refresh
    refresh()


def _info_row(label, value):
    if not value:
        return
    with ui.element('div').style("margin-bottom:10px;"):
        ui.label(label).style(
            "font-size:10px;font-weight:700;color:#737373;"
            "text-transform:uppercase;letter-spacing:0.08em;"
            "margin-bottom:2px;display:block;")
        ui.label(str(value)).style(
            "font-size:13px;color:#fafafa;font-weight:500;")


# =====================================================================
# PROJECT CHOOSER
# =====================================================================
def _open_project_chooser(state, refresh_drawer, refresh_main):
    projects = db.list_projects(state["user_id"])

    with ui.dialog() as dlg, ui.card().style(
        "background:#141414;padding:24px;min-width:320px;"
        "max-width:95vw;width:480px;border-radius:16px;"
        "border:1px solid #262626;"):
        ui.label(_t("projects_title")).classes("h1").style("margin-bottom:14px;")

        if not projects:
            ui.label(_t("no_projects_hint")).classes("muted").style(
                "margin-bottom:14px;")
        else:
            for p in projects:
                is_current = (p["id"] == state.get("project_id"))
                border = "#a855f7" if is_current else "#262626"
                with ui.element('div').style(
                    "background:#1a1a1a;border:1px solid " + border + ";"
                    "border-radius:10px;padding:12px 14px;margin-bottom:8px;"
                    "cursor:pointer;") as card:
                    ui.label(p.get("name") or "(untitled)").classes("h3")
                    loc = p.get("location") or ""
                    if loc:
                        ui.label(loc).classes("muted").style("font-size:12px;")

                    def _pick(pid=p["id"]):
                        state["project_id"] = pid
                        app.storage.user["project_id"] = pid
                        state["project"] = db.get_project(pid)
                        state["sub_filter"] = None
                        dlg.close()
                        refresh_drawer()
                        refresh_main()

                    card.on("click", _pick)

        def _new():
            dlg.close()
            _open_setup_dialog(state, refresh_drawer, is_new=True,
                                on_created=refresh_main)

        ui.button(_t("new_project"), icon="add", on_click=_new).classes(
            BTN_PRIMARY).style("width:100%;margin-top:6px;")

        def _delete():
            if not state.get("project_id"):
                ui.notify("No project to delete.", type="warning")
                return
            _confirm_delete(state, dlg, refresh_drawer, refresh_main)

        ui.button(_t("delete_project"), icon="delete", on_click=_delete).props(
            "flat").style("width:100%;color:#ef4444;margin-top:6px;")

    dlg.open()


def _confirm_delete(state, parent_dlg, refresh_drawer, refresh_main):
    pid = state.get("project_id")
    with ui.dialog() as dlg2, ui.card().style(
        "background:#141414;padding:24px;min-width:300px;"
        "max-width:95vw;width:400px;border-radius:16px;"
        "border:1px solid #262626;"):
        ui.label(_t("delete_confirm")).classes("h3").style("margin-bottom:14px;")

        def _yes():
            db.delete_project(pid)
            state["project_id"] = None
            state["project"] = None
            state["sub_filter"] = None
            app.storage.user.pop("project_id", None)
            dlg2.close()
            try:
                parent_dlg.close()
            except Exception:
                pass
            refresh_drawer()
            refresh_main()

        with ui.element('div').style("display:flex;gap:8px;"):
            ui.button(_t("delete_project"), on_click=_yes).classes(
                BTN_PRIMARY).style("flex:1;background:#ef4444 !important;")
            ui.button(_t("cancel_btn"), on_click=dlg2.close).classes(BTN_SOFT)
    dlg2.open()


# =====================================================================
# SETUP DIALOG
# =====================================================================
def _open_setup_dialog(state, refresh_drawer, is_new=False, on_created=None):
    proj = {} if is_new else (state.get("project") or {})

    with ui.dialog() as dlg, ui.card().style(
        "background:#141414;padding:24px;min-width:320px;"
        "max-width:95vw;width:460px;border-radius:16px;"
        "border:1px solid #262626;"):
        ui.label(_t("setup_title")).classes("h1").style("margin-bottom:18px;")

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

        async def handle_logo(e):
            logo_holder["bytes"] = await e.file.read()

        ui.upload(on_upload=handle_logo, auto_upload=True).style(
            "width:100%;").props("flat bordered accept=image/* label='" +
                                  _t("upload_logo") + "'")

        def save():
            try:
                if not name_in.value.strip():
                    ui.notify(_t("project_name"), type="warning")
                    return
                if is_new:
                    pid = db.create_project(
                        state["user_id"], name_in.value.strip(),
                        contractor_in.value.strip(), sub_in.value.strip(),
                        consultant_in.value.strip(), location_in.value.strip(),
                        engineer_in.value.strip(), logo_holder["bytes"])
                    state["project_id"] = pid
                    app.storage.user["project_id"] = pid
                    state["project"] = db.get_project(pid)
                else:
                    db.update_project(
                        state["project_id"], name_in.value.strip(),
                        contractor_in.value.strip(), sub_in.value.strip(),
                        consultant_in.value.strip(), location_in.value.strip(),
                        engineer_in.value.strip(), logo_holder["bytes"])
                    state["project"] = db.get_project(state["project_id"])
                ui.notify(_t("save") + " ✓", type="positive")
                dlg.close()
                hook = state.get("refresh_drawer")
                if hook:
                    try:
                        hook()
                    except Exception:
                        pass
                if refresh_drawer:
                    try:
                        refresh_drawer()
                    except Exception:
                        pass
                if on_created:
                    on_created()
                else:
                    state["render_main"]()
            except Exception as ex:
                import traceback
                traceback.print_exc()
                ui.notify("Save failed: " + str(ex), type="negative")

        with ui.element('div').style("display:flex;gap:8px;margin-top:18px;"):
            ui.button(_t("save_project"), on_click=save).classes(
                BTN_PRIMARY).style("flex:1;")
            ui.button(_t("cancel_btn"), on_click=dlg.close).classes(BTN_SOFT)

    dlg.open()


# =====================================================================
# MS DIALOG
# =====================================================================
def _open_ms_dialog(state, refresh_drawer):
    if not state.get("project_id"):
        ui.notify(_t("setup_first"), type="warning")
        return

    with ui.dialog() as dlg, ui.card().style(
        "background:#141414;padding:24px;min-width:320px;"
        "max-width:95vw;width:520px;border-radius:16px;"
        "border:1px solid #262626;"):
        ui.label(_t("ms_dialog_title")).classes("h1").style("margin-bottom:18px;")

        holder = {"bytes": None, "name": ""}
        file_status = ui.label("").classes("muted").style(
            "font-size:12px;margin-top:6px;")

        async def handle_file(e):
            holder["bytes"] = await e.file.read()
            holder["name"] = e.file.name
            file_status.set_text(_t("file_loaded") + " " + e.file.name +
                                  " (" + str(len(holder["bytes"]) // 1024) + " KB)")

        ui.upload(on_upload=handle_file, auto_upload=True).style(
            "width:100%;").props("flat bordered accept=.pdf,.docx,.doc,.txt,.md "
                                  "label='" + _t("ms_upload_file") + "'")
        file_status

        ms_num_in = ui.input(_t("ms_number"), value="MS-01").style("width:100%;")
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
                holder["bytes"], call_gemini_json, holder["name"])
            preview.clear()
            if result.get("error"):
                with preview:
                    ui.label(_t("error_prefix") + str(result["error"])).style(
                        "color:#ef4444;font-size:13px;")
                return
            clauses = result["clauses"]
            with preview:
                ui.label(_t("extracted") + " " + str(len(clauses)) + " " +
                          _t("clauses_count")).classes("h3").style("margin-bottom:6px;")
                with ui.element('div').classes("scroll-box"):
                    for cl in clauses:
                        with ui.element('div').style(
                            "padding:8px 6px;border-bottom:1px solid #1f1f1f;"):
                            ui.label("§" + cl["id"] + " — " + cl["title"]).classes(
                                "mono-lg")
                            ui.label(cl["text"][:180]).classes("muted").style(
                                "font-size:12px;margin-top:2px;")

                def confirm():
                    db.save_ms(
                        project_id=state["project_id"],
                        ms_number=ms_num_in.value.strip(),
                        title=title_in.value.strip(),
                        element_type=element_in.value,
                        discipline=disc_in.value,
                        pdf_bytes=holder["bytes"], clauses=clauses)
                    ui.notify(_t("ms_saved") + " ✓", type="positive")
                    dlg.close()
                    if refresh_drawer:
                        try:
                            refresh_drawer()
                        except Exception:
                            pass
                    hook = state.get("refresh_drawer")
                    if hook:
                        try:
                            hook()
                        except Exception:
                            pass

                ui.button(_t("confirm_save"), on_click=confirm).classes(
                    BTN_SUCCESS).style("width:100%;margin-top:10px;")

        with ui.element('div').style("display:flex;gap:8px;margin-top:18px;"):
            ui.button(_t("extract"), on_click=extract).classes(
                BTN_PRIMARY).style("flex:1;")
            ui.button(_t("cancel_btn"), on_click=dlg.close).classes(BTN_SOFT)

        preview

    dlg.open()


# =====================================================================
# NEW DEFECT WIZARD
# =====================================================================
def _build_new_defect(state):
    if not state.get("project_id"):
        _render_no_project(state, state["render_main"])
        return

    stage = {"photo": None, "mime": None,
             "candidates": None, "manual": [],
             "text_only": False, "text_desc": ""}

    with ui.element('div').classes("card").style("margin-bottom:14px;"):
        ui.label(_t("photo_title")).classes("h1").style("margin-bottom:4px;")
        ui.label(_t("photo_sub")).classes("muted").style("margin-bottom:14px;")

        async def handle_photo(e):
            try:
                data = await e.file.read()
            except Exception as ex:
                ui.notify(_t("upload_failed") + str(ex), type="negative")
                return
            if not data:
                ui.notify(_t("empty_file"), type="warning")
                return
            stage["photo"] = data
            stage["mime"] = ("image/jpeg"
                             if e.file.name.lower().endswith((".jpg", ".jpeg"))
                             else "image/png")
            stage["candidates"] = None
            stage["manual"] = []
            stage["text_only"] = False
            ui.notify(_t("photo_received") + " (" +
                       str(len(data) // 1024) + " KB)", type="positive")
            ui.timer(0.4, rebuild_body, once=True)

        ui.upload(on_upload=handle_photo, auto_upload=True).style(
            "width:100%;").props("flat bordered accept=image/* label='" +
                                  _t("choose_photo") + "'")

        with ui.element('div').classes("or-divider"):
            ui.label(_t("or_divider")).style(
                "font-size:11px;font-weight:700;letter-spacing:0.1em;")

        def _open_nophoto():
            _open_no_photo_dialog(state, stage, rebuild_body)

        ui.button(_t("no_photo_btn"), icon="edit_note",
                  on_click=_open_nophoto).classes(BTN_OUTLINE).style(
            "width:100%;")

    body = ui.element('div').style("width:100%;")

    def rebuild_body():
        body.clear()
        with body:
            _render_body_contents(state, stage, rebuild_body)

    rebuild_body()


def _open_no_photo_dialog(state, stage, refresh_fn):
    if not state.get("project_id"):
        ui.notify(_t("setup_first"), type="warning")
        return

    with ui.dialog() as dlg, ui.card().style(
        "background:#141414;padding:24px;min-width:320px;"
        "max-width:95vw;width:520px;border-radius:16px;"
        "border:1px solid #262626;"):
        ui.label(_t("no_photo_title")).classes("h1").style("margin-bottom:4px;")
        ui.label(_t("no_photo_sub")).classes("muted").style("margin-bottom:14px;")

        desc_in = ui.textarea(label=_t("defect_desc"),
                                placeholder=_t("defect_desc_placeholder")).style(
            "width:100%;")
        note_in = ui.textarea(label=_t("extra_note"),
                                placeholder=_t("extra_note_placeholder")).style(
            "width:100%;")

        with ui.element('div').style(
            "display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:10px;"):
            zone_in = ui.select(_zone_options(), value="A", label=_t("zone"))
            element_in = ui.select(_element_options(), value="column",
                                    label=_t("element"))

        btn = ui.button(_t("analyze"), icon="auto_awesome")

        async def do_analyze():
            if not (desc_in.value or "").strip():
                ui.notify(_t("desc_required"), type="warning")
                return
            btn.props("loading")
            btn.set_text(_t("analyzing"))
            ms_clauses = db.get_clauses_for_element(
                state["project_id"], element_in.value)
            result = await svc.analyze_defect_text(
                description=desc_in.value.strip(),
                note=note_in.value or "",
                ms_clauses=ms_clauses,
                element_type=element_in.value,
                call_gemini_json_fn=call_gemini_json)
            btn.props(remove="loading")
            btn.set_text(_t("analyze"))
            if result.get("error"):
                ui.notify(result["error"], type="negative")
                return

            stage["candidates"] = list(result["defects"])
            stage["manual"] = []
            stage["photo"] = None
            stage["mime"] = None
            stage["text_only"] = True
            stage["text_desc"] = desc_in.value.strip()
            stage["note"] = note_in.value or ""
            stage["zone"] = zone_in.value
            stage["element"] = element_in.value
            for c in stage["candidates"]:
                c["_sel"] = True
                c["_manual"] = False
                c["_nophoto"] = True
            dlg.close()
            ui.timer(0.2, refresh_fn, once=True)

        btn.on("click", do_analyze)
        btn.classes(BTN_PRIMARY).style("width:100%;margin-top:14px;")

        with ui.element('div').style("margin-top:8px;"):
            ui.button(_t("cancel_btn"), on_click=dlg.close).classes(
                BTN_SOFT).style("width:100%;")

    dlg.open()


def _render_body_contents(state, stage, refresh_fn):
    if not state.get("project_id"):
        return

    has_photo = bool(stage.get("photo"))
    has_text = bool(stage.get("text_only"))
    has_candidates = stage.get("candidates") is not None

    if not has_photo and not has_text:
        return

    if has_photo:
        with ui.element('div').classes("card").style("margin-bottom:14px;"):
            try:
                b64 = base64.b64encode(stage["photo"]).decode("ascii")
                mime = stage.get("mime") or "image/jpeg"
                ui.image("data:" + mime + ";base64," + b64).style(
                    "width:100%;max-height:340px;object-fit:cover;"
                    "border-radius:12px;border:1px solid #262626;")
            except Exception as ex:
                print("[ui] image render failed: " + repr(ex))

    if has_photo and not has_candidates:
        with ui.element('div').classes("card"):
            note_in = ui.textarea(label=_t("note_label"),
                                    placeholder=_t("note_placeholder")).style(
                "width:100%;")
            with ui.element('div').style(
                "display:grid;grid-template-columns:1fr 1fr;gap:10px;"
                "margin-top:10px;"):
                zone_in = ui.select(_zone_options(), value="A", label=_t("zone"))
                element_in = ui.select(_element_options(), value="column",
                                        label=_t("element"))

            analyze_btn = ui.button(_t("analyze"), icon="auto_awesome")

            async def do_analyze():
                ms_clauses = db.get_clauses_for_element(
                    state["project_id"], element_in.value)
                analyze_btn.props("loading")
                analyze_btn.set_text(_t("analyzing"))
                result = await svc.analyze_defect_photo(
                    photo_bytes=stage["photo"], mime_type=stage["mime"],
                    note=note_in.value or "", ms_clauses=ms_clauses,
                    element_type=element_in.value,
                    call_gemini_json_fn=call_gemini_json)
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
                ui.timer(0.3, refresh_fn, once=True)

            analyze_btn.on("click", do_analyze)
            analyze_btn.classes(BTN_PRIMARY).style("width:100%;margin-top:14px;")
        return

    if has_text and not has_candidates:
        return

    _render_candidates(state, stage, refresh_fn)


def _render_candidates(state, stage, refresh_fn):
    all_items = stage["candidates"] + stage["manual"]

    with ui.element('div').classes("card").style("margin-bottom:14px;"):
        if stage["candidates"]:
            ui.label(_t("ai_found")).classes("h3").style(
                "margin-bottom:14px;color:#d4d4d4;")
        else:
            ui.label(_t("ai_found_none")).classes("h3").style(
                "margin-bottom:14px;color:#d4d4d4;")

        for c in list(all_items):
            _render_defect_card(c, stage, refresh_fn)

        def _open_add():
            _open_add_dialog(stage, refresh_fn)

        ui.button(_t("add_manual"), icon="add", on_click=_open_add).classes(
            BTN_SOFT).style("width:100%;margin-top:6px;")

    with ui.element('div').classes("card"):
        ui.label(_t("notice_details")).classes("h1").style("margin-bottom:14px;")

        sub_in = ui.input(
            _t("send_to"),
            value=(state["project"] or {}).get("subcontractor", "") or "",
            placeholder=_t("send_to_placeholder")).style("width:100%;")

        with ui.element('div').style(
            "display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:10px;"):
            deadline_in = ui.select(
                {"1": "1 " + _t("days"), "2": "2 " + _t("days"),
                 "3": "3 " + _t("days"), "5": "5 " + _t("days"),
                 "7": "7 " + _t("days"), "14": "14 " + _t("days")},
                value="3", label=_t("deadline"))
            raise_in = ui.select(
                {"qc_internal": _t("qc_internal"),
                 "consultant": _t("consultant_ncr")},
                value="qc_internal", label=_t("raised_as"))

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
                    "context_mismatch": s.get("context_mismatch", False)})
            notice_uid = svc.generate_uid("NTC")
            pdf_bytes = svc.build_notice_pdf(
                project=state["project"], defects=clean_selected,
                notice_uid=notice_uid, subcontractor=sub_in.value.strip(),
                deadline_days=int(deadline_in.value), raise_type=raise_in.value,
                logo_bytes=state["project"].get("logo_bytes"))
            db.save_defect(
                project_id=state["project_id"], uid=notice_uid,
                zone=stage.get("zone", "A"),
                subcontractor=sub_in.value.strip(),
                deadline_days=int(deadline_in.value),
                raise_type=raise_in.value,
                photo_bytes=stage.get("photo"),
                note=stage.get("note", ""), selected=clean_selected,
                notice_pdf=pdf_bytes)
            ui.notify(_t("notice_saved") + " " + notice_uid, type="positive")
            ui.download(pdf_bytes, filename=notice_uid + ".pdf")
            stage["photo"] = None
            stage["mime"] = None
            stage["candidates"] = None
            stage["manual"] = []
            stage["text_only"] = False
            stage["text_desc"] = ""
            ui.timer(0.3, refresh_fn, once=True)

        gen_btn.on("click", do_generate)
        gen_btn.classes(BTN_PRIMARY).style("width:100%;margin-top:16px;")


def _render_defect_card(item, stage, refresh_fn):
    with ui.element('div').classes("item-box"):
        with ui.element('div').style("display:flex;gap:10px;align-items:flex-start;"):
            def _toggle(e):
                item["_sel"] = bool(e.value)
            ui.checkbox(value=item.get("_sel", True), on_change=_toggle)
            with ui.element('div').style("flex:1;min-width:0;"):
                with ui.element('div').style("display:flex;gap:6px;flex-wrap:wrap;margin-bottom:6px;"):
                    if item.get("_manual"):
                        ui.html('<span class="badge-manual">' + _t("tag_manual") + '</span>')
                    elif item.get("_nophoto"):
                        ui.html('<span class="badge-nophoto">' + _t("tag_nophoto") + '</span>')
                    else:
                        ui.html('<span class="badge-ai">' + _t("tag_ai") + '</span>')
                    if item.get("context_mismatch"):
                        ui.html('<span class="badge-mismatch">' + _t("mismatch_warn") + '</span>')

                ui.label(str(item.get("name", ""))).classes("mono-lg").style(
                    "margin-bottom:6px;")
                if item.get("location_hint"):
                    ui.label(str(item["location_hint"])).classes("mono-sm")
                cit = []
                if item.get("ms_violations"):
                    cit.append("MS: " + ", ".join(item["ms_violations"]))
                if item.get("code_violations"):
                    cit.append("ECP: " + ", ".join(item["code_violations"]))
                if cit:
                    ui.label(" · ".join(cit)).classes("mono-sm").style("margin-top:2px;")
                if item.get("repair_action"):
                    ui.label("> " + str(item["repair_action"])).classes("mono-sm").style(
                        "margin-top:4px;")
                sev = _severity_options().get(item.get("severity", "Medium"),
                                                item.get("severity", "Medium"))
                ui.label("[" + sev + "]").classes("mono-sm").style("margin-top:4px;")

            def _remove():
                if item in stage["candidates"]:
                    stage["candidates"].remove(item)
                if item in stage["manual"]:
                    stage["manual"].remove(item)
                ui.timer(0.05, refresh_fn, once=True)

            ui.button(icon="close", on_click=_remove).props(
                "flat round dense").style("color:#737373;")


def _open_add_dialog(stage, refresh_fn):
    with ui.dialog() as dlg, ui.card().style(
        "background:#141414;padding:24px;min-width:320px;"
        "max-width:95vw;width:440px;border-radius:16px;"
        "border:1px solid #262626;"):
        ui.label(_t("add_defect_title")).classes("h1").style("margin-bottom:14px;")
        name_in = ui.input(_t("name")).classes("mono").style("width:100%;")
        loc_in = ui.input(_t("location_hint")).style("width:100%;")
        sev_in = ui.select(_severity_options(), value="Medium",
                            label=_t("severity")).style("width:100%;")
        ms_in = ui.input(_t("ms_clause")).classes("mono").style("width:100%;")
        ecp_in = ui.input(_t("ecp_code")).classes("mono").style("width:100%;")
        rep_in = ui.input(_t("repair")).style("width:100%;")

        def _save():
            if not name_in.value.strip():
                ui.notify(_t("name_required"), type="warning")
                return
            stage["manual"].append({
                "name": name_in.value.strip(),
                "location_hint": loc_in.value.strip(),
                "severity": sev_in.value,
                "ms_violations": ([ms_in.value.strip()] if ms_in.value.strip() else []),
                "code_violations": ([ecp_in.value.strip()] if ecp_in.value.strip() else []),
                "repair_action": rep_in.value.strip(),
                "context_mismatch": False, "_sel": True, "_manual": True})
            dlg.close()
            ui.timer(0.05, refresh_fn, once=True)

        with ui.element('div').style("display:flex;gap:8px;margin-top:16px;"):
            ui.button(_t("add"), on_click=_save).classes(
                BTN_PRIMARY).style("flex:1;")
            ui.button(_t("cancel"), on_click=dlg.close).classes(BTN_SOFT)
    dlg.open()


# =====================================================================
# LOGS
# =====================================================================
def _build_logs(state):
    if not state.get("project_id"):
        _render_no_project(state, state["render_main"])
        return

    ui.label(_t("logs_title")).classes("h1").style("margin-bottom:4px;")
    ui.label(_t("logs_sub")).classes("muted").style("margin-bottom:16px;")

    # Sub filter chip
    if state.get("sub_filter"):
        with ui.element('div').style(
            "display:flex;align-items:center;gap:8px;margin-bottom:14px;"
        ):
            with ui.element('span').classes("chip"):
                ui.icon("engineering")
                ui.label(_t("filtered_by") + " " + str(state["sub_filter"]))

            def _clear():
                state["sub_filter"] = None
                state["render_main"]()

            ui.button(_t("clear_filter"), on_click=_clear).props(
                "flat dense no-caps").style(
                "color:#a855f7;font-weight:600;font-size:12px;"
                "min-height:32px;")

    fstate = {"filter": "all"}

    @ui.refreshable
    def log_list():
        rows = db.list_defects(
            state["project_id"],
            raise_filter=None if fstate["filter"] == "all" else fstate["filter"])

        if state.get("sub_filter"):
            rows = [r for r in rows
                    if (r.get("subcontractor") or "") == state["sub_filter"]]

        with ui.element('div').style(
            "display:flex;gap:8px;align-items:center;margin-bottom:14px;"):
            filt = ui.select(
                {"all": _t("filter_all"),
                 "qc_internal": _t("filter_qc"),
                 "consultant": _t("filter_consultant")},
                value=fstate["filter"]).style("flex:1;")

            def on_filter(e):
                fstate["filter"] = e.value
                log_list.refresh()

            filt.on("update:model-value", on_filter)

        if rows:
            open_count = sum(1 for r in rows if r["status"] == "open")
            ui.label(str(len(rows)) + " · " + _t("open") + " " + str(open_count) +
                      " · " + _t("closed") + " " + str(len(rows) - open_count)
                      ).classes("muted").style("margin-bottom:12px;")

        with ui.element('div').style(
            "display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:16px;"):
            def export_register():
                if not rows:
                    ui.notify(_t("no_rows"), type="warning")
                    return
                pdf = svc.build_register_pdf(state["project"], rows,
                                              logo_bytes=state["project"].get("logo_bytes"))
                ui.download(pdf, filename="defect_register.pdf")

            def export_closure():
                if not rows:
                    ui.notify(_t("no_rows"), type="warning")
                    return
                pdf = svc.build_closure_pdf(state["project"], rows,
                                             logo_bytes=state["project"].get("logo_bytes"))
                ui.download(pdf, filename="closure_report.pdf")

            ui.button(_t("export_register"), on_click=export_register).classes(
                BTN_SOFT).style("width:100%;")
            ui.button(_t("closure_report"), on_click=export_closure).classes(
                BTN_PRIMARY).style("width:100%;")

        if not rows:
            ui.label(_t("no_logs")).classes("muted").style(
                "text-align:center;padding:40px 0;")
            return

        for r in rows:
            _render_log_card(r, log_list.refresh)

    log_list()


def _render_log_card(row, refresh_fn):
    status = row.get("status", "open")
    is_open = status == "open"
    badge = "badge-open" if is_open else "badge-closed"
    badge_txt = _t("open") if is_open else _t("closed")
    title = row.get("first_defect") or row.get("uid", "")
    extra = ""
    if row.get("count", 0) > 1:
        extra = "  +" + str(row["count"] - 1)

    with ui.element('div').classes("card").style(
        "padding:16px;margin-bottom:10px;cursor:pointer;") as card:
        with ui.element('div').style(
            "display:flex;justify-content:space-between;"
            "align-items:flex-start;gap:10px;"):
            with ui.element('div').style("flex:1;min-width:0;"):
                ui.label(str(title) + extra).classes("mono-lg").style(
                    "margin-bottom:4px;word-break:break-word;")
                ui.label(row.get("uid", "") + "  ·  Zone " +
                          str(row.get("zone", "")) + "  ·  " +
                          str(row.get("subcontractor", ""))).classes("mono-sm")
            ui.html('<span class="' + badge + '">' + badge_txt + '</span>')

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
        "background:#141414;padding:0;max-width:560px;width:95vw;"
        "border-radius:16px;overflow:hidden;border:1px solid #262626;"):
        with ui.element('div').style(
            "padding:20px 20px 16px;border-bottom:1px solid #262626;"):
            ui.label(_t("notice") + " " + d["uid"]).classes("h2")
            ui.label("Zone " + str(d["zone"]) + " · " + str(d["subcontractor"])
                      ).classes("muted").style("margin-top:4px;")
            if d.get("consultant_ncr"):
                ui.label(_t("ncr_input") + ": " + str(d["consultant_ncr"])).style(
                    "color:#fbbf24;font-size:12px;font-weight:700;margin-top:6px;")

        with ui.element('div').style(
            "padding:20px;max-height:60vh;overflow-y:auto;"):
            if d.get("photo_bytes"):
                try:
                    b64 = base64.b64encode(d["photo_bytes"]).decode("ascii")
                    ui.image("data:image/jpeg;base64," + b64).style(
                        "width:100%;max-height:260px;object-fit:cover;"
                        "border-radius:10px;margin-bottom:14px;"
                        "border:1px solid #262626;")
                except Exception:
                    pass
            if d.get("note"):
                ui.label("📝 " + str(d["note"])).classes("soft").style(
                    "margin-bottom:14px;font-style:italic;")

            for i, s in enumerate(d["selected"], 1):
                with ui.element('div').classes("item-box"):
                    ui.label(str(i) + ".  " + str(s.get("name", ""))).classes(
                        "mono-lg").style("margin-bottom:4px;")
                    cit = []
                    if s.get("ms_violations"):
                        cit.append("MS: " + ", ".join(s["ms_violations"]))
                    if s.get("code_violations"):
                        cit.append("ECP: " + ", ".join(s["code_violations"]))
                    if cit:
                        ui.label(" · ".join(cit)).classes("mono-sm")
                    if s.get("repair_action"):
                        ui.label("> " + str(s["repair_action"])).classes(
                            "mono-sm").style("margin-top:4px;")

        with ui.element('div').style(
            "padding:14px 20px 20px;border-top:1px solid #262626;"
            "display:flex;flex-direction:column;gap:8px;"):
            if d.get("notice_pdf"):
                ui.button(_t("download_pdf"), icon="download",
                          on_click=lambda: ui.download(
                              d["notice_pdf"], filename=d["uid"] + ".pdf")
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
                        db.close_defect(defect_id, consultant_ncr=ncr_in.value.strip())
                    else:
                        db.close_defect(defect_id)
                    ui.notify(_t("marked_closed"), type="positive")
                    dialog.close()
                    on_close_cb()

                ui.button(_t("mark_closed"), icon="check", on_click=do_close).classes(
                    BTN_PRIMARY).style("width:100%;")

            ui.button(_t("close"), on_click=dialog.close).props("flat").style(
                "width:100%;color:#a3a3a3;")

    dialog.open()
