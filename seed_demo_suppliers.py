"""
Demo supplier seeding script for SupplyShield evaluation.
Inserts 10 suppliers: 4 HIGH risk, 4 MEDIUM risk, 2 LOW risk.
None are OFAC-sanctioned — designed for product evaluation and demo.

Run from the project root:
    python seed_demo_suppliers.py
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(r"C:\Users\KAVISH\supplyshield_final\data\suppliers.db")

DEMO_SUPPLIERS = [
    # ── HIGH RISK (geo-concentration, sole-source, weak financials) ──────────
    {
        "name": "SinoTech Electronics Co.",
        "country": "China",
        "what_they_supply": "Semiconductor chips and microcontrollers",
        "criticality": "Critical",
        "annual_spend_usd": 4_200_000,
        "spend_percentage": 18.5,
        "contract_expiry": "2025-09-30",
        "category": "Electronics",
        "notes": "Single-source supplier for our main MCU line. Long lead times observed in Q3.",
        "tier_level": "Tier 1",
        "sole_source": 1,
        "on_time_delivery_rate": 71.0,
        "years_in_relationship": 3,
        "financial_health": "Weak",
    },
    {
        "name": "Volkov Industrial Metals",
        "country": "Russia",
        "what_they_supply": "Titanium alloys and specialty metals",
        "criticality": "Critical",
        "annual_spend_usd": 3_100_000,
        "spend_percentage": 13.7,
        "contract_expiry": "2025-12-31",
        "category": "Raw Materials",
        "notes": "Geopolitical exposure high. Alternative sourcing being evaluated in Q4.",
        "tier_level": "Tier 1",
        "sole_source": 1,
        "on_time_delivery_rate": 65.0,
        "years_in_relationship": 5,
        "financial_health": "Weak",
    },
    {
        "name": "MyanTex Garments Ltd.",
        "country": "Myanmar",
        "what_they_supply": "Textile and apparel manufacturing",
        "criticality": "High",
        "annual_spend_usd": 1_800_000,
        "spend_percentage": 8.0,
        "contract_expiry": "2026-03-31",
        "category": "Manufacturing",
        "notes": "ESG audit flagged labor concerns in 2023. Follow-up audit scheduled.",
        "tier_level": "Tier 2",
        "sole_source": 0,
        "on_time_delivery_rate": 74.0,
        "years_in_relationship": 4,
        "financial_health": "Moderate",
    },
    {
        "name": "Harbin Precision Parts",
        "country": "China",
        "what_they_supply": "CNC machined precision components",
        "criticality": "High",
        "annual_spend_usd": 2_600_000,
        "spend_percentage": 11.5,
        "contract_expiry": "2026-06-30",
        "category": "Manufacturing",
        "notes": "High geo-concentration risk. Regional power shortage events impacted deliveries twice.",
        "tier_level": "Tier 1",
        "sole_source": 0,
        "on_time_delivery_rate": 78.0,
        "years_in_relationship": 6,
        "financial_health": "Moderate",
    },

    # ── MEDIUM RISK ──────────────────────────────────────────────────────────
    {
        "name": "Apex Logistics India Pvt.",
        "country": "India",
        "what_they_supply": "Third-party logistics and warehousing",
        "criticality": "Medium",
        "annual_spend_usd": 950_000,
        "spend_percentage": 4.2,
        "contract_expiry": "2026-09-30",
        "category": "Logistics",
        "notes": "Moderate on-time performance. Port congestion in Chennai affected SLAs in H1.",
        "tier_level": "Tier 2",
        "sole_source": 0,
        "on_time_delivery_rate": 82.0,
        "years_in_relationship": 3,
        "financial_health": "Moderate",
    },
    {
        "name": "TurkChem Specialty Chemicals",
        "country": "Turkey",
        "what_they_supply": "Industrial solvents and chemical compounds",
        "criticality": "High",
        "annual_spend_usd": 1_400_000,
        "spend_percentage": 6.2,
        "contract_expiry": "2026-12-31",
        "category": "Chemicals",
        "notes": "Currency volatility impacting contract pricing. Renegotiation pending.",
        "tier_level": "Tier 2",
        "sole_source": 0,
        "on_time_delivery_rate": 86.0,
        "years_in_relationship": 7,
        "financial_health": "Moderate",
    },
    {
        "name": "BrazilAgro Commodities S.A.",
        "country": "Brazil",
        "what_they_supply": "Agricultural raw materials and soy derivatives",
        "criticality": "Medium",
        "annual_spend_usd": 2_100_000,
        "spend_percentage": 9.3,
        "contract_expiry": "2026-05-31",
        "category": "Raw Materials",
        "notes": "Seasonal supply variability. Weather risk in Q1/Q2 historically caused 10-15% shortfall.",
        "tier_level": "Tier 1",
        "sole_source": 0,
        "on_time_delivery_rate": 84.0,
        "years_in_relationship": 9,
        "financial_health": "Good",
    },
    {
        "name": "PharmaSource Egypt LLC",
        "country": "Egypt",
        "what_they_supply": "Pharmaceutical excipients and API intermediates",
        "criticality": "High",
        "annual_spend_usd": 780_000,
        "spend_percentage": 3.5,
        "contract_expiry": "2025-11-30",
        "category": "Pharmaceuticals",
        "notes": "FX controls in Egypt causing payment delays. Compliance team monitoring.",
        "tier_level": "Tier 2",
        "sole_source": 0,
        "on_time_delivery_rate": 88.0,
        "years_in_relationship": 2,
        "financial_health": "Moderate",
    },

    # ── LOW RISK (for contrast in dashboard) ────────────────────────────────
    {
        "name": "Müller GmbH Precision",
        "country": "Germany",
        "what_they_supply": "Hydraulic actuators and mechanical assemblies",
        "criticality": "Medium",
        "annual_spend_usd": 3_400_000,
        "spend_percentage": 15.1,
        "contract_expiry": "2027-12-31",
        "category": "Industrial Equipment",
        "notes": "Long-term strategic partner. ISO 9001 certified. Consistent on-time delivery.",
        "tier_level": "Tier 1",
        "sole_source": 0,
        "on_time_delivery_rate": 97.0,
        "years_in_relationship": 14,
        "financial_health": "Excellent",
    },
    {
        "name": "NordicPack Solutions AS",
        "country": "Norway",
        "what_they_supply": "Sustainable packaging and recyclable materials",
        "criticality": "Low",
        "annual_spend_usd": 620_000,
        "spend_percentage": 2.7,
        "contract_expiry": "2027-06-30",
        "category": "Packaging",
        "notes": "ESG-compliant. Preferred supplier status. No issues in 8 years.",
        "tier_level": "Tier 2",
        "sole_source": 0,
        "on_time_delivery_rate": 99.0,
        "years_in_relationship": 8,
        "financial_health": "Excellent",
    },
]


def seed():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    inserted = 0
    skipped = 0

    for s in DEMO_SUPPLIERS:
        existing = c.execute(
            "SELECT id FROM onboarded_suppliers WHERE name = ?", (s["name"],)
        ).fetchone()

        if existing:
            print(f"  SKIP  {s['name']} (already exists)")
            skipped += 1
            continue

        c.execute(
            """
            INSERT INTO onboarded_suppliers (
                name, country, what_they_supply, criticality,
                annual_spend_usd, spend_percentage, contract_expiry,
                category, notes, tier_level, sole_source,
                on_time_delivery_rate, years_in_relationship, financial_health
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                s["name"], s["country"], s["what_they_supply"], s["criticality"],
                s["annual_spend_usd"], s["spend_percentage"], s["contract_expiry"],
                s["category"], s["notes"], s["tier_level"], s["sole_source"],
                s["on_time_delivery_rate"], s["years_in_relationship"], s["financial_health"],
            ),
        )
        print(f"  INSERT {s['name']} ({s['country']})")
        inserted += 1

    conn.commit()
    conn.close()
    print(f"\nDone. {inserted} inserted, {skipped} skipped (already existed).")


if __name__ == "__main__":
    seed()
