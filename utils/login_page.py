import streamlit as st

from .auth import (verify_password, verify_otp, generate_qr_code,
                   is_totp_confirmed, mark_totp_confirmed)


def show_login_page():
    """Full-page split login — hero left, form right."""

    st.markdown("""
    <!-- Google Fonts: Plus Jakarta Sans + DM Sans -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800&family=DM+Sans:wght@400;500;700&display=swap" rel="stylesheet">

    <style>
      /* ── Global surface reset ───────────────────────────────── */
      .stApp,
      [data-testid="stAppViewContainer"],
      [data-testid="stHeader"],
      body {
        background: #E0E5EC !important;
        font-family: 'DM Sans', sans-serif !important;
      }
      section[data-testid="stSidebar"] { display: none !important; }
      #MainMenu { display: none !important; }
      footer { display: none !important; }
      header[data-testid="stHeader"] { background: transparent !important; }

      /* ── Container ──────────────────────────────────────────── */
      .main .block-container {
        max-width: 1040px !important;
        padding: 3rem 2.5rem 2rem 2.5rem !important;
        margin: 0 auto !important;
        background: #E0E5EC !important;
      }
      [data-testid="stHorizontalBlock"] {
        gap: 2rem !important;
        align-items: flex-start !important;
      }

      /* ── LEFT HERO PANEL ────────────────────────────────────── */
      .hero-panel {
        background: #E0E5EC;
        border-radius: 32px;
        padding: 2.2rem 2rem;
        box-shadow: 9px 9px 16px rgb(163,177,198,0.6),
                    -9px -9px 16px rgba(255,255,255,0.5);
      }
      .hero-logo {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 1.9rem;
        font-weight: 800;
        color: #3D4852;
        letter-spacing: -1.5px;
        line-height: 1;
        margin-bottom: 4px;
      }
      .hero-logo span { color: #6C63FF; }
      .hero-tagline {
        font-size: 0.65rem;
        color: #6C63FF;
        text-transform: uppercase;
        letter-spacing: 3px;
        font-weight: 700;
        margin-bottom: 1.1rem;
      }
      .hero-divider {
        width: 44px;
        height: 3px;
        background: linear-gradient(90deg, #6C63FF, #38B2AC);
        border-radius: 2px;
        margin-bottom: 1.2rem;
      }
      .hero-headline {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 1.3rem;
        font-weight: 700;
        color: #3D4852;
        line-height: 1.42;
        margin-bottom: 0.7rem;
        letter-spacing: -0.4px;
      }
      .hero-sub {
        font-size: 0.86rem;
        color: #6B7280;
        line-height: 1.72;
        margin-bottom: 1.7rem;
      }

      /* ── Impact stats — 2×2 extruded grid ─────────────────── */
      .stats-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 11px;
        margin-bottom: 1.4rem;
      }
      .stat-card {
        background: #E0E5EC;
        border-radius: 16px;
        padding: 14px 15px;
        box-shadow: 5px 5px 10px rgb(163,177,198,0.6),
                    -5px -5px 10px rgba(255,255,255,0.5);
        transition: box-shadow 0.3s ease-out, transform 0.3s ease-out;
        cursor: default;
      }
      .stat-card:hover {
        transform: translateY(-2px);
        box-shadow: 8px 8px 16px rgb(163,177,198,0.7),
                    -8px -8px 16px rgba(255,255,255,0.6);
      }
      .stat-card-value {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 1.45rem;
        font-weight: 800;
        color: #6C63FF;
        line-height: 1;
        margin-bottom: 5px;
        letter-spacing: -0.5px;
      }
      .stat-card-label {
        font-size: 0.68rem;
        color: #6B7280;
        line-height: 1.42;
      }

      /* ── Value props — 2×2 extruded grid ──────────────────── */
      .vp-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 11px;
      }
      .vp-item {
        background: #E0E5EC;
        border-radius: 16px;
        padding: 13px 13px;
        box-shadow: 5px 5px 10px rgb(163,177,198,0.6),
                    -5px -5px 10px rgba(255,255,255,0.5);
        transition: box-shadow 0.3s ease-out, transform 0.3s ease-out;
        cursor: default;
      }
      .vp-item:hover {
        transform: translateY(-2px);
        box-shadow: 8px 8px 16px rgb(163,177,198,0.7),
                    -8px -8px 16px rgba(255,255,255,0.6);
      }
      .vp-icon {
        width: 30px;
        height: 30px;
        border-radius: 50%;
        background: #E0E5EC;
        box-shadow: inset 3px 3px 6px rgb(163,177,198,0.6),
                    inset -3px -3px 6px rgba(255,255,255,0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 9px;
        font-size: 0.85rem;
      }
      .vp-text strong {
        display: block;
        font-size: 0.74rem;
        color: #3D4852;
        font-weight: 700;
        margin-bottom: 3px;
        line-height: 1.3;
      }
      .vp-text small {
        font-size: 0.69rem;
        color: #6B7280;
        line-height: 1.5;
      }

      /* ── RIGHT FORM PANEL ───────────────────────────────────── */
      .form-panel {
        background: #E0E5EC;
        border-radius: 32px;
        padding: 1.8rem 1.8rem 1.5rem 1.8rem;
        box-shadow: 9px 9px 16px rgb(163,177,198,0.6),
                    -9px -9px 16px rgba(255,255,255,0.5);
        margin-bottom: 1rem;
      }
      .step-badge {
        display: inline-flex;
        align-items: center;
        font-size: 0.59rem;
        color: #6C63FF;
        text-transform: uppercase;
        letter-spacing: 2px;
        font-weight: 700;
        background: #E0E5EC;
        border-radius: 9999px;
        padding: 4px 13px;
        margin-bottom: 11px;
        box-shadow: inset 3px 3px 6px rgb(163,177,198,0.6),
                    inset -3px -3px 6px rgba(255,255,255,0.5);
      }
      .form-title {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 1.25rem;
        font-weight: 700;
        color: #3D4852;
        margin-bottom: 4px;
        letter-spacing: -0.4px;
      }
      .form-sub {
        font-size: 0.79rem;
        color: #6B7280;
        line-height: 1.55;
      }

      /* ── Inputs ─────────────────────────────────────────────── */
      div[data-testid="stTextInput"] input {
        background: #E0E5EC !important;
        border: none !important;
        border-radius: 16px !important;
        color: #3D4852 !important;
        font-size: 0.95rem !important;
        padding: 13px 16px !important;
        font-family: 'DM Sans', sans-serif !important;
        box-shadow: inset 6px 6px 10px rgb(163,177,198,0.6),
                    inset -6px -6px 10px rgba(255,255,255,0.5) !important;
        outline: none !important;
        transition: box-shadow 0.3s ease-out !important;
      }
      div[data-testid="stTextInput"] input:focus {
        box-shadow: inset 10px 10px 20px rgb(163,177,198,0.7),
                    inset -10px -10px 20px rgba(255,255,255,0.6) !important;
        outline: 2px solid rgba(108,99,255,0.5) !important;
        outline-offset: 2px !important;
      }
      div[data-testid="stTextInput"] input::placeholder {
        color: #A0AEC0 !important;
      }
      div[data-testid="stTextInput"] label {
        color: #6B7280 !important;
        font-size: 0.7rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.8px !important;
        font-weight: 600 !important;
        font-family: 'DM Sans', sans-serif !important;
      }

      /* ── Primary button ─────────────────────────────────────── */
      button[kind="primary"] {
        background: #6C63FF !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 16px !important;
        font-size: 0.9rem !important;
        width: 100% !important;
        margin-top: 6px !important;
        letter-spacing: 0.3px !important;
        font-family: 'DM Sans', sans-serif !important;
        transition: transform 0.3s ease-out, box-shadow 0.3s ease-out,
                    background 0.3s ease-out !important;
        box-shadow: 6px 6px 12px rgb(163,177,198,0.6),
                    -6px -6px 12px rgba(255,255,255,0.5) !important;
      }
      button[kind="primary"]:hover {
        transform: translateY(-1px) !important;
        background: #8B84FF !important;
        box-shadow: 9px 9px 16px rgb(163,177,198,0.7),
                    -9px -9px 16px rgba(255,255,255,0.6) !important;
      }
      button[kind="primary"]:active {
        transform: translateY(0.5px) !important;
        box-shadow: inset 4px 4px 8px rgba(80,70,200,0.35),
                    inset -2px -2px 4px rgba(255,255,255,0.15) !important;
      }

      /* ── Secondary / Back button ────────────────────────────── */
      button[kind="secondary"] {
        background: #E0E5EC !important;
        color: #6B7280 !important;
        font-weight: 600 !important;
        border: none !important;
        border-radius: 16px !important;
        font-size: 0.9rem !important;
        font-family: 'DM Sans', sans-serif !important;
        transition: transform 0.3s ease-out, box-shadow 0.3s ease-out !important;
        box-shadow: 5px 5px 10px rgb(163,177,198,0.6),
                    -5px -5px 10px rgba(255,255,255,0.5) !important;
      }
      button[kind="secondary"]:hover {
        transform: translateY(-1px) !important;
        box-shadow: 8px 8px 14px rgb(163,177,198,0.7),
                    -8px -8px 14px rgba(255,255,255,0.6) !important;
      }
      button[kind="secondary"]:active {
        transform: translateY(0.5px) !important;
        box-shadow: inset 3px 3px 6px rgb(163,177,198,0.6),
                    inset -3px -3px 6px rgba(255,255,255,0.5) !important;
      }

      /* ── Platform coverage ──────────────────────────────────── */
      .coverage-wrap {
        margin-top: 1.4rem;
        padding-top: 1.2rem;
      }
      .coverage-label {
        font-size: 0.6rem;
        color: #6B7280;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-bottom: 10px;
        font-weight: 700;
      }
      .coverage-item {
        display: flex;
        align-items: center;
        gap: 10px;
        font-size: 0.75rem;
        color: #6B7280;
        margin-bottom: 7px;
        line-height: 1.4;
      }
      .coverage-dot {
        width: 22px;
        height: 22px;
        border-radius: 50%;
        background: #E0E5EC;
        flex-shrink: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: inset 2px 2px 4px rgb(163,177,198,0.6),
                    inset -2px -2px 4px rgba(255,255,255,0.5);
      }
      .coverage-dot::after {
        content: '';
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: #6C63FF;
        display: block;
      }

      /* ── OTP instruction block ──────────────────────────────── */
      .otp-instruction {
        background: #E0E5EC;
        border-radius: 16px;
        padding: 14px 17px;
        font-size: 0.8rem;
        color: #6B7280;
        line-height: 1.85;
        margin: 1rem 0;
        box-shadow: inset 6px 6px 10px rgb(163,177,198,0.6),
                    inset -6px -6px 10px rgba(255,255,255,0.5);
      }
      .otp-instruction strong { color: #3D4852; font-weight: 700; }

      /* ── Streamlit alerts ───────────────────────────────────── */
      div[data-testid="stAlert"] {
        background: #E0E5EC !important;
        border: none !important;
        border-radius: 14px !important;
        box-shadow: inset 4px 4px 8px rgb(163,177,198,0.5),
                    inset -4px -4px 8px rgba(255,255,255,0.4) !important;
      }

      /* ── QR code image container ────────────────────────────── */
      [data-testid="stImage"] img {
        border-radius: 16px !important;
        box-shadow: 6px 6px 12px rgb(163,177,198,0.6),
                    -6px -6px 12px rgba(255,255,255,0.5) !important;
      }

      /* ── Footer ─────────────────────────────────────────────── */
      .lp-footer {
        text-align: center;
        margin-top: 2.5rem;
        font-size: 0.67rem;
        color: #A0AEC0;
        padding-bottom: 1rem;
        letter-spacing: 0.5px;
      }
    </style>
    """, unsafe_allow_html=True)

    # ── Two-column layout ─────────────────────────────────────
    left_col, right_col = st.columns([11, 8])

    # ══════════════════════════════════════════════════════════
    # LEFT — Hero
    # ══════════════════════════════════════════════════════════
    with left_col:
        st.markdown("""
        <div class="hero-panel">

          <div class="hero-logo">Supply<span>Shield</span></div>
          <div class="hero-tagline">Real-Time Supply Chain Risk Intelligence</div>
          <div class="hero-divider"></div>
          <div class="hero-headline">
            Know your supplier risk<br>before it becomes your crisis.
          </div>
          <div class="hero-sub">
            A multi-agent AI system that screens every supplier against OFAC sanctions,
            geopolitical risk, and adverse news — delivering a complete risk verdict
            in under 10 seconds.
          </div>

          <!-- 2×2 stat grid -->
          <div class="stats-grid">
            <div class="stat-card">
              <div class="stat-card-value">$210B</div>
              <div class="stat-card-label">Lost in the 2021 semiconductor supply shock</div>
            </div>
            <div class="stat-card">
              <div class="stat-card-value">85%</div>
              <div class="stat-card-label">Fortune 500 with no real-time Tier-2 visibility</div>
            </div>
            <div class="stat-card">
              <div class="stat-card-value">$1–3M</div>
              <div class="stat-card-label">Avg. OFAC fine for one missed sanctions update</div>
            </div>
            <div class="stat-card">
              <div class="stat-card-value">&lt;10s</div>
              <div class="stat-card-label">Full 5-agent risk verdict, start to finish</div>
            </div>
          </div>

          <!-- 2×2 value prop grid -->
          <div class="vp-grid">
            <div class="vp-item">
              <div class="vp-icon">🎯</div>
              <div class="vp-text">
                <strong>Zero-hallucination risk scores</strong>
                <small>Deterministic algorithm only — no LLM touches the numbers.
                Full mathematical traceability on every score.</small>
              </div>
            </div>
            <div class="vp-item">
              <div class="vp-icon">🛡️</div>
              <div class="vp-text">
                <strong>18,708 OFAC entities, fuzzy-matched</strong>
                <small>Catches aliases and transliterations that exact-match
                tools miss — before a single PO is placed.</small>
              </div>
            </div>
            <div class="vp-item">
              <div class="vp-icon">🤖</div>
              <div class="vp-text">
                <strong>AI mitigation with live web search</strong>
                <small>Qwen-72B + Serper generates context-aware actions
                with cited sources, within 30 days and 18 months.</small>
              </div>
            </div>
            <div class="vp-item">
              <div class="vp-icon">📊</div>
              <div class="vp-text">
                <strong>Portfolio-level visibility</strong>
                <small>Track score trends, detect deteriorating suppliers,
                and export audit-ready PDF reports.</small>
              </div>
            </div>
          </div>

        </div>
        """, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════
    # RIGHT — Form
    # ══════════════════════════════════════════════════════════
    with right_col:
        if "auth_step" not in st.session_state:
            st.session_state["auth_step"] = 1
        if "auth_user_verified" not in st.session_state:
            st.session_state["auth_user_verified"] = False

        # ── Step 1 — Credentials ──────────────────────────────
        if st.session_state["auth_step"] == 1:
            st.markdown("""
            <div class="form-panel">
              <div class="step-badge">Step 1 of 2</div>
              <div class="form-title">Sign In</div>
              <div class="form-sub">
                Enter your credentials to access the platform.
              </div>
            </div>
            """, unsafe_allow_html=True)

            username = st.text_input("Username", placeholder="Enter username")
            password = st.text_input("Password", type="password",
                                     placeholder="Enter password")

            if st.button("Continue →", type="primary", use_container_width=True):
                if verify_password(username, password):
                    st.session_state["auth_user_verified"] = True
                    st.session_state["auth_step"] = 2
                    st.rerun()
                else:
                    st.error("Invalid username or password.")

            st.markdown("""
            <div class="coverage-wrap">
              <div class="coverage-label">Platform coverage</div>
              <div class="coverage-item">
                <div class="coverage-dot"></div>
                OFAC SDN list &mdash; 18,708 entities, fuzzy-matched
              </div>
              <div class="coverage-item">
                <div class="coverage-dot"></div>
                60+ countries with calibrated geopolitical risk scores
              </div>
              <div class="coverage-item">
                <div class="coverage-dot"></div>
                Live adverse news &mdash; 13 risk terms monitored
              </div>
              <div class="coverage-item">
                <div class="coverage-dot"></div>
                8-factor scoring model for onboarded suppliers
              </div>
            </div>
            """, unsafe_allow_html=True)

        # ── Step 2 — OTP ──────────────────────────────────────
        elif st.session_state["auth_step"] == 2:
            if not is_totp_confirmed():
                st.markdown("""
                <div class="form-panel">
                  <div class="step-badge">Step 2 of 2 &mdash; First Time Setup</div>
                  <div class="form-title">Set Up Authenticator</div>
                  <div class="form-sub">
                    Scan the QR code with Google Authenticator or any TOTP app.
                    You only do this once.
                  </div>
                </div>
                """, unsafe_allow_html=True)
                _, col2, _ = st.columns([1, 2, 1])
                with col2:
                    qr_bytes = generate_qr_code()
                    st.image(qr_bytes, width=200,
                             caption="Scan with Google Authenticator")
            else:
                st.markdown("""
                <div class="form-panel">
                  <div class="step-badge">Step 2 of 2</div>
                  <div class="form-title">Two-Factor Authentication</div>
                  <div class="form-sub">
                    Enter the 6-digit code from your authenticator app.
                  </div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("""
            <div class="otp-instruction">
              1. Open Google Authenticator<br>
              2. Tap <strong>+</strong> &rarr; Scan QR code (first time only)<br>
              3. Enter the 6-digit code shown in the app
            </div>
            """, unsafe_allow_html=True)

            otp_code = st.text_input("Authentication Code",
                                      placeholder="000000", max_chars=6)

            col_back, col_verify = st.columns(2)
            with col_back:
                if st.button("← Back", use_container_width=True):
                    st.session_state["auth_step"] = 1
                    st.session_state["auth_user_verified"] = False
                    st.rerun()
            with col_verify:
                if st.button("Verify →", type="primary",
                              use_container_width=True):
                    if len(otp_code) != 6 or not otp_code.isdigit():
                        st.error("Enter a valid 6-digit code.")
                    elif verify_otp(otp_code):
                        if not is_totp_confirmed():
                            mark_totp_confirmed()
                        st.session_state["authenticated"] = True
                        st.session_state["auth_step"] = 1
                        st.rerun()
                    else:
                        st.error("Invalid code. Try again.")

    # ── Footer ────────────────────────────────────────────────
    st.markdown("""
    <div class="lp-footer">
      SupplyShield &nbsp;&middot;&nbsp; Microsoft AI Unlocked Hackathon
      &nbsp;&middot;&nbsp; IIT Roorkee &nbsp;&middot;&nbsp; Track 4
    </div>
    """, unsafe_allow_html=True)
