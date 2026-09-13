"""
ui/admin_page.py — Internal admin panel.
Accessible only to users with is_admin=1 OR matching ADMIN_EMAIL env var.
"""
import os
from nicegui import ui, app

from services import billing_db as bdb
from services import defect_db as db
from services import auth_service as auth


ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "").strip().lower()

STYLE = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Amiri:wght@400;700&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #0b0b0b; --surface: #101010; --surface-2: #161616;
    --border: #1e1e1e; --border-2: #262626;
    --text: #e8e8e8; --muted: #808080; --muted-2: #5a5a5a;
    --accent: #5eead4; --accent-dim: #14b8a6;
    --warn: #fbbf24; --success: #4ade80; --danger: #f87171;
  }
  html, body {
    background: var(--bg) !important; color: var(--text) !important;
    font-family: 'JetBrains Mono','Courier New',monospace !important;
    margin: 0; padding: 0;
  }
  .nicegui-content { padding: 0 !important; }
  .q-page, .q-layout { background: var(--bg) !important; }
  .q-btn { border-radius: 3px !important; text-transform: none !important;
           font-family: 'JetBrains Mono',monospace !important;
           font-size: 11px !important; min-height: 30px !important;
           box-shadow: none !important; }
  .btn-primary { background: var(--accent) !important;
                 color: #0b0b0b !important; font-weight: 700 !important; }
  .btn-soft { background: var(--surface-2) !important;
              color: var(--text) !important;
              border: 1px solid var(--border-2) !important; }
  .hdr {
    background: rgba(11,11,11,0.94); backdrop-filter: blur(10px);
    border-bottom: 1px solid var(--border); padding: 12px 20px;
    display: flex; align-items: center; justify-content: space-between;
  }
  .hdr .brand { font-weight: 700; font-size: 12px; color: var(--text); }
  .hdr .brand::before { content: '▲ '; color: var(--accent);
                        font-size: 9px; margin-right: 4px; }
  .main { padding: 20px; max-width: 1100px; margin: 0 auto; }
  .metric-strip {
    display: grid; grid-template-columns: repeat(3, 1fr);
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 4px; overflow: hidden; margin-bottom: 20px;
  }
  .metric-cell { padding: 16px; border-right: 1px solid var(--border);
                 border-bottom: 1px solid var(--border); }
  .metric-cell:nth-child(3n) { border-right: none; }
  .metric-cell:nth-last-child(-n+3) { border-bottom: none; }
  .metric-label {
    font-size: 9px; font-weight: 700; color: var(--muted-2);
    letter-spacing: 0.14em; text-transform: uppercase;
    margin-bottom: 4px;
  }
  .metric-value {
    font-size: 22px; font-weight: 700; letter-spacing: -0.03em;
    color: var(--text); line-height: 1.1;
    font-variant-numeric: tabular-nums;
  }
  .metric-value.accent { color: var(--accent); }
  .metric-value.success { color: var(--success); }
  .metric-value.warn { color: var(--warn); }
  .section { margin-bottom: 28px; }
  .section h2 {
    font-size: 14px; font-weight: 700; margin: 0 0 12px;
    letter-spacing: -0.02em;
  }
  table {
    width: 100%; border-collapse: collapse;
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 4px; overflow: hidden;
    font-size: 11px; font-variant-numeric: tabular-nums;
  }
  thead { background: #0a0a0a; }
  th {
    text-align: left; padding: 8px 10px; font-size: 9px;
    font-weight: 700; letter-spacing: 0.14em;
    color: var(--muted-2); text-transform: uppercase;
    border-bottom: 1px solid var(--border);
  }
  td {
    padding: 8px 10px; color: var(--text);
    border-bottom: 1px solid var(--border);
  }
  tr:last-child td { border-bottom: none; }
  tr:hover td { background: #141414; }
  .pill {
    display: inline-block; font-size: 9px; font-weight: 700;
    letter-spacing: 0.06em; padding: 2px 6px; border-radius: 2px;
    text-transform: uppercase;
  }
  .pill.free { color: var(--muted); border: 1px solid var(--border-2); }
  .pill.trial { color: var(--warn); border: 1px solid rgba(251,191,36,0.35); }
  .pill.pro { color: var(--accent); border: 1px solid rgba(94,234,212,0.3); }
  .pill.business { color: var(--success);
                   border: 1px solid rgba(74,222,128,0.35); }
  .pill.expired { color: var(--danger);
                  border: 1px solid rgba(248,113,113,0.35); }
  .muted { color: var(--muted); font-size: 10px; }
</style>
"""


def _is_admin(user_id):
    if not user_id:
        return False
    if ADMIN_EMAIL:
        u = db.get_user(user_id)
        if u and (u.get("email") or "").lower() == ADMIN_EMAIL:
            return True
    # Also allow is_admin flag
    try:
        c = bdb._conn()
        cur = c.cursor()
        cur.execute("SELECT is_admin FROM users WHERE id=?", (user_id,))
        row = cur.fetchone()
        c.close()
        if row:
            try:
                return bool(int(row[0] if not isinstance(row, dict)
                                else row.get("is_admin") or 0))
            except Exception:
                return False
    except Exception:
        pass
    return False


def admin_page(user_id):
    ui.add_head_html(STYLE)

    if not _is_admin(user_id):
        with ui.column().classes("w-full min-h-screen items-center "
                                  "justify-center"):
            ui.label("Access denied.").style(
                "color:#f87171;font-size:14px;font-family:'JetBrains "
                "Mono',monospace;")
            ui.button("Home", on_click=lambda: ui.navigate.to("/app")).style(
                "background:#5eead4;color:#0b0b0b;font-weight:700;"
                "border-radius:3px;padding:0 20px;min-height:36px;"
                "font-size:11px;text-transform:none;margin-top:14px;")
        return

    with ui.element('div').classes("hdr"):
        ui.label("ADMIN · DEFECT NOTICES").classes("brand")
        with ui.element('div').style("display:flex;gap:8px;"):
            ui.button("Open app", on_click=lambda: ui.navigate.to("/app")
                      ).classes("btn-soft")
            ui.button("Log out", on_click=lambda: ui.navigate.to("/logout")
                      ).classes("btn-soft")

    with ui.element('div').classes("main"):
        stats = bdb.admin_stats()

        with ui.element('div').classes("metric-strip"):
            _mc("USERS TOTAL", stats.get("users_total", 0), "")
            _mc("ON TRIAL", stats.get("users_trial", 0), "warn")
            _mc("PAID", stats.get("users_paid", 0), "success")
            _mc("PROJECTS", stats.get("projects_total", 0), "")
            _mc("DEFECTS", stats.get("defects_total", 0), "")
            _mc("REVENUE 30D", str(round(stats.get("revenue_30d", 0), 0)),
                 "accent")

        # Users table
        with ui.element('div').classes("section"):
            ui.html("<h2>Users</h2>")
            users = bdb.admin_user_list(limit=200)
            if not users:
                ui.label("No users yet.").classes("muted")
            else:
                html = "<table><thead><tr>"
                for h in ["ID", "EMAIL", "NAME", "PLAN", "PROJECTS",
                          "DEFECTS", "TRIAL ENDS", "SUB EXPIRES"]:
                    html += "<th>" + h + "</th>"
                html += "</tr></thead><tbody>"
                for u in users:
                    plan = (u.get("plan") or "free").lower()
                    exp = u.get("plan_expires_at") or ""
                    trial_end = u.get("trial_ends_at") or ""
                    pill_cls = plan
                    if plan == "trial" and trial_end:
                        # check expired
                        import datetime
                        try:
                            end_dt = datetime.datetime.strptime(
                                trial_end[:19], "%Y-%m-%d %H:%M:%S")
                            if datetime.datetime.utcnow() > end_dt:
                                pill_cls = "expired"
                        except Exception:
                            pass
                    html += "<tr>"
                    html += ("<td>" + str(u.get("id", "")) + "</td>")
                    html += ("<td>" + str(u.get("email", "")) + "</td>")
                    html += ("<td>" + str(u.get("name", "")) + "</td>")
                    html += ('<td><span class="pill ' + pill_cls + '">' +
                              plan + "</span></td>")
                    html += ("<td>" + str(u.get("projects_count", 0)) +
                              "</td>")
                    html += ("<td>" + str(u.get("defects_count", 0)) +
                              "</td>")
                    html += ("<td>" + (trial_end[:16] if trial_end else "-") +
                              "</td>")
                    html += ("<td>" + (exp[:16] if exp else "-") + "</td>")
                    html += "</tr>"
                html += "</tbody></table>"
                ui.html(html)

        # Recent payments
        with ui.element('div').classes("section"):
            ui.html("<h2>Recent payments</h2>")
            pays = bdb.admin_recent_payments(limit=50)
            if not pays:
                ui.label("No payments yet.").classes("muted")
            else:
                html = "<table><thead><tr>"
                for h in ["ID", "USER", "PLAN", "AMOUNT", "CURRENCY",
                          "PROVIDER", "STATUS", "DATE"]:
                    html += "<th>" + h + "</th>"
                html += "</tr></thead><tbody>"
                for p in pays:
                    html += "<tr>"
                    html += ("<td>" + str(p.get("id", "")) + "</td>")
                    html += ("<td>" +
                              str(p.get("email") or p.get("user_id", "")) +
                              "</td>")
                    html += ("<td>" + str(p.get("plan", "")) + "</td>")
                    html += ("<td>" + str(p.get("amount", "")) + "</td>")
                    html += ("<td>" + str(p.get("currency", "")) + "</td>")
                    html += ("<td>" + str(p.get("provider", "")) + "</td>")
                    html += ("<td>" + str(p.get("status", "")) + "</td>")
                    html += ("<td>" +
                              str(p.get("created_at", ""))[:16] + "</td>")
                    html += "</tr>"
                html += "</tbody></table>"
                ui.html(html)


def _mc(label, value, variant):
    with ui.element('div').classes("metric-cell"):
        ui.label(str(label)).classes("metric-label")
        cls = "metric-value"
        if variant:
            cls += " " + variant
        ui.label(str(value)).classes(cls)
