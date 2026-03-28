"""
SupplyShield — Central Configuration
Single source of truth for all risk thresholds, weights, and tunable parameters.

Import in services (2 levels deep):
    import sys; from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from config import HIGH_THRESHOLD, DEFAULT_WEIGHTS

Import in orchestrator (1 level deep):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from config import ...

Import in app.py / utils/:
    from config import ...   # project root already on sys.path
"""
from datetime import datetime

# ── Risk Classification Thresholds ────────────────────────────
HIGH_THRESHOLD   = 0.75   # score >= this → HIGH / REQUIRES_APPROVAL
MEDIUM_THRESHOLD = 0.45   # score >= this → MEDIUM; below → LOW

# Gate uses the same value — explicit alias avoids magic numbers there
GATE_APPROVAL_THRESHOLD = HIGH_THRESHOLD

# ── Default weights — standard 4-factor model ─────────────────
# OFAC is handled via a hard compliance override (score >= 0.90)
# rather than a weight, so it does not appear here.
DEFAULT_WEIGHTS = {
    "geography":     0.38,
    "news":          0.31,
    "single_source": 0.16,
    "lead_time":     0.15,
}

# ── Onboarded-supplier weights — 7-factor model ───────────────
# Applied when the supplier record contains financial_health,
# on_time_delivery_rate, or contract_days_remaining.
# OFAC is handled via a hard compliance override, not a weight.
ONBOARDED_WEIGHTS = {
    "geography":        0.28,
    "news":             0.22,
    "single_source":    0.11,
    "lead_time":        0.11,
    "financial_health": 0.11,
    "on_time_delivery": 0.10,
    "contract_expiry":  0.07,
}

# ── Expanded weights — 13-factor model ────────────────────────
# Applied when any of the 6 new performance/governance metrics are provided.
# Incorporates: fill rate (OTIF), lead-time variability, audit pass rate,
# supplier improvement index, cyber posture, and disruption frequency.
# Weights sum to 1.00.
EXPANDED_WEIGHTS = {
    "geography":             0.14,
    "news":                  0.12,
    "single_source":         0.07,
    "lead_time":             0.06,
    "financial_health":      0.09,
    "on_time_delivery":      0.07,
    "contract_expiry":       0.04,
    # New metrics (6)
    "order_fill_rate":       0.08,   # OTIF — in-full delivery performance
    "lead_time_variability": 0.06,   # consistency of delivery timing
    "audit_pass_rate":       0.09,   # compliance & governance track record
    "improvement_index":     0.05,   # corrective action closure rate
    "cyber_posture":         0.07,   # cybersecurity risk exposure
    "disruption_frequency":  0.06,   # historical supply chain incidents/yr
}

# ── Score maps for new metrics ─────────────────────────────────
CYBER_POSTURE_MAP = {"Poor": 0.85, "Fair": 0.40, "Good": 0.05}

LEAD_TIME_VARIABILITY_MAP = {"Low": 0.0, "Medium": 0.40, "High": 0.80}

# ── OFAC Screening ────────────────────────────────────────────
OFAC_SIMILARITY_THRESHOLD = 85    # % minimum fuzzy-match score (RapidFuzz token_set_ratio)
OFAC_MAX_MATCHES           = 10   # maximum SDN matches returned per supplier

# ── News Risk Thresholds ──────────────────────────────────────
NEWS_HIGH_MIN_HEADLINES    = 3    # >= N adverse headlines → HIGH news risk
NEWS_MEDIUM_MIN_HEADLINES  = 1    # >= N adverse headlines → MEDIUM news risk

# Terms used to search for adverse news — ordered by severity
ADVERSE_NEWS_TERMS = [
    "sanctions", "fraud", "corruption", "blacklist",
    "money laundering", "regulatory action", "law enforcement",
    "investigation", "embargo", "penalty", "violation",
    "supply chain disruption", "bankruptcy",
]

# ── Operational Defaults ──────────────────────────────────────
DEFAULT_LEAD_TIME_WEEKS    = 12
RECORDS_SEARCHED_FALLBACK  = 18708   # displayed when geointel SDN count unavailable

# ── Score Trend Thresholds ────────────────────────────────────
TREND_DETERIORATING_DELTA  =  0.05   # score rose by ≥ this → DETERIORATING
TREND_IMPROVING_DELTA      = -0.05   # score fell by ≥ this → IMPROVING

# ── Current year (for dynamic search queries) ─────────────────
CURRENT_YEAR = datetime.now().year

