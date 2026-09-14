"""
ui/defect_page.py — Full file.
- Team multi-user: invite by email, all see same project.
- MS Chat: Q&A over uploaded Method Statements + document compliance check.
- OCR for handwritten notes in the "no photo" dialog.
- Free-text zone input.
- Real-time chat (2s poll, smart scroll).
- 60-second delete window on chat messages.
- Role-colored chat authors.
- Defect-type filter in logs.
- Engineer name + place under every log title.
- Interactive ECharts dashboard.
"""
import io
import re
import json
import base64
import datetime
import html as _html_mod
from nicegui import ui, app

from services import defect_db as db
from services import defect_service as svc
from services import ms_chat_service as msc
from services.ai_service import call_gemini_json
from ui.pwa import inject_pwa


LANG = {"code": "en"}

TITLES = [
    "QC Engineer", "QC Manager", "Site Engineer", "Project Manager",
    "Civil Engineer", "Structural Engineer", "Electrical Engineer",
    "Mechanical Engineer", "Architect", "Consultant", "Foreman", "Other",
]

ROLE_OPTIONS = {
    "engineer": "Engineer",
    "consultant": "Consultant",
    "viewer": "Viewer",
}
ROLE_COLORS = {
    "owner": "#5eead4",
    "engineer": "#60a5fa",
    "consultant": "#f87171",
    "viewer": "#808080",
}

