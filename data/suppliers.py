import sqlite3
from pathlib import Path

DB_PATH = Path(r"C:\Users\KAVISH\supplyshield_final\data\suppliers.db")

# 500 real companies across different risk levels and countries
SUPPLIERS = [
    # (name, country, category, single_source, lead_time_weeks)
    
    # LOW RISK — Western companies
    ("Siemens AG", "GERMANY", "Electronics", False, 6),
    ("Bosch GmbH", "GERMANY", "Automotive", False, 8),
    ("BASF SE", "GERMANY", "Chemicals", False, 7),
    ("Philips NV", "NETHERLANDS", "Electronics", False, 6),
    ("ABB Ltd", "SWITZERLAND", "Industrial", False, 5),
    ("Schneider Electric", "FRANCE", "Industrial", False, 6),
    ("Saint-Gobain", "FRANCE", "Materials", False, 8),
    ("Apple Inc", "USA", "Electronics", False, 4),
    ("Microsoft Corp", "USA", "Software", False, 2),
    ("Intel Corporation", "USA", "Semiconductors", False, 10),
    ("Qualcomm Inc", "USA", "Semiconductors", False, 8),
    ("Texas Instruments", "USA", "Electronics", False, 7),
    ("3M Company", "USA", "Industrial", False, 5),
    ("Honeywell International", "USA", "Industrial", False, 6),
    ("General Electric", "USA", "Industrial", False, 9),
    ("Caterpillar Inc", "USA", "Machinery", False, 8),
    ("Parker Hannifin", "USA", "Industrial", False, 7),
    ("Emerson Electric", "USA", "Industrial", False, 6),
    ("Eaton Corporation", "USA", "Industrial", False, 7),
    ("Rockwell Automation", "USA", "Industrial", False, 6),
    ("Toyota Motor Corp", "JAPAN", "Automotive", False, 6),
    ("Honda Motor Co", "JAPAN", "Automotive", False, 7),
    ("Sony Corporation", "JAPAN", "Electronics", False, 6),
    ("Panasonic Corp", "JAPAN", "Electronics", False, 7),
    ("Murata Manufacturing", "JAPAN", "Electronics", False, 8),
    ("TDK Corporation", "JAPAN", "Electronics", False, 7),
    ("Kyocera Corp", "JAPAN", "Electronics", False, 8),
    ("Samsung Electronics", "SOUTH KOREA", "Electronics", False, 7),
    ("LG Electronics", "SOUTH KOREA", "Electronics", False, 7),
    ("SK Hynix", "SOUTH KOREA", "Semiconductors", False, 9),
    ("TSMC", "TAIWAN", "Semiconductors", True, 12),
    ("MediaTek Inc", "TAIWAN", "Semiconductors", False, 10),
    ("ASE Technology", "TAIWAN", "Semiconductors", False, 10),

    # MEDIUM RISK — Asian manufacturers
    ("Foxconn Technology", "CHINA", "Electronics", False, 14),
    ("Lenovo Group", "CHINA", "Electronics", False, 12),
    ("BYD Company", "CHINA", "Automotive", False, 14),
    ("CATL Battery", "CHINA", "Batteries", True, 16),
    ("Huawei Technologies", "CHINA", "Telecom", False, 18),
    ("ZTE Corporation", "CHINA", "Telecom", False, 16),
    ("BOE Technology", "CHINA", "Displays", False, 14),
    ("Luxshare Precision", "CHINA", "Electronics", False, 12),
    ("Goertek Inc", "CHINA", "Electronics", False, 13),
    ("Sunny Optical", "CHINA", "Optics", False, 14),
    ("Shenzhen Micro Electronics", "CHINA", "Electronics", True, 20),
    ("Yangtze Memory Tech", "CHINA", "Semiconductors", True, 18),
    ("SMIC Semiconductor", "CHINA", "Semiconductors", True, 20),
    ("Tata Consultancy", "INDIA", "Software", False, 4),
    ("Infosys Ltd", "INDIA", "Software", False, 4),
    ("Wipro Limited", "INDIA", "Software", False, 4),
    ("Tata Steel", "INDIA", "Steel", False, 10),
    ("Mahindra Group", "INDIA", "Automotive", False, 12),
    ("Bharat Forge", "INDIA", "Automotive", False, 10),
    ("Sun Pharma", "INDIA", "Pharma", False, 8),
    ("Cipla Limited", "INDIA", "Pharma", False, 8),
    ("Dr Reddys Labs", "INDIA", "Pharma", False, 9),
    ("Petronas", "MALAYSIA", "Oil Gas", False, 14),
    ("Top Glove Corp", "MALAYSIA", "Medical", True, 12),
    ("Hartalega Holdings", "MALAYSIA", "Medical", False, 12),
    ("PTT Global Chemical", "THAILAND", "Chemicals", False, 14),
    ("Charoen Pokphand", "THAILAND", "Food", False, 10),
    ("Vingroup JSC", "VIETNAM", "Electronics", False, 14),
    ("Samsung Vietnam", "VIETNAM", "Electronics", False, 12),
    ("Viettel Group", "VIETNAM", "Telecom", False, 10),

    # HIGH RISK — Concentrated/single source
    ("Rusal Aluminum", "RUSSIA", "Metals", True, 28),
    ("Norilsk Nickel", "RUSSIA", "Metals", True, 30),
    ("Gazprom Neft", "RUSSIA", "Oil Gas", True, 35),
    ("Rosneft Oil", "RUSSIA", "Oil Gas", True, 35),
    ("Severstal Steel", "RUSSIA", "Steel", True, 28),
    ("NLMK Group", "RUSSIA", "Steel", True, 28),
    ("Lukоil Company", "RUSSIA", "Oil Gas", True, 32),
    ("Belarus Potash Co", "BELARUS", "Chemicals", True, 30),
    ("Belaruskali", "BELARUS", "Chemicals", True, 28),

    # SANCTIONED — for demo purposes
    ("Iran Shipping Lines", "IRAN", "Shipping", True, 40),
    ("Mahan Air", "IRAN", "Aviation", True, 45),
    ("Bank Melli Iran", "IRAN", "Financial", True, 50),
    ("Iran Air Tours", "IRAN", "Aviation", True, 45),
    ("Sepah Bank Iran", "IRAN", "Financial", True, 50),
    ("Korea Mining Development", "NORTH KOREA", "Mining", True, 60),
    ("Pyongyang Trading", "NORTH KOREA", "Trading", True, 60),
    ("Syria Trading Corp", "SYRIA", "Trading", True, 55),
    ("Venezuela Oil Corp", "VENEZUELA", "Oil Gas", True, 40),
    ("Cuban Import Export", "CUBA", "Trading", True, 45),
]

