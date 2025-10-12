import base64
import json
import time
import logging
from dataclasses import dataclass
from typing import Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from django.conf import settings
from django.core.cache import cache

from utils.validators import validate_e164_phone

logger = logging.getLogger(__name__)

# Resolve environment-setting name (be flexible with naming)
DARAJA_ENV = getattr(settings, "DARAJA_ENV", getattr(settings, "DAR_ENV", "sandbox"))
DARAJA_BASE = "https://sandbox.safaricom.co.ke" if DARAJA_ENV == "sandbox" else "https://api.safaricom.co.ke"

# Safety margin when caching tokens (seconds)
DAR_TOKEN_CACHE_MARGIN = int(getattr(settings, "DAR_TOKEN_CACHE_MARGIN", 60))


@dataclass
class DarajaConfig:
    consumer_key: str
    consumer_secret: str
    passkey: str
    shortcode: str


def _session() -> requests.Session:
    """Create a requests session with a retry strategy suitable for network calls."""
    s = requests.Session()
    retries = Retry(total=3, backoff_factor=0.3, status_forcelist=[429, 500, 502, 503, 504])
    s.mount("https://", HTTPAdapter(max_retries=retries))
    return s


def get_access_token(cfg: DarajaConfig) -> str:
    """
    Fetch/access token from Daraja and cache it. Handles non-int expires_in values safely.
    Returns the access_token string or raises RuntimeError on failure.
    """
    cache_key = f"daraja_token_{cfg.consumer_key}"
    token = cache.get(cache_key)
    if token:
        logger.debug("daraja: using cached token (prefix=%s)", token[:8] + "...")
        return token

    s = _session()
    try:
        r = s.get(
            f"{DARAJA_BASE}/oauth/v1/generate?grant_type=client_credentials",
            auth=(cfg.consumer_key, cfg.consumer_secret),
            timeout=10,
        )
        r.raise_for_status()
    except Exception as exc:
        logger.exception("daraja: failed to fetch access token: %s", exc)
        raise RuntimeError("Failed to fetch Daraja access token") from exc

    data = r.json()
    token = data.get("access_token")
    if not token:
        logger.error("daraja: no access_token in response: %s", data)
        raise RuntimeError("Daraja returned no access_token")

    # Normalize/guard expires_in
    raw_expires = data.get("expires_in", getattr(settings, "DAR_DEFAULT_EXPIRES", 3500))
    try:
        expires = int(raw_expires)
    except (TypeError, ValueError):
        logger.warning("daraja: invalid expires_in %r, falling back to 3500", raw_expires)
        expires = 3500

    cache_timeout = max(0, expires - DAR_TOKEN_CACHE_MARGIN)

    # cache set — require numeric timeout
    try:
        cache.set(cache_key, token, timeout=cache_timeout)
    except Exception as exc:
        # caching should not break payments — log and continue
        logger.exception("daraja: failed to cache token: %s", exc)

    logger.debug("daraja: fetched token (prefix=%s) expires_in=%s cache_timeout=%s", token[:8] + "...", expires, cache_timeout)
    return token


def stk_password(shortcode: str, passkey: str, timestamp: str) -> str:
    """
    Daraja expects base64 of shortcode+passkey+timestamp (timestamp format YYYYMMDDHHMMSS).
    """
    raw = f"{shortcode}{passkey}{timestamp}"
    return base64.b64encode(raw.encode()).decode()


def stk_push(phone: str, amount: int, account_ref: str, callback_url: str, description: str = "Runway Payment") -> dict:
    """
    Trigger an STK push via Daraja.

    - `phone` may be in local or E.164 format (e.g. '0791...' or '+254791...').
      We normalize it using `validate_e164_phone` which should return a '+254...' string.
    - Daraja expects PartyA and PhoneNumber as '2547...' (no leading '+') for many endpoints,
      so we strip the leading '+' before sending.
    - Returns the JSON response from Daraja on success.
    - Raises RuntimeError with provider body included on HTTP error.
    """
    # Normalize & validate phone; our validator returns normalized E.164 string e.g. "+2547..."
    normalized = validate_e164_phone(phone)
    if not normalized:
        raise ValueError("Invalid phone number")

    # Daraja generally expects numbers without the leading '+'
    party_msisdn = normalized.lstrip("+")  # "2547..."

    # Build config from settings (these must be present in your .env/settings)
    try:
        cfg = DarajaConfig(
            consumer_key=getattr(settings, "DARAJA_CONSUMER_KEY"),
            consumer_secret=getattr(settings, "DARAJA_CONSUMER_SECRET"),
            passkey=getattr(settings, "DARAJA_PASSKEY"),
            shortcode=str(getattr(settings, "DARAJA_SHORTCODE")),
        )
    except Exception as exc:
        logger.exception("daraja: missing configuration in settings: %s", exc)
        raise RuntimeError("Daraja configuration missing in settings") from exc

    token = get_access_token(cfg)

    ts = time.strftime("%Y%m%d%H%M%S")
    payload = {
        "BusinessShortCode": cfg.shortcode,
        "Password": stk_password(cfg.shortcode, cfg.passkey, ts),
        "Timestamp": ts,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(amount),
        "PartyA": party_msisdn,
        "PartyB": cfg.shortcode,
        "PhoneNumber": party_msisdn,
        "CallBackURL": callback_url,
        "AccountReference": str(account_ref)[:12],
        "TransactionDesc": str(description)[:40],
    }

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # Logging for debug — DO NOT log secrets in production
    logger.info("daraja: initiating STK push shortcode=%s ts=%s amount=%s party=%s", cfg.shortcode, ts, amount, party_msisdn)
    logger.debug("daraja: stk_push payload=%s", json.dumps(payload))

    s = _session()
    try:
        resp = s.post(f"{DARAJA_BASE}/mpesa/stkpush/v1/processrequest", headers=headers, json=payload, timeout=20)
        # If status != 2xx, raise to be handled below
        resp.raise_for_status()
    except requests.HTTPError as exc:
        # Try to extract provider response body (JSON or text)
        body = None
        try:
            body = resp.json()
        except Exception:
            body = resp.text if resp is not None else None
        logger.error("daraja: STK push failed status=%s body=%s", getattr(resp, "status_code", None), body)
        # Provide a clearer error up the stack with provider response
        raise RuntimeError(f"Daraja STK error: status={getattr(resp, 'status_code', None)} body={body}") from exc
    except Exception as exc:
        logger.exception("daraja: unexpected error calling STK push: %s", exc)
        raise RuntimeError("Unexpected error when calling Daraja STK push") from exc

    # Success: try to return parsed JSON, fallback to raw text if unable
    try:
        return resp.json()
    except Exception:
        return {"raw_text": resp.text}
