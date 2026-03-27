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
