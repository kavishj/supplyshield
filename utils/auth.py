import streamlit as st
import pyotp
import qrcode
import hashlib
import json
import time
from pathlib import Path
from io import BytesIO
from PIL import Image

# ── Config storage ────────────────────────────────────────────
AUTH_FILE = Path(r"C:\Users\KAVISH\supplyshield_final\data\auth.json")

# ── Single admin credentials ──────────────────────────────────
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = hashlib.sha256("supplyshield2025".encode()).hexdigest()

def _load_auth() -> dict:
    """Load auth config from disk."""
    if AUTH_FILE.exists():
        with open(AUTH_FILE) as f:
            return json.load(f)
    return {}

def _save_auth(data: dict):
    """Save auth config to disk."""
    AUTH_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(AUTH_FILE, "w") as f:
        json.dump(data, f, indent=2)

def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def is_first_login() -> bool:
    """True if TOTP secret has not been set up yet."""
    auth = _load_auth()
    return not auth.get("totp_secret")

def get_totp_secret() -> str:
    """Get existing TOTP secret or create one."""
    auth = _load_auth()
    if not auth.get("totp_secret"):
        secret = pyotp.random_base32()
        auth["totp_secret"] = secret
        _save_auth(auth)
    return auth["totp_secret"]

def verify_password(username: str, password: str) -> bool:
    return (username == ADMIN_USERNAME and
            _hash_password(password) == ADMIN_PASSWORD_HASH)

def verify_otp(token: str) -> bool:
    secret = get_totp_secret()
    totp   = pyotp.TOTP(secret)
    # valid_window=1 allows 30s clock drift
    return totp.verify(token, valid_window=1)

def generate_qr_code() -> bytes:
    """Generate QR code image for Google Authenticator."""
    secret = get_totp_secret()
    totp   = pyotp.TOTP(secret)
    uri    = totp.provisioning_uri(
        name="admin@supplyshield",
        issuer_name="SupplyShield"
    )
    qr  = qrcode.make(uri)
    buf = BytesIO()
    qr.save(buf, format="PNG")
    return buf.getvalue()

def mark_totp_confirmed():
    """Mark that user has confirmed TOTP setup."""
    auth = _load_auth()
    auth["totp_confirmed"] = True
    _save_auth(auth)

def is_totp_confirmed() -> bool:
    auth = _load_auth()
    return auth.get("totp_confirmed", False)