T = {
    "en": {
        "app_title": "DEFECT NOTICES",
        "new_defect": "NEW DEFECT", "logs": "DEFECT LOGS",
        "subs": "SUBS", "dashboard": "DASHBOARD", "chat": "TEAM CHAT",
        "ms_chat": "MS CHAT",
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
        "no_photo_sub": "Describe the defect, or scan a handwritten note.",
        "defect_desc": "Defect description",
        "defect_desc_placeholder": "e.g. exposed rebar at column C3 base",
        "extra_note": "Extra note (optional)",
        "extra_note_placeholder": "any additional context",
        "analyze": "Analyze with AI", "analyzing": "Analyzing...",
        "note_label": "Note (optional)",
        "note_placeholder": "e.g. crack at column C3 base",
        "zone": "Zone", "zone_placeholder": "A / B / Block 2 / Roof...",
        "place_of_defect": "PLACE OF THE DEFECT",
        "place_of_defect_placeholder": "e.g. Block B, Column C3 base, Grid 4-5",
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
        "tag_dup": "SEEN {n}x",
        "ocr_label": "SCAN HANDWRITTEN NOTE (optional)",
        "ocr_hint": "Upload or take a photo of the handwritten page "
                     "(JPG / PNG) or a PDF. AI reads it and fills the "
                     "description below — you can edit it.",
        "ocr_upload": "Take or upload a photo / PDF",
        "ocr_reading": "Reading handwriting...",
        "ocr_done": "Text extracted. Edit below if needed.",
        "ocr_failed": "OCR failed:",
        "ocr_empty": "No readable text found.",
        "logs_title": "DEFECT LOGS",
        "logs_sub": "Every notice issued. Tap to view.",
        "no_logs": "No notices yet.",
        "no_match": "No matches.",
        "search_placeholder": "Search UID, defect, sub, engineer, place...",
        "filter_all": "All", "filter_qc": "QC Internal",
        "filter_consultant": "Consultant / NCR",
        "defect_type_label": "Defect type",
        "defect_type_all": "All types",
        "defect_type_structural": "Structural",
        "defect_type_arch": "Architectural",
        "defect_type_mep": "MEP",
        "defect_type_earthwork": "Earthwork",
        "defect_type_general": "General",
        "filter_type": "Type",
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
        "dash_summary": "SUMMARY", "dash_print": "PRINT DASHBOARD PDF",
        "dash_empty": "No defects yet.",
        "dash_scatter": "DEFECT LIFECYCLE (SCATTER)",
        "dash_scatter_x": "Days open", "dash_scatter_y": "Days to close",
        "dash_line": "RAISED VS CLOSED / WEEK",
        "dash_line_raised": "Raised", "dash_line_closed": "Closed",
        "no_data": "No data.",
        "col_name": "NAME", "col_open": "OPEN", "col_overdue": "OVERDUE",
        "col_closed": "CLOSED", "col_total": "TOTAL",
        "unassigned": "(unassigned)",
        "subs_title": "SUBCONTRACTORS", "subs_sub": "Master list and live performance.",
        "add_sub": "Add subcontractor", "add_sub_title": "Add subcontractor",
        "sub_name": "Subcontractor name",
        "sub_trade": "Trade (e.g. steel fixing, masonry)",
        "sub_phone": "Phone (optional)", "sub_notes": "Notes (optional)",
        "sub_saved": "Saved.", "sub_deleted": "Deleted.",
        "delete_sub_confirm": "Remove this subcontractor?",
        "no_subs": "No subcontractors yet.",
        "no_subs_hint": "Add one to track performance.",
        "view_defects": "View defects", "download_sub_pdf": "Performance PDF",
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
        "edit_defect": "Edit", "delete_defect": "Delete",
        "edit_defect_title": "Edit notice",
        "edit_defect_sub": "Change details. Notice PDF will be regenerated.",
        "defect_items": "Defect items", "add_item": "+ Add item",
        "remove_item": "Remove", "save_changes": "Save changes",
        "saved_changes": "Notice updated.",
        "confirm_delete_defect": "Delete this notice permanently?",
        "delete_warning": "This cannot be undone.",
        "deleted_defect": "Notice deleted.",
        "no_items": "No defects in this notice.",
        "raised_by": "By", "at_place": "At",
        "chat_title": "TEAM CHAT",
        "chat_sub": "Project-wide discussion for the QC team.",
        "chat_placeholder": "Type a message...  use @ to mention someone",
        "chat_send": "Send", "chat_empty": "No messages yet. Start the conversation.",
        "chat_reply": "Reply", "chat_replying_to": "Replying to",
        "chat_cancel": "Cancel", "chat_delete": "Delete",
        "chat_filter_from": "From", "chat_filter_to": "To",
        "chat_search": "Search by name or message...",
        "chat_confirm_delete": "Delete this message?",
        "chat_deleted": "Message deleted.",
        "chat_you": "you",
        "delete_too_late": "Can only delete within 60 seconds of posting.",
        "delete_not_owner": "Only the author can delete this message.",
        "delete_failed": "Delete failed.",
        "my_profile": "My profile", "profile_name": "Name",
        "profile_title": "Job title",
        "profile_photo": "Profile photo (optional)",
        "profile_saved": "Profile saved.",
        "profile_email": "Email", "profile_open": "Profile",
        "new_messages": "NEW MESSAGES",
        # Team
        "team_section": "TEAM",
        "team_members": "Members",
        "team_owner": "Owner",
        "team_invite": "Invite member",
        "team_invite_title": "Invite a team member",
        "team_invite_hint": "They must already have an account. Ask them "
                            "to sign up first if they don't.",
        "team_email": "Email address",
        "team_role": "Role",
        "team_role_engineer": "Engineer",
        "team_role_consultant": "Consultant",
        "team_role_viewer": "Viewer",
        "team_add": "Add to project",
        "team_added": "Member added.",
        "team_failed": "Add failed: ",
        "team_removed": "Member removed.",
        "team_remove": "Remove",
        "team_remove_confirm": "Remove this member from the project?",
        "team_you": "(you)",
        "team_no_members": "No members yet.",
        # MS Chat
        "ms_chat_title": "MS CHAT",
        "ms_chat_sub": "Your private chat with the MS. Ask questions or "
               "scan documents. No one else on the team sees this.",
        "ms_chat_empty": "No messages yet. Ask your first question below.",
        "ms_chat_ask": "Ask a question",
        "ms_chat_ask_placeholder": "e.g. What is the minimum cover for "
                                    "columns exposed to weather?",
        "ms_chat_send": "ASK",
        "ms_chat_check_btn": "Scan document",
        "ms_chat_check_hint": "Upload a batch ticket, delivery note, or "
                              "test result (JPG / PNG / PDF).",
        "ms_chat_reading": "Reading document...",
        "ms_chat_analysing": "Checking against MS...",
        "ms_chat_answer_from": "Answer",
        "ms_chat_not_found": "Not found in the uploaded MS.",
        "ms_chat_doc_type": "Document type",
        "ms_chat_extracted": "Extracted",
        "ms_chat_checks": "Checks against MS",
        "ms_chat_overall": "OVERALL",
        "ms_chat_compliant": "COMPLIANT",
        "ms_chat_conditional": "CONDITIONAL",
        "ms_chat_non_compliant": "NON-COMPLIANT",
        "ms_chat_clear": "Clear history",
        "ms_chat_clear_confirm": "Delete all MS chat history for this project?",
        "ms_chat_cleared": "History cleared.",
        "ms_chat_need_ms": "Upload a Method Statement first (drawer → "
                            "Method Statements → +).",
        "ms_chat_failed": "Failed: ",
        "ms_chat_kind_question": "QUESTION",
        "ms_chat_kind_check": "DOCUMENT CHECK",
        "ms_chat_source": "Source",
    },
    "ar": {
        "app_title": "إشعارات العيوب",
        "new_defect": "عيب جديد", "logs": "السجل",
        "dashboard": "الرئيسية", "subs": "المقاولون", "chat": "الدردشة",
        "ms_chat": "دردشة MS",
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
        "add_photos": "إضافة صور أخرى", "photos_count": "صورة",
        "no_photo_btn": "عيب بدون صورة", "no_photo_title": "عيب بدون صورة",
        "no_photo_sub": "صف العيب، أو امسح ملاحظة مكتوبة بخط اليد.",
        "defect_desc": "وصف العيب",
        "defect_desc_placeholder": "مثال: حديد مكشوف عند قاعدة C3",
        "extra_note": "ملاحظة إضافية (اختياري)",
        "extra_note_placeholder": "أي سياق إضافي",
        "analyze": "تحليل بالذكاء الاصطناعي", "analyzing": "جاري التحليل...",
        "note_label": "ملاحظة (اختياري)",
        "note_placeholder": "مثال: شرخ عند قاعدة C3",
        "zone": "المنطقة", "zone_placeholder": "A / B / بلوك 2 / السطح...",
        "place_of_defect": "مكان العيب",
        "place_of_defect_placeholder": "مثال: بلوك B، قاعدة عمود C3، محور 4-5",
        "engineer_field": "اسم المهندس",
        "place_field": "المكان بالتفصيل",
        "place_placeholder": "مثال: بلوك B، قاعدة عمود C3",
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
        "notice_saved": "تم الحفظ", "setup_first": "أعدّ المشروع أولاً.",
        "add_defect_title": "إضافة عيب يدوياً", "name": "اسم العيب",
        "location_hint": "الموقع", "severity": "الخطورة",
        "ms_clause": "بند MS", "ecp_code": "كود ECP",
        "repair": "الإصلاح", "add": "إضافة", "cancel": "إلغاء",
        "name_required": "اسم العيب مطلوب.", "desc_required": "الوصف مطلوب.",
        "tag_ai": "AI", "tag_manual": "يدوي",
        "tag_nophoto": "بدون صورة", "mismatch_warn": "لا بند مطابق",
        "tag_dup": "سُبق {n}x",
        "ocr_label": "امسح ملاحظة مكتوبة بخط اليد (اختياري)",
        "ocr_hint": "ارفع أو صوّر الصفحة المكتوبة (JPG / PNG) أو PDF.",
        "ocr_upload": "التقط أو ارفع صورة / PDF",
        "ocr_reading": "جاري قراءة الخط...",
        "ocr_done": "تم استخراج النص. عدّل بالأسفل إن لزم.",
        "ocr_failed": "فشل القراءة:", "ocr_empty": "لا يوجد نص مقروء.",
        "logs_title": "سجل العيوب", "logs_sub": "كل إشعار صدر.",
        "no_logs": "لا توجد إشعارات.", "no_match": "لا نتائج.",
        "search_placeholder": "ابحث بالرقم أو العيب أو المهندس أو المكان...",
        "filter_all": "الكل", "filter_qc": "داخلي QC",
        "filter_consultant": "استشاري / NCR",
        "defect_type_label": "نوع العيب", "defect_type_all": "كل الأنواع",
        "defect_type_structural": "إنشائي", "defect_type_arch": "معماري",
        "defect_type_mep": "كهروميكانيكي", "defect_type_earthwork": "أعمال ترابية",
        "defect_type_general": "عام", "filter_type": "النوع",
        "export_register": "السجل PDF", "closure_report": "الإغلاق PDF",
        "export_excel": "Excel", "open": "مفتوح", "closed": "مغلق",
        "no_rows": "لا صفوف.", "notice": "إشعار", "download_pdf": "تحميل PDF",
        "mark_closed": "إغلاق", "close": "إغلاق",
        "ncr_input": "رقم NCR الاستشاري", "ncr_required": "أدخل رقم NCR أولاً.",
        "marked_closed": "تم الإغلاق.", "not_found": "غير موجود.",
        "repair_label": "الإصلاح", "save": "حفظ", "cancel_btn": "إلغاء",
        "setup_title": "إعداد المشروع", "project_name": "اسم المشروع",
        "save_project": "حفظ", "ms_dialog_title": "تحميل بند طريقة عمل",
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
        "lang_button": "EN", "upload_failed": "فشل: ",
        "empty_file": "ملف فارغ.", "photo_received": "تم استلام الصورة",
        "file_loaded": "تم التحميل: ", "photos_received": "صور",
        "projects_title": "مشاريعك", "switch_project": "تبديل المشروع",
        "new_project": "مشروع جديد", "create_first": "أنشئ مشروعك الأول",
        "no_projects_hint": "لا مشاريع بعد.", "delete_project": "حذف المشروع",
        "delete_confirm": "حذف هذا المشروع وكل بياناته؟",
        "logout": "خروج", "signed_in_as": "مسجل", "or_divider": "أو",
        "dash_title": "الرئيسية", "dash_sub": "مؤشرات حية.",
        "kpi_total": "الإجمالي", "kpi_open": "مفتوح", "kpi_closed": "مغلق",
        "kpi_overdue": "متأخر", "kpi_closed_7d": "أُغلق-٧",
        "kpi_avg_days": "متوسط الإغلاق",
        "dash_zones": "المفتوح حسب المنطقة", "dash_weeks": "المُصدر أسبوعياً",
        "dash_subs": "حسب المقاول الفرعي", "dash_summary": "ملخص",
        "dash_print": "طباعة تقرير الرئيسية", "dash_empty": "لا عيوب بعد.",
        "dash_scatter": "دورة حياة العيب", "dash_scatter_x": "أيام مفتوح",
        "dash_scatter_y": "أيام حتى الإغلاق",
        "dash_line": "مُصدر مقابل مُغلق أسبوعياً",
        "dash_line_raised": "مُصدر", "dash_line_closed": "مُغلق",
        "no_data": "لا بيانات.",
        "col_name": "الاسم", "col_open": "مفتوح", "col_overdue": "متأخر",
        "col_closed": "مغلق", "col_total": "الإجمالي",
        "unassigned": "(غير معين)", "subs_title": "المقاولون الفرعيون",
        "subs_sub": "القائمة والأداء.", "add_sub": "إضافة مقاول فرعي",
        "add_sub_title": "إضافة مقاول فرعي",
        "sub_name": "اسم المقاول الفرعي", "sub_trade": "التخصص",
        "sub_phone": "هاتف (اختياري)", "sub_notes": "ملاحظات (اختياري)",
        "sub_saved": "تم الحفظ.", "sub_deleted": "تم الحذف.",
        "delete_sub_confirm": "حذف هذا المقاول؟",
        "no_subs": "لا مقاولون بعد.", "no_subs_hint": "أضف واحداً لتتبع أدائه.",
        "view_defects": "عرض العيوب", "download_sub_pdf": "تقرير الأداء PDF",
        "filtered_by": "فلتر", "clear_filter": "مسح",
        "from_defects": "من الإشعارات", "sub_open": "مفتوح",
        "sub_overdue": "متأخر", "sub_closed": "مغلق", "sub_total": "الإجمالي",
        "delete_sub": "حذف", "close_defect_title": "إغلاق العيب",
        "close_defect_sub": "أرفق صورة كإثبات.",
        "closure_photo_label": "صورة الإغلاق",
        "closure_photo_optional": "صورة الإغلاق (اختياري)",
        "closure_photo_hint": "مُفضل — صورة بعد الإصلاح.",
        "closure_attached": "تم الإرفاق", "closure_skipped": "بدون صورة",
        "confirm_close": "تأكيد الإغلاق", "close_without_photo": "إغلاق بدون صورة",
        "closure_photo_short": "إغلاق", "refresh": "تحديث", "week": "أسبوع",
        "no_ms_uploaded": "لا MS", "edit_defect": "تعديل",
        "delete_defect": "حذف", "edit_defect_title": "تعديل الإشعار",
        "edit_defect_sub": "عدّل التفاصيل. سيُعاد إنشاء PDF.",
        "defect_items": "بنود العيوب", "add_item": "+ إضافة بند",
        "remove_item": "حذف", "save_changes": "حفظ التعديلات",
        "saved_changes": "تم تحديث الإشعار.",
        "confirm_delete_defect": "حذف هذا الإشعار نهائياً؟",
        "delete_warning": "لا يمكن التراجع.",
        "deleted_defect": "تم حذف الإشعار.",
        "no_items": "لا بنود في هذا الإشعار.",
        "raised_by": "بواسطة", "at_place": "في",
        "chat_title": "دردشة الفريق", "chat_sub": "نقاش المشروع لفريق الجودة.",
        "chat_placeholder": "اكتب رسالة...  استخدم @ للإشارة",
        "chat_send": "إرسال", "chat_empty": "لا رسائل بعد. ابدأ النقاش.",
        "chat_reply": "رد", "chat_replying_to": "رداً على",
        "chat_cancel": "إلغاء", "chat_delete": "حذف",
        "chat_filter_from": "من", "chat_filter_to": "إلى",
        "chat_search": "ابحث بالاسم أو الرسالة...",
        "chat_confirm_delete": "حذف هذه الرسالة؟",
        "chat_deleted": "تم الحذف.", "chat_you": "أنت",
        "delete_too_late": "يمكن الحذف خلال 60 ثانية فقط بعد الإرسال.",
        "delete_not_owner": "فقط كاتب الرسالة يمكنه الحذف.",
        "delete_failed": "فشل الحذف.",
        "my_profile": "ملفي الشخصي", "profile_name": "الاسم",
        "profile_title": "المسمى الوظيفي",
        "profile_photo": "صورة شخصية (اختياري)",
        "profile_saved": "تم الحفظ.", "profile_email": "البريد",
        "profile_open": "الملف", "new_messages": "رسائل جديدة",
        "team_section": "الفريق", "team_members": "الأعضاء",
        "team_owner": "المالك", "team_invite": "دعوة عضو",
        "team_invite_title": "دعوة عضو للفريق",
        "team_invite_hint": "يجب أن يكون لديه حساب بالفعل.",
        "team_email": "البريد الإلكتروني", "team_role": "الدور",
        "team_role_engineer": "مهندس", "team_role_consultant": "استشاري",
        "team_role_viewer": "مشاهد", "team_add": "إضافة للمشروع",
        "team_added": "تمت الإضافة.", "team_failed": "فشل: ",
        "team_removed": "تم الحذف.", "team_remove": "حذف",
        "team_remove_confirm": "حذف هذا العضو من المشروع؟",
        "team_you": "(أنت)", "team_no_members": "لا أعضاء بعد.",
        "ms_chat_title": "دردشة MS",
        "ms_chat_sub": "دردشتك الخاصة مع MS. اسأل أو امسح مستندات. "
               "لا أحد في الفريق يرى هذا.",
        "ms_chat_empty": "لا رسائل بعد. اطرح سؤالك بالأسفل.",
        "ms_chat_ask": "اطرح سؤالاً",
        "ms_chat_ask_placeholder": "مثال: ما هو الحد الأدنى للغطاء للأعمدة المعرضة للجو؟",
        "ms_chat_send": "اسأل", "ms_chat_check_btn": "مسح مستند",
        "ms_chat_check_hint": "ارفع تذكرة خرسانة أو إذن تسليم أو نتيجة اختبار (JPG / PNG / PDF).",
        "ms_chat_reading": "جاري قراءة المستند...",
        "ms_chat_analysing": "جاري المقارنة بـ MS...",
        "ms_chat_answer_from": "الإجابة",
        "ms_chat_not_found": "غير موجود في MS المحمل.",
        "ms_chat_doc_type": "نوع المستند",
        "ms_chat_extracted": "البيانات المستخرجة",
        "ms_chat_checks": "الفحوصات مقابل MS",
        "ms_chat_overall": "النتيجة",
        "ms_chat_compliant": "مطابق",
        "ms_chat_conditional": "مشروط",
        "ms_chat_non_compliant": "غير مطابق",
        "ms_chat_clear": "مسح السجل",
        "ms_chat_clear_confirm": "حذف كل سجل دردشة MS لهذا المشروع؟",
        "ms_chat_cleared": "تم المسح.",
        "ms_chat_need_ms": "ارفع بيانات طريقة عمل أولاً.",
        "ms_chat_failed": "فشل: ",
        "ms_chat_kind_question": "سؤال",
        "ms_chat_kind_check": "فحص مستند",
        "ms_chat_source": "المصدر",
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


def _defect_type_options():
    return {
        "Structural": _t("defect_type_structural"),
        "Architectural": _t("defect_type_arch"),
        "MEP": _t("defect_type_mep"),
        "Earthwork": _t("defect_type_earthwork"),
        "General": _t("defect_type_general"),
    }


def _role_options():
    return {
        "engineer": _t("team_role_engineer"),
        "consultant": _t("team_role_consultant"),
        "viewer": _t("team_role_viewer"),
    }


_ELEMENT_KEYWORDS = {
    "column": ["column", "col ", "عمود", "أعمدة", "أعمده"],
    "beam":   ["beam", "كمرة", "كمره", "كمر", "جسر"],
    "slab":   ["slab", "سقف", "بلاطة", "بلاطه"],
    "wall":   ["wall", "حائط", "حيط", "جدار"],
    "foundation": ["foundation", "footing", "أساس", "اساس", "قاعدة", "قاعده"],
    "finishing": ["plaster", "finish", "تشطيب", "محارة", "محاره", "دهان"],
}


def _guess_element(place_text):
    p = (place_text or "").lower()
    for key, words in _ELEMENT_KEYWORDS.items():
        for w in words:
            if w in p:
                return key
    return "column"

async def _get_browser_location():
    """Ask the browser for the current GPS. Returns dict or None."""
    try:
        raw = await ui.run_javascript("""
            (async () => {
              try {
                const p = await new Promise((resolve, reject) => {
                  if (!navigator.geolocation) {
                    reject(new Error('Geolocation unsupported'));
                    return;
                  }
                  navigator.geolocation.getCurrentPosition(resolve, reject, {
                    enableHighAccuracy: true,
                    timeout: 10000,
                    maximumAge: 0
                  });
                });
                return JSON.stringify({
                  lat: p.coords.latitude,
                  lng: p.coords.longitude,
                  acc: p.coords.accuracy
                });
              } catch (e) {
                return 'ERR:' + (e && e.message ? e.message : 'unknown');
              }
            })()
        """, timeout=15)
    except Exception as e:
        print("[geo] js failed: " + repr(e))
        return None
    if not raw or str(raw).startswith("ERR:"):
        print("[geo] denied/failed: " + str(raw))
        return None
    try:
        d = json.loads(str(raw))
        if "lat" in d and "lng" in d:
            return {"lat": float(d["lat"]),
                    "lng": float(d["lng"]),
                    "acc": float(d.get("acc") or 0)}
    except Exception as e:
        print("[geo] parse failed: " + repr(e))
    return None
def _chat_author_color(title):
    t = (title or "").lower()
    if "consultant" in t or "استشاري" in t:
        return "#f87171"
    if "qc manager" in t or "مدير الجودة" in t or "quality manager" in t:
        return "#60a5fa"
    if "project manager" in t or "مدير المشروع" in t:
        return "#4ade80"
    if "qc engineer" in t or "مهندس الجودة" in t:
        return "#5eead4"
    return "#b8b8b8"


# =====================================================================
# OCR — handwriting / document text extraction
# =====================================================================
_OCR_PROMPT = (
    "You are an OCR engine. Read every word in this document (handwritten "
    "or printed). Return ONLY the raw extracted text, in the same language "
    "as the source. Do NOT translate. Do NOT summarize. Do NOT add "
    "commentary, headings, markdown, bullets, or quotation marks. Preserve "
    "line breaks. If a word is unclear, transcribe your best guess. If the "
    "image contains no readable text, return an empty string."
)


async def _ocr_handwriting(file_bytes, mime_type):
    if not file_bytes:
        return None, "Empty file."
    try:
        from google.genai import types
    except Exception as e:
        return None, "google-genai not available: " + repr(e)
    payload = file_bytes
    mime = (mime_type or "image/jpeg").lower()
    if mime.startswith("image/"):
        try:
            payload = svc._shrink_image(file_bytes, max_side=1600)
            mime = "image/jpeg"
        except Exception:
            payload = file_bytes
    try:
        part = types.Part.from_bytes(data=payload, mime_type=mime)
    except Exception as e:
        return None, "Could not prepare file: " + repr(e)
    try:
        raw = await call_gemini_json([_OCR_PROMPT, part],
                                       temperature=0.0, timeout=45)
    except Exception as e:
        return None, "AI call failed: " + str(e)
    text = (raw or "").strip()
    if not text:
        return "", _t("ocr_empty")
    return text, None


# =====================================================================
# THEME
# =====================================================================
def _inject_theme():
    rtl = "rtl" if _is_rtl() else "ltr"
    html = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Amiri:wght@400;700&display=swap" rel="stylesheet">
<style>
  :root {
    --bg:#0b0b0b; --surface:#101010; --surface-2:#161616;
    --surface-3:#1c1c1c; --border:#1e1e1e; --border-2:#262626;
    --text:#e8e8e8; --text-soft:#b8b8b8; --muted:#808080;
    --muted-2:#5a5a5a; --accent:#5eead4; --accent-dim:#14b8a6;
    --blue:#60a5fa; --success:#4ade80; --warn:#fbbf24; --danger:#f87171;
  }
  * { font-variant-ligatures: none; }
  html, body {
    background: var(--bg) !important; color: var(--text) !important;
    font-family: 'JetBrains Mono','Amiri','Courier New',monospace !important;
    font-size: 13px; line-height: 1.5;
    -webkit-font-smoothing: antialiased;
    letter-spacing: -0.01em;
    overflow-x: hidden !important;
    direction: __DIR__;
  }
  html, body, .q-page, .q-page-container, .scroll, * {
    scrollbar-width: none !important;
    -ms-overflow-style: none !important;
  }
  *::-webkit-scrollbar { width: 0 !important; height: 0 !important;
                         display: none !important; background: transparent !important; }
  .nicegui-content { padding: 0 !important; }
  .q-page, .q-layout, .q-page-container { background: var(--bg) !important; }
  .q-btn {
    border-radius: 3px !important; text-transform: none !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 500 !important; min-height: 32px !important;
    padding: 0 12px !important; font-size: 11px !important;
    box-shadow: none !important;
  }
  .btn-primary { background: var(--accent) !important;
                 color: #0b0b0b !important; font-weight: 700 !important; }
  .btn-soft { background: var(--surface-2) !important;
              color: var(--text) !important;
              border: 1px solid var(--border-2) !important; }
  .btn-success { background: var(--success) !important;
                 color: #0b0b0b !important; font-weight: 700 !important; }
  .btn-danger { background: var(--danger) !important;
                color: #0b0b0b !important; font-weight: 700 !important; }
  .btn-outline { background: transparent !important;
                 color: var(--text) !important;
                 border: 1px dashed var(--border-2) !important; }
  .q-field--outlined .q-field__control {
    border-radius: 3px !important; background: var(--surface-2) !important;
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
  .q-field__label { color: var(--muted) !important; }
  .q-menu { background: var(--surface-2) !important;
            border: 1px solid var(--border-2) !important;
            border-radius: 3px !important; }
  .q-item { color: var(--text) !important;
            font-family: 'JetBrains Mono', monospace !important;
            font-size: 12px !important; }
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
  .mono-lg { font-size: 12px; font-weight: 600; color: var(--text);
             word-break: break-word; }
  .mono-sm { font-size: 10px; color: var(--muted); }
  .label { font-size: 9px; font-weight: 700; color: var(--muted-2);
           text-transform: uppercase; letter-spacing: 0.14em; }
  .q-drawer { background: var(--bg) !important;
              border-right: 1px solid var(--border) !important; }
  .app-header {
    position: sticky; top: 0; z-index: 900; width: 100%;
    background: rgba(11,11,11,0.94);
    border-bottom: 1px solid var(--border); padding: 8px 14px;
    display: flex; align-items: center; justify-content: space-between;
    box-sizing: border-box;
  }
  .app-header .brand { font-weight: 700; font-size: 12px;
                       color: var(--text); }
  .app-header .brand::before {
    content: '\\25CF '; color: var(--accent); font-size: 9px;
    vertical-align: middle; margin-right: 4px;
  }
  .top-tabs {
    display: flex; align-items: center; gap: 4px; padding: 8px 14px;
    background: rgba(11,11,11,0.94);
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
    flex-shrink: 0; display: inline-flex; align-items: center;
  }
  .top-tab-btn.active { color: var(--accent); background: var(--surface-2); }
  .blink-cursor { display: inline-block; width: 4px; height: 9px;
                  background: var(--accent); vertical-align: middle;
                  margin-left: 5px;
                  animation: blink 1.1s steps(2, start) infinite; }
  @keyframes blink { to { visibility: hidden; } }
  .main-content { padding: 14px; padding-bottom: 40px;
                  max-width: 760px; margin: 0 auto; width: 100%;
                  box-sizing: border-box; }
  .q-uploader { background: var(--surface-2) !important;
                border: 1px dashed var(--border-2) !important;
                border-radius: 4px !important; width: 100% !important;
                max-width: 100% !important; color: var(--text) !important; }
  .q-uploader__header { background: transparent !important;
                        color: var(--text) !important; }
  .q-uploader__title, .q-uploader__subtitle { color: var(--text) !important; }
  .q-uploader .q-btn { color: var(--muted) !important; }
  .q-uploader__list { background: transparent !important; }
  .q-uploader__list .q-item { background: var(--surface) !important;
                              color: var(--text) !important;
                              border-radius: 2px !important;
                              margin: 3px !important; }
  .badge-open, .badge-closed, .badge-overdue, .badge-ai, .badge-manual,
  .badge-nophoto, .badge-mismatch, .badge-seen, .badge-closure, .badge-dup,
  .badge-you, .badge-ok, .badge-warn, .badge-fail, .badge-role {
    display: inline-block; font-size: 9px; font-weight: 700;
    letter-spacing: 0.08em; padding: 2px 6px; border-radius: 2px;
    text-transform: uppercase; line-height: 1.3;
  }
  .badge-open { color: var(--warn); border: 1px solid rgba(251,191,36,0.35); }
  .badge-closed { color: var(--success); border: 1px solid rgba(74,222,128,0.35); }
  .badge-overdue { color: var(--danger); border: 1px solid rgba(248,113,113,0.35); }
  .badge-ai { color: var(--accent); border: 1px solid rgba(94,234,212,0.3); }
  .badge-manual { color: var(--blue); border: 1px solid rgba(96,165,250,0.3); }
  .badge-nophoto { color: var(--muted); border: 1px solid var(--border-2); }
  .badge-mismatch { color: var(--warn); border: 1px solid rgba(251,191,36,0.3); }
  .badge-seen { color: var(--muted-2); border: 1px solid var(--border); }
  .badge-closure { color: var(--success); border: 1px solid rgba(74,222,128,0.3); }
  .badge-dup { color: #c4b5fd; border: 1px solid rgba(196,181,253,0.4); }
  .badge-you { color: var(--accent); border: 1px solid rgba(94,234,212,0.3); }
  .badge-ok { color: var(--success); border: 1px solid rgba(74,222,128,0.35); }
  .badge-warn { color: var(--warn); border: 1px solid rgba(251,191,36,0.35); }
  .badge-fail { color: var(--danger); border: 1px solid rgba(248,113,113,0.35); }
  .q-notification { border-radius: 3px !important; font-weight: 500 !important;
                    font-family: 'JetBrains Mono', monospace !important;
                    font-size: 11px !important;
                    background: var(--surface-2) !important;
                    color: var(--text) !important;
                    border: 1px solid var(--border-2) !important;
                    min-height: 30px !important; }
  .q-separator { background: var(--border) !important; }
  .scroll-box { max-height: 220px; overflow-y: auto;
                border: 1px solid var(--border); border-radius: 3px;
                padding: 6px; margin-top: 6px;
                background: var(--surface-2); }
  .or-divider { display: flex; align-items: center; gap: 8px;
                color: var(--muted-2); font-size: 9px; font-weight: 700;
                letter-spacing: 0.18em; margin: 10px 0; }
  .or-divider::before, .or-divider::after {
    content: ''; flex: 1; height: 1px; background: var(--border);
  }
  .metric-strip { display: grid; grid-template-columns: repeat(3, 1fr);
                  background: var(--surface); border: 1px solid var(--border);
                  border-radius: 4px; overflow: hidden;
                  margin-bottom: 12px; }
  .metric-cell { padding: 12px 14px; border-right: 1px solid var(--border);
                 border-bottom: 1px solid var(--border); }
  .metric-cell:nth-child(3n) { border-right: none; }
  .metric-cell:nth-last-child(-n+3) { border-bottom: none; }
  .metric-label { font-size: 9px; font-weight: 700; color: var(--muted-2);
                  letter-spacing: 0.14em; text-transform: uppercase;
                  margin-bottom: 4px; }
  .metric-value { font-size: 20px; font-weight: 700; color: var(--text);
                  line-height: 1.1; font-variant-numeric: tabular-nums; }
  .metric-value.open { color: var(--warn); }
  .metric-value.closed { color: var(--success); }
  .metric-value.overdue { color: var(--danger); }
  .metric-value.accent { color: var(--accent); }
  .bar-row { display: grid; grid-template-columns: 60px 1fr 40px;
             align-items: center; gap: 10px; padding: 6px 0;
             border-bottom: 1px solid var(--border); }
  .bar-row:last-child { border-bottom: none; }
  .bar-label { font-size: 11px; font-weight: 600; color: var(--text-soft); }
  .bar-track { height: 4px; background: var(--surface-3);
               border-radius: 2px; overflow: hidden; }
  .bar-fill { height: 100%; background: var(--accent); border-radius: 2px; }
  .bar-value { font-size: 11px; font-weight: 600; color: var(--text);
               text-align: right; font-variant-numeric: tabular-nums; }
  .sub-row { display: grid; grid-template-columns: 1fr auto; gap: 12px;
             padding: 10px 0; border-bottom: 1px solid var(--border);
             align-items: center; }
  .sub-row:last-child { border-bottom: none; }
  .sub-name { font-size: 12px; font-weight: 600; color: var(--text);
              white-space: nowrap; overflow: hidden;
              text-overflow: ellipsis; }
  .sub-badges { display: flex; gap: 4px; font-variant-numeric: tabular-nums; }
  .log-row { background: var(--surface); border: 1px solid var(--border);
             border-radius: 3px; padding: 12px 14px; margin-bottom: 6px;
             cursor: pointer; }
  .sub-card { background: var(--surface); border: 1px solid var(--border);
              border-radius: 4px; padding: 14px; margin-bottom: 8px; }
  .chip { display: inline-flex; align-items: center; gap: 6px;
          background: var(--surface-2); border: 1px solid var(--border-2);
          color: var(--text); font-size: 11px; font-weight: 500;
          padding: 3px 8px; border-radius: 2px; }
  .photo-grid { display: grid; grid-template-columns: repeat(3, 1fr);
                gap: 6px; margin-bottom: 12px; }
  .photo-cell { position: relative; }
  .photo-cell .q-img { width: 100%; height: 100px; object-fit: cover;
                       border-radius: 3px; border: 1px solid var(--border-2); }
  .photo-remove { position: absolute; top: 3px; right: 3px;
                  background: rgba(11,11,11,0.85); color: var(--danger);
                  border: 1px solid rgba(248,113,113,0.5); width: 20px;
                  height: 20px; border-radius: 2px; display: flex;
                  align-items: center; justify-content: center;
                  font-size: 12px; font-weight: 700; cursor: pointer;
                  z-index: 3; }
  .photo-tag { position: absolute; top: 6px; left: 6px;
               background: rgba(11,11,11,0.85); color: var(--muted);
               font-size: 9px; font-weight: 700; padding: 2px 6px;
               border-radius: 2px; text-transform: uppercase; z-index: 2; }
  .photo-tag.closure { color: var(--success); }
  .q-dialog .q-card { background: var(--surface) !important;
                      border: 1px solid var(--border-2) !important;
                      border-radius: 6px !important;
                      color: var(--text) !important; }
  .section-head { display: flex; justify-content: space-between;
                  align-items: center; margin-bottom: 10px;
                  padding-bottom: 6px; border-bottom: 1px solid var(--border); }
  .summary-card { background: var(--surface);
                  border: 1px solid var(--border); border-radius: 4px;
                  padding: 14px; font-size: 12px; line-height: 1.7;
                  color: var(--text-soft); margin-bottom: 12px; }
  .summary-card b { color: var(--accent); }
  /* Chat */
  .chat-msg { background: var(--surface); border: 1px solid var(--border);
              border-radius: 4px; padding: 10px 12px; margin-bottom: 8px; }
  .chat-msg.mine { border-color: rgba(94,234,212,0.4); }
  .chat-head { display: flex; justify-content: space-between;
               align-items: center; gap: 8px; margin-bottom: 4px; }
  .chat-author { font-size: 11px; font-weight: 700; cursor: pointer; }
  .chat-author:hover { text-decoration: underline; }
  .chat-title-tag { font-size: 10px; color: var(--muted); }
  .chat-time { font-size: 9px; color: var(--muted-2);
               font-variant-numeric: tabular-nums; }
  .chat-body { font-size: 12px; color: var(--text); line-height: 1.55;
               white-space: pre-wrap; word-break: break-word; }
  .chat-reply-quote { background: var(--surface-2);
                      border-left: 2px solid var(--accent);
                      padding: 4px 8px; font-size: 10px;
                      color: var(--muted); border-radius: 2px;
                      margin: 4px 0; }
  .chat-actions { display: flex; gap: 6px; margin-top: 4px; }
  .chat-act { font-size: 10px; color: var(--muted); cursor: pointer;
              background: none; border: none; padding: 2px 4px;
              font-family: inherit; font-weight: 600; }
  .chat-act:hover { color: var(--accent); }
  .chat-act.danger:hover { color: var(--danger); }
  .chat-composer { position: sticky; bottom: 0; background: var(--bg);
                   border-top: 1px solid var(--border); padding: 10px 0 4px;
                   z-index: 5; }
  .mention-chip { display: inline-block; color: var(--accent);
                  font-weight: 700; background: rgba(94,234,212,0.1);
                  padding: 0 4px; border-radius: 2px; }
  .mention-drop { position: absolute; bottom: 100%; left: 0; right: 0;
                  background: var(--surface-2);
                  border: 1px solid var(--border-2); border-radius: 4px;
                  max-height: 160px; overflow-y: auto; z-index: 100; }
  .mention-item { padding: 6px 10px; font-size: 11px; cursor: pointer;
                  color: var(--text); }
  .mention-item:hover { background: var(--surface-3); color: var(--accent); }
  .avatar-mini { width: 22px; height: 22px; border-radius: 50%;
                 background: var(--surface-3); display: inline-flex;
                 align-items: center; justify-content: center;
                 overflow: hidden; border: 1px solid var(--border-2);
                 color: var(--accent); font-weight: 700; font-size: 10px; }
  .avatar-mini img { width: 100%; height: 100%; object-fit: cover; }
  .avatar-big { width: 72px; height: 72px; border-radius: 50%;
                background: var(--surface-3); display: flex;
                align-items: center; justify-content: center;
                overflow: hidden; border: 1px solid var(--border-2);
                color: var(--accent); font-weight: 700; font-size: 26px; }
  .avatar-big img { width: 100%; height: 100%; object-fit: cover; }
  .chart-card { background: var(--surface); border: 1px solid var(--border);
                border-radius: 4px; padding: 12px; margin-bottom: 12px; }
                /* Defect status bar (item 2/3) */
  .status-bar {
    display: inline-block; width: 6px; height: 22px;
    border-radius: 2px; vertical-align: middle; margin-right: 8px;
    flex-shrink: 0;
  }
  .status-bar.orange { background: #d97706;
    box-shadow: 0 0 6px rgba(217,119,6,0.55); }
  .status-bar.green { background: #16a34a;
    box-shadow: 0 0 6px rgba(22,163,74,0.55); }
  .status-bar.red { background: #dc2626;
    box-shadow: 0 0 6px rgba(220,38,38,0.55); }
  .log-legend {
    display: flex; gap: 14px; flex-wrap: wrap;
    font-size: 10px; color: #808080; margin-bottom: 12px;
    padding: 8px 10px; background: var(--surface-2);
    border: 1px solid var(--border); border-radius: 4px;
  }
  .log-legend span { display: inline-flex; align-items: center; gap: 6px; }
  .log-legend .status-bar { height: 12px; width: 5px; margin: 0; }
  .log-dates {
    font-size: 10px; color: #b8b8b8; margin-top: 4px;
    font-variant-numeric: tabular-nums;
  }
  .log-dates b { color: #e8e8e8; }
  /* Floating chat tools */
  .chat-tools {
    position: fixed; top: 110px; right: 14px; z-index: 500;
    display: flex; flex-direction: column; gap: 6px;
  }
  .chat-tools .q-btn {
    background: rgba(11,11,11,0.94) !important;
    color: #5eead4 !important;
    border: 1px solid #262626 !important;
    box-shadow: 0 4px 10px rgba(0,0,0,0.4) !important;
  }
  
  .ocr-box { background: var(--surface-2); border: 1px dashed var(--border-2);
             border-radius: 4px; padding: 10px; margin-top: 6px; }
  /* MS chat */
  .ms-msg { background: var(--surface); border: 1px solid var(--border);
            border-radius: 4px; padding: 12px 14px; margin-bottom: 10px; }
  .ms-msg.kind-question { border-left: 3px solid #60a5fa; }
  .ms-msg.kind-check { border-left: 3px solid #fbbf24; }
  .ms-q { font-size: 12px; color: #b8b8b8; margin-bottom: 8px;
          white-space: pre-wrap; word-break: break-word; }
  .ms-a { font-size: 13px; color: #e8e8e8; line-height: 1.6;
          white-space: pre-wrap; word-break: break-word; }
  .ms-kv { display: grid; grid-template-columns: 1fr 1fr; gap: 4px 12px;
           font-size: 11px; color: #b8b8b8; margin-top: 6px; }
  .ms-kv b { color: #e8e8e8; }
  .ms-check { display: grid;
              grid-template-columns: 1fr 90px 60px;
              gap: 6px; padding: 6px 0;
              border-bottom: 1px solid var(--border);
              font-size: 11px; align-items: center; }
  .ms-check:last-child { border-bottom: none; }
  .ms-check .field { color: #b8b8b8; }
  .ms-check .val { color: #e8e8e8; font-weight: 600; }
  .ms-check .note { grid-column: 1 / -1; font-size: 10px;
                    color: #808080; margin-top: 2px; }
  .verdict-ok { color: #4ade80; font-weight: 700; }
  .verdict-warn { color: #fbbf24; font-weight: 700; }
  .verdict-fail { color: #f87171; font-weight: 700; }
  .overall-ok { color: #4ade80; font-weight: 700; letter-spacing: 0.14em; }
  .overall-warn { color: #fbbf24; font-weight: 700; letter-spacing: 0.14em; }
  .overall-fail { color: #f87171; font-weight: 700; letter-spacing: 0.14em; }
  .team-row { display: grid; grid-template-columns: 30px 1fr auto;
              gap: 8px; align-items: center; padding: 6px 0;
              border-bottom: 1px solid var(--border); }
  .team-row:last-child { border-bottom: none; }
  .team-avatar { width: 26px; height: 26px; border-radius: 50%;
                 background: var(--surface-3); display: flex;
                 align-items: center; justify-content: center;
                 color: var(--accent); font-weight: 700; font-size: 11px;
                 border: 1px solid var(--border-2); overflow: hidden; }
  .team-avatar img { width: 100%; height: 100%; object-fit: cover; }
</style>
""".replace("__DIR__", rtl)
    ui.add_head_html(html)


BTN_PRIMARY = "btn-primary"
BTN_SOFT = "btn-soft"
BTN_SUCCESS = "btn-success"
BTN_OUTLINE = "btn-outline"
BTN_DANGER = "btn-danger"


def _initial(name):
    s = (name or "?").strip()
    return s[0].upper() if s else "?"


_DASH_CACHE = {}
_DASH_TTL = 60  # seconds


def _dash_data(project_id):
    """Compute dashboard data with a 60s cache. Cleared on writes."""
    import time as _t
    now = _t.time()
    ent = _DASH_CACHE.get(project_id)
    if ent and (now - ent["ts"]) < _DASH_TTL:
        return ent["data"]
    data = {
        "kpis": db.kpi_summary(project_id),
        "zones": db.kpi_per_zone(project_id),
        "weeks": db.kpi_per_week(project_id, weeks=8),
        "scores": db.subcontractor_scores(project_id),
        "types": db.kpi_per_type(project_id),
        "scatter": db.defect_scatter_data(project_id),
        "rows": db.list_defects(project_id),
    }
    _DASH_CACHE[project_id] = {"ts": now, "data": data}
    return data


def _dash_invalidate(project_id):
    try:
        _DASH_CACHE.pop(project_id, None)
    except Exception:
        pass


def _is_admin_ui(user_id):
    try:
        return db.is_admin(user_id)
    except Exception:
        return False
def _can(state, action):
    """Check permission for the current user on the current project."""
    try:
        uid = state.get("user_id")
        pid = state.get("project_id")
        if not uid or not pid:
            return False
        return db.can_user(uid, pid, action)
    except Exception:
        return False


def _role_label(state):
    r = (state.get("role") or "").upper()
    return r or "MEMBER"


# =====================================================================
# MAIN
# =====================================================================
def build_defect_ui(user_id):
    _inject_theme()
    inject_pwa()
    user = db.get_user(user_id)

    state = {
        "user_id": user_id, "user": user,
        "project_id": app.storage.user.get("project_id"),
        "project": None, "tab": {"value": "new"},
        "sub_filter": None, "role": None,
    }

    if state["project_id"]:
        p = db.get_project(state["project_id"])
        if not p or not db.is_project_member(user_id, state["project_id"]):
            state["project_id"] = None
            state["project"] = None
            app.storage.user.pop("project_id", None)
        else:
            state["project"] = p
            state["role"] = db.get_user_role_in_project(
                user_id, state["project_id"])

    if not state["project_id"]:
        projects = db.list_projects(user_id)
        if projects:
            state["project_id"] = projects[0]["id"]
            state["project"] = projects[0]
            state["role"] = db.get_user_role_in_project(
                user_id, projects[0]["id"])
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
        with ui.element('div').style(
            "display:flex;align-items:center;gap:6px;"
        ):
            def _open_my_prof():
                _open_my_profile(state)
            ui.button(_initial(user.get("name") if user else "?"),
                      on_click=_open_my_prof).props("flat round dense").style(
                "color:#0b0b0b;background:#5eead4;font-weight:700;"
                "min-height:28px;min-width:28px;font-size:11px;")
            ui.button(_t("lang_button"), on_click=_toggle_lang).props(
                "flat dense no-caps size=sm").style(
                "color:#e8e8e8;font-weight:600;font-size:10px;"
                "border:1px solid #262626;border-radius:2px;"
                "padding:0 8px;min-height:26px;")

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
            elif tab == "mschat":
                _build_ms_chat(state)
            else:
                _build_dashboard(state)

    def _build_nav():
        nav_holder.clear()
        with nav_holder:
            for key, label in [
                ("new", _t("new_defect")), ("logs", _t("logs")),
                ("subs", _t("subs")), ("chat", _t("chat")),
                ("mschat", _t("ms_chat")),
                ("dashboard", _t("dashboard")),
            ]:
                active = state["tab"]["value"] == key
                cls = "top-tab-btn active" if active else "top-tab-btn"
                btn = ui.element('button').classes(cls)
                with btn:
                    ui.label(label).style("font-family:inherit;"
                                          "color:inherit;"
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

    _d = _dash_data(pid)
    kpis = _d["kpis"]
    if not kpis or kpis.get("total", 0) == 0:
        with ui.element('div').classes("card").style(
            "text-align:center;padding:32px;"
        ):
            ui.icon("insights").style("font-size:28px;color:#5a5a5a;")
            ui.label(_t("dash_empty")).classes("muted").style(
                "margin-top:10px;")
        return

    zones = _d["zones"]
    weeks = _d["weeks"]
    scores = _d["scores"]
    types = _d["types"]
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
            "Average close: <b>" + str(kpis["avg_days"]) + "d</b>. "
            "Busiest zone: <b>" + str(top_zone) + "</b>. "
            "Top sub: <b>" + str(top_sub) + "</b>."
        )

    with ui.element('div').classes("metric-strip"):
        _metric_cell(_t("kpi_total"), kpis["total"], "")
        _metric_cell(_t("kpi_open"), kpis["open"], "open")
        _metric_cell(_t("kpi_closed"), kpis["closed"], "closed")
        _metric_cell(_t("kpi_overdue"), kpis["overdue"], "overdue")
        _metric_cell(_t("kpi_closed_7d"), kpis["closed_7d"], "closed")
        _metric_cell(_t("kpi_avg_days"), str(kpis["avg_days"]) + "d", "accent")

    if weeks:
        labels = [w["label"] for w in weeks]
        raised = [w["count"] for w in weeks]
        try:
            rows = _d.get("rows") or []
            now = datetime.datetime.utcnow()
            closed_counts = []
            for i in range(len(weeks) - 1, -1, -1):
                start = now - datetime.timedelta(days=7 * (i + 1))
                end = now - datetime.timedelta(days=7 * i)
                c = 0
                for r in rows:
                    ca = r.get("closed_at")
                    if not ca:
                        continue
                    try:
                        cd = datetime.datetime.strptime(str(ca)[:19],
                                                         "%Y-%m-%d %H:%M:%S")
                        if start <= cd < end:
                            c += 1
                    except Exception:
                        pass
                closed_counts.append(c)
            closed_counts.reverse()
        except Exception:
            closed_counts = [0] * len(labels)

        with ui.element('div').classes("chart-card"):
            ui.label(_t("dash_line")).classes("label").style(
                "margin-bottom:6px;display:block;")
            ui.echart({
                'backgroundColor': 'transparent',
                'tooltip': {'trigger': 'axis'},
                'legend': {
                    'data': [_t("dash_line_raised"), _t("dash_line_closed")],
                    'textStyle': {'color': '#808080', 'fontSize': 10},
                    'top': 0,
                },
                'grid': {'left': 38, 'right': 12, 'top': 28, 'bottom': 26},
                'xAxis': {
                    'type': 'category',
                    'data': labels,
                    'axisLine': {'lineStyle': {'color': '#262626'}},
                    'axisLabel': {'color': '#808080', 'fontSize': 9},
                },
                'yAxis': {
                    'type': 'value',
                    'axisLine': {'lineStyle': {'color': '#262626'}},
                    'axisLabel': {'color': '#808080', 'fontSize': 9},
                    'splitLine': {'lineStyle': {'color': '#1a1a1a'}},
                },
                'series': [
                    {
                        'name': _t("dash_line_raised"),
                        'type': 'line', 'smooth': True,
                        'symbol': 'circle', 'symbolSize': 6,
                        'lineStyle': {'width': 2, 'color': '#5eead4'},
                        'itemStyle': {'color': '#5eead4'},
                        'areaStyle': {'color':
                            'rgba(94,234,212,0.12)'},
                        'data': raised,
                    },
                    {
                        'name': _t("dash_line_closed"),
                        'type': 'line', 'smooth': True,
                        'symbol': 'circle', 'symbolSize': 6,
                        'lineStyle': {'width': 2, 'color': '#4ade80'},
                        'itemStyle': {'color': '#4ade80'},
                        'data': closed_counts,
                    },
                ],
            }).style("height:230px;width:100%;")

    scatter = _d.get("scatter") or []
    if scatter:
        open_pts = [[p["x"], p["y"], p.get("uid", "")]
                    for p in scatter if p["status"] == "open"]
        closed_pts = [[p["x"], p["y"], p.get("uid", "")]
                      for p in scatter if p["status"] != "open"]
        with ui.element('div').classes("chart-card"):
            ui.label(_t("dash_scatter")).classes("label").style(
                "margin-bottom:6px;display:block;")
            ui.echart({
                'backgroundColor': 'transparent',
                'tooltip': {'trigger': 'item',
                             'formatter': 'UID: {c}'},
                'legend': {
                    'data': [_t("kpi_open"), _t("kpi_closed")],
                    'textStyle': {'color': '#808080', 'fontSize': 10},
                    'top': 0,
                },
                'grid': {'left': 42, 'right': 14, 'top': 28, 'bottom': 34},
                'xAxis': {
                    'type': 'value',
                    'name': _t("dash_scatter_x"),
                    'nameTextStyle': {'color': '#808080', 'fontSize': 9},
                    'axisLine': {'lineStyle': {'color': '#262626'}},
                    'axisLabel': {'color': '#808080', 'fontSize': 9},
                    'splitLine': {'lineStyle': {'color': '#1a1a1a'}},
                },
                'yAxis': {
                    'type': 'value',
                    'name': _t("dash_scatter_y"),
                    'nameTextStyle': {'color': '#808080', 'fontSize': 9},
                    'axisLine': {'lineStyle': {'color': '#262626'}},
                    'axisLabel': {'color': '#808080', 'fontSize': 9},
                    'splitLine': {'lineStyle': {'color': '#1a1a1a'}},
                },
                'series': [
                    {
                        'name': _t("kpi_open"), 'type': 'scatter',
                        'symbolSize': 10,
                        'itemStyle': {'color': '#fbbf24'},
                        'data': open_pts,
                    },
                    {
                        'name': _t("kpi_closed"), 'type': 'scatter',
                        'symbolSize': 10,
                        'itemStyle': {'color': '#4ade80'},
                        'data': closed_pts,
                    },
                ],
            }).style("height:230px;width:100%;")

    if zones:
        with ui.element('div').classes("chart-card"):
            ui.label(_t("dash_zones")).classes("label").style(
                "margin-bottom:6px;display:block;")
            ui.echart({
                'backgroundColor': 'transparent',
                'tooltip': {'trigger': 'axis'},
                'grid': {'left': 32, 'right': 12, 'top': 12, 'bottom': 26},
                'xAxis': {
                    'type': 'category',
                    'data': [str(z["zone"]) for z in zones],
                    'axisLine': {'lineStyle': {'color': '#262626'}},
                    'axisLabel': {'color': '#808080', 'fontSize': 9},
                },
                'yAxis': {
                    'type': 'value',
                    'axisLine': {'lineStyle': {'color': '#262626'}},
                    'axisLabel': {'color': '#808080', 'fontSize': 9},
                    'splitLine': {'lineStyle': {'color': '#1a1a1a'}},
                },
                'series': [{
                    'type': 'bar',
                    'data': [z["count"] for z in zones],
                    'itemStyle': {
                        'color': '#5eead4',
                        'borderRadius': [3, 3, 0, 0],
                    },
                    'barWidth': '55%',
                }],
            }).style("height:200px;width:100%;")

    if types:
        with ui.element('div').classes("chart-card"):
            ui.label(_t("defect_type_label")).classes("label").style(
                "margin-bottom:6px;display:block;")
            ui.echart({
                'backgroundColor': 'transparent',
                'tooltip': {'trigger': 'item'},
                'series': [{
                    'type': 'pie',
                    'radius': ['48%', '72%'],
                    'avoidLabelOverlap': True,
                    'label': {
                        'color': '#b8b8b8', 'fontSize': 10,
                        'formatter': '{b}: {c}',
                    },
                    'labelLine': {'lineStyle': {'color': '#262626'}},
                    'itemStyle': {
                        'borderColor': '#0b0b0b', 'borderWidth': 2,
                    },
                    'data': [
                        {'name': str(t["type"]), 'value': t["count"]}
                        for t in types
                    ],
                }],
            }).style("height:240px;width:100%;")

    if scores:
        with ui.element('div').classes("chart-card"):
            ui.label(_t("dash_subs")).classes("label").style(
                "margin-bottom:8px;display:block;")
            html = ("<table style='width:100%;border-collapse:collapse;"
                    "font-size:11px;font-variant-numeric:tabular-nums;'>"
                    "<thead><tr style='background:#0a0a0a;'>")
            for h in [_t("col_name"), _t("col_open"), _t("col_overdue"),
                      _t("col_closed"), _t("col_total")]:
                html += ("<th style='text-align:left;padding:6px 8px;"
                         "font-size:9px;letter-spacing:0.14em;"
                         "color:#5a5a5a;text-transform:uppercase;"
                         "border-bottom:1px solid #1e1e1e;'>" + h + "</th>")
            html += "</tr></thead><tbody>"
            for s in scores[:15]:
                nm = s["name"] or _t("unassigned")
                html += "<tr style='border-bottom:1px solid #1e1e1e;'>"
                html += ("<td style='padding:6px 8px;color:#e8e8e8;'>" +
                         _html_mod.escape(str(nm)) + "</td>")
                html += ("<td style='padding:6px 8px;color:#fbbf24;"
                         "font-weight:700;'>" + str(s["open"]) + "</td>")
                html += ("<td style='padding:6px 8px;color:#f87171;"
                         "font-weight:700;'>" + str(s["overdue"]) + "</td>")
                html += ("<td style='padding:6px 8px;color:#4ade80;"
                         "font-weight:700;'>" + str(s["closed"]) + "</td>")
                html += ("<td style='padding:6px 8px;color:#b8b8b8;'>" +
                         str(s["total"]) + "</td>")
                html += "</tr>"
            html += "</tbody></table>"
            ui.html(html)


def _metric_cell(label, value, variant):
    with ui.element('div').classes("metric-cell"):
        ui.label(label).classes("metric-label")
        cls = "metric-value"
        if variant:
            cls += " " + variant
        ui.label(str(value)).classes(cls)


def _build_dashboard_pdf(state, filename="dashboard.pdf"):
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
    )
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm

    project = state["project"]
    pid = state["project_id"]
    _d = _dash_data(pid)
    kpis = _d["kpis"]
    zones = _d["zones"]
    weeks = _d["weeks"]
    scores = _d["scores"]

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
                str(s["name"]), str(s["open"]), str(s["overdue"]),
                str(s["closed"]), str(s["total"]),
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

    ui.label(_t("subs_sub")).classes("muted").style("margin-bottom:8px;")

    if not masters:
        with ui.element('div').classes("card").style(
            "text-align:center;padding:32px;"
        ):
            ui.icon("engineering").style("font-size:28px;color:#5a5a5a;")
            ui.label(_t("no_subs")).classes("h3").style("margin-top:10px;")
            ui.label(_t("no_subs_hint")).classes("muted").style(
                "margin-top:4px;")
        return

    search_in = ui.input(placeholder="Search by name, trade, phone...").style(
        "width:100%;margin-bottom:12px;").props("dense clearable")

    sub_holder = ui.element('div').style("width:100%;")

    def _render_list(q=""):
        sub_holder.clear()
        q = (q or "").strip().lower()
        filtered = []
        for m in masters:
            hay = " ".join([
                str(m.get("name") or ""),
                str(m.get("trade") or ""),
                str(m.get("phone") or ""),
                str(m.get("notes") or ""),
            ]).lower()
            if not q or q in hay:
                filtered.append(m)

        with sub_holder:
            if not filtered:
                msg = "No matches." if q else _t("no_subs")
                ui.label(msg).classes("mono-sm").style(
                    "text-align:center;padding:26px 0;color:#5a5a5a;")
                return
            for m in filtered:
                _render_sub_card(state, pid, m, scores_by_name)

    def _on_search(e):
        _render_list(e.value or "")

    search_in.on("update:model-value", _on_search)
    _render_list()


def _render_sub_card(state, pid, m, scores_by_name):
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
                        str(score["open"]) + ' ' + _t("sub_open") + '</span>')
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
# PROFILE
# =====================================================================
def _open_my_profile(state, on_saved=None):
    u = db.get_user(state["user_id"]) or {}
    with ui.dialog() as dlg, ui.card().style(
        "padding:22px;min-width:320px;max-width:95vw;width:420px;"
    ):
        ui.label(_t("my_profile")).classes("h1").style("margin-bottom:16px;")

        name_in = ui.input(_t("profile_name"),
                            value=u.get("name") or "").style("width:100%;")
        title_opts = [""] + TITLES
        try:
            ti = title_opts.index(u.get("title") or "")
        except Exception:
            ti = 0
        title_in = ui.select(title_opts, value=title_opts[ti],
                              label=_t("profile_title"),
                              with_input=True).style("width:100%;")

        photo_holder = {"bytes": u.get("photo_bytes")}
        photo_lbl = ui.label(_t("profile_photo")).classes("mono-sm").style(
            "margin-top:8px;display:block;"
        )

        async def handle_photo(e):
            photo_holder["bytes"] = await e.file.read()
            photo_lbl.set_text(_t("profile_photo") + " OK")

        ui.upload(on_upload=handle_photo, auto_upload=True).style(
            "width:100%;"
        ).props("flat bordered accept=image/* label='" +
                _t("profile_photo") + "'")

        def _save():
            if not name_in.value.strip():
                ui.notify(_t("profile_name"), type="warning")
                return
            db.update_user_profile(
                state["user_id"], name_in.value.strip(),
                title_in.value or "", photo_holder["bytes"])
            state["user"] = db.get_user(state["user_id"])
            ui.notify(_t("profile_saved"), type="positive")
            dlg.close()
            if on_saved:
                try: on_saved()
                except Exception: pass
            try:
                ui.navigate.reload()
            except Exception:
                pass

        with ui.element('div').style("display:flex;gap:8px;margin-top:16px;"):
            ui.button(_t("save"), on_click=_save).classes(
                BTN_PRIMARY).style("flex:1;")
            ui.button(_t("cancel_btn"), on_click=dlg.close).classes(BTN_SOFT)
    dlg.open()


# =====================================================================
# TEAM / INVITE
# =====================================================================
def _open_invite_member_dialog(state, refresh_fn):
    if not state.get("project_id"):
        ui.notify(_t("setup_first"), type="warning")
        return
    if state.get("role") != "owner":
        ui.notify("Only the project owner can invite members.",
                   type="warning")
        return

    with ui.dialog() as dlg, ui.card().style(
        "padding:20px;min-width:340px;max-width:96vw;width:560px;"
        "max-height:92vh;overflow-y:auto;"
    ):
        ui.label(_t("team_invite_title")).classes("h1").style(
            "margin-bottom:14px;")

        with ui.tabs().style("width:100%;margin-bottom:14px;") as tabs:
            tab_email = ui.tab("Add by email")
            tab_link = ui.tab("Share invite link")

        with ui.tab_panels(tabs, value=tab_email).style("width:100%;"):
            # ---------- EMAIL PANEL ----------
            with ui.tab_panel(tab_email):
                ui.label(_t("team_invite_hint")).classes("mono-sm").style(
                    "margin-bottom:10px;display:block;line-height:1.5;")
                email_in = ui.input(_t("team_email")).style("width:100%;")
                role_in = ui.select(_role_options(), value="engineer",
                                     label=_t("team_role")).style("width:100%;")
                send_email_too = ui.checkbox(
                    "Send them an email notification",
                    value=True).style("margin-top:8px;")

                def _save_email():
                    em = (email_in.value or "").strip().lower()
                    if not em or "@" not in em:
                        ui.notify(_t("team_email"), type="warning")
                        return
                    ok, msg = db.add_project_member(
                        project_id=state["project_id"], email=em,
                        role=role_in.value or "engineer")
                    if not ok:
                        ui.notify(_t("team_failed") + str(msg),
                                   type="negative")
                        return

                    try:
                        db.activity_add(
                            state["project_id"], state["user_id"],
                            "invited_member", target_type="user",
                            target_id=em,
                            details="role=" + (role_in.value or "engineer"),
                            user_name=(state.get("user") or {}).get(
                                "name", ""))
                    except Exception:
                        pass

                    if send_email_too.value:
                        try:
                            from services import alert_service as alerts
                            proj_name = (state.get("project") or {}).get(
                                "name", "Project")
                            inviter = (state.get("user") or {}).get(
                                "name", "A teammate")
                            html = (
                                "<div style='font-family:monospace;"
                                "color:#111;'>"
                                "<h2>" + inviter + " added you to "
                                + str(proj_name) + "</h2>"
                                "<p>You now have access to this project "
                                "on Defect Notices.</p>"
                                "<p>Sign in with this email address to "
                                "see the project.</p>"
                                "</div>"
                            )
                            alerts.send_email(
                                em,
                                "You were added to " + str(proj_name),
                                html)
                        except Exception as e:
                            print("[invite] email failed: " + repr(e))

                    ui.notify(_t("team_added"), type="positive")
                    dlg.close()
                    ui.timer(0.03, refresh_fn, once=True)

                ui.button(_t("team_add"), on_click=_save_email).classes(
                    BTN_PRIMARY).style("width:100%;margin-top:14px;")
            # ---------- LINK PANEL ----------
            with ui.tab_panel(tab_link):
                ui.label("Generate a link. Anyone with this link can "
                          "join the project with the role below. "
                          "The link expires and can be revoked.").classes(
                    "mono-sm").style(
                    "margin-bottom:10px;display:block;line-height:1.5;")
                link_role = ui.select(_role_options(), value="engineer",
                                       label=_t("team_role")).style(
                    "width:100%;")
                days_opts = {"1": "1 day", "3": "3 days",
                             "7": "7 days", "30": "30 days"}
                link_days = ui.select(days_opts, value="7",
                                       label="Expires in").style(
                    "width:100%;")
                link_uses = ui.number("Max uses", value=50, min=1,
                                       max=500).style("width:100%;")

                result_holder = ui.element('div').style("width:100%;")

                def _generate():
                    result_holder.clear()
                    tok = db.invite_create(
                        project_id=state["project_id"],
                        role=link_role.value or "engineer",
                        created_by=state["user_id"],
                        days=int(link_days.value or "7"),
                        max_uses=int(link_uses.value or 50))
                    base = ""
                    try:
                        base = str(app.storage.browser.get(
                            "window_location", ""))
                    except Exception:
                        base = ""
                    if not base:
                        base = "https://smart-egy-ai-engine.onrender.com"
                    url = base.rstrip("/") + "/join?token=" + tok

                    with result_holder:
                        ui.label("Invite link (share this):").classes(
                            "label").style("margin-bottom:6px;display:block;")
                        link_in = ui.input(value=url).style(
                            "width:100%;").props("readonly")
                        try:
                            link_in.props("dense")
                        except Exception:
                            pass

                        # QR code
                        try:
                            from services.pdf_service import generate_qr_code
                            qr_buf = generate_qr_code(url)
                            b64 = base64.b64encode(qr_buf.read()).decode(
                                "ascii")
                            ui.html(
                                '<div style="text-align:center;'
                                'margin-top:14px;">'
                                '<img src="data:image/png;base64,' + b64 +
                                '" style="width:180px;height:180px;'
                                'background:#fff;padding:8px;'
                                'border-radius:6px;"/>'
                                '<div style="font-size:10px;color:#808080;'
                                'margin-top:6px;">Scan to join</div>'
                                '</div>'
                            )
                        except Exception as e:
                            print("[invite] QR failed: " + repr(e))

                        with ui.element('div').style(
                            "display:flex;gap:6px;margin-top:12px;"
                        ):
                            def _copy():
                                try:
                                    ui.run_javascript(
                                        "navigator.clipboard."
                                        "writeText('" +
                                        url.replace("'", "\\'") + "');")
                                    ui.notify("Link copied.",
                                               type="positive")
                                except Exception as e:
                                    ui.notify("Copy failed: " + str(e),
                                               type="negative")

                            def _email_send():
                                em = ui.input("Email to send the link to:") \
                                    .style("width:100%;")
                                ui.notify("Type email and click Send.",
                                           type="info")
                            ui.button("Copy link", icon="content_copy",
                                      on_click=_copy).classes(
                                BTN_SOFT).style("flex:1;")
                            ui.button("Open link", icon="open_in_new",
                                      on_click=lambda u=url:
                                      ui.navigate.to(u)).classes(
                                BTN_SOFT).style("flex:1;")

                ui.button("Generate link", icon="link",
                          on_click=_generate).classes(
                    BTN_PRIMARY).style("width:100%;margin-top:14px;")

                result_holder

                # Existing active links
                existing = db.invite_list_for_project(state["project_id"])
                if existing:
                    ui.element('div').style(
                        "border-top:1px solid #1e1e1e;margin:18px 0 10px;")
                    ui.label("Active links").classes("label").style(
                        "display:block;margin-bottom:8px;")
                    for inv in existing[:5]:
                        with ui.element('div').classes("item-box"):
                            with ui.element('div').style(
                                "display:flex;justify-content:space-between;"
                                "align-items:center;gap:8px;"
                            ):
                                with ui.element('div').style(
                                    "min-width:0;flex:1;"
                                ):
                                    ui.label(
                                        "role: " + str(inv.get("role") or "") +
                                        "  ·  uses " +
                                        str(inv.get("used_count") or 0) +
                                        "/" + str(inv.get("max_uses") or 50)
                                    ).classes("mono-sm").style(
                                        "font-size:10px;display:block;")
                                    ui.label(
                                        "expires " +
                                        str(inv.get("expires_at") or "")[:16]
                                    ).classes("mono-sm").style(
                                        "font-size:10px;display:block;")
                                def _revoke(iid=inv.get("id")):
                                    db.invite_revoke(iid)
                                    ui.notify("Link revoked.",
                                               type="positive")
                                    dlg.close()
                                ui.button(icon="close", on_click=_revoke).props(
                                    "flat round dense size=xs").style(
                                    "color:#f87171;")

        with ui.element('div').style(
            "display:flex;gap:8px;margin-top:16px;"
        ):
            ui.button(_t("cancel_btn"), on_click=dlg.close).classes(
                BTN_SOFT).style("flex:1;")

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

                if _can(state, "edit_project"):
                    def open_setup():
                        _open_setup_dialog(state, refresh, is_new=False)
                    ui.button(_t("edit"), icon="settings",
                              on_click=open_setup).classes(BTN_SOFT).style(
                        "width:100%;margin-top:10px;font-size:10px;"
                        "min-height:30px;")

                ui.element('div').style(
                    "border-top:1px solid #1e1e1e;margin:14px 0 12px;")

                # ---------- TEAM ----------
                with ui.element('div').style(
                    "display:flex;justify-content:space-between;"
                    "align-items:center;margin-bottom:8px;"
                ):
                    ui.label(_t("team_members")).classes("label")
                    if state.get("role") == "owner" and state.get("project_id"):
                        def _open_invite():
                            _open_invite_member_dialog(state, refresh)
                        ui.button(icon="person_add", on_click=_open_invite).props(
                            "flat round dense size=sm").style(
                            "color:#5eead4;")

                members = db.list_project_members(state["project_id"])
                if not members:
                    ui.label(_t("team_no_members")).classes("mono-sm")
                else:
                    for m in members:
                        role = (m.get("role") or "engineer").lower()
                        is_me = (m.get("user_id") == state["user_id"])
                        with ui.element('div').classes("team-row"):
                            av = '<div class="team-avatar">'
                            if m.get("name"):
                                av += _html_mod.escape(
                                    (m["name"] or "?")[:1].upper())
                            else:
                                av += "?"
                            av += '</div>'
                            ui.html(av)
                            with ui.element('div').style("min-width:0;"):
                                nm = str(m.get("name") or "—")
                                if is_me:
                                    nm += " " + _t("team_you")
                                ui.label(nm).style(
                                    "font-size:11px;color:#e8e8e8;"
                                    "font-weight:600;overflow:hidden;"
                                    "text-overflow:ellipsis;"
                                    "white-space:nowrap;")
                                sub = m.get("title") or m.get("email") or ""
                                if sub:
                                    ui.label(str(sub)).classes("mono-sm").style(
                                        "font-size:9px;overflow:hidden;"
                                        "text-overflow:ellipsis;"
                                        "white-space:nowrap;")
                            rc = ROLE_COLORS.get(role, "#808080")
                            ui.html('<span class="badge-role" style="color:' +
                                    rc + ';border:1px solid ' + rc +
                                    '55;">' + role + '</span>')
                            if (state.get("role") == "owner"
                                    and role != "owner"):
                                def _rm(mem=m):
                                    _confirm_remove_member(state, mem,
                                                            refresh)
                                ui.button(icon="close", on_click=_rm).props(
                                    "flat round dense size=xs").style(
                                    "color:#5a5a5a;")

                ui.element('div').style(
                    "border-top:1px solid #1e1e1e;margin:14px 0 12px;")

                # ---------- MS ----------
                with ui.element('div').style(
                    "display:flex;justify-content:space-between;"
                    "align-items:center;margin-bottom:8px;"
                ):
                    ui.label(_t("ms_section")).classes("label")
                    if state.get("project_id"):
                        def open_ms():
                            _open_ms_dialog(state, refresh)
                        ui.button(icon="add", on_click=open_ms).props(
                            "flat round dense size=sm").style(
                            "color:#5eead4;")

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

                # 👇 NEW — ACTIVITY SECTION — paste here 👇
                ui.element('div').style(
                    "border-top:1px solid #1e1e1e;margin:14px 0 12px;")

                with ui.element('div').style(
                    "display:flex;justify-content:space-between;"
                    "align-items:center;margin-bottom:8px;"
                ):
                    ui.label("ACTIVITY").classes("label")

                try:
                    acts = db.activity_list(state["project_id"], limit=15)
                except Exception:
                    acts = []

                if not acts:
                    ui.label("No activity yet.").classes("mono-sm")
                else:
                    for a in acts:
                        with ui.element('div').style(
                            "background:#101010;border:1px solid #1e1e1e;"
                            "border-radius:3px;padding:6px 8px;"
                            "margin-bottom:4px;"
                        ):
                            nm = a.get("user_name") or "user"
                            act = (a.get("action") or "").replace("_", " ")
                            tgt = a.get("target_id") or ""
                            detail = a.get("details") or ""
                            line = nm + "  " + act
                            if tgt:
                                line += "  · " + str(tgt)[:24]
                            ui.label(line).style(
                                "font-size:10px;color:#e8e8e8;"
                                "font-weight:600;")
                            if detail:
                                ui.label(str(detail)[:60]).classes(
                                    "mono-sm").style("font-size:9px;")
                            ui.label(str(a.get("created_at") or "")[:16]).classes(
                                "mono-sm").style("font-size:9px;color:#5a5a5a;")
                # 👆 END of new block 👆

            ui.element('div').style(
                "border-top:1px solid #1e1e1e;margin:14px 0 12px;")

            def _open_profile():
                _open_my_profile(state, refresh)
            ui.button(_t("my_profile"), icon="person",
                      on_click=_open_profile).classes(BTN_SOFT).style(
                "width:100%;font-size:10px;min-height:30px;"
                "margin-bottom:6px;")

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
        ui.label(_t("projects_title")).classes("h1").style(
            "margin-bottom:14px;")
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
                    role = db.get_user_role_in_project(state["user_id"], p["id"])
                    if role:
                        rc = ROLE_COLORS.get(role, "#808080")
                        ui.html('<span class="badge-role" style="color:' + rc +
                                ';border:1px solid ' + rc + '55;margin-top:4px;'
                                'display:inline-block;">' + role + '</span>')

                    def _pick(pid=p["id"]):
                        state["project_id"] = pid
                        app.storage.user["project_id"] = pid
                        state["project"] = db.get_project(pid)
                        state["role"] = db.get_user_role_in_project(
                            state["user_id"], pid)
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
            if state.get("role") != "owner":
                ui.notify("Only the owner can delete.", type="warning")
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
        ui.label(_t("delete_confirm")).classes("h3").style(
            "margin-bottom:14px;")

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
                                  value=proj.get("contractor", "")).style(
            "width:100%;")
        sub_in = ui.input(_t("subcontractor"),
                           value=proj.get("subcontractor", "")).style(
            "width:100%;")
        consultant_in = ui.input(_t("consultant"),
                                  value=proj.get("consultant", "")).style(
            "width:100%;")
        location_in = ui.input(_t("location"),
                                value=proj.get("location", "")).style(
            "width:100%;")
        engineer_in = ui.input(_t("engineer"),
                                value=proj.get("engineer_name", "")).style(
            "width:100%;")

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
                        consultant_in.value.strip(),
                        location_in.value.strip(),
                        engineer_in.value.strip(), logo_holder["bytes"])
                    state["project_id"] = pid
                    app.storage.user["project_id"] = pid
                    state["project"] = db.get_project(pid)
                    state["role"] = "owner"
                else:
                    db.update_project(
                        state["project_id"], name_in.value.strip(),
                        contractor_in.value.strip(), sub_in.value.strip(),
                        consultant_in.value.strip(),
                        location_in.value.strip(),
                        engineer_in.value.strip(), logo_holder["bytes"])
                    state["project"] = db.get_project(state["project_id"])
                ui.notify(_t("save") + " OK", type="positive")
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
        ui.label(_t("ms_dialog_title")).classes("h1").style(
            "margin-bottom:14px;")
        holder = {"bytes": None, "name": ""}
        file_status = ui.label("").classes("mono-sm").style("margin-top:6px;")

        async def handle_file(e):
            holder["bytes"] = await e.file.read()
            holder["name"] = e.file.name
            file_status.set_text(_t("file_loaded") + e.file.name +
                                  " (" + str(len(holder["bytes"]) // 1024) +
                                  " KB)")

        ui.upload(on_upload=handle_file, auto_upload=True).style(
            "width:100%;").props(
            "flat bordered accept=.pdf,.docx,.doc,.txt,.md "
            "label='" + _t("ms_upload_file") + "'")
        file_status
        ms_num_in = ui.input(_t("ms_number"), value="MS-01").style(
            "width:100%;")
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
                            ui.label("S" + cl["id"] + "  " + cl["title"]).style(
                                "font-size:10px;font-weight:600;"
                                "color:#e8e8e8;")
                            ui.label(cl["text"][:180]).classes(
                                "mono-sm").style(
                                "font-size:9px;margin-top:2px;")

                def confirm():
                    db.save_ms(
                        project_id=state["project_id"],
                        ms_number=ms_num_in.value.strip(),
                        title=title_in.value.strip(),
                        element_type=element_in.value,
                        discipline=disc_in.value,
                        pdf_bytes=holder["bytes"], clauses=clauses,
                        full_text=(result.get("full_text") or ""))
                    ui.notify(_t("ms_saved") + " OK", type="positive")
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
    if not _can(state, "raise"):
        with ui.element('div').classes("card").style(
            "text-align:center;padding:32px 20px;"
        ):
            ui.icon("lock").style("font-size:28px;color:#fbbf24;")
            ui.label("You don't have permission to raise defects on this "
                      "project.").classes("muted").style(
                "margin-top:10px;line-height:1.6;")
            ui.label("Your role: " + _role_label(state)).classes(
                "mono-sm").style("margin-top:6px;")
        return

    stage = {"photos": [], "mime": "image/jpeg",
             "candidates": None, "manual": [],
             "text_only": False, "text_desc": "",
             "zone": "A", "place": "", "element": "column",
             "note": "", "defect_type": "General",
             "lat": None, "lng": None}
    loc_state = {"ready": False, "acc": 0}

    with ui.element('div').classes("card").style("margin-bottom:12px;"):
        ui.label(_t("photo_title")).classes("h1").style("margin-bottom:3px;")
        ui.label(_t("photo_sub")).classes("muted").style("margin-bottom:10px;")

        # -------- SECURITY MESSAGE --------
        ui.html(
            '<div style="background:#101010;border:1px solid #1e1e1e;'
            'border-left:3px solid #fbbf24;border-radius:3px;'
            'padding:10px 12px;margin-bottom:12px;'
            'font-size:11px;color:#c8c8c8;line-height:1.6;">'
            '🔒 <b style="color:#e8e8e8;">Security</b> — To ensure every '
            'defect is verified at its exact site, photos must be taken '
            '<b>live from your camera</b> and your <b>location must be '
            'enabled</b>. Photos from your gallery cannot be uploaded.'
            '</div>'
        )

        # -------- LOCATION STATUS --------
        loc_bar = ui.element('div').style(
            "background:#101010;border:1px solid #1e1e1e;border-radius:3px;"
            "padding:8px 10px;margin-bottom:12px;font-size:11px;"
            "color:#808080;"
        )

        def render_loc():
            loc_bar.clear()
            with loc_bar:
                if loc_state["ready"]:
                    ui.html(
                        '<span style="color:#4ade80;font-weight:700;">'
                        '📍 Location enabled</span>'
                        '<span style="color:#5a5a5a;"> · accuracy ± '
                        + str(int(loc_state["acc"])) + 'm</span>'
                    )
                else:
                    ui.html(
                        '<span style="color:#fbbf24;font-weight:700;">'
                        '📍 Location not enabled</span>'
                        '<span style="color:#5a5a5a;"> · required before '
                        'taking a photo</span>'
                    )

        render_loc()

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
                            ui.html('<div class="photo-remove">x</div>'
                                    ).on("click", _rm)
                            try:
                                b64 = base64.b64encode(p).decode("ascii")
                                ui.image("data:image/jpeg;base64," + b64)
                            except Exception:
                                pass

        async def handle_photo(e):
            if not loc_state["ready"]:
                ui.notify("Enable location first.", type="warning")
                return
            try:
                data = await e.file.read()
            except Exception as ex:
                ui.notify(_t("upload_failed") + str(ex), type="negative")
                return
            if not data:
                ui.notify(_t("empty_file"), type="warning")
                return

            # Refresh GPS at the moment of upload
            pos = await _get_browser_location()
            if not pos:
                ui.notify(
                    "Location could not be read. Enable GPS and try again.",
                    type="negative", timeout=6000)
                return
            stage["lat"] = pos["lat"]
            stage["lng"] = pos["lng"]
            loc_state["acc"] = pos["acc"]
            render_loc()

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

        upload_holder = ui.element('div').style("width:100%;")

        async def enable_location():
            ui.notify("Requesting location permission...", type="info",
                       timeout=3000)
            pos = await _get_browser_location()
            if not pos:
                ui.notify(
                    "Location was denied or unavailable. Open your browser "
                    "settings and allow location for this site, then try "
                    "again.", type="negative", timeout=8000)
                return
            loc_state["ready"] = True
            loc_state["acc"] = pos["acc"]
            stage["lat"] = pos["lat"]
            stage["lng"] = pos["lng"]
            render_loc()
            render_upload()
            ui.notify("Location enabled — camera unlocked.",
                       type="positive")

        def render_upload():
            upload_holder.clear()
            with upload_holder:
                if not loc_state["ready"]:
                    ui.button("📍 Enable location to unlock camera",
                              icon="my_location",
                              on_click=enable_location).classes(
                        BTN_PRIMARY).style("width:100%;")
                    return
                ui.upload(on_upload=handle_photo, auto_upload=True).style(
                    "width:100%;").props(
                    "flat bordered accept=image/* capture=environment "
                    "multiple label='" +
                    (_t("add_photos") if stage["photos"]
                     else _t("choose_photo")) + "'")

        render_upload()

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
        "padding:20px;min-width:340px;max-width:96vw;width:560px;"
        "max-height:92vh;overflow-y:auto;"
    ):
        ui.label(_t("no_photo_title")).classes("h1").style("margin-bottom:3px;")
        ui.label(_t("no_photo_sub")).classes("muted").style("margin-bottom:14px;")

        ui.label(_t("ocr_label")).classes("label").style(
            "margin-bottom:2px;display:block;")
        ui.label(_t("ocr_hint")).classes("mono-sm").style(
            "margin-bottom:8px;display:block;line-height:1.5;")

        ocr_status = ui.label("").classes("mono-sm").style(
            "margin-top:6px;display:block;min-height:14px;")

        desc_in = ui.textarea(
            label=_t("defect_desc"),
            placeholder=_t("defect_desc_placeholder")).style("width:100%;")

        async def handle_ocr(e):
            try:
                data = await e.file.read()
            except Exception as ex:
                ui.notify(_t("upload_failed") + str(ex), type="negative")
                return
            if not data:
                ui.notify(_t("empty_file"), type="warning")
                return
            name = (e.file.name or "").lower()
            if name.endswith(".pdf"):
                mime = "application/pdf"
            elif name.endswith(".png"):
                mime = "image/png"
            elif name.endswith((".jpg", ".jpeg")):
                mime = "image/jpeg"
            else:
                mime = "image/jpeg"

            ocr_status.set_text(_t("ocr_reading"))
            ocr_status.style("color:#fbbf24;font-size:10px;margin-top:6px;"
                              "display:block;min-height:14px;")
            text, err = await _ocr_handwriting(data, mime)
            if err:
                ocr_status.set_text(_t("ocr_failed") + " " + str(err))
                ocr_status.style("color:#f87171;font-size:10px;"
                                  "margin-top:6px;display:block;"
                                  "min-height:14px;")
                return
            existing = (desc_in.value or "").strip()
            merged = (existing + "\n" + text).strip() if existing else text
            desc_in.value = merged
            ocr_status.set_text(_t("ocr_done"))
            ocr_status.style("color:#4ade80;font-size:10px;margin-top:6px;"
                              "display:block;min-height:14px;")

        with ui.element('div').classes("ocr-box"):
            ui.upload(on_upload=handle_ocr, auto_upload=True).style(
                "width:100%;").props(
                "flat bordered accept=image/*,.pdf "
                "label='" + _t("ocr_upload") + "'")
            ocr_status

        ui.element('div').style("height:6px;")
        desc_in

        with ui.element('div').style(
            "display:grid;grid-template-columns:1fr 2fr;gap:8px;"
            "margin-top:10px;"
        ):
            zone_in = ui.input(_t("zone"), value="A",
                                placeholder=_t("zone_placeholder")).style(
                "width:100%;")
            place_in = ui.input(
                _t("place_of_defect"),
                placeholder=_t("place_of_defect_placeholder")).style(
                "width:100%;")

        btn = ui.button(_t("analyze"), icon="auto_awesome")

        async def do_analyze():
            if not (desc_in.value or "").strip():
                ui.notify(_t("desc_required"), type="warning")
                return
            btn.props("loading")
            btn.set_text(_t("analyzing"))
            element_type = _guess_element(place_in.value)
            ms_clauses = db.get_clauses_for_element(
                state["project_id"], element_type)
            result = await svc.analyze_defect_text(
                description=desc_in.value.strip(),
                note="",
                ms_clauses=ms_clauses,
                element_type=element_type,
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
            stage["note"] = ""
            stage["zone"] = (zone_in.value or "A").strip() or "A"
            stage["place"] = (place_in.value or "").strip()
            stage["element"] = element_type
            for c in stage["candidates"]:
                c["_sel"] = True
                c["_manual"] = False
                c["_nophoto"] = True
            dlg.close()
            ui.timer(0.15, refresh_fn, once=True)

        btn.on("click", do_analyze)
        btn.classes(BTN_PRIMARY).style("width:100%;margin-top:14px;")

        def _raise_direct():
            desc = (desc_in.value or "").strip()
            if not desc:
                ui.notify(_t("desc_required"), type="warning")
                return
            lines = desc.split("\n", 1)
            name = (lines[0].strip() or "Defect")[:120]
            extra_context = lines[1].strip() if len(lines) > 1 else ""
            loc_hint = extra_context or (place_in.value or "").strip()
            stage["candidates"] = [{
                "name": name,
                "location_hint": loc_hint,
                "severity": "Medium",
                "ms_violations": [],
                "code_violations": [],
                "repair_action": "",
                "context_mismatch": True,
                "_sel": True,
                "_manual": True,
                "_nophoto": True,
            }]
            stage["manual"] = []
            stage["photos"] = []
            stage["text_only"] = True
            stage["text_desc"] = desc
            stage["note"] = ""
            stage["zone"] = (zone_in.value or "A").strip() or "A"
            stage["place"] = (place_in.value or "").strip()
            stage["element"] = _guess_element(place_in.value)
            dlg.close()
            ui.timer(0.15, refresh_fn, once=True)

        ui.button("Raise without AI analysis", icon="arrow_forward",
                  on_click=_raise_direct).classes(BTN_SOFT).style(
            "width:100%;margin-top:6px;")

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
                "display:grid;grid-template-columns:1fr 2fr;gap:8px;"
                "margin-top:8px;"
            ):
                zone_in = ui.input(_t("zone"), value="A",
                                    placeholder=_t("zone_placeholder")).style(
                    "width:100%;")
                place_in = ui.input(
                    _t("place_of_defect"),
                    placeholder=_t("place_of_defect_placeholder")).style(
                    "width:100%;")
            analyze_btn = ui.button(_t("analyze"), icon="auto_awesome")

            async def do_analyze():
                element_type = _guess_element(place_in.value)
                ms_clauses = db.get_clauses_for_element(
                    state["project_id"], element_type)
                analyze_btn.props("loading")
                analyze_btn.set_text(_t("analyzing"))
                result = await svc.analyze_defect_photo(
                    photo_bytes=stage["photos"][0], mime_type=stage["mime"],
                    note=note_in.value or "", ms_clauses=ms_clauses,
                    element_type=element_type,
                    call_gemini_json_fn=call_gemini_json)
                analyze_btn.props(remove="loading")
                analyze_btn.set_text(_t("analyze"))
                if result.get("error"):
                    ui.notify(result["error"], type="negative")
                    return
                stage["candidates"] = list(result["defects"])
                stage["manual"] = []
                stage["note"] = note_in.value or ""
                stage["zone"] = (zone_in.value or "A").strip() or "A"
                stage["place"] = (place_in.value or "").strip()
                stage["element"] = element_type
                for c in stage["candidates"]:
                    c["_sel"] = True
                    c["_manual"] = False
                ui.timer(0.15, refresh_fn, once=True)

            analyze_btn.on("click", do_analyze)
            analyze_btn.classes(BTN_PRIMARY).style(
                "width:100%;margin-top:12px;")
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
        ui.label(_t("notice_details")).classes("h1").style(
            "margin-bottom:12px;")
        sub_in = ui.input(
            _t("send_to"),
            value=(state["project"] or {}).get("subcontractor", "") or "",
            placeholder=_t("send_to_placeholder")).style("width:100%;")
        with ui.element('div').style(
            "display:grid;grid-template-columns:1fr 1fr;gap:8px;"
            "margin-top:8px;"
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

        default_eng = ((state.get("user") or {}).get("name") or
                       (state["project"] or {}).get("engineer_name", "") or "")
        engineer_in = ui.input(_t("engineer_field"),
                                value=default_eng).style(
            "width:100%;margin-top:8px;")
        ui.input(_t("place_of_defect"),
                  value=stage.get("place", "")).props("readonly").style(
            "width:100%;margin-top:8px;")
        dtype_in = ui.select(
            _defect_type_options(),
            value=stage.get("defect_type", "General"),
            label=_t("defect_type_label")).style("width:100%;margin-top:8px;")
        stage["defect_type"] = dtype_in.value

        def _on_dtype(e):
            stage["defect_type"] = e.value or "General"
        dtype_in.on("update:model-value", _on_dtype)

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
                    notice_uid=notice_uid,
                    subcontractor=sub_in.value.strip(),
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
                place=stage.get("place", "") or "",
                defect_type=stage.get("defect_type", "General"),
                lat=stage.get("lat"),
                lng=stage.get("lng"))

            try:
                db.activity_add(
                    state["project_id"], state["user_id"], "raised_defect",
                    target_type="defect", target_id=notice_uid,
                    details=(sub_in.value.strip() + " · " + stage.get(
                        "defect_type", "General")),
                    user_name=(state.get("user") or {}).get("name", ""))
            except Exception:
                pass
            ui.notify(_t("notice_saved") + " " + notice_uid,
                       type="positive")
            ui.download(pdf_bytes, filename=notice_uid + ".pdf")
            stage["photos"] = []
            stage["candidates"] = None
            stage["manual"] = []
            stage["text_only"] = False
            stage["text_desc"] = ""
            stage["place"] = ""
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
        ui.label(_t("add_defect_title")).classes("h1").style(
            "margin-bottom:12px;")
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
# LOGS
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

    ui.label(_t("logs_sub")).classes("muted").style("margin-bottom:8px;")

    ui.html(
        '<div class="log-legend">'
        '<span><i class="status-bar orange"></i>OPEN — not yet overdue</span>'
        '<span><i class="status-bar red"></i>OVERDUE / LATE</span>'
        '<span><i class="status-bar green"></i>CLOSED on time</span>'
        '</div>'
    )

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

    fstate = {"filter": "all", "query": "", "defect_type": "all"}

    @ui.refreshable
    def log_list():
        all_rows = db.list_defects(state["project_id"]) or []
        rows = all_rows
        if fstate["filter"] != "all":
            rows = [r for r in rows if r.get("raise_type") == fstate["filter"]]
        if state.get("sub_filter"):
            rows = [r for r in rows
                    if (r.get("subcontractor") or "") == state["sub_filter"]]
        if fstate["defect_type"] != "all":
            rows = [r for r in rows
                    if (r.get("defect_type") or "General")
                    == fstate["defect_type"]]
        if fstate["query"]:
            q = fstate["query"]

            def _match(r):
                hay = " ".join([
                    str(r.get("uid", "")), str(r.get("zone", "")),
                    str(r.get("subcontractor", "")),
                    str(r.get("first_defect", "")),
                    str(r.get("status", "")),
                    str(r.get("engineer_name", "")),
                    str(r.get("place", "")),
                    str(r.get("defect_type", "")),
                ]).lower()
                return q in hay
            rows = [r for r in rows if _match(r)]

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
            _render_log_card(r, log_list.refresh, state)

    def _on_filter(e):
        fstate["filter"] = (e.value if e and e.value else "all")
        log_list.refresh()

    def _on_search(e):
        fstate["query"] = (e.value or "").strip().lower()
        log_list.refresh()

    def _on_dtype(e):
        fstate["defect_type"] = (e.value if e and e.value else "all")
        log_list.refresh()

    ui.select(
        {"all": _t("filter_all"),
         "qc_internal": _t("filter_qc"),
         "consultant": _t("filter_consultant")},
        value=fstate["filter"],
        label=_t("filtered_by"),
        on_change=_on_filter,
    ).style("width:100%;margin-bottom:8px;").props("dense")

    ui.select(
        {"all": _t("defect_type_all"),
         "Structural": _t("defect_type_structural"),
         "Architectural": _t("defect_type_arch"),
         "MEP": _t("defect_type_mep"),
         "Earthwork": _t("defect_type_earthwork"),
         "General": _t("defect_type_general")},
        value=fstate["defect_type"],
        label=_t("filter_type"),
        on_change=_on_dtype,
    ).style("width:100%;margin-bottom:8px;").props("dense")

    ui.input(placeholder=_t("search_placeholder"),
             on_change=_on_search).style(
        "width:100%;margin-bottom:12px;").props("dense clearable")

    log_list()


def _render_log_card(row, refresh_fn, state=None):
    status = row.get("status", "open")
    is_open = status == "open"

    created_raw = row.get("created_at") or ""
    closed_raw = row.get("closed_at") or ""
    dl_days = int(row.get("deadline_days") or 3)
    created_dt = _parse_dt(created_raw)
    closed_dt = _parse_dt(closed_raw) if closed_raw else None
    now = datetime.datetime.utcnow()

    deadline_dt = None
    if created_dt:
        deadline_dt = created_dt + datetime.timedelta(days=dl_days)

    overdue = bool(deadline_dt and is_open and now > deadline_dt)
    closed_late = bool(closed_dt and deadline_dt and closed_dt > deadline_dt)

    if is_open and overdue:
        bar = "red"
    elif is_open:
        bar = "orange"
    elif closed_late:
        bar = "red"
    else:
        bar = "green"

    created_s = created_dt.strftime("%Y-%m-%d") if created_dt else "—"
    deadline_s = deadline_dt.strftime("%Y-%m-%d") if deadline_dt else "—"
    if closed_dt:
        close_s = closed_dt.strftime("%Y-%m-%d")
    else:
        close_s = "STILL NOT"

    title = row.get("first_defect") or row.get("uid", "")
    extra = ""
    if row.get("count", 0) > 1:
        extra = "  +" + str(row["count"] - 1)

    lat = row.get("lat")
    lng = row.get("lng")

    with ui.element('div').classes("log-row") as card:
        with ui.element('div').style(
            "display:flex;justify-content:space-between;"
            "align-items:flex-start;gap:10px;"
        ):
            with ui.element('div').style(
                "flex:1;min-width:0;display:flex;gap:8px;"
            ):
                ui.html('<div class="status-bar ' + bar + '"></div>')
                with ui.element('div').style("flex:1;min-width:0;"):
                    ui.label(str(title) + extra).classes("mono-lg").style(
                        "margin-bottom:4px;")
                    meta_bits = []
                    if row.get("engineer_name"):
                        meta_bits.append(str(row["engineer_name"]))
                    if row.get("place"):
                        meta_bits.append(str(row["place"]))
                    if meta_bits:
                        ui.label(" · ".join(meta_bits)).classes("mono-sm").style(
                            "margin-bottom:4px;color:#c8c8c8;")
                    ui.label(
                        row.get("uid", "") + "  " +
                        str(row.get("zone", "")) + "  " +
                        str(row.get("subcontractor", ""))
                    ).classes("mono-sm")
                    ui.html(
                        '<div class="log-dates">'
                        'CREATED <b>' + _html_mod.escape(created_s) + '</b>'
                        '  ·  DEADLINE <b>' + str(dl_days) + 'd</b>'
                        ' (by <b>' + _html_mod.escape(deadline_s) + '</b>)'
                        '  ·  CLOSE: <b>' + _html_mod.escape(close_s) +
                        '</b></div>'
                    )
                    dt = row.get("defect_type") or ""
                    if dt:
                        ui.html('<span class="badge-seen" style="margin-top:4px;'
                                'display:inline-block;">' +
                                _html_mod.escape(str(dt)) + '</span>')

                    if lat is not None and lng is not None:
                        gmaps = ("https://www.google.com/maps/search/"
                                 "?api=1&query=" + str(lat) + "," + str(lng))
                        with ui.element('div').style(
                            "margin-top:6px;display:flex;align-items:center;"
                            "gap:6px;"
                        ):
                            ui.html(
                                '<a href="' + gmaps + '" target="_blank" '
                                'style="color:#5eead4;text-decoration:none;'
                                'font-size:11px;font-weight:600;'
                                'display:inline-flex;align-items:center;'
                                'gap:4px;">📍 View on Google Maps</a>'
                            )
                            ui.label(
                                "{:.5f}, {:.5f}".format(float(lat), float(lng))
                            ).classes("mono-sm").style(
                                "font-size:9px;color:#5a5a5a;")

            with ui.element('div').style(
                "display:flex;flex-direction:column;align-items:flex-end;gap:4px;"
            ):
                if is_open and overdue:
                    ui.html('<span class="badge-overdue">OVERDUE</span>')
                elif is_open:
                    ui.html('<span class="badge-open">OPEN</span>')
                elif closed_late:
                    ui.html('<span class="badge-overdue">LATE</span>')
                else:
                    ui.html('<span class="badge-closed">CLOSED</span>')

        def _click():
            uid = state.get("user_id") if state else None
            _show_defect_dialog(row.get("id"), refresh_fn, user_id=uid,
                                  state=state)
        card.on("click", _click)


# =====================================================================
# DEFECT DETAIL / EDIT / DELETE
# =====================================================================
def _show_defect_dialog(defect_id, on_close_cb, user_id=None, state=None):
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

            # 👇 NEW — insert this block right here 👇
            if d.get("lat") is not None and d.get("lng") is not None:
                gmaps = ("https://www.google.com/maps/search/?api=1&query=" +
                         str(d["lat"]) + "," + str(d["lng"]))
                ui.html(
                    '<a href="' + gmaps + '" target="_blank" '
                    'style="color:#5eead4;font-size:11px;font-weight:600;'
                    'text-decoration:none;margin-top:6px;'
                    'display:inline-block;">📍 ' +
                    "{:.5f}, {:.5f}".format(float(d["lat"]),
                                              float(d["lng"])) + '</a>'
                )
            # 👆 END of new block 👆

            bits = []
            if d.get("engineer_name"):
                bits.append(_t("raised_by") + ": " + str(d["engineer_name"]))
            if d.get("place"):
                bits.append(_t("at_place") + ": " + str(d["place"]))
            if bits:
                ui.label("  ·  ".join(bits)).classes("mono-sm").style(
                    "margin-top:2px;")
            if d.get("defect_type"):
                ui.label(str(d["defect_type"])).classes("mono-sm").style(
                    "margin-top:2px;color:#5eead4;font-weight:600;")
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
                with ui.element('div').style("position:relative;"):
                    ui.html('<div class="photo-tag closure">' +
                            _t("closure_photo_short") + '</div>')
                    try:
                        b64 = base64.b64encode(d["closure_photo"]).decode(
                            "ascii")
                        ui.image("data:image/jpeg;base64," + b64).style(
                            "width:100%;max-height:200px;object-fit:cover;"
                            "border-radius:3px;border:1px solid #1e1e1e;")
                    except Exception:
                        pass

            if d.get("note"):
                ui.label("> " + str(d["note"])).classes("mono-sm").style(
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

            can_edit = False
            can_delete = False
            can_close = False
            try:
                if user_id:
                    can_edit = db.can_user(user_id, d["project_id"], "edit")
                    can_close = db.can_user(user_id, d["project_id"], "close")
                    if d["status"] == "open":
                        can_delete = db.can_user(user_id, d["project_id"],
                                                  "delete_open")
                    else:
                        can_delete = db.can_user(user_id, d["project_id"],
                                                  "delete_closed")
            except Exception:
                pass

            if can_edit or can_delete:
                with ui.element('div').style(
                    "display:grid;grid-template-columns:1fr 1fr;gap:6px;"
                ):
                    if can_edit:
                        def _edit():
                            dialog.close()
                            _open_edit_defect_dialog(d, on_close_cb)
                        ui.button(_t("edit_defect"), icon="edit",
                                  on_click=_edit).classes(BTN_SOFT).style(
                            "width:100%;")
                    else:
                        ui.label("").style("min-height:1px;")

                    if can_delete:
                        def _delete():
                            dialog.close()
                            _open_delete_defect_dialog(d, on_close_cb,
                                                         user_id=user_id)
                        ui.button(_t("delete_defect"), icon="delete",
                                  on_click=_delete).classes(BTN_DANGER).style(
                            "width:100%;")
                    else:
                        ui.label("").style("min-height:1px;")

            if can_close and d["status"] == "open":
                def _open_close():
                    _open_close_defect_dialog(d, is_consultant,
                                                dialog, on_close_cb,
                                                state=state)
                ui.button(_t("mark_closed"), icon="check",
                          on_click=_open_close).classes(
                    BTN_PRIMARY).style("width:100%;")

            ui.button(_t("close"), on_click=dialog.close).props("flat").style(
                "width:100%;color:#808080;font-size:10px;")

    dialog.open()


def _open_close_defect_dialog(d, is_consultant, parent_dlg, on_close_cb,
                                state=None):
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
            closure_status.style("color:#4ade80;font-size:10px;"
                                  "margin-top:6px;")

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
            try:
                db.activity_add(
                    d["project_id"],
                    (state or {}).get("user_id") or 0,
                    "closed_defect",
                    target_type="defect", target_id=d["uid"],
                    details=("NCR " + (ncr_in.value or "").strip()
                             if (is_consultant and ncr_in) else ""),
                    user_name=((state or {}).get("user") or {}).get("name", ""))
            except Exception:
                pass
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
        "defect_type": d.get("defect_type") or "General",
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
                ui.input(_t("zone")).bind_value(meta, "zone")
            ui.select(
                {"qc_internal": _t("qc_internal"),
                 "consultant": _t("consultant_ncr")},
                label=_t("raised_as")).style("width:100%;margin-top:8px;"
                ).bind_value(meta, "raise_type")
            ui.input(_t("engineer_field")).style(
                "width:100%;margin-top:8px;").bind_value(meta,
                                                          "engineer_name")
            ui.input(_t("place_of_defect")).style(
                "width:100%;margin-top:8px;").bind_value(meta, "place")
            ui.select(
                _defect_type_options(),
                label=_t("defect_type_label")
            ).style("width:100%;margin-top:8px;").bind_value(meta,
                                                              "defect_type")

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
                                "width:100%;").bind_value(it,
                                                           "location_hint")
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
                        "location_hint":
                            (it.get("location_hint") or "").strip(),
                        "severity": it.get("severity") or "Medium",
                        "ms_violations": ms_list,
                        "code_violations": ecp_list,
                        "repair_action":
                            (it.get("repair_action") or "").strip(),
                        "zone": meta["zone"],
                        "context_mismatch":
                            it.get("context_mismatch", False),
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
                        place=meta.get("place") or None,
                        defect_type=meta.get("defect_type") or None)
                except Exception as ex:
                    import traceback
                    traceback.print_exc()
                    ui.notify("Save failed: " + str(ex), type="negative")
                    return
                try:
                    db.activity_add(
                        d["project_id"], None, "edited_defect",
                        target_type="defect", target_id=d["uid"],
                        details="", user_name="")
                except Exception:
                    pass
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
def _open_delete_defect_dialog(d, on_close_cb, user_id=None):
    is_closed = (d.get("status") or "open") != "open"
    is_adm = _is_admin_ui(user_id) if user_id else False

    if is_closed and not is_adm:
        with ui.dialog() as dlg, ui.card().style(
            "padding:20px;min-width:300px;max-width:95vw;width:400px;"
        ):
            ui.icon("lock").style("font-size:32px;color:#fbbf24;")
            ui.label("Closed notices can't be deleted").classes("h3").style(
                "margin-top:10px;margin-bottom:6px;")
            ui.label("Only an admin can delete a closed defect. "
                      "If this is an error, ask your admin to remove it.").classes(
                "mono-sm").style("line-height:1.5;margin-bottom:14px;")
            ui.button(_t("close"), on_click=dlg.close).classes(BTN_SOFT).style(
                "width:100%;")
        dlg.open()
        return

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
            try:
                db.activity_add(
                    d["project_id"], user_id, "deleted_defect",
                    target_type="defect", target_id=d["uid"],
                    details="", user_name="")
            except Exception:
                pass
            ui.notify(_t("deleted_defect"), type="positive")
            dlg.close()
            on_close_cb()

        with ui.element('div').style("display:flex;gap:8px;"):
            ui.button(_t("delete_defect"), on_click=_yes).classes(
                BTN_DANGER).style("flex:1;")
            ui.button(_t("cancel_btn"), on_click=dlg.close).classes(BTN_SOFT)

    dlg.open()


# =====================================================================
# CHANGE PASSWORD
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
# TEAM CHAT — real-time, 60s delete, role colors
# =====================================================================
def _chat_render_body(body):
    safe = _html_mod.escape(str(body or ""))
    parts = safe.split(" ")
    out = []
    for p in parts:
        if p.startswith("@") and len(p) > 1:
            out.append('<span class="mention-chip">' + p + '</span>')
        else:
            out.append(p)
    return " ".join(out)


def _parse_dt(s):
    try:
        return datetime.datetime.strptime(str(s)[:19],
                                            "%Y-%m-%d %H:%M:%S")
    except Exception:
        return None


def _build_chat(state):
    if not state.get("project_id"):
        _render_no_project(state, state["render_main"])
        return
    pid = state["project_id"]
    user = state.get("user") or {}
    my_name = (user.get("name") or user.get("email") or "me")
    my_uid = state["user_id"]

    with ui.element('div').classes("section-head"):
        ui.label(_t("chat_title")).classes("h1")

        def _refresh():
            state["render_main"]()
        ui.button(icon="refresh", on_click=_refresh).props(
            "flat round dense size=sm").style("color:#808080;")

    ui.label(_t("chat_sub")).classes("muted").style("margin-bottom:12px;")

    fstate = {"query": "", "from": "", "to": "", "reply_to": None}

    authors = db.chat_authors(pid)
    if my_name not in authors:
        authors = [my_name] + authors

    def _on_search(e):
        fstate["query"] = (e.value or "").strip().lower()
        chat_list.refresh()

    def _on_from(e):
        fstate["from"] = (e.value or "").strip()
        chat_list.refresh()

    def _on_to(e):
        fstate["to"] = (e.value or "").strip()
        chat_list.refresh()

    with ui.element('div').style(
        "display:grid;grid-template-columns:1fr 1fr;gap:6px;"
        "margin-bottom:8px;"
    ):
        ui.input(label=_t("chat_filter_from"), on_change=_on_from).props(
            "dense type=date")
        ui.input(label=_t("chat_filter_to"), on_change=_on_to).props(
            "dense type=date")

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

    _prof_cache = {}

    def _get_profile(uid):
        if not uid:
            return {}
        if uid not in _prof_cache:
            try:
                _prof_cache[uid] = db.get_user(uid) or {}
            except Exception:
                _prof_cache[uid] = {}
        return _prof_cache[uid]

    @ui.refreshable
    def chat_list():
        msgs = db.chat_list(pid, limit=300)
        if fstate["query"]:
            q = fstate["query"]

            def _m(m):
                return (q in (m.get("body") or "").lower() or
                        q in (m.get("author") or "").lower())
            msgs = [m for m in msgs if _m(m)]
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

        by_id = {m["id"]: m for m in msgs}

        for m in msgs:
            mid = m.get("id")
            author = m.get("author") or ""
            body = m.get("body") or ""
            created_raw = m.get("created_at") or ""
            created = str(created_raw)[:16]
            reply_to = m.get("reply_to_id")
            is_mine = (str(author) == str(my_name))
            cls = "chat-msg mine" if is_mine else "chat-msg"
            prof = _get_profile(m.get("user_id"))
            title = prof.get("title") or ""
            a_color = _chat_author_color(title)

            with ui.element('div').classes(cls):
                with ui.element('div').classes("chat-head"):
                    with ui.element('div').style(
                        "display:flex;align-items:center;gap:4px;"
                    ):
                        def _open_prof(uid=m.get("user_id")):
                            if uid:
                                _open_member_profile(uid)
                        name_lbl = ui.label(author).classes("chat-author")
                        name_lbl.style("color:" + a_color + ";")
                        name_lbl.on("click", _open_prof)
                        if title:
                            ui.label("· " + title).classes("chat-title-tag")
                        if is_mine:
                            ui.html('<span class="badge-you">' +
                                    _t("chat_you") + '</span>')
                    ui.label(created).classes("chat-time")

                if reply_to and reply_to in by_id:
                    parent = by_id[reply_to]
                    ui.html(
                        '<div class="chat-reply-quote">' +
                        '<b>' + _html_mod.escape(
                            str(parent.get("author", ""))) +
                        '</b>: ' +
                        _html_mod.escape(
                            str(parent.get("body", ""))[:80]) +
                        '</div>'
                    )

                ui.html('<div class="chat-body">' +
                        _chat_render_body(body) + '</div>')

                with ui.element('div').classes("chat-actions"):
                    def _reply(rid=mid):
                        fstate["reply_to"] = rid
                        render_reply_indicator()
                    ui.label(_t("chat_reply")).classes("chat-act").style(
                        "cursor:pointer;"
                    ).on("click", _reply)

                    if is_mine:
                        cd = _parse_dt(created_raw)
                        remaining = 0
                        if cd:
                            try:
                                age = (datetime.datetime.utcnow() - cd
                                       ).total_seconds()
                                remaining = max(0, 60 - age)
                            except Exception:
                                remaining = 0
                        if remaining > 0:
                            del_holder = ui.element('span')
                            with del_holder:
                                def _del(did=mid):
                                    ok, reason = db.chat_delete_secure(
                                        did, my_uid, within_seconds=60)
                                    if ok:
                                        ui.notify(_t("chat_deleted"),
                                                   type="positive")
                                        chat_list.refresh()
                                    elif reason == "too_late":
                                        ui.notify(_t("delete_too_late"),
                                                   type="warning")
                                        chat_list.refresh()
                                    elif reason == "not_owner":
                                        ui.notify(_t("delete_not_owner"),
                                                   type="warning")
                                    else:
                                        ui.notify(_t("delete_failed"),
                                                   type="negative")
                                ui.label(_t("chat_delete")).classes(
                                    "chat-act danger"
                                ).style("cursor:pointer;").on("click", _del)

                            def _hide(h=del_holder):
                                try:
                                    h.clear()
                                except Exception:
                                    pass
                            ui.timer(remaining, _hide, once=True)

    # Floating search button (fixed on right)
    with ui.element('div').classes("chat-tools"):
        def _toggle_search():
            search_box.set_visibility(not search_box.visible)
        ui.button(icon="search", on_click=_toggle_search).props(
            "round dense size=sm")

    search_box = ui.input(placeholder=_t("chat_search"),
                            on_change=_on_search).style(
        "width:100%;margin-bottom:12px;display:none;").props("dense clearable")

    chat_list()

    with ui.element('div').classes("chat-composer"):
        with ui.element('div').style("position:relative;width:100%;"):
            body_in = ui.textarea(
                placeholder=_t("chat_placeholder")
            ).style("width:100%;").props("dense autogrow")

            mention_holder = ui.element('div').style(
                "position:absolute;bottom:100%;left:0;right:0;display:none;"
            )

            def _update_mentions():
                txt = body_in.value or ""
                last = txt.split()[-1] if txt.split() else ""
                if last.startswith("@") and len(last) >= 1:
                    query = last[1:].lower()
                    matches = [a for a in authors
                               if query in (a or "").lower()][:6]
                    mention_holder.clear()
                    mention_holder.style("display:block;")
                    with mention_holder:
                        with ui.element('div').classes("mention-drop"):
                            if not matches:
                                ui.label("No matches").classes(
                                    "mention-item").style("color:#5a5a5a;")
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
                                    "click", _pick)
                else:
                    mention_holder.style("display:none;")

            body_in.on("update:model-value",
                        lambda e: _update_mentions())

        def _send():
            txt = (body_in.value or "").strip()
            if not txt:
                return
            mentions = re.findall(r"@([A-Za-z0-9_.\-]+)", txt)
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
            ui.run_javascript(
                "window.scrollTo({top: document.body.scrollHeight,"
                " behavior:'smooth'});")

        ui.button(_t("chat_send"), icon="send", on_click=_send).classes(
            BTN_PRIMARY).style("width:100%;margin-top:6px;")
        body_in.on('keydown.enter', lambda _: _send())

    state.setdefault("_chat_last_id", db.chat_max_id(pid))
    # jump to bottom on open (two attempts — one for after layout)
    ui.run_javascript(
        "window.scrollTo({top: document.body.scrollHeight,"
        " behavior:'auto'});")
    ui.timer(0.35, lambda: ui.run_javascript(
        "window.scrollTo({top: document.body.scrollHeight,"
        " behavior:'auto'});"), once=True)
    ui.timer(0.9, lambda: ui.run_javascript(
        "window.scrollTo({top: document.body.scrollHeight,"
        " behavior:'auto'});"), once=True)

    async def _poll():
        try:
            cur_max = db.chat_max_id(pid)
        except Exception:
            return
        if cur_max != state.get("_chat_last_id"):
            state["_chat_last_id"] = cur_max
            try:
                near_bottom = await ui.run_javascript(
                    "(window.innerHeight + window.scrollY) >= "
                    "(document.body.scrollHeight - 200)")
            except Exception:
                near_bottom = True
            try:
                chat_list.refresh()
            except Exception:
                pass
            if near_bottom:
                try:
                    await ui.run_javascript(
                        "window.scrollTo({top: document.body.scrollHeight,"
                        " behavior:'smooth'});")
                except Exception:
                    pass

    ui.timer(5.0, _poll)


# =====================================================================
# MS CHAT — Q&A + document check
# =====================================================================
def _build_ms_chat(state):
    if not state.get("project_id"):
        _render_no_project(state, state["render_main"])
        return
    pid = state["project_id"]
    uid = state["user_id"]
    _current_uid_holder["uid"] = uid
    user = state.get("user") or {}
    my_name = (user.get("name") or user.get("email") or "me")

    # Floating tool buttons (top-right, always visible)
    with ui.element('div').classes("chat-tools"):
        def _clear_hist():
            try:
                db.ms_chat_clear(pid, uid)
                ui.notify(_t("ms_chat_cleared"), type="positive")
                ms_list.refresh()
            except Exception as ex:
                import traceback
                traceback.print_exc()
                ui.notify("Clear failed: " + str(ex), type="negative")
        ui.button(icon="delete_sweep", on_click=_clear_hist).props(
            "round dense size=sm")

        def _refresh():
            state["render_main"]()
        ui.button(icon="refresh", on_click=_refresh).props(
            "round dense size=sm")

        def _scroll_bottom():
            ui.run_javascript(
                "window.scrollTo({top: document.body.scrollHeight,"
                " behavior:'smooth'});")
        ui.button(icon="vertical_align_bottom", on_click=_scroll_bottom).props(
            "round dense size=sm")

    with ui.element('div').classes("section-head"):
        ui.label(_t("ms_chat_title")).classes("h1")

    ui.label(_t("ms_chat_sub")).classes("muted").style("margin-bottom:12px;")

    clauses_count = len(db.get_clauses_for_element(pid))
    if clauses_count == 0:
        with ui.element('div').classes("card").style(
            "text-align:center;padding:26px 20px;margin-bottom:12px;"
        ):
            ui.icon("description").style("font-size:26px;color:#5a5a5a;")
            ui.label(_t("ms_chat_need_ms")).classes("muted").style(
                "margin-top:10px;line-height:1.6;")
        return

    ui.label(str(clauses_count) + " " + _t("clauses_count")).classes(
        "mono-sm").style("margin-bottom:10px;")

    @ui.refreshable
    def ms_list():
        msgs = db.ms_chat_list(pid, uid, limit=200)
        if not msgs:
            ui.label(_t("ms_chat_empty")).classes("mono-sm").style(
                "text-align:center;padding:32px 0;color:#5a5a5a;")
            return
        for m in msgs:
            _render_ms_message(m, on_delete=ms_list.refresh)

    ms_list()

    # Composer
    with ui.element('div').classes("chat-composer"):
        ui.label(_t("ms_chat_ask")).classes("label").style(
            "display:block;margin-bottom:4px;")
        q_in = ui.textarea(
            placeholder=_t("ms_chat_ask_placeholder")).style(
            "width:100%;").props("dense autogrow")

        async def _ask():
            q = (q_in.value or "").strip()
            if not q:
                ui.notify("Type a question first.", type="warning")
                return
            try:
                btn_ask.props("loading")
                btn_ask.set_text(_t("analyzing"))
            except Exception:
                pass
            try:
                result = await msc.ask_ms_question(pid, q, call_gemini_json)
            except Exception as ex:
                import traceback
                traceback.print_exc()
                try:
                    btn_ask.props(remove="loading")
                    btn_ask.set_text(_t("ms_chat_send"))
                except Exception:
                    pass
                ui.notify("Ask error: " + str(ex), type="negative")
                return
            try:
                btn_ask.props(remove="loading")
                btn_ask.set_text(_t("ms_chat_send"))
            except Exception:
                pass
            if not result:
                ui.notify("Empty result.", type="negative")
                return
            if result.get("error"):
                ui.notify(_t("ms_chat_failed") + str(result["error"]),
                           type="negative")
                return
            answer = result.get("answer") or ""
            if not answer.strip():
                ui.notify("Empty answer.", type="warning")
                return
            try:
                db.ms_chat_add(pid, uid, my_name, "question", q,
                                {"answer": answer})
            except Exception as ex:
                import traceback
                traceback.print_exc()
                ui.notify("Save failed: " + str(ex), type="negative")
                return
            q_in.value = ""
            try:
                ms_list.refresh()
            except Exception:
                pass
            ui.run_javascript(
                "window.scrollTo({top: document.body.scrollHeight,"
                " behavior:'smooth'});")

        btn_ask = ui.button(_t("ms_chat_send"), icon="send", on_click=_ask)
        btn_ask.classes(BTN_PRIMARY).style("width:100%;margin-top:6px;")
        q_in.on('keydown.enter', lambda _: _ask())

        with ui.element('div').classes("or-divider"):
            ui.label(_t("or_divider"))

        ui.label(_t("ms_chat_check_hint")).classes("mono-sm").style(
            "display:block;margin-bottom:6px;line-height:1.5;")

        doc_status = ui.label("").classes("mono-sm").style(
            "margin-top:6px;display:block;min-height:14px;")

        async def _handle_doc(e):
            try:
                data = await e.file.read()
            except Exception as ex:
                ui.notify(_t("upload_failed") + str(ex), type="negative")
                return
            if not data:
                ui.notify(_t("empty_file"), type="warning")
                return
            name = (e.file.name or "").lower()
            if name.endswith(".pdf"):
                mime = "application/pdf"
            elif name.endswith(".png"):
                mime = "image/png"
            else:
                mime = "image/jpeg"

            doc_status.set_text(_t("ms_chat_reading"))
            doc_status.style("color:#fbbf24;font-size:10px;margin-top:6px;"
                              "display:block;min-height:14px;")
            try:
                result = await msc.check_document_against_ms(
                    file_bytes=data, mime_type=mime, project_id=pid,
                    ocr_fn=_ocr_handwriting,
                    call_gemini_json_fn=call_gemini_json)
            except Exception as ex:
                doc_status.set_text(_t("ms_chat_failed") + str(ex))
                doc_status.style("color:#f87171;font-size:10px;"
                                  "margin-top:6px;display:block;"
                                  "min-height:14px;")
                return
            if result.get("error"):
                doc_status.set_text(_t("ms_chat_failed") +
                                     str(result["error"]))
                doc_status.style("color:#f87171;font-size:10px;"
                                  "margin-top:6px;display:block;"
                                  "min-height:14px;")
                return
            doc_status.set_text("")
            resp = {k: result.get(k) for k in
                    ("doc_type", "extracted", "checks", "overall",
                     "summary", "ocr_text")}
            db.ms_chat_add(pid, uid, my_name, "check",
                            _t("ms_chat_check_btn"), resp)
            ms_list.refresh()
            ui.run_javascript(
                "window.scrollTo({top: document.body.scrollHeight,"
                " behavior:'smooth'});")

        ui.upload(on_upload=_handle_doc, auto_upload=True).style(
            "width:100%;").props(
            "flat bordered accept=image/*,.pdf label='" +
            _t("ms_chat_check_btn") + "'")
        doc_status

    # scroll to bottom on open
    ui.run_javascript(
        "window.scrollTo({top: document.body.scrollHeight,"
        " behavior:'auto'});")
    ui.timer(0.35, lambda: ui.run_javascript(
        "window.scrollTo({top: document.body.scrollHeight,"
        " behavior:'auto'});"), once=True)
    ui.timer(0.9, lambda: ui.run_javascript(
        "window.scrollTo({top: document.body.scrollHeight,"
        " behavior:'auto'});"), once=True)

    state.setdefault("_ms_chat_last_id", db.ms_chat_max_id(pid, uid))

    async def _ms_poll():
        try:
            cur_max = db.ms_chat_max_id(pid, uid)
        except Exception:
            return
        if cur_max != state.get("_ms_chat_last_id"):
            state["_ms_chat_last_id"] = cur_max
            try:
                ms_list.refresh()
            except Exception:
                pass

    ui.timer(5.0, _ms_poll)

_current_uid_holder = {"uid": None}
def _render_ms_message(m, on_delete=None):
    kind = (m.get("kind") or "question").lower()
    cls = "ms-msg kind-question" if kind == "question" else "ms-msg kind-check"
    author = m.get("author") or "?"
    created = str(m.get("created_at") or "")[:16]
    body = m.get("body") or ""
    resp = m.get("response") or {}
    mid = m.get("id")

    with ui.element('div').classes(cls):
        with ui.element('div').style(
            "display:flex;justify-content:space-between;"
            "align-items:center;gap:8px;margin-bottom:6px;"
        ):
            with ui.element('div').style(
                "display:flex;align-items:center;gap:6px;"
            ):
                ui.html('<span class="badge-seen" style="color:#b8b8b8;">' +
                        _html_mod.escape(
                            _t("ms_chat_kind_question") if kind == "question"
                            else _t("ms_chat_kind_check")) + '</span>')
                ui.label(author).style(
                    "font-size:11px;color:#b8b8b8;font-weight:600;")
            with ui.element('div').style(
                "display:flex;align-items:center;gap:6px;"
            ):
                ui.label(created).classes("chat-time")

                def _del(did=mid):
                    db.ms_chat_delete(did, _current_uid_holder.get("uid"))
                    ui.notify("Deleted.", type="positive")
                    if on_delete:
                        on_delete()
                if mid:
                    ui.button(icon="delete", on_click=_del).props(
                        "flat round dense size=xs").style(
                        "color:#808080;").tooltip("Delete")

        if kind == "question":
            with ui.element('div').style(
                "background:#161616;border:1px solid #1e1e1e;"
                "border-radius:3px;padding:8px 10px;margin-bottom:8px;"
            ):
                ui.label("Q: " + str(body)).classes("ms-q").style(
                    "margin-bottom:0;")
            answer = str(resp.get("answer") or "")
            ui.label(_t("ms_chat_answer_from")).classes("label").style(
                "display:block;margin-bottom:4px;")
            ui.label(answer).classes("ms-a")
        else:
            ui.label(_t("ms_chat_check_btn")).classes("label").style(
                "display:block;margin-bottom:6px;")
            doc_type = resp.get("doc_type") or ""
            if doc_type:
                ui.label(_t("ms_chat_doc_type") + ": " + str(doc_type)).style(
                    "font-size:12px;color:#e8e8e8;font-weight:600;"
                    "margin-bottom:8px;")
            extracted = resp.get("extracted") or {}
            if extracted:
                ui.label(_t("ms_chat_extracted")).classes("label").style(
                    "display:block;margin-bottom:4px;")
                with ui.element('div').classes("ms-kv"):
                    for k, v in extracted.items():
                        ui.html("<div><b>" + _html_mod.escape(str(k)) +
                                ":</b> " + _html_mod.escape(str(v)) +
                                "</div>")
            checks = resp.get("checks") or []
            if checks:
                ui.label(_t("ms_chat_checks")).classes("label").style(
                    "display:block;margin-top:10px;margin-bottom:4px;")
                for c in checks:
                    v = (c.get("verdict") or "").lower()
                    vcls = ("verdict-ok" if v == "ok" else
                            "verdict-warn" if v == "warn" else
                            "verdict-fail")
                    field = str(c.get("field") or "")
                    val = str(c.get("value") or "")
                    req = str(c.get("ms_requirement") or "")
                    cid = str(c.get("clause_id") or "")
                    note = str(c.get("note") or "")
                    with ui.element('div').classes("ms-check"):
                        ui.html("<div class='field'>" +
                                _html_mod.escape(field) + "</div>")
                        ui.html("<div class='val'>" +
                                _html_mod.escape(val) + "</div>")
                        extra = (v or "").upper()
                        ui.html("<div class='" + vcls + "'>" + extra +
                                "</div>")
                        line2 = []
                        if req:
                            line2.append("MS: " + req)
                        if cid:
                            line2.append("[" + _html_mod.escape("S" + cid) +
                                          "]")
                        if note:
                            line2.append(note)
                        if line2:
                            ui.html("<div class='note'>" +
                                    _html_mod.escape(" · ".join(line2)) +
                                    "</div>")
            overall = (resp.get("overall") or "").lower()
            if overall:
                ocls = ("overall-ok" if overall == "compliant" else
                        "overall-warn" if overall == "conditional" else
                        "overall-fail")
                olabel = ("ms_chat_compliant" if overall == "compliant" else
                          "ms_chat_conditional" if overall == "conditional"
                          else "ms_chat_non_compliant")
                ui.element('div').style("height:10px;")
                with ui.element('div').style(
                    "display:flex;justify-content:space-between;"
                    "align-items:center;padding-top:6px;"
                    "border-top:1px solid #1e1e1e;margin-top:6px;"
                ):
                    ui.label(_t("ms_chat_overall")).classes("label")
                    ui.html("<div class='" + ocls + "'>" +
                            _html_mod.escape(_t(olabel)) + "</div>")
            summary = resp.get("summary") or ""
            if summary:
                ui.label(str(summary)).classes("mono-sm").style(
                    "margin-top:8px;line-height:1.5;")


def _open_member_profile(user_id):
    u = db.get_user(user_id)
    if not u:
        return
    with ui.dialog() as dlg, ui.card().style(
        "padding:22px;min-width:260px;max-width:95vw;width:340px;"
    ):
        with ui.element('div').style(
            "display:flex;flex-direction:column;align-items:center;gap:8px;"
        ):
            av = '<div class="avatar-big">'
            if u.get("photo_bytes"):
                try:
                    b64 = base64.b64encode(u["photo_bytes"]).decode("ascii")
                    av += '<img src="data:image/jpeg;base64,' + b64 + '"/>'
                except Exception:
                    av += _html_mod.escape(_initial(u.get("name") or ""))
            else:
                av += _html_mod.escape(_initial(u.get("name") or ""))
            av += '</div>'
            ui.html(av)
            ui.label(u.get("name") or "—").style(
                "font-size:15px;font-weight:700;color:#e8e8e8;")
            if u.get("title"):
                color = _chat_author_color(u["title"])
                ui.label(u["title"]).style(
                    "font-size:11px;color:" + color + ";font-weight:600;"
                    "letter-spacing:0.05em;"
                )
            if u.get("email"):
                ui.label(u["email"]).classes("mono-sm").style(
                    "margin-top:2px;")
        ui.element('div').style("height:14px;")
        ui.button(_t("close"), on_click=dlg.close).classes(BTN_SOFT).style(
            "width:100%;"
        )
    dlg.open()
