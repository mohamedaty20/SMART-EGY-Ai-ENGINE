"""
services/billing_db.py — Subscriptions, plans, payments, password reset,
admin stats, onboarding.
"""
import os
import json
import sqlite3
import datetime
import threading

DB_PATH = os.environ.get("DEFECT_DB_PATH", "defects.db")
TURSO_URL = os.environ.get("TURSO_URL", "").strip()
TURSO_TOKEN = os.environ.get("TURSO_TOKEN", "").strip()
LOCAL_CACHE = "/tmp/defects_cache.db"

_LOCK = threading.Lock()

PLANS = {
    "free": {"id": "free", "name": "Starter", "price_egp": 0,
             "price_usd": 0, "max_projects": 1, "max_ms": 3,
             "monthly_ai_calls": 30},
    "pro": {"id": "pro", "name": "Pro", "price_egp": 500,
            "price_usd": 15, "max_projects": 3, "max_ms": 10,
            "monthly_ai_calls": 500},
    "business": {"id": "business", "name": "Business",
                 "price_egp": 2000, "price_usd": 60, "max_projects": 999,
                 "max_ms": 999, "monthly_ai_calls": 5000},
    "trial": {"id": "trial", "name": "Trial", "price_egp": 0,
              "price_usd": 0, "max_projects": 2, "max_ms": 5,
              "monthly_ai_calls": 100},
}

TRIAL_DAYS = 14


def _now():
    return datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def _use_turso():
    return bool(TURSO_URL and TURSO_TOKEN)


def _conn():
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
            except Exception:
                pass
            return c
        except Exception as e:
            print("[bill] Turso failed: " + repr(e))
    return sqlite3.connect(DB_PATH, check_same_thread=False, timeout=10)


def _sync(c):
    try:
        c.sync()
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


USER_BILL_COLS = ["id", "email", "name", "plan", "plan_started_at",
                  "plan_expires_at", "trial_ends_at", "payment_provider",
                  "payment_ref", "has_onboarded"]

PAYMENT_COLS = ["id", "user_id", "plan", "amount", "currency",
                "provider", "provider_ref", "status", "created_at"]

RESET_COLS = ["id", "user_id", "token", "expires_at", "used_at",
              "created_at"]


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
                print("[bill] added " + table + "." + name)
            except Exception as e:
                print("[bill] add col failed: " + repr(e))


