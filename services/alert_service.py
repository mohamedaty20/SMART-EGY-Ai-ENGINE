"""
services/alert_service.py — Overdue detection + optional email alerts.

Email sending activates when one of these env vars is set:
  RESEND_API_KEY       (recommended, free tier)
  SENDGRID_API_KEY     (alternative)
Set ALERT_FROM_EMAIL to your sender address (must be verified).
"""
import os
import json
import urllib.request

from services import defect_db as db


RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "").strip()
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY", "").strip()
ALERT_FROM_EMAIL = os.environ.get("ALERT_FROM_EMAIL",
                                    "notifications@defectnotices.app").strip()


def email_available():
    return bool(RESEND_API_KEY or SENDGRID_API_KEY)


def get_overdue(project_id, min_days_overdue=1):
    """Return list of open defects whose deadline has passed."""
    import datetime
    now = datetime.datetime.utcnow()
    rows = db.list_defects(project_id)
    out = []
    for r in rows:
        if r.get("status") != "open":
            continue
        created = r.get("created_at")
        dl = int(r.get("deadline_days") or 3)
        try:
            cd = datetime.datetime.strptime(created[:19],
                                             "%Y-%m-%d %H:%M:%S")
            days = (now - cd).days
            overdue = days - dl
            if overdue >= min_days_overdue:
                r["_days_open"] = days
                r["_days_overdue"] = overdue
                out.append(r)
        except Exception:
            pass
    out.sort(key=lambda x: -x.get("_days_overdue", 0))
    return out


def count_overdue(project_id):
    try:
        return len(get_overdue(project_id, min_days_overdue=1))
    except Exception:
        return 0


# =====================================================================
# EMAIL SEND (optional)
# =====================================================================
def _send_resend(to_email, subject, html):
    payload = {
        "from": ALERT_FROM_EMAIL,
        "to": [to_email],
        "subject": subject,
        "html": html,
    }
    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": "Bearer " + RESEND_API_KEY,
            "Content-Type": "application/json",
        },
        method="POST")
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.status in (200, 201, 202)


def _send_sendgrid(to_email, subject, html):
    payload = {
        "personalizations": [{"to": [{"email": to_email}]}],
        "from": {"email": ALERT_FROM_EMAIL},
        "subject": subject,
        "content": [{"type": "text/html", "value": html}],
    }
    req = urllib.request.Request(
        "https://api.sendgrid.com/v3/mail/send",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": "Bearer " + SENDGRID_API_KEY,
            "Content-Type": "application/json",
        },
        method="POST")
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.status in (200, 201, 202)


def send_overdue_email(to_email, project_name, overdue_items):
    """Fire-and-forget summary email. Returns True if sent."""
    if not email_available():
        return False
    rows_html = ""
    for r in overdue_items[:20]:
        rows_html += (
            "<tr>"
            "<td style='padding:6px;border-bottom:1px solid #eee;"
            "font-family:monospace;font-size:12px;'>" +
            str(r.get("uid", "")) + "</td>"
            "<td style='padding:6px;border-bottom:1px solid #eee;"
            "font-family:monospace;font-size:12px;'>" +
            str(r.get("first_defect", "")) + "</td>"
            "<td style='padding:6px;border-bottom:1px solid #eee;"
            "font-family:monospace;font-size:12px;'>" +
            str(r.get("subcontractor", "")) + "</td>"
            "<td style='padding:6px;border-bottom:1px solid #eee;"
            "font-family:monospace;font-size:12px;color:#c00;'>" +
            str(r.get("_days_overdue", 0)) + "d</td>"
            "</tr>"
        )
    html = (
        "<div style='font-family:monospace;color:#111;max-width:600px;'>"
        "<h2 style='color:#0a0a0a;'>Overdue defects — " +
        str(project_name) + "</h2>"
        "<p style='color:#555;font-size:13px;'>" +
        str(len(overdue_items)) + " defect(s) past deadline.</p>"
        "<table style='width:100%;border-collapse:collapse;'>"
        "<thead><tr style='background:#0a0a0a;color:#fff;"
        "text-align:left;'>"
        "<th style='padding:8px;font-size:11px;'>UID</th>"
        "<th style='padding:8px;font-size:11px;'>DEFECT</th>"
        "<th style='padding:8px;font-size:11px;'>SUB</th>"
        "<th style='padding:8px;font-size:11px;'>OVERDUE</th>"
        "</tr></thead>"
        "<tbody>" + rows_html + "</tbody>"
        "</table>"
        "<p style='color:#888;font-size:11px;margin-top:20px;'>"
        "Open the app to review and close them.</p>"
        "</div>"
    )
    subject = ("Overdue defects — " + str(project_name) + " (" +
               str(len(overdue_items)) + ")")
    try:
        if RESEND_API_KEY:
            return _send_resend(to_email, subject, html)
        if SENDGRID_API_KEY:
            return _send_sendgrid(to_email, subject, html)
    except Exception as e:
        print("[alert] email failed: " + repr(e))
    return False
