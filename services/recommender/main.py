import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
from config import CURRENT_YEAR, MEDIUM_THRESHOLD, CATEGORY_CERTIFICATIONS

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests, os, time, logging, json
from typing import Optional
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor

load_dotenv(override=False)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("recommender")

app = FastAPI(title="RecommenderAgent", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
HTTP = requests.Session()

GROQ_MODEL   = "llama-3.3-70b-versatile"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
SERPER_URL   = "https://google.serper.dev/search"


def get_groq_key() -> str:
    return os.getenv("GROQ_API_KEY", "").strip()

def get_serper_key() -> str:
    return os.getenv("SERPER_API_KEY", "").strip()


# ── Web search ────────────────────────────────────────────────
def serper_search(query: str, num: int = 4) -> list:
    key = get_serper_key()
    if not key:
        return []
    try:
        resp = HTTP.post(
            SERPER_URL,
            headers={"X-API-KEY": key, "Content-Type": "application/json"},
            json={"q": query, "num": num},
            timeout=25,
        )
        resp.raise_for_status()
        return [
            {"title": r.get("title", ""), "url": r.get("link", ""), "snippet": r.get("snippet", "")}
            for r in resp.json().get("organic", [])[:num]
        ]
    except Exception as e:
        logger.warning(f"Serper search failed for '{query}': {e}")
        return []


def get_category_certifications(category: str) -> list:
    """Return industry certifications for a given category (case-insensitive, partial match)."""
    cat_lower = category.lower().strip()
    for key in CATEGORY_CERTIFICATIONS:
        if key in cat_lower or cat_lower in key:
            return CATEGORY_CERTIFICATIONS[key]
    return CATEGORY_CERTIFICATIONS["default"]


def extract_named_companies(snippets: list, exclude_name: str) -> list:
    """
    Pull capitalised proper-noun company names from web snippets.
    Excludes the current supplier name to avoid recommending themselves.
    Returns up to 5 unique names.
    """
    import re
    exclude = exclude_name.upper()
    candidates = set()
    # Match sequences of Title-Case words (2-4 words) likely to be company names
    pattern = re.compile(r'\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){1,3})\b')
    # Words that are clearly not company names
    noise = {
        "Supply", "Chain", "Risk", "Management", "Global", "International",
        "Alternative", "Supplier", "Suppliers", "Company", "Group", "The",
        "This", "These", "Their", "Based", "According", "With", "From",
        "Industry", "Market", "Report", "North", "South", "East", "West",
        "United", "States", "Kingdom", "Europe", "Asia", "Pacific",
    }
    for s in snippets:
        text = s.get("snippet", "") + " " + s.get("title", "")
        for match in pattern.findall(text):
            words = match.split()
            if any(w in noise for w in words):
                continue
            if exclude in match.upper():
                continue
            if len(match) > 5:
                candidates.add(match.strip())
    return sorted(candidates)[:5]


def build_search_queries(supplier_name: str, country: str, category: str,
                         risk_components: dict, ofac_status: str,
                         score_trend: str = "STABLE") -> list:
    """Build context-aware search queries based on the actual risk profile."""
    queries = []

    if not risk_components:
        return [
            f"alternative {category} suppliers {country} supply chain diversification",
            f"{category} supplier audit compliance certification {country}",
            f"{supplier_name} supply chain risk {CURRENT_YEAR}",
        ]

    # Identify all high-scoring drivers (compound risk)
    high_drivers = sorted(
        [(k, v) for k, v in risk_components.items() if v >= MEDIUM_THRESHOLD],
        key=lambda x: -x[1],
    )
    top_driver = high_drivers[0][0] if high_drivers else max(risk_components, key=risk_components.get)

    # Query 1: Supplier-specific intelligence (always)
    if ofac_status == "SANCTIONED":
        queries.append(f"{supplier_name} OFAC sanctions SDN list alternatives {CURRENT_YEAR}")
    elif score_trend == "DETERIORATING":
        queries.append(f"{supplier_name} {country} supply chain risk deterioration {CURRENT_YEAR}")
    else:
        queries.append(f"{supplier_name} {country} financial stability supply chain {CURRENT_YEAR}")

    # Query 2: Top risk driver remediation
    driver_queries = {
        "geography":     f"supply chain diversification away from {country} {category} alternative suppliers",
        "ofac":          f"OFAC sanctions compliance procurement alternatives {category} {country}",
        "news":          f"{supplier_name} {country} adverse news risk mitigation supplier audit {CURRENT_YEAR}",
        "single_source": f"dual sourcing {category} suppliers alternative to {country} supply chain resilience",
        "lead_time":     f"reduce lead time {category} procurement nearshore supplier {country} alternatives",
        "financial_health": f"financially distressed supplier alternatives {category} {country} {CURRENT_YEAR}",
        "on_time_delivery": f"supplier on-time delivery improvement {category} performance management",
        "contract_expiry": f"supplier contract renewal negotiation {category} procurement best practices",
    }
    queries.append(driver_queries.get(top_driver, f"{category} supplier risk mitigation {country}"))

    # Query 3: Compound risk or audit standards
    if len(high_drivers) >= 2:
        second_driver = high_drivers[1][0]
        compound_queries = {
            ("geography", "single_source"): f"sole source {category} supplier {country} geopolitical risk alternative qualification",
            ("geography", "news"):          f"{country} supplier adverse news geopolitical risk procurement mitigation",
            ("ofac", "geography"):          f"OFAC sanctioned country {country} {category} supply chain compliance alternatives",
            ("news", "single_source"):      f"single source {category} supplier adverse media backup qualification {CURRENT_YEAR}",
        }
        pair = (top_driver, second_driver)
        rev_pair = (second_driver, top_driver)
        q3 = compound_queries.get(pair) or compound_queries.get(rev_pair) or \
             f"{category} supplier audit standards compliance certification {country}"
        queries.append(q3)
    else:
        queries.append(f"{category} supplier audit standards compliance certification {country}")

    # Query 4: Named alternative suppliers (always) — find actual company names
    # Target low-risk alternative countries based on current supplier's country
    alt_regions = {
        "CHINA": "Germany OR Japan OR South Korea OR Taiwan",
        "RUSSIA": "Germany OR Poland OR Czech Republic OR Finland",
        "INDIA": "Germany OR Malaysia OR Vietnam OR Mexico",
        "VIETNAM": "Malaysia OR Thailand OR Mexico OR Poland",
        "MEXICO": "USA OR Canada OR Germany OR Poland",
        "BANGLADESH": "Vietnam OR Indonesia OR Ethiopia OR Portugal",
    }.get(country.upper(), "Germany OR USA OR Japan OR South Korea")
    queries.append(
        f'top "{category}" manufacturers suppliers ({alt_regions}) certified list {CURRENT_YEAR}'
    )

    return queries


def gather_web_intelligence(supplier_name: str, country: str, category: str,
                            risk_components: dict, ofac_status: str = "CLEAR",
                            score_trend: str = "STABLE") -> dict:
    """Targeted searches built from the actual risk profile."""
    queries = build_search_queries(
        supplier_name, country, category, risk_components, ofac_status, score_trend
    )
    top_driver  = max(risk_components, key=risk_components.get) if risk_components else "geography"

    # Fast path when Serper is not configured: preserve response shape and query list
    # while avoiding threadpool/no-op network call overhead.
    if not get_serper_key():
        return {
            "sources":            [],
            "alternatives":       [],
            "audit_standards":    [],
            "geopolitical":       [],
            "named_alternatives": [],
            "top_driver":         top_driver,
            "queries_used":       queries,
        }

    # Network-bound searches run concurrently to reduce end-to-end latency.
    with ThreadPoolExecutor(max_workers=min(4, len(queries) or 1)) as ex:
        results_per_query = list(ex.map(serper_search, queries))
    alts        = results_per_query[0]
    geo         = results_per_query[1] if len(results_per_query) > 1 else []
    audits      = results_per_query[2] if len(results_per_query) > 2 else []
    named_srcs  = results_per_query[3] if len(results_per_query) > 3 else []

    all_sources = [r for bucket in results_per_query for r in bucket]

    # Extract actual company names from the named-alternatives search results
    named_alternatives = extract_named_companies(named_srcs + alts, supplier_name)

    return {
        "sources":            all_sources,
        "alternatives":       alts,
        "audit_standards":    audits,
        "geopolitical":       geo,
        "named_alternatives": named_alternatives,
        "top_driver":         top_driver,
        "queries_used":       queries,
    }


# ── Prompt builder ────────────────────────────────────────────
def build_system_prompt() -> str:
    return (
        "You are a senior supply chain risk consultant with 20 years of experience in "
        "procurement risk, OFAC compliance, and supplier diversification.\n\n"
        "CRITICAL RULES FOR SPECIFICITY — every recommendation MUST follow these:\n"
        "1. NAME actual alternative suppliers from the provided list (e.g. 'qualify Siemens AG "
        "(Germany) or Kyocera (Japan) as alternatives') — never say 'find alternative suppliers'.\n"
        "2. NAME specific certifications from the provided list (e.g. 'obtain ISO 9001 and IATF 16949') "
        "— never say 'get audited' or 'obtain relevant certifications'.\n"
        "3. QUANTIFY where possible: use the annual spend to estimate safety stock cost, "
        "switching cost, or risk exposure in USD.\n"
        "4. NAME specific contract clauses (e.g. 'add a Force Majeure clause covering [country] "
        "political risk, a Dual-Source obligation clause, and a 30-day priority allocation guarantee').\n"
        "5. For geographic risk, NAME the specific alternative countries and explain why they are "
        "lower risk (e.g. 'Vietnam (score 0.35) or Malaysia (score 0.35) vs current China (score 0.55)').\n"
        "6. Each rationale must reference the ACTUAL risk scores/components provided — "
        "not generic supply chain theory.\n\n"
        "Return only valid JSON — no markdown, no preamble."
    )


def _safety_stock_cost(annual_spend: float, days: int) -> str:
    """Estimate working capital cost of N days safety stock from annual spend."""
    if not annual_spend or annual_spend <= 0:
        return ""
    cost = annual_spend * (days / 365)
    return f"~${cost:,.0f} in working capital (at ${annual_spend:,.0f}/yr spend)"


def build_user_prompt(req: dict, web: dict) -> str:
    comps    = req.get("risk_components", {})
    spend    = req.get("annual_spend_usd")
    spend_t  = f"${spend:,.0f}/yr" if spend is not None and spend > 0 else "not specified"
    on_time  = req.get("on_time_delivery_rate")
    on_time_t = f"{float(on_time):.0f}%" if on_time is not None else "not specified"
    years    = req.get("years_in_relationship")
    years_t  = f"{years} years" if years else "not specified"

    # Certifications for this category
    category = req.get("category", "")
    certs    = get_category_certifications(category)
    certs_t  = ", ".join(certs)

    # Named alternative suppliers found in web search
    named_alts = web.get("named_alternatives", [])
    named_alts_t = (
        "Named candidates from web search: " + ", ".join(named_alts)
        if named_alts else "None found — use your knowledge to name 2-3 real companies"
    )

    # Safety stock cost estimate
    stock_30  = _safety_stock_cost(spend, 30)
    stock_60  = _safety_stock_cost(spend, 60)
    stock_t   = f"30-day buffer ≈ {stock_30} | 60-day buffer ≈ {stock_60}" if stock_30 else "spend not provided"

    # Custom weight note
    cw = req.get("custom_weights") or {}
    weight_note = ""
    if cw:
        weight_note = (
            f"\nCustom risk weights applied: "
            f"OFAC={cw.get('ofac', 0.35):.0%}, "
            f"Geo={cw.get('geography', 0.25):.0%}, "
            f"News={cw.get('news', 0.20):.0%}, "
            f"Single-Source={cw.get('single_source', 0.10):.0%}, "
            f"Lead-Time={cw.get('lead_time', 0.10):.0%}"
        )

    # Key concerns & gaps from summarizer
    concerns_t = "\n".join(f"  - {c}" for c in req.get("key_concerns", [])) or "  - (see risk components)"
    gaps_t     = "\n".join(f"  - {g}" for g in req.get("gaps", [])) or "  - Standard due diligence gaps"

    # Web snippets
    snippets = ""
    for s in web["sources"][:9]:
        if s.get("snippet"):
            snippets += f"  [{s['title']}]({s['url']}): {s['snippet']}\n"
    snippets = snippets or "  (no web results retrieved)\n"

    # Score trend line
    trend      = req.get("score_trend", "STABLE")
    delta      = req.get("score_delta")
    delta_t    = f" (Δ {delta:+.3f})" if delta is not None else ""
    trend_line = f"  Score Trend:   {trend}{delta_t}\n" if trend != "STABLE" else ""

    return f"""
SUPPLIER RISK DATA:
  Supplier:      {req['supplier_name']} | Country: {req['country']} | Category: {req['category']}
  Risk Score:    {req['risk_score']:.3f} | Category: {req['risk_category']}
  OFAC Status:   {req['ofac_status']} | News Risk: {req['news_risk']}
{trend_line}  Components:    OFAC={comps.get('ofac',0):.2f} | Geo={comps.get('geography',0):.2f} | News={comps.get('news',0):.2f} | Single-Source={comps.get('single_source',0):.2f} | Lead-Time={comps.get('lead_time',0):.2f}{weight_note}

BUYER COMPANY:
  Name:           {req.get('company_name', 'Your Company')} | Industry: {req.get('company_industry', 'N/A')}
  Annual Spend:   {spend_t}
  Safety Stock Cost: {stock_t}
  Sole Source:    {req.get('sole_source', False)} | Tier Level: {req.get('tier_level') or 'N/A'}
  On-Time Delivery: {on_time_t} | Financial Health: {req.get('financial_health') or 'N/A'}
  Relationship:   {years_t} | Contract Expiry: {req.get('contract_expiry') or 'N/A'}

INDUSTRY CERTIFICATIONS FOR THIS CATEGORY ({category}):
  {certs_t}
  → Use these exact certification names in your recommendations. Do NOT say "relevant certifications".

NAMED ALTERNATIVE SUPPLIERS (from live web search):
  {named_alts_t}
  → Name at least 2 of these (or known real companies) in your alternative supplier recommendations.

RISK SUMMARY (from SummarizerAgent):
  {req.get('summary', '').replace(chr(10), ' ')[:600]}

KEY CONCERNS:
{concerns_t}

INFORMATION GAPS:
{gaps_t}

WEB INTELLIGENCE (snippets — cite URLs in source fields):
{snippets}

TASK:
Generate exactly 3 IMMEDIATE actions (within 30 days) and 3 LONG-TERM actions (3-18 months).

Specificity requirements:
- Name actual alternative supplier companies (not "find alternatives")
- Name actual certifications from the list above (not "get certified")
- Reference actual risk scores in rationales (e.g. "geography score 0.72 indicates...")
- Include safety stock cost estimate in any buffer stock recommendation
- Name specific contract clause types (Force Majeure, Dual-Source obligation, etc.)

Return ONLY valid JSON (no markdown, no preamble):
{{
  "immediate_actions": [
    {{
      "action": "concise action title (max 12 words)",
      "rationale": "specific reasoning referencing actual scores, company names, or cost figures (2-3 sentences)",
      "priority": "HIGH or MEDIUM",
      "source": "URL from web intelligence or 'Internal Analysis'"
    }}
  ],
  "long_term_actions": [
    {{
      "action": "concise action title (max 12 words)",
      "rationale": "root-cause reasoning with specific certifications, supplier names, or contract terms (2-3 sentences)",
      "timeline": "e.g. 3-6 months",
      "source": "URL from web intelligence or 'Internal Analysis'"
    }}
  ],
  "top_recommendations_for_summary": "1-2 sentence executive statement naming the single highest-priority action, the specific risk score driving it, and the expected outcome"
}}
""".strip()


# ── Rule-based fallback ───────────────────────────────────────
def rule_based_recommendations(req: dict, web: dict) -> dict:
    comps        = req.get("risk_components", {})
    # Identify compound risk drivers (all above medium threshold, sorted descending)
    high_drivers = sorted(
        [(k, v) for k, v in comps.items() if v >= MEDIUM_THRESHOLD],
        key=lambda x: -x[1],
    )
    top          = high_drivers[0][0] if high_drivers else (max(comps, key=comps.get) if comps else "geography")
    ofac         = req.get("ofac_status", "CLEAR")
    country      = req.get("country", "N/A")
    category     = req.get("category", "N/A")
    name         = req.get("supplier_name", "Supplier")
    score        = req.get("risk_score", 0.5)
    risk_cat     = req.get("risk_category", "MEDIUM")
    spend        = req.get("annual_spend_usd")
    spend_t      = f"${spend:,.0f}/yr exposure" if spend else "significant exposure"

    alt_url   = next((s["url"] for s in web.get("alternatives", []) if s.get("url")), "Internal Analysis")
    audit_url = next((s["url"] for s in web.get("audit_standards", []) if s.get("url")), "Internal Analysis")

    if ofac == "SANCTIONED":
        immediate = [
            {"action": "Freeze all purchase orders and payments immediately",
             "rationale": f"{name} is on the OFAC SDN list. Any transaction risks penalties up to $1M per violation under OFAC enforcement guidelines. Cease all financial activity at once.",
             "priority": "HIGH", "source": "Internal Analysis"},
            {"action": "Engage legal counsel within 24 hours for compliance review",
             "rationale": "Sanctions violations carry criminal liability. An OFAC counsel must assess current exposure, determine voluntary disclosure obligations, and guide the remediation process.",
             "priority": "HIGH", "source": "Internal Analysis"},
            {"action": f"Identify emergency backup {category} suppliers within 7 days",
             "rationale": f"With {spend_t}, production continuity is at risk. An emergency sourcing exercise must begin immediately to avoid supply interruption.",
             "priority": "HIGH", "source": alt_url},
        ]
        long_term = [
            {"action": "Integrate OFAC pre-screening into PO approval workflow",
             "rationale": "Automated SDN checks at the purchase order stage prevent future sanctions exposure before any financial commitment is made.",
             "timeline": "1-2 months", "source": "Internal Analysis"},
            {"action": f"Diversify {category} supply base to 3+ vetted regions",
             "rationale": f"Geographic over-reliance on {country} contributed to this sanctioned single-point-of-failure. Multi-region sourcing eliminates this class of risk.",
             "timeline": "6-12 months", "source": alt_url},
            {"action": "Deploy quarterly sanctions compliance training for procurement",
             "rationale": "Regular training reduces recurrence risk and demonstrates good-faith compliance effort, which is considered favourably in any OFAC enforcement proceedings.",
             "timeline": "3-6 months", "source": "Internal Analysis"},
        ]
        top_rec = f"Immediately freeze all activity with {name} due to OFAC sanctions match and engage legal counsel within 24 hours to assess exposure and voluntary disclosure obligations."

    elif len(high_drivers) >= 2:
        # Compound risk: multiple factors elevated — address the top two explicitly
        d1_key, d1_val = high_drivers[0]
        d2_key, d2_val = high_drivers[1]
        driver_labels = {
            "geography": "geographic concentration", "news": "adverse news",
            "single_source": "single-source dependency", "lead_time": "extended lead time",
            "financial_health": "financial health", "on_time_delivery": "on-time delivery",
            "contract_expiry": "contract expiry risk",
        }
        d1_label = driver_labels.get(d1_key, d1_key)
        d2_label = driver_labels.get(d2_key, d2_key)
        immediate = [
            {"action": f"Commission combined risk audit addressing {d1_label} and {d2_label}",
             "rationale": f"{name} shows elevated scores on both {d1_label} ({d1_val:.2f}/1.0) and {d2_label} ({d2_val:.2f}/1.0). A combined audit prevents siloed remediation that misses interaction effects between the two drivers.",
             "priority": "HIGH", "source": audit_url},
            {"action": f"Increase safety stock to 60 days and lock priority allocation clause",
             "rationale": f"Compound risk from {d1_label} and {d2_label} means multiple disruption scenarios are plausible simultaneously. Buffer stock and allocation clauses provide near-term protection while structural fixes are implemented.",
             "priority": "HIGH", "source": "Internal Analysis"},
            {"action": f"Begin qualification of 2 alternative {category} suppliers in lower-risk regions",
             "rationale": f"Single-supplier reliance combined with elevated {d1_label} creates an outsized vulnerability. Qualification of alternatives in parallel reduces time-to-switch from months to weeks.",
             "priority": "HIGH", "source": alt_url},
        ]
        long_term = [
            {"action": f"Implement split-sourcing (70/30) to reduce dependency on {name}",
             "rationale": f"Distributing volume across two qualified suppliers directly reduces both the {d1_label} and {d2_label} risk contributions to the composite score.",
             "timeline": "6-12 months", "source": alt_url},
            {"action": f"Negotiate contractual protections for each elevated risk driver",
             "rationale": f"Risk-specific contract clauses (e.g., exit rights on adverse news, priority allocation on lead-time breach) protect the buyer when the risk profile worsens.",
             "timeline": "3-6 months", "source": "Internal Analysis"},
            {"action": "Deploy real-time monitoring dashboard for all elevated risk factors",
             "rationale": "Compound risk profiles require continuous monitoring — a single factor deteriorating can cascade. Automated alerts trigger action before a risk event becomes a supply crisis.",
             "timeline": "1-3 months", "source": "Internal Analysis"},
        ]
        top_rec = f"Address the compound risk of {d1_label} ({d1_val:.2f}) and {d2_label} ({d2_val:.2f}) simultaneously through a combined audit and parallel alternative supplier qualification — single-factor remediation alone will not materially reduce the composite score."

    elif top == "geography":
        immediate = [
            {"action": f"Commission geopolitical risk assessment for {country}",
             "rationale": f"Geographic risk score is {comps.get('geography',0):.2f}/1.0 — the primary driver of the {risk_cat} rating. An independent assessment quantifies current and forward-looking exposure.",
             "priority": "HIGH", "source": "Internal Analysis"},
            {"action": "Increase inventory buffer to 60-90 days for this category",
             "rationale": f"With supply originating from {country}, safety stock is the fastest protection against a regional disruption event while structural alternatives are qualified.",
             "priority": "HIGH", "source": "Internal Analysis"},
            {"action": "Request supplier business continuity and financial health documentation",
             "rationale": "Elevated geographic risk requires independent verification that the supplier can sustain operations through regional instability.",
             "priority": "MEDIUM", "source": audit_url},
        ]
        long_term = [
            {"action": f"Qualify 2 alternative {category} suppliers outside {country}",
             "rationale": "Geographic diversification is the structural solution. Dual-region sourcing reduces the geographic component score and eliminates single-country dependency.",
             "timeline": "6-9 months", "source": alt_url},
            {"action": "Negotiate dual-sourcing clauses into the primary supplier contract",
             "rationale": "Contractual flexibility to redistribute volume gives the procurement team leverage to shift supply without termination penalties during a crisis.",
             "timeline": "3-6 months", "source": "Internal Analysis"},
            {"action": "Establish nearshore/friendshore supplier relationships proactively",
             "rationale": "Building qualified relationships in allied-country suppliers before they are urgently needed avoids premium emergency sourcing costs.",
             "timeline": "9-18 months", "source": alt_url},
        ]
        top_rec = f"Build a 60-90 day inventory buffer for {name}'s supply immediately while qualifying at least two alternative {category} suppliers outside {country} to structurally reduce the geographic risk score."

    elif top == "single_source":
        immediate = [
            {"action": "Document full single-source dependency and business impact",
             "rationale": f"A formal impact analysis quantifies the financial and operational consequence of a supply disruption from {name}, enabling proportionate mitigation investment.",
             "priority": "HIGH", "source": "Internal Analysis"},
            {"action": "Initiate emergency qualification of a backup supplier",
             "rationale": f"Single-source exposure with {spend_t} creates a critical vulnerability. A parallel qualification process should start within two weeks.",
             "priority": "HIGH", "source": alt_url},
            {"action": "Negotiate supply guarantee and priority allocation clause",
             "rationale": "A contractual priority allocation clause protects supply access while the backup qualification is underway.",
             "priority": "MEDIUM", "source": "Internal Analysis"},
        ]
        long_term = [
            {"action": f"Qualify minimum 2 additional {category} suppliers",
             "rationale": "Eliminating single-source dependency is the definitive fix. The target should be a 70/30 primary/secondary split within the fiscal year.",
             "timeline": "6-12 months", "source": alt_url},
            {"action": "Implement 70/30 split-sourcing strategy",
             "rationale": "A split-sourcing contract maintains the primary supplier relationship while building secondary-source capacity that can scale rapidly if needed.",
             "timeline": "9-12 months", "source": "Internal Analysis"},
            {"action": "Review product specifications for supplier-agnostic design",
             "rationale": "Proprietary specifications lock in single suppliers. Supplier-agnostic specifications reduce switching costs and expand the qualified supplier pool.",
             "timeline": "12-18 months", "source": "Internal Analysis"},
        ]
        top_rec = f"Begin an emergency backup supplier qualification for {name}'s {category} category within two weeks, while negotiating a supply guarantee clause to protect continuity during the qualification period."

    elif top == "news":
        immediate = [
            {"action": f"Conduct enhanced due diligence on {name} news risk drivers",
             "rationale": f"News risk score {comps.get('news',0):.2f}/1.0 indicates active adverse media. Understanding the specific allegations is prerequisite to any mitigation decision.",
             "priority": "HIGH", "source": "Internal Analysis"},
            {"action": "Escalate to procurement management for enhanced approval process",
             "rationale": "Active adverse media warrants additional management oversight of any ongoing or new purchase orders until the news risk is understood and resolved.",
             "priority": "HIGH", "source": "Internal Analysis"},
            {"action": "Request a formal response from the supplier regarding adverse media",
             "rationale": "A supplier's response to adverse media disclosures provides evidence for compliance records and clarifies whether the risk is factual or reputational noise.",
             "priority": "MEDIUM", "source": audit_url},
        ]
        long_term = [
            {"action": "Implement continuous media monitoring for this supplier",
             "rationale": "Real-time adverse media alerts allow the procurement team to respond to developing stories before they escalate to regulatory action.",
             "timeline": "1-3 months", "source": "Internal Analysis"},
            {"action": f"Develop contingency sourcing plan for {category} category",
             "rationale": "Pre-qualified alternatives reduce response time from weeks to days if news risk escalates to regulatory enforcement or reputational liability.",
             "timeline": "3-6 months", "source": alt_url},
            {"action": "Add reputational risk clauses to contract renewal",
             "rationale": "Contractual exit rights triggered by material adverse news events protect the buyer from reputational contagion without requiring termination-for-convenience penalties.",
             "timeline": "3-6 months", "source": "Internal Analysis"},
        ]
        top_rec = f"Conduct an immediate enhanced due diligence review of the adverse media driving {name}'s news risk score and escalate ongoing purchase orders to management approval while the investigation is underway."

    else:  # lead_time or other
        immediate = [
            {"action": f"Conduct full risk audit on {name}",
             "rationale": f"Overall risk score {score:.3f} in {risk_cat} tier requires a structured audit to verify and prioritise each risk driver before the next procurement cycle.",
             "priority": "HIGH", "source": audit_url},
            {"action": "Increase safety stock by 30-45 days for long-lead components",
             "rationale": f"Extended lead times increase vulnerability to supply shocks. Buffer inventory is the fastest protection while structural lead-time improvements are negotiated.",
             "priority": "MEDIUM", "source": "Internal Analysis"},
            {"action": "Upgrade screening frequency to monthly",
             "rationale": "Monthly risk rescreening catches deterioration in OFAC status, news sentiment, or geopolitical conditions before they impact procurement decisions.",
             "priority": "MEDIUM", "source": "Internal Analysis"},
        ]
        long_term = [
            {"action": f"Develop contingency sourcing for {category} category",
             "rationale": "Pre-qualified alternative suppliers reduce emergency sourcing lead-time from months to weeks if this supplier's risk profile deteriorates further.",
             "timeline": "3-6 months", "source": alt_url},
            {"action": "Negotiate lead-time reduction commitment in next contract",
             "rationale": f"Lead-time score {comps.get('lead_time',0):.2f}/1.0 indicates structural improvement is possible through contractual volume commitments that justify supplier capacity investment.",
             "timeline": "6-12 months", "source": "Internal Analysis"},
            {"action": "Implement supplier performance improvement programme with KPIs",
             "rationale": "Structured performance targets with contractual consequences drive measurable risk score reduction over successive assessment periods.",
             "timeline": "6-12 months", "source": "Internal Analysis"},
        ]
        top_rec = f"Run a structured risk audit on {name} immediately and increase safety stock by 30-45 days to protect against lead-time risk while negotiating performance improvements in the next contract cycle."

    return {
        "immediate_actions":           immediate,
        "long_term_actions":           long_term,
        "top_recommendations_for_summary": top_rec,
        "web_sources":                 web.get("sources", []),
        "model":                       "rule-based-fallback",
        "success":                     True,
    }


# ── Request model ─────────────────────────────────────────────
class RecommendRequest(BaseModel):
    supplier_name:         str
    country:               str   = "N/A"
    category:              str   = "N/A"
    risk_score:            float = 0.5
    risk_category:         str   = "MEDIUM"
    risk_components:       dict  = {}
    ofac_status:           str   = "CLEAR"
    news_risk:             str   = "NONE"
    news_headlines:        list  = []
    summary:               str   = ""
    key_concerns:          list  = []
    gaps:                  list  = []
    company_name:          str   = "N/A"
    company_industry:      str   = "N/A"
    custom_weights:        dict  = {}
    annual_spend_usd:      Optional[float] = None
    sole_source:           bool  = False
    tier_level:            Optional[str]   = None
    on_time_delivery_rate: Optional[float] = None
    years_in_relationship: Optional[int]   = None
    financial_health:      Optional[str]   = None
    contract_expiry:       Optional[str]   = None
    # Score trend (from orchestrator DB comparison)
    score_trend:           str             = "STABLE"   # IMPROVING / STABLE / DETERIORATING
    score_delta:           Optional[float] = None       # current - previous score


# ── Endpoints ─────────────────────────────────────────────────
@app.get("/health")
def health():
    return {
        "agent":               "RecommenderAgent",
        "status":              "healthy",
        "model":               GROQ_MODEL,
        "groq_key_configured": bool(get_groq_key()),
        "serper_configured":   bool(get_serper_key()),
    }


@app.post("/recommend")
def recommend(req: RecommendRequest):
    start    = time.perf_counter()
    req_data = req.model_dump()

    # Step 1: Gather web intelligence (always, regardless of LLM availability)
    web = gather_web_intelligence(
        req.supplier_name, req.country, req.category, req.risk_components,
        ofac_status=req.ofac_status, score_trend=req.score_trend,
    )

    groq_key = get_groq_key()
    if not groq_key:
        result = rule_based_recommendations(req_data, web)
        result["elapsed_ms"] = round((time.perf_counter() - start) * 1000, 2)
        return result

    # Step 2: Call Llama 3.3 70B via Groq
    try:
        resp = HTTP.post(
            GROQ_API_URL,
            headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
            json={
                "model": GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": build_system_prompt()},
                    {"role": "user",   "content": build_user_prompt(req_data, web)},
                ],
                "max_tokens":  1400,
                "temperature": 0.4,
                "top_p":       0.9,
            },
            timeout=60,
        )

        if resp.status_code in (429, 503):
            result = rule_based_recommendations(req_data, web)
            result["model"]      = GROQ_MODEL
            result["error"]      = f"Groq {resp.status_code} — fallback used"
            result["elapsed_ms"] = round((time.perf_counter() - start) * 1000, 2)
            return result

        resp.raise_for_status()
        llm_out = resp.json()

        # Extract text from chat-completions response
        text = llm_out["choices"][0]["message"]["content"].strip()

        # Strip markdown code blocks if present
        if text.startswith("```"):
            text = text.split("```", 2)[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.rsplit("```", 1)[0]

        # Extract JSON
        j_start = text.find("{")
        j_end   = text.rfind("}") + 1
        if j_start < 0 or j_end <= j_start:
            raise ValueError("No JSON object found in LLM response")

        parsed   = json.loads(text[j_start:j_end])
        immediate = parsed.get("immediate_actions", [])
        long_term = parsed.get("long_term_actions", [])

        # Ensure at least 3 of each — pad with fallback if LLM returned fewer
        if len(immediate) < 3 or len(long_term) < 3:
            fb = rule_based_recommendations(req_data, web)
            if len(immediate) < 3:
                immediate = fb["immediate_actions"]
            if len(long_term) < 3:
                long_term = fb["long_term_actions"]

        return {
            "immediate_actions":               immediate[:5],
            "long_term_actions":               long_term[:5],
            "top_recommendations_for_summary": parsed.get("top_recommendations_for_summary", ""),
            "web_sources":                     web["sources"],
            "model":                           GROQ_MODEL,
            "success":                         True,
            "elapsed_ms":                      round((time.perf_counter() - start) * 1000, 2),
        }

    except Exception as e:
        logger.warning(f"Groq call failed: {e} — using rule-based fallback")
        result = rule_based_recommendations(req_data, web)
        result["model"]      = GROQ_MODEL
        result["success"]    = False
        result["error"]      = str(e)
        result["elapsed_ms"] = round((time.perf_counter() - start) * 1000, 2)
        return result