# ── Category → Industry Certifications / Standards ────────────
# Injected into recommender prompts to replace generic "get audited" advice
# with specific certification names relevant to the supplier's category.
CATEGORY_CERTIFICATIONS = {
    # Manufacturing / Industrial
    "electronics":          ["ISO 9001", "IPC-A-610", "IATF 16949 (if automotive)", "RoHS/REACH compliance"],
    "semiconductor":        ["ISO 9001", "IATF 16949", "AEC-Q100/Q101", "ISO 26262 (automotive)"],
    "automotive":           ["IATF 16949", "ISO 26262", "APQP/PPAP", "VDA 6.3 process audit"],
    "aerospace":            ["AS9100D", "NADCAP", "FAA/EASA approval", "ISO 9001"],
    "medical devices":      ["ISO 13485", "FDA 21 CFR Part 820", "CE marking", "MDR 2017/745"],
    "pharmaceuticals":      ["GMP (21 CFR Parts 210/211)", "ISO 15378", "ICH Q10", "FDA registration"],
    "food":                 ["FSSC 22000", "BRC Global Standard", "SQF Level 2/3", "HACCP certification"],
    "chemicals":            ["ISO 14001", "REACH registration", "Responsible Care", "ISO 45001"],
    "textiles":             ["OEKO-TEX Standard 100", "GOTS", "SA8000 (labour)", "WRAP certification"],
    "packaging":            ["ISO 9001", "FSC chain of custody", "BRC/IOP", "ISO 22000"],
    "construction":         ["ISO 9001", "CE marking (products)", "ISO 14001", "OHSAS 18001/ISO 45001"],
    "metals":               ["ISO 9001", "EN 10204 material certs", "NADCAP (special processes)", "RoHS"],
    "plastics":             ["ISO 9001", "IATF 16949 (automotive)", "RoHS/REACH", "UL certification"],
    # Logistics / Services
    "logistics":            ["ISO 28001", "CTPAT (US)", "AEO (EU)", "ISO 9001", "TAPA FSR/TSR"],
    "warehousing":          ["ISO 9001", "CTPAT", "GDP (pharma)", "ISO 28001"],
    "it services":          ["ISO 27001", "SOC 2 Type II", "ISO 20000", "CMMC (US defence)"],
    "software":             ["ISO 27001", "SOC 2 Type II", "ISO 9001", "CMMI Level 3+"],
    # Commodities / Raw materials
    "raw materials":        ["ISO 9001", "conflict minerals (3TG/Dodd-Frank)", "ISO 14001", "RoHS"],
    "commodities":          ["ISO 9001", "sustainability certifications (Rainforest Alliance, etc.)", "ISO 14001"],
    # Fallback for unlisted categories
    "default":              ["ISO 9001 (quality)", "ISO 14001 (environmental)", "SA8000 (labour standards)", "ISO 28001 (supply chain security)"],
}

# ── Country Risk Scores ───────────────────────────────────────
# 0.0 = no risk · 1.0 = maximum risk
# Countries not in this dict fall back to the geo_concentration
# slider value supplied by the user (default 0.5).
COUNTRY_RISK = {
    # ── Sanctioned / conflict / extreme risk ──────────────────
    "IRAN":                   1.00,
    "NORTH KOREA":            1.00,
    "RUSSIA":                 0.95,
    "SYRIA":                  0.95,
    "BELARUS":                0.90,
    "AFGHANISTAN":            0.90,
    "SOMALIA":                0.90,
    "SUDAN":                  0.85,
    "LIBYA":                  0.85,
    "IRAQ":                   0.80,
    "MYANMAR":                0.80,
    "VENEZUELA":              0.80,
    "LEBANON":                0.80,
    "UKRAINE":                0.75,   # active conflict zone
    "CUBA":                   0.75,
    "HAITI":                  0.75,
    "ZIMBABWE":               0.70,
    # ── High risk ─────────────────────────────────────────────
    "PAKISTAN":               0.60,
    "NIGERIA":                0.60,
    "CHINA":                  0.55,
    "ETHIOPIA":               0.55,
    "KAZAKHSTAN":             0.55,
    "UZBEKISTAN":             0.55,
    "SRI LANKA":              0.50,
    "BANGLADESH":             0.50,
    "ALGERIA":                0.50,
    "LAOS":                   0.50,
    "ECUADOR":                0.50,
    "KENYA":                  0.50,
    # ── Medium-high risk ──────────────────────────────────────
    "PHILIPPINES":            0.40,
    "TURKEY":                 0.40,
    "MEXICO":                 0.40,
    "CAMBODIA":               0.45,
    "EGYPT":                  0.45,
    "ARGENTINA":              0.45,
    "MONGOLIA":               0.45,
    "AZERBAIJAN":             0.45,
    "SOUTH AFRICA":           0.40,
    "COLOMBIA":               0.40,
    "PERU":                   0.40,
    "GHANA":                  0.45,
    "TUNISIA":                0.40,
    "GEORGIA":                0.40,
    "PANAMA":                 0.30,
    # ── Medium risk ───────────────────────────────────────────
    "INDIA":                  0.30,
    "BRAZIL":                 0.35,
    "INDONESIA":              0.35,
    "VIETNAM":                0.35,
    "THAILAND":               0.35,
    "MALAYSIA":               0.35,
    "MOROCCO":                0.35,
    "JORDAN":                 0.35,
    "SAUDI ARABIA":           0.30,
    "UAE":                    0.25,
    "UNITED ARAB EMIRATES":   0.25,
    "QATAR":                  0.20,
    "OMAN":                   0.25,
    "KUWAIT":                 0.20,
    "ISRAEL":                 0.20,
    "TAIWAN":                 0.15,
    "SOUTH KOREA":            0.10,
    "SINGAPORE":              0.10,
    "CHILE":                  0.20,
    "URUGUAY":                0.20,
    "ROMANIA":                0.20,
    "GREECE":                 0.20,
    "SERBIA":                 0.30,
    "HUNGARY":                0.15,
    "ITALY":                  0.15,
    "SPAIN":                  0.10,
    "PORTUGAL":               0.10,
    "CZECH REPUBLIC":         0.10,
    "CZECHIA":                0.10,
    "POLAND":                 0.10,
    # ── Low risk ──────────────────────────────────────────────
    "USA":                    0.05,
    "UNITED STATES":          0.05,
    "CANADA":                 0.05,
    "UK":                     0.05,
    "UNITED KINGDOM":         0.05,
    "GERMANY":                0.05,
    "FRANCE":                 0.05,
    "JAPAN":                  0.05,
    "AUSTRALIA":              0.05,
    "NEW ZEALAND":            0.05,
    "NETHERLANDS":            0.05,
    "SWITZERLAND":            0.05,
    "SWEDEN":                 0.05,
    "DENMARK":                0.05,
    "NORWAY":                 0.05,
    "FINLAND":                0.05,
    "IRELAND":                0.05,
    "BELGIUM":                0.05,
    "AUSTRIA":                0.05,
    "LUXEMBOURG":             0.05,
}
