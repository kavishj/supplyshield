"""
SupplyShield — Demo Seed Script
================================
Run this ONCE before recording the demo video.
It creates the admin company profile and 6 onboarded suppliers
that cover every risk outcome in the system.

Usage:
    python seed_demo_data.py
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(r"C:\Users\KAVISH\supplyshield_final\data\suppliers.db")

# ── Company Profile ────────────────────────────────────────────────────────────
COMPANY_PROFILE = {
    "id":                   1,
    "business_name":        "NexaCore Systems Inc.",
    "country":              "UNITED STATES",
    "industry":             "Defense Electronics & Industrial Automation",
    "contact_email":        "procurement@nexacore-systems.com",
    "tax_id":               "47-3891024",
    "annual_revenue":       450_000_000,
    "lead_time_weeks":      10,
    "num_employees":        1840,
    "iso_certifications":   "ISO 9001:2015, AS9100D, IPC-A-610 Class 3",
    "anti_bribery_policy":  1,
    "labor_law_compliance": 1,
    "sp_rating":            "BB+",
    "products_services":    (
        "PCB assemblies, power conversion modules, and electronic control units "
        "for defense contractors, medical imaging, and industrial automation OEMs"
    ),
    "address":              "4200 Research Blvd, Suite 300, Austin, TX 78759, USA",
    "onboarding_complete":  1,
}

# ── Onboarded Suppliers ────────────────────────────────────────────────────────
# Expected outcomes when running analysis:
#
#  1. TexBoard Solutions LLC        → LOW    → AUTO_APPROVED
#  2. Murata Electronics NA         → LOW    → AUTO_APPROVED
#  3. Shenzhen Genco PCB Co.        → MEDIUM → AUTO_APPROVED  (risk flagged, not blocked)
#  4. Huawei Technologies           → HIGH   → REQUIRES_APPROVAL  ← run SINGLE analysis (see note)
#  5. Iran Electronics Industries   → BLOCKED (Direct OFAC SDN match)
#  6. Renova Industrial Solutions   → BLOCKED (OFAC 50% Rule — Vekselberg)  ← test before demo
#
# NOTE for supplier #4 (Huawei):
#   Run via SINGLE analysis mode. Enter these extended parameters in the form:
#     Financial Health  → Poor
#     On-Time Delivery  → 65%
#     Lead Time (weeks) → 28
#     Sole Source       → Yes
#     Contract Expiry   → 2026-04-16
#   This guarantees score ≈ 0.756 (HIGH) → REQUIRES_APPROVAL, regardless of news.
#   Huawei also always returns HIGH news risk (sanctions/trade war coverage).
#
# NOTE for supplier #6 (Renova):
#   The OFAC 50% rule check is a LIVE web search + LLM extraction.
#   TEST THIS BEFORE THE DEMO. Expected: web search finds Viktor Vekselberg (~70% owner)
#   who is on the OFAC SDN list → cumulative OFAC stake ≥ 50% → BLOCKED.
#   If it returns MANUAL_REVIEW instead, run the single analysis again (LLM calls can vary).

SUPPLIERS = [
    # ── 1. AUTO-APPROVED / LOW ─────────────────────────────────────────────────
    {
        "name":                  "TexBoard Solutions LLC",
        "country":               "UNITED STATES",
        "what_they_supply":      "Standard FR-4 double-sided PCBs and prototype boards for non-critical sub-assemblies",
        "criticality":           "Medium",
        "annual_spend_usd":      1_200_000,
        "spend_percentage":      11.6,
        "contract_expiry":       "2027-09-30",
        "category":              "PCB Fabrication",
        "notes":                 (
            "Domestic backup PCB vendor. Consistent quality and short lead times. "
            "Used for non-flight, non-safety-critical assemblies. No compliance concerns raised to date."
        ),
        "tier_level":            "Tier 2",
        "sole_source":           0,
        "on_time_delivery_rate": 96.0,
        "years_in_relationship": 5,
        "financial_health":      "Good",
    },
    # ── 2. AUTO-APPROVED / LOW ─────────────────────────────────────────────────
    {
        "name":                  "Murata Electronics North America",
        "country":               "UNITED STATES",
        "what_they_supply":      "MLCC capacitors, EMC filters, and passive electronic components (0402–1210 series)",
        "criticality":           "Critical",
        "annual_spend_usd":      3_200_000,
        "spend_percentage":      30.9,
        "contract_expiry":       "2028-06-30",
        "category":              "Electronic Components",
        "notes":                 (
            "Primary Tier 1 passive component partner. Dual-qualified alongside TDK as "
            "secondary source. Long-standing relationship with dedicated account manager. "
            "No supply chain or compliance concerns. Preferred supplier for all MLCC ≥0402."
        ),
        "tier_level":            "Tier 1",
        "sole_source":           0,
        "on_time_delivery_rate": 97.0,
        "years_in_relationship": 11,
        "financial_health":      "Good",
    },
    # ── 3. MEDIUM RISK / AUTO-APPROVED (risk flagged, not blocked) ─────────────
    {
        "name":                  "Shenzhen Genco PCB Co.",
        "country":               "CHINA",
        "what_they_supply":      "6-layer standard PCBs for industrial motor drive controllers",
        "criticality":           "High",
        "annual_spend_usd":      2_900_000,
        "spend_percentage":      28.0,
        "contract_expiry":       "2026-05-31",
        "category":              "PCB Fabrication",
        "notes":                 (
            "Cost-competitive Chinese PCB vendor. Relationship manager flagged slipping delivery "
            "performance over Q3-Q4 2025. Contract renewal discussions ongoing but not finalised. "
            "Geographic concentration risk in Shenzhen. Seek Malaysia backup qualification."
        ),
        "tier_level":            "Tier 2",
        "sole_source":           0,
        "on_time_delivery_rate": 76.0,
        "years_in_relationship": 3,
        "financial_health":      "Fair",
    },
    # ── 4. HIGH RISK / REQUIRES_APPROVAL ───────────────────────────────────────
    # RUN VIA SINGLE ANALYSIS MODE with extended params (see note at top of file)
    {
        "name":                  "Huawei Technologies Co. Ltd",
        "country":               "CHINA",
        "what_they_supply":      "Custom ASIC chipsets and 5G baseband modules for industrial IoT gateway units",
        "criticality":           "Critical",
        "annual_spend_usd":      1_850_000,
        "spend_percentage":      17.9,
        "contract_expiry":       "2026-04-16",
        "category":              "Semiconductors & ICs",
        "notes":                 (
            "Sole-qualified supplier for NexaCore's IoT gateway ASIC (part #NC-5G-GW-1024). "
            "US Commerce Dept Entity List restrictions have extended lead times significantly. "
            "Contract lapsing — renewal stalled due to legal review of export licence implications. "
            "OTD degraded from 91% (2024) to 65% (2025) due to chip allocation delays. "
            "Payment terms renegotiated unfavourably — financial relationship under strain."
        ),
        "tier_level":            "Tier 1",
        "sole_source":           1,
        "on_time_delivery_rate": 65.0,
        "years_in_relationship": 4,
        "financial_health":      "Poor",
    },
    # ── 5. BLOCKED — DIRECT OFAC SDN MATCH ─────────────────────────────────────
    {
        "name":                  "Iran Electronics Industries",
        "country":               "IRAN",
        "what_they_supply":      "RF subsystem modules and military-grade connectors",
        "criticality":           "High",
        "annual_spend_usd":      480_000,
        "spend_percentage":      4.6,
        "contract_expiry":       "2026-09-30",
        "category":              "RF & Electronic Systems",
        "notes":                 (
            "FLAGGED FOR COMPLIANCE REVIEW. Introduced through a Singapore-based intermediary "
            "('SingTech Distribution Pte Ltd') as a non-disclosed principal. SupplyShield "
            "analysis revealed this is Iran Electronics Industries — a designated entity on "
            "the OFAC SDN list. Procurement engagement HALTED. Legal team notified."
        ),
        "tier_level":            "Tier 2",
        "sole_source":           0,
        "on_time_delivery_rate": 78.0,
        "years_in_relationship": 1,
        "financial_health":      "Fair",
    },
    # ── 6. BLOCKED — OFAC 50% RULE ─────────────────────────────────────────────
    {
        "name":                  "Renova Industrial Solutions",
        "country":               "RUSSIA",
        "what_they_supply":      "Titanium alloy heat sinks and precision-machined enclosures for high-power electronics",
        "criticality":           "Medium",
        "annual_spend_usd":      720_000,
        "spend_percentage":      7.0,
        "contract_expiry":       "2027-03-31",
        "category":              "Mechanical Components",
        "notes":                 (
            "Russian subsidiary of Renova Group. Competitive titanium machining capability. "
            "Relationship initiated through a Hannover Messe referral (2025). "
            "Full beneficial ownership structure verification PENDING. "
            "SupplyShield 50% Rule check flagged Viktor Vekselberg (OFAC SDN) as "
            "majority beneficial owner (~70%). Procurement engagement HALTED."
        ),
        "tier_level":            "Tier 3",
        "sole_source":           0,
        "on_time_delivery_rate": 84.0,
        "years_in_relationship": 1,
        "financial_health":      "Fair",
    },
]


# ── Seed logic ─────────────────────────────────────────────────────────────────

def seed():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # ── Company profile ────────────────────────────────────────────────────────
    conn.execute("DELETE FROM company_profile")
    conn.execute("""
        INSERT INTO company_profile (
            id, business_name, country, industry, contact_email, tax_id,
            annual_revenue, lead_time_weeks, num_employees, iso_certifications,
            anti_bribery_policy, labor_law_compliance, sp_rating,
            products_services, address, onboarding_complete
        ) VALUES (
            :id, :business_name, :country, :industry, :contact_email, :tax_id,
            :annual_revenue, :lead_time_weeks, :num_employees, :iso_certifications,
            :anti_bribery_policy, :labor_law_compliance, :sp_rating,
            :products_services, :address, :onboarding_complete
        )
    """, COMPANY_PROFILE)

    # ── Onboarded suppliers ────────────────────────────────────────────────────
    conn.execute("DELETE FROM onboarded_suppliers")
    for s in SUPPLIERS:
        conn.execute("""
            INSERT INTO onboarded_suppliers (
                name, country, what_they_supply, criticality,
                annual_spend_usd, spend_percentage, contract_expiry,
                category, notes, tier_level, sole_source,
                on_time_delivery_rate, years_in_relationship, financial_health
            ) VALUES (
                :name, :country, :what_they_supply, :criticality,
                :annual_spend_usd, :spend_percentage, :contract_expiry,
                :category, :notes, :tier_level, :sole_source,
                :on_time_delivery_rate, :years_in_relationship, :financial_health
            )
        """, s)

    conn.commit()
    conn.close()

    print("✓ Company profile seeded:  NexaCore Systems Inc.")
    print(f"✓ {len(SUPPLIERS)} suppliers seeded:")
    for s in SUPPLIERS:
        print(f"    • {s['name']:<45} ({s['country']})")
    print()
    print("Next steps:")
    print("  1. Log in → complete onboarding (profile already set)")
    print("  2. Go to My Suppliers — all 6 should appear")
    print("  3. Run analysis as described in the notes above each supplier")


if __name__ == "__main__":
    seed()
