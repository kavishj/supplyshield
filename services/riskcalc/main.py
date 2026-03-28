import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
from config import (COUNTRY_RISK, DEFAULT_WEIGHTS, ONBOARDED_WEIGHTS, EXPANDED_WEIGHTS,
                    HIGH_THRESHOLD, MEDIUM_THRESHOLD,
                    CYBER_POSTURE_MAP, LEAD_TIME_VARIABILITY_MAP)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import time, logging
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("riskcalc")

app = FastAPI(title="RiskCalculatorAgent", version="3.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

NEWS_RISK_MAP       = {"HIGH": 0.8, "MEDIUM": 0.4, "LOW": 0.1, "NONE": 0.0}
FINANCIAL_HEALTH_MAP = {"Poor": 0.85, "Fair": 0.45, "Good": 0.05}
TIER_RISK_MAP       = {"Tier 1": 0.0, "Tier 2": 0.3, "Tier 3": 0.6}


def _lead_time_score(weeks: float) -> float:
    if weeks <= 0:  return 0.0   # invalid / unknown — no penalty
    if weeks <= 8:  return 0.0
    if weeks <= 16: return 0.5 * (weeks - 8) / 8
    return min(1.0, 0.5 + (weeks - 16) / 32)


def _on_time_score(rate: float) -> float:
    """0-100% rate → 0.0–1.0 risk (lower on-time = higher risk)."""
    rate = max(0.0, min(100.0, rate))   # clamp to valid range
    if rate >= 95: return 0.0
    if rate >= 85: return 0.2
    if rate >= 70: return 0.5
    return 0.85


def _contract_expiry_score(days_remaining: Optional[int]) -> float:
    if days_remaining is None: return 0.0
    if days_remaining <= 30:   return 0.90
    if days_remaining <= 90:   return 0.55
    if days_remaining <= 180:  return 0.25
    return 0.0


# ── New metric scoring functions (13-factor model) ─────────────

def _fill_rate_score(rate: float) -> float:
    """Order fill rate / OTIF 'in-full' %  →  0.0–1.0 risk."""
    rate = max(0.0, min(100.0, rate))
    if rate >= 95: return 0.0
    if rate >= 85: return 0.20
    if rate >= 70: return 0.55
    return 0.90


def _lead_time_variability_score(variability: str) -> float:
    """Low / Medium / High variability  →  0.0–1.0 risk."""
    return LEAD_TIME_VARIABILITY_MAP.get(variability.strip().capitalize(), 0.40)


def _audit_pass_rate_score(rate: float) -> float:
    """Compliance audit pass rate %  →  0.0–1.0 risk."""
    rate = max(0.0, min(100.0, rate))
    if rate >= 90: return 0.0
    if rate >= 75: return 0.30
    if rate >= 60: return 0.60
    return 0.90


def _improvement_index_score(rate: float) -> float:
    """Corrective-action closure rate %  →  0.0–1.0 risk."""
    rate = max(0.0, min(100.0, rate))
    if rate >= 85: return 0.0
    if rate >= 65: return 0.30
    if rate >= 45: return 0.60
    return 0.85


def _cyber_posture_score(posture: str) -> float:
    """Poor / Fair / Good  →  0.0–1.0 risk."""
    return CYBER_POSTURE_MAP.get(posture.strip().capitalize(), 0.40)


def _disruption_frequency_score(incidents: int) -> float:
    """Supply chain incidents in past 12 months  →  0.0–1.0 risk."""
    if incidents <= 0: return 0.0
    if incidents == 1: return 0.25
    if incidents <= 3: return 0.55
    return 0.90


def _normalise_weights(w: dict) -> dict:
    """Ensure weights sum to 1.0. Falls back to DEFAULT_WEIGHTS if all zero."""
    total = sum(w.values())
    if total == 0:
        logger.warning("All custom weights are zero — falling back to DEFAULT_WEIGHTS")
        return dict(DEFAULT_WEIGHTS)
    return {k: v / total for k, v in w.items()}


class ScoreRequest(BaseModel):
    ofac_status:           str
    country:               Optional[str]   = None
    geo_concentration:     float           = 0.5
    single_source:         bool            = False
    lead_time_weeks:       float           = 12.0
    news_risk:             str             = "NONE"
    # Custom weights (from analysis form — override defaults if provided)
    custom_weights:        Optional[dict]  = None
    # Extended onboarded-supplier fields (7-factor model)
    financial_health:        Optional[str]   = None   # Good / Fair / Poor
    on_time_delivery_rate:   Optional[float] = None   # 0–100 %
    contract_days_remaining: Optional[int]   = None   # days until expiry
    tier_level:              Optional[str]   = None   # Tier 1 / 2 / 3
    # New expanded fields (13-factor model)
    order_fill_rate:         Optional[float] = None   # OTIF in-full %, 0–100
    lead_time_variability:   Optional[str]   = None   # Low / Medium / High
    audit_pass_rate:         Optional[float] = None   # compliance audit pass %, 0–100
    improvement_index:       Optional[float] = None   # corrective action closure %, 0–100
    cyber_posture:           Optional[str]   = None   # Poor / Fair / Good
    disruption_frequency:    Optional[int]   = None   # supply chain incidents per year


@app.get("/health")
def health():
    return {
        "agent":            "RiskCalculatorAgent",
        "status":           "healthy",
        "default_weights":  DEFAULT_WEIGHTS,
        "onboarded_weights": ONBOARDED_WEIGHTS,
        "version":          "3.0.0",
    }


@app.post("/score")
def score(req: ScoreRequest):
    start = time.perf_counter()

    # ── Base component scores ──────────────────────────────────
    geo_score  = (COUNTRY_RISK.get(req.country.upper().strip(), req.geo_concentration)
                  if req.country else req.geo_concentration)
    geo_score  = max(0.0, min(1.0, geo_score))   # clamp in case geo_concentration out of range
    news_score = NEWS_RISK_MAP.get((req.news_risk or "NONE").upper(), 0.0)

    components = {
        "ofac":          1.0 if req.ofac_status == "SANCTIONED" else 0.0,
        "geography":     geo_score,
        "news":          news_score,
        "single_source": 0.8 if req.single_source else 0.0,
        "lead_time":     _lead_time_score(req.lead_time_weeks),
    }

    # ── Determine which weight set to use ─────────────────────
    has_extended = any([
        req.financial_health is not None,
        req.on_time_delivery_rate is not None,
        req.contract_days_remaining is not None,
    ])
    has_expanded = any([
        req.order_fill_rate is not None,
        req.lead_time_variability is not None,
        req.audit_pass_rate is not None,
        req.improvement_index is not None,
        req.cyber_posture is not None,
        req.disruption_frequency is not None,
    ])

    if req.custom_weights:
        raw_custom = {k: float(v) for k, v in req.custom_weights.items() if float(v) > 0}
        if has_expanded:
            # Performance metrics take fixed weights from EXPANDED_WEIGHTS.
            # User's custom weights (geo/news/ss/lt) fill the remaining budget.
            NEW_METRIC_KEYS = {
                "order_fill_rate", "lead_time_variability", "audit_pass_rate",
                "improvement_index", "cyber_posture", "disruption_frequency",
            }
            active_fixed = {k: EXPANDED_WEIGHTS[k] for k in NEW_METRIC_KEYS if k in components}
            fixed_total  = sum(active_fixed.values())
            remaining    = max(0.01, 1.0 - fixed_total)
            custom_total = sum(raw_custom.values())
            scaled       = {k: (v / custom_total) * remaining for k, v in raw_custom.items()} \
                           if custom_total > 0 else {}
            weights = {**active_fixed, **scaled}
        else:
            weights = _normalise_weights(raw_custom)
    elif has_expanded:
        weights = dict(EXPANDED_WEIGHTS)
    elif has_extended:
        weights = dict(ONBOARDED_WEIGHTS)
    else:
        weights = dict(DEFAULT_WEIGHTS)

    # ── Extended + expanded components ────────────────────────
    if has_extended or has_expanded or req.custom_weights:
        # 7-factor onboarded fields
        if req.financial_health is not None:
            components["financial_health"] = FINANCIAL_HEALTH_MAP.get(req.financial_health, 0.4)
        if req.on_time_delivery_rate is not None:
            components["on_time_delivery"] = _on_time_score(req.on_time_delivery_rate)
        if req.contract_days_remaining is not None:
            components["contract_expiry"] = _contract_expiry_score(req.contract_days_remaining)
        # 13-factor expanded fields
        if req.order_fill_rate is not None:
            components["order_fill_rate"] = _fill_rate_score(req.order_fill_rate)
        if req.lead_time_variability is not None:
            components["lead_time_variability"] = _lead_time_variability_score(req.lead_time_variability)
        if req.audit_pass_rate is not None:
            components["audit_pass_rate"] = _audit_pass_rate_score(req.audit_pass_rate)
        if req.improvement_index is not None:
            components["improvement_index"] = _improvement_index_score(req.improvement_index)
        if req.cyber_posture is not None:
            components["cyber_posture"] = _cyber_posture_score(req.cyber_posture)
        if req.disruption_frequency is not None:
            components["disruption_frequency"] = _disruption_frequency_score(req.disruption_frequency)

    # ── Final score ────────────────────────────────────────────
    score_val = round(
        min(1.0, sum(components.get(k, 0) * weights.get(k, 0) for k in weights)),
        4,
    )

    # Compliance override — sanctioned supplier always HIGH
    if req.ofac_status == "SANCTIONED":
        score_val = max(score_val, 0.90)

    if score_val >= HIGH_THRESHOLD:   category = "HIGH"
    elif score_val >= MEDIUM_THRESHOLD: category = "MEDIUM"
    else:                               category = "LOW"

    if req.ofac_status == "SANCTIONED":
        rec = "BLOCK — Supplier on OFAC SDN list. Immediate legal review required."
    elif category == "HIGH":
        rec = "ESCALATE — High risk. Requires procurement manager approval."
    elif category == "MEDIUM":
        rec = "REVIEW — Medium risk. Enhanced due diligence recommended."
    else:
        rec = "APPROVE — Low risk. Standard onboarding applies."

    elapsed = round((time.perf_counter() - start) * 1000, 2)
    logger.info(f"Scored: {score_val} ({category}) in {elapsed}ms | weights={'onboarded' if has_extended else 'standard'}")

    return {
        "score":             score_val,
        "category":          category,
        "recommendation":    rec,
        "components":        components,
        "weights":           weights,
        "weights_mode":      "custom" if req.custom_weights else ("expanded" if has_expanded else ("onboarded" if has_extended else "standard")),
        "approval_required": score_val >= HIGH_THRESHOLD,
        "elapsed_ms":        elapsed,
    }
