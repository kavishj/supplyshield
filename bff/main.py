"""
SupplyShield — Backend for Frontend (BFF)
Port: 8006

Responsibilities:
  - Auth (JWT, TOTP)  — isolated, easily removable
  - Company profile CRUD  → data/suppliers.db :: company_profile
  - Onboarded suppliers CRUD → data/suppliers.db :: onboarded_suppliers
  - Audit log query  → data/suppliers.db :: suppliers
  - Orchestrator proxy (analyze, recommend, portfolio, risky, recommendations)
  - PDF export

The Streamlit app is untouched — both services share the same SQLite DB.
"""

import hashlib
import json
import os
import sqlite3
import sys
import time
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional

import jwt
import pyotp
import qrcode
import requests as req
from fastapi import Depends, FastAPI, Form, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from PIL import Image  # noqa: F401
from pydantic import BaseModel

# ── Project root on path (for pdf_export + config) ───────────────────────────
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from utils.pdf_export import generate_supplier_pdf  # noqa: E402
from config import DEFAULT_WEIGHTS  # noqa: E402

# ── Paths ─────────────────────────────────────────────────────────────────────
DATA_DIR      = _ROOT / "data"
AUTH_FILE     = DATA_DIR / "auth.json"
DB_PATH       = Path(os.getenv("DB_PATH", str(DATA_DIR / "suppliers.db")))
TEMPLATE_PATH = DATA_DIR / "SupplyShield_Suppliers_Template.xlsx"
ORCHESTRATOR  = os.getenv("ORCHESTRATOR_URL", "http://127.0.0.1:8000")

# ── JWT / Auth config ─────────────────────────────────────────────────────────
JWT_SECRET    = os.getenv("JWT_SECRET", "supplyshield-dev-secret-change-in-prod")
JWT_ALGO      = "HS256"
JWT_EXPIRE_S  = int(os.getenv("JWT_EXPIRE_S", 86400))
AUTH_REQUIRED = os.getenv("AUTH_REQUIRED", "true").lower() == "true"

# ── Admin credentials (mirrors utils/auth.py) ─────────────────────────────────
ADMIN_USERNAME      = "admin"
ADMIN_PASSWORD_HASH = hashlib.sha256("supplyshield2025".encode()).hexdigest()


# ─────────────────────────────────────────────────────────────────────────────
# Auth helpers
# ─────────────────────────────────────────────────────────────────────────────

def _load_auth() -> dict:
    if AUTH_FILE.exists():
        with open(AUTH_FILE) as f:
            return json.load(f)
    return {}

def _save_auth(data: dict) -> None:
    AUTH_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(AUTH_FILE, "w") as f:
        json.dump(data, f, indent=2)

def _get_totp_secret() -> str:
    auth = _load_auth()
    if not auth.get("totp_secret"):
        secret = pyotp.random_base32()
        auth["totp_secret"] = secret
        _save_auth(auth)
    return auth["totp_secret"]

def _verify_password(username: str, password: str) -> bool:
    return (
        username == ADMIN_USERNAME
        and hashlib.sha256(password.encode()).hexdigest() == ADMIN_PASSWORD_HASH
    )

def _verify_otp_code(token: str) -> bool:
    return pyotp.TOTP(_get_totp_secret()).verify(token, valid_window=1)

def _generate_qr_bytes() -> bytes:
    totp = pyotp.TOTP(_get_totp_secret())
    uri  = totp.provisioning_uri(name="admin@supplyshield", issuer_name="SupplyShield")
    buf  = BytesIO()
    qrcode.make(uri).save(buf, format="PNG")
    return buf.getvalue()

def _is_totp_confirmed() -> bool:
    return _load_auth().get("totp_confirmed", False)

def _mark_totp_confirmed() -> None:
    auth = _load_auth()
    auth["totp_confirmed"] = True
    _save_auth(auth)

def _make_token(username: str) -> str:
    now = int(time.time())
    return jwt.encode({"sub": username, "iat": now, "exp": now + JWT_EXPIRE_S},
                      JWT_SECRET, algorithm=JWT_ALGO)

def _decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")


# ─────────────────────────────────────────────────────────────────────────────
# DB helpers
# ─────────────────────────────────────────────────────────────────────────────

def _db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def _row_to_dict(row) -> dict:
    return dict(row) if row else {}


