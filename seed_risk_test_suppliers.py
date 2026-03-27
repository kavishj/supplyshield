"""
SupplyShield — Risk Test Supplier Seed Script
=============================================
Inserts 6 suppliers covering MEDIUM and HIGH risk without any OFAC sanctions.
Designed to exercise different risk drivers and recommendation paths.

Run from the project root:
    python seed_risk_test_suppliers.py

─────────────────────────────────────────────────────────────────────────────
IMPORTANT: Lead-time is a FORM SLIDER (not stored in DB).
When analysing each supplier, set the "Lead Time (weeks)" slider to the
value shown in the notes field.  All other risk factors come from the DB.

IMPORTANT: Use financial_health = "Poor" / "Fair" / "Good" (not "Weak").
"Weak"/"Moderate"/"Excellent" fall back to the 0.4 default and won't score
correctly.
─────────────────────────────────────────────────────────────────────────────

SCORE CALCULATOR (today = 2026-03-26, OFAC = 0.0 for all):
──────────────────────────────────────────────────────────────────────────────
 ID  Supplier                       Country    Lead-wk  news=NONE  news=HIGH
──────────────────────────────────────────────────────────────────────────────
 H1  Sibirsk Rare Earth Mining LLC  Russia     20 wk    0.619 MED  0.786 HIGH ✓
 H2  BelChem Industrial Compounds   Belarus    18 wk    0.600 MED  0.766 HIGH ✓
 H3  YangonTech Components Co.      Myanmar    24 wk    0.594 MED  0.760 HIGH ✓
 M1  KarachiTex Fabrics Pvt. Ltd.   Pakistan   20 wk    0.506 MED  0.634 MED ✓
 M2  Shenzhen GoldPeak Electronics  China      16 wk    0.503 MED  0.669 MED ✓
 M3  LagosEnergy Chemical Supplies  Nigeria    24 wk    0.519 MED  0.685 MED ✓
──────────────────────────────────────────────────────────────────────────────

HIGH profiles depend on the live NewsAPI returning adverse headlines.
Russia / Belarus / Myanmar regularly appear in sanctions and supply-chain
disruption news, so HIGH news_risk is the expected outcome.

MEDIUM profiles score MEDIUM even with news=NONE and the default 12-week
lead-time slider, making them safe for deterministic testing.

Risk drivers being tested (for recommendation coverage):
  H1  Geography + Sole-source + Expiring contract  (Russian metals crisis)
  H2  Geography + Financial collapse + Expiring contract (Belarus chemicals)
  H3  Geography + Long lead-time + Sole-source     (Myanmar coup disruption)
  M1  Sole-source + Geography + Poor performance   (Pakistan textiles)
  M2  Sole-source + Expiring contract + Financial  (China electronics)
  M3  Lead-time + Financial health + Geography     (Nigeria oil chemicals)
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(r"C:\Users\KAVISH\supplyshield_final\data\suppliers.db")

TEST_SUPPLIERS = [

    # ── HIGH RISK (no OFAC) ───────────────────────────────────────────────────
    # Primary driver: Geography (Russia 0.95) + Sole-source + Poor financials
    # Recommendation path: geo-diversification + emergency sourcing + legal review
    # Analysis form: set Lead Time = 20 weeks
    {
        "name":                 "Sibirsk Rare Earth Mining LLC",
        "country":              "Russia",
        "what_they_supply":     "Rare earth metals, neodymium and palladium concentrates",
        "criticality":          "Critical",
        "annual_spend_usd":     3_800_000,
        "spend_percentage":     16.8,
        "contract_expiry":      "2026-04-20",   # 25 days → contract_expiry score 0.90
        "category":             "Raw Materials",
        "notes":                (
            "SOLE SOURCE. Critical rare-earth supply with no qualified alternatives. "
            "Geopolitical exposure elevated post-2022. Financial distress signals observed "
            "in Q4 audits. [TEST: set Lead-Time slider to 20 weeks for expected HIGH score]"
        ),
        "tier_level":           "Tier 1",
        "sole_source":          1,
        "on_time_delivery_rate": 64.0,          # <70% → on_time score 0.85
        "years_in_relationship": 4,
        "financial_health":     "Poor",          # 0.85 — must use "Poor" not "Weak"
    },

    # Primary driver: Geography (Belarus 0.90) + Financial collapse + Imminent contract expiry
    # Recommendation path: financial review + emergency contract renewal + alternative qualification
    # Analysis form: set Lead Time = 18 weeks
    {
        "name":                 "BelChem Industrial Compounds JLLC",
        "country":              "Belarus",
        "what_they_supply":     "Industrial solvents, acetone and specialty chemical compounds",
        "criticality":          "Critical",
        "annual_spend_usd":     2_900_000,
        "spend_percentage":     12.9,
        "contract_expiry":      "2026-04-10",   # 15 days → contract_expiry score 0.90
        "category":             "Chemicals & Compounds",
        "notes":                (
            "SOLE SOURCE. Critical solvent supply for manufacturing line 3. "
            "Contract expires in under 30 days — renewal negotiations stalled. "
            "Financial distress confirmed in latest credit report. "
            "[TEST: set Lead-Time slider to 18 weeks for expected HIGH score]"
        ),
        "tier_level":           "Tier 1",
        "sole_source":          1,
        "on_time_delivery_rate": 62.0,          # <70% → on_time score 0.85
        "years_in_relationship": 3,
        "financial_health":     "Poor",
    },

    # Primary driver: Geography (Myanmar 0.80) + Long lead-time + Sole-source
    # Recommendation path: lead-time mitigation + safety stock + alternative region qualification
    # Analysis form: set Lead Time = 24 weeks
    {
        "name":                 "YangonTech Components Co., Ltd.",
        "country":              "Myanmar",
        "what_they_supply":     "Precision electronic components and PCB assemblies",
        "criticality":          "Critical",
        "annual_spend_usd":     2_200_000,
        "spend_percentage":     9.8,
        "contract_expiry":      "2026-04-18",   # 23 days → contract_expiry score 0.90
        "category":             "Electronics & Semiconductors",
        "notes":                (
            "SOLE SOURCE. Component lead times have grown to 20-24 weeks post-2021 coup. "
            "ESG audit flagged forced-labour risks in upstream sub-tiers. "
            "No alternative supplier qualified. "
            "[TEST: set Lead-Time slider to 24 weeks for expected HIGH score]"
        ),
        "tier_level":           "Tier 1",
        "sole_source":          1,
        "on_time_delivery_rate": 62.0,
        "years_in_relationship": 2,
        "financial_health":     "Poor",
    },

    # ── MEDIUM RISK (no OFAC) ─────────────────────────────────────────────────
    # Primary driver: Sole-source + Geography (Pakistan 0.60) + Poor performance
    # Recommendation path: supplier diversification + performance improvement plan
    # Analysis form: set Lead Time = 20 weeks (also scores MEDIUM at default 12 wk)
    {
        "name":                 "KarachiTex Fabrics Pvt. Ltd.",
        "country":              "Pakistan",
        "what_they_supply":     "Woven cotton and synthetic fabric rolls for apparel manufacturing",
        "criticality":          "Critical",
        "annual_spend_usd":     1_750_000,
        "spend_percentage":     7.8,
        "contract_expiry":      "2026-06-09",   # 75 days → contract_expiry score 0.55
        "category":             "Textiles & Fabrics",
        "notes":                (
            "SOLE SOURCE. Only qualified source meeting fabric-grade specifications. "
            "Delivery failures in Q2 2025 due to port congestion in Karachi. "
            "Financial audit shows strained working capital ratio. "
            "[TEST: set Lead-Time to 20 weeks; also scores MEDIUM at default 12 weeks]"
        ),
        "tier_level":           "Tier 1",
        "sole_source":          1,
        "on_time_delivery_rate": 68.0,          # <70% → 0.85
        "years_in_relationship": 5,
        "financial_health":     "Poor",
    },

    # Primary driver: Sole-source + Imminent contract expiry + Financial stress (China 0.55)
    # Recommendation path: contract renewal urgency + dual-source strategy + financial monitoring
    # Analysis form: set Lead Time = 16 weeks (also scores MEDIUM at default 12 wk)
    {
        "name":                 "Shenzhen GoldPeak Electronics Ltd.",
        "country":              "China",
        "what_they_supply":     "Custom PCBA modules, SMT assembly and IC programming services",
        "criticality":          "Critical",
        "annual_spend_usd":     3_100_000,
        "spend_percentage":     13.7,
        "contract_expiry":      "2026-04-20",   # 25 days → contract_expiry score 0.90
        "category":             "Electronics & Semiconductors",
        "notes":                (
            "SOLE SOURCE for custom PCBA. Contract expires in 25 days — renewal terms "
            "not yet agreed. Cash flow deterioration reported after key customer loss. "
            "Geo-concentration risk from China trade policy. "
            "[TEST: set Lead-Time to 16 weeks; also scores MEDIUM at default 12 weeks]"
        ),
        "tier_level":           "Tier 1",
        "sole_source":          1,
        "on_time_delivery_rate": 65.0,          # <70% → 0.85
        "years_in_relationship": 4,
        "financial_health":     "Poor",
    },

    # Primary driver: Long lead-time + Financial health + Geography (Nigeria 0.60)
    # Recommendation path: safety stock increase + financial due diligence + lead-time reduction
    # Analysis form: set Lead Time = 24 weeks (also scores MEDIUM at default 12 wk)
    {
        "name":                 "LagosEnergy Chemical Supplies Ltd.",
        "country":              "Nigeria",
        "what_they_supply":     "Petrochemical feedstocks, lubricants and industrial oils",
        "criticality":          "Critical",
        "annual_spend_usd":     2_450_000,
        "spend_percentage":     10.9,
        "contract_expiry":      "2026-06-19",   # 85 days → contract_expiry score 0.55
        "category":             "Chemicals & Compounds",
        "notes":                (
            "SOLE SOURCE for specialty lubricant grade. Port and customs delays add 6-8 "
            "weeks to nominal lead times. Audited financials show debt-to-equity above "
            "threshold. Currency volatility adding payment risk. "
            "[TEST: set Lead-Time to 24 weeks; also scores MEDIUM at default 12 weeks]"
        ),
        "tier_level":           "Tier 1",
        "sole_source":          1,
        "on_time_delivery_rate": 68.0,
        "years_in_relationship": 3,
        "financial_health":     "Poor",
    },
]


def seed():
    if not DB_PATH.exists():
        print(f"ERROR: Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    inserted = 0
    skipped  = 0

    for s in TEST_SUPPLIERS:
        existing = c.execute(
            "SELECT id FROM onboarded_suppliers WHERE UPPER(name) = UPPER(?)",
            (s["name"],),
        ).fetchone()

        if existing:
            print(f"  SKIP    {s['name']} (already exists, id={existing[0]})")
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
        risk_band = "HIGH" if s["country"] in ("Russia", "Belarus", "Myanmar") else "MEDIUM"
        print(f"  INSERT  {s['name']} ({s['country']}) — expected {risk_band}")
        inserted += 1

    conn.commit()
    conn.close()
    print(f"\nDone. {inserted} inserted, {skipped} skipped.")
    print("\nNext steps:")
    print("  1. Go to 'My Suppliers' → select a supplier → click Analyse")
    print("  2. Set Lead-Time slider to the value shown in each supplier's Notes")
    print("  3. H1/H2/H3: expect HIGH when news API returns adverse headlines")
    print("  4. M1/M2/M3: expect MEDIUM regardless of news or lead-time slider")


if __name__ == "__main__":
    seed()
