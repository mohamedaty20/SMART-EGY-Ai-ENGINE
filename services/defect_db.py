"""
services/defect_db.py — Thread-local connections. Adds defect_type.
"""
import os
import re
import time
import json
import base64
import sqlite3
import datetime
import threading

DB_PATH = os.environ.get("DEFECT_DB_PATH", "defects.db")
TURSO_URL = os.environ.get("TURSO_URL", "").strip()
TURSO_TOKEN = os.environ.get("TURSO_TOKEN", "").strip()
LOCAL_CACHE = "/tmp/defects_cache.db"

_LOCK = threading.Lock()
_LIST_CACHE = {}
_LIST_CACHE_LOCK = threading.Lock()
_LAST_SYNC = [0.0]
_TL = threading.local()


def _bump_list_cache():
    with _LIST_CACHE_LOCK:
        _LIST_CACHE.clear()


def _now():
    return datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def _use_turso():
    return bool(TURSO_URL and TURSO_TOKEN)


def _conn():
    """One connection per thread, reused. No close() calls elsewhere."""
    c = getattr(_TL, "c", None)
    if c is not None:
        return c
    if _use_turso():
        try:
            import libsql
            try:
                c = libsql.connect(LOCAL_CACHE, sync_url=TURSO_URL,
                                    auth_token=TURSO_TOKEN)
            except TypeError:
                c = libsql.connect(database=LOCAL_CACHE,
                                    sync_url=TURSO_URL,
                                    auth_token=TURSO_TOKEN)
            try:
                c.sync()
                _LAST_SYNC[0] = time.time()
            except Exception:
                pass
            _TL.c = c
            return c
        except Exception as e:
            print("[db] Turso failed: " + repr(e))
    c = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=10)
    _TL.c = c
    return c


def _sync(c):
    try:
        c.sync()
        _LAST_SYNC[0] = time.time()
    except Exception:
        pass


def _to_dicts(rows, cols):
    out = []
    for r in rows:
        if r is None:
            continue
        if isinstance(r, dict):
            out.append(r)
            continue
        d = {}
        for i, name in enumerate(cols):
            try:
                d[name] = r[i]
            except Exception:
                d[name] = None
        out.append(d)
    return out


def _to_dict(row, cols):
    if row is None:
        return None
    if isinstance(row, dict):
        return row
    d = {}
    for i, name in enumerate(cols):
        try:
            d[name] = row[i]
        except Exception:
            d[name] = None
    return d


def _encode_photos(photos):
    if not photos:
        return None
    try:
        return json.dumps([base64.b64encode(p).decode("ascii")
                            for p in photos])
    except Exception:
        return None


def _decode_photos(json_str):
    if not json_str:
        return []
    try:
        arr = json.loads(json_str)
        out = []
        for s in arr:
            try:
                out.append(base64.b64decode(s))
            except Exception:
                pass
        return out
    except Exception:
        return []


USER_COLS = ["id", "email", "password_hash", "name", "title",
             "photo_bytes", "created_at"]

PROJECT_COLS = ["id", "user_id", "name", "contractor", "subcontractor",
                "consultant", "location", "engineer_name",
                "logo_bytes", "created_at"]

MS_LIST_COLS = ["id", "ms_number", "title", "element_type", "discipline",
                "clauses_json"]

DEFECT_LIST_COLS = ["id", "uid", "zone", "subcontractor", "status",
                    "created_at", "closed_at", "raise_type",
                    "selected_json", "deadline_days",
                    "engineer_name", "place", "defect_type"]

DEFECT_FULL_COLS = ["id", "project_id", "uid", "zone", "photo_bytes",
                    "note", "ai_candidates_json", "selected_json",
                    "subcontractor", "deadline_days", "raise_type",
                    "status", "created_at", "closed_at", "notice_pdf",
                    "consultant_ncr", "closure_photo", "photos_json",
                    "engineer_name", "place", "defect_type"]

SUB_COLS = ["id", "name", "trade", "phone", "notes"]

CHAT_COLS = ["id", "project_id", "user_id", "author", "body",
             "reply_to_id", "mentions", "created_at"]


