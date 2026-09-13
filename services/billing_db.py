"""
services/billing_db.py — Subscriptions, plans, payments.
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

# --------------------------------------------------------------
# Plan definitions
# --------------------------------------------------------------
PLANS = {
    "free": {
        "id": "free",
        "name": "Starter",
        "price_egp": 0,
        "price_usd": 0,
        "max_projects": 1,
        "max_ms": 3,
        "monthly_ai_calls": 30,
    },
    "pro": {
        "id": "pro",
        "name": "Pro",
        "price_egp": 500,
        "price_usd": 15,
        "max_projects": 3,
        "max_ms": 10,
        "monthly_ai_calls": 500,
    },
    "business": {
        "id": "business",
        "name": "Business",
        "price_egp": 2000,
        "price_usd": 60,
        "max_projects": 999,
        "max_ms": 999,
        "monthly_ai_calls": 5000,
    },
    "trial": {
        "id": "trial",
        "name": "Trial",
        "price_egp": 0,
        "price_usd": 0,
        "max_projects": 2,
        "max_ms": 5,
        "monthly_ai_calls": 100,
    },
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
                  "payment_ref"]

PAYMENT_COLS = ["id", "user_id", "plan", "amount", "currency",
                "provider", "provider_ref", "status", "created_at"]


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
        ])
        cur.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER, plan TEXT, amount REAL, currency TEXT,
                provider TEXT, provider_ref TEXT, status TEXT,
                created_at TEXT
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
               trial_ends_at, payment_provider, payment_ref
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
    """Called once at signup. Sets trial window."""
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
    """Returns (active: bool, plan: str, reason: str)."""
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

    # paid plan
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
    """Mark user as on 'plan' for N months. Log payment record."""
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


# =====================================================================
# USAGE COUNTERS
# =====================================================================
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