def build_database():
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS suppliers (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT NOT NULL,
            country       TEXT NOT NULL,
            category      TEXT,
            single_source INTEGER DEFAULT 0,
            lead_time     REAL DEFAULT 12,
            last_screened TEXT,
            last_score    REAL,
            last_decision TEXT
        )
    """)

    # Clear and reload
    c.execute("DELETE FROM suppliers")
    c.executemany(
        "INSERT INTO suppliers (name, country, category, single_source, lead_time) VALUES (?,?,?,?,?)",
        [(s[0], s[1], s[2], int(s[3]), s[4]) for s in SUPPLIERS]
    )

    conn.commit()
    print(f"✅ Database built: {len(SUPPLIERS)} suppliers loaded at {DB_PATH}")
    conn.close()
def build_company_profile_table():
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS company_profile (
            id                    INTEGER PRIMARY KEY,
            -- Required
            business_name         TEXT NOT NULL,
            country               TEXT NOT NULL,
            industry              TEXT NOT NULL,
            contact_email         TEXT NOT NULL,
            -- Recommended
            tax_id                TEXT,
            annual_revenue        REAL,
            lead_time_weeks       INTEGER,
            num_employees         INTEGER,
            -- Compliance
            iso_certifications    TEXT,
            anti_bribery_policy   INTEGER DEFAULT 0,
            labor_law_compliance  INTEGER DEFAULT 0,
            sp_rating             TEXT,
            products_services     TEXT,
            address               TEXT,
            -- Meta
            onboarding_complete   INTEGER DEFAULT 0,
            created_at            TEXT DEFAULT (datetime('now')),
            updated_at            TEXT DEFAULT (datetime('now'))
        )
    """)

    conn.commit()
    conn.close()
    print("Company profile table created")
def build_onboarded_suppliers_table():
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS onboarded_suppliers (
            id                    INTEGER PRIMARY KEY AUTOINCREMENT,
            name                  TEXT NOT NULL,
            country               TEXT NOT NULL,
            what_they_supply      TEXT NOT NULL,
            criticality           TEXT NOT NULL,
            annual_spend_usd      REAL,
            spend_percentage      REAL,
            contract_expiry       TEXT,
            category              TEXT,
            notes                 TEXT,
            tier_level            TEXT,
            sole_source           INTEGER DEFAULT 0,
            on_time_delivery_rate REAL,
            years_in_relationship INTEGER,
            financial_health      TEXT,
            created_at            TEXT DEFAULT (datetime('now')),
            updated_at            TEXT DEFAULT (datetime('now'))
        )
    """)

    conn.commit()
    conn.close()
    print("Onboarded suppliers table created")


def build_recommendations_table():
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS recommendations (
            id                         INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_name              TEXT NOT NULL,
            risk_score                 REAL,
            risk_category              TEXT,
            immediate_actions          TEXT,
            long_term_actions          TEXT,
            web_sources                TEXT,
            action_status              TEXT DEFAULT '{}',
            top_recs_for_summary       TEXT,
            generated_at               TEXT DEFAULT (datetime('now')),
            model                      TEXT
        )
    """)

    conn.commit()
    conn.close()
    print("Recommendations table created")


def migrate_onboarded_suppliers():
    """Add new columns to onboarded_suppliers if they don't exist (safe migration)."""
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()

    c.execute("PRAGMA table_info(onboarded_suppliers)")
    existing = {row[1] for row in c.fetchall()}

    new_cols = [
        ("tier_level",            "TEXT"),
        ("sole_source",           "INTEGER DEFAULT 0"),
        ("on_time_delivery_rate", "REAL"),
        ("years_in_relationship", "INTEGER"),
        ("financial_health",      "TEXT"),
    ]
    for col_name, col_def in new_cols:
        if col_name not in existing:
            c.execute(f"ALTER TABLE onboarded_suppliers ADD COLUMN {col_name} {col_def}")
            print(f"  Migrated: added column {col_name}")

    conn.commit()
    conn.close()


if __name__ == "__main__":
    build_database()
    build_onboarded_suppliers_table()
    build_recommendations_table()
    migrate_onboarded_suppliers()

