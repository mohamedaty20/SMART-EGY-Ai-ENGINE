"""
services/payment_service.py — Payment providers.

Reads env vars:
  PAYMOB_API_KEY, PAYMOB_INTEGRATION_ID, PAYMOB_IFRAME_ID
  PAYMOB_HMAC_SECRET
  STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET

If nothing is set, falls back to DEMO mode — a fake page that lets you
complete a payment and see the callback flow. For internal testing only.
"""
import os
import hmac
import json
import time
import hashlib
import urllib.parse
import urllib.request

from services import billing_db as bdb


PAYMOB_API_KEY = os.environ.get("PAYMOB_API_KEY", "").strip()
PAYMOB_INTEGRATION_ID = os.environ.get("PAYMOB_INTEGRATION_ID", "").strip()
PAYMOB_IFRAME_ID = os.environ.get("PAYMOB_IFRAME_ID", "").strip()
PAYMOB_HMAC_SECRET = os.environ.get("PAYMOB_HMAC_SECRET", "").strip()

STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "").strip()
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "").strip()

BASE_URL = os.environ.get("APP_BASE_URL",
                           "https://smart-egy-ai-engine.onrender.com").rstrip("/")


def provider_available():
    """Return dict of which providers are configured."""
    return {
        "paymob": bool(PAYMOB_API_KEY and PAYMOB_INTEGRATION_ID
                        and PAYMOB_IFRAME_ID),
        "stripe": bool(STRIPE_SECRET_KEY),
        "demo": True,
    }


