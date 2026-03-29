# SupplyShield

> **Real-Time Geopolitical Supply Chain Risk Intelligence**
> A Level 3 Collaborative Multi-Agent System that delivers a complete supplier risk verdict in under 10 seconds.

[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.135-green?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3-61DAFB?logo=react)](https://react.dev)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)](https://docs.docker.com/compose/)
[![LLM](https://img.shields.io/badge/LLM-Groq%20Llama%203.3%2070B-orange)](https://groq.com)
[![License](https://img.shields.io/badge/License-MIT-lightgrey)](LICENSE)

---

## The Problem

85% of Fortune 500 companies have zero real-time visibility into Tier-2 and Tier-3 supplier risk. They rely on quarterly audits and manual news monitoring — tools built for a pre-globalization world.

| Failure Mode | Real Cost |
|---|---|
| Stale compliance data | One missed OFAC update → $1–3M fine |
| No structured risk math | Single LLMs hallucinate sanctions status and tariff rates |
| No procurement gate | Auto-suspending a sole-source supplier can halt $1B+ in production within 24 hours |

SupplyShield turns supply chain risk from a quarterly, reactive process into **real-time, autonomous, and auditable intelligence**.

---

## Architecture

SupplyShield is a microservice platform composed of **7 independently deployable services**:

```
┌──────────────────────────────────────────────────────────────┐
│  Frontend — React 18 + Vite + Tailwind (nginx, Port 80)      │
│  Neumorphic UI · Recharts · Zustand · React Router           │
└────────────────────────┬─────────────────────────────────────┘
                         │  /api  (nginx proxy)
┌────────────────────────▼─────────────────────────────────────┐
│  BFF — FastAPI  (Port 8006)                                  │
│  JWT + TOTP 2FA · Supplier CRUD · PDF · Excel upload         │
└────────────────────────┬─────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────┐
│  Orchestrator — FastAPI  (Port 8000)                         │
│  Agent coordination · Trend detection · Audit persistence    │
└──────┬──────────┬──────────┬──────────┬───────────┬──────────┘
       │          │          │          │           │
       ▼          ▼          ▼          ▼           ▼
  GeoIntel   RiskCalc    Gate      Summarizer  Recommender
  (8001)     (8002)      (8003)    (8004)      (8005)
  OFAC SDN   13-factor   Procure-  Groq exec   Web search
  News API   det. score  ment gate brief       + Groq recs
  50% Rule
```

**Data persistence:** SQLite database and SDN CSV shared via a named Docker volume across BFF and Orchestrator.

---

## Key Features

### Real-Time OFAC Compliance
- Fuzzy-matches every supplier against the **OFAC Specially Designated Nationals (SDN) list** using RapidFuzz `token_set_ratio` (≥85% similarity threshold)
- SDN list **auto-downloads from the US Treasury** on startup and refreshes every 7 days; force-refresh via `POST /refresh-sdn`
- Implements the **OFAC 50% Rule**: uses live web search + Groq LLM to extract corporate ownership structure — if OFAC-linked parties cumulatively own ≥50%, the supplier is automatically `BLOCKED`
- Compliance override is absolute: sanctioned suppliers always score ≥ 0.90 regardless of all other factors

### Adaptive 13-Factor Risk Scoring
The RiskCalc agent automatically selects the correct model based on available data:

| Model | Factors | Triggered When |
|---|---|---|
| **Standard** (4-factor) | Geography, News, Single-source, Lead time | Unknown / untracked supplier |
| **Onboarded** (7-factor) | + Financial health, On-time delivery, Contract expiry | Supplier record has extended fields |
| **Expanded** (13-factor) | + Fill rate, Lead-time variability, Audit pass rate, Improvement index, Cyber posture, Disruption frequency | Supplier has full performance KPIs |

All scoring is **deterministic** — no LLM involved in the math. Custom weight overrides are supported and automatically renormalized.

### AI-Powered Intelligence (Three Purposeful Uses)

| Agent | What AI Does | Why Not a Simpler Tool |
|---|---|---|
| **GeoIntel** | Extracts `{shareholder, ownership_%}` pairs from unstructured web snippets to enforce the OFAC 50% Rule | No structured API provides corporate ownership data; requires natural language understanding |
| **Summarizer** | Generates a 200-word tone-calibrated executive brief (urgent for SANCTIONED, measured for MEDIUM) | Template systems can't adapt language to context; boards need communication artifacts, not JSON |
| **Recommender** | Runs 4 parallel web searches → extracts named alternative suppliers → generates industry-specific certifications + USD-quantified safety stock recommendations | Generic advice ("diversify suppliers") is worthless; only LLM can synthesize live search context into specific, actionable guidance |

Every LLM-dependent service has a **rule-based fallback** — the platform produces output even with no API keys configured.

### Procurement Gate
Every analysis produces a hard three-tier decision with full audit trail:

| Decision | Condition |
|---|---|
| `BLOCKED` | OFAC match **or** OFAC 50% Rule triggered |
| `REQUIRES_APPROVAL` | Risk score ≥ **0.65** |
| `AUTO_APPROVED` | Risk score < 0.65 |

### Additional Capabilities
- **Portfolio Dashboard** — aggregate KPIs, gate breakdown, country risk, category risk across all screened suppliers
- **Batch Screening** — screen every supplier in the database in one operation
- **Score Trend Detection** — `DETERIORATING` / `STABLE` / `IMPROVING` across successive screenings (delta threshold: ±0.05)
- **Excel Bulk Upload** — smart column detection across 22-field schema; no reformatting required
- **Supplier Self-Service Portal** — suppliers receive risk notifications, upload compliance documents, and track remediation actions
- **PDF Export** — branded risk report: components, OFAC matches, news, AI summary, gate decision
- **Full Audit Log** — every screening timestamped with score, decision, and components

---

## Project Structure

```
supplyshield_final/
├── config.py                   # Central config — all thresholds, weights, maps
├── docker-compose.yml          # 7-service orchestration
├── requirements.txt            # Root Python dependencies
├── .env.example                # Environment variable template
│
├── bff/                        # Backend-for-Frontend (Port 8006)
│   ├── main.py                 # Auth, CRUD, PDF, Excel, orchestrator proxy
│   ├── Dockerfile
│   └── requirements.txt
│
├── orchestrator/               # Agent coordinator (Port 8000)
│   ├── main.py                 # Pipeline orchestration, DB, trend detection
│   └── Dockerfile
│
├── services/
│   ├── geointel/               # GeoIntel Agent (Port 8001)
│   │   ├── main.py             # OFAC screening, news, 50% rule
│   │   └── Dockerfile
│   ├── riskcalc/               # Risk Calculator (Port 8002)
│   │   ├── main.py             # 13-factor deterministic scoring
│   │   └── Dockerfile
│   ├── gate/                   # Procurement Gate (Port 8003)
│   │   ├── main.py             # Decision logic
│   │   └── Dockerfile
│   ├── summarizer/             # Summarizer Agent (Port 8004)
│   │   ├── main.py             # Groq executive brief + rule-based fallback
│   │   └── Dockerfile
│   └── recommender/            # Recommender Agent (Port 8005)
│       ├── main.py             # Web search + Groq recommendations
│       └── Dockerfile
│
├── frontend/                   # React 18 + Vite + Tailwind
│   ├── src/
│   │   ├── pages/              # Login, Dashboard, Analysis, Portfolio, etc.
│   │   ├── components/         # Layout, ProtectedRoute, SupplierWorldMap, UI kit
│   │   ├── stores/             # Zustand: authStore, appStore, themeStore
│   │   └── api/                # bff.js — all BFF endpoint clients
│   └── Dockerfile              # nginx multi-stage build
│
├── data/
│   ├── suppliers.db            # SQLite database (auto-created)
│   ├── sdn.csv                 # OFAC SDN list (auto-downloaded)
│   └── suppliers.py            # DB schema and seed data
│
└── utils/
    ├── pdf_export.py           # ReportLab PDF generation
    └── auth.py                 # Auth helpers
```

---

## Quick Start

### Option 1 — Docker (Recommended)

**Prerequisites:** Docker Desktop, Git

```bash
git clone https://github.com/<your-username>/supplyshield.git
cd supplyshield

# Copy and fill in your API keys
cp .env.example .env
# Edit .env with your keys (see Environment Variables section)

# Build and start all 7 services
docker compose up --build
```

Open [http://localhost](http://localhost) in your browser.

**Login credentials (demo):**
- Username: `admin`
- Password: `supplyshield2025`
- MFA: scan the QR code shown on the OTP setup screen with Google Authenticator or Authy

> The OFAC SDN list downloads automatically on first startup (~25 MB). This takes 30–60 seconds depending on your connection. Check `docker compose logs geointel` to confirm: `"Loaded 18,708 SDN records"`.

---

### Option 2 — Local Development

**Prerequisites:** Python 3.11+, Node.js 18+

#### 1. Install Python dependencies

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r bff/requirements.txt
```

#### 2. Install and start the frontend

```bash
cd frontend
npm install
npm run dev                       # starts on http://localhost:5173
```

#### 3. Start each service in a separate terminal

```bash
# Terminal 1 — GeoIntel
cd services/geointel && uvicorn main:app --port 8001 --reload

# Terminal 2 — RiskCalc
cd services/riskcalc && uvicorn main:app --port 8002 --reload

# Terminal 3 — Gate
cd services/gate && uvicorn main:app --port 8003 --reload

# Terminal 4 — Summarizer
cd services/summarizer && uvicorn main:app --port 8004 --reload

# Terminal 5 — Recommender
cd services/recommender && uvicorn main:app --port 8005 --reload

# Terminal 6 — Orchestrator
cd orchestrator && uvicorn main:app --port 8000 --reload

# Terminal 7 — BFF
cd bff && uvicorn main:app --port 8006 --reload
```

#### 4. Seed the database (optional)

```bash
python data/suppliers.py          # creates schema + seeds 87 demo suppliers
python seed_demo_data.py          # adds demo company profile
```

---

## Environment Variables

Copy `.env.example` to `.env` and fill in the values:

```env
# ── LLM & Intelligence APIs ──────────────────────────────────
GROQ_API_KEY=           # Required for AI summaries and recommendations
                        # Free tier: https://console.groq.com
NEWSAPI_KEY=            # Required for live news risk detection
                        # Free tier: https://newsapi.org
SERPER_API_KEY=         # Required for web search (50% rule + recommender)
                        # Free tier: https://serper.dev

# ── Authentication ────────────────────────────────────────────
JWT_SECRET=change-this-to-a-long-random-string-in-production
JWT_EXPIRE_S=86400      # Token lifetime in seconds (default: 24 hours)
AUTH_REQUIRED=true      # Set to false to disable auth entirely (dev only)

# ── Database ──────────────────────────────────────────────────
DB_PATH=/app/data/suppliers.db   # Set automatically by docker-compose

# ── Service URLs (set automatically by docker-compose) ────────
ORCHESTRATOR_URL=http://orchestrator:8000
GEOINTEL_URL=http://geointel:8001
RISKCALC_URL=http://riskcalc:8002
GATE_URL=http://gate:8003
SUMMARIZER_URL=http://summarizer:8004
RECOMMENDER_URL=http://recommender:8005
```

**Minimum viable setup** (OFAC screening + risk scoring only, no AI features):
Only `JWT_SECRET` is strictly required. The platform degrades gracefully — without `GROQ_API_KEY` the Summarizer uses its rule-based fallback and the Recommender returns a structured fallback response. Without `NEWSAPI_KEY` the news risk defaults to `NONE`.

---

## Risk Scoring Reference

### Thresholds

| Category | Score Range | Gate Decision |
|---|---|---|
| `HIGH` | ≥ 0.65 | `REQUIRES_APPROVAL` |
| `MEDIUM` | 0.40 – 0.64 | `REQUIRES_APPROVAL` |
| `LOW` | < 0.40 | `AUTO_APPROVED` |
| `SANCTIONED` | Any (override ≥ 0.90) | `BLOCKED` |

### Default Weight Sets

**Standard (4-factor)**
```
geography:     0.38
news:          0.31
single_source: 0.16
lead_time:     0.15
```

**Onboarded (7-factor)**
```
geography:        0.28   news:             0.22
single_source:    0.11   lead_time:        0.11
financial_health: 0.11   on_time_delivery: 0.10
contract_expiry:  0.07
```

**Expanded (13-factor)**
```
geography:             0.14   news:                  0.12
financial_health:      0.09   audit_pass_rate:       0.09
single_source:         0.07   cyber_posture:         0.07
on_time_delivery:      0.07   order_fill_rate:       0.08
lead_time:             0.06   lead_time_variability: 0.06
disruption_frequency:  0.06   improvement_index:     0.05
contract_expiry:       0.04
```

All weights are defined in [`config.py`](config.py) and can be overridden per-request via the `custom_weights` field in the analysis payload.

### Component Score Maps

| Factor | Inputs → Score |
|---|---|
| **News Risk** | HIGH→0.80, MEDIUM→0.40, LOW→0.10, NONE→0.00 |
| **Financial Health** | Poor→0.85, Fair→0.45, Good→0.05 |
| **Cyber Posture** | Poor→0.85, Fair→0.40, Good→0.05 |
| **Lead-Time Variability** | High→0.80, Medium→0.40, Low→0.00 |
| **On-Time Delivery** | ≥95%→0.00, ≥85%→0.20, ≥70%→0.50, <70%→0.85 |
| **Order Fill Rate** | ≥95%→0.00, ≥85%→0.20, ≥70%→0.55, <70%→0.90 |
| **Audit Pass Rate** | ≥90%→0.00, ≥75%→0.30, ≥60%→0.60, <60%→0.90 |
| **Improvement Index** | ≥85%→0.00, ≥65%→0.30, ≥45%→0.60, <45%→0.85 |
| **Disruption Freq.** | 0→0.00, 1→0.25, 2–3→0.55, ≥4→0.90 |
| **Contract Expiry** | ≤30d→0.90, ≤90d→0.55, ≤180d→0.25, >180d→0.00 |

---

## API Reference

All endpoints are proxied through the BFF at `http://localhost:8006`. The frontend calls `/api/*` which nginx forwards to the BFF.

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/auth/login` | Validate username + password |
| `POST` | `/auth/verify-otp` | Verify TOTP code → returns JWT |
| `GET` | `/auth/qr-code` | Get QR code PNG for authenticator setup |
| `GET` | `/auth/me` | Validate current token |

### Core Analysis

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/analyze` | Full 5-agent pipeline for a single supplier |
| `POST` | `/batch` | Screen all suppliers in the database |
| `POST` | `/recommend` | Generate recommendations on demand |

**`POST /analyze` — minimal payload:**
```json
{
  "company_name": "Acme Electronics Ltd",
  "country": "China",
  "single_source": false,
  "lead_time_weeks": 14
}
```

**`POST /analyze` — full 13-factor payload:**
```json
{
  "company_name": "Acme Electronics Ltd",
  "country": "China",
  "geo_concentration": 0.55,
  "single_source": true,
  "lead_time_weeks": 14,
  "include_summary": true,
  "include_recommendations": true,
  "financial_health": "Fair",
  "on_time_delivery_rate": 82.5,
  "contract_expiry": "2025-09-30",
  "tier_level": "Tier 2",
  "order_fill_rate": 78.0,
  "lead_time_variability": "High",
  "audit_pass_rate": 71.0,
  "improvement_index": 55.0,
  "cyber_posture": "Fair",
  "disruption_frequency": 2,
  "annual_spend_usd": 4500000,
  "inventory_buffer_days": 21,
  "has_rto_defined": false,
  "company_name_buyer": "GlobalTech Manufacturing",
  "company_industry": "Electronics"
}
```

### Suppliers & Portfolio

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/suppliers/onboarded` | List all onboarded suppliers |
| `POST` | `/suppliers/onboarded` | Add or update a supplier |
| `DELETE` | `/suppliers/onboarded/{id}` | Remove a supplier |
| `POST` | `/suppliers/excel-upload` | Bulk import from Excel file |
| `GET` | `/suppliers/excel-template` | Download the import template |
| `GET` | `/portfolio` | Aggregate portfolio risk dashboard data |
| `GET` | `/risky-suppliers` | HIGH + MEDIUM risk suppliers with recommendations |
| `GET` | `/audit-log` | Full screening history |

### Recommendations & Actions

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/recommendations/{supplier_name}` | Get stored recommendations |
| `POST` | `/recommendations/{supplier_name}/action-status` | Mark an action complete/incomplete |

**Action status payload:**
```json
{ "action_id": "immediate_0", "completed": true }
```

### Utilities

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | BFF + all agent health check |
| `POST` | `/pdf/generate` | Generate branded PDF risk report |
| `GET` | `/profile` | Get company profile |
| `POST` | `/profile` | Save company profile |

### GeoIntel Direct Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `http://localhost:8001/screen` | Screen a supplier (OFAC + news + 50% rule) |
| `POST` | `http://localhost:8001/refresh-sdn` | Force re-download SDN list from OFAC |
| `GET` | `http://localhost:8001/health` | SDN record count + list age in days |

---

## Technology Stack

| Layer | Technology | Version |
|---|---|---|
| **Frontend** | React + Vite + Tailwind CSS | 18.3 / 5.3 / 3.4 |
| **State** | Zustand | 4.5 |
| **Charts** | Recharts | 2.12 |
| **Backend** | FastAPI + Uvicorn | 0.135 / 0.41 |
| **Validation** | Pydantic | 2.12 |
| **LLM** | Groq (Llama 3.3 70B Versatile) | — |
| **Fuzzy Match** | RapidFuzz | 3.14 |
| **News** | NewsAPI Python | 0.2.7 |
| **Web Search** | Serper API | — |
| **PDF** | ReportLab | 4.4 |
| **Auth** | PyJWT + PyOTP | 2.12 / 2.9 |
| **Database** | SQLite | 3 |
| **Containers** | Docker + Docker Compose | — |
| **Web Server** | nginx | (alpine) |

---

## Agent Pipeline Performance

| Agent | Typical Latency | Notes |
|---|---|---|
| GeoIntelAgent | ~350 ms | + ~8s if OFAC 50% rule triggers Groq |
| RiskCalcAgent | ~45 ms | Fully deterministic, no network calls |
| ProcurementGateAgent | ~10 ms | Pure decision logic |
| SummarizerAgent | ~2,100 ms | Groq LLM call; ~200 ms on rule-based fallback |
| RecommenderAgent | ~8,500 ms | 4 parallel Serper searches + Groq generation |
| **Full pipeline (with AI)** | **~11–12 s** | |
| **Full pipeline (no recommendations)** | **~2.5 s** | |

---

## Configuration

All tunable parameters live in [`config.py`](config.py). No service restart required for local development changes.

```python
# Risk thresholds
HIGH_THRESHOLD   = 0.65   # score >= this → HIGH / REQUIRES_APPROVAL
MEDIUM_THRESHOLD = 0.40   # score >= this → MEDIUM; below → LOW

# OFAC screening
OFAC_SIMILARITY_THRESHOLD = 85   # minimum fuzzy-match score (0–100)
OFAC_MAX_MATCHES           = 10  # maximum SDN matches returned per query

# News risk
NEWS_HIGH_MIN_HEADLINES   = 3    # >= N adverse headlines → HIGH news risk
NEWS_MEDIUM_MIN_HEADLINES = 1    # >= N adverse headlines → MEDIUM news risk

# Trend detection
TREND_DETERIORATING_DELTA =  0.05   # score rose by >= this → DETERIORATING
TREND_IMPROVING_DELTA     = -0.05   # score fell by >= this → IMPROVING
```

Country risk scores and industry certification mappings are also defined in `config.py` and used by the GeoIntel and Recommender agents respectively.

---

## Graceful Degradation

SupplyShield is designed to produce value at every level of API key availability:

| APIs configured | Features available |
|---|---|
| None | OFAC screening, deterministic 13-factor scoring, procurement gate, rule-based summary |
| + `NEWSAPI_KEY` | + Live adverse news detection |
| + `SERPER_API_KEY` | + OFAC 50% Rule shareholding check |
| + `GROQ_API_KEY` | + AI executive brief, specific named recommendations |
| All | Full platform |

---

## Roadmap

- [ ] Multi-tenant SaaS with organization-scoped supplier portfolios
- [ ] Predictive risk scoring via time-series trend analysis
- [ ] SAP Ariba and Oracle Procurement Cloud webhook connectors
- [ ] Regulatory expansion: EU CBAM carbon risk scoring, Japan ESPA conflict mineral tracking
- [ ] PostgreSQL backend with connection pooling for production scale
- [ ] Real-time OFAC SDN webhook (replace 7-day polling with push updates)
- [ ] Async streaming for LLM responses to reduce perceived latency

---

## Author

**Kavish Jain** — Economics, Indian Institute of Technology Roorkee
Built for Microsoft AI Unlocked Hackathon · Challenge Track 4

> *Information asymmetry is a market failure. Multi-agent systems are uniquely positioned to correct it.*

---

*MIT License*
