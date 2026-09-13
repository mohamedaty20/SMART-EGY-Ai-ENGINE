"""
services/defect_db.py — SQLite layer.
"""
import os
import json
import sqlite3
import datetime
import threading

DB_PATH = os.environ.get("DEFECT_DB_PATH", "defects.db")
_LOCK = threading.Lock()


def _conn():
    c = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=10)
    c.row_factory = sqlite3.Row
    return c


def _now():
    return datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def _ensure_columns(cur, table, wanted):
    cur.execute("PRAGMA table_info(" + table + ")")
    have = {r[1] for r in cur.fetchall()}
    for name, ddl in wanted:
        if name not in have:
            try:
                cur.execute("ALTER TABLE " + table + " ADD COLUMN " +
                            name + " " + ddl)
                print("[db] added column " + table + "." + name)
            except Exception as e:
                print("[db] add column failed: " + repr(e))


def init_db():
    with _LOCK:
        c = _conn()
        cur = c.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                contractor TEXT,
                subcontractor TEXT,
                consultant TEXT,
                location TEXT,
                engineer_name TEXT,
                logo_bytes BLOB,
                created_at TEXT
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS method_statements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                ms_number TEXT,
                title TEXT,
                element_type TEXT,
                discipline TEXT,
                pdf_bytes BLOB,
                clauses_json TEXT,
                created_at TEXT
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS defects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                uid TEXT,
                zone TEXT,
                photo_bytes BLOB,
                note TEXT,
                ai_candidates_json TEXT,
                selected_json TEXT,
                subcontractor TEXT,
                deadline_days INTEGER,
                raise_type TEXT,
                status TEXT,
                created_at TEXT,
                closed_at TEXT,
                notice_pdf BLOB,
                consultant_ncr TEXT
            )
        """)

        _ensure_columns(cur, "projects", [
            ("subcontractor", "TEXT"),
        ])
        _ensure_columns(cur, "defects", [
            ("raise_type", "TEXT"),
            ("closed_at", "TEXT"),
            ("notice_pdf", "BLOB"),
            ("consultant_ncr", "TEXT"),
        ])

        c.commit()
        c.close()


init_db()


# =====================================================================
# PROJECTS
# =====================================================================
def save_project(name, contractor, consultant, location,
                 engineer_name, logo_bytes=None, subcontractor=None):
    with _LOCK:
        c = _conn()
        cur = c.cursor()
        cur.execute("SELECT id, subcontractor FROM projects "
                    "ORDER BY id LIMIT 1")
        row = cur.fetchone()
        if row:
            sub = (subcontractor if subcontractor is not None
                   else (row["subcontractor"] or ""))
            cur.execute("""
                UPDATE projects
                SET name=?, contractor=?, consultant=?, location=?,
                    engineer_name=?, logo_bytes=?, subcontractor=?
                WHERE id=?
            """, (name, contractor, consultant, location,
                  engineer_name, logo_bytes, sub, row["id"]))
            pid = row["id"]
        else:
            cur.execute("""
                INSERT INTO projects
                    (name, contractor, subcontractor, consultant, location,
                     engineer_name, logo_bytes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (name, contractor, subcontractor or "", consultant,
                  location, engineer_name, logo_bytes, _now()))
            pid = cur.lastrowid
        c.commit()
        c.close()
        return pid


def save_subcontractor(name):
    with _LOCK:
        c = _conn()
        cur = c.cursor()
        cur.execute("SELECT id FROM projects ORDER BY id LIMIT 1")
        row = cur.fetchone()
        if row:
            cur.execute("UPDATE projects SET subcontractor=? WHERE id=?",
                        (name, row["id"]))
            c.commit()
        c.close()


def get_project():
    c = _conn()
    cur = c.cursor()
    cur.execute("SELECT * FROM projects ORDER BY id LIMIT 1")
    row = cur.fetchone()
    c.close()
    if not row:
        return None
    return dict(row)