def init_billing():
    with _LOCK:
        c = _conn()
        cur = c.cursor()
        _ensure_columns(cur, "users", [
            ("plan", "TEXT DEFAULT 'free'"),
            ("plan_started_at", "TEXT"),
            ("plan_expires_at", "TEXT"),
            ("trial_ends_at", "TEXT"),
            ("payment_provider", "TEXT"),
            ("payment_ref", "TEXT"),
            ("has_onboarded", "INTEGER DEFAULT 0"),
            ("is_admin", "INTEGER DEFAULT 0"),
        ])
        cur.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER, plan TEXT, amount REAL, currency TEXT,
                provider TEXT, provider_ref TEXT, status TEXT,
                created_at TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS password_resets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER, token TEXT UNIQUE, expires_at TEXT,
                used_at TEXT, created_at TEXT
            )
        """)
        c.commit()
        _sync(c)
        c.close()
        print("[bill] init complete")


init_billing()


# =====================================================================
# USER BILLING
# =====================================================================
def get_user_billing(user_id):
    c = _conn()
    cur = c.cursor()
    cur.execute("""
        SELECT id, email, name, plan, plan_started_at, plan_expires_at,
               trial_ends_at, payment_provider, payment_ref, has_onboarded
        FROM users WHERE id=?
    """, (user_id,))
    row = cur.fetchone()
    c.close()
    b = _to_dict(row, USER_BILL_COLS)
    if not b:
        return None
    if not b.get("plan"):
        b["plan"] = "free"
    return b


def start_trial(user_id):
    now = datetime.datetime.utcnow()
    end = now + datetime.timedelta(days=TRIAL_DAYS)
    with _LOCK:
        c = _conn()
        cur = c.cursor()
        cur.execute("""
            UPDATE users SET plan='trial', plan_started_at=?,
                trial_ends_at=? WHERE id=? AND (plan IS NULL OR plan='')
        """, (now.strftime("%Y-%m-%d %H:%M:%S"),
              end.strftime("%Y-%m-%d %H:%M:%S"), user_id))
        c.commit()
        _sync(c)
        c.close()


def is_active(user_id):
    b = get_user_billing(user_id)
    if not b:
        return False, "free", "no_user"
    plan = b.get("plan") or "free"
    now = datetime.datetime.utcnow()
    if plan == "free":
        return True, "free", "free_forever"
    if plan == "trial":
        ends = b.get("trial_ends_at")
        if not ends:
            return False, "trial", "no_end"
        try:
            end_dt = datetime.datetime.strptime(ends[:19],
                                                 "%Y-%m-%d %H:%M:%S")
        except Exception:
            return False, "trial", "bad_end"
        if now > end_dt:
            return False, "trial", "expired"
        return True, "trial", "active"
    if plan in ("pro", "business"):
        expires = b.get("plan_expires_at")
        if not expires:
            return True, plan, "no_expiry"
        try:
            end_dt = datetime.datetime.strptime(expires[:19],
                                                 "%Y-%m-%d %H:%M:%S")
        except Exception:
            return True, plan, "bad_expiry"
        if now > end_dt:
            return False, plan, "expired"
        return True, plan, "active"
    return False, plan, "unknown"


def plan_limits(plan_id):
    return PLANS.get(plan_id, PLANS["free"])


def apply_payment(user_id, plan, provider, provider_ref,
                  months=1, amount=0, currency="EGP"):
    now = datetime.datetime.utcnow()
    expires = now + datetime.timedelta(days=30 * months)
    with _LOCK:
        c = _conn()
        cur = c.cursor()
        cur.execute("""
            UPDATE users
            SET plan=?, plan_started_at=?, plan_expires_at=?,
                payment_provider=?, payment_ref=?
            WHERE id=?
        """, (plan, now.strftime("%Y-%m-%d %H:%M:%S"),
              expires.strftime("%Y-%m-%d %H:%M:%S"),
              provider, provider_ref, user_id))
        cur.execute("""
            INSERT INTO payments
                (user_id, plan, amount, currency, provider,
                 provider_ref, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 'paid', ?)
        """, (user_id, plan, float(amount), currency, provider,
              provider_ref, _now()))
        c.commit()
        _sync(c)
        c.close()


def list_payments(user_id):
    c = _conn()
    cur = c.cursor()
    cur.execute("""
        SELECT id, user_id, plan, amount, currency, provider,
               provider_ref, status, created_at
        FROM payments WHERE user_id=? ORDER BY id DESC
    """, (user_id,))
    rows = _to_dicts(cur.fetchall(), PAYMENT_COLS)
    c.close()
    return rows


def count_projects(user_id):
    c = _conn()
    cur = c.cursor()
    cur.execute("SELECT COUNT(*) FROM projects WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    c.close()
    try:
        return int(row[0]) if row else 0
    except Exception:
        return 0


def count_ms_for_user(user_id):
    c = _conn()
    cur = c.cursor()
    cur.execute("""
        SELECT COUNT(*) FROM method_statements ms
        JOIN projects p ON p.id = ms.project_id
        WHERE p.user_id=?
    """, (user_id,))
    row = cur.fetchone()
    c.close()
    try:
        return int(row[0]) if row else 0
    except Exception:
        return 0


def can_create_project(user_id):
    active, plan, _ = is_active(user_id)
    if not active:
        return False, "Subscription expired. Renew to continue."
    lim = plan_limits(plan)
    n = count_projects(user_id)
    if n >= lim["max_projects"]:
        return False, ("Plan limit: " + str(lim["max_projects"]) +
                       " project(s). Upgrade for more.")
    return True, ""


def can_upload_ms(user_id):
    active, plan, _ = is_active(user_id)
    if not active:
        return False, "Subscription expired."
    lim = plan_limits(plan)
    n = count_ms_for_user(user_id)
    if n >= lim["max_ms"]:
        return False, ("Plan limit: " + str(lim["max_ms"]) +
                       " MS file(s). Upgrade for more.")
    return True, ""


# =====================================================================
# PASSWORD RESET
# =====================================================================
def create_reset_token(user_id, token, hours=2):
    now = datetime.datetime.utcnow()
    expires = now + datetime.timedelta(hours=hours)
    with _LOCK:
        c = _conn()
        cur = c.cursor()
        cur.execute("DELETE FROM password_resets WHERE user_id=? "
                    "AND used_at IS NULL", (user_id,))
        cur.execute("""
            INSERT INTO password_resets
                (user_id, token, expires_at, created_at)
            VALUES (?, ?, ?, ?)
        """, (user_id, token, expires.strftime("%Y-%m-%d %H:%M:%S"),
              now.strftime("%Y-%m-%d %H:%M:%S")))
        c.commit()
        _sync(c)
        c.close()


def get_reset_by_token(token):
    c = _conn()
    cur = c.cursor()
    cur.execute("""
        SELECT id, user_id, token, expires_at, used_at, created_at
        FROM password_resets WHERE token=?
    """, (token,))
    row = cur.fetchone()
    c.close()
    return _to_dict(row, RESET_COLS)


def mark_reset_used(reset_id):
    with _LOCK:
        c = _conn()
        cur = c.cursor()
        cur.execute("UPDATE password_resets SET used_at=? WHERE id=?",
                    (_now(), reset_id))
        c.commit()
        _sync(c)
        c.close()


# =====================================================================
# ONBOARDING
# =====================================================================
def mark_onboarded(user_id):
    with _LOCK:
        c = _conn()
        cur = c.cursor()
        cur.execute("UPDATE users SET has_onboarded=1 WHERE id=?", (user_id,))
        c.commit()
        _sync(c)
        c.close()


def has_onboarded(user_id):
    b = get_user_billing(user_id)
    if not b:
        return False
    try:
        return bool(int(b.get("has_onboarded") or 0))
    except Exception:
        return False


# =====================================================================
# ADMIN
# =====================================================================
def admin_stats():
    """Aggregate stats for admin panel."""
    c = _conn()
    cur = c.cursor()
    stats = {}

    cur.execute("SELECT COUNT(*) FROM users")
    stats["users_total"] = int((cur.fetchone() or [0])[0])

    cur.execute("SELECT COUNT(*) FROM users WHERE plan='trial' "
                "AND trial_ends_at > ?", (_now(),))
    stats["users_trial"] = int((cur.fetchone() or [0])[0])

    cur.execute("SELECT COUNT(*) FROM users WHERE plan IN ('pro','business')")
    stats["users_paid"] = int((cur.fetchone() or [0])[0])

    cur.execute("SELECT COUNT(*) FROM projects")
    stats["projects_total"] = int((cur.fetchone() or [0])[0])

    cur.execute("SELECT COUNT(*) FROM defects")
    stats["defects_total"] = int((cur.fetchone() or [0])[0])

    cur.execute("SELECT COALESCE(SUM(amount),0) FROM payments "
                "WHERE status='paid'")
    try:
        stats["revenue_total"] = float((cur.fetchone() or [0])[0])
    except Exception:
        stats["revenue_total"] = 0.0

    # Revenue last 30 days
    cutoff = (datetime.datetime.utcnow() -
              datetime.timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("SELECT COALESCE(SUM(amount),0) FROM payments "
                "WHERE status='paid' AND created_at >= ?", (cutoff,))
    try:
        stats["revenue_30d"] = float((cur.fetchone() or [0])[0])
    except Exception:
        stats["revenue_30d"] = 0.0

    c.close()
    return stats


def admin_user_list(limit=200):
    c = _conn()
    cur = c.cursor()
    cur.execute("""
        SELECT id, email, name, plan, plan_started_at, plan_expires_at,
               trial_ends_at, has_onboarded
        FROM users ORDER BY id DESC LIMIT ?
    """, (int(limit),))
    rows = _to_dicts(cur.fetchall(), USER_BILL_COLS)
    c.close()

    # Add project + defect counts per user
    for u in rows:
        c = _conn()
        cur = c.cursor()
        cur.execute("SELECT COUNT(*) FROM projects WHERE user_id=?",
                    (u["id"],))
        u["projects_count"] = int((cur.fetchone() or [0])[0])
        cur.execute("""
            SELECT COUNT(*) FROM defects d
            JOIN projects p ON p.id = d.project_id
            WHERE p.user_id=?
        """, (u["id"],))
        u["defects_count"] = int((cur.fetchone() or [0])[0])
        c.close()
    return rows


def admin_recent_payments(limit=50):
    c = _conn()
    cur = c.cursor()
    cur.execute("""
        SELECT p.id, p.user_id, p.plan, p.amount, p.currency,
               p.provider, p.status, p.created_at, u.email
        FROM payments p
        LEFT JOIN users u ON u.id = p.user_id
        ORDER BY p.id DESC LIMIT ?
    """, (int(limit),))
    rows = _to_dicts(cur.fetchall(),
                     PAYMENT_COLS + ["email"])
    c.close()
    return rows
