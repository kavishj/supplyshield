import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
from config import HIGH_THRESHOLD, MEDIUM_THRESHOLD  # pyright: ignore[reportMissingImports]

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests, os, time, logging
from dotenv import load_dotenv

load_dotenv(override=False)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("summarizer")

app = FastAPI(title="SummarizerAgent", version="3.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
HTTP = requests.Session()

GROQ_MODEL   = "llama-3.3-70b-versatile"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

COMPONENT_LABELS = {
    "geography":     "geographic concentration risk",
    "news":          "adverse news sentiment",
    "single_source": "single-source supply dependency",
    "lead_time":     "extended lead time vulnerability",
    "financial_health": "financial health risk",
    "on_time_delivery": "on-time delivery performance",
    "contract_expiry":  "contract expiry urgency",
}
SUMMARY_LABELS = {
    "geography":     "geographic concentration",
    "news":          "news sentiment risk",
    "single_source": "single-source dependency",
    "lead_time":     "extended lead time",
    "financial_health": "financial health",
    "on_time_delivery": "delivery performance",
    "contract_expiry":  "contract expiry",
}


def get_groq_key():
    return os.getenv("GROQ_API_KEY", "").strip()


# ── Structured extraction (rule-based, always runs) ───────────
def extract_structured(data: dict) -> dict:
    """Extract key_concerns, gaps, and top_risk_factor from risk data."""
    c     = data.get("components", {})
    ofac  = data.get("ofac_status", "CLEAR")
    cat   = data.get("risk_category", "LOW")
    score = data.get("risk_score", 0)

    # Top risk factor (exclude ofac component from weighted display)
    scored = {k: v for k, v in c.items() if k != "ofac"}
    top_key         = max(scored, key=scored.get) if scored else "geography"
    top_risk_factor = COMPONENT_LABELS.get(top_key, top_key)

    # Key concerns — all components scoring > 0.3
    key_concerns = []
    for k, v in sorted(scored.items(), key=lambda x: -x[1]):
        if v > 0.3:
            key_concerns.append(f"{COMPONENT_LABELS.get(k, k)} scored {v:.2f}/1.0")
    if ofac == "SANCTIONED":
        key_concerns.insert(0, "Supplier appears on OFAC Specially Designated Nationals list")
    if not key_concerns:
        key_concerns = [f"Overall risk score {score:.3f} in {cat} tier"]

    # Information gaps
    gaps = []
    if not data.get("news_headlines"):
        gaps.append("No live news intelligence available — manual media check recommended")
    if c.get("geography", 0) > 0.5 and not data.get("country"):
        gaps.append("Country-level geopolitical intelligence not retrieved")
    if c.get("single_source", 0) == 0 and cat in ("HIGH", "MEDIUM"):
        gaps.append("Sole-source status unconfirmed — verify supply chain redundancy")
    if not gaps:
        gaps = ["Full supplier financial audit not yet conducted"]

    return {
        "top_risk_factor": top_risk_factor,
        "key_concerns":    key_concerns[:4],
        "gaps":            gaps[:3],
    }


# ── Rule-based summary text ───────────────────────────────────
def rule_based_summary(data: dict, top_recommendations: str = "") -> str:
    c   = data.get("components", {})
    scored = {k: v for k, v in c.items() if k != "ofac"}
    top = max(scored, key=scored.get) if scored else "geography"

    ofac_line = (
        f"{data['company_name']} flagged on OFAC SDN list with {data.get('ofac_matches') or 0} match(es)."
        if data["ofac_status"] == "SANCTIONED"
        else f"{data['company_name']} returned CLEAR across all {data.get('records_searched') or 18708:,} OFAC SDN records."
    )
    gate_line = {
        "BLOCKED":           "ProcurementGate has BLOCKED this supplier pending legal review.",
        "REQUIRES_APPROVAL": "ProcurementGate has escalated this to procurement management for approval.",
        "AUTO_APPROVED":     "ProcurementGate has AUTO-APPROVED this supplier for standard onboarding.",
    }.get(data["gate_decision"], "")

    rec_line = (
        f"\n\nTop recommended action: {top_recommendations}"
        if top_recommendations else ""
    )

    risk_score = data.get("risk_score") or 0.0
    return (
        f"{data['company_name']} carries a composite risk score of {risk_score:.3f}/1.000 "
        f"— placing it in the {data.get('risk_category', 'UNKNOWN')} risk tier.\n\n"
        f"{ofac_line}\n\n"
        f"The dominant risk driver is {SUMMARY_LABELS.get(top, top)} (component score: {c.get(top, 0):.3f}). "
        f"This factor contributes most significantly to the overall exposure profile.\n\n"
        f"{gate_line} Recommended action: {data.get('recommendation', 'N/A')}"
        f"{rec_line}"
    )


class SummaryRequest(BaseModel):
    company_name:         str
    country:              str   = "N/A"
    ofac_status:          str
    ofac_matches:         int
    records_searched:     int   = 18708
    risk_score:           float
    risk_category:        str
    gate_decision:        str
    recommendation:       str
    components:           dict
    news_headlines:       list  = []
    top_recommendations:  str   = ""


@app.get("/health")
def health():
    token = get_groq_key()
    return {
        "agent":                "SummarizerAgent",
        "status":               "healthy",
        "model":                GROQ_MODEL,
        "groq_key_configured":  bool(token),
        "version":              "3.0.0",
    }


@app.post("/summarize")
def summarize(req: SummaryRequest):
    start      = time.perf_counter()
    groq_key   = get_groq_key()
    data       = req.model_dump()

    # Always extract structured fields
    structured = extract_structured(data)

    if not groq_key:
        return {
            "summary":          rule_based_summary(data, req.top_recommendations),
            "top_risk_factor":  structured["top_risk_factor"],
            "key_concerns":     structured["key_concerns"],
            "gaps":             structured["gaps"],
            "model":            "rule-based-fallback",
            "success":          True,
            "elapsed_ms":       round((time.perf_counter() - start) * 1000, 2),
        }

    news_text = ""
    if req.news_headlines:
        news_text = "Recent news headlines: " + " | ".join(req.news_headlines[:3])

    # ── Risk-level tone instruction ────────────────────────────
    if req.ofac_status == "SANCTIONED":
        tone = (
            "This is a sanctions compliance emergency. Use urgent, direct language.\n"
            "Paragraph 1: State the OFAC SDN match and its immediate legal implications.\n"
            "Paragraph 2: Business and financial risks of continued engagement.\n"
            "Paragraph 3: Mandatory next steps — freeze all purchase orders, engage legal "
            "counsel within 24 hours, and escalate to senior management."
        )
    elif req.risk_score >= HIGH_THRESHOLD:
        tone = (
            "This supplier is HIGH risk. Use assertive, escalation-oriented language.\n"
            "Paragraph 1: Overall risk profile — score, category, and gate decision.\n"
            "Paragraph 2: The two highest-scoring risk drivers and their operational impact.\n"
            "Paragraph 3: Required escalation steps before any purchase order is placed."
        )
    elif req.risk_score >= MEDIUM_THRESHOLD:
        tone = (
            "This supplier is MEDIUM risk. Use measured, due-diligence language.\n"
            "Paragraph 1: Overall risk profile — score, category, and gate decision.\n"
            "Paragraph 2: Primary risk driver and any notable information gaps.\n"
            "Paragraph 3: Enhanced due-diligence actions recommended before contract renewal."
        )
    else:
        tone = (
            "This supplier is LOW risk. Use reassuring but precise language.\n"
            "Paragraph 1: Confirm low exposure with score and category.\n"
            "Paragraph 2: Any residual risk factors worth monitoring.\n"
            "Paragraph 3: Standard onboarding approval with periodic review cadence."
        )

    # ── Build top risk drivers string ─────────────────────────
    scored = {k: v for k, v in req.components.items() if k != "ofac" and v > 0}
    top_drivers = ", ".join(
        f"{SUMMARY_LABELS.get(k, k)}={v:.2f}"
        for k, v in sorted(scored.items(), key=lambda x: -x[1])[:4]
    )

    system_prompt = (
        "You are a senior procurement compliance officer writing executive risk briefings. "
        "Base your response strictly on the supplier data provided. "
        "Do not invent facts, add disclaimers, or repeat the input data verbatim. "
        "Write in plain business English. Be concise and actionable."
    )

    user_prompt = (
        f"Write a 3-paragraph executive risk briefing for the following supplier.\n\n"
        f"Supplier: {req.company_name}\n"
        f"Country: {req.country}\n"
        f"OFAC Status: {req.ofac_status} ({req.ofac_matches} matches)\n"
        f"Risk Score: {req.risk_score:.3f} / 1.000\n"
        f"Risk Category: {req.risk_category}\n"
        f"Gate Decision: {req.gate_decision}\n"
        f"Top Risk Drivers: {top_drivers}\n"
        f"{news_text}\n"
        f"Recommended Action: {req.recommendation}\n\n"
        f"Tone and structure:\n{tone}\n\n"
        f"Keep the total response under 200 words."
    )

    try:
        resp = HTTP.post(
            GROQ_API_URL,
            headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
            json={
                "model": GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": user_prompt},
                ],
                "max_tokens": 350,
                "temperature": 0.3,
                "top_p": 0.9,
            },
            timeout=45,
        )

        if resp.status_code in (429, 503):
            return {
                "summary":         rule_based_summary(data, req.top_recommendations),
                "top_risk_factor": structured["top_risk_factor"],
                "key_concerns":    structured["key_concerns"],
                "gaps":            structured["gaps"],
                "model":           GROQ_MODEL,
                "success":         False,
                "error":           f"Groq {resp.status_code} — fallback used",
                "elapsed_ms":      round((time.perf_counter() - start) * 1000, 2),
            }

        resp.raise_for_status()
        result = resp.json()
        text   = result["choices"][0]["message"]["content"].strip()

        if req.top_recommendations and text:
            text += f"\n\nTop recommended action: {req.top_recommendations}"

        return {
            "summary":          text or rule_based_summary(data, req.top_recommendations),
            "top_risk_factor":  structured["top_risk_factor"],
            "key_concerns":     structured["key_concerns"],
            "gaps":             structured["gaps"],
            "model":            GROQ_MODEL,
            "success":          True,
            "elapsed_ms":       round((time.perf_counter() - start) * 1000, 2),
        }

    except Exception as e:
        logger.warning(f"Groq call failed: {e} — using fallback")
        return {
            "summary":          rule_based_summary(data, req.top_recommendations),
            "top_risk_factor":  structured["top_risk_factor"],
            "key_concerns":     structured["key_concerns"],
            "gaps":             structured["gaps"],
            "model":            GROQ_MODEL,
            "success":          False,
            "error":            str(e),
            "elapsed_ms":       round((time.perf_counter() - start) * 1000, 2),
        }
