"""
ui/defect_page.py — Full file.
Dashboard: summary + SVG line + SVG scatter + printable PDF.
Chat tab. Filters fixed. Search fixed. No scrollbars. Engineer + place.
"""
import io
import base64
import datetime
from nicegui import ui, app

from services import defect_db as db
from services import defect_service as svc
from services.ai_service import call_gemini_json


LANG = {"code": "en"}

T = {
    "en": {
        "app_title": "DEFECT NOTICES",
        "new_defect": "NEW DEFECT", "logs": "DEFECT LOGS",
        "subs": "SUBS", "dashboard": "DASHBOARD", "chat": "TEAM CHAT",
        "project": "PROJECT", "no_project": "NO PROJECT",
        "setup_project": "Set up project", "edit": "Edit",
        "contractor": "Contractor", "subcontractor": "Subcontractor",
        "consultant": "Consultant", "location": "Location",
        "engineer": "QC Engineer", "upload_logo": "Upload logo",
        "ms_section": "Method Statements", "no_ms": "No MS",
        "clauses_count": "clauses",
        "photo_title": "Take a photo of the defect",
        "photo_sub": "Tap below to pick a site photo.",
        "choose_photo": "Choose photo",
        "add_photos": "Add more photos",
        "photos_count": "photo(s)",
        "no_photo_btn": "Raise defect without photo",
        "no_photo_title": "Defect without photo",
        "no_photo_sub": "Describe the defect. AI will match it to the MS.",
        "defect_desc": "Defect description",
        "defect_desc_placeholder": "e.g. exposed rebar at column C3 base",
        "extra_note": "Extra note (optional)",
        "extra_note_placeholder": "any additional context",
        "analyze": "Analyze with AI", "analyzing": "Analyzing...",
        "note_label": "Note (optional)",
        "note_placeholder": "e.g. crack at column C3 base",
        "zone": "Zone", "element": "Element",
        "engineer_field": "Engineer name",
        "place_field": "Exact place",
        "place_placeholder": "e.g. Block B, Column C3 base, Grid 4-5",
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
        "tag_nophoto": "NO PHOTO", "mismatch_warn": "NO MS MATCH",
        "tag_dup": "SEEN {n}\u00d7",
        "logs_title": "DEFECT LOGS",
        "logs_sub": "Every notice issued. Tap to view.",
        "no_logs": "No notices yet.",
        "no_match": "No matches.",
        "search_placeholder": "Search UID, defect, sub, engineer, place...",
        "filter_all": "All", "filter_qc": "QC Internal",
        "filter_consultant": "Consultant / NCR",
        "export_register": "REGISTER PDF", "closure_report": "CLOSURE PDF",
        "export_excel": "EXCEL",
        "open": "OPEN", "closed": "CLOSED", "no_rows": "No rows.",
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
        "upload_failed": "Upload failed: ", "empty_file": "Empty file.",
        "photo_received": "Photo received", "file_loaded": "Loaded: ",
        "photos_received": "photos",
        "projects_title": "Your Projects", "switch_project": "Switch project",
        "new_project": "New project", "create_first": "Create your first project",
        "no_projects_hint": "No projects yet.",
        "delete_project": "Delete project",
        "delete_confirm": "Delete this project and all its data?",
        "logout": "Log out", "signed_in_as": "Signed in",
        "or_divider": "OR",
        "dash_title": "DASHBOARD", "dash_sub": "Live project metrics.",
        "kpi_total": "TOTAL", "kpi_open": "OPEN", "kpi_closed": "CLOSED",
        "kpi_overdue": "OVERDUE", "kpi_closed_7d": "CLOSED-7D",
        "kpi_avg_days": "AVG-CLOSE",
        "dash_zones": "OPEN BY ZONE", "dash_weeks": "RAISED / WEEK",
        "dash_subs": "BY SUBCONTRACTOR",
        "dash_summary": "SUMMARY",
        "dash_scatter": "DURATION BY DAYS OPEN",
        "dash_print": "PRINT DASHBOARD PDF",
        "dash_empty": "No defects yet.",
        "no_data": "No data.",
        "col_name": "NAME", "col_open": "OPEN", "col_overdue": "OVERDUE",
        "col_closed": "CLOSED", "col_total": "TOTAL",
        "unassigned": "(unassigned)",
        "subs_title": "SUBCONTRACTORS",
        "subs_sub": "Master list and live performance.",
        "add_sub": "Add subcontractor",
        "add_sub_title": "Add subcontractor",
        "sub_name": "Subcontractor name",
        "sub_trade": "Trade (e.g. steel fixing, masonry)",
        "sub_phone": "Phone (optional)",
        "sub_notes": "Notes (optional)",
        "sub_saved": "Saved.", "sub_deleted": "Deleted.",
        "delete_sub_confirm": "Remove this subcontractor?",
        "no_subs": "No subcontractors yet.",
        "no_subs_hint": "Add one to track performance.",
        "view_defects": "View defects",
        "download_sub_pdf": "Performance PDF",
        "filtered_by": "FILTER", "clear_filter": "Clear",
        "from_defects": "from notices",
        "sub_open": "OPEN", "sub_overdue": "OVERDUE",
        "sub_closed": "CLOSED", "sub_total": "TOTAL",
        "delete_sub": "Remove",
        "close_defect_title": "Close defect",
        "close_defect_sub": "Attach a closure photo as proof.",
        "closure_photo_label": "Closure photo",
        "closure_photo_optional": "Closure photo (optional)",
        "closure_photo_hint": "Recommended — photo of repaired work.",
        "closure_attached": "Photo attached",
        "closure_skipped": "Closing without photo",
        "confirm_close": "Confirm close",
        "close_without_photo": "Close without photo",
        "closure_photo_short": "CLOSURE",
        "refresh": "REFRESH", "week": "wk",
        "no_ms_uploaded": "no MS",
        "edit_defect": "Edit",
        "delete_defect": "Delete",
        "edit_defect_title": "Edit notice",
        "edit_defect_sub": "Change details. Notice PDF will be regenerated.",
        "defect_items": "Defect items",
        "add_item": "+ Add item",
        "remove_item": "Remove",
        "save_changes": "Save changes",
        "saved_changes": "Notice updated.",
        "confirm_delete_defect": "Delete this notice permanently?",
        "delete_warning": "This cannot be undone.",
        "deleted_defect": "Notice deleted.",
        "no_items": "No defects in this notice.",
        "raised_by": "By",
        "at_place": "At",
        "chat_title": "TEAM CHAT",
        "chat_sub": "Project-wide discussion for the QC team.",
        "chat_placeholder": "Type a message...  use @ to mention someone",
        "chat_send": "Send",
        "chat_empty": "No messages yet. Start the conversation.",
        "chat_reply": "Reply",
        "chat_replying_to": "Replying to",
        "chat_cancel": "Cancel",
        "chat_delete": "Delete",
        "chat_filter_author": "Author",
        "chat_filter_from": "From",
        "chat_filter_to": "To",
        "chat_filter_all": "All",
        "chat_search": "Search messages...",
        "chat_confirm_delete": "Delete this message?",
        "chat_deleted": "Message deleted.",
        "chat_you": "you",
        "chat_mention": "Mention",
    },
    "ar": {
        "app_title": "إشعارات العيوب",
        "new_defect": "عيب جديد", "logs": "السجل",
        "dashboard": "الرئيسية", "subs": "المقاولون", "chat": "الدردشة",
        "project": "المشروع", "no_project": "لا مشروع",
        "setup_project": "إعداد المشروع", "edit": "تعديل",
        "contractor": "المقاول", "subcontractor": "المقاول الفرعي",
        "consultant": "الاستشاري", "location": "الموقع",
        "engineer": "مهندس الجودة", "upload_logo": "تحميل الشعار",
        "ms_section": "بيانات طريقة العمل", "no_ms": "لا توجد بيانات",
        "clauses_count": "بند",
        "photo_title": "التقط صورة للعيب",
        "photo_sub": "اضغط لاختيار صورة الموقع.",
        "choose_photo": "اختر صورة",
        "add_photos": "إضافة صور أخرى",
        "photos_count": "صورة",
        "no_photo_btn": "عيب بدون صورة",
        "no_photo_title": "عيب بدون صورة",
        "no_photo_sub": "صف العيب. سيطابقه الذكاء الاصطناعي.",
        "defect_desc": "وصف العيب",
        "defect_desc_placeholder": "مثال: حديد مكشوف عند قاعدة C3",
        "extra_note": "ملاحظة إضافية (اختياري)",
        "extra_note_placeholder": "أي سياق إضافي",
        "analyze": "تحليل بالذكاء الاصطناعي", "analyzing": "جاري التحليل...",
        "note_label": "ملاحظة (اختياري)",
        "note_placeholder": "مثال: شرخ عند قاعدة C3",
        "zone": "المنطقة", "element": "العنصر",
        "engineer_field": "اسم المهندس",
        "place_field": "المكان بالتفصيل",
        "place_placeholder": "مثال: بلوك B، قاعدة عمود C3، محور 4-5",
        "ai_found": "العيوب المكتشفة. أزل غير الصحيحة وأضف المفقود:",
        "ai_found_none": "لم يُكتشف شيء. أضف عيباً يدوياً.",
        "add_manual": "+ إضافة عيب",
        "notice_details": "تفاصيل الإشعار",
        "send_to": "إرسال إلى المقاول الفرعي",
        "send_to_placeholder": "مثال: الأهرام لتثبيت الحديد",
        "deadline": "المهلة", "days": "أيام", "raised_as": "المصدر",
        "qc_internal": "داخلي QC", "consultant_ncr": "استشاري / NCR",
        "generate_pdf": "إنشاء إشعار PDF",
        "tick_one": "اختر عيباً واحداً على الأقل.",
        "enter_sub": "أدخل اسم المقاول الفرعي.",
        "notice_saved": "تم الحفظ",
        "setup_first": "أعدّ المشروع أولاً.",
        "add_defect_title": "إضافة عيب يدوياً", "name": "اسم العيب",
        "location_hint": "الموقع", "severity": "الخطورة",
        "ms_clause": "بند MS", "ecp_code": "كود ECP",
        "repair": "الإصلاح", "add": "إضافة", "cancel": "إلغاء",
        "name_required": "اسم العيب مطلوب.",
        "desc_required": "الوصف مطلوب.",
        "tag_ai": "AI", "tag_manual": "يدوي",
        "tag_nophoto": "بدون صورة", "mismatch_warn": "لا بند مطابق",
        "tag_dup": "سُبق {n}\u00d7",
        "logs_title": "سجل العيوب",
        "logs_sub": "كل إشعار صدر.",
        "no_logs": "لا توجد إشعارات.",
        "no_match": "لا نتائج.",
        "search_placeholder": "ابحث بالرقم أو العيب أو المهندس أو المكان...",
        "filter_all": "الكل", "filter_qc": "داخلي QC",
        "filter_consultant": "استشاري / NCR",
        "export_register": "السجل PDF", "closure_report": "الإغلاق PDF",
        "export_excel": "Excel",
        "open": "مفتوح", "closed": "مغلق", "no_rows": "لا صفوف.",
        "notice": "إشعار", "download_pdf": "تحميل PDF",
        "mark_closed": "إغلاق", "close": "إغلاق",
        "ncr_input": "رقم NCR الاستشاري",
        "ncr_required": "أدخل رقم NCR أولاً.",
        "marked_closed": "تم الإغلاق.", "not_found": "غير موجود.",
        "repair_label": "الإصلاح",
        "save": "حفظ", "cancel_btn": "إلغاء",
        "setup_title": "إعداد المشروع", "project_name": "اسم المشروع",
        "save_project": "حفظ",
        "ms_dialog_title": "تحميل بند طريقة عمل",
        "ms_number": "رقم MS", "ms_title": "العنوان",
        "element_type": "العنصر", "discipline": "التخصص",
        "extract": "استخراج البنود", "extracting": "جاري الاستخراج...",
        "extracted": "تم استخراج", "confirm_save": "تأكيد وحفظ",
        "ms_saved": "تم الحفظ", "ms_upload_file": "اختر ملف",
        "upload_first": "اختر ملفاً أولاً.", "error_prefix": "خطأ: ",
        "severity_low": "منخفض", "severity_medium": "متوسط",
        "severity_high": "عالي", "severity_critical": "حرج",
        "element_column": "عمود", "element_beam": "كمرة",
        "element_slab": "بلاطة", "element_wall": "حائط",
        "element_foundation": "أساس", "element_finishing": "تشطيبات",
        "discipline_structural": "إنشائي", "discipline_arch": "معماري",
        "discipline_mep": "كهروميكانيكي", "zone_general": "عام",
        "lang_button": "EN",
        "upload_failed": "فشل: ", "empty_file": "ملف فارغ.",
        "photo_received": "تم استلام الصورة", "file_loaded": "تم التحميل: ",
        "photos_received": "صور",
        "projects_title": "مشاريعك", "switch_project": "تبديل المشروع",
        "new_project": "مشروع جديد", "create_first": "أنشئ مشروعك الأول",
        "no_projects_hint": "لا مشاريع بعد.",
        "delete_project": "حذف المشروع",
        "delete_confirm": "حذف هذا المشروع وكل بياناته؟",
        "logout": "خروج", "signed_in_as": "مسجل",
        "or_divider": "أو",
        "dash_title": "الرئيسية", "dash_sub": "مؤشرات حية.",
        "kpi_total": "الإجمالي", "kpi_open": "مفتوح", "kpi_closed": "مغلق",
        "kpi_overdue": "متأخر", "kpi_closed_7d": "أُغلق-٧",
        "kpi_avg_days": "متوسط الإغلاق",
        "dash_zones": "المفتوح حسب المنطقة", "dash_weeks": "المُصدر أسبوعياً",
        "dash_subs": "حسب المقاول الفرعي",
        "dash_summary": "ملخص",
        "dash_scatter": "المدة حسب أيام الفتح",
        "dash_print": "طباعة تقرير الرئيسية",
        "dash_empty": "لا عيوب بعد.",
        "no_data": "لا بيانات.",
        "col_name": "الاسم", "col_open": "مفتوح", "col_overdue": "متأخر",
        "col_closed": "مغلق", "col_total": "الإجمالي",
        "unassigned": "(غير معين)",
        "subs_title": "المقاولون الفرعيون",
        "subs_sub": "القائمة والأداء.",
        "add_sub": "إضافة مقاول فرعي",
        "add_sub_title": "إضافة مقاول فرعي",
        "sub_name": "اسم المقاول الفرعي",
        "sub_trade": "التخصص",
        "sub_phone": "هاتف (اختياري)",
        "sub_notes": "ملاحظات (اختياري)",
        "sub_saved": "تم الحفظ.", "sub_deleted": "تم الحذف.",
        "delete_sub_confirm": "حذف هذا المقاول؟",
        "no_subs": "لا مقاولون بعد.",
        "no_subs_hint": "أضف واحداً لتتبع أدائه.",
        "view_defects": "عرض العيوب",
        "download_sub_pdf": "تقرير الأداء PDF",
        "filtered_by": "فلتر", "clear_filter": "مسح",
        "from_defects": "من الإشعارات",
        "sub_open": "مفتوح", "sub_overdue": "متأخر",
        "sub_closed": "مغلق", "sub_total": "الإجمالي",
        "delete_sub": "حذف",
        "close_defect_title": "إغلاق العيب",
        "close_defect_sub": "أرفق صورة كإثبات.",
        "closure_photo_label": "صورة الإغلاق",
        "closure_photo_optional": "صورة الإغلاق (اختياري)",
        "closure_photo_hint": "مُفضل — صورة بعد الإصلاح.",
        "closure_attached": "تم الإرفاق",
        "closure_skipped": "بدون صورة",
        "confirm_close": "تأكيد الإغلاق",
        "close_without_photo": "إغلاق بدون صورة",
        "closure_photo_short": "إغلاق",
        "refresh": "تحديث", "week": "أسبوع",
        "no_ms_uploaded": "لا MS",
        "edit_defect": "تعديل",
        "delete_defect": "حذف",
        "edit_defect_title": "تعديل الإشعار",
        "edit_defect_sub": "عدّل التفاصيل. سيُعاد إنشاء PDF.",
        "defect_items": "بنود العيوب",
        "add_item": "+ إضافة بند",
        "remove_item": "حذف",
        "save_changes": "حفظ التعديلات",
        "saved_changes": "تم تحديث الإشعار.",
        "confirm_delete_defect": "حذف هذا الإشعار نهائياً؟",
        "delete_warning": "لا يمكن التراجع.",
        "deleted_defect": "تم حذف الإشعار.",
        "no_items": "لا بنود في هذا الإشعار.",
        "raised_by": "بواسطة",
        "at_place": "في",
        "chat_title": "دردشة الفريق",
        "chat_sub": "نقاش المشروع لفريق الجودة.",
        "chat_placeholder": "اكتب رسالة...  استخدم @ للإشارة",
        "chat_send": "إرسال",
        "chat_empty": "لا رسائل بعد. ابدأ النقاش.",
        "chat_reply": "رد",
        "chat_replying_to": "رداً على",
        "chat_cancel": "إلغاء",
        "chat_delete": "حذف",
        "chat_filter_author": "الكاتب",
        "chat_filter_from": "من",
        "chat_filter_to": "إلى",
        "chat_filter_all": "الكل",
        "chat_search": "ابحث في الرسائل...",
        "chat_confirm_delete": "حذف هذه الرسالة؟",
        "chat_deleted": "تم الحذف.",
        "chat_you": "أنت",
        "chat_mention": "إشارة",
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
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Amiri:wght@400;700&display=swap" rel="stylesheet">
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#0b0b0b">
<link rel="apple-touch-icon" href="/icon-192.png">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black">
<script>
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/service-worker.js').catch(function(){});
  }
</script>
<style>
  :root {
    --bg: #0b0b0b; --surface: #101010; --surface-2: #161616;
    --surface-3: #1c1c1c; --border: #1e1e1e; --border-2: #262626;
    --text: #e8e8e8; --text-soft: #b8b8b8; --muted: #808080;
    --muted-2: #5a5a5a; --accent: #5eead4; --accent-dim: #14b8a6;
    --blue: #60a5fa; --success: #4ade80; --warn: #fbbf24;
    --danger: #f87171;
  }
  * { font-variant-ligatures: none; }
  html, body {
    background: var(--bg) !important; color: var(--text) !important;
    font-family: 'JetBrains Mono', 'Amiri', 'Courier New', monospace !important;
    font-size: 13px; line-height: 1.5;
    -webkit-font-smoothing: antialiased;
    letter-spacing: -0.01em;
    overflow-x: hidden !important;
    overflow-y: hidden !important;
    height: 100%;
    direction: __DIR__;
  }
  /* Hide ALL scrollbars */
  * { scrollbar-width: none !important; -ms-overflow-style: none !important; }
  *::-webkit-scrollbar { display: none !important; width: 0 !important;
                         height: 0 !important; background: transparent !important; }
  .nicegui-content { padding: 0 !important; max-width: 100vw !important;
                     overflow-x: hidden !important; }
  .q-page, .q-layout, .q-page-container {
    max-width: 100vw !important; overflow-x: hidden !important;
    background: var(--bg) !important;
  }
  .q-btn {
    border-radius: 3px !important; text-transform: none !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 500 !important; letter-spacing: -0.01em !important;
    min-height: 32px !important; padding: 0 12px !important;
    font-size: 11px !important; box-shadow: none !important;
  }
  .q-btn:hover { box-shadow: none !important; }
  .btn-primary { background: var(--accent) !important;
                 color: #0b0b0b !important; font-weight: 700 !important; }
  .btn-primary:hover { background: var(--accent-dim) !important;
                       color: #0b0b0b !important; }
  .btn-soft { background: var(--surface-2) !important;
              color: var(--text) !important;
              border: 1px solid var(--border-2) !important; }
  .btn-soft:hover { background: var(--surface-3) !important;
                    border-color: #333 !important; }
  .btn-success { background: var(--success) !important;
                 color: #0b0b0b !important; font-weight: 700 !important; }
  .btn-danger { background: var(--danger) !important;
                color: #0b0b0b !important; font-weight: 700 !important; }
  .btn-outline { background: transparent !important;
                 color: var(--text) !important;
                 border: 1px dashed var(--border-2) !important; }
  .btn-outline:hover { border-color: var(--accent) !important;
                       color: var(--accent) !important;
                       background: rgba(94,234,212,0.04) !important; }
  .q-field--outlined .q-field__control {
    border-radius: 3px !important; background: var(--surface-2) !important;
    font-family: 'JetBrains Mono', monospace !important;
    min-height: 36px !important;
  }
  .q-field--outlined .q-field__control:before {
    border-color: var(--border-2) !important;
  }
  .q-field--outlined.q-field--focused .q-field__control:after {
    border-color: var(--accent) !important;
  }
  .q-field__label, .q-field__native, .q-field__input {
    color: var(--text) !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 12px !important;
  }
  .q-field__label { color: var(--muted) !important;
                    font-size: 11px !important; }
  .q-select__dropdown-icon { color: var(--muted) !important; }
  .q-menu { background: var(--surface-2) !important;
            border: 1px solid var(--border-2) !important;
            border-radius: 3px !important; }
  .q-item { color: var(--text) !important;
            font-family: 'JetBrains Mono', monospace !important;
            min-height: 32px !important; font-size: 12px !important; }
  .q-item--active { color: var(--accent) !important; }
  .card { background: var(--surface); border-radius: 4px;
          border: 1px solid var(--border); padding: 16px;
          width: 100%; box-sizing: border-box; }
  .item-box { background: var(--surface-2); border-radius: 3px;
              border: 1px solid var(--border); padding: 10px 12px;
              margin-bottom: 6px; width: 100%; box-sizing: border-box; }
  .h1 { font-size: 16px; font-weight: 700; color: var(--text);
        letter-spacing: -0.02em; }
  .h2 { font-size: 13px; font-weight: 600; color: var(--text); }
  .h3 { font-size: 12px; font-weight: 600; color: var(--text); }
  .muted { color: var(--muted); font-size: 11px; }
  .soft { color: var(--text-soft); font-size: 11px; }
  .mono-lg { font-size: 12px; font-weight: 600; color: var(--text);
             letter-spacing: -0.01em; word-break: break-word; }
  .mono-sm { font-size: 10px; font-weight: 400; color: var(--muted);
             letter-spacing: 0.01em; }
  .label { font-size: 9px; font-weight: 700; color: var(--muted-2);
           text-transform: uppercase; letter-spacing: 0.14em; }
  .q-drawer { background: var(--bg) !important;
              border-right: 1px solid var(--border) !important; }
  .app-header {
    position: sticky; top: 0; z-index: 900; width: 100%;
    background: rgba(11,11,11,0.94);
    backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
    border-bottom: 1px solid var(--border); padding: 8px 14px;
    display: flex; align-items: center; justify-content: space-between;
    box-sizing: border-box;
  }
  .app-header .brand { font-weight: 700; font-size: 12px;
                       color: var(--text); letter-spacing: -0.01em; }
  .app-header .brand::before {
    content: '● '; color: var(--accent); font-size: 9px;
    vertical-align: middle; margin-right: 4px;
  }
  .top-tabs {
    display: flex; align-items: center; gap: 4px; padding: 8px 14px;
    background: rgba(11,11,11,0.94);
    backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
    border-bottom: 1px solid var(--border);
    position: sticky; top: 0; z-index: 890;
    overflow-x: auto; overflow-y: hidden;
    width: 100%; box-sizing: border-box;
  }
  .top-tab-btn {
    background: transparent; border: none; color: var(--muted);
    font-family: 'JetBrains Mono', monospace; font-size: 11px;
    font-weight: 600; letter-spacing: 0.05em; padding: 6px 10px;
    border-radius: 2px; cursor: pointer; white-space: nowrap;
    flex-shrink: 0;
    transition: color 0.12s ease, background 0.12s ease;
  }
  .top-tab-btn:hover { color: var(--text); background: var(--surface-2); }
  .top-tab-btn.active { color: var(--accent); background: var(--surface-2); }
  .blink-cursor { display: inline-block; width: 6px; height: 11px;
                  background: #ffffff; vertical-align: middle;
                  margin-left: 5px;
                  animation: blink 1.1s steps(2, start) infinite; }
  @keyframes blink { to { visibility: hidden; } }
  .main-content { padding: 14px; padding-bottom: 30px;
                  max-width: 760px; margin: 0 auto; width: 100%;
                  box-sizing: border-box; }
  .q-uploader {
    background: var(--surface-2) !important;
    border: 1px dashed var(--border-2) !important;
    border-radius: 4px !important; width: 100% !important;
    max-width: 100% !important; color: var(--text) !important;
    box-shadow: none !important;
  }
  .q-uploader__header { background: transparent !important;
                        color: var(--text) !important;
                        min-height: 40px !important; }
  .q-uploader__title { color: var(--text) !important;
                       font-size: 11px !important;
                       font-weight: 500 !important;
                       font-family: inherit !important; }
  .q-uploader__subtitle { color: var(--muted) !important;
                          font-size: 10px !important;
                          font-family: inherit !important; }
  .q-uploader .q-btn { color: var(--muted) !important; }
  .q-uploader__list { background: transparent !important; }
  .q-uploader__list .q-item {
    background: var(--surface) !important; color: var(--text) !important;
    border-radius: 2px !important; margin: 3px !important;
    min-height: 34px !important;
  }
  .q-uploader__list .q-item__label {
    color: var(--text) !important; font-size: 10px !important;
    font-family: inherit !important;
  }
  .badge-open, .badge-closed, .badge-overdue,
  .badge-ai, .badge-manual, .badge-nophoto, .badge-mismatch,
  .badge-seen, .badge-closure, .badge-dup, .badge-you {
    display: inline-block; font-family: inherit; font-size: 9px;
    font-weight: 700; letter-spacing: 0.08em; padding: 2px 6px;
    border-radius: 2px; text-transform: uppercase; line-height: 1.3;
  }
  .badge-open { color: var(--warn);
                border: 1px solid rgba(251,191,36,0.35); }
  .badge-closed { color: var(--success);
                  border: 1px solid rgba(74,222,128,0.35); }
  .badge-overdue { color: var(--danger);
                   border: 1px solid rgba(248,113,113,0.35); }
  .badge-ai { color: var(--accent);
              border: 1px solid rgba(94,234,212,0.3); }
  .badge-manual { color: var(--blue);
                  border: 1px solid rgba(96,165,250,0.3); }
  .badge-nophoto { color: var(--muted);
                   border: 1px solid var(--border-2); }
  .badge-mismatch { color: var(--warn);
                    border: 1px solid rgba(251,191,36,0.3); }
  .badge-seen { color: var(--muted-2);
                border: 1px solid var(--border); }
  .badge-closure { color: var(--success);
                   border: 1px solid rgba(74,222,128,0.3); }
  .badge-dup { color: #c4b5fd;
               border: 1px solid rgba(196,181,253,0.4); }
  .badge-you { color: var(--accent);
               border: 1px solid rgba(94,234,212,0.3); }
  .q-notification {
    border-radius: 3px !important; font-weight: 500 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 11px !important;
    background: var(--surface-2) !important; color: var(--text) !important;
    border: 1px solid var(--border-2) !important;
    min-height: 30px !important;
  }
  .q-separator { background: var(--border) !important; }
  .scroll-box {
    max-height: 220px; overflow-y: auto;
    border: 1px solid var(--border); border-radius: 3px;
    padding: 6px; margin-top: 6px; background: var(--surface-2);
  }
  .or-divider {
    display: flex; align-items: center; gap: 8px;
    color: var(--muted-2); font-size: 9px; font-weight: 700;
    letter-spacing: 0.18em; margin: 10px 0;
  }
  .or-divider::before, .or-divider::after {
    content: ''; flex: 1; height: 1px; background: var(--border);
  }
  .metric-strip {
    display: grid; grid-template-columns: repeat(3, 1fr);
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 4px; overflow: hidden; margin-bottom: 12px;
  }
  .metric-cell {
    padding: 12px 14px; border-right: 1px solid var(--border);
    border-bottom: 1px solid var(--border);
  }
  .metric-cell:nth-child(3n) { border-right: none; }
  .metric-cell:nth-last-child(-n+3) { border-bottom: none; }
  .metric-label {
    font-size: 9px; font-weight: 700; color: var(--muted-2);
    letter-spacing: 0.14em; text-transform: uppercase;
    margin-bottom: 4px;
  }
  .metric-value {
    font-size: 20px; font-weight: 700; letter-spacing: -0.03em;
    color: var(--text); line-height: 1.1;
    font-variant-numeric: tabular-nums;
  }
  .metric-value.open { color: var(--warn); }
  .metric-value.closed { color: var(--success); }
  .metric-value.overdue { color: var(--danger); }
  .metric-value.accent { color: var(--accent); }
  .sub-row {
    display: grid; grid-template-columns: 1fr auto; gap: 12px;
    padding: 10px 0; border-bottom: 1px solid var(--border);
    align-items: center;
  }
  .sub-row:last-child { border-bottom: none; }
  .sub-name {
    font-size: 12px; font-weight: 600; color: var(--text);
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }
  .sub-badges {
    display: flex; gap: 4px; font-variant-numeric: tabular-nums;
  }
  .log-row {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 3px; padding: 12px 14px; margin-bottom: 6px;
    cursor: pointer; transition: border-color 0.12s;
  }
  .log-row:hover { border-color: var(--border-2); }
  .sub-card { background: var(--surface); border: 1px solid var(--border);
              border-radius: 4px; padding: 14px; margin-bottom: 8px; }
  .chip {
    display: inline-flex; align-items: center; gap: 6px;
    background: var(--surface-2); border: 1px solid var(--border-2);
    color: var(--text); font-size: 11px; font-weight: 500;
    padding: 3px 8px; border-radius: 2px; letter-spacing: 0.01em;
  }
  .chip .q-icon { font-size: 13px; color: var(--accent); }
  .photo-compare {
    display: grid; grid-template-columns: 1fr 1fr;
    gap: 8px; margin-bottom: 12px;
  }
  .photo-grid {
    display: grid; grid-template-columns: repeat(3, 1fr);
    gap: 6px; margin-bottom: 12px;
  }
  .photo-cell { position: relative; }
  .photo-cell .q-img {
    width: 100%; height: 100px; object-fit: cover;
    border-radius: 3px; border: 1px solid var(--border-2);
  }
  .photo-remove {
    position: absolute; top: 3px; right: 3px;
    background: rgba(11,11,11,0.85);
    color: var(--danger); border: 1px solid rgba(248,113,113,0.5);
    width: 20px; height: 20px; border-radius: 2px;
    display: flex; align-items: center; justify-content: center;
    font-size: 12px; font-weight: 700; cursor: pointer;
    z-index: 3;
  }
  .photo-tag {
    position: absolute; top: 6px; left: 6px;
    background: rgba(11,11,11,0.85); color: var(--muted);
    font-size: 9px; font-weight: 700; padding: 2px 6px;
    border-radius: 2px; letter-spacing: 0.1em;
    z-index: 2; text-transform: uppercase;
  }
  .photo-tag.closure { color: var(--success); }
  .q-dialog .q-card {
    background: var(--surface) !important;
    border: 1px solid var(--border-2) !important;
    border-radius: 6px !important; color: var(--text) !important;
  }
  .section-head {
    display: flex; justify-content: space-between; align-items: center;
    margin-bottom: 10px; padding-bottom: 6px;
    border-bottom: 1px solid var(--border);
  }
  .section-head .label { margin: 0; }
  .summary-card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 4px; padding: 14px;
    font-size: 12px; line-height: 1.7; color: var(--text-soft);
    margin-bottom: 12px;
  }
  .summary-card b { color: var(--accent); }
  /* Chat */
  .chat-msg {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 4px; padding: 10px 12px; margin-bottom: 8px;
    display: flex; flex-direction: column; gap: 4px;
  }
  .chat-msg.mine { border-color: rgba(94,234,212,0.4); }
  .chat-head {
    display: flex; justify-content: space-between;
    align-items: center; gap: 8px;
  }
  .chat-author {
    font-size: 11px; font-weight: 700; color: var(--accent);
  }
  .chat-time {
    font-size: 9px; color: var(--muted-2);
    font-variant-numeric: tabular-nums;
  }
  .chat-body {
    font-size: 12px; color: var(--text); line-height: 1.55;
    white-space: pre-wrap; word-break: break-word;
  }
  .chat-reply-quote {
    background: var(--surface-2); border-left: 2px solid var(--accent);
    padding: 4px 8px; font-size: 10px; color: var(--muted);
    border-radius: 2px; margin-bottom: 4px;
  }
  .chat-actions {
    display: flex; gap: 6px; margin-top: 2px;
  }
  .chat-act {
    font-size: 10px; color: var(--muted); cursor: pointer;
    background: none; border: none; padding: 2px 4px;
    font-family: inherit; font-weight: 600;
  }
  .chat-act:hover { color: var(--accent); }
  .chat-act.danger:hover { color: var(--danger); }
  .chat-composer {
    position: sticky; bottom: 0;
    background: var(--bg); border-top: 1px solid var(--border);
    padding: 10px 0 4px; z-index: 5;
  }
  .mention-chip {
    display: inline-block; color: var(--accent); font-weight: 700;
    background: rgba(94,234,212,0.1); padding: 0 4px; border-radius: 2px;
    margin: 0 1px;
  }
  .mention-drop {
    position: absolute; bottom: 100%; left: 0; right: 0;
    background: var(--surface-2); border: 1px solid var(--border-2);
    border-radius: 4px; max-height: 160px; overflow-y: auto;
    z-index: 100;
  }
  .mention-item {
    padding: 6px 10px; font-size: 11px; cursor: pointer;
    color: var(--text);
  }
  .mention-item:hover { background: var(--surface-3); color: var(--accent); }
</style>
""".replace("__DIR__", rtl)
    ui.add_head_html(html)


BTN_PRIMARY = "btn-primary"
BTN_SOFT = "btn-soft"
BTN_SUCCESS = "btn-success"
BTN_OUTLINE = "btn-outline"
BTN_DANGER = "btn-danger"


# =====================================================================
# SVG CHARTS
# =====================================================================
def _svg_line_chart(values, labels, height=200):
    W = 600
    H = height
    PL, PR, PT, PB = 42, 16, 18, 34
    CW = W - PL - PR
    CH = H - PT - PB
    maxv = max(values) if values else 1
    if maxv < 1:
        maxv = 1
    n = len(values)
    stepx = CW / max(n - 1, 1)
    pts = []
    for i, v in enumerate(values):
        x = PL + i * stepx
        y = PT + CH - (v / float(maxv)) * CH
        pts.append((x, y, v))

    poly = " ".join(str(round(x, 1)) + "," + str(round(y, 1))
                    for x, y, _ in pts)
    area = (str(PL) + "," + str(PT + CH) + " " + poly + " " +
            str(round(PL + (n - 1) * stepx, 1)) + "," + str(PT + CH))

    y_ticks = ""
    for i in range(5):
        yv = round(maxv * i / 4.0)
        yy = PT + CH - (i / 4.0) * CH
        y_ticks += (
            '<line x1="' + str(PL) + '" y1="' + str(round(yy, 1)) +
            '" x2="' + str(PL + CW) + '" y2="' + str(round(yy, 1)) +
            '" stroke="#1e1e1e" stroke-width="1"/>'
            '<text x="' + str(PL - 6) + '" y="' + str(round(yy + 3, 1)) +
            '" font-size="9" fill="#5a5a5a" text-anchor="end" '
            'font-family="monospace">' + str(yv) + '</text>'
        )

    x_labels = ""
    for i, (x, _, _) in enumerate(pts):
        if i % 2 == 0 or i == n - 1:
            x_labels += (
                '<text x="' + str(round(x, 1)) + '" y="' + str(H - 12) +
                '" font-size="9" fill="#5a5a5a" text-anchor="middle" '
                'font-family="monospace">' + str(labels[i]) + '</text>'
            )

    dots = ""
    for x, y, v in pts:
        dots += ('<circle cx="' + str(round(x, 1)) + '" cy="' +
                 str(round(y, 1)) + '" r="3" fill="#5eead4" '
                 'stroke="#0b0b0b" stroke-width="1"/>')

    svg = (
        '<svg viewBox="0 0 ' + str(W) + ' ' + str(H) + '" '
        'preserveAspectRatio="xMidYMid meet" '
        'style="width:100%;height:auto;display:block;">'
        '<polygon points="' + area + '" fill="rgba(94,234,212,0.08)"/>'
        '<polyline points="' + poly + '" fill="none" '
        'stroke="#5eead4" stroke-width="1.8"/>'
        + y_ticks + x_labels + dots +
        '</svg>'
    )
    return svg


def _svg_scatter(points, height=220):
    W = 600
    H = height
    PL, PR, PT, PB = 48, 16, 18, 34
    CW = W - PL - PR
    CH = H - PT - PB
    if not points:
        return '<div style="color:#5a5a5a;font-size:11px;' \
               'text-align:center;padding:40px;">No data.</div>'
    maxx = max(p["x"] for p in points) or 1
    maxy = max(p["y"] for p in points) or 1
    if maxx < 1:
        maxx = 1
    if maxy < 1:
        maxy = 1

    grid = ""
    for i in range(5):
        yy = PT + CH - (i / 4.0) * CH
        yv = round(maxy * i / 4.0)
        grid += ('<line x1="' + str(PL) + '" y1="' + str(round(yy, 1)) +
                 '" x2="' + str(PL + CW) + '" y2="' + str(round(yy, 1)) +
                 '" stroke="#1e1e1e" stroke-width="1"/>'
                 '<text x="' + str(PL - 6) + '" y="' + str(round(yy + 3, 1)) +
                 '" font-size="9" fill="#5a5a5a" text-anchor="end" '
                 'font-family="monospace">' + str(yv) + '</text>')
    for i in range(5):
        xx = PL + (i / 4.0) * CW
        xv = round(maxx * i / 4.0)
        grid += ('<line x1="' + str(round(xx, 1)) + '" y1="' + str(PT) +
                 '" x2="' + str(round(xx, 1)) + '" y2="' + str(PT + CH) +
                 '" stroke="#1e1e1e" stroke-width="1"/>'
                 '<text x="' + str(round(xx, 1)) + '" y="' + str(H - 12) +
                 '" font-size="9" fill="#5a5a5a" text-anchor="middle" '
                 'font-family="monospace">' + str(xv) + '</text>')

    dots = ""
    for p in points:
        cx = PL + (p["x"] / float(maxx)) * CW
        cy = PT + CH - (p["y"] / float(maxy)) * CH
        color = "#4ade80" if p["status"] == "closed" else "#f87171"
        dots += ('<circle cx="' + str(round(cx, 1)) + '" cy="' +
                 str(round(cy, 1)) + '" r="4" fill="' + color +
                 '" opacity="0.8" stroke="#0b0b0b" stroke-width="1"/>')

    ylab = ('<text x="14" y="' + str(PT + CH / 2) +
            '" font-size="9" fill="#5a5a5a" text-anchor="middle" '
            'font-family="monospace" transform="rotate(-90 14 ' +
            str(PT + CH / 2) + ')">DURATION (days)</text>')
    xlab = ('<text x="' + str(PL + CW / 2) + '" y="' + str(H - 2) +
            '" font-size="9" fill="#5a5a5a" text-anchor="middle" '
            'font-family="monospace">DAYS OPEN</text>')

    svg = (
        '<svg viewBox="0 0 ' + str(W) + ' ' + str(H) + '" '
        'preserveAspectRatio="xMidYMid meet" '
        'style="width:100%;height:auto;display:block;">'
        + grid + dots + ylab + xlab +
        '</svg>'
    )
    return svg


# =====================================================================
# MAIN
# =====================================================================
def build_defect_ui(user_id):
    _inject_theme()
    user = db.get_user(user_id)

    state = {
        "user_id": user_id, "user": user,
        "project_id": app.storage.user.get("project_id"),
        "project": None, "tab": {"value": "new"},
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
        "background:#0b0b0b;width:320px;max-width:88vw;"
    ) as drawer:
        _build_drawer(state, drawer)

    with ui.element('div').classes("app-header"):
        with ui.element('div').style(
            "display:flex;align-items:center;gap:10px;"
        ):
            ui.button(icon="menu", on_click=drawer.toggle).props(
                "flat round dense size=sm").style("color:#e8e8e8;")
            ui.label(_t("app_title")).classes("brand")
        ui.button(_t("lang_button"), on_click=_toggle_lang).props(
            "flat dense no-caps size=sm").style(
            "color:#e8e8e8;font-weight:600;font-size:10px;"
            "border:1px solid #262626;border-radius:2px;"
            "padding:0 8px;min-height:26px;letter-spacing:0.06em;")

    nav_holder = ui.element('div').classes("top-tabs")
    content = ui.element('div').classes("main-content")

    def _render_tab():
        content.clear()
        with content:
            if not state.get("project_id"):
                _render_no_project(state, _render_tab)
                return
            tab = state["tab"]["value"]
            if tab == "new":
                _build_new_defect(state)
            elif tab == "logs":
                _build_logs(state)
            elif tab == "subs":
                _build_subs(state)
            elif tab == "chat":
                _build_chat(state)
            else:
                _build_dashboard(state)

    def _build_nav():
        nav_holder.clear()
        with nav_holder:
            for key, label in [
                ("new", _t("new_defect")), ("logs", _t("logs")),
                ("subs", _t("subs")), ("chat", _t("chat")),
                ("dashboard", _t("dashboard")),
            ]:
                active = state["tab"]["value"] == key
                cls = "top-tab-btn active" if active else "top-tab-btn"
                btn = ui.element('button').classes(cls)
                with btn:
                    with ui.element('span').style(
                        "display:inline-flex;align-items:center;"
                        "font-family:'JetBrains Mono',monospace;"
                        "font-size:11px;font-weight:600;"
                        "letter-spacing:0.05em;color:inherit;"
                        "background:transparent;"
                    ):
                        ui.label(label).style(
                            "font-family:inherit;color:inherit;"
                            "background:transparent;")
                        if key == "logs":
                            ui.element('span').classes("blink-cursor")

                def _handler(k=key):
                    if state["tab"]["value"] == k:
                        return
                    state["tab"]["value"] = k
                    _build_nav()
                    _render_tab()

                btn.on("click", _handler)

    state["render_main"] = _render_tab
    state["build_nav"] = _build_nav
    _build_nav()
    _render_tab()


def _render_no_project(state, refresh_fn):
    with ui.element('div').classes("card").style(
        "text-align:center;padding:36px 20px;"
    ):
        ui.icon("add_business").style("font-size:32px;color:#5eead4;")
        ui.label(_t("create_first")).classes("h1").style(
            "margin-top:14px;margin-bottom:6px;")
        ui.label(_t("no_projects_hint")).classes("muted")
        ui.element('div').style("height:16px;")

        def _open():
            _open_setup_dialog(state, None, is_new=True,
                                on_created=refresh_fn)
        ui.button(_t("new_project"), icon="add", on_click=_open).classes(
            BTN_PRIMARY).style("width:100%;max-width:280px;")


# =====================================================================
# DASHBOARD
# =====================================================================
def _build_dashboard(state):
    if not state.get("project_id"):
        _render_no_project(state, state["render_main"])
        return
    pid = state["project_id"]

    with ui.element('div').classes("section-head"):
        ui.label(_t("dash_title")).classes("h1")

        def _print_pdf():
            try:
                _build_dashboard_pdf(state, "dashboard.pdf")
            except Exception as ex:
                import traceback
                traceback.print_exc()
                ui.notify("PDF failed: " + str(ex), type="negative")

        with ui.element('div').style("display:flex;gap:6px;"):
            ui.button(_t("dash_print"), icon="picture_as_pdf",
                      on_click=_print_pdf).classes(BTN_SOFT).style(
                "font-size:10px;min-height:28px;")

            def _refresh():
                state["render_main"]()
            ui.button(icon="refresh", on_click=_refresh).props(
                "flat round dense size=sm").style("color:#808080;")

    kpis = db.kpi_summary(pid)

    if not kpis or kpis.get("total", 0) == 0:
        with ui.element('div').classes("card").style(
            "text-align:center;padding:32px;"
        ):
            ui.icon("insights").style("font-size:28px;color:#5a5a5a;")
            ui.label(_t("dash_empty")).classes("muted").style("margin-top:10px;")
        return

    # Summary card
    zones = db.kpi_per_zone(pid)
    weeks = db.kpi_per_week(pid, weeks=8)
    scores = db.subcontractor_scores(pid)
    top_zone = zones[0]["zone"] if zones else "-"
    top_sub = scores[0]["name"] if scores else "-"

    with ui.element('div').classes("summary-card"):
        ui.label(_t("dash_summary")).classes("label").style(
            "margin-bottom:6px;display:block;")
        ui.html(
            "Project has <b>" + str(kpis["total"]) + "</b> defects total. "
            "<b>" + str(kpis["open"]) + "</b> open, "
            "<b>" + str(kpis["closed"]) + "</b> closed, "
            "<b>" + str(kpis["overdue"]) + "</b> overdue. "
            "Average close time: <b>" + str(kpis["avg_days"]) + "d</b>. "
            "Busiest zone: <b>" + str(top_zone) + "</b>. "
            "Top subcontractor by open: <b>" + str(top_sub) + "</b>."
        )

    # Metric strip
    with ui.element('div').classes("metric-strip"):
        _metric_cell(_t("kpi_total"), kpis["total"], "")
        _metric_cell(_t("kpi_open"), kpis["open"], "open")
        _metric_cell(_t("kpi_closed"), kpis["closed"], "closed")
        _metric_cell(_t("kpi_overdue"), kpis["overdue"], "overdue")
        _metric_cell(_t("kpi_closed_7d"), kpis["closed_7d"], "closed")
        _metric_cell(_t("kpi_avg_days"), str(kpis["avg_days"]) + "d", "accent")

    # Line chart — raised per week
    if weeks:
        with ui.element('div').classes("card").style("margin-bottom:12px;"):
            ui.label(_t("dash_weeks")).classes("label").style(
                "margin-bottom:8px;"
            )
            vals = [w["count"] for w in weeks]
            labels = [w["label"] for w in weeks]
            ui.html(_svg_line_chart(vals, labels, height=200))

    # Scatter chart
    scatter = db.defect_scatter_data(pid)
    if scatter:
        with ui.element('div').classes("card").style("margin-bottom:12px;"):
            with ui.element('div').style(
                "display:flex;justify-content:space-between;"
                "align-items:center;margin-bottom:8px;"
            ):
                ui.label(_t("dash_scatter")).classes("label")
                with ui.element('div').style(
                    "display:flex;gap:10px;font-size:9px;"
                    "color:#808080;letter-spacing:0.05em;"
                ):
                    ui.html('<span style="color:#4ade80;">● CLOSED</span>')
                    ui.html('<span style="color:#f87171;">● OPEN</span>')
            ui.html(_svg_scatter(scatter, height=220))

    # Per-sub table
    if scores:
        with ui.element('div').classes("card"):
            ui.label(_t("dash_subs")).classes("label").style(
                "margin-bottom:8px;"
            )
            for s in scores[:10]:
                name = s["name"] or _t("unassigned")
                with ui.element('div').classes("sub-row"):
                    ui.label(str(name)).classes("sub-name")
                    with ui.element('div').classes("sub-badges"):
                        ui.html('<span class="badge-open">' +
                                str(s["open"]) + '</span>')
                        if s["overdue"]:
                            ui.html('<span class="badge-overdue">' +
                                    str(s["overdue"]) + '</span>')
                        ui.html('<span class="badge-closed">' +
                                str(s["closed"]) + '</span>')


def _metric_cell(label, value, variant):
    with ui.element('div').classes("metric-cell"):
        ui.label(label).classes("metric-label")
        cls = "metric-value"
        if variant:
            cls += " " + variant
        ui.label(str(value)).classes(cls)


# =====================================================================
# DASHBOARD PDF
# =====================================================================
def _build_dashboard_pdf(state, filename="dashboard.pdf"):
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable,
    )
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm

    project = state["project"]
    pid = state["project_id"]
    kpis = db.kpi_summary(pid)
    zones = db.kpi_per_zone(pid)
    weeks = db.kpi_per_week(pid, weeks=8)
    scores = db.subcontractor_scores(pid)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=18 * mm, bottomMargin=18 * mm,
    )
    NAVY = colors.HexColor("#0a0a0a")
    ACCENT = colors.HexColor("#14b8a6")
    GREY = colors.HexColor("#525252")

    title_style = ParagraphStyle("T", fontName="Helvetica-Bold",
                                  fontSize=14, textColor=NAVY, spaceAfter=2)
    sub_style = ParagraphStyle("S", fontName="Helvetica",
                                fontSize=9, textColor=ACCENT, spaceAfter=8)
    label_style = ParagraphStyle("L", fontName="Helvetica-Bold",
                                  fontSize=8, textColor=NAVY, leading=11)
    body_style = ParagraphStyle("B", fontName="Helvetica", fontSize=9,
                                 textColor=colors.black, leading=12)
    small_style = ParagraphStyle("Sm", fontName="Helvetica", fontSize=7,
                                  textColor=GREY, leading=9)

    story = []
    story.append(Paragraph("DASHBOARD SUMMARY", title_style))
    story.append(Paragraph(str(project.get("name", "")), sub_style))
    story.append(HRFlowable(width="100%", thickness=0.8, color=ACCENT,
                             spaceAfter=10))

    meta_rows = [
        [Paragraph("<b>Project:</b>", label_style),
         Paragraph(str(project.get("name", "")), body_style),
         Paragraph("<b>Date:</b>", label_style),
         Paragraph(datetime.date.today().strftime("%Y-%m-%d"), body_style)],
        [Paragraph("<b>Contractor:</b>", label_style),
         Paragraph(str(project.get("contractor", "")), body_style),
         Paragraph("<b>Consultant:</b>", label_style),
         Paragraph(str(project.get("consultant", "")), body_style)],
    ]
    t_meta = Table(meta_rows, colWidths=[22*mm, 68*mm, 25*mm, 65*mm])
    t_meta.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 14))

    story.append(Paragraph("KEY METRICS", label_style))
    story.append(Spacer(1, 6))
    kpi_data = [
        ["Total", "Open", "Closed", "Overdue", "Closed-7d", "Avg close (d)"],
        [str(kpis["total"]), str(kpis["open"]), str(kpis["closed"]),
         str(kpis["overdue"]), str(kpis["closed_7d"]),
         str(kpis["avg_days"])],
    ]
    t_kpi = Table(kpi_data, colWidths=[28*mm]*6)
    t_kpi.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F5F5F5")),
        ('BOX', (0, 0), (-1, -1), 0.4, colors.HexColor("#BFBFBF")),
        ('INNERGRID', (0, 0), (-1, -1), 0.3, colors.HexColor("#BFBFBF")),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_kpi)
    story.append(Spacer(1, 16))

    if weeks:
        story.append(Paragraph("RAISED PER WEEK", label_style))
        story.append(Spacer(1, 4))
        wk_data = [["Week"] + [w["label"] for w in weeks]]
        wk_data.append(["Count"] + [str(w["count"]) for w in weeks])
        t_wk = Table(wk_data, colWidths=[20*mm] + [20*mm]*len(weeks))
        t_wk.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#F5F5F5")),
            ('BOX', (0, 0), (-1, -1), 0.4, colors.HexColor("#BFBFBF")),
            ('INNERGRID', (0, 0), (-1, -1), 0.3, colors.HexColor("#BFBFBF")),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        story.append(t_wk)
        story.append(Spacer(1, 16))

    if zones:
        story.append(Paragraph("OPEN BY ZONE", label_style))
        story.append(Spacer(1, 4))
        z_data = [["Zone", "Open"]]
        for z in zones:
            z_data.append([str(z["zone"]), str(z["count"])])
        t_z = Table(z_data, colWidths=[30*mm, 30*mm])
        t_z.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F5F5F5")),
            ('BOX', (0, 0), (-1, -1), 0.4, colors.HexColor("#BFBFBF")),
            ('INNERGRID', (0, 0), (-1, -1), 0.3, colors.HexColor("#BFBFBF")),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(t_z)
        story.append(Spacer(1, 16))

    if scores:
        story.append(Paragraph("PER SUBCONTRACTOR", label_style))
        story.append(Spacer(1, 4))
        s_data = [["Subcontractor", "Open", "Overdue", "Closed", "Total"]]
        for s in scores[:20]:
            s_data.append([
                str(s["name"]),
                str(s["open"]),
                str(s["overdue"]),
                str(s["closed"]),
                str(s["total"]),
            ])
        t_s = Table(s_data, colWidths=[70*mm, 20*mm, 25*mm, 22*mm, 20*mm])
        t_s.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F5F5F5")),
            ('BOX', (0, 0), (-1, -1), 0.4, colors.HexColor("#BFBFBF")),
            ('INNERGRID', (0, 0), (-1, -1), 0.3, colors.HexColor("#BFBFBF")),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8.5),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(t_s)

    story.append(Spacer(1, 20))
    story.append(Paragraph(
        "Generated " + datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
        small_style))

    doc.build(story)
    buf.seek(0)
    ui.download(buf.read(), filename=filename)


# =====================================================================
# SUBS
# =====================================================================
def _build_subs(state):
    if not state.get("project_id"):
        _render_no_project(state, state["render_main"])
        return
    pid = state["project_id"]
    masters = db.list_subcontractors(pid)
    scores = db.subcontractor_scores(pid)
    scores_by_name = {s["name"]: s for s in (scores or [])}

    with ui.element('div').classes("section-head"):
        ui.label(_t("subs_title")).classes("h1")

        def _open_add():
            _open_add_sub_dialog(state, state["render_main"])
        ui.button(icon="add", on_click=_open_add).props(
            "flat round dense size=sm").style("color:#5eead4;")

    ui.label(_t("subs_sub")).classes("muted").style("margin-bottom:14px;")

    if not masters:
        with ui.element('div').classes("card").style(
            "text-align:center;padding:32px;"
        ):
            ui.icon("engineering").style("font-size:28px;color:#5a5a5a;")
            ui.label(_t("no_subs")).classes("h3").style("margin-top:10px;")
            ui.label(_t("no_subs_hint")).classes("muted").style("margin-top:4px;")
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
                        meta_bits.append(str(m["phone"]))
                    if meta_bits:
                        ui.label(" · ".join(meta_bits)).classes("mono-sm")
                    if not m.get("from_master"):
                        ui.html('<span class="badge-seen">' +
                                _t("from_defects") + '</span>').style(
                            "margin-top:6px;display:inline-block;")

                if m.get("id"):
                    def _del(sub_id=m["id"]):
                        _confirm_delete_sub(state, sub_id, state["render_main"])
                    ui.button(icon="close", on_click=_del).props(
                        "flat round dense size=sm").style("color:#5a5a5a;")

            with ui.element('div').style(
                "display:flex;gap:6px;flex-wrap:wrap;margin-top:10px;"
            ):
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
                    ui.label(_t("no_data")).classes("mono-sm")

            if score["total"]:
                with ui.element('div').style(
                    "display:grid;grid-template-columns:1fr 1fr;gap:6px;"
                    "margin-top:10px;"
                ):
                    def _view(nm=name):
                        state["sub_filter"] = nm
                        state["tab"]["value"] = "logs"
                        if state.get("build_nav"):
                            state["build_nav"]()
                        state["render_main"]()

                    def _pdf(nm=name, sc=score):
                        try:
                            rows = [r for r in db.list_defects(pid)
                                    if (r.get("subcontractor") or "") == nm]
                            pdf = svc.build_sub_pdf(
                                state["project"], nm, sc, rows,
                                logo_bytes=state["project"].get("logo_bytes"))
                            ui.download(pdf, filename="sub_" +
                                        nm.replace(" ", "_") + ".pdf")
                        except Exception as ex:
                            import traceback
                            traceback.print_exc()
                            ui.notify("PDF failed: " + str(ex),
                                       type="negative")

                    ui.button(_t("view_defects"), icon="list_alt",
                              on_click=_view).classes(BTN_SOFT).style(
                        "width:100%;font-size:10px;min-height:30px;")
                    ui.button(_t("download_sub_pdf"), icon="picture_as_pdf",
                              on_click=_pdf).classes(BTN_SOFT).style(
                        "width:100%;font-size:10px;min-height:30px;")


def _open_add_sub_dialog(state, refresh_fn):
    if not state.get("project_id"):
        ui.notify(_t("setup_first"), type="warning")
        return
    with ui.dialog() as dlg, ui.card().style(
        "padding:20px;min-width:320px;max-width:95vw;width:440px;"
    ):
        ui.label(_t("add_sub_title")).classes("h1").style("margin-bottom:14px;")
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
            ui.timer(0.03, refresh_fn, once=True)

        with ui.element('div').style("display:flex;gap:8px;margin-top:16px;"):
            ui.button(_t("add"), on_click=_save).classes(
                BTN_PRIMARY).style("flex:1;")
            ui.button(_t("cancel"), on_click=dlg.close).classes(BTN_SOFT)
    dlg.open()


def _confirm_delete_sub(state, sub_id, refresh_fn):
    with ui.dialog() as dlg, ui.card().style(
        "padding:20px;min-width:280px;max-width:95vw;width:380px;"
    ):
        ui.label(_t("delete_sub_confirm")).classes("h3").style(
            "margin-bottom:14px;")

        def _yes():
            db.delete_subcontractor(sub_id)
            ui.notify(_t("sub_deleted"), type="positive")
            dlg.close()
            ui.timer(0.03, refresh_fn, once=True)

        with ui.element('div').style("display:flex;gap:8px;"):
            ui.button(_t("delete_sub"), on_click=_yes).classes(
                BTN_DANGER).style("flex:1;")
            ui.button(_t("cancel_btn"), on_click=dlg.close).classes(BTN_SOFT)
    dlg.open()


# =====================================================================
# DRAWER
# =====================================================================
def _build_drawer(state, drawer):
    holder = ui.element('div').style(
        "padding:16px;width:100%;box-sizing:border-box;")

    def refresh():
        holder.clear()
        with holder:
            proj = state.get("project") or {}
            user = state.get("user") or {}

            with ui.element('div').style(
                "display:flex;align-items:center;gap:10px;"
                "padding-bottom:12px;border-bottom:1px solid #1e1e1e;"
                "margin-bottom:12px;"
            ):
                if proj.get("logo_bytes"):
                    ui.image(io.BytesIO(proj["logo_bytes"])).style(
                        "width:36px;height:36px;object-fit:contain;"
                        "border-radius:3px;border:1px solid #1e1e1e;"
                        "background:#161616;padding:3px;")
                else:
                    with ui.element('div').style(
                        "width:36px;height:36px;border-radius:3px;"
                        "background:#161616;border:1px solid #1e1e1e;"
                        "display:flex;align-items:center;"
                        "justify-content:center;color:#5a5a5a;"
                    ):
                        ui.icon("business").style("font-size:16px;")
                with ui.element('div').style("flex:1;min-width:0;"):
                    if proj.get("name"):
                        ui.label(proj.get("name", "")).style(
                            "font-size:12px;font-weight:600;color:#e8e8e8;"
                            "white-space:nowrap;overflow:hidden;"
                            "text-overflow:ellipsis;")
                        ui.label(_t("project")).classes("label").style(
                            "font-size:9px;")
                    else:
                        ui.label(_t("no_project")).style(
                            "font-size:12px;font-weight:600;color:#808080;")

            def _open_chooser():
                _open_project_chooser(state, refresh, state["render_main"])
            ui.button(_t("switch_project"), icon="swap_horiz",
                      on_click=_open_chooser).classes(BTN_SOFT).style(
                "width:100%;margin-bottom:10px;font-size:10px;"
                "min-height:30px;")

            if proj.get("name"):
                _kv(_t("contractor"), proj.get("contractor", ""))
                _kv(_t("subcontractor"), proj.get("subcontractor", ""))
                _kv(_t("consultant"), proj.get("consultant", ""))
                _kv(_t("location"), proj.get("location", ""))
                _kv(_t("engineer"), proj.get("engineer_name", ""))

                def open_setup():
                    _open_setup_dialog(state, refresh, is_new=False)
                ui.button(_t("edit"), icon="settings",
                          on_click=open_setup).classes(BTN_SOFT).style(
                    "width:100%;margin-top:10px;font-size:10px;"
                    "min-height:30px;")

                ui.element('div').style(
                    "border-top:1px solid #1e1e1e;margin:14px 0 12px;")

                with ui.element('div').style(
                    "display:flex;justify-content:space-between;"
                    "align-items:center;margin-bottom:8px;"
                ):
                    ui.label(_t("ms_section")).classes("label")
                    if state.get("project_id"):
                        def open_ms():
                            _open_ms_dialog(state, refresh)
                        ui.button(icon="add", on_click=open_ms).props(
                            "flat round dense size=sm").style("color:#5eead4;")

                ms_list = db.list_ms(state["project_id"])
                if not ms_list:
                    ui.label(_t("no_ms")).classes("mono-sm")
                else:
                    for m in ms_list:
                        with ui.element('div').classes("item-box"):
                            ui.label(m["ms_number"] + "  " + m["title"]).style(
                                "font-size:10px;font-weight:600;"
                                "color:#e8e8e8;margin-bottom:3px;")
                            ui.label(
                                m["element_type"] + " · " + m["discipline"] +
                                " · " + str(len(m["clauses"])) + " " +
                                _t("clauses_count")
                            ).classes("mono-sm").style("font-size:9px;")

            ui.element('div').style(
                "border-top:1px solid #1e1e1e;margin:14px 0 12px;")
            if user:
                ui.label(_t("signed_in_as")).classes("label").style(
                    "font-size:9px;margin-bottom:3px;")
                ui.label(user.get("name") or user.get("email") or "").style(
                    "font-size:11px;color:#e8e8e8;font-weight:500;"
                    "margin-bottom:10px;")

            def _change_pw():
                _open_change_password_dialog(state)

            ui.button("Change password", icon="password",
                      on_click=_change_pw).classes(BTN_SOFT).style(
                "width:100%;font-size:10px;min-height:30px;"
                "margin-bottom:6px;")

            ui.button(_t("logout"), icon="logout",
                      on_click=lambda: ui.navigate.to("/logout")).classes(
                BTN_SOFT).style("width:100%;font-size:10px;min-height:30px;")

    state["refresh_drawer"] = refresh
    refresh()


def _kv(label, value):
    if not value:
        return
    with ui.element('div').style("margin-bottom:8px;"):
        ui.label(label).classes("label").style(
            "font-size:9px;margin-bottom:2px;display:block;")
        ui.label(str(value)).style(
            "font-size:11px;color:#e8e8e8;font-weight:500;")


# =====================================================================
# PROJECT CHOOSER
# =====================================================================
def _open_project_chooser(state, refresh_drawer, refresh_main):
    projects = db.list_projects(state["user_id"]) or []
    with ui.dialog() as dlg, ui.card().style(
        "padding:20px;min-width:320px;max-width:95vw;width:460px;"
    ):
        ui.label(_t("projects_title")).classes("h1").style("margin-bottom:14px;")
        if not projects:
            ui.label(_t("no_projects_hint")).classes("muted").style(
                "margin-bottom:14px;")
        else:
            for p in projects:
                is_current = (p["id"] == state.get("project_id"))
                border = "#5eead4" if is_current else "#1e1e1e"
                with ui.element('div').style(
                    "background:#161616;border:1px solid " + border + ";"
                    "border-radius:3px;padding:10px 12px;margin-bottom:6px;"
                    "cursor:pointer;"
                ) as card:
                    ui.label(p.get("name") or "(untitled)").style(
                        "font-size:12px;font-weight:600;color:#e8e8e8;")
                    loc = p.get("location") or ""
                    if loc:
                        ui.label(loc).classes("mono-sm")

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
                return
            _confirm_delete(state, dlg, refresh_drawer, refresh_main)
        ui.button(_t("delete_project"), icon="close", on_click=_delete).props(
            "flat").style("width:100%;color:#f87171;margin-top:6px;"
                          "font-size:10px;")
    dlg.open()


def _confirm_delete(state, parent_dlg, refresh_drawer, refresh_main):
    pid = state.get("project_id")
    with ui.dialog() as dlg2, ui.card().style(
        "padding:20px;min-width:280px;max-width:95vw;width:380px;"
    ):
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
                BTN_DANGER).style("flex:1;")
            ui.button(_t("cancel_btn"), on_click=dlg2.close).classes(BTN_SOFT)
    dlg2.open()


# =====================================================================
# SETUP DIALOG
# =====================================================================
def _open_setup_dialog(state, refresh_drawer, is_new=False, on_created=None):
    proj = {} if is_new else (state.get("project") or {})
    with ui.dialog() as dlg, ui.card().style(
        "padding:20px;min-width:320px;max-width:95vw;width:440px;"
    ):
        ui.label(_t("setup_title")).classes("h1").style("margin-bottom:14px;")
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
                    try: hook()
                    except Exception: pass
                if refresh_drawer:
                    try: refresh_drawer()
                    except Exception: pass
                if on_created:
                    on_created()
                else:
                    state["render_main"]()
            except Exception as ex:
                import traceback
                traceback.print_exc()
                ui.notify("Save failed: " + str(ex), type="negative")

        with ui.element('div').style("display:flex;gap:8px;margin-top:16px;"):
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
        "padding:20px;min-width:320px;max-width:95vw;width:500px;"
    ):
        ui.label(_t("ms_dialog_title")).classes("h1").style("margin-bottom:14px;")
        holder = {"bytes": None, "name": ""}
        file_status = ui.label("").classes("mono-sm").style("margin-top:6px;")

        async def handle_file(e):
            holder["bytes"] = await e.file.read()
            holder["name"] = e.file.name
            file_status.set_text(_t("file_loaded") + e.file.name +
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
        preview = ui.element('div').style("width:100%;margin-top:10px;")

        async def extract():
            if not holder["bytes"]:
                ui.notify(_t("upload_first"), type="warning")
                return
            preview.clear()
            with preview:
                ui.label(_t("extracting")).classes("mono-sm")
            result = await svc.extract_clauses_from_pdf(
                holder["bytes"], call_gemini_json, holder["name"])
            preview.clear()
            if result.get("error"):
                with preview:
                    ui.label(_t("error_prefix") + str(result["error"])).style(
                        "color:#f87171;font-size:10px;")
                return
            clauses = result["clauses"]
            with preview:
                ui.label(_t("extracted") + " " + str(len(clauses)) + " " +
                          _t("clauses_count")).style(
                    "font-size:10px;font-weight:600;color:#e8e8e8;"
                    "margin-bottom:6px;display:block;")
                with ui.element('div').classes("scroll-box"):
                    for cl in clauses:
                        with ui.element('div').style(
                            "padding:6px;border-bottom:1px solid #1e1e1e;"
                        ):
                            ui.label("§" + cl["id"] + "  " + cl["title"]).style(
                                "font-size:10px;font-weight:600;color:#e8e8e8;")
                            ui.label(cl["text"][:180]).classes("mono-sm").style(
                                "font-size:9px;margin-top:2px;")

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
                        try: refresh_drawer()
                        except Exception: pass
                    hook = state.get("refresh_drawer")
                    if hook:
                        try: hook()
                        except Exception: pass

                ui.button(_t("confirm_save"), on_click=confirm).classes(
                    BTN_SUCCESS).style("width:100%;margin-top:10px;")

        with ui.element('div').style("display:flex;gap:8px;margin-top:16px;"):
            ui.button(_t("extract"), on_click=extract).classes(
                BTN_PRIMARY).style("flex:1;")
            ui.button(_t("cancel_btn"), on_click=dlg.close).classes(BTN_SOFT)
        preview
    dlg.open()


# =====================================================================
# NEW DEFECT
# =====================================================================
def _build_new_defect(state):
    if not state.get("project_id"):
        _render_no_project(state, state["render_main"])
        return
    stage = {"photos": [], "mime": "image/jpeg",
             "candidates": None, "manual": [],
             "text_only": False, "text_desc": ""}

    with ui.element('div').classes("card").style("margin-bottom:12px;"):
        ui.label(_t("photo_title")).classes("h1").style("margin-bottom:3px;")
        ui.label(_t("photo_sub")).classes("muted").style("margin-bottom:12px;")

        photos_holder = ui.element('div').style("width:100%;")

        def render_photos():
            photos_holder.clear()
            with photos_holder:
                if not stage["photos"]:
                    return
                with ui.element('div').classes("photo-grid"):
                    for i, p in enumerate(stage["photos"]):
                        with ui.element('div').classes("photo-cell"):
                            def _rm(idx=i):
                                stage["photos"].pop(idx)
                                render_photos()
                                rebuild_body()
                            ui.html('<div class="photo-remove">\u00d7</div>'
                                    ).on("click", _rm)
                            try:
                                b64 = base64.b64encode(p).decode("ascii")
                                ui.image("data:image/jpeg;base64," + b64)
                            except Exception:
                                pass

        async def handle_photo(e):
            try:
                data = await e.file.read()
            except Exception as ex:
                ui.notify(_t("upload_failed") + str(ex), type="negative")
                return
            if not data:
                ui.notify(_t("empty_file"), type="warning")
                return
            stage["photos"].append(data)
            if e.file.name.lower().endswith((".jpg", ".jpeg")):
                stage["mime"] = "image/jpeg"
            else:
                stage["mime"] = "image/png"
            stage["candidates"] = None
            stage["manual"] = []
            stage["text_only"] = False
            ui.notify(_t("photo_received") + " — " +
                       str(len(stage["photos"])) + " " +
                       _t("photos_count"), type="positive")
            render_photos()
            ui.timer(0.2, rebuild_body, once=True)

        render_photos()

        ui.upload(on_upload=handle_photo, auto_upload=True).style(
            "width:100%;").props("flat bordered accept=image/* multiple "
                                  "label='" +
                                  (_t("add_photos") if stage["photos"]
                                   else _t("choose_photo")) + "'")

        with ui.element('div').classes("or-divider"):
            ui.label(_t("or_divider"))

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
        "padding:20px;min-width:320px;max-width:95vw;width:500px;"
    ):
        ui.label(_t("no_photo_title")).classes("h1").style("margin-bottom:3px;")
        ui.label(_t("no_photo_sub")).classes("muted").style("margin-bottom:14px;")
        desc_in = ui.textarea(label=_t("defect_desc"),
                                placeholder=_t("defect_desc_placeholder")).style(
            "width:100%;")
        note_in = ui.textarea(label=_t("extra_note"),
                                placeholder=_t("extra_note_placeholder")).style(
            "width:100%;")
        with ui.element('div').style(
            "display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:8px;"
        ):
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
            stage["photos"] = []
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
            ui.timer(0.15, refresh_fn, once=True)

        btn.on("click", do_analyze)
        btn.classes(BTN_PRIMARY).style("width:100%;margin-top:12px;")
        with ui.element('div').style("margin-top:6px;"):
            ui.button(_t("cancel_btn"), on_click=dlg.close).classes(
                BTN_SOFT).style("width:100%;")
    dlg.open()


def _render_body_contents(state, stage, refresh_fn):
    if not state.get("project_id"):
        return
    has_photos = bool(stage.get("photos"))
    has_text = bool(stage.get("text_only"))
    has_candidates = stage.get("candidates") is not None
    if not has_photos and not has_text:
        return

    if has_photos and not has_candidates:
        with ui.element('div').classes("card"):
            note_in = ui.textarea(label=_t("note_label"),
                                    placeholder=_t("note_placeholder")).style(
                "width:100%;")
            with ui.element('div').style(
                "display:grid;grid-template-columns:1fr 1fr;gap:8px;"
                "margin-top:8px;"
            ):
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
                    photo_bytes=stage["photos"][0], mime_type=stage["mime"],
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
                ui.timer(0.15, refresh_fn, once=True)

            analyze_btn.on("click", do_analyze)
            analyze_btn.classes(BTN_PRIMARY).style("width:100%;margin-top:12px;")
        return
    if has_text and not has_candidates:
        return
    _render_candidates(state, stage, refresh_fn)


def _duplicate_count(state, name):
    try:
        if not state.get("project_id") or not name:
            return 0
        return len(db.find_similar_defects(state["project_id"], name,
                                            days=60, limit=5))
    except Exception:
        return 0


def _render_candidates(state, stage, refresh_fn):
    all_items = stage["candidates"] + stage["manual"]
    with ui.element('div').classes("card").style("margin-bottom:12px;"):
        if stage["candidates"]:
            ui.label(_t("ai_found")).classes("h3").style(
                "margin-bottom:10px;color:#b8b8b8;")
        else:
            ui.label(_t("ai_found_none")).classes("h3").style(
                "margin-bottom:10px;color:#b8b8b8;")
        for c in list(all_items):
            _render_defect_card(c, stage, refresh_fn, state)

        def _open_add():
            _open_add_dialog(stage, refresh_fn)
        ui.button(_t("add_manual"), icon="add", on_click=_open_add).classes(
            BTN_SOFT).style("width:100%;margin-top:4px;")

    with ui.element('div').classes("card"):
        ui.label(_t("notice_details")).classes("h1").style("margin-bottom:12px;")
        sub_in = ui.input(
            _t("send_to"),
            value=(state["project"] or {}).get("subcontractor", "") or "",
            placeholder=_t("send_to_placeholder")).style("width:100%;")
        with ui.element('div').style(
            "display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:8px;"
        ):
            deadline_in = ui.select(
                {"1": "1 " + _t("days"), "2": "2 " + _t("days"),
                 "3": "3 " + _t("days"), "5": "5 " + _t("days"),
                 "7": "7 " + _t("days"), "14": "14 " + _t("days")},
                value="3", label=_t("deadline"))
            raise_in = ui.select(
                {"qc_internal": _t("qc_internal"),
                 "consultant": _t("consultant_ncr")},
                value="qc_internal", label=_t("raised_as"))

        # NEW: engineer name + place
        engineer_in = ui.input(
            _t("engineer_field"),
            value=(state["project"] or {}).get("engineer_name", "") or ""
        ).style("width:100%;margin-top:8px;")
        place_in = ui.input(
            _t("place_field"), placeholder=_t("place_placeholder")
        ).style("width:100%;margin-top:8px;")

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
            photos_list = stage.get("photos") or []
            try:
                pdf_bytes = svc.build_notice_pdf(
                    project=state["project"], defects=clean_selected,
                    notice_uid=notice_uid, subcontractor=sub_in.value.strip(),
                    deadline_days=int(deadline_in.value),
                    raise_type=raise_in.value,
                    logo_bytes=state["project"].get("logo_bytes"),
                    photos=photos_list)
            except Exception as ex:
                import traceback
                traceback.print_exc()
                ui.notify("PDF failed: " + str(ex), type="negative")
                return
            db.save_defect(
                project_id=state["project_id"], uid=notice_uid,
                zone=stage.get("zone", "A"),
                subcontractor=sub_in.value.strip(),
                deadline_days=int(deadline_in.value),
                raise_type=raise_in.value,
                photo_bytes=(photos_list[0] if photos_list else None),
                note=stage.get("note", ""), selected=clean_selected,
                notice_pdf=pdf_bytes,
                extra_photos=photos_list[1:] if len(photos_list) > 1 else [],
                engineer_name=engineer_in.value or "",
                place=place_in.value or "")
            ui.notify(_t("notice_saved") + " " + notice_uid, type="positive")
            ui.download(pdf_bytes, filename=notice_uid + ".pdf")
            stage["photos"] = []
            stage["candidates"] = None
            stage["manual"] = []
            stage["text_only"] = False
            stage["text_desc"] = ""
            ui.timer(0.15, refresh_fn, once=True)

        gen_btn.on("click", do_generate)
        gen_btn.classes(BTN_PRIMARY).style("width:100%;margin-top:14px;")


def _render_defect_card(item, stage, refresh_fn, state=None):
    with ui.element('div').classes("item-box"):
        with ui.element('div').style(
            "display:flex;gap:10px;align-items:flex-start;"
        ):
            def _toggle(e):
                item["_sel"] = bool(e.value)
            ui.checkbox(value=item.get("_sel", True),
                         on_change=_toggle).props("dense size=sm")
            with ui.element('div').style("flex:1;min-width:0;"):
                with ui.element('div').style(
                    "display:flex;gap:4px;flex-wrap:wrap;margin-bottom:5px;"
                ):
                    if item.get("_manual"):
                        ui.html('<span class="badge-manual">' +
                                _t("tag_manual") + '</span>')
                    elif item.get("_nophoto"):
                        ui.html('<span class="badge-nophoto">' +
                                _t("tag_nophoto") + '</span>')
                    else:
                        ui.html('<span class="badge-ai">' +
                                _t("tag_ai") + '</span>')
                    if item.get("context_mismatch"):
                        ui.html('<span class="badge-mismatch">' +
                                _t("mismatch_warn") + '</span>')
                    if state:
                        n = _duplicate_count(state, item.get("name", ""))
                        if n > 0:
                            ui.html('<span class="badge-dup">' +
                                    _t("tag_dup").replace("{n}", str(n)) +
                                    '</span>')
                ui.label(str(item.get("name", ""))).classes("mono-lg").style(
                    "margin-bottom:5px;")
                if item.get("location_hint"):
                    ui.label(str(item["location_hint"])).classes("mono-sm")
                cit = []
                if item.get("ms_violations"):
                    cit.append("MS:" + ",".join(item["ms_violations"]))
                if item.get("code_violations"):
                    cit.append("ECP:" + ",".join(item["code_violations"]))
                if cit:
                    ui.label(" ".join(cit)).classes("mono-sm").style(
                        "margin-top:2px;")
                if item.get("repair_action"):
                    ui.label(">" + str(item["repair_action"])).classes(
                        "mono-sm").style("margin-top:3px;")
                sev = _severity_options().get(
                    item.get("severity", "Medium"),
                    item.get("severity", "Medium"))
                ui.label("[" + sev + "]").classes("mono-sm").style(
                    "margin-top:3px;")

            def _remove():
                if item in stage["candidates"]:
                    stage["candidates"].remove(item)
                if item in stage["manual"]:
                    stage["manual"].remove(item)
                ui.timer(0.03, refresh_fn, once=True)
            ui.button(icon="close", on_click=_remove).props(
                "flat round dense size=sm").style("color:#5a5a5a;")


def _open_add_dialog(stage, refresh_fn):
    with ui.dialog() as dlg, ui.card().style(
        "padding:20px;min-width:320px;max-width:95vw;width:440px;"
    ):
        ui.label(_t("add_defect_title")).classes("h1").style("margin-bottom:12px;")
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
                "context_mismatch": False, "_sel": True, "_manual": True})
            dlg.close()
            ui.timer(0.03, refresh_fn, once=True)

        with ui.element('div').style("display:flex;gap:8px;margin-top:14px;"):
            ui.button(_t("add"), on_click=_save).classes(
                BTN_PRIMARY).style("flex:1;")
            ui.button(_t("cancel"), on_click=dlg.close).classes(BTN_SOFT)
    dlg.open()


# =====================================================================
# LOGS (with search & filter — FIXED)
# =====================================================================
def _build_logs(state):
    if not state.get("project_id"):
        _render_no_project(state, state["render_main"])
        return
    with ui.element('div').classes("section-head"):
        ui.label(_t("logs_title")).classes("h1")

        def _refresh():
            state["render_main"]()
        ui.button(icon="refresh", on_click=_refresh).props(
            "flat round dense size=sm").style("color:#808080;")

    ui.label(_t("logs_sub")).classes("muted").style("margin-bottom:12px;")

    if state.get("sub_filter"):
        with ui.element('div').style(
            "display:flex;align-items:center;gap:8px;margin-bottom:12px;"
        ):
            with ui.element('span').classes("chip"):
                ui.icon("engineering")
                ui.label(str(state["sub_filter"]))

            def _clear():
                state["sub_filter"] = None
                state["render_main"]()
            ui.button(_t("clear_filter"), on_click=_clear).props(
                "flat dense no-caps size=sm").style(
                "color:#5eead4;font-weight:600;font-size:10px;"
                "min-height:26px;")

    fstate = {"filter": "all", "query": ""}

    @ui.refreshable
    def log_list():
        all_rows = db.list_defects(state["project_id"]) or []
        rows = all_rows
        if fstate["filter"] != "all":
            rows = [r for r in rows if r.get("raise_type") == fstate["filter"]]
        if state.get("sub_filter"):
            rows = [r for r in rows
                    if (r.get("subcontractor") or "") == state["sub_filter"]]
        if fstate["query"]:
            q = fstate["query"]
            def _match(r):
                hay = " ".join([
                    str(r.get("uid", "")),
                    str(r.get("zone", "")),
                    str(r.get("subcontractor", "")),
                    str(r.get("first_defect", "")),
                    str(r.get("status", "")),
                    str(r.get("engineer_name", "")),
                    str(r.get("place", "")),
                ]).lower()
                return q in hay
            rows = [r for r in rows if _match(r)]

        def on_filter_change(e):
            fstate["filter"] = (e.value if e and e.value else "all")
            log_list.refresh()

        def on_search_change(e):
            fstate["query"] = (e.value or "").strip().lower()
            log_list.refresh()

        with ui.element('div').style("margin-bottom:10px;"):
            ui.select(
                {"all": _t("filter_all"),
                 "qc_internal": _t("filter_qc"),
                 "consultant": _t("filter_consultant")},
                value=fstate["filter"],
                on_change=on_filter_change
            ).style("width:100%;").props("dense")

        ui.input(placeholder=_t("search_placeholder"),
                  on_change=on_search_change).style(
            "width:100%;margin-bottom:12px;").props("dense clearable")

        if rows:
            open_count = sum(1 for r in rows if r["status"] == "open")
            ui.label(
                str(len(rows)) + " · " + _t("open") + " " + str(open_count) +
                " · " + _t("closed") + " " + str(len(rows) - open_count)
            ).classes("mono-sm").style("margin-bottom:10px;")

        with ui.element('div').style(
            "display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px;"
            "margin-bottom:12px;"
        ):
            def export_register():
                if not rows:
                    ui.notify(_t("no_rows"), type="warning")
                    return
                pdf = svc.build_register_pdf(
                    state["project"], rows,
                    logo_bytes=state["project"].get("logo_bytes"))
                ui.download(pdf, filename="defect_register.pdf")

            def export_closure():
                if not rows:
                    ui.notify(_t("no_rows"), type="warning")
                    return
                pdf = svc.build_closure_pdf(
                    state["project"], rows,
                    logo_bytes=state["project"].get("logo_bytes"))
                ui.download(pdf, filename="closure_report.pdf")

            def export_excel():
                if not rows:
                    ui.notify(_t("no_rows"), type="warning")
                    return
                try:
                    xlsx = svc.build_register_xlsx(
                        state["project"], rows,
                        logo_bytes=state["project"].get("logo_bytes"))
                    ui.download(xlsx, filename="defect_register.xlsx")
                except Exception as ex:
                    import traceback
                    traceback.print_exc()
                    ui.notify("Excel failed: " + str(ex), type="negative")

            ui.button(_t("export_register"), on_click=export_register).classes(
                BTN_SOFT).style("width:100%;font-size:10px;")
            ui.button(_t("closure_report"), on_click=export_closure).classes(
                BTN_SOFT).style("width:100%;font-size:10px;")
            ui.button(_t("export_excel"), on_click=export_excel).classes(
                BTN_SOFT).style("width:100%;font-size:10px;")

        if not rows:
            msg = _t("no_match") if fstate["query"] else _t("no_logs")
            ui.label(msg).classes("mono-sm").style(
                "text-align:center;padding:32px 0;")
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

    with ui.element('div').classes("log-row") as card:
        with ui.element('div').style(
            "display:flex;justify-content:space-between;"
            "align-items:flex-start;gap:10px;"
        ):
            with ui.element('div').style("flex:1;min-width:0;"):
                ui.label(str(title) + extra).classes("mono-lg").style(
                    "margin-bottom:4px;")
                eng = row.get("engineer_name") or ""
                place = row.get("place") or ""
                subline = (row.get("uid", "") + "  " +
                           str(row.get("zone", "")) + "  " +
                           str(row.get("subcontractor", "")))
                ui.label(subline).classes("mono-sm")
                # Engineer + place line
                bits = []
                if eng:
                    bits.append(_t("raised_by") + ": " + str(eng))
                if place:
                    bits.append(_t("at_place") + ": " + str(place))
                if bits:
                    ui.label("  ·  ".join(bits)).classes("mono-sm").style(
                        "margin-top:2px;")
            ui.html('<span class="' + badge + '">' + badge_txt + '</span>')

        def _click():
            _show_defect_dialog(row.get("id"), refresh_fn)
        card.on("click", _click)


# =====================================================================
# DEFECT DETAIL / EDIT / DELETE
# =====================================================================
def _show_defect_dialog(defect_id, on_close_cb):
    d = db.get_defect(defect_id)
    if not d:
        ui.notify(_t("not_found"), type="negative")
        return
    is_consultant = (d.get("raise_type") or "qc_internal") == "consultant"

    with ui.dialog() as dialog, ui.card().style(
        "padding:0;max-width:560px;width:95vw;overflow:hidden;"
    ):
        with ui.element('div').style(
            "padding:16px 16px 12px;border-bottom:1px solid #1e1e1e;"
        ):
            ui.label(_t("notice") + " " + d["uid"]).classes("h2")
            ui.label(
                "ZONE " + str(d["zone"]) + "  " + str(d["subcontractor"])
            ).classes("mono-sm").style("margin-top:4px;")
            if d.get("engineer_name") or d.get("place"):
                bits = []
                if d.get("engineer_name"):
                    bits.append(_t("raised_by") + ": " + str(d["engineer_name"]))
                if d.get("place"):
                    bits.append(_t("at_place") + ": " + str(d["place"]))
                ui.label("  ·  ".join(bits)).classes("mono-sm").style(
                    "margin-top:2px;")
            if d.get("consultant_ncr"):
                ui.label(_t("ncr_input") + ": " +
                          str(d["consultant_ncr"])).style(
                    "color:#fbbf24;font-size:11px;font-weight:600;"
                    "margin-top:6px;")

        with ui.element('div').style(
            "padding:16px;max-height:60vh;overflow-y:auto;"
        ):
            photos = []
            if d.get("photo_bytes"):
                photos.append(d["photo_bytes"])
            for p in (d.get("extra_photos") or []):
                photos.append(p)

            if photos:
                with ui.element('div').classes("photo-grid"):
                    for p in photos[:6]:
                        try:
                            b64 = base64.b64encode(p).decode("ascii")
                            ui.image("data:image/jpeg;base64," + b64)
                        except Exception:
                            pass

            if d.get("closure_photo"):
                _photo_box(d["closure_photo"],
                            _t("closure_photo_short"), is_closure=True)

            if d.get("note"):
                ui.label("> " + str(d["note"])).classes("soft").style(
                    "margin-bottom:12px;font-style:italic;")

            for i, s in enumerate(d["selected"], 1):
                with ui.element('div').classes("item-box"):
                    ui.label(str(i) + ". " + str(s.get("name", ""))).classes(
                        "mono-lg").style("margin-bottom:4px;")
                    cit = []
                    if s.get("ms_violations"):
                        cit.append("MS:" + ",".join(s["ms_violations"]))
                    if s.get("code_violations"):
                        cit.append("ECP:" + ",".join(s["code_violations"]))
                    if cit:
                        ui.label(" ".join(cit)).classes("mono-sm")
                    if s.get("repair_action"):
                        ui.label(">" + str(s["repair_action"])).classes(
                            "mono-sm").style("margin-top:3px;")

        with ui.element('div').style(
            "padding:12px 16px 16px;border-top:1px solid #1e1e1e;"
            "display:flex;flex-direction:column;gap:6px;"
        ):
            if d.get("notice_pdf"):
                ui.button(_t("download_pdf"), icon="download",
                          on_click=lambda: ui.download(
                              d["notice_pdf"], filename=d["uid"] + ".pdf")
                          ).classes(BTN_SOFT).style("width:100%;")

            with ui.element('div').style(
                "display:grid;grid-template-columns:1fr 1fr;gap:6px;"
            ):
                def _edit():
                    dialog.close()
                    _open_edit_defect_dialog(d, on_close_cb)

                def _delete():
                    dialog.close()
                    _open_delete_defect_dialog(d, on_close_cb)

                ui.button(_t("edit_defect"), icon="edit",
                          on_click=_edit).classes(BTN_SOFT).style(
                    "width:100%;")
                ui.button(_t("delete_defect"), icon="delete",
                          on_click=_delete).classes(BTN_DANGER).style(
                    "width:100%;")

            if d["status"] == "open":
                def _open_close():
                    _open_close_defect_dialog(d, is_consultant,
                                                dialog, on_close_cb)
                ui.button(_t("mark_closed"), icon="check",
                          on_click=_open_close).classes(
                    BTN_PRIMARY).style("width:100%;")

            ui.button(_t("close"), on_click=dialog.close).props("flat").style(
                "width:100%;color:#808080;font-size:10px;")

    dialog.open()


def _photo_box(photo_bytes, tag, is_closure=False):
    with ui.element('div').classes("photo-box"):
        tag_cls = "photo-tag closure" if is_closure else "photo-tag"
        ui.html('<div class="' + tag_cls + '">' + tag + '</div>')
        try:
            b64 = base64.b64encode(photo_bytes).decode("ascii")
            ui.image("data:image/jpeg;base64," + b64).style(
                "width:100%;height:150px;object-fit:cover;"
                "border-radius:3px;border:1px solid #1e1e1e;")
        except Exception:
            ui.element('div').style(
                "width:100%;height:150px;background:#161616;"
                "border-radius:3px;border:1px solid #1e1e1e;")


def _open_close_defect_dialog(d, is_consultant, parent_dlg, on_close_cb):
    with ui.dialog() as dlg, ui.card().style(
        "padding:20px;min-width:320px;max-width:95vw;width:420px;"
    ):
        ui.label(_t("close_defect_title")).classes("h1").style(
            "margin-bottom:3px;")
        ui.label(_t("close_defect_sub")).classes("muted").style(
            "margin-bottom:12px;")
        ncr_in = None
        if is_consultant:
            ncr_in = ui.input(_t("ncr_input")).style("width:100%;")

        closure_holder = {"bytes": None}
        closure_status = ui.label(_t("closure_photo_hint")).classes(
            "mono-sm").style("margin-top:6px;display:block;")

        async def handle_closure(e):
            try:
                data = await e.file.read()
            except Exception as ex:
                ui.notify(_t("upload_failed") + str(ex), type="negative")
                return
            if not data:
                ui.notify(_t("empty_file"), type="warning")
                return
            closure_holder["bytes"] = data
            closure_status.set_text(_t("closure_attached") + " (" +
                                     str(len(data) // 1024) + " KB)")
            closure_status.style("color:#4ade80;font-size:10px;margin-top:6px;")

        ui.upload(on_upload=handle_closure, auto_upload=True).style(
            "width:100%;").props(
            "flat bordered accept=image/* label='" +
            _t("closure_photo_optional") + "'")
        closure_status

        def _do_close():
            if is_consultant:
                if not ncr_in or not ncr_in.value.strip():
                    ui.notify(_t("ncr_required"), type="warning")
                    return
                db.close_defect(d["id"],
                                 consultant_ncr=ncr_in.value.strip(),
                                 closure_photo=closure_holder["bytes"])
            else:
                db.close_defect(d["id"],
                                 closure_photo=closure_holder["bytes"])
            ui.notify(_t("marked_closed"), type="positive")
            dlg.close()
            try:
                parent_dlg.close()
            except Exception:
                pass
            on_close_cb()

        with ui.element('div').style(
            "display:flex;flex-direction:column;gap:6px;margin-top:14px;"
        ):
            ui.button(_t("confirm_close"), icon="check",
                      on_click=_do_close).classes(BTN_PRIMARY).style(
                "width:100%;")
            ui.button(_t("cancel_btn"), on_click=dlg.close).classes(
                BTN_SOFT).style("width:100%;")
    dlg.open()


# =====================================================================
# EDIT DEFECT DIALOG
# =====================================================================
def _open_edit_defect_dialog(d, on_close_cb):
    meta = {
        "subcontractor": d.get("subcontractor", "") or "",
        "deadline_days": str(int(d.get("deadline_days") or 3)),
        "zone": d.get("zone") or "A",
        "raise_type": d.get("raise_type") or "qc_internal",
        "consultant_ncr": d.get("consultant_ncr") or "",
        "note": d.get("note") or "",
        "engineer_name": d.get("engineer_name") or "",
        "place": d.get("place") or "",
    }
    items = []
    for s in (d.get("selected") or []):
        items.append({
            "name": s.get("name", ""),
            "location_hint": s.get("location_hint", ""),
            "severity": s.get("severity", "Medium"),
            "ms_violations": ", ".join(s.get("ms_violations") or []),
            "code_violations": ", ".join(s.get("code_violations") or []),
            "repair_action": s.get("repair_action", ""),
            "context_mismatch": s.get("context_mismatch", False),
        })
    is_consultant = (d.get("raise_type") or "qc_internal") == "consultant"

    with ui.dialog() as dialog, ui.card().style(
        "padding:0;max-width:640px;width:95vw;overflow:hidden;"
    ):
        with ui.element('div').style(
            "padding:16px 16px 12px;border-bottom:1px solid #1e1e1e;"
        ):
            ui.label(_t("edit_defect_title")).classes("h2")
            ui.label(d["uid"]).classes("mono-sm").style("margin-top:4px;")

        with ui.element('div').style(
            "padding:16px;max-height:66vh;overflow-y:auto;"
        ):
            ui.label(_t("notice_details")).classes("label").style(
                "margin-bottom:8px;")
            ui.input(_t("send_to")).style("width:100%;").bind_value(
                meta, "subcontractor")
            with ui.element('div').style(
                "display:grid;grid-template-columns:1fr 1fr;gap:8px;"
                "margin-top:8px;"
            ):
                ui.select(
                    {"1": "1 " + _t("days"), "2": "2 " + _t("days"),
                     "3": "3 " + _t("days"), "5": "5 " + _t("days"),
                     "7": "7 " + _t("days"), "14": "14 " + _t("days")},
                    label=_t("deadline")).bind_value(meta, "deadline_days")
                ui.select(_zone_options(),
                           label=_t("zone")).bind_value(meta, "zone")
            ui.select(
                {"qc_internal": _t("qc_internal"),
                 "consultant": _t("consultant_ncr")},
                label=_t("raised_as")).style("width:100%;margin-top:8px;"
                ).bind_value(meta, "raise_type")
            ui.input(_t("engineer_field")).style(
                "width:100%;margin-top:8px;").bind_value(meta, "engineer_name")
            ui.input(_t("place_field")).style(
                "width:100%;margin-top:8px;").bind_value(meta, "place")

            ncr_in = None
            if is_consultant or d.get("consultant_ncr"):
                ncr_in = ui.input(_t("ncr_input")).style(
                    "width:100%;margin-top:8px;").bind_value(
                    meta, "consultant_ncr")
            ui.textarea(label=_t("note_label")).style(
                "width:100%;margin-top:8px;").bind_value(meta, "note")

            ui.label(_t("defect_items")).classes("label").style(
                "margin-top:16px;margin-bottom:8px;")
            items_holder = ui.element('div').style("width:100%;")

            def render_items():
                items_holder.clear()
                with items_holder:
                    if not items:
                        ui.label(_t("no_items")).classes("mono-sm")
                    for idx, it in enumerate(items):
                        with ui.element('div').classes("item-box"):
                            with ui.element('div').style(
                                "display:flex;justify-content:space-between;"
                                "align-items:center;margin-bottom:6px;"
                            ):
                                ui.label("#" + str(idx + 1)).classes(
                                    "label").style("font-size:9px;")

                                def _rm(i=idx):
                                    items.pop(i)
                                    render_items()
                                ui.button(icon="close", on_click=_rm).props(
                                    "flat round dense size=sm").style(
                                    "color:#f87171;")
                            ui.input(_t("name")).style(
                                "width:100%;").bind_value(it, "name")
                            ui.input(_t("location_hint")).style(
                                "width:100%;").bind_value(it, "location_hint")
                            with ui.element('div').style(
                                "display:grid;grid-template-columns:1fr 1fr;"
                                "gap:8px;"
                            ):
                                ui.select(_severity_options(),
                                           label=_t("severity")).bind_value(
                                    it, "severity")
                                ui.input(_t("ms_clause")).bind_value(
                                    it, "ms_violations")
                            ui.input(_t("ecp_code")).style(
                                "width:100%;").bind_value(
                                it, "code_violations")
                            ui.input(_t("repair")).style(
                                "width:100%;").bind_value(
                                it, "repair_action")

            render_items()

            def _add_item():
                items.append({
                    "name": "", "location_hint": "", "severity": "Medium",
                    "ms_violations": "", "code_violations": "",
                    "repair_action": "", "context_mismatch": False,
                })
                render_items()

            ui.button(_t("add_item"), icon="add", on_click=_add_item).classes(
                BTN_SOFT).style("width:100%;margin-top:6px;")

        with ui.element('div').style(
            "padding:12px 16px 16px;border-top:1px solid #1e1e1e;"
            "display:flex;flex-direction:column;gap:6px;"
        ):
            def _save_changes():
                if not meta["subcontractor"].strip():
                    ui.notify(_t("enter_sub"), type="warning")
                    return
                selected = []
                for it in items:
                    nm = (it.get("name") or "").strip()
                    if not nm:
                        continue
                    ms_list = [v.strip() for v in
                               (it.get("ms_violations") or "").split(",")
                               if v.strip()]
                    ecp_list = [v.strip() for v in
                                (it.get("code_violations") or "").split(",")
                                if v.strip()]
                    selected.append({
                        "name": nm,
                        "location_hint": (it.get("location_hint") or "").strip(),
                        "severity": it.get("severity") or "Medium",
                        "ms_violations": ms_list,
                        "code_violations": ecp_list,
                        "repair_action": (it.get("repair_action") or "").strip(),
                        "zone": meta["zone"],
                        "context_mismatch": it.get("context_mismatch", False),
                    })
                if not selected:
                    ui.notify(_t("name_required"), type="warning")
                    return
                project = db.get_project(d["project_id"])
                try:
                    pdf_bytes = svc.build_notice_pdf(
                        project=project, defects=selected,
                        notice_uid=d["uid"],
                        subcontractor=meta["subcontractor"].strip(),
                        deadline_days=int(meta["deadline_days"]),
                        raise_type=meta["raise_type"],
                        logo_bytes=(project or {}).get("logo_bytes"))
                except Exception as ex:
                    import traceback
                    traceback.print_exc()
                    ui.notify("PDF build failed: " + str(ex),
                               type="negative")
                    return
                ncr_val = None
                if ncr_in and meta.get("consultant_ncr", "").strip():
                    ncr_val = meta["consultant_ncr"].strip()
                try:
                    db.update_defect_notice(
                        defect_id=d["id"],
                        subcontractor=meta["subcontractor"].strip(),
                        deadline_days=int(meta["deadline_days"]),
                        zone=meta["zone"],
                        note=meta["note"] or "",
                        raise_type=meta["raise_type"],
                        selected=selected,
                        notice_pdf=pdf_bytes,
                        consultant_ncr=ncr_val,
                        engineer_name=meta.get("engineer_name") or None,
                        place=meta.get("place") or None)
                except Exception as ex:
                    import traceback
                    traceback.print_exc()
                    ui.notify("Save failed: " + str(ex), type="negative")
                    return
                ui.notify(_t("saved_changes"), type="positive")
                dialog.close()
                on_close_cb()

            ui.button(_t("save_changes"), icon="check",
                      on_click=_save_changes).classes(BTN_PRIMARY).style(
                "width:100%;")
            ui.button(_t("cancel_btn"), on_click=dialog.close).classes(
                BTN_SOFT).style("width:100%;")
    dialog.open()


# =====================================================================
# DELETE DEFECT DIALOG
# =====================================================================
def _open_delete_defect_dialog(d, on_close_cb):
    with ui.dialog() as dlg, ui.card().style(
        "padding:20px;min-width:300px;max-width:95vw;width:400px;"
    ):
        ui.label(_t("confirm_delete_defect")).classes("h3").style(
            "margin-bottom:6px;")
        ui.label(_t("delete_warning")).classes("muted").style(
            "margin-bottom:4px;")
        ui.label(d["uid"]).classes("mono-sm").style("margin-bottom:14px;")

        def _yes():
            db.delete_defect(d["id"])
            ui.notify(_t("deleted_defect"), type="positive")
            dlg.close()
            on_close_cb()

        with ui.element('div').style("display:flex;gap:8px;"):
            ui.button(_t("delete_defect"), on_click=_yes).classes(
                BTN_DANGER).style("flex:1;")
            ui.button(_t("cancel_btn"), on_click=dlg.close).classes(BTN_SOFT)

    dlg.open()


# =====================================================================
# CHANGE PASSWORD DIALOG
# =====================================================================
def _open_change_password_dialog(state):
    from services import auth_service as auth
    from services import defect_db as ddb

    with ui.dialog() as dlg, ui.card().style(
        "padding:20px;min-width:320px;max-width:95vw;width:420px;"
    ):
        ui.label("Change password").classes("h1").style("margin-bottom:4px;")
        ui.label("At least 6 characters.").classes("muted").style(
            "margin-bottom:14px;")

        cur_in = ui.input("Current password", password=True).style(
            "width:100%;")
        new_in = ui.input("New password", password=True,
                            password_toggle_button=True).style("width:100%;")
        conf_in = ui.input("Confirm new password", password=True).style(
            "width:100%;")

        err_holder = ui.element('div').style("width:100%;")

        def _save():
            err_holder.clear()
            uid = state.get("user_id")
            u = ddb.get_user(uid)
            if not u:
                return
            salt, h = (u.get("password_hash") or ":").split(":", 1)
            if not auth.verify_password(cur_in.value or "", salt, h):
                with err_holder:
                    ui.label("Current password is wrong.").style(
                        "color:#f87171;font-size:11px;margin-top:8px;")
                return
            ok, msg = auth.password_strength_ok(new_in.value or "")
            if not ok:
                with err_holder:
                    ui.label(msg).style(
                        "color:#f87171;font-size:11px;margin-top:8px;")
                return
            if (new_in.value or "") != (conf_in.value or ""):
                with err_holder:
                    ui.label("Passwords do not match.").style(
                        "color:#f87171;font-size:11px;margin-top:8px;")
                return
            ns, nh = auth.hash_password(new_in.value or "")
            ddb.update_user_password(uid, ns + ":" + nh)
            ui.notify("Password updated.", type="positive")
            dlg.close()

        with ui.element('div').style(
            "display:flex;flex-direction:column;gap:6px;margin-top:14px;"
        ):
            ui.button("Save password", on_click=_save).classes(
                BTN_PRIMARY).style("width:100%;")
            ui.button("Cancel", on_click=dlg.close).classes(BTN_SOFT).style(
                "width:100%;")

        err_holder

    dlg.open()


# =====================================================================
# CHAT
# =====================================================================
def _chat_render_body(body, known_authors):
    """Escape HTML, then wrap @mentions in a chip."""
    import html as _html
    safe = _html.escape(str(body or ""))
    parts = safe.split(" ")
    out = []
    for p in parts:
        if p.startswith("@") and len(p) > 1:
            out.append('<span class="mention-chip">' + p + '</span>')
        else:
            out.append(p)
    return " ".join(out)


def _build_chat(state):
    if not state.get("project_id"):
        _render_no_project(state, state["render_main"])
        return
    pid = state["project_id"]
    user = state.get("user") or {}
    my_name = (user.get("name") or user.get("email") or "me")

    with ui.element('div').classes("section-head"):
        ui.label(_t("chat_title")).classes("h1")

        def _refresh():
            state["render_main"]()
        ui.button(icon="refresh", on_click=_refresh).props(
            "flat round dense size=sm").style("color:#808080;")

    ui.label(_t("chat_sub")).classes("muted").style("margin-bottom:12px;")

    # Filters state
    fstate = {
        "author": "all",
        "query": "",
        "from": "",
        "to": "",
        "reply_to": None,
    }

    authors = db.chat_authors(pid)
    if my_name not in authors:
        authors = [my_name] + authors

    author_opts = {"all": _t("chat_filter_all")}
    for a in authors:
        author_opts[a] = a

    def on_author_change(e):
        fstate["author"] = (e.value if e and e.value else "all")
        chat_list.refresh()

    def on_search_change(e):
        fstate["query"] = (e.value or "").strip().lower()
        chat_list.refresh()

    def on_from_change(e):
        fstate["from"] = (e.value or "").strip()
        chat_list.refresh()

    def on_to_change(e):
        fstate["to"] = (e.value or "").strip()
        chat_list.refresh()

    with ui.element('div').style(
        "display:grid;grid-template-columns:1fr 1fr;gap:6px;"
        "margin-bottom:8px;"
    ):
        ui.select(author_opts, value=fstate["author"],
                   label=_t("chat_filter_author"),
                   on_change=on_author_change).props("dense")
        ui.input(placeholder=_t("chat_search"),
                  on_change=on_search_change).props("dense")

    with ui.element('div').style(
        "display:grid;grid-template-columns:1fr 1fr;gap:6px;"
        "margin-bottom:12px;"
    ):
        ui.input(label=_t("chat_filter_from"), on_change=on_from_change).props(
            "dense"
        ).props("type=date")
        ui.input(label=_t("chat_filter_to"), on_change=on_to_change).props(
            "dense"
        ).props("type=date")

    # Reply indicator
    reply_holder = ui.element('div').style("width:100%;")

    def render_reply_indicator():
        reply_holder.clear()
        rid = fstate.get("reply_to")
        if not rid:
            return
        target = db.chat_get(rid) or {}
        with reply_holder:
            with ui.element('div').style(
                "display:flex;justify-content:space-between;"
                "align-items:center;background:#161616;"
                "border:1px solid #262626;border-radius:3px;"
                "padding:6px 10px;margin-bottom:6px;"
            ):
                ui.label(
                    _t("chat_replying_to") + ": " +
                    str(target.get("author", "")) + " — " +
                    str(target.get("body", ""))[:60]
                ).style("font-size:10px;color:#b8b8b8;")

                def _cancel():
                    fstate["reply_to"] = None
                    render_reply_indicator()
                ui.button(_t("chat_cancel"), on_click=_cancel).props(
                    "flat dense no-caps size=sm").style(
                    "color:#808080;font-size:10px;")

    render_reply_indicator()

    @ui.refreshable
    def chat_list():
        msgs = db.chat_list(pid, limit=300)

        # Apply filters
        if fstate["author"] != "all":
            msgs = [m for m in msgs if (m.get("author") or "") ==
                    fstate["author"]]
        if fstate["query"]:
            q = fstate["query"]
            msgs = [m for m in msgs
                    if q in (m.get("body") or "").lower()]
        if fstate["from"]:
            msgs = [m for m in msgs
                    if (m.get("created_at") or "")[:10] >= fstate["from"]]
        if fstate["to"]:
            msgs = [m for m in msgs
                    if (m.get("created_at") or "")[:10] <= fstate["to"]]

        if not msgs:
            ui.label(_t("chat_empty")).classes("mono-sm").style(
                "text-align:center;padding:32px 0;color:#5a5a5a;")
            return

        # Build message map for reply lookup
        by_id = {m["id"]: m for m in msgs}

        for m in msgs:
            mid = m.get("id")
            author = m.get("author") or ""
            body = m.get("body") or ""
            created = (m.get("created_at") or "")[:16]
            reply_to = m.get("reply_to_id")
            is_mine = (author == my_name)
            cls = "chat-msg mine" if is_mine else "chat-msg"

            with ui.element('div').classes(cls):
                with ui.element('div').classes("chat-head"):
                    with ui.element('div').style(
                        "display:flex;align-items:center;gap:6px;"
                    ):
                        ui.label(author).classes("chat-author")
                        if is_mine:
                            ui.html('<span class="badge-you">' +
                                    _t("chat_you") + '</span>')
                    ui.label(created).classes("chat-time")

                if reply_to and reply_to in by_id:
                    parent = by_id[reply_to]
                    ui.html(
                        '<div class="chat-reply-quote">' +
                        '<b>' + str(parent.get("author", "")) + '</b>: ' +
                        str(parent.get("body", ""))[:80] +
                        '</div>'
                    )

                ui.html('<div class="chat-body">' +
                        _chat_render_body(body, authors) + '</div>')

                with ui.element('div').classes("chat-actions"):
                    def _reply(rid=mid):
                        fstate["reply_to"] = rid
                        render_reply_indicator()
                    ui.element('button').classes("chat-act").on(
                        "click", _reply
                    )
                    ui.label(_t("chat_reply")).classes("chat-act").style(
                        "cursor:pointer;"
                    ).on("click", _reply)

                    if is_mine:
                        def _del(did=mid):
                            _confirm_delete_chat(state, did, chat_list.refresh)
                        ui.label(_t("chat_delete")).classes(
                            "chat-act danger"
                        ).style("cursor:pointer;").on("click", _del)

    chat_list()

    # Composer
    with ui.element('div').classes("chat-composer"):
        with ui.element('div').style("position:relative;width:100%;"):
            body_in = ui.textarea(
                placeholder=_t("chat_placeholder")
            ).style("width:100%;").props("dense autogrow")

            mention_holder = ui.element('div').style(
                "position:absolute;bottom:100%;left:0;right:0;"
                "display:none;"
            )

            def _update_mentions():
                txt = body_in.value or ""
                # Show mention dropdown if last typed token starts with @
                last = txt.split()[-1] if txt.split() else ""
                if last.startswith("@") and len(last) >= 1:
                    query = last[1:].lower()
                    matches = [a for a in authors
                               if query in (a or "").lower()][:6]
                    mention_holder.clear()
                    mention_holder.style("display:block;")
                    with mention_holder:
                        ui.html('<div class="mention-drop" id="mq"></div>')
                        with ui.element('div').classes("mention-drop"):
                            if not matches:
                                ui.label("No matches").classes(
                                    "mention-item"
                                ).style("color:#5a5a5a;")
                            for a in matches:
                                def _pick(nm=a):
                                    parts = (body_in.value or "").split()
                                    if parts and parts[-1].startswith("@"):
                                        parts[-1] = "@" + nm
                                    else:
                                        parts.append("@" + nm)
                                    body_in.value = " ".join(parts) + " "
                                    mention_holder.style("display:none;")
                                ui.label(a).classes("mention-item").on(
                                    "click", _pick
                                )
                else:
                    mention_holder.style("display:none;")

            body_in.on("update:model-value",
                        lambda e: _update_mentions())

        def _send():
            txt = (body_in.value or "").strip()
            if not txt:
                return
            # Extract mentions
            import re as _re
            mentions = _re.findall(r"@([A-Za-z0-9_.\-]+)", txt)
            # Remove self from mentions
            mentions = [m for m in mentions if m and m != my_name]
            try:
                db.chat_add(pid, state["user_id"], my_name, txt,
                             reply_to_id=fstate.get("reply_to"),
                             mentions=mentions)
            except Exception as ex:
                ui.notify("Send failed: " + str(ex), type="negative")
                return
            body_in.value = ""
            fstate["reply_to"] = None
            render_reply_indicator()
            mention_holder.style("display:none;")
            chat_list.refresh()

        ui.button(_t("chat_send"), icon="send", on_click=_send).classes(
            BTN_PRIMARY).style("width:100%;margin-top:6px;")


def _confirm_delete_chat(state, msg_id, refresh_fn):
    with ui.dialog() as dlg, ui.card().style(
        "padding:20px;min-width:280px;max-width:95vw;width:360px;"
    ):
        ui.label(_t("chat_confirm_delete")).classes("h3").style(
            "margin-bottom:14px;")

        def _yes():
            db.chat_delete(msg_id)
            ui.notify(_t("chat_deleted"), type="positive")
            dlg.close()
            ui.timer(0.03, refresh_fn, once=True)

        with ui.element('div').style("display:flex;gap:8px;"):
            ui.button(_t("chat_delete"), on_click=_yes).classes(
                BTN_DANGER).style("flex:1;")
            ui.button(_t("cancel_btn"), on_click=dlg.close).classes(BTN_SOFT)
    dlg.open()
