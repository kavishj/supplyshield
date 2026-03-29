"""
SupplyShield — Demo Seed Script
================================
Run this ONCE to seed the database with the TexBoard Solutions supplier.

Usage:
    python seed_demo_data.py
"""

import sqlite3, os
from pathlib import Path

_DEFAULT_DB = (
    r"C:\Users\KAVISH\supplyshield_final\data\suppliers.db"
    if os.name == "nt"
    else "/app/data/suppliers.db"
)
DB_PATH = Path(os.getenv("DB_PATH", _DEFAULT_DB))

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
SUPPLIERS = [
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

    print("Company profile seeded:  NexaCore Systems Inc.")
    print(f"{len(SUPPLIERS)} supplier(s) seeded:")
    for s in SUPPLIERS:
        print(f"    - {s['name']} ({s['country']})")
    print()
    print("Next steps:")
    print("  1. Log in -> complete onboarding (profile already set)")
    print("  2. Go to My Suppliers — TexBoard Solutions LLC should appear")


if __name__ == "__main__":
    seed()