# =====================================================================
# METHOD STATEMENTS
# =====================================================================
def save_ms(project_id, ms_number, title, element_type, discipline,
            pdf_bytes, clauses):
    with _LOCK:
        c = _conn()
        cur = c.cursor()
        cur.execute("""
            INSERT INTO method_statements
                (project_id, ms_number, title, element_type, discipline,
                 pdf_bytes, clauses_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (project_id, ms_number, title, element_type, discipline,
              pdf_bytes, json.dumps(clauses), _now()))
        c.commit()
        c.close()


def list_ms(project_id):
    c = _conn()
    cur = c.cursor()
    cur.execute("""
        SELECT id, ms_number, title, element_type, discipline, clauses_json
        FROM method_statements WHERE project_id=? ORDER BY id DESC
    """, (project_id,))
    rows = cur.fetchall()
    c.close()
    out = []
    for r in rows:
        try:
            clauses = json.loads(r["clauses_json"] or "[]")
        except Exception:
            clauses = []
        out.append({
            "id": r["id"],
            "ms_number": r["ms_number"],
            "title": r["title"],
            "element_type": r["element_type"],
            "discipline": r["discipline"],
            "clauses": clauses,
        })
    return out


def get_clauses_for_element(project_id, element_type):
    c = _conn()
    cur = c.cursor()
    cur.execute("""
        SELECT clauses_json FROM method_statements
        WHERE project_id=? AND LOWER(element_type)=LOWER(?)
    """, (project_id, element_type))
    rows = cur.fetchall()
    if not rows:
        cur.execute("""
            SELECT clauses_json FROM method_statements
            WHERE project_id=?
        """, (project_id,))
        rows = cur.fetchall()
    c.close()
    clauses = []
    for r in rows:
        try:
            clauses.extend(json.loads(r["clauses_json"] or "[]"))
        except Exception:
            pass
    return clauses


# =====================================================================
# DEFECTS
# =====================================================================
def save_defect(project_id, uid, zone, subcontractor, deadline_days,
                raise_type, photo_bytes, note, selected, notice_pdf,
                ai_candidates=None):
    with _LOCK:
        c = _conn()
        cur = c.cursor()
        cur.execute("""
            INSERT INTO defects
                (project_id, uid, zone, photo_bytes, note,
                 ai_candidates_json, selected_json, subcontractor,
                 deadline_days, raise_type, status, created_at,
                 notice_pdf)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'open', ?, ?)
        """, (
            project_id, uid, zone, photo_bytes, note,
            json.dumps(ai_candidates or []),
            json.dumps(selected or []),
            subcontractor, int(deadline_days or 3),
            raise_type or "qc_internal",
            _now(),
            notice_pdf,
        ))
        c.commit()
        c.close()


def list_defects(project_id, raise_filter=None):
    c = _conn()
    cur = c.cursor()
    if raise_filter in ("qc_internal", "consultant"):
        cur.execute("""
            SELECT id, uid, zone, subcontractor, status, created_at,
                   closed_at, raise_type, selected_json
            FROM defects
            WHERE project_id=? AND COALESCE(raise_type,'qc_internal')=?
            ORDER BY id DESC
        """, (project_id, raise_filter))
    else:
        cur.execute("""
            SELECT id, uid, zone, subcontractor, status, created_at,
                   closed_at, raise_type, selected_json
            FROM defects
            WHERE project_id=?
            ORDER BY id DESC
        """, (project_id,))
    rows = cur.fetchall()
    c.close()
    out = []
    for r in rows:
        try:
            sel = json.loads(r["selected_json"] or "[]")
        except Exception:
            sel = []
        first_name = ""
        if sel:
            first_name = str(sel[0].get("name", ""))[:100]
        out.append({
            "id": r["id"],
            "uid": r["uid"],
            "zone": r["zone"],
            "subcontractor": r["subcontractor"],
            "status": r["status"],
            "created_at": r["created_at"],
            "closed_at": r["closed_at"],
            "raise_type": r["raise_type"] or "qc_internal",
            "count": len(sel),
            "first_defect": first_name,
        })
    return out


def get_defect(defect_id):
    c = _conn()
    cur = c.cursor()
    cur.execute("SELECT * FROM defects WHERE id=?", (defect_id,))
    r = cur.fetchone()
    c.close()
    if not r:
        return None
    d = dict(r)
    try:
        d["selected"] = json.loads(d.get("selected_json") or "[]")
    except Exception:
        d["selected"] = []
    try:
        d["ai_candidates"] = json.loads(d.get("ai_candidates_json") or "[]")
    except Exception:
        d["ai_candidates"] = []
    return d


def close_defect(defect_id, consultant_ncr=None):
    with _LOCK:
        c = _conn()
        cur = c.cursor()
        if consultant_ncr:
            cur.execute("""
                UPDATE defects
                SET status='closed', closed_at=?, consultant_ncr=?
                WHERE id=?
            """, (_now(), consultant_ncr, defect_id))
        else:
            cur.execute("""
                UPDATE defects
                SET status='closed', closed_at=?
                WHERE id=?
            """, (_now(), defect_id))
        c.commit()
        c.close()