def _http_post_json(url, payload, headers=None, timeout=15):
    data = json.dumps(payload).encode("utf-8")
    h = {"Content-Type": "application/json"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, data=data, headers=h, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _http_get_json(url, headers=None, timeout=15):
    h = {}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


# =====================================================================
# PAYMOB
# =====================================================================
def paymob_auth_token():
    if not PAYMOB_API_KEY:
        raise Exception("PAYMOB_API_KEY missing")
    resp = _http_post_json("https://accept.paymob.com/api/auth/tokens",
                            {"api_key": PAYMOB_API_KEY})
    return resp.get("token")


def paymob_create_order(amount_cents, currency="EGP",
                         merchant_order_id=None):
    token = paymob_auth_token()
    if not token:
        raise Exception("Paymob auth failed")
    payload = {
        "auth_token": token,
        "delivery_needed": False,
        "amount_cents": int(amount_cents),
        "currency": currency,
        "merchant_order_id": merchant_order_id or str(int(time.time())),
        "items": [],
    }
    resp = _http_post_json("https://accept.paymob.com/api/ecommerce/orders",
                            payload)
    return resp.get("id")


def paymob_payment_key(order_id, amount_cents, user,
                        currency="EGP"):
    token = paymob_auth_token()
    if not token:
        raise Exception("Paymob auth failed")
    name_parts = (user.get("name") or "Customer").split(" ", 1)
    payload = {
        "auth_token": token,
        "amount_cents": int(amount_cents),
        "expiration": 3600,
        "order_id": order_id,
        "currency": currency,
        "integration_id": int(PAYMOB_INTEGRATION_ID),
        "billing_data": {
            "apartment": "NA", "email": user.get("email") or "na@na.com",
            "floor": "NA", "first_name": name_parts[0] or "NA",
            "street": "NA", "building": "NA",
            "phone_number": "+201000000000",
            "shipping_method": "NA", "postal_code": "NA",
            "city": "Cairo", "country": "EG", "state": "NA",
            "last_name": (name_parts[1] if len(name_parts) > 1 else "NA"),
        },
    }
    resp = _http_post_json("https://accept.paymob.com/api/acceptance/payment_keys",
                            payload)
    return resp.get("token")


def paymob_iframe_url(payment_token):
    return ("https://accept.paymob.com/api/acceptance/iframes/" +
            str(PAYMOB_IFRAME_ID) + "?payment_token=" + str(payment_token))


def paymob_verify_hmac(query_params):
    """
    Paymob callback includes 'hmac' — verify against concatenation
    of specific fields in alphabetical order.
    """
    if not PAYMOB_HMAC_SECRET:
        return False
    fields = [
        "amount_cents", "created_at", "currency", "error_occured",
        "has_parent_transaction", "id", "integration_id", "is_3d_secure",
        "is_auth", "is_capture", "is_refunded", "is_standalone_payment",
        "is_voided", "order", "owner", "pending",
        "source_data.pan", "source_data.sub_type",
        "source_data.type", "success",
    ]
    parts = []
    for f in fields:
        v = query_params.get(f, "")
        if isinstance(v, dict):
            v = ""
        parts.append(str(v))
    concat = "".join(parts)
    expected = hmac.new(PAYMOB_HMAC_SECRET.encode(),
                         concat.encode(), hashlib.sha512).hexdigest()
    return hmac.compare_digest(expected, str(query_params.get("hmac", "")))


def paymob_checkout_url(user, plan_id, months=1):
    plan = bdb.PLANS.get(plan_id)
    if not plan:
        raise Exception("Unknown plan")
    amount_egp = int(plan["price_egp"]) * int(months)
    amount_cents = amount_egp * 100
    order_id = paymob_create_order(amount_cents, currency="EGP",
                                    merchant_order_id=
                                    "u" + str(user["id"]) + "-" + plan_id)
    token = paymob_payment_key(order_id, amount_cents, user)
    return paymob_iframe_url(token)


# =====================================================================
# STRIPE (checkout links — no SDK needed)
# =====================================================================
def stripe_create_checkout(user, plan_id, months=1):
    plan = bdb.PLANS.get(plan_id)
    if not plan:
        raise Exception("Unknown plan")
    amount_usd = int(plan["price_usd"]) * int(months)
    if amount_usd < 1:
        raise Exception("Amount too small")
    # Stripe Checkout via REST
    payload = [
        ("mode", "payment"),
        ("success_url", BASE_URL + "/payment/ok?provider=stripe&plan=" +
                        plan_id + "&uid=" + str(user["id"])),
        ("cancel_url", BASE_URL + "/pricing?cancel=1"),
        ("line_items[0][price_data][currency]", "usd"),
        ("line_items[0][price_data][product_data][name]",
         "Defect Notices — " + plan["name"] + " (" +
         str(months) + " month)"),
        ("line_items[0][price_data][unit_amount]", str(amount_usd * 100)),
        ("line_items[0][quantity]", "1"),
        ("client_reference_id", "u" + str(user["id"]) + "-" + plan_id),
        ("metadata[user_id]", str(user["id"])),
        ("metadata[plan]", plan_id),
    ]
    body = urllib.parse.urlencode(payload).encode("utf-8")
    req = urllib.request.Request(
        "https://api.stripe.com/v1/checkout/sessions", data=body,
        headers={"Authorization": "Bearer " + STRIPE_SECRET_KEY},
        method="POST")
    with urllib.request.urlopen(req, timeout=20) as r:
        resp = json.loads(r.read().decode("utf-8"))
    return resp.get("url")


# =====================================================================
# HIGH-LEVEL
# =====================================================================
def checkout_url(user, plan_id, months=1, preferred="paymob"):
    """
    Return (url, provider). If the preferred provider isn't configured,
    falls back to demo. Never raises if it can make a demo URL.
    """
    plans = bdb.PLANS
    if plan_id not in plans or plan_id == "free":
        raise Exception("Not a payable plan")

    providers = provider_available()

    if preferred == "paymob" and providers["paymob"]:
        try:
            return paymob_checkout_url(user, plan_id, months), "paymob"
        except Exception as e:
            print("[pay] paymob failed: " + repr(e))

    if preferred == "stripe" and providers["stripe"]:
        try:
            return stripe_create_checkout(user, plan_id, months), "stripe"
        except Exception as e:
            print("[pay] stripe failed: " + repr(e))

    # Fallback: demo
    return (BASE_URL + "/payment/demo?plan=" + plan_id +
            "&months=" + str(months) + "&uid=" + str(user["id"])), "demo"


def complete_demo_payment(user_id, plan_id, months=1):
    """Apply a demo payment — for internal testing only."""
    plan = bdb.PLANS.get(plan_id)
    if not plan:
        return False
    bdb.apply_payment(
        user_id=user_id, plan=plan_id, provider="demo",
        provider_ref="demo-" + str(int(time.time())),
        months=int(months), amount=plan["price_egp"], currency="EGP")
    return True