def _ensure_columns(cur, table, wanted):
    cur.execute("PRAGMA table_info(" + table + ")")
    have = set()
    for r in cur.fetchall():
        try:
            if isinstance(r, dict):
                have.add(r.get("name"))
            else:
                have.add(r[1])
        except Exception:
            pass
    for name, ddl in wanted:
        if name not in have:
            try:
                cur.execute("ALTER TABLE " + table + " ADD COLUMN " +
                            name + " " + ddl)
                print("[db] added " + table + "." + name)
            except Exception as e:
                print("[db] add col failed: " + repr(e))


def init_db():
    with _LOCK:
        c = _conn()
        cur = c.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE, password_hash TEXT, name TEXT,
                title TEXT, photo_bytes BLOB, created_at TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
                name TEXT, contractor TEXT, subcontractor TEXT,
                consultant TEXT, location TEXT, engineer_name TEXT,
                logo_bytes BLOB, created_at TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS method_statements (
                id INTEGER PRIMARY KEY AUTOINCREMENT, project_id INTEGER,
                ms_number TEXT, title TEXT, element_type TEXT,
                discipline TEXT, pdf_bytes BLOB, clauses_json TEXT,
                created_at TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS defects (
                id INTEGER PRIMARY KEY AUTOINCREMENT, project_id INTEGER,
                uid TEXT, zone TEXT, photo_bytes BLOB, note TEXT,
                ai_candidates_json TEXT, selected_json TEXT,
                subcontractor TEXT, deadline_days INTEGER,
                raise_type TEXT, status TEXT, created_at TEXT,
                closed_at TEXT, notice_pdf BLOB, consultant_ncr TEXT,
                closure_photo BLOB, photos_json TEXT,
                engineer_name TEXT, place TEXT, defect_type TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS subcontractors (
                id INTEGER PRIMARY KEY AUTOINCREMENT, project_id INTEGER,
                name TEXT, trade TEXT, phone TEXT, notes TEXT,
                created_at TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER, user_id INTEGER, author TEXT,
                body TEXT, reply_to_id INTEGER, mentions TEXT,
                created_at TEXT
            )
        """)

        _ensure_columns(cur, "users", [
            ("title", "TEXT"), ("photo_bytes", "BLOB"),
        ])
        _ensure_columns(cur, "projects", [
            ("user_id", "INTEGER"), ("subcontractor", "TEXT"),
        ])
        _ensure_columns(cur, "defects", [
            ("raise_type", "TEXT"), ("closed_at", "TEXT"),
            ("notice_pdf", "BLOB"), ("consultant_ncr", "TEXT"),
            ("closure_photo", "BLOB"), ("photos_json", "TEXT"),
            ("engineer_name", "TEXT"), ("place", "TEXT"),
            ("defect_type", "TEXT"),
        ])

        for idx in [
            "CREATE INDEX IF NOT EXISTS idx_defects_project "
            "ON defects(project_id)",
            "CREATE INDEX IF NOT EXISTS idx_ms_project "
            "ON method_statements(project_id)",
            "CREATE INDEX IF NOT EXISTS idx_subs_project "
            "ON subcontractors(project_id)",
            "CREATE INDEX IF NOT EXISTS idx_chat_project "
            "ON chat_messages(project_id)",
        ]:
            try:
                cur.execute(idx)
            except Exception:
                pass

        c.commit()
        _sync(c)
        print("[db] init — turso=" + str(_use_turso()))


init_db()


# =====================================================================
# USERS
# =====================================================================
def create_user(email, password_hash, name):
    email = (email or "").strip().lower()
    with _LOCK:
        c = _conn()
        cur = c.cursor()
        cur.execute("SELECT id FROM users WHERE LOWER(email)=?", (email,))
        if cur.fetchone():
            return None, "Email already registered."
        cur.execute("""
            INSERT INTO users (email, password_hash, name, created_at)
            VALUES (?, ?, ?, ?)
        """, (email, password_hash, name, _now()))
        uid = cur.lastrowid
        cur.execute("SELECT COUNT(*) FROM users")
        row = cur.fetchone()
        count = row[0] if row else 1
        if count == 1:
            cur.execute("UPDATE projects SET user_id=? WHERE user_id IS NULL",
                        (uid,))
        c.commit()
        _sync(c)
        return uid, None


def get_user_by_email(email):
    c = _conn()
    cur = c.cursor()
    cur.execute("""
        SELECT id, email, password_hash, name, title, photo_bytes,
               created_at
        FROM users WHERE LOWER(email)=?
    """, ((email or "").strip().lower(),))
    row = cur.fetchone()
    return _to_dict(row, USER_COLS)


def get_user(user_id):
    c = _conn()
    cur = c.cursor()
    cur.execute("""
        SELECT id, email, password_hash, name, title, photo_bytes,
               created_at
        FROM users WHERE id=?
    """, (user_id,))
    row = cur.fetchone()
    return _to_dict(row, USER_COLS)


def update_user_password(user_id, password_hash):
    with _LOCK:
        c = _conn()
        cur = c.cursor()
        cur.execute("UPDATE users SET password_hash=? WHERE id=?",
                    (password_hash, user_id))
        c.commit()
        _sync(c)


def update_user_profile(user_id, name, title, photo_bytes=None):
    with _LOCK:
        c = _conn()
        cur = c.cursor()
        if photo_bytes is not None:
            cur.execute("""
                UPDATE users SET name=?, title=?, photo_bytes=? WHERE id=?
            """, (name, title, photo_bytes, user_id))
        else:
            cur.execute("UPDATE users SET name=?, title=? WHERE id=?",
                        (name, title, user_id))
        c.commit()
        _sync(c)


# =====================================================================
# PROJECTS
# =====================================================================
def list_projects(user_id):
    c = _conn()
    cur = c.cursor()
    cur.execute("""
        SELECT id, user_id, name, contractor, subcontractor, consultant,
               location, engineer_name, logo_bytes, created_at
        FROM projects WHERE user_id=? ORDER BY id DESC
    """, (user_id,))
    return _to_dicts(cur.fetchall(), PROJECT_COLS)


def create_project(user_id, name, contractor="", subcontractor="",
                   consultant="", location="", engineer_name="",
                   logo_bytes=None):
    with _LOCK:
        c = _conn()
        cur = c.cursor()
        cur.execute("""
            INSERT INTO projects
                (user_id, name, contractor, subcontractor, consultant,
                 location, engineer_name, logo_bytes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, name, contractor, subcontractor, consultant,
              location, engineer_name, logo_bytes, _now()))
        pid = cur.lastrowid
        c.commit()
        _sync(c)
        return pid


def update_project(project_id, name, contractor="", subcontractor="",
                   consultant="", location="", engineer_name="",
                   logo_bytes=None):
    with _LOCK:
        c = _conn()
        cur = c.cursor()
        cur.execute("""
            UPDATE projects
            SET name=?, contractor=?, subcontractor=?, consultant=?,
                location=?, engineer_name=?, logo_bytes=?
            WHERE id=?
        """, (name, contractor, subcontractor, consultant,
              location, engineer_name, logo_bytes, project_id))
        c.commit()
        _sync(c)


def delete_project(project_id):
    with _LOCK:
        c = _conn()
        cur = c.cursor()
        cur.execute("DELETE FROM method_statements WHERE project_id=?",
                    (project_id,))
        cur.execute("DELETE FROM defects WHERE project_id=?", (project_id,))
        cur.execute("DELETE FROM subcontractors WHERE project_id=?",
                    (project_id,))
        cur.execute("DELETE FROM chat_messages WHERE project_id=?",
                    (project_id,))
        cur.execute("DELETE FROM projects WHERE id=?", (project_id,))
        c.commit()
        _sync(c)


def get_project(project_id):
    c = _conn()
    cur = c.cursor()
    cur.execute("""
        SELECT id, user_id, name, contractor, subcontractor, consultant,
               location, engineer_name, logo_bytes, created_at
        FROM projects WHERE id=?
    """, (project_id,))
    return _to_dict(cur.fetchone(), PROJECT_COLS)


# =====================================================================
# MS
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
        _sync(c)


def list_ms(project_id):
    c = _conn()
    cur = c.cursor()
    cur.execute("""
        SELECT id, ms_number, title, element_type, discipline, clauses_json
        FROM method_statements WHERE project_id=? ORDER BY id DESC
    """, (project_id,))
    rows = _to_dicts(cur.fetchall(), MS_LIST_COLS)
    out = []
    for r in rows:
        try:
            clauses = json.loads(r.get("clauses_json") or "[]")
        except Exception:
            clauses = []
        out.append({
            "id": r.get("id"), "ms_number": r.get("ms_number"),
            "title": r.get("title"), "element_type": r.get("element_type"),
            "discipline": r.get("discipline"), "clauses": clauses,
        })
    return out


def get_clauses_for_element(project_id, element_type=None):
    """Return all clauses for the project. element_type is ignored now."""
    c = _conn()
    cur = c.cursor()
    cur.execute("SELECT clauses_json FROM method_statements "
                "WHERE project_id=?", (project_id,))
    rows = _to_dicts(cur.fetchall(), ["clauses_json"])
    clauses = []
    for r in rows:
        try:
            clauses.extend(json.loads(r.get("clauses_json") or "[]"))
        except Exception:
            pass
    return clauses


# =====================================================================
# DEFECTS
# =====================================================================
def save_defect(project_id, uid, zone, subcontractor, deadline_days,
                raise_type, photo_bytes, note, selected, notice_pdf,
                ai_candidates=None, extra_photos=None,
                engineer_name=None, place=None, defect_type=None):
    _bump_list_cache()
    with _LOCK:
        c = _conn()
        cur = c.cursor()
        cur.execute("""
            INSERT INTO defects
                (project_id, uid, zone, photo_bytes, note,
                 ai_candidates_json, selected_json, subcontractor,
                 deadline_days, raise_type, status, created_at,
                 notice_pdf, photos_json, engineer_name, place, defect_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'open', ?, ?, ?, ?, ?, ?)
        """, (project_id, uid, zone, photo_bytes, note,
              json.dumps(ai_candidates or []),
              json.dumps(selected or []),
              subcontractor, int(deadline_days or 3),
              raise_type or "qc_internal", _now(), notice_pdf,
              _encode_photos(extra_photos),
              engineer_name or "", place or "", defect_type or ""))
        c.commit()
        _sync(c)


def list_defects(project_id, raise_filter=None):
    _ck = (project_id, raise_filter)
    with _LIST_CACHE_LOCK:
        if _ck in _LIST_CACHE:
            return _LIST_CACHE[_ck]
    c = _conn()
    cur = c.cursor()
    if raise_filter in ("qc_internal", "consultant"):
        cur.execute("""
            SELECT id, uid, zone, subcontractor, status, created_at,
                   closed_at, raise_type, selected_json, deadline_days,
                   engineer_name, place, defect_type
            FROM defects
            WHERE project_id=? AND COALESCE(raise_type,'qc_internal')=?
            ORDER BY id DESC
        """, (project_id, raise_filter))
    else:
        cur.execute("""
            SELECT id, uid, zone, subcontractor, status, created_at,
                   closed_at, raise_type, selected_json, deadline_days,
                   engineer_name, place, defect_type
            FROM defects WHERE project_id=? ORDER BY id DESC
        """, (project_id,))
    raw = _to_dicts(cur.fetchall(), DEFECT_LIST_COLS)
    out = []
    for r in raw:
        try:
            sel = json.loads(r.get("selected_json") or "[]")
        except Exception:
            sel = []
        first_name = str(sel[0].get("name", ""))[:100] if sel else ""
        out.append({
            "id": r.get("id"), "uid": r.get("uid"), "zone": r.get("zone"),
            "subcontractor": r.get("subcontractor"),
            "status": r.get("status"),
            "created_at": r.get("created_at"),
            "closed_at": r.get("closed_at"),
            "raise_type": r.get("raise_type") or "qc_internal",
            "count": len(sel), "first_defect": first_name,
            "deadline_days": r.get("deadline_days") or 3,
            "selected": sel,
            "engineer_name": r.get("engineer_name") or "",
            "place": r.get("place") or "",
            "defect_type": r.get("defect_type") or "",
        })
    with _LIST_CACHE_LOCK:
        _LIST_CACHE[_ck] = out
    return out


def get_defect(defect_id):
    c = _conn()
    cur = c.cursor()
    cur.execute("""
        SELECT id, project_id, uid, zone, photo_bytes, note,
               ai_candidates_json, selected_json, subcontractor,
               deadline_days, raise_type, status, created_at,
               closed_at, notice_pdf, consultant_ncr, closure_photo,
               photos_json, engineer_name, place, defect_type
        FROM defects WHERE id=?
    """, (defect_id,))
    row = cur.fetchone()
    d = _to_dict(row, DEFECT_FULL_COLS)
    if not d:
        return None
    try:
        d["selected"] = json.loads(d.get("selected_json") or "[]")
    except Exception:
        d["selected"] = []
    try:
        d["ai_candidates"] = json.loads(d.get("ai_candidates_json") or "[]")
    except Exception:
        d["ai_candidates"] = []
    d["extra_photos"] = _decode_photos(d.get("photos_json"))
    return d


def close_defect(defect_id, consultant_ncr=None, closure_photo=None):
    _bump_list_cache()
    with _LOCK:
        c = _conn()
        cur = c.cursor()
        if consultant_ncr and closure_photo is not None:
            cur.execute("""
                UPDATE defects SET status='closed', closed_at=?,
                    consultant_ncr=?, closure_photo=? WHERE id=?
            """, (_now(), consultant_ncr, closure_photo, defect_id))
        elif consultant_ncr:
            cur.execute("""
                UPDATE defects SET status='closed', closed_at=?,
                    consultant_ncr=? WHERE id=?
            """, (_now(), consultant_ncr, defect_id))
        elif closure_photo is not None:
            cur.execute("""
                UPDATE defects SET status='closed', closed_at=?,
                    closure_photo=? WHERE id=?
            """, (_now(), closure_photo, defect_id))
        else:
            cur.execute("""
                UPDATE defects SET status='closed', closed_at=? WHERE id=?
            """, (_now(), defect_id))
        c.commit()
        _sync(c)


def update_defect_notice(defect_id, subcontractor, deadline_days, zone,
                          note, raise_type, selected, notice_pdf,
                          consultant_ncr=None, extra_photos=None,
                          engineer_name=None, place=None, defect_type=None):
    _bump_list_cache()
    with _LOCK:
        c = _conn()
        cur = c.cursor()
        photos_json = None
        if extra_photos is not None:
            photos_json = _encode_photos(extra_photos)
        if consultant_ncr:
            cur.execute("""
                UPDATE defects
                SET subcontractor=?, deadline_days=?, zone=?, note=?,
                    raise_type=?, selected_json=?, notice_pdf=?,
                    consultant_ncr=?, photos_json=?,
                    engineer_name=COALESCE(?, engineer_name),
                    place=COALESCE(?, place),
                    defect_type=COALESCE(?, defect_type)
                WHERE id=?
            """, (subcontractor, int(deadline_days or 3), zone, note,
                  raise_type or "qc_internal", json.dumps(selected),
                  notice_pdf, consultant_ncr, photos_json,
                  engineer_name, place, defect_type, defect_id))
        else:
            cur.execute("""
                UPDATE defects
                SET subcontractor=?, deadline_days=?, zone=?, note=?,
                    raise_type=?, selected_json=?, notice_pdf=?,
                    photos_json=?,
                    engineer_name=COALESCE(?, engineer_name),
                    place=COALESCE(?, place),
                    defect_type=COALESCE(?, defect_type)
                WHERE id=?
            """, (subcontractor, int(deadline_days or 3), zone, note,
                  raise_type or "qc_internal", json.dumps(selected),
                  notice_pdf, photos_json,
                  engineer_name, place, defect_type, defect_id))
        c.commit()
        _sync(c)


def delete_defect(defect_id):
    _bump_list_cache()
    with _LOCK:
        c = _conn()
        cur = c.cursor()
        cur.execute("DELETE FROM defects WHERE id=?", (defect_id,))
        c.commit()
        _sync(c)


# =====================================================================
# DUPLICATE
# =====================================================================
def _keywords(text):
    if not text:
        return set()
    return set(re.findall(r'[a-z\u0600-\u06FF]{4,}', str(text).lower()))


def find_similar_defects(project_id, name, days=60, limit=5,
                          min_overlap=0.4):
    kw = _keywords(name)
    if not kw:
        return []
    cutoff = (datetime.datetime.utcnow() -
              datetime.timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    c = _conn()
    cur = c.cursor()
    cur.execute("""
        SELECT id, uid, zone, created_at, selected_json, subcontractor
        FROM defects WHERE project_id=? AND created_at >= ?
        ORDER BY id DESC LIMIT 300
    """, (project_id, cutoff))
    rows = _to_dicts(cur.fetchall(),
                     ["id", "uid", "zone", "created_at",
                      "selected_json", "subcontractor"])
    matches = []
    for r in rows:
        try:
            sel = json.loads(r.get("selected_json") or "[]")
        except Exception:
            continue
        for s in sel:
            past = str(s.get("name", ""))
            past_kw = _keywords(past)
            if not past_kw:
                continue
            overlap = len(kw & past_kw) / float(max(len(kw), len(past_kw)))
            if overlap >= min_overlap:
                matches.append({
                    "uid": r.get("uid"), "zone": r.get("zone"),
                    "subcontractor": r.get("subcontractor"),
                    "name": past, "date": r.get("created_at"),
                })
                break
        if len(matches) >= limit:
            break
    return matches


# =====================================================================
# SUBS
# =====================================================================
def add_subcontractor(project_id, name, trade="", phone="", notes=""):
    with _LOCK:
        c = _conn()
        cur = c.cursor()
        cur.execute("""
            INSERT INTO subcontractors
                (project_id, name, trade, phone, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (project_id, name, trade, phone, notes, _now()))
        c.commit()
        _sync(c)


def delete_subcontractor(sub_id):
    with _LOCK:
        c = _conn()
        cur = c.cursor()
        cur.execute("DELETE FROM subcontractors WHERE id=?", (sub_id,))
        c.commit()
        _sync(c)


def list_subcontractors(project_id):
    c = _conn()
    cur = c.cursor()
    cur.execute("""
        SELECT id, name, trade, phone, notes
        FROM subcontractors WHERE project_id=? ORDER BY name ASC
    """, (project_id,))
    master = _to_dicts(cur.fetchall(), SUB_COLS)
    cur.execute("""
        SELECT DISTINCT subcontractor FROM defects
        WHERE project_id=? AND subcontractor IS NOT NULL
              AND subcontractor != ''
    """, (project_id,))
    used_rows = _to_dicts(cur.fetchall(), ["subcontractor"])
    used = set()
    for r in used_rows:
        n = r.get("subcontractor")
        if n:
            used.add(n)
    out = []
    seen = set()
    for r in master:
        out.append({"id": r.get("id"), "name": r.get("name"),
                    "trade": r.get("trade") or "",
                    "phone": r.get("phone") or "",
                    "notes": r.get("notes") or "", "from_master": True})
        seen.add(r.get("name"))
    for name in used:
        if name not in seen:
            out.append({"id": None, "name": name, "trade": "",
                        "phone": "", "notes": "", "from_master": False})
    return out


def subcontractor_scores(project_id):
    rows = list_defects(project_id)
    now = datetime.datetime.utcnow()
    agg = {}
    for r in rows:
        name = r.get("subcontractor") or "(unassigned)"
        if name not in agg:
            agg[name] = {"name": name, "open": 0, "closed": 0,
                         "overdue": 0, "total": 0}
        agg[name]["total"] += 1
        if r["status"] == "open":
            agg[name]["open"] += 1
            try:
                created = datetime.datetime.strptime(
                    r["created_at"][:19], "%Y-%m-%d %H:%M:%S")
                if (now - created).days > int(r.get("deadline_days") or 3):
                    agg[name]["overdue"] += 1
            except Exception:
                pass
        else:
            agg[name]["closed"] += 1
    return sorted(agg.values(), key=lambda x: x["open"], reverse=True)


# =====================================================================
# KPIs
# =====================================================================
def kpi_summary(project_id):
    rows = list_defects(project_id)
    now = datetime.datetime.utcnow()
    week_ago = now - datetime.timedelta(days=7)
    total = len(rows)
    open_c = closed_c = overdue_c = closed_7d = 0
    days_to_close = []
    for r in rows:
        if r["status"] == "open":
            open_c += 1
            try:
                created = datetime.datetime.strptime(
                    r["created_at"][:19], "%Y-%m-%d %H:%M:%S")
                if (now - created).days > int(r.get("deadline_days") or 3):
                    overdue_c += 1
            except Exception:
                pass
        else:
            closed_c += 1
            if r.get("closed_at"):
                try:
                    cd = datetime.datetime.strptime(
                        r["closed_at"][:19], "%Y-%m-%d %H:%M:%S")
                    if cd >= week_ago:
                        closed_7d += 1
                    try:
                        cr = datetime.datetime.strptime(
                            r["created_at"][:19], "%Y-%m-%d %H:%M:%S")
                        days_to_close.append((cd - cr).days)
                    except Exception:
                        pass
                except Exception:
                    pass
    avg_days = 0
    if days_to_close:
        avg_days = round(sum(days_to_close) / float(len(days_to_close)), 1)
    return {"total": total, "open": open_c, "closed": closed_c,
            "overdue": overdue_c, "closed_7d": closed_7d,
            "avg_days": avg_days}


def kpi_per_zone(project_id):
    rows = list_defects(project_id)
    agg = {}
    for r in rows:
        if r["status"] != "open":
            continue
        z = r.get("zone") or "?"
        agg[z] = agg.get(z, 0) + 1
    return [{"zone": k, "count": v}
            for k, v in sorted(agg.items(), key=lambda x: -x[1])]


def kpi_per_week(project_id, weeks=8):
    rows = list_defects(project_id)
    now = datetime.datetime.utcnow()
    buckets = []
    for i in range(weeks - 1, -1, -1):
        start = now - datetime.timedelta(days=7 * (i + 1))
        end = now - datetime.timedelta(days=7 * i)
        label = start.strftime("%d %b")
        count = 0
        for r in rows:
            try:
                cr = datetime.datetime.strptime(
                    r["created_at"][:19], "%Y-%m-%d %H:%M:%S")
                if start <= cr < end:
                    count += 1
            except Exception:
                pass
        buckets.append({"label": label, "count": count})
    return buckets


def kpi_per_type(project_id):
    rows = list_defects(project_id)
    agg = {}
    for r in rows:
        t = r.get("defect_type") or "General"
        agg[t] = agg.get(t, 0) + 1
    return [{"type": k, "count": v}
            for k, v in sorted(agg.items(), key=lambda x: -x[1])]


def defect_scatter_data(project_id):
    rows = list_defects(project_id)
    out = []
    now = datetime.datetime.utcnow()
    for r in rows:
        try:
            cr = datetime.datetime.strptime(r["created_at"][:19],
                                             "%Y-%m-%d %H:%M:%S")
        except Exception:
            continue
        days_open = (now - cr).days
        if r["status"] == "closed" and r.get("closed_at"):
            try:
                cd = datetime.datetime.strptime(r["closed_at"][:19],
                                                 "%Y-%m-%d %H:%M:%S")
                dur = max((cd - cr).days, 0)
            except Exception:
                dur = days_open
        else:
            dur = days_open
        out.append({
            "x": days_open,
            "y": dur,
            "status": r["status"],
            "uid": r.get("uid", ""),
            "name": r.get("first_defect", "")[:40],
        })
    out.sort(key=lambda p: p["x"])
    return out


# =====================================================================
# CHAT
# =====================================================================
def chat_add(project_id, user_id, author, body, reply_to_id=None,
              mentions=None):
    _bump_list_cache()
    with _LOCK:
        c = _conn()
        cur = c.cursor()
        cur.execute("""
            INSERT INTO chat_messages
                (project_id, user_id, author, body, reply_to_id,
                 mentions, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (project_id, user_id, author, body,
              int(reply_to_id) if reply_to_id else None,
              json.dumps(mentions or []), _now()))
        mid = cur.lastrowid
        c.commit()
        _sync(c)
        return mid


def chat_list(project_id, limit=200):
    c = _conn()
    cur = c.cursor()
    cur.execute("""
        SELECT id, project_id, user_id, author, body, reply_to_id,
               mentions, created_at
        FROM chat_messages
        WHERE project_id=?
        ORDER BY id DESC LIMIT ?
    """, (project_id, int(limit)))
    rows = _to_dicts(cur.fetchall(), CHAT_COLS)
    out = []
    for r in rows:
        try:
            r["mentions"] = json.loads(r.get("mentions") or "[]")
        except Exception:
            r["mentions"] = []
        out.append(r)
    out.reverse()
    return out


def chat_get(msg_id):
    c = _conn()
    cur = c.cursor()
    cur.execute("""
        SELECT id, project_id, user_id, author, body, reply_to_id,
               mentions, created_at
        FROM chat_messages WHERE id=?
    """, (msg_id,))
    row = cur.fetchone()
    d = _to_dict(row, CHAT_COLS)
    if d:
        try:
            d["mentions"] = json.loads(d.get("mentions") or "[]")
        except Exception:
            d["mentions"] = []
    return d


def chat_delete(msg_id):
    with _LOCK:
        c = _conn()
        cur = c.cursor()
        cur.execute("DELETE FROM chat_messages WHERE id=?", (msg_id,))
        c.commit()
        _sync(c)


def chat_authors(project_id):
    c = _conn()
    cur = c.cursor()
    cur.execute("""
        SELECT DISTINCT author FROM chat_messages
        WHERE project_id=? AND author IS NOT NULL AND author != ''
        ORDER BY author
    """, (project_id,))
    rows = _to_dicts(cur.fetchall(), ["author"])
    return [r["author"] for r in rows if r.get("author")]
