"""
ui/defect_page.py — Full file.
- Team multi-user: invite by email, all see same project.
- MS Chat: Q&A over uploaded Method Statements + document compliance check.
- OCR for handwritten notes in the "no photo" dialog.
- Real-time chat with 60s delete window, role colors, mentions.
- Defect-type filter, engineer name + place under every log title.
- Interactive ECharts dashboard.
- Feature 5: per-defect comment thread.
- Feature 6: per-defect watchlist.
- Feature 7: bulk actions in Defect Logs.
- Feature 10: custom report templates.
- Gemini-style MS Chat UI.
- Fixed: app-topbar sticky (header + tabs together).
- Fixed: ms_list no longer duplicates on refresh.
- Feature: MS Reader tab (browse, chapters, in-MS search).
- Feature: TDS TOOLS tab (TDS → Method Statement + ITP).
- Feature: INSPECTIONS tab (daily QC plans, 3-state status, carry-over).
"""
import io
import re
import json
import asyncio
import base64
import datetime
import html as _html_mod
from nicegui import ui, app

from services import defect_db as db
from services import defect_service as svc
from services import ms_chat_service as msc
from services import tds_service as tds
from services import inspection_service as ins
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
        "ms_chat_thinking": "Thinking...",
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
        "ms_chat_thinking": "جاري التفكير...",
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
# OCR
# =====================================================================
_OCR_PROMPT = (
    "You are a precise OCR engine for handwritten and printed documents. "
    "Read every character in this document exactly as it appears."
    "\n\nCRITICAL RULES:"
    "\n1. Detect the language automatically (Arabic, English, or mixed)."
    "\n2. If the text is Arabic, transcribe it in correct right-to-left "
    "reading order, word by word, preserving every letter including "
    "hamza forms (أ إ آ ء ئ ؤ), taa marbuta (ة), taa (ت), and any "
    "diacritics. Do NOT drop, merge, or reorder Arabic letters."
    "\n3. Do NOT translate. Do NOT summarize. Do NOT add commentary, "
    "headings, bullet points, or markdown."
    "\n4. Preserve line breaks exactly as they appear on the page."
    "\n5. For mixed Arabic + English lines, keep each word in its "
    "original language and script."
    "\n6. If a word is unclear, transcribe your best guess using context."
    "\n7. Return ONLY the raw extracted text. No quotes, no labels, "
    "no explanations."
    "\n8. If the image contains no readable text, return an empty string."
)


def _preprocess_for_ocr(file_bytes, mime_type):
    mime = (mime_type or "image/jpeg").lower()
    if mime == "application/pdf" or not mime.startswith("image/"):
        return file_bytes, mime
    try:
        from PIL import Image, ImageOps, ImageFilter
    except Exception as e:
        print("[ocr] PIL unavailable: " + repr(e))
        return file_bytes, mime
    try:
        import io as _io
        img = Image.open(_io.BytesIO(file_bytes))
        img = ImageOps.exif_transpose(img)
        if img.mode not in ("L", "RGB"):
            img = img.convert("RGB")
        w, h = img.size
        longest = max(w, h)
        if longest < 1400:
            scale = 1400.0 / float(longest)
            img = img.resize((int(w * scale), int(h * scale)),
                              Image.LANCZOS)
        elif longest > 2400:
            scale = 2400.0 / float(longest)
            img = img.resize((int(w * scale), int(h * scale)),
                              Image.LANCZOS)
        img = img.filter(ImageFilter.UnsharpMask(radius=1.4,
                                                  percent=140,
                                                  threshold=3))
        buf = _io.BytesIO()
        img.save(buf, format="JPEG", quality=92, optimize=True)
        return buf.getvalue(), "image/jpeg"
    except Exception as e:
        print("[ocr] preprocess failed: " + repr(e))
        return file_bytes, mime


