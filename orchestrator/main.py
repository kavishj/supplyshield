import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
from config import (DEFAULT_WEIGHTS, RECORDS_SEARCHED_FALLBACK,
                    TREND_DETERIORATING_DELTA, TREND_IMPROVING_DELTA,
                    MEDIUM_THRESHOLD)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests, time, logging, os, json, sqlite3
from typing import Optional
from dotenv import load_dotenv
from datetime import date, datetime

load_dotenv(override=False)

DB_PATH = Path(os.getenv("DB_PATH", r"C:\Users\KAVISH\supplyshield_final\data\suppliers.db"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("orchestrator")

app = FastAPI(title="SupplyShield Orchestrator", version="3.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ── Agent URLs ────────────────────────────────────────────────
GEOINTEL_URL    = os.getenv("GEOINTEL_URL",    "http://127.0.0.1:8001")
RISKCALC_URL    = os.getenv("RISKCALC_URL",    "http://127.0.0.1:8002")
GATE_URL        = os.getenv("GATE_URL",         "http://127.0.0.1:8003")
SUMMARIZER_URL  = os.getenv("SUMMARIZER_URL",   "http://127.0.0.1:8004")
RECOMMENDER_URL = os.getenv("RECOMMENDER_URL",  "http://127.0.0.1:8005")


class AnalyzeRequest(BaseModel):
    company_name:           str
    country:                Optional[str]   = None
    geo_concentration:      float           = 0.5
    single_source:          bool            = False
    lead_time_weeks:        float           = 12.0
    include_summary:        bool            = True
    include_recommendations: bool           = False   # on-demand only
    # Custom weights (from analysis form)
    custom_weights:         Optional[dict]  = None
    # Company context for recommender
    company_name_buyer:     Optional[str]   = None
    company_industry:       Optional[str]   = None
    # Onboarded supplier extended fields (7-factor)
    annual_spend_usd:       Optional[float] = None
    sole_source_onboarded:  Optional[bool]  = None
    tier_level:             Optional[str]   = None
    on_time_delivery_rate:  Optional[float] = None
    years_in_relationship:  Optional[int]   = None
    financial_health:       Optional[str]   = None
    contract_expiry:        Optional[str]   = None
    # New expanded fields (13-factor)
    order_fill_rate:        Optional[float] = None   # OTIF in-full %, 0–100
    lead_time_variability:  Optional[str]   = None   # Low / Medium / High
    audit_pass_rate:        Optional[float] = None   # compliance audit pass %, 0–100
    improvement_index:      Optional[float] = None   # corrective action closure %, 0–100
    cyber_posture:          Optional[str]   = None   # Poor / Fair / Good
    disruption_frequency:   Optional[int]   = None   # supply chain incidents/yr
    # Buyer-side resilience context (not scored — fed to recommender)
    inventory_buffer_days:  Optional[int]   = None   # days of supply on hand
    has_rto_defined:        Optional[bool]  = None   # Recovery Time Objective documented


class RecommendOnlyRequest(BaseModel):
    """For on-demand recommendation generation from the Recommendations page."""
    supplier_name:          str
    country:                Optional[str]   = None
    category:               Optional[str]   = None
    risk_score:             float           = 0.5
    risk_category:          str             = "MEDIUM"
    risk_components:        dict            = {}
    ofac_status:            str             = "CLEAR"
    news_risk:              str             = "NONE"
    news_headlines:         list            = []
    summary:                str             = ""
    key_concerns:           list            = []
    gaps:                   list            = []
    company_name_buyer:     Optional[str]   = None
    company_industry:       Optional[str]   = None
    custom_weights:         Optional[dict]  = None
    annual_spend_usd:       Optional[float] = None
    sole_source:            bool            = False
    tier_level:             Optional[str]   = None
    on_time_delivery_rate:  Optional[float] = None
    years_in_relationship:  Optional[int]   = None
    financial_health:       Optional[str]   = None
    contract_expiry:        Optional[str]   = None
    order_fill_rate:        Optional[float] = None
    lead_time_variability:  Optional[str]   = None
    audit_pass_rate:        Optional[float] = None
    improvement_index:      Optional[float] = None
    cyber_posture:          Optional[str]   = None
    disruption_frequency:   Optional[int]   = None
    inventory_buffer_days:  Optional[int]   = None
    has_rto_defined:        Optional[bool]  = None


def call_agent(url: str, payload: dict, timeout: int = 15) -> dict:
    resp = requests.post(url, json=payload, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


# ── DB helpers ────────────────────────────────────────────────
def _safe_json(val, default: str):
    """Safely decode a JSON string from the DB, returning a parsed default on failure."""
    try:
        return json.loads(val or default)
    except (json.JSONDecodeError, TypeError):
        logger.warning(f"Corrupted JSON in recommendations DB, using default: {val!r}")
        return json.loads(default)


def _ensure_recommendations_table():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS recommendations (
            id                     INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_name          TEXT NOT NULL,
            risk_score             REAL,
            risk_category          TEXT,
            immediate_actions      TEXT,
            long_term_actions      TEXT,
            web_sources            TEXT,
            action_status          TEXT DEFAULT '{}',
            top_recs_for_summary   TEXT,
            generated_at           TEXT DEFAULT (datetime('now')),
            model                  TEXT
        )
    """)
    conn.commit()
    conn.close()


@app.on_event("startup")
def _startup():
    _ensure_recommendations_table()


def save_recommendation(supplier_name: str, risk_score: float, risk_category: str,
                        rec_result: dict):
    conn = sqlite3.connect(DB_PATH)
    # Upsert: delete old, insert new
    conn.execute("DELETE FROM recommendations WHERE UPPER(supplier_name) = UPPER(?)",
                 (supplier_name,))
    conn.execute("""
        INSERT INTO recommendations
            (supplier_name, risk_score, risk_category,
             immediate_actions, long_term_actions, web_sources,
             action_status, top_recs_for_summary, generated_at, model)
        VALUES (?, ?, ?, ?, ?, ?, '{}', ?, datetime('now'), ?)
    """, (
        supplier_name,
        risk_score,
        risk_category,
        json.dumps(rec_result.get("immediate_actions", [])),
        json.dumps(rec_result.get("long_term_actions", [])),
        json.dumps(rec_result.get("web_sources", [])),
        rec_result.get("top_recommendations_for_summary", ""),
        rec_result.get("model", ""),
    ))
    conn.commit()
    conn.close()


def get_recommendation(supplier_name: str) -> Optional[dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT * FROM recommendations WHERE UPPER(supplier_name) = UPPER(?)",
        (supplier_name,),
    ).fetchone()
    conn.close()
    if not row:
        return None
    r = dict(row)
    r["immediate_actions"] = _safe_json(r.get("immediate_actions"), "[]")
    r["long_term_actions"]  = _safe_json(r.get("long_term_actions"),  "[]")
    r["web_sources"]        = _safe_json(r.get("web_sources"),         "[]")
    r["action_status"]      = _safe_json(r.get("action_status"),       "{}")
    return r


def get_previous_score(supplier_name: str) -> Optional[float]:
    """Return the last_score stored in the suppliers table, or None if not found."""
    try:
        conn = sqlite3.connect(DB_PATH)
        row = conn.execute(
            "SELECT last_score FROM suppliers WHERE UPPER(name) = UPPER(?)",
            (supplier_name,),
        ).fetchone()
        conn.close()
        return float(row[0]) if row and row[0] is not None else None
    except Exception:
        return None


def compute_trend(current: float, previous: Optional[float]) -> tuple:
    """Return (trend_label, delta) comparing current to previous score."""
    if previous is None:
        return "STABLE", None
    delta = round(current - previous, 4)
    if delta >= TREND_DETERIORATING_DELTA:
        return "DETERIORATING", delta
    if delta <= TREND_IMPROVING_DELTA:
        return "IMPROVING", delta
    return "STABLE", delta


def _contract_days_remaining(expiry_str: Optional[str]) -> Optional[int]:
    if not expiry_str:
        return None
    try:
        exp = datetime.strptime(expiry_str, "%Y-%m-%d").date()
        return (exp - date.today()).days
    except Exception:
        return None


# ── Health ────────────────────────────────────────────────────
@app.get("/health")
def health():
    agents = {
        "geointel":    GEOINTEL_URL,
        "riskcalc":    RISKCALC_URL,
        "gate":        GATE_URL,
        "summarizer":  SUMMARIZER_URL,
        "recommender": RECOMMENDER_URL,
    }
    statuses = {}
    for name, url in agents.items():
        try:
            r = requests.get(f"{url}/health", timeout=3)
            statuses[name] = "healthy" if r.status_code == 200 else "unhealthy"
        except Exception:
            statuses[name] = "unreachable"

    return {
        "orchestrator": "healthy",
        "agents":        statuses,
        "all_healthy":   all(s == "healthy" for s in statuses.values()),
    }


# ── Batch ─────────────────────────────────────────────────────
@app.post("/batch")
def batch_analyze():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM suppliers")
    suppliers = [dict(row) for row in c.fetchall()]
    conn.close()

    results, errors = [], []
    write_conn = sqlite3.connect(DB_PATH)

    for supplier in suppliers:
        try:
            geo = requests.post(f"{GEOINTEL_URL}/screen",
                  json={"company_name": supplier["name"], "skip_news": True}, timeout=15).json()

            risk = requests.post(f"{RISKCALC_URL}/score", json={
                "ofac_status":    geo.get("status", "CLEAR"),
                "country":        supplier.get("country") or None,
                "single_source":  bool(supplier.get("single_source", False)),
                "lead_time_weeks": float(supplier["lead_time"]) if supplier.get("lead_time") else 12.0,
                "news_risk":      geo.get("news_risk", "NONE"),
            }, timeout=15).json()

            gate = requests.post(f"{GATE_URL}/evaluate", json={
                "company_name":  supplier["name"],
                "risk_score":    risk["score"],
                "risk_category": risk["category"],
                "ofac_status":   geo["status"],
            }, timeout=15).json()

            write_conn.execute("""
                UPDATE suppliers
                SET last_screened = datetime('now'), last_score = ?, last_decision = ?
                WHERE id = ?
            """, (risk["score"], gate["decision"], supplier["id"]))

            results.append({
                "id":             supplier["id"],
                "name":           supplier["name"],
                "country":        supplier["country"],
                "category":       supplier["category"],
                "risk_score":     risk["score"],
                "risk_category":  risk["category"],
                "ofac_status":    geo["status"],
                "gate_decision":  gate["decision"],
                "recommendation": risk["recommendation"],
                "news_risk":      geo.get("news_risk", "NONE"),
            })
        except Exception as e:
            errors.append({"supplier": supplier["name"], "error": str(e)})

    write_conn.commit()
    write_conn.close()
    results.sort(key=lambda x: x["risk_score"], reverse=True)
    return {
        "total_screened":    len(results),
        "total_errors":      len(errors),
        "blocked":           len([r for r in results if r["gate_decision"] == "BLOCKED"]),
        "requires_approval": len([r for r in results if r["gate_decision"] == "REQUIRES_APPROVAL"]),
        "auto_approved":     len([r for r in results if r["gate_decision"] == "AUTO_APPROVED"]),
        "results":           results,
        "errors":            errors,
    }


# ── Suppliers list ────────────────────────────────────────────
@app.get("/suppliers")
def get_suppliers():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM suppliers ORDER BY last_score DESC NULLS LAST")
    suppliers = [dict(row) for row in c.fetchall()]
    conn.close()
    return {"total": len(suppliers), "suppliers": suppliers}


# ── Main analyze pipeline ─────────────────────────────────────
@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    total_start = time.perf_counter()
    agents_log  = []

    # ── Agent 1: GeoIntel ─────────────────────────────────────
    try:
        geo = call_agent(f"{GEOINTEL_URL}/screen", {"company_name": req.company_name})
        agents_log.append({"agent": "GeoIntelAgent", "status": "ok",
                           "elapsed_ms": geo["elapsed_ms"]})
    except Exception as e:
        logger.error(f"GeoIntelAgent failed: {e}")
        return {"error": "GeoIntelAgent unavailable", "detail": str(e)}

    # ── Agent 2: RiskCalc ─────────────────────────────────────
    riskcalc_payload = {
        "ofac_status":    geo["status"],
        "country":        req.country,
        "geo_concentration": req.geo_concentration,
        "single_source":  req.single_source,
        "lead_time_weeks": req.lead_time_weeks,
        "news_risk":      geo["news_risk"],
    }
    if req.custom_weights:
        riskcalc_payload["custom_weights"] = req.custom_weights
    if req.financial_health:
        riskcalc_payload["financial_health"] = req.financial_health
    if req.on_time_delivery_rate is not None:
        riskcalc_payload["on_time_delivery_rate"] = req.on_time_delivery_rate
    if req.contract_expiry:
        riskcalc_payload["contract_days_remaining"] = _contract_days_remaining(req.contract_expiry)
    if req.tier_level:
        riskcalc_payload["tier_level"] = req.tier_level
    # New 13-factor expanded metrics
    if req.order_fill_rate is not None:
        riskcalc_payload["order_fill_rate"] = req.order_fill_rate
    if req.lead_time_variability:
        riskcalc_payload["lead_time_variability"] = req.lead_time_variability
    if req.audit_pass_rate is not None:
        riskcalc_payload["audit_pass_rate"] = req.audit_pass_rate
    if req.improvement_index is not None:
        riskcalc_payload["improvement_index"] = req.improvement_index
    if req.cyber_posture:
        riskcalc_payload["cyber_posture"] = req.cyber_posture
    if req.disruption_frequency is not None:
        riskcalc_payload["disruption_frequency"] = req.disruption_frequency

    try:
        risk = call_agent(f"{RISKCALC_URL}/score", riskcalc_payload)
        agents_log.append({"agent": "RiskCalculatorAgent", "status": "ok",
                           "elapsed_ms": risk["elapsed_ms"]})
    except Exception as e:
        logger.error(f"RiskCalculatorAgent failed: {e}")
        return {"error": "RiskCalculatorAgent unavailable", "detail": str(e)}

    # ── Agent 3: Gate ─────────────────────────────────────────
    ofac_50 = geo.get("ofac_50_percent_rule") or {}
    ofac_50_triggered = ofac_50.get("status") == "BLOCKED"
    ofac_50_pct       = ofac_50.get("cumulative_ofac_pct", 0.0)

    try:
        gate = call_agent(f"{GATE_URL}/evaluate", {
            "company_name":           req.company_name,
            "risk_score":             risk["score"],
            "risk_category":          risk["category"],
            "ofac_status":            geo["status"],
            "ofac_50_rule_triggered": ofac_50_triggered,
            "ofac_50_rule_pct":       ofac_50_pct,
        })
        agents_log.append({"agent": "ProcurementGateAgent", "status": "ok",
                           "elapsed_ms": gate["elapsed_ms"]})
    except Exception as e:
        logger.error(f"ProcurementGateAgent failed: {e}")
        return {"error": "ProcurementGateAgent unavailable", "detail": str(e)}

    # ── Score trend detection ─────────────────────────────────
    previous_score          = get_previous_score(req.company_name)
    score_trend, score_delta = compute_trend(risk["score"], previous_score)

    # ── Agent 4: Summarizer (non-fatal) ───────────────────────
    summary_result = None
    key_concerns   = []
    gaps           = []
    top_risk_factor = ""

    if req.include_summary:
        try:
            summary_result = call_agent(f"{SUMMARIZER_URL}/summarize", {
                "company_name":    req.company_name,
                "country":         req.country or "N/A",
                "ofac_status":     geo["status"],
                "ofac_matches":    geo["match_count"],
                "records_searched": geo["records_searched"],
                "risk_score":      risk["score"],
                "risk_category":   risk["category"],
                "gate_decision":   gate["decision"],
                "recommendation":  risk["recommendation"],
                "components":      risk["components"],
                "news_headlines":  geo["news_headlines"],
                "top_recommendations": "",  # filled after recommender if needed
            }, timeout=35)
            agents_log.append({"agent": "SummarizerAgent", "status": "ok",
                               "elapsed_ms": summary_result["elapsed_ms"]})
            key_concerns    = summary_result.get("key_concerns", [])
            gaps            = summary_result.get("gaps", [])
            top_risk_factor = summary_result.get("top_risk_factor", "")
        except Exception as e:
            logger.warning(f"SummarizerAgent failed (non-fatal): {e}")
            agents_log.append({"agent": "SummarizerAgent", "status": "degraded"})

    # ── Agent 5: Recommender (on-demand or HIGH/MEDIUM auto) ──
    rec_result    = None
    ai_summary    = summary_result["summary"] if summary_result else None

    if req.include_recommendations and risk["category"] in ("HIGH", "MEDIUM"):
        try:
            rec_payload = {
                "supplier_name":        req.company_name,
                "country":              req.country or "N/A",
                "category":             "N/A",
                "risk_score":           risk["score"],
                "risk_category":        risk["category"],
                "risk_components":      risk["components"],
                "ofac_status":          geo["status"],
                "news_risk":            geo.get("news_risk", "NONE"),
                "news_headlines":       geo.get("news_headlines", []),
                "summary":              ai_summary or "",
                "key_concerns":         key_concerns,
                "gaps":                 gaps,
                "company_name":         req.company_name_buyer or "N/A",
                "company_industry":     req.company_industry or "N/A",
                "custom_weights":       req.custom_weights or {},
                "annual_spend_usd":     req.annual_spend_usd,
                "sole_source":          req.sole_source_onboarded or req.single_source,
                "tier_level":           req.tier_level,
                "on_time_delivery_rate": req.on_time_delivery_rate,
                "years_in_relationship": req.years_in_relationship,
                "financial_health":     req.financial_health,
                "contract_expiry":      req.contract_expiry,
                "score_trend":          score_trend,
                "score_delta":          score_delta,
                # New expanded metrics (for specific recommendations)
                "order_fill_rate":      req.order_fill_rate,
                "lead_time_variability": req.lead_time_variability,
                "audit_pass_rate":      req.audit_pass_rate,
                "improvement_index":    req.improvement_index,
                "cyber_posture":        req.cyber_posture,
                "disruption_frequency": req.disruption_frequency,
                # Buyer resilience context
                "inventory_buffer_days": req.inventory_buffer_days,
                "has_rto_defined":       req.has_rto_defined,
            }
            rec_result = call_agent(f"{RECOMMENDER_URL}/recommend", rec_payload, timeout=120)
            agents_log.append({"agent": "RecommenderAgent", "status": "ok",
                               "elapsed_ms": rec_result.get("elapsed_ms", 0)})

            # Persist recommendations
            save_recommendation(req.company_name, risk["score"], risk["category"], rec_result)

            # Append top recommendation to summary (multi-agent teamwork)
            top_rec = rec_result.get("top_recommendations_for_summary", "")
            if top_rec and ai_summary:
                ai_summary = ai_summary.rstrip() + f"\n\nTop recommended action: {top_rec}"

        except Exception as e:
            logger.warning(f"RecommenderAgent failed (non-fatal): {e}")
            agents_log.append({"agent": "RecommenderAgent", "status": "degraded"})

    # ── Check for stored recommendation ───────────────────────
    stored_rec = get_recommendation(req.company_name) if not rec_result else None
    if stored_rec and not rec_result:
        rec_result = stored_rec

    total_elapsed = round((time.perf_counter() - total_start) * 1000, 2)

    return {
        "company_name":           req.company_name,
        "country":                req.country,
        "ofac_status":            geo["status"],
        "ofac_matches":           geo["match_count"],
        "matched_entities":       geo["matched_entities"],
        "records_searched":       geo.get("records_searched", RECORDS_SEARCHED_FALLBACK),
        "risk_score":             risk["score"],
        "risk_category":          risk["category"],
        "risk_components":        risk["components"],
        "weights_mode":           risk.get("weights_mode", "standard"),
        "approval_required":      risk["approval_required"],
        "recommendation":         risk["recommendation"],
        "gate_decision":          gate["decision"],
        "gate_reason":            gate["reason"],
        "gate_action":            gate["action"],
        "ai_summary":             ai_summary,
        "summary_model":          summary_result["model"] if summary_result else None,
        "key_concerns":           key_concerns,
        "gaps":                   gaps,
        "top_risk_factor":        top_risk_factor,
        "news_headlines":         geo.get("news_headlines", []),
        "news_risk":              geo.get("news_risk", "NONE"),
        "news_count":             len(geo.get("news_headlines", [])),
        "ofac_50_percent_rule":   geo.get("ofac_50_percent_rule"),
        "risk_weights":           risk.get("weights", DEFAULT_WEIGHTS),
        "score_trend":            score_trend,
        "score_delta":            score_delta,
        "previous_score":         previous_score,
        "recommendations":        rec_result,
        "agents_log":             agents_log,
        "total_elapsed_ms":       total_elapsed,
    }


# ── On-demand recommend endpoint ─────────────────────────────
@app.post("/recommend")
def recommend_supplier(req: RecommendOnlyRequest):
    """Generate (or regenerate) recommendations for a supplier on-demand."""
    start = time.perf_counter()

    try:
        rec_payload = {
            "supplier_name":        req.supplier_name,
            "country":              req.country or "N/A",
            "category":             req.category or "N/A",
            "risk_score":           req.risk_score,
            "risk_category":        req.risk_category,
            "risk_components":      req.risk_components,
            "ofac_status":          req.ofac_status,
            "news_risk":            req.news_risk,
            "news_headlines":       req.news_headlines,
            "summary":              req.summary,
            "key_concerns":         req.key_concerns,
            "gaps":                 req.gaps,
            "company_name":         req.company_name_buyer or "N/A",
            "company_industry":     req.company_industry or "N/A",
            "custom_weights":       req.custom_weights or {},
            "annual_spend_usd":     req.annual_spend_usd,
            "sole_source":          req.sole_source,
            "tier_level":           req.tier_level,
            "on_time_delivery_rate": req.on_time_delivery_rate,
            "years_in_relationship": req.years_in_relationship,
            "financial_health":     req.financial_health,
            "contract_expiry":      req.contract_expiry,
        }
        result = call_agent(f"{RECOMMENDER_URL}/recommend", rec_payload, timeout=120)
        save_recommendation(req.supplier_name, req.risk_score, req.risk_category, result)
        result["total_elapsed_ms"] = round((time.perf_counter() - start) * 1000, 2)
        return result

    except Exception as e:
        logger.error(f"RecommenderAgent unavailable: {e}")
        return {"error": "RecommenderAgent unavailable", "detail": str(e)}


# ── Get stored recommendation ─────────────────────────────────
@app.get("/recommendations/{supplier_name}")
def get_recommendations(supplier_name: str):
    rec = get_recommendation(supplier_name)
    if not rec:
        return {"found": False}
    return {"found": True, "recommendation": rec}


# ── Update action status (checkbox) ──────────────────────────
@app.post("/recommendations/{supplier_name}/action_status")
def update_action_status(supplier_name: str, body: dict):
    """body: {"action_id": "immediate_0", "completed": true}"""
    rec = get_recommendation(supplier_name)
    if not rec:
        return {"error": "No recommendation found"}

    if "action_id" not in body or "completed" not in body:
        return {"error": "Missing required fields: action_id, completed"}
    status = rec.get("action_status", {})
    status[body["action_id"]] = bool(body["completed"])

    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "UPDATE recommendations SET action_status = ? WHERE UPPER(supplier_name) = UPPER(?)",
        (json.dumps(status), supplier_name),
    )
    conn.commit()
    conn.close()
    return {"success": True, "action_status": status}


# ── Risky suppliers for Recommendations page ──────────────────
@app.get("/risky_suppliers")
def get_risky_suppliers():
    """Return all HIGH and MEDIUM risk suppliers with their stored recommendations."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT s.name, s.country, s.category, s.last_score, s.last_decision, s.last_screened,
               r.id AS rec_id, r.risk_category, r.immediate_actions, r.long_term_actions,
               r.web_sources, r.action_status, r.top_recs_for_summary, r.generated_at, r.model
        FROM suppliers s
        LEFT JOIN recommendations r ON UPPER(s.name) = UPPER(r.supplier_name)
        WHERE s.last_score >= ?
        ORDER BY s.last_score DESC
    """, (MEDIUM_THRESHOLD,)).fetchall()
    conn.close()

    result = []
    for row in rows:
        d = dict(row)
        d["immediate_actions"] = _safe_json(d.get("immediate_actions"), "[]")
        d["long_term_actions"]  = _safe_json(d.get("long_term_actions"),  "[]")
        d["web_sources"]        = _safe_json(d.get("web_sources"),         "[]")
        d["action_status"]      = _safe_json(d.get("action_status"),       "{}")
        result.append(d)

    return {"total": len(result), "suppliers": result}
