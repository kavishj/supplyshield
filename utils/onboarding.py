import sys
import streamlit as st
import sqlite3
from pathlib import Path
import os

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
from config import COUNTRY_RISK

DB_PATH = Path(os.getenv("DB_PATH",
               r"C:\Users\KAVISH\supplyshield_final\data\suppliers.db"))

INDUSTRIES = [
    "Automotive", "Aerospace & Defense", "Chemicals",
    "Consumer Electronics", "Energy & Utilities",
    "Financial Services", "Food & Beverage",
    "Healthcare & Pharma", "Industrial Machinery",
    "Information Technology", "Logistics & Shipping",
    "Medical Devices", "Mining & Metals",
    "Oil & Gas", "Retail & E-commerce",
    "Semiconductors", "Telecommunications",
    "Textiles & Apparel", "Other",
]

SP_RATINGS = [
    "Not Rated", "AAA", "AA+", "AA", "AA-",
    "A+", "A", "A-", "BBB+", "BBB", "BBB-",
    "BB+", "BB", "BB-", "B+", "B", "B-",
    "CCC", "CC", "C", "D",
]

def get_profile() -> dict:
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM company_profile ORDER BY id DESC LIMIT 1"
        ).fetchone()
        conn.close()
        return dict(row) if row else {}
    except:
        return {}

def save_profile(data: dict):
    conn = sqlite3.connect(DB_PATH)
    existing = conn.execute(
        "SELECT id FROM company_profile LIMIT 1"
    ).fetchone()

    if existing:
        conn.execute("""
            UPDATE company_profile SET
                business_name       = ?,
                country             = ?,
                industry            = ?,
                contact_email       = ?,
                tax_id              = ?,
                annual_revenue      = ?,
                lead_time_weeks     = ?,
                num_employees       = ?,
                iso_certifications  = ?,
                anti_bribery_policy = ?,
                labor_law_compliance= ?,
                sp_rating           = ?,
                products_services   = ?,
                address             = ?,
                onboarding_complete = 1,
                updated_at          = datetime('now')
            WHERE id = ?
        """, (
            data["business_name"], data["country"],
            data["industry"],      data["contact_email"],
            data.get("tax_id"),    data.get("annual_revenue"),
            data.get("lead_time_weeks"), data.get("num_employees"),
            data.get("iso_certifications"),
            int(data.get("anti_bribery_policy", False)),
            int(data.get("labor_law_compliance", False)),
            data.get("sp_rating"), data.get("products_services"),
            data.get("address"),   existing[0],
        ))
    else:
        conn.execute("""
            INSERT INTO company_profile (
                business_name, country, industry, contact_email,
                tax_id, annual_revenue, lead_time_weeks, num_employees,
                iso_certifications, anti_bribery_policy,
                labor_law_compliance, sp_rating,
                products_services, address, onboarding_complete
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,1)
        """, (
            data["business_name"], data["country"],
            data["industry"],      data["contact_email"],
            data.get("tax_id"),    data.get("annual_revenue"),
            data.get("lead_time_weeks"), data.get("num_employees"),
            data.get("iso_certifications"),
            int(data.get("anti_bribery_policy", False)),
            int(data.get("labor_law_compliance", False)),
            data.get("sp_rating"), data.get("products_services"),
            data.get("address"),
        ))

    conn.commit()
    conn.close()

def is_onboarding_complete() -> bool:
    profile = get_profile()
    return bool(profile.get("onboarding_complete", 0))