# ─────────────────────────────────────────────────────────────────────────────
# FastAPI app
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(title="SupplyShield BFF", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:4173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_bearer = HTTPBearer(auto_error=False)

def require_auth(credentials: HTTPAuthorizationCredentials = Depends(_bearer)) -> dict:
    if not AUTH_REQUIRED:
        return {"sub": "admin"}
    if not credentials:
        raise HTTPException(401, "Not authenticated")
    return _decode_token(credentials.credentials)


# ─────────────────────────────────────────────────────────────────────────────
# Request / Response models
# ─────────────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str

class OTPRequest(BaseModel):
    otp_code: str

class ProfilePayload(BaseModel):
    business_name:       str
    country:             str
    industry:            str
    contact_email:       str
    tax_id:              Optional[str]       = None
    annual_revenue:      Optional[float]     = None
    lead_time_weeks:     Optional[int]       = None
    num_employees:       Optional[int]       = None
    iso_certifications:  Optional[str]       = None
    anti_bribery_policy: Optional[bool]      = False
    labor_law_compliance:Optional[bool]      = False
    sp_rating:           Optional[str]       = None
    products_services:   Optional[str]       = None
    address:             Optional[str]       = None

class SupplierPayload(BaseModel):
    name:                 str
    country:              str
    what_they_supply:     str
    criticality:          str
    annual_spend_usd:     Optional[float]    = None
    spend_percentage:     Optional[float]    = None
    contract_expiry:      Optional[str]      = None
    category:             Optional[str]      = None
    notes:                Optional[str]      = None
    tier_level:           Optional[str]      = None
    sole_source:          Optional[bool]     = False
    on_time_delivery_rate:Optional[float]    = None
    years_in_relationship:Optional[int]      = None
    financial_health:     Optional[str]      = None

class ActionStatusPayload(BaseModel):
    action_id: str
    completed: bool


# ─────────────────────────────────────────────────────────────────────────────
# Health
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    # Also ping orchestrator to get agent statuses
    agent_health = {}
    try:
        r = req.get(f"{ORCHESTRATOR}/health", timeout=3)
        agent_health = r.json().get("agents", {})
    except Exception:
        pass
    return {"status": "ok", "service": "bff", "auth_required": AUTH_REQUIRED,
            "agents": agent_health}


# ─────────────────────────────────────────────────────────────────────────────
# Auth routes
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/auth/login")
def login(req_body: LoginRequest):
    if not _verify_password(req_body.username, req_body.password):
        raise HTTPException(401, "Invalid username or password")
    return {"success": True, "requires_setup": not _is_totp_confirmed()}

@app.post("/auth/verify-otp")
def verify_otp(req_body: OTPRequest):
    if len(req_body.otp_code) != 6 or not req_body.otp_code.isdigit():
        raise HTTPException(400, "Enter a valid 6-digit code")
    if not _verify_otp_code(req_body.otp_code):
        raise HTTPException(401, "Invalid code. Try again.")
    if not _is_totp_confirmed():
        _mark_totp_confirmed()
    return {"success": True, "token": _make_token("admin")}

@app.get("/auth/qr-code")
def qr_code():
    return Response(content=_generate_qr_bytes(), media_type="image/png")

@app.get("/auth/me")
def me(user: dict = Depends(require_auth)):
    return {"authenticated": True, "username": user["sub"]}


# ─────────────────────────────────────────────────────────────────────────────
# Company Profile
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/profile")
def get_profile(_user: dict = Depends(require_auth)):
    with _db() as conn:
        row = conn.execute(
            "SELECT * FROM company_profile ORDER BY id DESC LIMIT 1"
        ).fetchone()
    return _row_to_dict(row)

@app.get("/profile/status")
def profile_status(_user: dict = Depends(require_auth)):
    with _db() as conn:
        row = conn.execute(
            "SELECT onboarding_complete FROM company_profile LIMIT 1"
        ).fetchone()
    complete = bool(row["onboarding_complete"]) if row else False
    return {"onboarding_complete": complete}

@app.post("/profile")
def save_profile(data: ProfilePayload, _user: dict = Depends(require_auth)):
    with _db() as conn:
        existing = conn.execute(
            "SELECT id FROM company_profile LIMIT 1"
        ).fetchone()
        if existing:
            conn.execute("""
                UPDATE company_profile SET
                    business_name=?, country=?, industry=?, contact_email=?,
                    tax_id=?, annual_revenue=?, lead_time_weeks=?, num_employees=?,
                    iso_certifications=?, anti_bribery_policy=?, labor_law_compliance=?,
                    sp_rating=?, products_services=?, address=?,
                    onboarding_complete=1, updated_at=datetime('now')
                WHERE id=?
            """, (
                data.business_name, data.country, data.industry, data.contact_email,
                data.tax_id, data.annual_revenue, data.lead_time_weeks, data.num_employees,
                data.iso_certifications, int(data.anti_bribery_policy or False),
                int(data.labor_law_compliance or False), data.sp_rating,
                data.products_services, data.address, existing[0],
            ))
        else:
            conn.execute("""
                INSERT INTO company_profile (
                    business_name, country, industry, contact_email,
                    tax_id, annual_revenue, lead_time_weeks, num_employees,
                    iso_certifications, anti_bribery_policy, labor_law_compliance,
                    sp_rating, products_services, address, onboarding_complete
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,1)
            """, (
                data.business_name, data.country, data.industry, data.contact_email,
                data.tax_id, data.annual_revenue, data.lead_time_weeks, data.num_employees,
                data.iso_certifications, int(data.anti_bribery_policy or False),
                int(data.labor_law_compliance or False), data.sp_rating,
                data.products_services, data.address,
            ))
        conn.commit()
    return {"success": True}


# ─────────────────────────────────────────────────────────────────────────────
# Onboarded Suppliers
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/suppliers/onboarded")
def get_onboarded_suppliers(_user: dict = Depends(require_auth)):
    with _db() as conn:
        rows = conn.execute(
            "SELECT * FROM onboarded_suppliers ORDER BY criticality, name"
        ).fetchall()
    return [_row_to_dict(r) for r in rows]

@app.post("/suppliers/onboarded")
def save_onboarded_supplier(data: SupplierPayload, _user: dict = Depends(require_auth)):
    with _db() as conn:
        existing = conn.execute(
            "SELECT id FROM onboarded_suppliers WHERE UPPER(name)=UPPER(?)",
            (data.name,)
        ).fetchone()
        if existing:
            conn.execute("""
                UPDATE onboarded_suppliers SET
                    country=?, what_they_supply=?, criticality=?,
                    annual_spend_usd=?, spend_percentage=?, contract_expiry=?,
                    category=?, notes=?, tier_level=?, sole_source=?,
                    on_time_delivery_rate=?, years_in_relationship=?,
                    financial_health=?, updated_at=datetime('now')
                WHERE id=?
            """, (
                data.country, data.what_they_supply, data.criticality,
                data.annual_spend_usd, data.spend_percentage, data.contract_expiry,
                data.category, data.notes, data.tier_level,
                int(data.sole_source or False), data.on_time_delivery_rate,
                data.years_in_relationship, data.financial_health, existing[0],
            ))
        else:
            conn.execute("""
                INSERT INTO onboarded_suppliers (
                    name, country, what_they_supply, criticality,
                    annual_spend_usd, spend_percentage, contract_expiry,
                    category, notes, tier_level, sole_source,
                    on_time_delivery_rate, years_in_relationship, financial_health
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                data.name, data.country, data.what_they_supply, data.criticality,
                data.annual_spend_usd, data.spend_percentage, data.contract_expiry,
                data.category, data.notes, data.tier_level,
                int(data.sole_source or False), data.on_time_delivery_rate,
                data.years_in_relationship, data.financial_health,
            ))
        conn.commit()
    return {"success": True}

@app.delete("/suppliers/onboarded/{supplier_id}")
def delete_onboarded_supplier(supplier_id: int, _user: dict = Depends(require_auth)):
    with _db() as conn:
        conn.execute("DELETE FROM onboarded_suppliers WHERE id=?", (supplier_id,))
        conn.commit()
    return {"success": True}

@app.post("/suppliers/excel-upload")
async def excel_upload(file: UploadFile = File(...), _user: dict = Depends(require_auth)):
    # Import here to keep top-level imports clean
    import io, pandas as pd

    def _norm(c):
        if c is None or (isinstance(c, float) and pd.isna(c)):
            return ""
        s = str(c).strip().lower().replace(" ", "_").replace("(", "").replace(")", "")
        return "".join(ch for ch in s if ch.isalnum() or ch in {"_", "%"})

    raw_bytes = await file.read()
    df_raw    = pd.read_excel(io.BytesIO(raw_bytes), header=None)
    required  = {"supplier_name", "country", "what_they_supply", "criticality_level"}

    header_row = None
    for i in range(min(10, len(df_raw))):
        cells = {_norm(c) for c in df_raw.iloc[i].tolist() if _norm(c)}
        if required.issubset(cells):
            header_row = i
            break

    if header_row is None:
        df = pd.read_excel(io.BytesIO(raw_bytes))
        df.columns = [_norm(c) for c in df.columns]
    else:
        cols = [_norm(c) or f"unnamed_{i}" for i, c in enumerate(df_raw.iloc[header_row].tolist())]
        df   = df_raw.iloc[header_row + 1:].copy()
        df.columns = cols

    missing = required - set(df.columns)
    if missing:
        raise HTTPException(400, f"Missing columns: {missing}")

    saved, errors = 0, []
    with _db() as conn:
        for idx, row in df.iterrows():
            try:
                name = str(row.get("supplier_name", "")).strip()
                if not name or name.lower() == "nan":
                    continue

                spend_pct = row.get("spend_%_of_total_budget") or row.get("spend_percentage")
                if spend_pct and pd.notna(spend_pct) and float(spend_pct) <= 1.0:
                    spend_pct = float(spend_pct) * 100

                expiry = row.get("contract_expiry_date") or row.get("contract_expiry")
                if pd.notna(expiry) and expiry:
                    try:
                        expiry = pd.to_datetime(expiry).strftime("%Y-%m-%d")
                    except Exception:
                        expiry = None
                else:
                    expiry = None

                spend_usd = row.get("annual_spend_usd")
                if pd.notna(spend_usd) and spend_usd:
                    spend_usd = float(str(spend_usd).replace("$", "").replace(",", ""))
                else:
                    spend_usd = None

                existing = conn.execute(
                    "SELECT id FROM onboarded_suppliers WHERE UPPER(name)=UPPER(?)",
                    (name,)
                ).fetchone()

                country     = str(row.get("country", "")).strip().upper()
                supply      = str(row.get("what_they_supply", "")).strip()
                criticality = str(row.get("criticality_level", "Medium")).strip()
                cat_val     = row.get("supply_category", "Other")
                category    = str(cat_val).strip() if pd.notna(cat_val) else "Other"

                if existing:
                    conn.execute("""
                        UPDATE onboarded_suppliers SET
                            country=?, what_they_supply=?, criticality=?,
                            annual_spend_usd=?, spend_percentage=?, contract_expiry=?,
                            category=?, updated_at=datetime('now')
                        WHERE id=?
                    """, (country, supply, criticality, spend_usd,
                          float(spend_pct) if spend_pct and pd.notna(spend_pct) else None,
                          expiry, category, existing[0]))
                else:
                    conn.execute("""
                        INSERT INTO onboarded_suppliers
                        (name, country, what_they_supply, criticality,
                         annual_spend_usd, spend_percentage, contract_expiry, category)
                        VALUES (?,?,?,?,?,?,?,?)
                    """, (name, country, supply, criticality, spend_usd,
                          float(spend_pct) if spend_pct and pd.notna(spend_pct) else None,
                          expiry, category))
                saved += 1
            except Exception as e:
                errors.append(f"Row {idx}: {e}")
        conn.commit()

    return {"success": True, "saved": saved, "errors": errors}

@app.get("/suppliers/excel-template")
def excel_template(_user: dict = Depends(require_auth)):
    if not TEMPLATE_PATH.exists():
        raise HTTPException(404, "Template file not found")
    with open(TEMPLATE_PATH, "rb") as f:
        content = f.read()
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=SupplyShield_Suppliers_Template.xlsx"},
    )


# ─────────────────────────────────────────────────────────────────────────────
# Audit Log
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/audit-log")
def audit_log(_user: dict = Depends(require_auth)):
    with _db() as conn:
        # Pull base screening data from the suppliers table
        rows = conn.execute("""
            SELECT name, country, category, last_screened, last_score,
                   last_decision, single_source, lead_time
            FROM suppliers
            WHERE last_screened IS NOT NULL
            ORDER BY last_screened DESC
        """).fetchall()
    log = []
    for r in rows:
        row = _row_to_dict(r)
        # Normalise to the field names the frontend expects
        dec_raw = row.get("last_decision") or ""
        log.append({
            "supplier_name":  row.get("name"),
            "country":        row.get("country"),
            "category":       row.get("category"),
            "timestamp":      row.get("last_screened"),
            "risk_score":     row.get("last_score"),
            "decision":       dec_raw.replace("_", " ").upper() if dec_raw else None,
            # Richer analysis fields are not stored in the suppliers table;
            # the page renders gracefully when these are absent.
        })
    return {"log": log}


# ─────────────────────────────────────────────────────────────────────────────
# Orchestrator proxies
# ─────────────────────────────────────────────────────────────────────────────

def _orch(method: str, path: str, **kwargs) -> Any:
    try:
        r = req.request(method, f"{ORCHESTRATOR}{path}", **kwargs)
        return r.json()
    except Exception as e:
        raise HTTPException(502, f"Orchestrator unreachable: {e}")

def _save_to_audit(result: dict):
    """Mirror of app.py save_to_audit_log — called after every /analyze."""
    try:
        with _db() as conn:
            existing = conn.execute(
                "SELECT id FROM suppliers WHERE UPPER(name)=UPPER(?)",
                (result["company_name"],)
            ).fetchone()
            if existing:
                conn.execute("""
                    UPDATE suppliers SET last_screened=datetime('now'),
                    last_score=?, last_decision=? WHERE UPPER(name)=UPPER(?)
                """, (result["risk_score"], result["gate_decision"], result["company_name"]))
            else:
                conn.execute("""
                    INSERT INTO suppliers
                    (name, country, category, single_source, lead_time,
                     last_screened, last_score, last_decision)
                    VALUES (?,?,?,?,?,datetime('now'),?,?)
                """, (
                    result["company_name"], result.get("country") or "N/A",
                    "Manual Entry", 0, 12,
                    result["risk_score"], result["gate_decision"],
                ))
            conn.commit()
    except Exception:
        pass   # non-fatal

@app.post("/analyze")
def analyze(payload: Dict[str, Any] = None, _user: dict = Depends(require_auth)):
    result = _orch("POST", "/analyze", json=payload, timeout=130)
    if "error" not in result:
        _save_to_audit(result)
    return result

@app.post("/recommend")
def recommend(payload: Dict[str, Any] = None, _user: dict = Depends(require_auth)):
    return _orch("POST", "/recommend", json=payload, timeout=130)

@app.get("/portfolio")
def portfolio(_user: dict = Depends(require_auth)):
    raw = _orch("GET", "/suppliers", timeout=10)
    # Only include suppliers that have been analysed (have a score)
    analysed = [s for s in (raw.get("suppliers") or []) if s.get("last_score") is not None]
    if not analysed:
        return {"summary": {}, "suppliers": [], "gate_breakdown": [],
                "country_risk": [], "category_risk": []}

    HIGH_THRESHOLD = 0.75
    scores     = [s["last_score"] for s in analysed]
    decisions  = [s.get("last_decision") or "" for s in analysed]

    # Normalise decision strings (orchestrator uses underscores, e.g. REQUIRES_APPROVAL)
    def _norm_dec(d: str) -> str:
        return d.replace("_", " ").upper() if d else ""

    normed = [_norm_dec(d) for d in decisions]

    # Summary KPIs
    total        = len(analysed)
    blocked      = sum(1 for d in normed if d == "BLOCKED")
    req_approval = sum(1 for d in normed if d == "REQUIRES APPROVAL")
    approved     = sum(1 for d in normed if d == "APPROVED")
    avg_score    = round(sum(scores) / total, 4)
    high_risk    = sum(1 for sc in scores if sc >= HIGH_THRESHOLD)

    # Flat supplier list for table / histogram
    suppliers_flat = [
        {
            "supplier_name": s.get("name"),
            "country":       s.get("country"),
            "category":      s.get("category"),
            "score":         s.get("last_score"),
            "decision":      _norm_dec(s.get("last_decision") or ""),
        }
        for s in analysed
    ]

    # Gate breakdown for donut
    from collections import defaultdict
    gate_counts = defaultdict(int)
    for d in normed:
        gate_counts[d or "UNKNOWN"] += 1
    gate_breakdown = [{"decision": k, "count": v} for k, v in gate_counts.items()]

    # Country risk
    country_scores = defaultdict(list)
    for s in analysed:
        c = s.get("country") or "Unknown"
        country_scores[c].append(s["last_score"])
    country_risk = [
        {"country": c, "avg_score": round(sum(v) / len(v), 4), "count": len(v)}
        for c, v in country_scores.items()
    ]

    # Category risk
    cat_scores = defaultdict(list)
    for s in analysed:
        cat = s.get("category") or "Unknown"
        cat_scores[cat].append(s["last_score"])
    category_risk = [
        {"category": c, "avg_score": round(sum(v) / len(v), 4), "count": len(v)}
        for c, v in cat_scores.items()
    ]

    return {
        "summary": {
            "total_analyzed":    total,
            "blocked":           blocked,
            "requires_approval": req_approval,
            "approved":          approved,
            "avg_risk_score":    avg_score,
            "high_risk_count":   high_risk,
        },
        "suppliers":      suppliers_flat,
        "gate_breakdown": gate_breakdown,
        "country_risk":   country_risk,
        "category_risk":  category_risk,
    }

@app.get("/risky-suppliers")
def risky_suppliers(_user: dict = Depends(require_auth)):
    return _orch("GET", "/risky_suppliers", timeout=10)

@app.get("/recommendations/{supplier_name}")
def get_recommendation(supplier_name: str, _user: dict = Depends(require_auth)):
    return _orch("GET", f"/recommendations/{supplier_name}", timeout=5)

@app.post("/recommendations/{supplier_name}/action-status")
def update_action_status(supplier_name: str, payload: ActionStatusPayload,
                         _user: dict = Depends(require_auth)):
    return _orch("POST", f"/recommendations/{supplier_name}/action_status",
                 json=payload.model_dump(), timeout=5)

@app.post("/batch")
def batch(_user: dict = Depends(require_auth)):
    return _orch("POST", "/batch", timeout=300)


# ─────────────────────────────────────────────────────────────────────────────
# PDF Export
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/pdf/generate")
def generate_pdf(result: Dict[str, Any], _user: dict = Depends(require_auth)):
    try:
        pdf_bytes = generate_supplier_pdf(result)
        name = result.get("company_name", "supplier").replace(" ", "_")
        from datetime import datetime
        filename = f"SupplyShield_{name}_{datetime.now().strftime('%Y%m%d')}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception as e:
        raise HTTPException(500, f"PDF generation failed: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# Supplier Portal — tables, auth helpers, models
# ─────────────────────────────────────────────────────────────────────────────

@app.on_event("startup")
def _init_supplier_tables():
    with _db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS supplier_users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                supplier_id   INTEGER NOT NULL UNIQUE,
                username      TEXT    NOT NULL UNIQUE,
                password_hash TEXT    NOT NULL,
                email         TEXT,
                contact_name  TEXT,
                created_at    TEXT    DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS supplier_notifications (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                supplier_id       INTEGER NOT NULL,
                risk_category     TEXT    NOT NULL,
                message           TEXT    DEFAULT '',
                immediate_actions TEXT    DEFAULT '[]',
                long_term_actions TEXT    DEFAULT '[]',
                sent_at           TEXT    DEFAULT (datetime('now')),
                is_read           INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS supplier_documents (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                supplier_id     INTEGER NOT NULL,
                notification_id INTEGER,
                filename        TEXT    NOT NULL,
                file_data       BLOB    NOT NULL,
                file_size       INTEGER,
                note            TEXT,
                uploaded_at     TEXT    DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS supplier_action_log (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                supplier_id     INTEGER NOT NULL,
                notification_id INTEGER,
                action_type     TEXT    NOT NULL,
                details         TEXT,
                created_at      TEXT    DEFAULT (datetime('now')),
                admin_seen      INTEGER DEFAULT 0
            );
        """)


def _make_supplier_token(supplier_id: int, username: str) -> str:
    now = int(time.time())
    return jwt.encode(
        {"sub": username, "supplier_id": supplier_id, "role": "supplier",
         "iat": now, "exp": now + JWT_EXPIRE_S},
        JWT_SECRET, algorithm=JWT_ALGO,
    )


def require_supplier_auth(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> dict:
    if not credentials:
        raise HTTPException(401, "Not authenticated")
    payload = _decode_token(credentials.credentials)
    if payload.get("role") != "supplier":
        raise HTTPException(403, "Supplier access only")
    return payload


class SupplierAccountCreate(BaseModel):
    supplier_id:  int
    username:     str
    password:     str
    email:        Optional[str] = None
    contact_name: Optional[str] = None


class SupplierLoginRequest(BaseModel):
    username: str
    password: str


class NotifySupplierPayload(BaseModel):
    supplier_id:       int
    risk_category:     str
    message:           str = ""
    immediate_actions: List[Dict[str, Any]] = []
    long_term_actions: List[Dict[str, Any]] = []


# ─────────────────────────────────────────────────────────────────────────────
# Supplier Portal — Admin endpoints  (require admin JWT)
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/supplier-portal/accounts")
def create_supplier_account(
    data: SupplierAccountCreate,
    _user: dict = Depends(require_auth),
):
    ph = hashlib.sha256(data.password.encode()).hexdigest()
    try:
        with _db() as conn:
            conn.execute(
                """INSERT INTO supplier_users
                   (supplier_id, username, password_hash, email, contact_name)
                   VALUES (?, ?, ?, ?, ?)""",
                (data.supplier_id, data.username, ph, data.email, data.contact_name),
            )
    except Exception as e:
        raise HTTPException(409, f"Account already exists or username taken: {e}")
    return {"success": True}


@app.get("/supplier-portal/accounts")
def list_supplier_accounts(_user: dict = Depends(require_auth)):
    with _db() as conn:
        rows = conn.execute(
            """SELECT su.id, su.supplier_id, su.username, su.email,
                      su.contact_name, su.created_at, os.name AS supplier_name
               FROM supplier_users su
               JOIN onboarded_suppliers os ON os.id = su.supplier_id
               ORDER BY su.created_at DESC"""
        ).fetchall()
    return [_row_to_dict(r) for r in rows]


@app.get("/supplier-portal/accounts/{supplier_id}/status")
def get_supplier_account_status(
    supplier_id: int,
    _user: dict = Depends(require_auth),
):
    with _db() as conn:
        row = conn.execute(
            "SELECT id, username, email, contact_name, created_at FROM supplier_users WHERE supplier_id=?",
            (supplier_id,),
        ).fetchone()
    return {"exists": row is not None, "account": _row_to_dict(row)}


@app.post("/supplier-portal/notify")
def notify_supplier(
    data: NotifySupplierPayload,
    _user: dict = Depends(require_auth),
):
    with _db() as conn:
        acct = conn.execute(
            "SELECT id FROM supplier_users WHERE supplier_id=?",
            (data.supplier_id,),
        ).fetchone()
        if not acct:
            raise HTTPException(404, "No supplier portal account. Create one first.")
        conn.execute(
            """INSERT INTO supplier_notifications
               (supplier_id, risk_category, message, immediate_actions, long_term_actions)
               VALUES (?, ?, ?, ?, ?)""",
            (
                data.supplier_id,
                data.risk_category,
                data.message,
                json.dumps(data.immediate_actions),
                json.dumps(data.long_term_actions),
            ),
        )
    return {"success": True}


@app.get("/supplier-portal/action-log")
def get_supplier_action_log(_user: dict = Depends(require_auth)):
    with _db() as conn:
        rows = conn.execute(
            """SELECT sal.*, os.name AS supplier_name
               FROM supplier_action_log sal
               JOIN onboarded_suppliers os ON os.id = sal.supplier_id
               ORDER BY sal.created_at DESC
               LIMIT 300"""
        ).fetchall()
    return [_row_to_dict(r) for r in rows]


@app.put("/supplier-portal/action-log/mark-seen")
def mark_action_log_seen(_user: dict = Depends(require_auth)):
    with _db() as conn:
        conn.execute("UPDATE supplier_action_log SET admin_seen=1 WHERE admin_seen=0")
    return {"success": True}


@app.get("/supplier-portal/documents/{doc_id}")
def download_supplier_document(
    doc_id: int,
    _user: dict = Depends(require_auth),
):
    with _db() as conn:
        row = conn.execute(
            "SELECT filename, file_data FROM supplier_documents WHERE id=?",
            (doc_id,),
        ).fetchone()
    if not row:
        raise HTTPException(404, "Document not found")
    return Response(
        content=bytes(row["file_data"]),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{row["filename"]}"'},
    )


# ─────────────────────────────────────────────────────────────────────────────
# Supplier Portal — Supplier endpoints  (require supplier JWT)
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/supplier-portal/auth/login")
def supplier_login(data: SupplierLoginRequest):
    with _db() as conn:
        row = conn.execute(
            "SELECT * FROM supplier_users WHERE username=?",
            (data.username,),
        ).fetchone()
    if not row:
        raise HTTPException(401, "Invalid username or password")
    ph = hashlib.sha256(data.password.encode()).hexdigest()
    if ph != row["password_hash"]:
        raise HTTPException(401, "Invalid username or password")
    with _db() as conn:
        supplier = conn.execute(
            "SELECT name, country FROM onboarded_suppliers WHERE id=?",
            (row["supplier_id"],),
        ).fetchone()
    token = _make_supplier_token(row["supplier_id"], row["username"])
    return {
        "token":            token,
        "supplier_id":      row["supplier_id"],
        "username":         row["username"],
        "contact_name":     row["contact_name"],
        "supplier_name":    supplier["name"]    if supplier else "",
        "supplier_country": supplier["country"] if supplier else "",
    }


@app.get("/supplier-portal/notifications")
def get_my_notifications(user: dict = Depends(require_supplier_auth)):
    sid = user["supplier_id"]
    with _db() as conn:
        rows = conn.execute(
            "SELECT * FROM supplier_notifications WHERE supplier_id=? ORDER BY sent_at DESC",
            (sid,),
        ).fetchall()
        docs = conn.execute(
            """SELECT id, notification_id, filename, file_size, note, uploaded_at
               FROM supplier_documents WHERE supplier_id=?""",
            (sid,),
        ).fetchall()
    docs_by_notif: Dict[int, list] = {}
    for d in docs:
        d = _row_to_dict(d)
        docs_by_notif.setdefault(d["notification_id"], []).append(d)
    result = []
    for r in rows:
        n = _row_to_dict(r)
        n["immediate_actions"] = json.loads(n.get("immediate_actions") or "[]")
        n["long_term_actions"]  = json.loads(n.get("long_term_actions")  or "[]")
        n["documents"]          = docs_by_notif.get(n["id"], [])
        result.append(n)
    return result


@app.put("/supplier-portal/notifications/{notif_id}/read")
def mark_notification_read(
    notif_id: int,
    user: dict = Depends(require_supplier_auth),
):
    sid = user["supplier_id"]
    with _db() as conn:
        conn.execute(
            "UPDATE supplier_notifications SET is_read=1 WHERE id=? AND supplier_id=?",
            (notif_id, sid),
        )
        conn.execute(
            """INSERT INTO supplier_action_log
               (supplier_id, notification_id, action_type, details)
               VALUES (?, ?, 'notification_read', ?)""",
            (sid, notif_id, json.dumps({"notification_id": notif_id})),
        )
    return {"success": True}


@app.post("/supplier-portal/documents")
async def upload_supplier_document(
    notification_id: int    = Form(...),
    note:            str    = Form(""),
    file:            UploadFile = File(...),
    user:            dict   = Depends(require_supplier_auth),
):
    sid = user["supplier_id"]
    with _db() as conn:
        notif = conn.execute(
            "SELECT id FROM supplier_notifications WHERE id=? AND supplier_id=?",
            (notification_id, sid),
        ).fetchone()
    if not notif:
        raise HTTPException(404, "Notification not found")
    data = await file.read()
    with _db() as conn:
        cursor = conn.execute(
            """INSERT INTO supplier_documents
               (supplier_id, notification_id, filename, file_data, file_size, note)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (sid, notification_id, file.filename, data, len(data), note.strip() or None),
        )
        doc_id = cursor.lastrowid
        conn.execute(
            """INSERT INTO supplier_action_log
               (supplier_id, notification_id, action_type, details)
               VALUES (?, ?, 'document_uploaded', ?)""",
            (sid, notification_id,
             json.dumps({"filename": file.filename, "doc_id": doc_id, "size": len(data)})),
        )
    return {"success": True, "doc_id": doc_id, "filename": file.filename}
