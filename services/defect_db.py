"""
services/defect_db.py

SQLite persistence for the defect tool. Four tables, no more.

Tables:
    projects             -- one row, filled once during setup
    method_statements    -- one row per uploaded MS PDF
    defects              -- one row per defect notice generated
    (notices are stored inside defects.notice_pdf)
"""

import sqlite3
import json
from datetime import datetime
from contextlib import contextmanager
from config import DB_PATH


# =====================================================================
# CONNECTION + SCHEMA
# =====================================================================
@contextmanager
def _conn():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def _init_db():
    with _conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, contractor TEXT, consultant TEXT,
            location TEXT, engineer_name TEXT,
            logo_bytes BLOB,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS method_statements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            ms_number TEXT, title TEXT,
            element_type TEXT, discipline TEXT,
            pdf_bytes BLOB,
            clauses_json TEXT,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS defects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            uid TEXT UNIQUE,
            zone TEXT, subcontractor TEXT,
            deadline_days INTEGER,
            raise_type TEXT,
            photo_bytes BLOB,
            note TEXT,
            selected_json TEXT,
            status TEXT DEFAULT 'open',
            notice_pdf BLOB,
            created_at TEXT,
            closed_at TEXT
        );
        """)


_init_db()


# =====================================================================
# PROJECTS
# =====================================================================
def save_project(name, contractor, consultant, location,
                 engineer_name, logo_bytes=None):
    with _conn() as c:
        # Only one project for the MVP. Replace if one already exists.
        c.execute("DELETE FROM projects")
        cur = c.execute(
            "INSERT INTO projects (name, contractor, consultant, location,"
            " engineer_name, logo_bytes, created_at)"
            " VALUES (?,?,?,?,?,?,?)",
            (name, contractor, consultant, location, engineer_name,
             logo_bytes, datetime.utcnow().isoformat())
        )
        return cur.lastrowid


def get_project():
    with _conn() as c:
        row = c.execute(
            "SELECT id, name, contractor, consultant, location,"
            " engineer_name, logo_bytes FROM projects LIMIT 1"
        ).fetchone()
    if not row:
        return None
    return {
        "id": row[0], "name": row[1], "contractor": row[2],
        "consultant": row[3], "location": row[4],
        "engineer_name": row[5], "logo_bytes": row[6],
    }


# =====================================================================
# METHOD STATEMENTS
# =====================================================================
def save_ms(project_id, ms_number, title, element_type, discipline,
            pdf_bytes, clauses):
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO method_statements (project_id, ms_number, title,"
            " element_type, discipline, pdf_bytes, clauses_json, created_at)"
            " VALUES (?,?,?,?,?,?,?,?)",
            (project_id, ms_number, title, element_type, discipline,
             pdf_bytes, json.dumps(clauses),
             datetime.utcnow().isoformat())
        )
        return cur.lastrowid


def list_ms(project_id=1):
    with _conn() as c:
        rows = c.execute(
            "SELECT id, ms_number, title, element_type, discipline,"
            " clauses_json FROM method_statements"
            " WHERE project_id=? ORDER BY id DESC", (project_id,)
        ).fetchall()
    out = []
    for r in rows:
        out.append({
            "id": r[0], "ms_number": r[1], "title": r[2],
            "element_type": r[3], "discipline": r[4],
            "clauses": json.loads(r[5] or "[]"),
        })
    return out


def get_clauses_for_element(project_id, element_type):
    """Return all clauses from MSs whose element matches."""
    with _conn() as c:
        rows = c.execute(
            "SELECT ms_number, clauses_json FROM method_statements"
            " WHERE project_id=? AND element_type=?",
            (project_id, element_type)
        ).fetchall()
    out = []
    for ms_num, cj in rows:
        for cl in json.loads(cj or "[]"):
            cl2 = dict(cl)
            cl2["ms_number"] = ms_num
            out.append(cl2)
    return out


# =====================================================================
# DEFECTS
# =====================================================================
def save_defect(project_id, uid, zone, subcontractor, deadline_days,
                raise_type, photo_bytes, note, selected, notice_pdf):
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO defects (project_id, uid, zone, subcontractor,"
            " deadline_days, raise_type, photo_bytes, note, selected_json,"
            " notice_pdf, created_at)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (project_id, uid, zone, subcontractor, deadline_days,
             raise_type, photo_bytes, note, json.dumps(selected),
             notice_pdf, datetime.utcnow().isoformat())
        )
        return cur.lastrowid


def list_defects(project_id=1):
    with _conn() as c:
        rows = c.execute(
            "SELECT id, uid, zone, subcontractor, status,"
            " selected_json, created_at FROM defects"
            " WHERE project_id=? ORDER BY id DESC", (project_id,)
        ).fetchall()
    out = []
    for r in rows:
        selected = json.loads(r[5] or "[]")
        out.append({
            "id": r[0], "uid": r[1], "zone": r[2],
            "subcontractor": r[3], "status": r[4],
            "count": len(selected),
            "created_at": r[6],
        })
    return out


def get_defect(defect_id):
    with _conn() as c:
        row = c.execute(
            "SELECT id, project_id, uid, zone, subcontractor,"
            " deadline_days, raise_type, photo_bytes, note,"
            " selected_json, status, notice_pdf, created_at, closed_at"
            " FROM defects WHERE id=?", (defect_id,)
        ).fetchone()
    if not row:
        return None
    d = {
        "id": row[0], "project_id": row[1], "uid": row[2],
        "zone": row[3], "subcontractor": row[4],
        "deadline_days": row[5], "raise_type": row[6],
        "photo_bytes": row[7], "note": row[8],
        "selected": json.loads(row[9] or "[]"),
        "status": row[10], "notice_pdf": row[11],
        "created_at": row[12], "closed_at": row[13],
    }
    return d


def close_defect(defect_id):
    with _conn() as c:
        c.execute(
            "UPDATE defects SET status='closed', closed_at=?"
            " WHERE id=?",
            (datetime.utcnow().isoformat(), defect_id)
        )