def show_onboarding():
    """Full-page onboarding — two-column layout with context panel."""

    st.markdown("""
    <style>
      .main .block-container {
        max-width: 1060px !important;
        padding: 2.5rem 2rem !important;
        margin: 0 auto !important;
      }
      section[data-testid="stSidebar"] { display: none !important; }
      footer { display: none !important; }

      /* ── Header ───────────────────────────────────────────── */
      .ob-brand {
        font-size: 1.5rem;
        font-weight: 900;
        color: #FFFFFF;
        letter-spacing: -1px;
        margin-bottom: 2px;
      }
      .ob-brand-sub {
        font-size: 0.7rem;
        color: #00C2FF;
        text-transform: uppercase;
        letter-spacing: 2.5px;
        font-weight: 600;
        margin-bottom: 2rem;
      }

      /* ── Progress bar ─────────────────────────────────────── */
      .ob-progress-wrap {
        display: flex;
        align-items: center;
        gap: 0;
        margin-bottom: 2.5rem;
      }
      .ob-step-bubble {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.78rem;
        font-weight: 700;
        flex-shrink: 0;
      }
      .ob-step-bubble.active {
        background: #00C2FF;
        color: #0A1628;
      }
      .ob-step-bubble.done {
        background: rgba(0,194,255,0.15);
        color: #00C2FF;
        border: 1px solid rgba(0,194,255,0.3);
      }
      .ob-step-bubble.upcoming {
        background: #112240;
        color: #334155;
        border: 1px solid #1E3A5F;
      }
      .ob-step-label {
        font-size: 0.68rem;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        margin-left: 8px;
        margin-right: 20px;
      }
      .ob-step-label.active { color: #E2E8F0; font-weight: 600; }
      .ob-step-label.done   { color: #00C2FF; }
      .ob-step-label.upcoming { color: #334155; }
      .ob-step-line {
        flex: 1;
        height: 1px;
        background: #1E3A5F;
        margin: 0 8px 0 0;
        max-width: 40px;
      }

      /* ── Context sidebar cards ────────────────────────────── */
      .ctx-card {
        background: #112240;
        border: 1px solid #1E3A5F;
        border-radius: 12px;
        padding: 18px 20px;
        margin-bottom: 14px;
      }
      .ctx-card-title {
        font-size: 0.82rem;
        font-weight: 700;
        color: #E2E8F0;
        margin-bottom: 6px;
      }
      .ctx-card-body {
        font-size: 0.76rem;
        color: #64748B;
        line-height: 1.55;
      }
      .ctx-card-body b { color: #94A3B8; }

      .ctx-unlocks {
        background: #0D1F3C;
        border: 1px solid #1E3A5F;
        border-left: 3px solid #00C2FF;
        border-radius: 8px;
        padding: 14px 16px;
        margin-bottom: 14px;
      }
      .ctx-unlocks-title {
        font-size: 0.68rem;
        color: #00C2FF;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        font-weight: 600;
        margin-bottom: 10px;
      }
      .ctx-unlock-item {
        display: flex;
        align-items: flex-start;
        gap: 8px;
        font-size: 0.76rem;
        color: #64748B;
        margin-bottom: 6px;
        line-height: 1.4;
      }
      .ctx-unlock-item:last-child { margin-bottom: 0; }
      .ctx-dot {
        width: 5px;
        height: 5px;
        border-radius: 50%;
        background: #00C2FF;
        flex-shrink: 0;
        margin-top: 5px;
      }

      /* ── Form styling ─────────────────────────────────────── */
      .ob-section-header {
        font-size: 0.68rem;
        color: #00C2FF;
        text-transform: uppercase;
        letter-spacing: 2px;
        font-weight: 600;
        padding-bottom: 8px;
        border-bottom: 1px solid #1E3A5F;
        margin-bottom: 1rem;
        margin-top: 0.5rem;
      }
      .ob-section-header span {
        color: #334155;
        font-size: 0.62rem;
        font-weight: 400;
        letter-spacing: 0;
        text-transform: none;
        margin-left: 8px;
      }
      .ob-note {
        background: #112240;
        border: 1px solid #1E3A5F;
        border-left: 3px solid #00C2FF;
        border-radius: 8px;
        padding: 12px 16px;
        font-size: 0.8rem;
        color: #94A3B8;
        line-height: 1.6;
        margin-bottom: 1.5rem;
      }
      div[data-testid="stTextInput"] label,
      div[data-testid="stSelectbox"] label,
      div[data-testid="stNumberInput"] label,
      div[data-testid="stTextArea"] label {
        color: #94A3B8 !important;
        font-size: 0.76rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.8px !important;
      }
      button[kind="primary"] {
        background: #00C2FF !important;
        color: #0A1628 !important;
        font-weight: 700 !important;
        border-radius: 8px !important;
        width: 100% !important;
      }
    </style>
    """, unsafe_allow_html=True)

    existing = get_profile()

    # ── Brand header ──────────────────────────────────────────
    st.markdown("""
    <div class="ob-brand">SupplyShield</div>
    <div class="ob-brand-sub">Company Setup</div>
    """, unsafe_allow_html=True)

    # ── Progress indicator ────────────────────────────────────
    st.markdown("""
    <div class="ob-progress-wrap">
      <div class="ob-step-bubble active">1</div>
      <div class="ob-step-label active">Company Identity</div>
      <div class="ob-step-line"></div>
      <div class="ob-step-bubble done">2</div>
      <div class="ob-step-label done">Business Details</div>
      <div class="ob-step-line"></div>
      <div class="ob-step-bubble done">3</div>
      <div class="ob-step-label done">Compliance Profile</div>
      <div class="ob-step-line"></div>
      <div class="ob-step-bubble upcoming">✓</div>
      <div class="ob-step-label upcoming">Launch</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Two-column layout: form left, context right ───────────
    form_col, ctx_col = st.columns([6, 4], gap="large")

    with ctx_col:
        st.markdown("""
        <div class="ctx-unlocks">
          <div class="ctx-unlocks-title">What this unlocks</div>
          <div class="ctx-unlock-item">
            <div class="ctx-dot"></div>
            <span>Personalised risk scores benchmarked against your industry and geography</span>
          </div>
          <div class="ctx-unlock-item">
            <div class="ctx-dot"></div>
            <span>Spend-weighted recommendations — higher spend drives more aggressive mitigation</span>
          </div>
          <div class="ctx-unlock-item">
            <div class="ctx-dot"></div>
            <span>Audit-ready PDF reports with your company letterhead context</span>
          </div>
          <div class="ctx-unlock-item">
            <div class="ctx-dot"></div>
            <span>8-factor risk model for your onboarded suppliers (vs. 5-factor for unknown suppliers)</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="ctx-card">
          <div class="ctx-card-title">Your data stays local</div>
          <div class="ctx-card-body">
            All profile information is stored in a <b>local SQLite database</b>
            on your machine. Nothing is sent to external servers.
            The data is only used to personalise your risk analysis.
          </div>
        </div>

        <div class="ctx-card">
          <div class="ctx-card-title">Why industry matters</div>
          <div class="ctx-card-body">
            A semiconductor firm and a textile company face completely different
            supply chain risk profiles. Your industry calibrates which risk factors
            SupplyShield weighs most heavily in your recommendations.
          </div>
        </div>

        <div class="ctx-card">
          <div class="ctx-card-title">Annual revenue &amp; spend</div>
          <div class="ctx-card-body">
            Revenue context lets the AI generate <b>proportionate</b> recommendations.
            A $500M firm's mitigation strategy for a $2M supplier is different
            from a $50M firm's — same risk, different stakes.
          </div>
        </div>

        <div class="ctx-card">
          <div class="ctx-card-title">Compliance profile</div>
          <div class="ctx-card-body">
            Your ISO certifications and compliance policies appear in
            generated audit reports, demonstrating good-faith due diligence
            to regulators and auditors.
          </div>
        </div>
        """, unsafe_allow_html=True)

    with form_col:
        st.markdown("""
        <div class="ob-note">
          Fields marked <b>*</b> are required. All other fields improve the accuracy
          of your risk scores and AI recommendations — fill in as much as you can.
        </div>
        """, unsafe_allow_html=True)

        # ── Section 1: Company Identity ───────────────────────
        st.markdown('<div class="ob-section-header">Company Identity <span>— required</span></div>',
                    unsafe_allow_html=True)

        business_name = st.text_input(
            "Official Business Name *",
            value=existing.get("business_name", ""),
            placeholder="e.g. Acme Manufacturing Corp",
        )

        col1, col2 = st.columns(2)
        with col1:
            country = st.text_input(
                "Country of Incorporation *",
                value=existing.get("country", ""),
                placeholder="e.g. USA, GERMANY, INDIA",
            )
        with col2:
            industry = st.selectbox(
                "Industry *",
                INDUSTRIES,
                index=INDUSTRIES.index(existing.get("industry", "Other"))
                if existing.get("industry") in INDUSTRIES else 0,
            )

        contact_email = st.text_input(
            "Primary Contact Email *",
            value=existing.get("contact_email", ""),
            placeholder="procurement@yourcompany.com",
        )

        # ── Section 2: Business Details ───────────────────────
        st.markdown(
            '<div class="ob-section-header">Business Details <span>— recommended</span></div>',
            unsafe_allow_html=True,
        )

        col3, col4 = st.columns(2)
        with col3:
            tax_id = st.text_input(
                "Tax ID / Business Registration",
                value=existing.get("tax_id", "") or "",
                placeholder="e.g. 12-3456789",
            )
        with col4:
            sp_rating = st.selectbox(
                "S&P Global Credit Rating",
                SP_RATINGS,
                index=SP_RATINGS.index(existing.get("sp_rating", "Not Rated"))
                if existing.get("sp_rating") in SP_RATINGS else 0,
            )

        col5, col6, col7 = st.columns(3)
        with col5:
            annual_revenue = st.number_input(
                "Annual Revenue (USD)",
                min_value=0,
                value=int(existing.get("annual_revenue", 0) or 0),
                step=1000000,
                format="%d",
                help="Last financial year revenue in USD",
            )
        with col6:
            lead_time_weeks = st.number_input(
                "Typical Lead Time (weeks)",
                min_value=1,
                max_value=104,
                value=int(existing.get("lead_time_weeks", 12) or 12),
                help="Average weeks from order to delivery",
            )
        with col7:
            num_employees = st.number_input(
                "Number of Employees",
                min_value=0,
                value=int(existing.get("num_employees", 0) or 0),
                step=10,
            )

        address = st.text_input(
            "Physical Address",
            value=existing.get("address", "") or "",
            placeholder="123 Business St, City, Country",
        )

        products_services = st.text_area(
            "Products / Services Description",
            value=existing.get("products_services", "") or "",
            placeholder="Brief description of what your company produces or provides...",
            height=80,
        )

        # ── Section 3: Compliance Profile ─────────────────────
        st.markdown(
            '<div class="ob-section-header">Compliance Profile <span>— optional</span></div>',
            unsafe_allow_html=True,
        )

        iso_certifications = st.text_input(
            "Quality Certifications",
            value=existing.get("iso_certifications", "") or "",
            placeholder="e.g. ISO 9001, ISO 14001, AS9100",
            help="Comma-separated list of certifications",
        )

        col8, col9 = st.columns(2)
        with col8:
            anti_bribery = st.checkbox(
                "Anti-bribery & anti-corruption policy in place",
                value=bool(existing.get("anti_bribery_policy", 0)),
            )
        with col9:
            labor_compliance = st.checkbox(
                "Compliant with local labor and safety laws",
                value=bool(existing.get("labor_law_compliance", 0)),
            )

        # ── Submit ────────────────────────────────────────────
        st.markdown("<div style='margin-top:1.5rem'></div>", unsafe_allow_html=True)

        errors = []
        if st.button("Complete Setup & Launch SupplyShield →",
                     type="primary", use_container_width=True):
            if not business_name.strip():
                errors.append("Official Business Name is required.")
            if not country.strip():
                errors.append("Country of Incorporation is required.")
            elif country.strip().upper() not in COUNTRY_RISK:
                st.warning(
                    f"Country **{country.strip()}** is not in the risk database. "
                    "Risk scoring will use your geographic concentration setting as a fallback."
                )
            if not contact_email.strip():
                errors.append("Contact Email is required.")
            else:
                _email = contact_email.strip()
                _at = _email.find("@")
                if _at <= 0 or _at == len(_email) - 1 or "." not in _email[_at:]:
                    errors.append("Please enter a valid email address (e.g. name@company.com).")

            if errors:
                for e in errors:
                    st.error(e)
            else:
                save_profile({
                    "business_name":       business_name.strip(),
                    "country":             country.strip().upper(),
                    "industry":            industry,
                    "contact_email":       contact_email.strip(),
                    "tax_id":              tax_id.strip() or None,
                    "annual_revenue":      annual_revenue or None,
                    "lead_time_weeks":     lead_time_weeks,
                    "num_employees":       num_employees or None,
                    "iso_certifications":  iso_certifications.strip() or None,
                    "anti_bribery_policy": anti_bribery,
                    "labor_law_compliance":labor_compliance,
                    "sp_rating":           sp_rating if sp_rating != "Not Rated" else None,
                    "products_services":   products_services.strip() or None,
                    "address":             address.strip() or None,
                })
                st.session_state["onboarding_complete"] = True
                st.success("Profile saved. Loading SupplyShield...")
                st.rerun()

        if not existing.get("onboarding_complete"):
            st.markdown("<div style='margin-top:0.5rem'></div>", unsafe_allow_html=True)
            if st.button("Skip for now", use_container_width=True):
                st.session_state["onboarding_complete"] = True
                st.rerun()
            st.caption(
                "You can complete your profile later from the Company Profile page. "
                "Skipping will limit personalisation."
            )

    # ── Footer ────────────────────────────────────────────────
    st.markdown("""
    <div style="text-align:center;margin-top:2.5rem;padding-top:1rem;
                border-top:1px solid #0D1F3C;
                font-size:0.7rem;color:#334155">
      SupplyShield &nbsp;·&nbsp; Microsoft AI Unlocked Hackathon
      &nbsp;·&nbsp; IIT Roorkee
    </div>
    """, unsafe_allow_html=True)