async def _ocr_handwriting(file_bytes, mime_type):
    if not file_bytes:
        return None, "Empty file."
    try:
        from google.genai import types
    except Exception as e:
        return None, "google-genai not available: " + repr(e)
    payload, mime = _preprocess_for_ocr(file_bytes, mime_type)
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
    if len(text) >= 2 and text[0] == text[-1] and text[0] in ('"', "'", "`"):
        text = text[1:-1].strip()
    while "\n\n\n" in text:
        text = text.replace("\n\n\n", "\n\n")
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
    --gem-bg:#1e1f20; --gem-user:#333537; --gem-input:#2a2b2d;
    --gem-text:#e3e3e3; --gem-muted:#9aa0a6;
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

  /* ---------- Sticky top bar (header + tabs together) ---------- */
  .app-topbar {
    position: sticky;
    top: 0;
    z-index: 900;
    width: 100%;
    background: rgba(11,11,11,0.94);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    box-sizing: border-box;
  }
  .app-header {
    position: static;
    background: transparent;
    border-bottom: 1px solid var(--border);
    padding: 8px 14px;
    display: flex; align-items: center; justify-content: space-between;
    box-sizing: border-box;
    width: 100%;
  }
  .app-header .brand { font-weight: 700; font-size: 12px;
                       color: var(--text); }
  .app-header .brand::before {
    content: '\\25CF '; color: var(--accent); font-size: 9px;
    vertical-align: middle; margin-right: 4px;
  }
  .top-tabs {
    position: static;
    display: flex; align-items: center; gap: 4px; padding: 8px 14px;
    background: transparent;
    border-bottom: 1px solid var(--border);
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
  .badge-comment { color: var(--accent);
                   border: 1px solid rgba(94,234,212,0.3); }
  .badge-watch { color: var(--warn);
                 border: 1px solid rgba(251,191,36,0.35); }
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
  .chat-tools {
    position: fixed; top: 118px; right: 14px; z-index: 500;
    display: flex; flex-direction: column; gap: 6px;
  }
  .chat-tools .q-btn {
    background: rgba(11,11,11,0.94) !important;
    color: #5eead4 !important;
    border: 1px solid #262626 !important;
    box-shadow: 0 4px 10px rgba(0,0,0,0.4) !important;
    min-width: 32px !important; min-height: 32px !important;
    padding: 0 !important;
  }
  .ocr-box { background: var(--surface-2); border: 1px dashed var(--border-2);
             border-radius: 4px; padding: 10px; margin-top: 6px; }
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
  .comment-row { background: #101010; border: 1px solid #1e1e1e;
                 border-radius: 3px; padding: 8px 10px;
                 margin-bottom: 4px; }
  .comment-author { font-size: 10px; color: var(--accent);
                    font-weight: 600; }
  .comment-time { font-size: 9px; color: var(--muted-2);
                  font-variant-numeric: tabular-nums; }
  .comment-body { font-size: 11px; color: var(--text); margin-top: 4px;
                  line-height: 1.5; white-space: pre-wrap;
                  word-break: break-word; }
  .bulk-bar {
    position: sticky; bottom: 0; z-index: 600;
    background: rgba(11,11,11,0.96);
    border-top: 1px solid var(--accent);
    padding: 10px 12px; margin-top: 12px;
    display: flex; flex-wrap: wrap; gap: 6px;
    border-radius: 4px;
  }
  .bulk-bar .q-btn { min-height: 30px !important; font-size: 10px !important; }

  /* ============================================================
     Gemini-style MS Chat
     ============================================================ */
  .gem-wrap {
    display: flex; flex-direction: column;
    width: 100%;
    padding: 4px 0 280px 0;
    box-sizing: border-box;
    gap: 18px;
  }
  .gem-row { display: flex; width: 100%; }
  .gem-row.user { justify-content: flex-end; }
  .gem-row.ai { justify-content: flex-start; }
  .gem-user {
    background: var(--gem-user);
    color: var(--gem-text);
    border-radius: 20px;
    padding: 10px 15px;
    max-width: 82%;
    font-size: 14.5px;
    line-height: 1.55;
    white-space: pre-wrap;
    word-break: break-word;
    font-family: 'JetBrains Mono','Amiri',monospace;
  }
  .gem-ai {
    max-width: 100%;
    width: 100%;
    padding: 2px 4px 2px 0;
    font-size: 14.5px;
    line-height: 1.68;
    color: var(--gem-text);
    white-space: pre-wrap;
    word-break: break-word;
    font-family: 'JetBrains Mono','Amiri',monospace;
  }
  .gem-ai-label {
    font-size: 9px; letter-spacing: 0.16em;
    color: #6a6a6a; font-weight: 700;
    text-transform: uppercase;
    margin-bottom: 8px;
  }
  .gem-msg-meta {
    font-size: 10px; color: #808080;
    margin-top: 4px;
    display: flex; align-items: center; gap: 8px;
  }
  .gem-del {
    background: transparent; border: none;
    color: #4a4a4a; cursor: pointer; padding: 0 4px;
    font-size: 12px; line-height: 1;
  }
  .gem-del:hover { color: #f87171; }
  .gem-thinking {
    display: inline-flex; gap: 5px; align-items: center;
    color: var(--gem-muted);
    font-size: 13px;
  }
  .gem-dot {
    width: 5px; height: 5px; border-radius: 50%;
    background: var(--accent);
    animation: gemBounce 1.2s infinite ease-in-out both;
  }
  .gem-dot:nth-child(2) { animation-delay: 0.15s; }
  .gem-dot:nth-child(3) { animation-delay: 0.3s; }
  @keyframes gemBounce {
    0%, 80%, 100% { opacity: 0.3; transform: translateY(0); }
    40% { opacity: 1; transform: translateY(-3px); }
  }
  .gem-composer {
    position: fixed;
    left: 0; right: 0; bottom: 0;
    padding: 16px 12px 16px;
    background: linear-gradient(180deg, rgba(11,11,11,0) 0%,
                                rgba(11,11,11,0.95) 30%,
                                #0b0b0b 100%);
    z-index: 400;
    pointer-events: none;
  }
  .gem-composer-inner {
    max-width: 720px;
    margin: 0 auto;
    pointer-events: auto;
    position: relative;
  }
  .gem-pill {
    display: flex;
    align-items: flex-end;
    gap: 4px;
    background: var(--gem-input);
    border: 1px solid #35363a;
    border-radius: 26px;
    padding: 6px 6px 6px 6px;
    min-height: 50px;
    transition: border-color 0.15s, background 0.15s;
  }
  .gem-pill:focus-within {
    border-color: #4a4b4f;
    background: #303134;
  }
  .gem-pill .q-field { flex: 1; min-width: 0; }
  .gem-pill .q-field--outlined .q-field__control {
    background: transparent !important;
    border: none !important;
    min-height: 36px !important;
    padding: 0 !important;
  }
  .gem-pill .q-field--outlined .q-field__control:before,
  .gem-pill .q-field--outlined .q-field__control:after {
    border: none !important;
  }
  .gem-pill .q-field__native,
  .gem-pill .q-field__input,
  .gem-pill textarea {
    color: var(--gem-text) !important;
    font-family: 'JetBrains Mono','Amiri',monospace !important;
    font-size: 14.5px !important;
    padding: 8px 6px !important;
    line-height: 1.5 !important;
  }
  .gem-icon-btn {
    width: 38px; height: 38px;
    border-radius: 50%;
    background: transparent;
    border: none;
    color: #c5c7cb;
    display: flex; align-items: center; justify-content: center;
    cursor: pointer;
    flex-shrink: 0;
    transition: background 0.12s, color 0.12s;
  }
  .gem-icon-btn:hover { background: #3a3b3d; color: #ffffff; }
  .gem-icon-btn .q-icon { font-size: 22px !important; }
  .gem-icon-btn.send {
    background: #35363a;
    color: #6a6d72;
    cursor: default;
    transition: background 0.15s, color 0.15s;
  }
  .gem-icon-btn.send.active {
    background: var(--accent);
    color: #0b0b0b;
    cursor: pointer;
  }
  .gem-icon-btn.send.active:hover { background: #4dd4bf; }
  .gem-icon-btn.plus { color: #e8e8e8; }
  .gem-hint {
    text-align: center;
    font-size: 10px;
    color: #5a5a5a;
    margin-top: 8px;
    letter-spacing: 0.02em;
  }
  .gem-empty {
    display: flex; flex-direction: column;
    align-items: flex-start; justify-content: center;
    padding: 40px 4px 20px;
    min-height: 40vh;
  }
  .gem-empty-title {
    font-size: 22px; font-weight: 700;
    color: var(--gem-text);
    margin-bottom: 10px;
    letter-spacing: -0.01em;
    background: linear-gradient(90deg, #5eead4, #60a5fa, #a78bfa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  .gem-empty-sub {
    font-size: 13px; color: #9aa0a6;
    margin-bottom: 18px; line-height: 1.6;
  }
  .gem-empty-chips {
    display: flex; flex-wrap: wrap; gap: 8px;
  }
  .gem-chip {
    background: #1f2022;
    border: 1px solid #2a2b2d;
    color: #e3e3e3;
    border-radius: 18px;
    padding: 8px 14px;
    font-size: 12.5px;
    cursor: pointer;
    transition: background 0.12s;
  }
  .gem-chip:hover { background: #2a2b2d; }
  .gem-check-card {
    background: #161718;
    border: 1px solid #232426;
    border-radius: 14px;
    padding: 14px 16px;
    margin-top: 6px;
    max-width: 100%;
  }
  .gem-check-title {
    font-size: 10px; letter-spacing: 0.14em;
    color: #6a6a6a; font-weight: 700;
    text-transform: uppercase;
    margin-bottom: 10px;
  }
  .gem-kv-row {
    display: flex; gap: 8px;
    font-size: 12px; color: #b8b8b8;
    padding: 4px 0;
    border-bottom: 1px solid #1e1f21;
  }
  .gem-kv-row:last-child { border-bottom: none; }
  .gem-kv-row b { color: #e3e3e3; min-width: 100px; }
  .gem-verdict {
    display: inline-block;
    font-size: 10px; font-weight: 800;
    letter-spacing: 0.14em;
    padding: 4px 10px;
    border-radius: 6px;
    text-transform: uppercase;
  }
  .gem-verdict.ok { background: rgba(74,222,128,0.14); color: #4ade80; }
  .gem-verdict.warn { background: rgba(251,191,36,0.14); color: #fbbf24; }
  .gem-verdict.fail { background: rgba(248,113,113,0.14); color: #f87171; }
  .gem-check-row {
    display: grid;
    grid-template-columns: 1fr auto;
    gap: 8px;
    padding: 8px 0;
    border-bottom: 1px solid #1e1f21;
    align-items: flex-start;
  }
  .gem-check-row:last-child { border-bottom: none; }
  .gem-check-field { font-size: 12px; color: #c8c8c8; }
  .gem-check-val { font-size: 12px; color: #e3e3e3; font-weight: 600; }
  .gem-check-note {
    font-size: 10.5px; color: #808080;
    margin-top: 4px; line-height: 1.5;
    grid-column: 1 / -1;
  }
  .cite-pill {
    display: inline-block;
    background: rgba(94,234,212,0.12);
    color: #5eead4;
    border: 1px solid rgba(94,234,212,0.35);
    border-radius: 8px;
    padding: 0 6px;
    margin: 0 2px;
    font-size: 11.5px;
    font-weight: 700;
    cursor: pointer;
    line-height: 1.5;
    transition: background 0.12s;
  }
  .cite-pill:hover { background: rgba(94,234,212,0.22); }
  .cite-pill.miss {
    background: rgba(128,128,128,0.08);
    color: #808080;
    border-color: #2a2a2a;
    cursor: default;
  }
  .ms-reader-doc {
    background: #101010; border: 1px solid #1e1e1e;
    border-radius: 4px; padding: 10px 12px; margin-bottom: 6px;
    cursor: pointer;
  }
  .ms-reader-doc:hover { background: #161616; }
  .ms-reader-clause {
    background: #101010; border: 1px solid #1e1e1e;
    border-radius: 3px; padding: 8px 10px; margin-bottom: 4px;
  }
  .ms-reader-clause .cid {
    color: #5eead4; font-weight: 700; font-size: 11px;
  }
  .ms-reader-clause .ctitle {
    color: #e8e8e8; font-weight: 600; font-size: 12px;
    margin-left: 6px;
  }
  .ms-reader-clause .ctext {
    color: #b8b8b8; font-size: 11px; margin-top: 4px;
    line-height: 1.55; white-space: pre-wrap;
  }

  /* ============================================================
     MS READER TAB
     ============================================================ */
  .reader-content { width: 100%; padding: 0 !important;
                    max-width: none !important; margin: 0 !important; }
  .reader-wrap { display: flex; width: 100%; min-height: 70vh;
                 position: relative; }
  .reader-menu {
    width: 270px; flex-shrink: 0;
    background: #0e0e0e; border-right: 1px solid var(--border);
    padding: 12px 10px; box-sizing: border-box; overflow-y: auto;
    max-height: calc(100vh - 110px);
  }
  .reader-main { flex: 1; min-width: 0; position: relative; }
  .reader-topbar {
    display: flex; align-items: center; gap: 8px;
    padding: 10px 12px; border-bottom: 1px solid var(--border);
    position: sticky; top: 0; z-index: 5;
    background: rgba(11,11,11,0.94);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
  }
  .reader-menu-btn {
    background: transparent; border: 1px solid var(--border-2);
    color: var(--text); padding: 4px 8px; border-radius: 3px;
    cursor: pointer; display: none; flex-shrink: 0;
  }
  .reader-title {
    font-size: 12px; font-weight: 700; color: #e8e8e8;
    flex: 1; min-width: 0; overflow: hidden;
    text-overflow: ellipsis; white-space: nowrap;
  }
  .reader-readall {
    font-size: 10px; font-weight: 700; color: var(--accent);
    border: 1px solid rgba(94,234,212,0.4); border-radius: 3px;
    padding: 4px 8px; cursor: pointer; background: transparent;
    white-space: nowrap; flex-shrink: 0;
  }
  .reader-readall:hover { background: rgba(94,234,212,0.1); }
  .reader-ms-item {
    display: block; padding: 8px 10px; border-radius: 3px;
    background: transparent; border: 1px solid transparent;
    color: var(--text); cursor: pointer;
    margin-bottom: 4px; width: 100%; box-sizing: border-box;
  }
  .reader-ms-item:hover { background: var(--surface-2); }
  .reader-ms-item.active {
    background: var(--surface-2);
    border-color: rgba(94,234,212,0.5);
  }
  .reader-chapters { margin: 4px 0 12px 8px; }
  .reader-chapter-item {
    display: block; padding: 5px 8px; font-size: 10.5px;
    color: #b8b8b8; cursor: pointer; border-radius: 3px;
    border: none; background: transparent; width: 100%;
    box-sizing: border-box; text-align: left; line-height: 1.4;
  }
  .reader-chapter-item:hover { background: #161616; color: var(--accent); }
  .reader-chapter-item.active {
    color: var(--accent); background: rgba(94,234,212,0.08);
    font-weight: 700;
  }
  .reader-search {
    padding: 8px 12px; border-bottom: 1px solid var(--border);
    background: #0b0b0b;
  }
  .reader-body {
    padding: 22px 26px 140px 26px;
    font-family: 'JetBrains Mono','Amiri',monospace;
    color: #d8d8d8;
    word-break: break-word;
    max-width: 900px; margin: 0 auto;
    scroll-margin-top: 150px;
  }
  .reader-body-outer { scroll-margin-top: 150px; }
  .reader-body .reader-h1 {
    font-size: 17px; font-weight: 700; color: var(--accent);
    margin: 30px 0 14px 0; padding: 0 0 8px 0;
    border-bottom: 1px solid rgba(94,234,212,0.28);
    letter-spacing: -0.01em; line-height: 1.3;
    scroll-margin-top: 160px;
  }
  .reader-chapter-item {
    text-decoration: none;
  }
  .reader-readall {
    text-decoration: none;
    display: inline-block;
  }
  .reader-body .reader-h1:first-child { margin-top: 4px; }
  .reader-body .reader-h2 {
    font-size: 14px; font-weight: 700; color: #5eead4;
    margin: 22px 0 10px 0; line-height: 1.35;
    letter-spacing: -0.005em; opacity: 0.94;
  }
  .reader-body .reader-h3 {
    font-size: 13px; font-weight: 700; color: #9be8dc;
    margin: 16px 0 8px 0; line-height: 1.4;
  }
  .reader-body .reader-para {
    margin: 0 0 12px 0; font-size: 13.5px;
    line-height: 1.8; color: #d0d0d0;
  }
  .reader-body .reader-gap { height: 6px; }
  .reader-body .reader-hl {
    background: rgba(94,234,212,0.4); color: #0b0b0b;
    border-radius: 2px; padding: 1px 3px; font-weight: 700;
  }
  .reader-empty {
    text-align: center; padding: 60px 20px; color: #808080;
  }
  @media (max-width: 767px) {
    .reader-menu-btn { display: inline-flex; }
    .reader-menu {
      position: fixed; top: 0; left: 0; bottom: 0;
      width: 82vw; max-width: 320px; z-index: 1000;
      transform: translateX(-100%);
      transition: transform 0.2s ease;
      box-shadow: 4px 0 20px rgba(0,0,0,0.6);
      max-height: 100vh; padding-top: 20px;
    }
    .reader-wrap.menu-open .reader-menu {
      transform: translateX(0);
    }
    .reader-wrap.menu-open::after {
      content: ''; position: fixed; inset: 0;
      background: rgba(0,0,0,0.55); z-index: 999;
    }
    .reader-body { padding: 16px 16px 120px 16px; }
    .reader-body .reader-h1 { font-size: 15px; }
    .reader-body .reader-h2 { font-size: 13px; }
  }
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
_DASH_TTL = 60
_current_uid_holder = {"uid": None}


def _dash_data(project_id):
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

    if user and db.is_suspended(user_id):
        with ui.element('div').classes("card").style(
            "max-width:420px;margin:80px auto;text-align:center;"
            "padding:36px 24px;"
        ):
            ui.icon("block").style("font-size:36px;color:#f87171;")
            ui.label("Account suspended").classes("h1").style(
                "margin-top:14px;margin-bottom:8px;")
            ui.label(
                "Your account has been suspended by an administrator. "
                "Contact your administrator to restore access."
            ).classes("muted").style("line-height:1.6;")

            def _logout():
                try:
                    app.storage.user.clear()
                except Exception:
                    pass
                ui.navigate.to("/logout")

            ui.button("Log out", icon="logout", on_click=_logout).classes(
                BTN_PRIMARY).style("width:100%;margin-top:20px;")
        return

    state = {
        "user_id": user_id, "user": user,
        "project_id": app.storage.user.get("project_id"),
        "project": None, "tab": {"value": "chat"},
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

    # ---- Sticky topbar (header + tabs) ----
    with ui.element('div').classes("app-topbar"):
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
                          on_click=_open_my_prof).props(
                    "flat round dense").style(
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
        tab = state["tab"]["value"]
        if tab == "reader":
            content.classes(remove="main-content")
            content.classes(add="reader-content")
        else:
            content.classes(remove="reader-content")
            content.classes(add="main-content")
        with content:
            if not state.get("project_id"):
                _render_no_project(state, _render_tab)
                return
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
            elif tab == "reader":
                _build_ms_reader(state)
            elif tab == "tds":
                _build_tds_tools(state)
            elif tab == "inspections":
                _build_inspections(state)
            elif tab == "admin":
                _build_admin(state)
            else:
                _build_dashboard(state)

    def _build_nav():
        nav_holder.clear()
        with nav_holder:
            tabs = [
                ("chat", _t("chat")),
                ("new", _t("new_defect")), ("logs", _t("logs")),
                ("subs", _t("subs")),
                ("mschat", _t("ms_chat")),
                ("reader", "MS READER"),
                ("tds", "TDS TOOLS"),
                ("inspections", "INSPECTIONS"),
                ("dashboard", _t("dashboard")),
            ]
            if _is_admin_ui(state.get("user_id")):
                tabs.append(("admin", "ADMIN"))
            for key, label in tabs:
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
                        'areaStyle': {'color': 'rgba(94,234,212,0.12)'},
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
                'tooltip': {'trigger': 'item', 'formatter': 'UID: {c}'},
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

        try:
            from services import billing_db as _billing
            _own = state.get("user_id")
            if _own:
                _s = _billing.billing_seats_summary(_own)
                _lim = _s.get("limit")
                _lim_s = "unlimited" if _lim is None else str(_lim)
                _col = "#4ade80"
                if _lim is not None:
                    if _s["used"] >= _lim:
                        _col = "#f87171"
                    elif _s["used"] >= _lim - 1:
                        _col = "#fbbf24"
                ui.html(
                    '<div style="font-size:10px;color:#b8b8b8;'
                    'background:#101010;border:1px solid #1e1e1e;'
                    'border-radius:3px;padding:6px 10px;'
                    'margin-bottom:12px;">SEATS '
                    '<b style="color:' + _col + ';">' +
                    str(_s["used"]) + ' / ' + _lim_s +
                    '</b> on <b style="color:#e8e8e8;">' +
                    _html_mod.escape(str(_s.get("label") or "")) +
                    '</b></div>'
                )
        except Exception:
            pass

        with ui.tabs().style("width:100%;margin-bottom:14px;") as tabs:
            tab_email = ui.tab("Add by email")
            tab_link = ui.tab("Share invite link")

        with ui.tab_panels(tabs, value=tab_email).style("width:100%;"):
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
                            try:
                                if m.get("user_id") and \
                                        _is_admin_ui(m["user_id"]):
                                    ui.html(
                                        '<span class="badge-role" style="'
                                        'color:#fbbf24;border:1px solid '
                                        '#fbbf2455;margin-left:4px;">'
                                        'ADMIN</span>')
                                if m.get("user_id") and \
                                        db.is_suspended(m["user_id"]):
                                    ui.html(
                                        '<span class="badge-role" style="'
                                        'color:#f87171;border:1px solid '
                                        '#f8717155;margin-left:4px;">'
                                        'SUSPENDED</span>')
                            except Exception:
                                pass
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
            status_lbl = None
            with preview:
                status_lbl = ui.label(_t("extracting")).classes("mono-sm")
            result = await svc.extract_clauses_from_pdf(
                holder["bytes"], call_gemini_json, holder["name"])
            full_text = result.get("full_text") or ""

            chapters = []
            if not result.get("error") and full_text and \
                    len(full_text) > 200:
                try:
                    if status_lbl:
                        status_lbl.set_text(
                            "Extracting chapter structure...")
                except Exception:
                    pass
                try:
                    chapters = await msc.extract_chapters_from_full_text(
                        full_text, call_gemini_json)
                except Exception as e:
                    print("[ms] chapters extract failed: " + repr(e))
                    chapters = []

            preview.clear()
            if result.get("error"):
                with preview:
                    ui.label(_t("error_prefix") + str(result["error"])).style(
                        "color:#f87171;font-size:10px;")
                return
            clauses = result["clauses"]
            with preview:
                extra_bit = ("  ·  " + str(len(chapters)) + " chapters"
                             if chapters else "")
                ui.label(_t("extracted") + " " + str(len(clauses)) + " " +
                          _t("clauses_count") + extra_bit).style(
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
                        full_text=full_text,
                        chapters=chapters)
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
# MS READER (Feature H) — browse + read full MS text
# =====================================================================
_READER_HEADING_RE = re.compile(r'^\s*(\d+(?:\.\d+){0,4})\s*[\.\)]?\s+\S')
_READER_SECTION_RE = re.compile(
    r'^\s*(?:SECTION|CHAPTER|PART|APPENDIX|ANNEX)\s+[\dA-Z]',
    re.IGNORECASE)


def _reader_looks_like_heading(s):
    if not s:
        return 0
    t = s.strip()
    if not t:
        return 0
    if len(t) > 130:
        return 0
    if _READER_SECTION_RE.match(t):
        return 2
    m = _READER_HEADING_RE.match(t)
    if m:
        try:
            dots = m.group(1).count(".")
        except Exception:
            dots = 0
        if dots == 0:
            return 2
        return 3
    if (len(t) < 80 and t == t.upper()
            and any(c.isalpha() for c in t)
            and not t.endswith(":")
            and len(t.split()) <= 10):
        return 2
    return 0


def _reader_highlight(text, q):
    if not q:
        return _html_mod.escape(text)
    try:
        pat = re.compile(re.escape(q), re.IGNORECASE)
    except Exception:
        return _html_mod.escape(text)
    out = []
    last = 0
    for m in pat.finditer(text):
        out.append(_html_mod.escape(text[last:m.start()]))
        out.append('<span class="reader-hl">' +
                   _html_mod.escape(m.group(0)) + '</span>')
        last = m.end()
    out.append(_html_mod.escape(text[last:]))
    return "".join(out)


def _reader_safe_anchor(cid):
    s = re.sub(r'[^0-9A-Za-z]+', '_', str(cid or "").strip())
    if not s:
        s = "x"
    return "ch-" + s


def _build_ms_reader(state):
    try:
        _build_ms_reader_inner(state)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("[reader] FATAL: " + repr(e))
        with ui.element('div').style(
            "padding:40px 20px;text-align:center;"
        ):
            ui.icon("error_outline").style(
                "font-size:40px;color:#f87171;")
            ui.label("MS Reader failed to load").style(
                "font-size:14px;margin-top:12px;font-weight:700;"
                "color:#e8e8e8;")
            ui.label(str(e)).style(
                "font-size:11px;margin-top:10px;color:#808080;"
                "font-family:monospace;word-break:break-word;")
            ui.label(
                "Check Render Logs for [reader] errors."
            ).style("font-size:10px;margin-top:8px;color:#5a5a5a;")

            def _retry():
                state["render_main"]()
            ui.button("Retry", icon="refresh",
                      on_click=_retry).classes(BTN_SOFT).style(
                "margin-top:16px;")


def _build_ms_reader_inner(state):
    if not state.get("project_id"):
        _render_no_project(state, state["render_main"])
        return
    pid = state["project_id"]

    if state.get("reader_pid") != pid:
        state["reader_pid"] = pid
        state["reader"] = {
            "ms_id": None, "menu_open": False,
            "menu_q": "", "search_q": "", "active_chapter": None,
        }
    rstate = state["reader"]

    try:
        ms_list = db.list_ms(pid) or []
    except Exception:
        ms_list = []

    wrap = ui.element('div').classes("reader-wrap")
    if rstate.get("menu_open"):
        wrap.classes(add="menu-open")

    with wrap:
        with ui.element('aside').classes("reader-menu"):
            _render_reader_menu(state, rstate, ms_list, pid)
        with ui.element('main').classes("reader-main"):
            _render_reader_main(state, rstate, pid)
    print("[reader] built. ms_id=" + repr(rstate.get("ms_id")))


def _render_reader_menu(state, rstate, ms_list, pid):
    with ui.element('div').style(
        "display:flex;align-items:center;justify-content:space-between;"
        "margin-bottom:10px;gap:8px;"
    ):
        ui.label("METHOD STATEMENTS").style(
            "font-size:11px;font-weight:700;color:#5eead4;"
            "letter-spacing:0.06em;")

        def _close_menu():
            rstate["menu_open"] = False
            state["render_main"]()
        ui.button(icon="close", on_click=_close_menu).props(
            "flat round dense size=sm").style("color:#5a5a5a;")

    menu_search = ui.input(
        placeholder="Search MS or chapter...",
        value=rstate.get("menu_q", ""),
    ).style("width:100%;margin-bottom:10px;").props("dense clearable")

    holder = ui.element('div').style("width:100%;")

    def _render_menu_list():
        holder.clear()
        q = (rstate.get("menu_q") or "").strip().lower()
        with holder:
            if not ms_list:
                ui.label("No Method Statements uploaded yet.").style(
                    "color:#808080;font-size:11px;padding:20px 0;"
                    "text-align:center;")
                return
            shown = 0
            for m in ms_list:
                mid = m.get("id")
                title_txt = (
                    str(m.get("title") or "") + " " +
                    str(m.get("ms_number") or "")
                ).lower()
                is_selected = rstate.get("ms_id") == mid
                if q and q not in title_txt and not is_selected:
                    continue
                shown += 1
                _render_menu_ms_item(m, rstate, state, q)
            if q and shown == 0:
                ui.label("No matches.").style(
                    "color:#808080;font-size:11px;padding:20px 0;"
                    "text-align:center;")

    def _on_menu_search(e=None):
        try:
            rstate["menu_q"] = menu_search.value or ""
        except Exception:
            rstate["menu_q"] = ""
        _render_menu_list()

    _attached = False
    try:
        menu_search.on_value_change(_on_menu_search)
        _attached = True
    except Exception as e1:
        print("[reader] menu on_value_change err: " + repr(e1))
    if not _attached:
        try:
            menu_search.on("update:model-value", _on_menu_search)
        except Exception as e2:
            print("[reader] menu update:model-value err: " + repr(e2))

    _render_menu_list()


def _render_menu_ms_item(m, rstate, state, q):
    mid = m.get("id")
    is_selected = rstate.get("ms_id") == mid
    active_chapter = rstate.get("active_chapter")

    item = ui.element('div').classes(
        "reader-ms-item" +
        (" active" if is_selected and not active_chapter else "")
    )
    with item:
        with ui.element('div').style(
            "display:flex;justify-content:space-between;"
            "align-items:flex-start;gap:6px;"
        ):
            ui.html(
                '<span style="font-size:11px;font-weight:700;'
                'color:#e8e8e8;word-break:break-word;line-height:1.35;">' +
                _html_mod.escape(str(m.get("ms_number") or "")) + '  ' +
                _html_mod.escape(str(m.get("title") or "")) + '</span>'
            )
            ui.html(
                '<span style="font-size:10px;color:#5eead4;">' +
                ('▾' if is_selected else '▸') + '</span>'
            )

    def _click_ms():
        if rstate.get("ms_id") == mid:
            rstate["ms_id"] = None
            rstate["active_chapter"] = None
        else:
            rstate["ms_id"] = mid
            rstate["active_chapter"] = None
            rstate["search_q"] = ""
        rstate["menu_open"] = False
        rstate["scroll_top"] = True
        state["render_main"]()
    item.on("click", _click_ms)

    if not is_selected:
        return

    try:
        ms = db.get_ms_by_id(mid)
    except Exception:
        ms = None
    chapters = (ms or {}).get("chapters") or []

    with ui.element('div').classes("reader-chapters"):
        ui.html(
            '<a class="reader-chapter-item" '
            'href="#reader-top">● Read all</a>',
            sanitize=False
        )

        if not chapters:
            ui.label("No chapters extracted yet.").style(
                "font-size:10px;color:#808080;padding:4px 8px;"
                "line-height:1.5;")
        else:
            for ch in chapters:
                cid = str(ch.get("id") or "").strip()
                title = str(ch.get("title") or "").strip()
                if not cid and not title:
                    continue
                if q and q not in (cid + " " + title).lower():
                    continue
                anchor = "ch-" + re.sub(r'[^0-9A-Za-z]+', '_',
                                         cid or "x")
                label = (("S" + cid + "  ") if cid else "") + title
                ui.html(
                    '<a class="reader-chapter-item" '
                    'href="#' + _html_mod.escape(anchor) + '" '
                    'data-chapter="' + _html_mod.escape(cid) + '">' +
                    _html_mod.escape(label) + '</a>',
                    sanitize=False
                )


def _render_reader_main(state, rstate, pid):
    if not rstate.get("ms_id"):
        with ui.element('div').classes("reader-empty"):
            ui.icon("menu_book").style("font-size:36px;color:#5a5a5a;")
            ui.label("Pick a Method Statement to read").style(
                "font-size:14px;color:#b8b8b8;margin-top:12px;")
            ui.label(
                "Use the left menu to browse documents and chapters, or "
                "click Read all to see the entire MS."
            ).style("font-size:11px;color:#808080;margin-top:6px;"
                    "max-width:320px;margin-left:auto;margin-right:auto;"
                    "line-height:1.6;")
            with ui.element('div').style("margin-top:20px;"):
                def _open_menu():
                    rstate["menu_open"] = True
                    state["render_main"]()
                ui.button("Browse MS", icon="menu_book",
                          on_click=_open_menu).classes(BTN_PRIMARY).style(
                    "width:200px;")
        return

    try:
        ms = db.get_ms_by_id(rstate["ms_id"])
    except Exception:
        ms = None
    if not ms:
        with ui.element('div').classes("reader-empty"):
            ui.label("This MS could not be loaded.").style(
                "font-size:13px;color:#f87171;")
        return

    full_text = str(ms.get("full_text") or "")
    chapters = ms.get("chapters") or []

    with ui.element('div').classes("reader-topbar"):
        def _toggle_menu():
            rstate["menu_open"] = not rstate.get("menu_open")
            state["render_main"]()
        with ui.element('button').classes("reader-menu-btn") as btn:
            ui.icon("menu").style("font-size:16px;")
        btn.on("click", _toggle_menu)

        title_str = (str(ms.get("ms_number") or "") + "  " +
                     str(ms.get("title") or ""))
        ui.label(title_str).classes("reader-title")

        ui.html(
            '<a class="reader-readall" href="#reader-top">Read all</a>',
            sanitize=False
        )

    with ui.element('div').style(
        "padding:10px 12px;display:grid;grid-template-columns:1fr 1fr;"
        "gap:6px;border-bottom:1px solid var(--border);"
    ):
        def _find_errors():
            _open_ms_weak_points_dialog(ms)
        def _rate_ms():
            _open_ms_rating_dialog(ms)
        ui.button("Find errors with AI", icon="rule",
                  on_click=_find_errors).classes(BTN_SOFT).style(
            "width:100%;font-size:10px;")
        ui.button("Rate this MS", icon="star",
                  on_click=_rate_ms).classes(BTN_SOFT).style(
            "width:100%;font-size:10px;")

    hits_holder = {"label": None}
    with ui.element('div').classes("reader-search"):
        with ui.element('div').style(
            "display:flex;align-items:center;gap:8px;"
        ):
            def _on_search_change(e=None):
                val = None
                try:
                    if isinstance(e, str):
                        val = e
                    elif e is not None and hasattr(e, "value"):
                        val = e.value
                except Exception:
                    val = None
                if val is None:
                    try:
                        val = s_in.value or ""
                    except Exception:
                        val = ""
                rstate["search_q"] = str(val or "")
                print("[reader] search_q=" + repr(rstate["search_q"]))
                try:
                    body_refreshable.refresh()
                except Exception as ex:
                    print("[reader] refresh err: " + repr(ex))

            s_in = ui.input(
                placeholder="Search inside this MS...",
                value=rstate.get("search_q", ""),
                on_change=_on_search_change,
            ).style("flex:1;").props("dense clearable")
            h_lbl = ui.label("").style(
                "font-size:10px;color:#5eead4;font-weight:700;"
                "min-width:56px;text-align:right;white-space:nowrap;")
            hits_holder["label"] = h_lbl

    body_slot = ui.element('div').style("width:100%;")

    def _set_hits(n):
        try:
            if not n:
                hits_holder["label"].set_text("")
            else:
                hits_holder["label"].set_text(
                    str(n) + (" hit" if n == 1 else " hits"))
        except Exception:
            pass

    def render_body():
        body_slot.clear()
        hits = 0
        with body_slot:
            try:
                hits = _render_reader_body(full_text, chapters, rstate)
            except Exception as e:
                import traceback
                traceback.print_exc()
                print("[reader] body err: " + repr(e))
        _set_hits(hits)

    def _on_search_change2(e=None):
        val = None
        try:
            if isinstance(e, str):
                val = e
            elif e is not None and hasattr(e, "value"):
                val = e.value
        except Exception:
            val = None
        if val is None:
            try:
                val = s_in.value or ""
            except Exception:
                val = ""
        rstate["search_q"] = str(val or "")
        render_body()

    _bound = False
    try:
        s_in.on_value_change(_on_search_change2)
        _bound = True
    except Exception:
        pass
    if not _bound:
        try:
            s_in.on("update:model-value", _on_search_change2)
        except Exception:
            pass

    render_body()

    if rstate.pop("scroll_top", False):
        js = (
            "(function(){"
            "var tries=0;"
            "var t=setInterval(function(){"
            "  var el=document.querySelector('.reader-body-outer')"
            "       || document.querySelector('.reader-body');"
            "  if(!el){tries++; if(tries>30){clearInterval(t);} return;}"
            "  clearInterval(t);"
            "  try{ el.scrollIntoView({behavior:'smooth',block:'start'}); }"
            "  catch(e1){"
            "    try{"
            "      var r=el.getBoundingClientRect();"
            "      var y=(window.pageYOffset"
            "            ||document.documentElement.scrollTop||0)"
            "            + r.top - 150;"
            "      if(y<0)y=0;"
            "      window.scrollTo(0,y);"
            "    }catch(e2){}"
            "  }"
            "},60);"
            "})();"
        )
        try:
            ui.run_javascript(js)
            print("[reader] scroll scheduled")
        except Exception as e:
            print("[reader] scroll js err: " + repr(e))


def _render_reader_body(full_text, chapters, rstate):
    if not (full_text or "").strip():
        ui.html(
            '<div class="reader-body" style="color:#808080;'
            'padding-top:40px;">No full text stored for this MS. '
            'Re-upload the document to enable reading.</div>')
        return 0

    q = (rstate.get("search_q") or "").strip()
    lines = full_text.split("\n")

    valid_chapters = [c for c in chapters
                       if isinstance(c.get("line"), int)
                       and c.get("line", -1) >= 0]
    valid_chapters.sort(key=lambda c: c["line"])
    chapter_at_line = {c["line"]: c for c in valid_chapters}

    hits = 0

    def hl(text):
        nonlocal hits
        if not q:
            return _html_mod.escape(text)
        try:
            pat = re.compile(re.escape(q), re.IGNORECASE)
        except Exception:
            return _html_mod.escape(text)
        out = []
        last = 0
        for m in pat.finditer(text):
            out.append(_html_mod.escape(text[last:m.start()]))
            out.append('<span class="reader-hl">' +
                       _html_mod.escape(m.group(0)) + '</span>')
            hits += 1
            last = m.end()
        out.append(_html_mod.escape(text[last:]))
        return "".join(out)

    parts = ['<span id="reader-top"></span>']
    for i, raw in enumerate(lines):
        s = raw.rstrip()
        if i in chapter_at_line:
            ch = chapter_at_line[i]
            cid = str(ch.get("id") or "").strip()
            anchor = "ch-" + re.sub(r'[^0-9A-Za-z]+', '_', cid or "x")
            esc = hl(s if s.strip() else (ch.get("title") or ""))
            parts.append(
                '<h2 id="' + _html_mod.escape(anchor) +
                '" class="reader-h1">' + esc + '</h2>')
            continue
        if not s.strip():
            parts.append('<div class="reader-gap"></div>')
            continue
        level = _reader_looks_like_heading(s)
        esc = hl(s)
        if level == 2:
            parts.append('<h3 class="reader-h2">' + esc + '</h3>')
        elif level == 3:
            parts.append('<h4 class="reader-h3">' + esc + '</h4>')
        else:
            parts.append('<p class="reader-para">' + esc + '</p>')

    body_html = ('<div class="reader-body">' + "".join(parts) + '</div>')
    try:
        ui.html(body_html, sanitize=False)
    except TypeError:
        ui.html(body_html)

    return hits


def _open_ms_weak_points_dialog(ms):
    with ui.dialog() as dlg, ui.card().style(
        "padding:22px;min-width:320px;max-width:95vw;width:520px;"
    ):
        ui.label("Find errors in MS with AI").classes("h1").style(
            "margin-bottom:6px;")
        ui.label("Coming in the next update.").classes(
            "muted").style("margin-bottom:12px;color:#fbbf24;")
        ui.label(
            "This will compare \"" + str(ms.get("title") or "this MS") +
            "\" line by line against SCP 203, ECP 202, AASHTO, and ISO."
        ).classes("mono-sm").style(
            "line-height:1.65;color:#b8b8b8;margin-bottom:14px;")
        ui.button(_t("close"), on_click=dlg.close).classes(
            BTN_SOFT).style("width:100%;")
    dlg.open()


def _open_ms_rating_dialog(ms):
    with ui.dialog() as dlg, ui.card().style(
        "padding:22px;min-width:320px;max-width:95vw;width:520px;"
    ):
        ui.label("Rate this MS").classes("h1").style("margin-bottom:6px;")
        ui.label("Coming in the next update.").classes(
            "muted").style("margin-bottom:12px;color:#fbbf24;")
        ui.label(
            "This will show a full analytical rating of \"" +
            str(ms.get("title") or "this MS") + "\"."
        ).classes("mono-sm").style(
            "line-height:1.65;color:#b8b8b8;margin-bottom:14px;")
        ui.button(_t("close"), on_click=dlg.close).classes(
            BTN_SOFT).style("width:100%;")
    dlg.open()


# =====================================================================
# TDS TOOLS — upload TDS → AI MOS + ITP
# =====================================================================
def _build_tds_tools(state):
    if not state.get("project_id"):
        _render_no_project(state, state["render_main"])
        return

    tstate = state.setdefault("tds", {
        "result": None, "running": False, "error": None,
        "filename": "",
    })

    with ui.element('div').classes("section-head"):
        ui.label("TDS → MOS & ITP").classes("h1")

        def _refresh():
            tstate["result"] = None
            tstate["error"] = None
            state["render_main"]()
        ui.button(icon="refresh", on_click=_refresh).props(
            "flat round dense size=sm").style("color:#808080;")

    ui.label(
        "Upload a manufacturer Technical Data Sheet (PDF, DOCX, TXT, "
        "or image). The tool extracts critical parameters with AI and "
        "drafts a Method Statement + an Inspection & Test Plan."
    ).classes("muted").style("margin-bottom:12px;line-height:1.6;")

    with ui.element('div').classes("card").style("margin-bottom:12px;"):
        upload_status = ui.label("").classes("mono-sm").style(
            "margin-top:6px;display:block;min-height:16px;")

        async def _on_upload(e):
            if tstate["running"]:
                ui.notify("Already processing…", type="warning")
                return
            try:
                data = await e.file.read()
            except Exception as ex:
                ui.notify("Read failed: " + str(ex), type="negative")
                return

            name = (e.file.name or "").lower()
            tstate["filename"] = e.file.name or ""
            tstate["result"] = None
            tstate["error"] = None

            upload_status.set_text("Extracting text from " +
                                    (e.file.name or "file") + "…")
            upload_status.style(
                "margin-top:6px;display:block;min-height:16px;"
                "color:#fbbf24;font-size:10px;")

            text = ""
            try:
                if name.endswith((".pdf", ".docx", ".txt", ".md")):
                    text = await asyncio.to_thread(
                        svc.extract_document_text, data, e.file.name)
                elif name.endswith((".jpg", ".jpeg", ".png")):
                    mime = ("image/jpeg"
                            if name.endswith((".jpg", ".jpeg"))
                            else "image/png")
                    text, err = await _ocr_handwriting(data, mime)
                    if err and not text:
                        text = ""
                else:
                    text = await asyncio.to_thread(
                        svc.extract_document_text, data, e.file.name)
            except Exception as ex:
                print("[tds] extract failed: " + repr(ex))
                text = ""

            if not text or len(text.strip()) < 100:
                tstate["error"] = (
                    "Could not read enough text from the file. "
                    "Try a text-based PDF or DOCX."
                )
                upload_status.set_text("Failed: not enough text.")
                upload_status.style(
                    "margin-top:6px;display:block;min-height:16px;"
                    "color:#f87171;font-size:10px;")
                state["render_main"]()
                return

            upload_status.set_text(
                "Extracted " + str(len(text)) + " chars. "
                "Calling AI to draft MOS + ITP… (up to 2 min)")

            tstate["running"] = True
            try:
                result = await tds.generate_mos_itp(text, call_gemini_json)
            except Exception as ex:
                import traceback
                traceback.print_exc()
                result = {"error": "AI failed: " + repr(ex)}
            tstate["running"] = False

            if result.get("error"):
                tstate["error"] = result["error"]
            else:
                tstate["result"] = result
            state["render_main"]()

        ui.upload(on_upload=_on_upload, auto_upload=True).style(
            "width:100%;").props(
            "flat bordered accept=.pdf,.docx,.txt,.md,.jpg,.jpeg,.png "
            "label='Upload TDS (PDF / DOCX / TXT / Image)'")
        upload_status

    if tstate.get("error"):
        with ui.element('div').classes("card").style(
            "border-left:3px solid #f87171;margin-bottom:12px;"
        ):
            ui.label("Error").style(
                "font-size:11px;font-weight:700;color:#f87171;")
            ui.label(str(tstate["error"])).classes("mono-sm").style(
                "margin-top:4px;line-height:1.6;color:#b8b8b8;")
            raw = tstate.get("result") or {}
            if raw.get("raw"):
                ui.label(str(raw["raw"])[:500]).classes("mono-sm").style(
                    "margin-top:6px;color:#5a5a5a;font-size:9px;")

    result = tstate.get("result")
    if not result:
        return

    product = result.get("product") or {}
    mos = result.get("method_statement") or {}
    itp = result.get("inspection_test_plan") or {}
    crit = result.get("critical_parameters") or []

    with ui.element('div').style(
        "display:grid;grid-template-columns:1fr 1fr;gap:6px;"
        "margin-bottom:12px;"
    ):
        def _mos_txt():
            try:
                lines = []
                lines.append(mos.get("title") or "METHOD STATEMENT")
                lines.append("=" * 60)
                p_bits = []
                if product.get("name"):
                    p_bits.append("Product: " + str(product["name"]))
                if product.get("manufacturer"):
                    p_bits.append("Manufacturer: " +
                                  str(product["manufacturer"]))
                if product.get("tds_reference"):
                    p_bits.append("TDS ref: " +
                                  str(product["tds_reference"]))
                if product.get("category"):
                    p_bits.append("Category: " +
                                  str(product["category"]))
                lines.extend(p_bits)
                lines.append("Date: " +
                             datetime.date.today().strftime("%Y-%m-%d"))
                lines.append("")
                if product.get("description"):
                    lines.append(str(product["description"]))
                    lines.append("")
                if crit:
                    lines.append("KEY PARAMETERS FROM TDS")
                    lines.append("-" * 60)
                    for cp in crit:
                        lines.append(
                            str(cp.get("parameter") or "") + " : " +
                            str(cp.get("value") or "")
                            + ("  (" + str(cp["source_note"]) + ")"
                               if cp.get("source_note") else "")
                        )
                    lines.append("")
                for sec in (mos.get("sections") or []):
                    num = str(sec.get("number") or "").strip()
                    head = str(sec.get("heading") or "").strip()
                    head_line = (num + ". " + head) if num else head
                    if not head_line:
                        continue
                    lines.append(head_line)
                    lines.append("-" * len(head_line))
                    body = str(sec.get("body") or "").strip()
                    if body:
                        lines.append(body)
                    lines.append("")
                lines.append("")
                lines.append("PREPARED BY (QC): ____________________")
                lines.append("APPROVED BY (CONSULTANT): ____________________")
                lines.append("")
                txt = "\n".join(lines).encode("utf-8")
                ui.download(txt, filename="method_statement.txt")
            except Exception as ex:
                import traceback
                traceback.print_exc()
                ui.notify("TXT failed: " + str(ex), type="negative")

        def _itp_txt():
            try:
                lines = []
                lines.append(itp.get("title") or
                             "INSPECTION & TEST PLAN")
                lines.append("=" * 100)
                p_bits = []
                if product.get("name"):
                    p_bits.append("Product: " + str(product["name"]))
                if product.get("manufacturer"):
                    p_bits.append("Manufacturer: " +
                                  str(product["manufacturer"]))
                lines.extend(p_bits)
                lines.append("Date: " +
                             datetime.date.today().strftime("%Y-%m-%d"))
                lines.append("")
                headers = ["#", "Activity", "Reference", "Checkpoint",
                           "Acceptance criteria", "Method",
                           "Frequency", "Responsible"]
                widths = [3, 22, 16, 26, 34, 20, 12, 14]
                def _row(cells):
                    out = []
                    for i, c in enumerate(cells):
                        c = str(c or "").replace("\n", " ")
                        w = widths[i]
                        if i == 0:
                            out.append(c.rjust(w))
                        else:
                            out.append(c[:w].ljust(w))
                    return " | ".join(out)
                lines.append(_row(headers))
                lines.append("-+-".join("-" * w for w in widths))
                for i, r in enumerate(itp.get("rows") or [], start=1):
                    lines.append(_row([
                        str(i),
                        r.get("activity") or "",
                        r.get("reference") or "",
                        r.get("checkpoint") or "",
                        r.get("acceptance_criteria") or "",
                        r.get("method") or "",
                        r.get("frequency") or "",
                        r.get("responsible") or "",
                    ]))
                lines.append("")
                txt = "\n".join(lines).encode("utf-8")
                ui.download(txt, filename="inspection_test_plan.txt")
            except Exception as ex:
                import traceback
                traceback.print_exc()
                ui.notify("TXT failed: " + str(ex), type="negative")

        def _dl_mos():
            try:
                pdf = tds.build_mos_pdf(product, mos, crit)
                ui.download(pdf, filename="method_statement.pdf")
            except Exception as ex:
                import traceback
                traceback.print_exc()
                ui.notify("PDF failed: " + str(ex), type="negative")

        def _dl_itp():
            try:
                pdf = tds.build_itp_pdf(product, itp)
                ui.download(pdf, filename="inspection_test_plan.pdf")
            except Exception as ex:
                import traceback
                traceback.print_exc()
                ui.notify("PDF failed: " + str(ex), type="negative")

        ui.button("Method Statement — TXT", icon="description",
                  on_click=_mos_txt).classes(BTN_SOFT).style(
            "width:100%;font-size:10px;")
        ui.button("ITP — TXT", icon="description",
                  on_click=_itp_txt).classes(BTN_SOFT).style(
            "width:100%;font-size:10px;")
        ui.button("Method Statement — PDF", icon="picture_as_pdf",
                  on_click=_dl_mos).classes(BTN_PRIMARY).style(
            "width:100%;font-size:10px;")
        ui.button("ITP — PDF", icon="picture_as_pdf",
                  on_click=_dl_itp).classes(BTN_PRIMARY).style(
            "width:100%;font-size:10px;")

    with ui.element('div').classes("card").style("margin-bottom:12px;"):
        ui.label("PRODUCT").classes("label")
        ui.label(str(product.get("name") or "Not specified")).style(
            "font-size:14px;font-weight:700;color:#e8e8e8;margin-top:4px;")
        bits = []
        if product.get("manufacturer"):
            bits.append("Mfr: " + str(product["manufacturer"]))
        if product.get("tds_reference"):
            bits.append("TDS: " + str(product["tds_reference"]))
        if product.get("category"):
            bits.append("Cat: " + str(product["category"]))
        if bits:
            ui.label(" · ".join(bits)).classes("mono-sm").style(
                "margin-top:4px;color:#b8b8b8;")

    with ui.element('div').classes("card").style("margin-bottom:12px;"):
        ui.html(
            '<div style="font-size:15px;font-weight:700;'
            'color:#5eead4;border-bottom:1px solid rgba(94,234,212,0.3);'
            'padding-bottom:8px;margin-bottom:12px;'
            'letter-spacing:-0.01em;">' +
            _html_mod.escape(mos.get("title") or "METHOD STATEMENT") +
            '</div>'
        )
        for sec in (mos.get("sections") or []):
            num = str(sec.get("number") or "").strip()
            head = str(sec.get("heading") or "").strip()
            head_line = (num + ". " + head) if num else head
            if not head_line:
                continue
            ui.html(
                '<div style="font-size:12px;font-weight:700;'
                'color:#5eead4;margin-top:14px;margin-bottom:4px;'
                'letter-spacing:0.02em;">' +
                _html_mod.escape(head_line) + '</div>'
            )
            body = str(sec.get("body") or "").strip()
            if body:
                ui.html(
                    '<pre style="margin:0 0 4px 0;white-space:pre-wrap;'
                    'word-break:break-word;font-family:inherit;'
                    'font-size:12px;line-height:1.7;color:#d0d0d0;">' +
                    _html_mod.escape(body) + '</pre>'
                )

    with ui.element('div').classes("card").style("margin-bottom:12px;"):
        ui.html(
            '<div style="font-size:15px;font-weight:700;'
            'color:#5eead4;border-bottom:1px solid rgba(94,234,212,0.3);'
            'padding-bottom:8px;margin-bottom:12px;'
            'letter-spacing:-0.01em;">' +
            _html_mod.escape(itp.get("title") or "INSPECTION & TEST PLAN") +
            '</div>'
        )
        rows = itp.get("rows") or []
        if not rows:
            ui.label("No ITP rows generated.").classes("muted")
        else:
            html = ('<table style="width:100%;border-collapse:collapse;'
                    'font-size:10.5px;'
                    'font-variant-numeric:tabular-nums;">'
                    '<thead><tr style="background:#0a0a0a;">')
            heads = ["#", "Activity", "Reference", "Checkpoint",
                     "Acceptance criteria", "Method", "Freq.", "Resp."]
            for h in heads:
                html += ('<th style="text-align:left;padding:6px 6px;'
                         'font-size:9px;letter-spacing:0.12em;'
                         'color:#5eead4;text-transform:uppercase;'
                         'border-bottom:1px solid #1e1e1e;">' +
                         _html_mod.escape(h) + '</th>')
            html += '</tr></thead><tbody>'
            for i, r in enumerate(rows, start=1):
                html += '<tr style="border-bottom:1px solid #1e1e1e;">'
                cells = [
                    str(i),
                    str(r.get("activity") or ""),
                    str(r.get("reference") or ""),
                    str(r.get("checkpoint") or ""),
                    str(r.get("acceptance_criteria") or ""),
                    str(r.get("method") or ""),
                    str(r.get("frequency") or ""),
                    str(r.get("responsible") or ""),
                ]
                for j, c in enumerate(cells):
                    col = "#e8e8e8" if j == 0 else "#d0d0d0"
                    html += ('<td style="padding:6px 6px;'
                             'vertical-align:top;color:' + col + ';'
                             'font-size:10.5px;line-height:1.45;">' +
                             _html_mod.escape(c) + '</td>')
                html += '</tr>'
            html += '</tbody></table>'
            ui.html(html)

# =====================================================================
# MS CHAT — Gemini style
# =====================================================================
# =====================================================================
# MS READER + CITATIONS (Feature #8)
# =====================================================================
_CITE_RE = re.compile(r'\[S([\w.\-]+)\]')


def _clause_map_for_project(pid):
    try:
        clauses = db.get_clauses_for_element(pid) or []
    except Exception:
        return {}
    out = {}
    for c in clauses:
        cid = str(c.get("id", "")).strip()
        if cid:
            out[cid] = c
    return out


def _open_clause_modal(cid, pid):
    clauses = _clause_map_for_project(pid)
    clause = clauses.get(str(cid))
    if not clause:
        ui.notify("Clause S" + str(cid) + " not found in the uploaded MS.",
                    type="warning")
        return
    with ui.dialog() as dlg, ui.card().style(
        "padding:20px;min-width:320px;max-width:95vw;width:520px;"
        "max-height:88vh;overflow-y:auto;"
    ):
        with ui.element('div').style(
            "display:flex;align-items:center;gap:8px;"
            "padding-bottom:10px;border-bottom:1px solid #1e1e1e;"
            "margin-bottom:12px;"
        ):
            ui.html('<span class="cite-pill" style="cursor:default;">[S' +
                    _html_mod.escape(str(cid)) + ']</span>')
            ui.label(str(clause.get("title", ""))).style(
                "font-size:14px;font-weight:700;color:#e8e8e8;"
                "letter-spacing:-0.01em;")
        body = str(clause.get("text", "") or "")
        if body:
            ui.html('<div style="font-size:13px;color:#e3e3e3;'
                    'line-height:1.7;white-space:pre-wrap;'
                    'word-break:break-word;">' +
                    _html_mod.escape(body) + '</div>')
        else:
            ui.label("(This clause has no body text stored.)").classes(
                "mono-sm").style("color:#5a5a5a;")
        ui.button(_t("close"), on_click=dlg.close).classes(
            BTN_SOFT).style("width:100%;margin-top:16px;")
    dlg.open()


def _render_answer_with_citations(answer, pid):
    text = str(answer or "")
    if not text:
        return
    clauses = _clause_map_for_project(pid)
    html_parts = []
    last = 0
    for m in _CITE_RE.finditer(text):
        if m.start() > last:
            html_parts.append(_html_mod.escape(text[last:m.start()]))
        cid = m.group(1)
        if cid in clauses:
            html_parts.append(
                '<span class="cite-pill" data-cid="' +
                _html_mod.escape(cid) +
                '" title="Tap to view the clause text">[' +
                _html_mod.escape(cid) + ']</span>'
            )
        else:
            html_parts.append(
                '<span class="cite-pill miss">[' +
                _html_mod.escape(cid) + ']</span>'
            )
        last = m.end()
    if last < len(text):
        html_parts.append(_html_mod.escape(text[last:]))
    ui.html('<div class="gem-ai">' + "".join(html_parts) + '</div>')


def _open_ms_reader_dialog(pid):
    if not pid:
        ui.notify(_t("setup_first"), type="warning")
        return
    try:
        docs = db.list_ms(pid) or []
    except Exception as e:
        ui.notify("Failed to load MS: " + str(e), type="negative")
        return
    if not docs:
        ui.notify(_t("ms_chat_need_ms"), type="warning")
        return

    with ui.dialog() as dlg, ui.card().style(
        "padding:0;max-width:640px;width:95vw;max-height:90vh;"
        "overflow:hidden;"
    ):
        with ui.element('div').style(
            "padding:16px 18px 12px;border-bottom:1px solid #1e1e1e;"
            "display:flex;justify-content:space-between;align-items:center;"
        ):
            ui.label("METHOD STATEMENTS").style(
                "font-size:13px;font-weight:700;color:#e8e8e8;"
                "letter-spacing:0.06em;")
            ui.label(str(len(docs)) + " uploaded").classes("mono-sm").style(
                "font-size:10px;color:#808080;")

        view_holder = ui.element('div').style(
            "padding:14px 18px 18px;max-height:calc(90vh - 120px);"
            "overflow-y:auto;"
        )

        def render_list():
            view_holder.clear()
            with view_holder:
                for doc in docs:
                    with ui.element('div').classes("ms-reader-doc") as card:
                        with ui.element('div').style(
                            "display:flex;justify-content:space-between;"
                            "align-items:flex-start;gap:8px;"
                        ):
                            with ui.element('div').style(
                                "flex:1;min-width:0;"
                            ):
                                ui.label(
                                    str(doc.get("ms_number", "")) + "  " +
                                    str(doc.get("title", ""))
                                ).style(
                                    "font-size:12px;font-weight:700;"
                                    "color:#e8e8e8;word-break:break-word;")
                                ui.label(
                                    str(doc.get("element_type", "")) + " · " +
                                    str(doc.get("discipline", ""))
                                ).classes("mono-sm").style(
                                    "font-size:10px;color:#808080;"
                                    "margin-top:2px;")
                            ui.html('<span class="badge-seen">' +
                                    str(len(doc.get("clauses") or [])) +
                                    ' clauses</span>')

                        def _open(d=doc):
                            render_doc(d)
                        card.on("click", _open)

        def render_doc(doc):
            view_holder.clear()
            with view_holder:
                with ui.element('div').style(
                    "display:flex;align-items:center;gap:8px;"
                    "margin-bottom:12px;"
                ):
                    def _back():
                        render_list()
                    ui.button(icon="arrow_back", on_click=_back).props(
                        "flat round dense size=sm").style("color:#5eead4;")
                    with ui.element('div').style("flex:1;min-width:0;"):
                        ui.label(str(doc.get("title", ""))).style(
                            "font-size:14px;font-weight:700;color:#e8e8e8;")
                        ui.label(str(doc.get("ms_number", "")) + " · " +
                                  str(doc.get("element_type", "")) + " · " +
                                  str(doc.get("discipline", ""))).classes(
                            "mono-sm").style(
                            "font-size:10px;color:#808080;margin-top:2px;")

                clauses = doc.get("clauses") or []
                if not clauses:
                    ui.label("No clauses stored for this document.").classes(
                        "mono-sm").style("color:#5a5a5a;padding:20px 0;"
                                          "text-align:center;")
                    return
                for c in clauses:
                    with ui.element('div').classes("ms-reader-clause"):
                        with ui.element('div').style(
                            "display:flex;align-items:baseline;gap:2px;"
                        ):
                            ui.html('<span class="cid">S' +
                                    _html_mod.escape(str(c.get("id", ""))) +
                                    '</span>')
                            ui.html('<span class="ctitle">' +
                                    _html_mod.escape(
                                        str(c.get("title", ""))) +
                                    '</span>')
                        if c.get("text"):
                            ui.html('<div class="ctext">' +
                                    _html_mod.escape(str(c.get("text", "")))
                                    + '</div>')

        render_list()

        with ui.element('div').style(
            "padding:10px 18px 16px;border-top:1px solid #1e1e1e;"
        ):
            ui.button(_t("close"), on_click=dlg.close).classes(
                BTN_SOFT).style("width:100%;")

    dlg.open()


def _ensure_cite_click_listener():
    ui.run_javascript("""
        (function(){
          if (window._citeListenerAttached) return;
          window._citeListenerAttached = true;
          document.body.addEventListener('click', function(ev){
            var el = ev.target.closest('.cite-pill[data-cid]');
            if (el) {
              emitEvent('cite_click', el.getAttribute('data-cid'));
            }
          });
        })();
    """)


def _build_ms_chat(state):
    if not state.get("project_id"):
        _render_no_project(state, state["render_main"])
        return
    pid = state["project_id"]
    uid = state["user_id"]
    _current_uid_holder["uid"] = uid
    user = state.get("user") or {}
    my_name = (user.get("name") or user.get("email") or "me")

    _ensure_cite_click_listener()
    if not state.get("_cite_handler_registered"):
        def _on_cite_click(e):
            try:
                cid = e.args[0] if e.args else None
            except Exception:
                cid = None
            if cid:
                _open_clause_modal(cid, state.get("project_id"))
        ui.on("cite_click", _on_cite_click)
        state["_cite_handler_registered"] = True

    with ui.element('div').classes("chat-tools"):
        def _open_reader():
            _open_ms_reader_dialog(pid)
        ui.button(icon="menu_book", on_click=_open_reader).props(
            "round dense size=sm").tooltip("Browse Method Statements")

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
            "round dense size=sm").tooltip(_t("ms_chat_clear"))

        def _refresh():
            state["render_main"]()
        ui.button(icon="refresh", on_click=_refresh).props(
            "round dense size=sm").tooltip("Refresh")

    with ui.element('div').style("padding:0 4px 8px 4px;"):
        ui.label(_t("ms_chat_title")).style(
            "font-size:18px;font-weight:700;color:#e3e3e3;"
            "letter-spacing:-0.01em;")

    clauses_count = len(db.get_clauses_for_element(pid))
    if clauses_count == 0:
        with ui.element('div').style(
            "text-align:center;padding:60px 20px;"
        ):
            ui.icon("description").style(
                "font-size:36px;color:#5a5a5a;")
            ui.label(_t("ms_chat_need_ms")).style(
                "color:#9aa0a6;font-size:13px;margin-top:14px;"
                "line-height:1.7;max-width:320px;margin-left:auto;"
                "margin-right:auto;display:block;")
        return

    q_input_holder = {"el": None}

    @ui.refreshable
    def ms_list():
        try:
            msgs = db.ms_chat_list(pid, uid, limit=200) or []
        except Exception:
            msgs = []

        if not msgs:
            with ui.element('div').classes("gem-wrap"):
                with ui.element('div').classes("gem-empty"):
                    ui.label("Hi " + my_name.split()[0] + " 👋").classes(
                        "gem-empty-title")
                    ui.label(
                        "Ask me anything about your Method Statements. "
                        "I'll answer from the uploaded MS and cite the "
                        "clause."
                    ).classes("gem-empty-sub")
                    with ui.element('div').classes("gem-empty-chips"):
                        def _make_suggest(question):
                            def _fill():
                                try:
                                    el = q_input_holder.get("el")
                                    if el is not None:
                                        el.value = question
                                except Exception:
                                    pass
                            return _fill
                        ui.label(
                            "What is the minimum cover for columns?"
                        ).classes("gem-chip").on(
                            "click",
                            _make_suggest(
                                "What is the minimum cover for "
                                "columns exposed to weather?"))
                        ui.label(
                            "Lap length for tension bars?"
                        ).classes("gem-chip").on(
                            "click",
                            _make_suggest(
                                "What is the lap length for tension bars?"))
                        ui.label(
                            "Curing requirements?"
                        ).classes("gem-chip").on(
                            "click",
                            _make_suggest(
                                "What are the curing requirements?"))
            return

        with ui.element('div').classes("gem-wrap"):
            for m in msgs:
                _render_ms_message(m, on_delete=ms_list.refresh, pid=pid)

    ms_list()

    with ui.element('div').classes("gem-composer"):
        with ui.element('div').classes("gem-composer-inner"):

            async def _on_doc(e):
                try:
                    data = await e.file.read()
                except Exception as ex:
                    ui.notify(_t("upload_failed") + str(ex),
                               type="negative")
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

                ui.notify(_t("ms_chat_reading"), type="info", timeout=2000)
                try:
                    result = await msc.check_document_against_ms(
                        file_bytes=data, mime_type=mime, project_id=pid,
                        ocr_fn=_ocr_handwriting,
                        call_gemini_json_fn=call_gemini_json)
                except Exception as ex:
                    ui.notify(_t("ms_chat_failed") + str(ex),
                               type="negative")
                    return
                if result.get("error"):
                    ui.notify(_t("ms_chat_failed") +
                               str(result["error"]), type="negative")
                    return
                resp = {k: result.get(k) for k in
                        ("doc_type", "extracted", "checks", "overall",
                         "summary", "ocr_text")}
                try:
                    db.ms_chat_add(pid, uid, my_name, "check",
                                    _t("ms_chat_check_btn"), resp)
                except Exception as ex:
                    ui.notify("Save failed: " + str(ex), type="negative")
                    return
                try:
                    ms_list.refresh()
                except Exception:
                    pass
                ui.run_javascript(
                    "window.scrollTo({top: document.body.scrollHeight,"
                    " behavior:'smooth'});")

            hidden_upload_holder = ui.element('div').style(
                "position:absolute;left:-9999px;top:-9999px;width:1px;"
                "height:1px;overflow:hidden;")
            with hidden_upload_holder:
                ui.upload(on_upload=_on_doc, auto_upload=True).props(
                    "flat bordered accept=image/*,.pdf").style(
                    "width:1px;height:1px;")

            with ui.element('div').classes("gem-pill"):
                def _open_picker():
                    try:
                        ui.run_javascript("""
                            (function() {
                              var holders = document.querySelectorAll(
                                '.gem-composer-inner .q-uploader');
                              for (var i = 0; i < holders.length; i++) {
                                var inp = holders[i].querySelector(
                                  'input[type=file]');
                                if (inp) { inp.click(); return; }
                              }
                            })();
                        """)
                    except Exception as e:
                        print("[ms] open picker failed: " + repr(e))

                ui.button(icon="add", on_click=_open_picker).classes(
                    "gem-icon-btn plus").props("flat round dense")

                q_input = ui.textarea(
                    placeholder=_t("ms_chat_ask_placeholder")
                ).style("width:100%;").props("dense autogrow borderless")
                q_input_holder["el"] = q_input

                send_btn = ui.button(icon="arrow_upward").classes(
                    "gem-icon-btn send").props("flat round dense")

                send_state = {"busy": False}

                async def _ask():
                    if send_state["busy"]:
                        ui.notify("Still waiting for the previous answer…",
                                   type="warning")
                        return
                    q = (q_input.value or "").strip()
                    if not q:
                        return
                    send_state["busy"] = True
                    try:
                        send_btn.classes(remove="active")
                        send_btn.props("loading")
                    except Exception:
                        pass

                    result = None
                    err_msg = None
                    try:
                        result = await asyncio.wait_for(
                            msc.ask_ms_question(pid, q, call_gemini_json),
                            timeout=90.0)
                    except asyncio.TimeoutError:
                        err_msg = ("The AI did not respond within 90s. "
                                    "Please try again.")
                    except Exception as ex:
                        import traceback
                        traceback.print_exc()
                        err_msg = repr(ex)
                    finally:
                        try:
                            send_btn.props(remove="loading")
                        except Exception:
                            pass
                        send_state["busy"] = False

                    if err_msg:
                        ui.notify(_t("ms_chat_failed") + err_msg,
                                   type="negative", timeout=9000)
                        return

                    if not result or result.get("error"):
                        ui.notify(
                            _t("ms_chat_failed") +
                            str((result or {}).get("error", "Empty result")),
                            type="negative")
                        return
                    answer = (result.get("answer") or "").strip()
                    if not answer:
                        ui.notify("The AI returned an empty answer.",
                                   type="warning")
                        return

                    try:
                        db.ms_chat_add(pid, uid, my_name, "question", q,
                                        {"answer": answer})
                    except Exception as ex:
                        import traceback
                        traceback.print_exc()
                        ui.notify("Could not save the answer: " + str(ex),
                                   type="negative")
                        return

                    q_input.value = ""
                    try:
                        send_btn.classes(remove="active")
                    except Exception:
                        pass
                    try:
                        ms_list.refresh()
                    except Exception:
                        pass
                    ui.run_javascript(
                        "window.scrollTo({top: document.body.scrollHeight,"
                        " behavior:'smooth'});")

                def _on_send():
                    try:
                        ui.timer(0.01, _ask, once=True)
                    except Exception:
                        pass

                send_btn.on("click", _on_send)

                def _on_input(e):
                    txt = (q_input.value or "").strip()
                    try:
                        if txt:
                            send_btn.classes(add="active")
                        else:
                            send_btn.classes(remove="active")
                    except Exception:
                        pass
                q_input.on("update:model-value", _on_input)
                q_input.on("keydown.enter", lambda _: _on_send())

            ui.label("MS Chat · answers only from the uploaded Method "
                       "Statements").classes("gem-hint")

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


def _render_ms_message(m, on_delete=None, pid=None):
    kind = (m.get("kind") or "question").lower()
    author = m.get("author") or "?"
    created = str(m.get("created_at") or "")[:16]
    body = str(m.get("body") or "")
    resp = m.get("response") or {}
    mid = m.get("id")

    with ui.element('div').classes("gem-row user"):
        with ui.element('div').style(
            "display:flex;flex-direction:column;align-items:flex-end;"
            "max-width:82%;"
        ):
            with ui.element('div').classes("gem-user"):
                ui.label(body)
            with ui.element('div').classes("gem-msg-meta"):
                ui.label(created)

    with ui.element('div').classes("gem-row ai"):
        with ui.element('div').style("width:100%;min-width:0;"):
            if kind == "question":
                answer = str(resp.get("answer") or "")
                if not answer:
                    ui.label("(No answer was saved for this question.)").style(
                        "font-size:12px;color:#808080;font-style:italic;")
                elif pid:
                    _render_answer_with_citations(answer, pid)
                else:
                    ui.label(answer).classes("gem-ai")
            else:
                _render_gem_check_card(resp)

            with ui.element('div').classes("gem-msg-meta"):
                ui.label(_t("ms_chat_kind_question") if kind == "question"
                          else _t("ms_chat_kind_check"))
                if mid:
                    def _del(did=mid):
                        db.ms_chat_delete(
                            did, _current_uid_holder.get("uid"))
                        ui.notify("Deleted.", type="positive")
                        if on_delete:
                            on_delete()
                    btn = ui.label("Delete").classes("gem-del")
                    btn.on("click", _del)


def _render_gem_check_card(resp):
    with ui.element('div').classes("gem-check-card"):
        ui.label(_t("ms_chat_check_btn")).classes("gem-check-title")

        doc_type = resp.get("doc_type") or ""
        if doc_type:
            with ui.element('div').classes("gem-kv-row"):
                ui.html("<b>Type</b> " +
                        _html_mod.escape(str(doc_type)))

        extracted = resp.get("extracted") or {}
        if extracted:
            for k, v in extracted.items():
                with ui.element('div').classes("gem-kv-row"):
                    ui.html("<b>" + _html_mod.escape(str(k)) + "</b> " +
                            _html_mod.escape(str(v)))

        checks = resp.get("checks") or []
        if checks:
            with ui.element('div').style("margin-top:10px;"):
                for c in checks:
                    v = (c.get("verdict") or "").lower()
                    vcls = ("ok" if v == "ok" else
                            "warn" if v == "warn" else "fail")
                    field = str(c.get("field") or "")
                    val = str(c.get("value") or "")
                    req = str(c.get("ms_requirement") or "")
                    cid = str(c.get("clause_id") or "")
                    note = str(c.get("note") or "")
                    with ui.element('div').classes("gem-check-row"):
                        with ui.element('div'):
                            ui.label(field).classes("gem-check-field")
                            ui.label(val).classes("gem-check-val")
                        ui.html('<span class="gem-verdict ' + vcls + '">' +
                                (v or "").upper() + '</span>')
                        if req or cid or note:
                            bits = []
                            if req:
                                bits.append("MS: " + req)
                            if cid:
                                bits.append("[S" + cid + "]")
                            if note:
                                bits.append(note)
                            ui.html('<div class="gem-check-note">' +
                                    _html_mod.escape(" · ".join(bits)) +
                                    '</div>')

        overall = (resp.get("overall") or "").lower()
        if overall:
            ocls = ("ok" if overall == "compliant" else
                    "warn" if overall == "conditional" else "fail")
            olabel = ("COMPLIANT" if overall == "compliant" else
                      "CONDITIONAL" if overall == "conditional"
                      else "NON-COMPLIANT")
            with ui.element('div').style(
                "display:flex;justify-content:space-between;"
                "align-items:center;margin-top:12px;"
                "padding-top:10px;border-top:1px solid #232426;"
            ):
                ui.label(_t("ms_chat_overall")).classes("gem-check-title")
                ui.html('<span class="gem-verdict ' + ocls + '">' +
                        olabel + '</span>')

        summary = resp.get("summary") or ""
        if summary:
            ui.label(str(summary)).style(
                "font-size:12.5px;color:#b8b8b8;"
                "margin-top:10px;line-height:1.6;")


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


# =====================================================================
# TEAM CHAT
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
            with ui.element('div').classes("gem-wrap"):
                with ui.element('div').classes("gem-empty"):
                    ui.label(_t("chat_title")).classes("gem-empty-title")
                    ui.label(_t("chat_sub")).classes("gem-empty-sub")
            return

        by_id = {m["id"]: m for m in msgs}

        with ui.element('div').classes("gem-wrap"):
            for m in msgs:
                mid = m.get("id")
                author = m.get("author") or ""
                body = m.get("body") or ""
                created_raw = m.get("created_at") or ""
                created = str(created_raw)[:16]
                reply_to = m.get("reply_to_id")
                is_mine = (str(author) == str(my_name))
                prof = _get_profile(m.get("user_id"))
                title = prof.get("title") or ""
                a_color = _chat_author_color(title)

                with ui.element('div').classes(
                    "gem-row user" if is_mine else "gem-row ai"
                ):
                    if is_mine:
                        with ui.element('div').style(
                            "display:flex;flex-direction:column;"
                            "align-items:flex-end;max-width:82%;"
                        ):
                            with ui.element('div').style(
                                "display:flex;align-items:center;gap:6px;"
                                "margin-bottom:4px;"
                            ):
                                def _open_prof_me(uid=m.get("user_id")):
                                    if uid:
                                        _open_member_profile(uid)
                                name_lbl = ui.label(author).style(
                                    "font-size:11px;font-weight:700;"
                                    "color:" + a_color + ";cursor:pointer;"
                                )
                                name_lbl.on("click", _open_prof_me)
                                if title:
                                    ui.label("· " + title).style(
                                        "font-size:10px;color:#808080;")
                                ui.label(created).classes("chat-time")

                            if reply_to and reply_to in by_id:
                                parent = by_id[reply_to]
                                ui.html(
                                    '<div class="chat-reply-quote" '
                                    'style="margin-bottom:6px;">' +
                                    '<b>' + _html_mod.escape(
                                        str(parent.get("author", ""))) +
                                    '</b>: ' +
                                    _html_mod.escape(
                                        str(parent.get("body", ""))[:80]) +
                                    '</div>'
                                )
                            with ui.element('div').classes("gem-user"):
                                ui.html(_chat_render_body(body))
                            with ui.element('div').classes("gem-msg-meta"):
                                def _reply_mine(rid=mid):
                                    fstate["reply_to"] = rid
                                    render_reply_indicator()
                                ui.label(_t("chat_reply")).classes(
                                    "gem-del").style(
                                    "cursor:pointer;color:#5a5a5a;"
                                ).on("click", _reply_mine)

                                cd = _parse_dt(created_raw)
                                remaining = 0
                                if cd:
                                    try:
                                        age = (datetime.datetime.utcnow() -
                                               cd).total_seconds()
                                        remaining = max(0, 60 - age)
                                    except Exception:
                                        remaining = 0
                                if remaining > 0:
                                    del_holder = ui.element('span')
                                    with del_holder:
                                        def _del(did=mid):
                                            ok, reason = \
                                                db.chat_delete_secure(
                                                    did, my_uid,
                                                    within_seconds=60)
                                            if ok:
                                                ui.notify(
                                                    _t("chat_deleted"),
                                                    type="positive")
                                                chat_list.refresh()
                                            elif reason == "too_late":
                                                ui.notify(
                                                    _t("delete_too_late"),
                                                    type="warning")
                                                chat_list.refresh()
                                            elif reason == "not_owner":
                                                ui.notify(
                                                    _t("delete_not_owner"),
                                                    type="warning")
                                            else:
                                                ui.notify(
                                                    _t("delete_failed"),
                                                    type="negative")
                                        ui.label(_t("chat_delete")).classes(
                                            "gem-del"
                                        ).style(
                                            "cursor:pointer;color:#5a5a5a;"
                                        ).on("click", _del)
                                    def _hide(h=del_holder):
                                        try:
                                            h.clear()
                                        except Exception:
                                            pass
                                    ui.timer(remaining, _hide, once=True)

                    else:
                        with ui.element('div').style(
                            "width:100%;min-width:0;"
                        ):
                            with ui.element('div').style(
                                "display:flex;align-items:center;gap:6px;"
                                "margin-bottom:4px;"
                            ):
                                def _open_prof(uid=m.get("user_id")):
                                    if uid:
                                        _open_member_profile(uid)
                                name_lbl = ui.label(author).style(
                                    "font-size:11px;font-weight:700;"
                                    "color:" + a_color + ";cursor:pointer;"
                                )
                                name_lbl.on("click", _open_prof)
                                if title:
                                    ui.label("· " + title).style(
                                        "font-size:10px;color:#808080;")
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

                            ui.html('<div class="gem-ai">' +
                                    _chat_render_body(body) + '</div>')

                            def _reply_other(rid=mid):
                                fstate["reply_to"] = rid
                                render_reply_indicator()
                            ui.label(_t("chat_reply")).classes(
                                "gem-del").style(
                                "cursor:pointer;color:#5a5a5a;"
                            ).on("click", _reply_other)

    with ui.element('div').classes("chat-tools"):
        def _toggle_search():
            search_box.set_visibility(not search_box.visible)
        ui.button(icon="search", on_click=_toggle_search).props(
            "round dense size=sm")

    search_box = ui.input(placeholder=_t("chat_search"),
                            on_change=_on_search).style(
        "width:100%;margin-bottom:12px;display:none;").props("dense clearable")

    chat_list()

    with ui.element('div').classes("gem-composer"):
        with ui.element('div').classes("gem-composer-inner"):
            mention_holder = ui.element('div').style(
                "position:absolute;bottom:100%;left:0;right:0;"
                "display:none;"
            )

            with ui.element('div').classes("gem-pill"):
                body_in = ui.textarea(
                    placeholder=_t("chat_placeholder")
                ).style("width:100%;").props("dense autogrow borderless")

                send_btn = ui.button(icon="arrow_upward").classes(
                    "gem-icon-btn send").props("flat round dense")

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
                    try:
                        send_btn.classes(remove="active")
                    except Exception:
                        pass
                    fstate["reply_to"] = None
                    render_reply_indicator()
                    mention_holder.style("display:none;")
                    chat_list.refresh()
                    ui.run_javascript(
                        "window.scrollTo({top: document.body.scrollHeight,"
                        " behavior:'smooth'});")

                send_btn.on("click", _send)

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
                                        "mention-item").style(
                                        "color:#5a5a5a;")
                                for a in matches:
                                    def _pick(nm=a):
                                        parts = (body_in.value or "").split()
                                        if parts and parts[-1].startswith("@"):
                                            parts[-1] = "@" + nm
                                        else:
                                            parts.append("@" + nm)
                                        body_in.value = " ".join(parts) + " "
                                        mention_holder.style("display:none;")
                                        try:
                                            send_btn.classes(add="active")
                                        except Exception:
                                            pass
                                    ui.label(a).classes("mention-item").on(
                                        "click", _pick)
                    else:
                        mention_holder.style("display:none;")

                def _on_input(e):
                    txt = (body_in.value or "").strip()
                    try:
                        if txt:
                            send_btn.classes(add="active")
                        else:
                            send_btn.classes(remove="active")
                    except Exception:
                        pass
                    _update_mentions()

                body_in.on("update:model-value", _on_input)
                body_in.on('keydown.enter', lambda _: _send())

    state.setdefault("_chat_last_id", db.chat_max_id(pid))
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
# REPORT TEMPLATES DIALOG (Feature #10)
# =====================================================================
def _open_templates_dialog(state, refresh_logs_fn):
    pid = state.get("project_id")
    if not pid:
        ui.notify(_t("setup_first"), type="warning")
        return

    try:
        db.report_template_ensure_presets(pid)
    except Exception as e:
        print("[tpl] ensure presets failed: " + repr(e))

    with ui.dialog() as dlg, ui.card().style(
        "padding:20px;min-width:340px;max-width:96vw;width:620px;"
        "max-height:92vh;overflow-y:auto;"
    ):
        ui.label("Report templates").classes("h1").style(
            "margin-bottom:4px;")
        ui.label("Presets control what appears on exported PDFs: logo, "
                  "signature block, summary table, photos.").classes(
            "mono-sm").style("margin-bottom:14px;display:block;"
                              "line-height:1.5;")

        holder = ui.element('div').style("width:100%;")

        def render_list():
            holder.clear()
            try:
                items = db.report_template_list(pid) or []
            except Exception:
                items = []
            with holder:
                if not items:
                    ui.label("No templates yet.").classes("mono-sm").style(
                        "color:#5a5a5a;padding:12px 0;")
                    return
                for t in items:
                    with ui.element('div').classes("item-box"):
                        with ui.element('div').style(
                            "display:flex;justify-content:space-between;"
                            "align-items:center;gap:8px;margin-bottom:6px;"
                        ):
                            with ui.element('div').style(
                                "display:flex;align-items:center;gap:6px;"
                            ):
                                ui.label(str(t.get("name") or "")).style(
                                    "font-size:12px;font-weight:600;"
                                    "color:#e8e8e8;")
                                if t.get("is_default"):
                                    ui.html(
                                        '<span class="badge-watch" '
                                        'style="font-size:9px;">DEFAULT</span>'
                                    )
                            with ui.element('div').style(
                                "display:flex;align-items:center;gap:4px;"
                            ):
                                def _make_default(tid=t.get("id")):
                                    db.report_template_update(
                                        tid, is_default=True)
                                    ui.notify("Default set", type="positive")
                                    render_list()
                                    refresh_logs_fn()
                                if not t.get("is_default"):
                                    ui.button("Set default",
                                              on_click=_make_default
                                    ).props("flat dense no-caps size=sm"
                                    ).style("color:#5eead4;font-size:10px;")

                                def _edit(tid=t.get("id")):
                                    _open_template_editor(
                                        state, tid, on_done=render_list,
                                        refresh_logs_fn=refresh_logs_fn)
                                ui.button("Edit", on_click=_edit).props(
                                    "flat dense no-caps size=sm").style(
                                    "color:#60a5fa;font-size:10px;")

                                def _del(tid=t.get("id"),
                                          nm=t.get("name")):
                                    db.report_template_delete(tid)
                                    ui.notify("Deleted " + str(nm),
                                              type="positive")
                                    render_list()
                                    refresh_logs_fn()
                                ui.button(icon="close", on_click=_del).props(
                                    "flat round dense size=xs").style(
                                    "color:#f87171;")

                        cfg = t.get("config") or {}
                        bits = []
                        for key, label in (
                            ("include_logo", "logo"),
                            ("include_signatures", "signatures"),
                            ("include_summary", "summary"),
                            ("include_photos", "photos"),
                        ):
                            if cfg.get(key):
                                bits.append("✓ " + label)
                            else:
                                bits.append("·  " + label)
                        ui.label("  ".join(bits)).classes("mono-sm").style(
                            "font-size:10px;color:#b8b8b8;")

        render_list()

        ui.element('div').style(
            "border-top:1px solid #1e1e1e;margin:14px 0 10px;")

        def _new_tpl():
            _open_template_editor(state, None, on_done=render_list,
                                    refresh_logs_fn=refresh_logs_fn)
        ui.button("+ New template", on_click=_new_tpl).classes(
            BTN_PRIMARY).style("width:100%;")

        with ui.element('div').style("margin-top:12px;"):
            ui.button(_t("close"), on_click=dlg.close).classes(
                BTN_SOFT).style("width:100%;")
    dlg.open()


def _open_template_editor(state, template_id=None, on_done=None,
                            refresh_logs_fn=None):
    pid = state.get("project_id")
    if not pid:
        return
    existing = None
    if template_id:
        try:
            existing = db.report_template_get(template_id)
        except Exception:
            existing = None

    default_cfg = {
        "include_logo": True,
        "include_signatures": True,
        "include_summary": True,
        "include_photos": True,
    }
    cfg = dict(default_cfg)
    if existing and isinstance(existing.get("config"), dict):
        cfg.update(existing["config"])

    title = "Edit template" if existing else "New template"
    with ui.dialog() as dlg, ui.card().style(
        "padding:20px;min-width:320px;max-width:95vw;width:460px;"
    ):
        ui.label(title).classes("h1").style("margin-bottom:14px;")

        name_in = ui.input("Template name",
                            value=(existing or {}).get("name") or "").style(
            "width:100%;")

        ui.element('div').style("height:6px;")
        logo_cb = ui.checkbox("Include project logo",
                                value=bool(cfg.get("include_logo"))).style(
            "font-size:11px;")
        sig_cb = ui.checkbox("Include signature blocks",
                               value=bool(cfg.get("include_signatures"))
                               ).style("font-size:11px;")
        sum_cb = ui.checkbox("Include summary table",
                               value=bool(cfg.get("include_summary"))
                               ).style("font-size:11px;")
        photo_cb = ui.checkbox("Include photos on notices",
                                 value=bool(cfg.get("include_photos"))
                                 ).style("font-size:11px;")
        default_cb = ui.checkbox("Make this the default",
                                   value=bool((existing or {}).get(
                                       "is_default"))).style(
            "font-size:11px;margin-top:6px;")

        def _save():
            nm = (name_in.value or "").strip()
            if not nm:
                ui.notify("Template name required.", type="warning")
                return
            new_cfg = {
                "include_logo": bool(logo_cb.value),
                "include_signatures": bool(sig_cb.value),
                "include_summary": bool(sum_cb.value),
                "include_photos": bool(photo_cb.value),
            }
            try:
                if existing:
                    db.report_template_update(
                        existing["id"], name=nm, config=new_cfg,
                        is_default=bool(default_cb.value))
                else:
                    db.report_template_add(
                        pid, nm, new_cfg,
                        is_default=bool(default_cb.value))
            except Exception as ex:
                ui.notify("Save failed: " + str(ex), type="negative")
                return
            ui.notify("Template saved.", type="positive")
            dlg.close()
            if on_done:
                try: on_done()
                except Exception: pass
            if refresh_logs_fn:
                try: refresh_logs_fn()
                except Exception: pass

        with ui.element('div').style(
            "display:flex;gap:8px;margin-top:16px;"
        ):
            ui.button(_t("save"), on_click=_save).classes(
                BTN_PRIMARY).style("flex:1;")
            ui.button(_t("cancel_btn"), on_click=dlg.close).classes(
                BTN_SOFT).style("flex:1;")
    dlg.open()


# =====================================================================
# LOGS — with Bulk actions (#7) + Templates (#10)
# =====================================================================
def _build_logs(state):
    if not state.get("project_id"):
        _render_no_project(state, state["render_main"])
        return

    sel_state = {"on": False, "picked": set()}

    try:
        db.report_template_ensure_presets(state["project_id"])
    except Exception as e:
        print("[tpl] preset ensure failed: " + repr(e))

    with ui.element('div').classes("section-head"):
        ui.label(_t("logs_title")).classes("h1")

        def _toggle_sel():
            sel_state["on"] = not sel_state["on"]
            sel_state["picked"].clear()
            log_list.refresh()
            _render_sel_btn()

        sel_btn_holder = ui.element('span')

        def _render_sel_btn():
            sel_btn_holder.clear()
            with sel_btn_holder:
                if sel_state["on"]:
                    ui.button("Cancel select", icon="close",
                              on_click=_toggle_sel).classes(BTN_SOFT).style(
                        "font-size:10px;min-height:28px;")
                else:
                    ui.button("Select", icon="checklist",
                              on_click=_toggle_sel).classes(BTN_SOFT).style(
                        "font-size:10px;min-height:28px;")

        with ui.element('div').style(
            "display:flex;align-items:center;gap:6px;"
        ):
            _render_sel_btn()

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

    fstate = {"filter": "all", "query": "", "defect_type": "all",
              "watch_only": False, "template_id": None}

    try:
        default_tpl = db.report_template_get_default(state["project_id"])
        if default_tpl:
            fstate["template_id"] = default_tpl["id"]
    except Exception:
        default_tpl = None

    def _current_template_config():
        tid = fstate.get("template_id")
        if not tid:
            return None
        try:
            t = db.report_template_get(tid)
            if t and isinstance(t.get("config"), dict):
                return t["config"]
        except Exception:
            pass
        return None

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
        if fstate.get("watch_only"):
            try:
                watched = db.watch_list_for_user(state.get("user_id"))
            except Exception:
                watched = set()
            rows = [r for r in rows if r.get("id") in watched]
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
            "display:flex;gap:6px;align-items:center;margin-bottom:8px;"
        ):
            try:
                tpls = db.report_template_list(state["project_id"]) or []
            except Exception:
                tpls = []
            if tpls:
                tpl_opts = {}
                for t in tpls:
                    lbl = t.get("name") or ("Template " + str(t.get("id")))
                    if t.get("is_default"):
                        lbl = "★ " + lbl
                    tpl_opts[t.get("id")] = lbl
                tpl_sel = ui.select(
                    tpl_opts,
                    value=fstate.get("template_id") or
                    list(tpl_opts.keys())[0],
                    label="Template",
                ).style("flex:1;").props("dense")

                def _on_tpl(e):
                    fstate["template_id"] = e.value
                tpl_sel.on("update:model-value", _on_tpl)

            def _manage():
                _open_templates_dialog(state, log_list.refresh)
            ui.button("Manage", icon="tune",
                      on_click=_manage).classes(BTN_SOFT).style(
                "font-size:10px;min-height:30px;")

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
                    logo_bytes=state["project"].get("logo_bytes"),
                    template_config=_current_template_config())
                ui.download(pdf, filename="defect_register.pdf")

            def export_closure():
                if not rows:
                    ui.notify(_t("no_rows"), type="warning")
                    return
                pdf = svc.build_closure_pdf(
                    state["project"], rows,
                    logo_bytes=state["project"].get("logo_bytes"),
                    template_config=_current_template_config())
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

        bulk_holder = ui.element('div').style("width:100%;")

        def _clear_picks():
            sel_state["picked"].clear()
            log_list.refresh()

        def _bulk_close():
            ids = list(sel_state["picked"])
            if not ids:
                return
            n = 0
            for did in ids:
                try:
                    db.close_defect(did)
                    try:
                        d = db.get_defect(did) or {}
                        db.activity_add(
                            d.get("project_id"), state["user_id"],
                            "closed_defect", target_type="defect",
                            target_id=d.get("uid") or "",
                            details="bulk close",
                            user_name=(state.get("user") or {}).get(
                                "name", ""))
                    except Exception:
                        pass
                    n += 1
                except Exception as e:
                    print("[bulk] close " + str(did) + " failed: " + repr(e))
            ui.notify(str(n) + " closed.", type="positive")
            _clear_picks()

        def _bulk_delete():
            ids = list(sel_state["picked"])
            if not ids:
                return
            _open_bulk_delete_dialog(state, ids, after=_clear_picks)

        def _bulk_reassign():
            ids = list(sel_state["picked"])
            if not ids:
                return
            _open_bulk_reassign_dialog(state, ids, after=_clear_picks)

        def _bulk_watch():
            ids = list(sel_state["picked"])
            if not ids:
                return
            n = 0
            for did in ids:
                try:
                    ok, _ = db.watch_add(did, state["user_id"])
                    if ok:
                        n += 1
                except Exception:
                    pass
            ui.notify(str(n) + " watched.", type="positive")
            _clear_picks()

        def _render_bulk_bar():
            bulk_holder.clear()
            if not sel_state["on"]:
                return
            n = len(sel_state["picked"])
            with bulk_holder:
                if n == 0:
                    ui.label("Select notices below to bulk-act.").classes(
                        "mono-sm").style(
                        "font-size:10px;color:#5a5a5a;"
                        "padding:6px 2px;display:block;")
                    return
                with ui.element('div').classes("bulk-bar"):
                    ui.label(str(n) + " selected").style(
                        "font-size:11px;font-weight:700;color:#5eead4;"
                        "align-self:center;margin-right:6px;")

                    if _can(state, "close"):
                        ui.button("Close all", icon="check",
                                  on_click=_bulk_close).classes(
                            BTN_PRIMARY).style("flex:1;")
                    if _can(state, "edit"):
                        ui.button("Reassign sub", icon="engineering",
                                  on_click=_bulk_reassign).classes(
                            BTN_SOFT).style("flex:1;")
                    if _can(state, "delete_open"):
                        ui.button("Delete all", icon="delete",
                                  on_click=_bulk_delete).classes(
                            BTN_DANGER).style("flex:1;")
                    ui.button("Watch all", icon="star",
                              on_click=_bulk_watch).classes(
                        BTN_SOFT).style("flex:1;")
                    ui.button("Clear", icon="clear_all",
                              on_click=_clear_picks).classes(
                        BTN_OUTLINE).style("flex:1;")

        _render_bulk_bar()

        for r in rows:
            _render_log_card(r, log_list.refresh, state,
                              sel_state, _render_bulk_bar)

    def _on_filter(e):
        fstate["filter"] = (e.value if e and e.value else "all")
        log_list.refresh()

    def _on_search(e):
        fstate["query"] = (e.value or "").strip().lower()
        log_list.refresh()

    def _on_dtype(e):
        fstate["defect_type"] = (e.value if e and e.value else "all")
        log_list.refresh()

    def _on_watch(e):
        fstate["watch_only"] = bool(e.value)
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

    ui.checkbox("⭐ Watching only", value=False,
                 on_change=_on_watch).style(
        "font-size:11px;color:#e8e8e8;margin-bottom:8px;")

    ui.input(placeholder=_t("search_placeholder"),
             on_change=_on_search).style(
        "width:100%;margin-bottom:12px;").props("dense clearable")

    log_list()


def _open_bulk_delete_dialog(state, defect_ids, after=None):
    with ui.dialog() as dlg, ui.card().style(
        "padding:20px;min-width:300px;max-width:95vw;width:420px;"
    ):
        ui.label("Delete " + str(len(defect_ids)) + " notices?").classes(
            "h3").style("margin-bottom:6px;")
        ui.label("This cannot be undone.").classes("muted").style(
            "margin-bottom:14px;")

        def _yes():
            n = 0
            for did in defect_ids:
                try:
                    d = db.get_defect(did) or {}
                    db.delete_defect(did)
                    try:
                        db.activity_add(
                            d.get("project_id"), state["user_id"],
                            "deleted_defect", target_type="defect",
                            target_id=d.get("uid") or "",
                            details="bulk delete",
                            user_name=(state.get("user") or {}).get(
                                "name", ""))
                    except Exception:
                        pass
                    n += 1
                except Exception as e:
                    print("[bulk] delete " + str(did) + " failed: " + repr(e))
            ui.notify(str(n) + " deleted.", type="positive")
            dlg.close()
            if after:
                try: after()
                except Exception: pass

        with ui.element('div').style("display:flex;gap:8px;"):
            ui.button("Delete all", on_click=_yes).classes(BTN_DANGER).style(
                "flex:1;")
            ui.button(_t("cancel_btn"), on_click=dlg.close).classes(BTN_SOFT)
    dlg.open()


def _open_bulk_reassign_dialog(state, defect_ids, after=None):
    pid = state.get("project_id")
    subs = []
    try:
        subs = db.list_subcontractors(pid) or []
    except Exception:
        subs = []
    opts = {"": "— choose —"}
    for s in subs:
        nm = s.get("name")
        if nm and nm not in opts:
            opts[nm] = nm
    with ui.dialog() as dlg, ui.card().style(
        "padding:20px;min-width:320px;max-width:95vw;width:440px;"
    ):
        ui.label("Reassign " + str(len(defect_ids)) + " notices").classes(
            "h3").style("margin-bottom:10px;")
        ui.label("New subcontractor:").classes("label").style(
            "display:block;margin-bottom:4px;")
        sel = ui.select(opts, value="").style("width:100%;").props("dense")
        new_in = ui.input(placeholder="or type a new name").style(
            "width:100%;margin-top:8px;")

        def _apply():
            nm = (new_in.value or "").strip() or (sel.value or "").strip()
            if not nm:
                ui.notify("Pick or type a subcontractor.", type="warning")
                return
            n = db.bulk_update_subcontractor(defect_ids, nm)
            ui.notify(str(n) + " reassigned to " + nm + ".",
                       type="positive")
            dlg.close()
            if after:
                try: after()
                except Exception: pass

        with ui.element('div').style(
            "display:flex;gap:8px;margin-top:16px;"
        ):
            ui.button("Apply", on_click=_apply).classes(
                BTN_PRIMARY).style("flex:1;")
            ui.button(_t("cancel_btn"), on_click=dlg.close).classes(
                BTN_SOFT).style("flex:1;")
    dlg.open()


def _render_log_card(row, refresh_fn, state=None, sel_state=None,
                      on_pick_change=None):
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

    try:
        n_comments = db.comment_count(row.get("id"))
    except Exception:
        n_comments = 0

    try:
        _uid = state.get("user_id") if state else None
        is_watching_card = bool(_uid and db.watch_is_watching(
            row.get("id"), _uid))
    except Exception:
        is_watching_card = False

    selection_on = bool(sel_state and sel_state.get("on"))
    is_picked = bool(sel_state and row.get("id") in sel_state.get("picked", set()))

    with ui.element('div').classes("log-row") as card:
        if selection_on:
            card.style("border-color:#5eead4;" if is_picked else "")

        with ui.element('div').style(
            "display:flex;justify-content:space-between;"
            "align-items:flex-start;gap:10px;"
        ):
            with ui.element('div').style(
                "flex:1;min-width:0;display:flex;gap:8px;"
            ):
                if selection_on:
                    def _toggle_pick(e):
                        try:
                            did = row.get("id")
                            if e.value:
                                sel_state["picked"].add(did)
                            else:
                                sel_state["picked"].discard(did)
                        except Exception:
                            pass
                        if on_pick_change:
                            try: on_pick_change()
                            except Exception: pass

                    ui.checkbox(value=is_picked,
                                 on_change=_toggle_pick).props(
                        "dense size=sm").style("align-self:flex-start;")

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

                    if n_comments > 0:
                        ui.html(
                            '<span class="badge-comment" style="margin-top:4px;'
                            'margin-left:4px;display:inline-block;">'
                            '💬 ' + str(n_comments) + '</span>'
                        )

                    if is_watching_card:
                        ui.html(
                            '<span class="badge-watch" style="margin-top:4px;'
                            'margin-left:4px;display:inline-block;">'
                            '⭐ WATCHING</span>'
                        )

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

        if not selection_on:
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

    def _current_author_name():
        if state:
            u = state.get("user") or {}
            nm = (u.get("name") or u.get("email") or "")
            if nm:
                return nm
        try:
            if user_id:
                u = db.get_user(user_id) or {}
                return (u.get("name") or u.get("email") or "user")
        except Exception:
            pass
        return "user"

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

            if user_id:
                watch_holder = ui.element('div').style(
                    "width:100%;margin-top:8px;")

                def render_watch():
                    watch_holder.clear()
                    try:
                        w = db.watch_is_watching(d["id"], user_id)
                        wc = db.watch_count(d["id"])
                    except Exception:
                        w = False
                        wc = 0
                    with watch_holder:
                        with ui.element('div').style(
                            "display:flex;align-items:center;gap:8px;"
                        ):
                            def _toggle():
                                try:
                                    if w:
                                        db.watch_remove(d["id"], user_id)
                                    else:
                                        db.watch_add(d["id"], user_id)
                                except Exception as ex:
                                    ui.notify("Watch failed: " + str(ex),
                                                type="negative")
                                    return
                                render_watch()
                                try:
                                    on_close_cb()
                                except Exception:
                                    pass

                            ui.button(
                                "⭐  Watching" if w else "☆  Watch this defect",
                                on_click=_toggle,
                            ).classes(BTN_SOFT if w else BTN_OUTLINE).style(
                                "font-size:11px;min-height:30px;")
                            if wc:
                                ui.label(str(wc) + " watcher" +
                                          ("s" if wc != 1 else "")
                                          ).classes("mono-sm").style(
                                    "font-size:9px;color:#5a5a5a;")

                render_watch()

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

            ui.element('div').style(
                "border-top:1px solid #1e1e1e;margin:14px 0 12px;")
            with ui.element('div').style(
                "display:flex;justify-content:space-between;"
                "align-items:center;margin-bottom:8px;"
            ):
                ui.label("COMMENTS").classes("label")
                try:
                    cc0 = db.comment_count(d["id"])
                except Exception:
                    cc0 = 0
                if cc0 > 0:
                    ui.html('<span style="font-size:10px;'
                            'color:#5eead4;font-weight:600;">'
                            + str(cc0) + '</span>')

            comments_holder = ui.element('div').style("width:100%;")

            def render_comments():
                comments_holder.clear()
                try:
                    items = db.comment_list(d["id"]) or []
                except Exception:
                    items = []
                with comments_holder:
                    if not items:
                        ui.label("No comments yet. Start the discussion."
                                ).classes("mono-sm").style(
                            "font-size:10px;color:#5a5a5a;"
                            "padding:6px 0;")
                    for c in items:
                        cid = c.get("id")
                        author = c.get("author") or "user"
                        body_text = c.get("body") or ""
                        when = str(c.get("created_at") or "")[:16]
                        is_mine = (user_id and
                                    c.get("user_id") == user_id)
                        is_admin_user = False
                        try:
                            is_admin_user = bool(
                                user_id and db.is_admin(user_id))
                        except Exception:
                            is_admin_user = False
                        can_del = bool(is_mine or is_admin_user)
                        with ui.element('div').classes("comment-row"):
                            with ui.element('div').style(
                                "display:flex;justify-content:space-between;"
                                "align-items:center;gap:8px;"
                            ):
                                ui.label(str(author)).classes(
                                    "comment-author")
                                with ui.element('div').style(
                                    "display:flex;align-items:center;gap:6px;"
                                ):
                                    ui.label(when).classes(
                                        "comment-time")
                                    if can_del:
                                        def _del_comment(cx=cid):
                                            ok, _reason = db.comment_delete(
                                                cx, user_id=user_id,
                                                is_admin_user=is_admin_user)
                                            if ok:
                                                render_comments()
                                            else:
                                                ui.notify(
                                                    "Could not delete "
                                                    "comment.",
                                                    type="warning")
                                        ui.button(icon="close",
                                                  on_click=_del_comment
                                        ).props(
                                            "flat round dense size=xs"
                                        ).style("color:#5a5a5a;")
                            ui.label(str(body_text)).classes("comment-body")

            render_comments()

            new_comment_in = ui.textarea(
                placeholder="Add a comment..."
            ).style("width:100%;margin-top:6px;").props("dense autogrow")

            def _post_comment():
                txt = (new_comment_in.value or "").strip()
                if not txt:
                    return
                if not user_id:
                    ui.notify("Sign in to comment.", type="warning")
                    return
                try:
                    db.comment_add(d["id"], user_id,
                                    _current_author_name(), txt)
                except Exception as ex:
                    ui.notify("Comment failed: " + str(ex),
                                type="negative")
                    return
                new_comment_in.value = ""
                render_comments()
                try:
                    on_close_cb()
                except Exception:
                    pass

            ui.button("Post comment", icon="send",
                      on_click=_post_comment).classes(BTN_SOFT).style(
                "width:100%;margin-top:6px;")

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
# ADMIN PANEL
# =====================================================================
def _build_admin(state):
    if not state.get("project_id"):
        _render_no_project(state, state["render_main"])
        return
    if not _is_admin_ui(state.get("user_id")):
        with ui.element('div').classes("card").style(
            "text-align:center;padding:32px 20px;"
        ):
            ui.icon("lock").style("font-size:28px;color:#fbbf24;")
            ui.label("Only admins can open this page.").classes(
                "muted").style("margin-top:10px;line-height:1.6;")
            ui.label("Your role: " + _role_label(state)).classes(
                "mono-sm").style("margin-top:6px;")
        return

    with ui.element('div').classes("section-head"):
        ui.label("ADMIN").classes("h1")

        def _refresh():
            state["render_main"]()
        ui.button(icon="refresh", on_click=_refresh).props(
            "flat round dense size=sm").style("color:#808080;")

    with ui.tabs().style("width:100%;margin-bottom:12px;") as atabs:
        a_audit = ui.tab("Audit Trail")
        a_users = ui.tab("Users")
        a_billing = ui.tab("Billing")

    with ui.tab_panels(atabs, value=a_audit).style("width:100%;"):
        with ui.tab_panel(a_audit):
            _build_admin_audit(state)
        with ui.tab_panel(a_users):
            _build_admin_users(state)
        with ui.tab_panel(a_billing):
            _build_admin_billing(state)


def _build_admin_audit(state):
    pid = state["project_id"]
    fstate = {"action": "all", "query": ""}

    @ui.refreshable
    def audit_list():
        try:
            rows = db.activity_list(pid, limit=500) or []
        except Exception:
            rows = []
        if fstate["action"] != "all":
            rows = [r for r in rows
                    if (r.get("action") or "") == fstate["action"]]
        if fstate["query"]:
            q = fstate["query"]

            def _match(r):
                hay = " ".join([
                    str(r.get("user_name") or ""),
                    str(r.get("action") or ""),
                    str(r.get("target_id") or ""),
                    str(r.get("details") or ""),
                ]).lower()
                return q in hay
            rows = [r for r in rows if _match(r)]

        ui.label(str(len(rows)) + " events").classes("mono-sm").style(
            "margin-bottom:10px;")
        if not rows:
            ui.label("No events match.").classes("mono-sm").style(
                "text-align:center;padding:32px 0;color:#5a5a5a;")
            return
        for r in rows:
            action = (r.get("action") or "").replace("_", " ")
            nm = r.get("user_name") or "user"
            tgt = r.get("target_id") or ""
            detail = r.get("details") or ""
            when = str(r.get("created_at") or "")[:19]
            a_raw = (r.get("action") or "").lower()
            color = "#b8b8b8"
            if "delete" in a_raw:
                color = "#f87171"
            elif "close" in a_raw:
                color = "#4ade80"
            elif "raise" in a_raw or "invite" in a_raw:
                color = "#5eead4"
            with ui.element('div').style(
                "background:#101010;border:1px solid #1e1e1e;"
                "border-radius:3px;padding:8px 10px;margin-bottom:4px;"
            ):
                with ui.element('div').style(
                    "display:flex;justify-content:space-between;"
                    "align-items:center;gap:8px;"
                ):
                    ui.label(str(nm) + "  " + action).style(
                        "font-size:11px;font-weight:600;color:" + color + ";")
                    ui.label(when).classes("mono-sm").style(
                        "font-size:9px;color:#5a5a5a;")
                if tgt:
                    ui.label("target: " + str(tgt)[:60]).classes(
                        "mono-sm").style("font-size:9px;")
                if detail:
                    ui.label(str(detail)[:120]).classes("mono-sm").style(
                        "font-size:9px;color:#808080;")

    def _on_action(e):
        fstate["action"] = (e.value if e and e.value else "all")
        audit_list.refresh()

    def _on_query(e):
        fstate["query"] = (e.value or "").strip().lower()
        audit_list.refresh()

    ui.select(
        {"all": "All actions",
         "raised_defect": "Raised defect",
         "edited_defect": "Edited defect",
         "closed_defect": "Closed defect",
         "deleted_defect": "Deleted defect",
         "invited_member": "Invited member"},
        value="all", label="Filter by action", on_change=_on_action,
    ).style("width:100%;margin-bottom:8px;").props("dense")

    ui.input(placeholder="Search user, target, details...",
             on_change=_on_query).style(
        "width:100%;margin-bottom:12px;").props("dense clearable")

    audit_list()


def _build_admin_users(state):
    my_uid = state.get("user_id")
    search_in = ui.input(placeholder="Search name, email, title...").style(
        "width:100%;margin-bottom:12px;").props("dense clearable")

    holder = ui.element('div').style("width:100%;")

    def render():
        holder.clear()
        q = (search_in.value or "").strip().lower()
        try:
            users = db.admin_list_users() or []
        except Exception as e:
            with holder:
                ui.label("Failed to load users: " + str(e)).style(
                    "color:#f87171;font-size:11px;")
            return
        if q:
            users = [u for u in users if q in (
                (u.get("name") or "") + " " +
                (u.get("email") or "") + " " +
                (u.get("title") or "")).lower()]

        with holder:
            if not users:
                ui.label("No users match.").classes("mono-sm").style(
                    "text-align:center;padding:26px 0;color:#5a5a5a;")
                return

            ui.label(str(len(users)) + " users").classes("mono-sm").style(
                "margin-bottom:10px;")

            for u in users:
                uid = u["id"]
                is_me = (uid == my_uid)
                with ui.element('div').style(
                    "background:#101010;border:1px solid #1e1e1e;"
                    "border-radius:3px;padding:10px 12px;margin-bottom:6px;"
                ):
                    with ui.element('div').style(
                        "display:flex;justify-content:space-between;"
                        "align-items:flex-start;gap:10px;"
                    ):
                        with ui.element('div').style(
                            "flex:1;min-width:0;"
                        ):
                            nm = u.get("name") or "—"
                            if is_me:
                                nm += "  (you)"
                            ui.label(nm).style(
                                "font-size:12px;font-weight:600;"
                                "color:#e8e8e8;overflow:hidden;"
                                "text-overflow:ellipsis;")
                            sub = u.get("email") or ""
                            if sub:
                                ui.label(sub).classes("mono-sm").style(
                                    "font-size:10px;")
                            meta = []
                            if u.get("title"):
                                meta.append(u["title"])
                            meta.append(str(u.get("projects") or 0) +
                                        " project(s)")
                            ui.label(" · ".join(meta)).classes(
                                "mono-sm").style(
                                "font-size:9px;color:#808080;")

                            with ui.element('div').style(
                                "margin-top:6px;display:flex;gap:4px;"
                                "flex-wrap:wrap;"
                            ):
                                if u.get("is_admin"):
                                    ui.html(
                                        '<span class="badge-role" style="'
                                        'color:#fbbf24;border:1px solid '
                                        '#fbbf2455;">ADMIN</span>')
                                if u.get("is_suspended"):
                                    ui.html(
                                        '<span class="badge-role" style="'
                                        'color:#f87171;border:1px solid '
                                        '#f8717155;">SUSPENDED</span>')

                        with ui.element('div').style(
                            "display:flex;flex-direction:column;gap:4px;"
                            "min-width:120px;"
                        ):
                            admin_flag = bool(u.get("is_admin"))
                            susp_flag = bool(u.get("is_suspended"))

                            def _toggle_admin(uid_=uid, cur=admin_flag):
                                ok, msg = db.set_admin(uid_, not cur)
                                if ok:
                                    ui.notify(
                                        "Admin " +
                                        ("removed" if cur else "granted"),
                                        type="positive")
                                    render()
                                else:
                                    ui.notify("Failed: " + str(msg),
                                              type="negative")
                            ui.button(
                                "Demote" if admin_flag else "Make admin",
                                on_click=_toggle_admin,
                            ).classes(
                                BTN_SOFT if admin_flag else BTN_PRIMARY
                            ).style("width:100%;font-size:10px;"
                                    "min-height:28px;")

                            def _toggle_susp(uid_=uid, cur=susp_flag):
                                if uid_ == my_uid and not cur:
                                    ui.notify(
                                        "You can't suspend yourself.",
                                        type="warning")
                                    return
                                ok, msg = db.set_suspended(uid_, not cur)
                                if ok:
                                    ui.notify(
                                        "Suspended" if not cur else "Active",
                                        type="positive")
                                    render()
                                else:
                                    ui.notify("Failed: " + str(msg),
                                              type="negative")
                            ui.button(
                                "Unsuspend" if susp_flag else "Suspend",
                                on_click=_toggle_susp,
                            ).classes(
                                BTN_SOFT if not susp_flag else BTN_DANGER
                            ).style("width:100%;font-size:10px;"
                                    "min-height:28px;")

    search_in.on("update:model-value", lambda e: render())
    render()


def _build_admin_billing(state):
    from services import billing_db as billing

    holder = ui.element('div').style("width:100%;")

    def render():
        holder.clear()
        try:
            owners = billing.billing_list_owners() or []
        except Exception as e:
            with holder:
                ui.label("Failed to load owners: " + str(e)).style(
                    "color:#f87171;font-size:11px;")
            return

        with holder:
            if not owners:
                ui.label("No owner accounts yet.").classes("mono-sm").style(
                    "text-align:center;padding:26px 0;color:#5a5a5a;")
                return

            ui.label(str(len(owners)) + " owner account(s)").classes(
                "mono-sm").style("margin-bottom:10px;")

            plan_opts = {"free": "Starter — 3 seats",
                         "pro":  "Pro — 15 seats",
                         "business": "Business — unlimited",
                         "trial": "Trial — 3 seats"}

            for o in owners:
                with ui.element('div').style(
                    "background:#101010;border:1px solid #1e1e1e;"
                    "border-radius:3px;padding:10px 12px;margin-bottom:6px;"
                ):
                    with ui.element('div').style(
                        "display:flex;justify-content:space-between;"
                        "align-items:flex-start;gap:10px;"
                    ):
                        with ui.element('div').style("flex:1;min-width:0;"):
                            ui.label(o.get("name") or "—").style(
                                "font-size:12px;font-weight:600;"
                                "color:#e8e8e8;overflow:hidden;"
                                "text-overflow:ellipsis;")
                            if o.get("email"):
                                ui.label(o["email"]).classes("mono-sm").style(
                                    "font-size:10px;")
                            lim = o.get("limit")
                            lim_s = "unlimited" if lim is None else str(lim)
                            col = "#4ade80"
                            if o.get("over"):
                                col = "#f87171"
                            elif lim is not None and o["used"] >= lim:
                                col = "#fbbf24"
                            ui.html(
                                '<div style="font-size:10px;color:#b8b8b8;'
                                'margin-top:4px;">Plan '
                                '<b style="color:#e8e8e8;">' +
                                _html_mod.escape(str(
                                    o.get("plan_label") or
                                    o.get("plan") or "Starter")) +
                                '</b> · Seats '
                                '<b style="color:' + col + ';">' +
                                str(o.get("used") or 0) + ' / ' + lim_s +
                                '</b></div>'
                            )

                        with ui.element('div').style(
                            "display:flex;flex-direction:column;gap:4px;"
                            "min-width:160px;"
                        ):
                            sel = ui.select(
                                plan_opts,
                                value=o.get("plan") or "free",
                                label="Plan").style("width:100%;").props(
                                "dense")

                            def _save(owner_id=o.get("owner_id"), s=sel):
                                ok, msg = billing.billing_set_plan(
                                    owner_id, s.value)
                                if ok:
                                    ui.notify("Plan updated",
                                              type="positive")
                                    render()
                                else:
                                    ui.notify("Failed: " + str(msg),
                                              type="negative")
                            ui.button("Save plan", on_click=_save).classes(
                                BTN_SOFT).style(
                                "width:100%;font-size:10px;min-height:28px;")

    render()


# =====================================================================
# INSPECTIONS — daily QC inspection plans with 3-state status
# =====================================================================
def _insp_today():
    return datetime.date.today().strftime("%Y-%m-%d")


def _maybe_auto_carry(pid):
    today = _insp_today()
    try:
        if db.inspection_table_get(pid, today):
            return
    except Exception:
        return
    try:
        prev = db.inspection_table_get_latest_before(pid, today)
    except Exception:
        prev = None
    if not prev:
        return
    prev_t = prev.get("table") or {}
    rows = prev_t.get("rows") or []
    carried = [r for r in rows
               if str(r.get("status") or "") in ("suspended", "rejected")]
    if not carried:
        return
    new_t = {"columns": prev_t.get("columns") or [], "rows": carried}
    try:
        db.inspection_table_upsert(pid, today, "",
                                    new_t, is_carried=True)
        print("[insp] auto-carried " + str(len(carried)) +
              " rows into " + today)
    except Exception as e:
        print("[insp] auto-carry failed: " + repr(e))


def _build_inspections(state):
    if not state.get("project_id"):
        _render_no_project(state, state["render_main"])
        return
    pid = state["project_id"]
    today = _insp_today()

    istate = state.setdefault("inspections", {
        "date": today,
        "edit_mode": False,
        "dirty": False,
        "table_data": None,
        "source_filename": "",
        "has_loaded": False,
    })

    if istate.get("date") == today:
        _maybe_auto_carry(pid)

    if not istate.get("has_loaded") or \
            istate.get("loaded_date") != istate["date"]:
        row = db.inspection_table_get(pid, istate["date"])
        if row:
            istate["table_data"] = row.get("table") or {}
            istate["source_filename"] = row.get("source_filename") or ""
        else:
            istate["table_data"] = None
            istate["source_filename"] = ""
        istate["has_loaded"] = True
        istate["loaded_date"] = istate["date"]
        istate["dirty"] = False
        istate["edit_mode"] = False

    can_edit = _can(state, "edit") or _can(state, "raise")

    with ui.element('div').classes("section-head"):
        ui.label("INSPECTIONS").classes("h1")

        if istate.get("table_data") and can_edit:
            def _toggle_edit():
                istate["edit_mode"] = not istate["edit_mode"]
                state["render_main"]()
            icon = "edit_off" if istate["edit_mode"] else "edit"
            ui.button(icon=icon, on_click=_toggle_edit).props(
                "flat round dense size=sm").style(
                "color:#5eead4;" if istate["edit_mode"] else "color:#808080;"
            ).tooltip("Edit table")

        def _refresh():
            istate["has_loaded"] = False
            state["render_main"]()
        ui.button(icon="refresh", on_click=_refresh).props(
            "flat round dense size=sm").style("color:#808080;")

    ui.label(
        "Upload a daily quality inspection plan (PDF / JPG / PNG). "
        "The AI extracts it as a table. Mark each inspection Accepted, "
        "Suspended or Rejected."
    ).classes("muted").style("margin-bottom:12px;line-height:1.6;")

    with ui.element('div').style(
        "display:flex;gap:8px;align-items:center;margin-bottom:12px;"
    ):
        ui.label("Date:").style(
            "font-size:11px;color:#b8b8b8;font-weight:600;")

        def _on_date(e):
            new_d = (e.value or today).strip() or today
            if new_d == istate["date"]:
                return
            istate["date"] = new_d
            istate["has_loaded"] = False
            istate["edit_mode"] = False
            istate["dirty"] = False
            state["render_main"]()

        date_in = ui.input(value=istate["date"],
                            on_change=_on_date).props(
            "dense type=date").style("flex:1;")

    if istate.get("dirty") and istate.get("table_data") and can_edit:
        def _do_save():
            tdata = istate["table_data"] or {}
            try:
                db.inspection_table_upsert(
                    pid, istate["date"],
                    istate.get("source_filename") or "",
                    tdata, is_carried=False)
                istate["dirty"] = False
                ui.notify("Saved.", type="positive")
                try:
                    db.activity_add(
                        pid, state.get("user_id"), "inspection_saved",
                        target_type="inspection_table",
                        target_id=istate["date"],
                        details=str(len(tdata.get("rows") or [])) +
                                " rows",
                        user_name=(state.get("user") or {}).get("name", ""))
                except Exception:
                    pass
            except Exception as ex:
                import traceback
                traceback.print_exc()
                ui.notify("Save failed: " + str(ex), type="negative")
                return
            state["render_main"]()
        ui.button("Save changes", icon="save", on_click=_do_save).classes(
            BTN_PRIMARY).style("width:100%;margin-bottom:12px;")

    upload_holder = ui.element('div').style("width:100%;margin-bottom:12px;")
    upload_status = ui.label("").classes("mono-sm").style(
        "margin-top:6px;display:block;min-height:16px;")

    async def _process_upload(data, filename):
        upload_status.set_text("Extracting table from " +
                                filename + "…")
        upload_status.style(
            "margin-top:6px;display:block;min-height:16px;"
            "color:#fbbf24;font-size:10px;")
        try:
            result = await ins.extract_inspection_table(
                data, filename, _ocr_handwriting, call_gemini_json)
        except Exception as ex:
            import traceback
            traceback.print_exc()
            result = {"error": "Extract failed: " + repr(ex)}

        if result.get("error"):
            upload_status.set_text("Failed: " + str(result["error"]))
            upload_status.style(
                "margin-top:6px;display:block;min-height:16px;"
                "color:#f87171;font-size:10px;")
            return

        new_rows = result.get("rows") or []
        new_cols = result.get("columns") or []
        if not new_rows or not new_cols:
            upload_status.set_text("No table found in the file.")
            upload_status.style(
                "margin-top:6px;display:block;min-height:16px;"
                "color:#f87171;font-size:10px;")
            return

        existing = istate.get("table_data")
        if existing and (existing.get("rows") or []):
            _open_add_or_replace_dialog(
                state, istate, new_cols, new_rows, filename,
                upload_status)
            return

        new_t = {"columns": new_cols,
                 "rows": [{"cells": [str(c) for c in r],
                            "status": "", "note": "",
                            "defect_uid": ""} for r in new_rows]}
        try:
            db.inspection_table_upsert(
                pid, istate["date"], filename, new_t, is_carried=False)
            istate["table_data"] = new_t
            istate["source_filename"] = filename
            istate["has_loaded"] = True
            istate["loaded_date"] = istate["date"]
            istate["edit_mode"] = True
            ui.notify("Table extracted.", type="positive")
        except Exception as ex:
            ui.notify("Save failed: " + str(ex), type="negative")
            return
        upload_status.set_text("")
        state["render_main"]()

    async def _on_upload(e):
        try:
            data = await e.file.read()
        except Exception as ex:
            ui.notify("Read failed: " + str(ex), type="negative")
            return
        filename = e.file.name or "upload"
        await _process_upload(data, filename)

    with upload_holder:
        ui.upload(on_upload=_on_upload, auto_upload=True).style(
            "width:100%;").props(
            "flat bordered accept=.pdf,.jpg,.jpeg,.png,.docx,.txt "
            "label='Upload inspection plan (PDF / JPG / PNG)'")
        upload_status

    tdata = istate.get("table_data")
    if not tdata:
        with ui.element('div').classes("card").style(
            "text-align:center;padding:32px 20px;"
        ):
            ui.icon("checklist").style(
                "font-size:32px;color:#5a5a5a;")
            ui.label("No inspection plan for " + istate["date"]).style(
                "font-size:13px;color:#b8b8b8;margin-top:12px;")
            ui.label(
                "Upload a plan above, or pick a different date."
            ).classes("mono-sm").style("margin-top:6px;")
        return

    columns = list(tdata.get("columns") or [])
    rows = list(tdata.get("rows") or [])
    if not columns:
        ui.label("Table has no columns.").classes("muted")
        return

    grid_template = ("grid-template-columns: " +
                      " ".join(["minmax(80px,1fr)"] * len(columns)) +
                      " 40px 40px 40px 60px;")

    with ui.element('div').style(
        "background:#0e0e0e;border:1px solid #1e1e1e;border-radius:6px;"
        "overflow:hidden;margin-bottom:12px;"
    ):
        with ui.element('div').style(
            "display:grid;" + grid_template +
            "gap:1px;background:#1e1e1e;"
        ):
            for c in columns:
                ui.label(str(c)).style(
                    "padding:8px 10px;background:#0a0a0a;"
                    "font-size:11px;font-weight:700;color:#5eead4;"
                    "letter-spacing:0.02em;text-transform:uppercase;"
                    "word-break:break-word;")
            for h, col in (("Acc", "#4ade80"),
                            ("Sus", "#fbbf24"),
                            ("Rej", "#f87171")):
                ui.label(h).style(
                    "padding:8px 4px;background:#0a0a0a;text-align:center;"
                    "font-size:10px;font-weight:700;color:" + col + ";")
            ui.label("Note").style(
                "padding:8px 10px;background:#0a0a0a;"
                "font-size:10px;font-weight:700;color:#808080;")

            for ridx, r in enumerate(rows):
                cells = list(r.get("cells") or [])
                if len(cells) < len(columns):
                    cells = cells + [""] * (len(columns) - len(cells))
                elif len(cells) > len(columns):
                    cells = cells[:len(columns)]

                for cidx, cellv in enumerate(cells):
                    if istate["edit_mode"] and can_edit:
                        def _on_cell_change(e, ri=ridx, ci=cidx):
                            try:
                                istate["table_data"]["rows"][ri]["cells"][ci] = \
                                    str(e.value or "")
                                istate["dirty"] = True
                            except Exception:
                                pass
                        ui.input(value=str(cellv),
                                  on_change=_on_cell_change).props(
                            "dense borderless").style(
                            "background:#101010;padding:0;min-height:34px;"
                            "font-size:11px;color:#e8e8e8;")
                    else:
                        ui.label(str(cellv)).style(
                            "padding:8px 10px;background:#101010;"
                            "font-size:11px;color:#d0d0d0;"
                            "word-break:break-word;")

                cur_status = str(r.get("status") or "")
                for sval, scolor in (("accepted", "#4ade80"),
                                      ("suspended", "#fbbf24"),
                                      ("rejected", "#f87171")):
                    active = (cur_status == sval)
                    box = ui.element('div').style(
                        "background:" +
                        (scolor if active else "#101010") +
                        ";border:1px solid " +
                        (scolor if active else "#2a2a2a") +
                        ";border-radius:4px;width:22px;height:22px;"
                        "margin:6px auto;cursor:" +
                        ("pointer" if (can_edit and istate["edit_mode"])
                         else "default") + ";")

                    def _on_box_click(sv=sval, ri=ridx, act=active):
                        if not (can_edit and istate["edit_mode"]):
                            return
                        if act:
                            return
                        if sv in ("suspended", "rejected"):
                            _open_insp_defect_dialog(state, istate, ri, sv)
                        else:
                            _set_insp_status(state, istate, ri, sv)
                    box.on("click", _on_box_click)

                note_txt = str(r.get("note") or "")
                if istate["edit_mode"] and can_edit:
                    def _on_note_change(e, ri=ridx):
                        try:
                            istate["table_data"]["rows"][ri]["note"] = \
                                str(e.value or "")
                            istate["dirty"] = True
                        except Exception:
                            pass
                    ui.input(value=note_txt,
                              on_change=_on_note_change).props(
                        "dense borderless").style(
                        "background:#101010;padding:0;min-height:34px;"
                        "font-size:11px;color:#e8e8e8;")
                else:
                    ui.label(note_txt).style(
                        "padding:8px 10px;background:#101010;"
                        "font-size:10.5px;color:#b8b8b8;"
                        "word-break:break-word;")

    def _download_pdf():
        try:
            proj = db.get_project(pid) or {}
            pdf = ins.build_inspection_pdf(
                proj, istate["date"], istate["table_data"] or {})
            ui.download(pdf,
                        filename="inspection_" + istate["date"] + ".pdf")
        except Exception as ex:
            import traceback
            traceback.print_exc()
            ui.notify("PDF failed: " + str(ex), type="negative")

    ui.button("Download day " + istate["date"] + " as PDF",
              icon="picture_as_pdf",
              on_click=_download_pdf).classes(BTN_SOFT).style(
        "width:100%;margin-top:4px;")


def _set_insp_status(state, istate, row_idx, status):
    try:
        istate["table_data"]["rows"][row_idx]["status"] = status
        istate["dirty"] = True
    except Exception:
        pass
    state["render_main"]()


def _open_insp_defect_dialog(state, istate, row_idx, status):
    tdata = istate.get("table_data") or {}
    rows = tdata.get("rows") or []
    row = rows[row_idx] if row_idx < len(rows) else {}
    cells = list(row.get("cells") or [])
    cols = list(tdata.get("columns") or [])

    def _find_col(*keys):
        for i, c in enumerate(cols):
            lc = str(c).lower()
            for k in keys:
                if k in lc:
                    return i
        return -1

    floor_i = _find_col("floor", "level", "story")
    insp_i = _find_col("inspection", "activity", "item", "task")
    loc_i = _find_col("location", "place", "area", "zone")
    spec_i = _find_col("spec", "code", "reference", "standard")

    floor_v = cells[floor_i] if 0 <= floor_i < len(cells) else ""
    insp_v = cells[insp_i] if 0 <= insp_i < len(cells) else ""
    if not insp_v:
        insp_v = cells[0] if cells else "Inspection"
    loc_v = cells[loc_i] if 0 <= loc_i < len(cells) else ""
    spec_v = cells[spec_i] if 0 <= spec_i < len(cells) else ""

    project = db.get_project(state["project_id"]) or {}
    default_sub = project.get("subcontractor") or ""
    default_eng = (state.get("user") or {}).get("name") or \
                  project.get("engineer_name") or ""

    with ui.dialog() as dlg, ui.card().style(
        "padding:22px;min-width:340px;max-width:96vw;width:540px;"
        "max-height:92vh;overflow-y:auto;"
    ):
        ui.label("Defect properties").classes("h1").style(
            "margin-bottom:4px;")
        ui.label("This " + status.upper() + " inspection will be logged "
                  "as a defect.").classes("muted").style(
            "margin-bottom:14px;")

        ui.label("Inspection").classes("label").style(
            "display:block;margin-bottom:3px;")
        ui.label(str(insp_v)).style(
            "font-size:12px;font-weight:600;color:#e8e8e8;"
            "margin-bottom:10px;")

        sub_in = ui.input("Subcontractor", value=default_sub).style(
            "width:100%;")
        zone_in = ui.input("Zone / Floor", value=str(floor_v)).style(
            "width:100%;")
        place_in = ui.input("Place of the defect",
                              value=str(loc_v)).style("width:100%;")
        sev_in = ui.select(_severity_options(), value="Medium",
                            label="Severity").style("width:100%;")
        with ui.element('div').style(
            "display:grid;grid-template-columns:1fr 1fr;gap:8px;"
        ):
            deadline_in = ui.select(
                {"1": "1 day", "2": "2 days", "3": "3 days",
                 "5": "5 days", "7": "7 days", "14": "14 days"},
                value="3", label="Deadline")
            engineer_in = ui.input("Engineer name",
                                     value=default_eng)
        nature_in = ui.textarea(
            "Defect nature / comment",
            value=str(row.get("note") or "")
        ).style("width:100%;margin-top:8px;").props("dense autogrow")

        def _confirm():
            note = (nature_in.value or "").strip()
            if not note:
                ui.notify("Enter the defect nature / comment.",
                           type="warning")
                return
            if not sub_in.value.strip():
                ui.notify("Enter the subcontractor.", type="warning")
                return

            uid = svc.generate_uid("INS")
            selected = [{
                "name": str(insp_v)[:120] or "Inspection defect",
                "location_hint": str(place_in.value or loc_v)[:60],
                "severity": sev_in.value or "Medium",
                "ms_violations": [],
                "code_violations": ([str(spec_v)]
                                     if str(spec_v).strip() else []),
                "repair_action": "",
                "zone": str(zone_in.value or floor_v or "General"),
                "context_mismatch": True,
            }]
            try:
                db.save_defect(
                    project_id=state["project_id"], uid=uid,
                    zone=str(zone_in.value or floor_v or "General"),
                    subcontractor=sub_in.value.strip(),
                    deadline_days=int(deadline_in.value),
                    raise_type="qc_internal",
                    photo_bytes=None,
                    note=note,
                    selected=selected,
                    notice_pdf=None,
                    engineer_name=engineer_in.value or "",
                    place=str(place_in.value or loc_v or ""),
                    defect_type="General",
                )
            except Exception as ex:
                import traceback
                traceback.print_exc()
                ui.notify("Defect creation failed: " + str(ex),
                           type="negative")
                return

            try:
                db.activity_add(
                    state["project_id"], state.get("user_id"),
                    "inspection_" + status,
                    target_type="defect", target_id=uid,
                    details=str(insp_v)[:80],
                    user_name=(state.get("user") or {}).get("name", ""))
            except Exception:
                pass

            try:
                istate["table_data"]["rows"][row_idx]["status"] = status
                istate["table_data"]["rows"][row_idx]["note"] = note
                istate["table_data"]["rows"][row_idx]["defect_uid"] = uid
                istate["dirty"] = True
            except Exception:
                pass
            ui.notify("Defect " + uid + " created.", type="positive")
            dlg.close()
            state["render_main"]()

        def _cancel():
            dlg.close()

        with ui.element('div').style(
            "display:flex;gap:8px;margin-top:16px;"
        ):
            ui.button("Confirm", icon="check",
                      on_click=_confirm).classes(BTN_PRIMARY).style(
                "flex:1;")
            ui.button("Cancel", on_click=_cancel).classes(BTN_SOFT).style(
                "flex:1;")
    dlg.open()


def _open_add_or_replace_dialog(state, istate, new_cols, new_rows,
                                  filename, upload_status):
    pid = state["project_id"]
    existing = istate.get("table_data") or {}

    def _apply_add():
        merged = ins.merge_tables(existing, new_rows)
        try:
            db.inspection_table_upsert(
                pid, istate["date"], filename, merged,
                is_carried=False)
            istate["table_data"] = merged
            istate["source_filename"] = filename
            istate["has_loaded"] = True
            istate["loaded_date"] = istate["date"]
            istate["edit_mode"] = True
            ui.notify("Added " + str(merged.get("added", 0)) +
                       " new inspection(s).", type="positive")
        except Exception as ex:
            ui.notify("Save failed: " + str(ex), type="negative")
            return
        dlg.close()
        state["render_main"]()

    def _apply_replace():
        new_t = {"columns": new_cols,
                 "rows": [{"cells": [str(c) for c in r],
                            "status": "", "note": "",
                            "defect_uid": ""} for r in new_rows]}
        try:
            db.inspection_table_upsert(
                pid, istate["date"], filename, new_t,
                is_carried=False)
            istate["table_data"] = new_t
            istate["source_filename"] = filename
            istate["has_loaded"] = True
            istate["loaded_date"] = istate["date"]
            istate["edit_mode"] = True
            ui.notify("Replaced with new table.", type="positive")
        except Exception as ex:
            ui.notify("Save failed: " + str(ex), type="negative")
            return
        dlg.close()
        state["render_main"]()

    with ui.dialog() as dlg, ui.card().style(
        "padding:22px;min-width:320px;max-width:96vw;width:520px;"
    ):
        ui.label("A table already exists for " + istate["date"]).classes(
            "h1").style("margin-bottom:6px;")
        ui.label(
            "Choose how to combine the newly uploaded plan with the "
            "existing table for this date."
        ).classes("mono-sm").style(
            "line-height:1.6;color:#b8b8b8;margin-bottom:14px;")

        ui.label("Existing: " +
                  str(len((existing.get("rows") or []))) +
                  " rows").classes("mono-sm").style(
            "color:#b8b8b8;font-size:11px;")
        ui.label("New upload: " + str(len(new_rows)) +
                  " rows").classes("mono-sm").style(
            "color:#b8b8b8;font-size:11px;margin-bottom:12px;")

        with ui.element('div').style(
            "display:flex;flex-direction:column;gap:8px;"
        ):
            ui.button("Add to existing", icon="add",
                      on_click=_apply_add).classes(BTN_PRIMARY).style(
                "width:100%;")
            ui.button("Create new and replace existing", icon="swap_horiz",
                      on_click=_apply_replace).classes(BTN_DANGER).style(
                "width:100%;")
            ui.button("Cancel", on_click=dlg.close).classes(
                BTN_SOFT).style("width:100%;")
    dlg.open()
