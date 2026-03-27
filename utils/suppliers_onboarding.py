import streamlit as st
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime, date
import os

DB_PATH = Path(os.getenv("DB_PATH",
               r"C:\Users\KAVISH\supplyshield_final\data\suppliers.db"))

CRITICALITY_OPTIONS = [
    "Critical — production stops without this supplier",
    "High — significant disruption if unavailable",
    "Medium — manageable with workarounds",
    "Low — easily replaceable",
]

TIER_OPTIONS = ["Tier 1", "Tier 2", "Tier 3"]

FINANCIAL_HEALTH_OPTIONS = ["Good", "Fair", "Poor"]

SUPPLY_CATEGORIES = [
    "Raw Materials",
    "Components & Parts",
    "Finished Goods",
    "Packaging",
    "Chemicals & Compounds",
    "Textiles & Fabrics",
    "Electronics & Semiconductors",
    "Machinery & Equipment",
    "Logistics & Shipping",
    "Software & Technology",
    "Professional Services",
    "Other",
]

def get_onboarded_suppliers() -> pd.DataFrame:
    try:
        conn = sqlite3.connect(DB_PATH)
        df   = pd.read_sql_query(
            "SELECT * FROM onboarded_suppliers ORDER BY criticality, name",
            conn,
        )
        conn.close()
        return df
    except:
        return pd.DataFrame()

def get_supplier_by_name(name: str) -> dict:
    """Check if a supplier exists in onboarded database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        row  = conn.execute(
            "SELECT * FROM onboarded_suppliers WHERE UPPER(name) = UPPER(?)",
            (name,),
        ).fetchone()
        conn.close()
        return dict(row) if row else {}
    except:
        return {}

def save_onboarded_supplier(data: dict) -> bool:
    try:
        conn     = sqlite3.connect(DB_PATH)
        existing = conn.execute(
            "SELECT id FROM onboarded_suppliers WHERE UPPER(name) = UPPER(?)",
            (data["name"],),
        ).fetchone()

        if existing:
            conn.execute("""
                UPDATE onboarded_suppliers SET
                    country               = ?,
                    what_they_supply      = ?,
                    criticality           = ?,
                    annual_spend_usd      = ?,
                    spend_percentage      = ?,
                    contract_expiry       = ?,
                    category              = ?,
                    notes                 = ?,
                    tier_level            = ?,
                    sole_source           = ?,
                    on_time_delivery_rate = ?,
                    years_in_relationship = ?,
                    financial_health      = ?,
                    updated_at            = datetime('now')
                WHERE id = ?
            """, (
                data["country"],
                data["what_they_supply"],
                data["criticality"],
                data.get("annual_spend_usd"),
                data.get("spend_percentage"),
                data.get("contract_expiry"),
                data.get("category"),
                data.get("notes"),
                data.get("tier_level"),
                int(data.get("sole_source", False)),
                data.get("on_time_delivery_rate"),
                data.get("years_in_relationship"),
                data.get("financial_health"),
                existing[0],
            ))
        else:
            conn.execute("""
                INSERT INTO onboarded_suppliers (
                    name, country, what_they_supply, criticality,
                    annual_spend_usd, spend_percentage,
                    contract_expiry, category, notes,
                    tier_level, sole_source, on_time_delivery_rate,
                    years_in_relationship, financial_health
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                data["name"],
                data["country"],
                data["what_they_supply"],
                data["criticality"],
                data.get("annual_spend_usd"),
                data.get("spend_percentage"),
                data.get("contract_expiry"),
                data.get("category"),
                data.get("notes"),
                data.get("tier_level"),
                int(data.get("sole_source", False)),
                data.get("on_time_delivery_rate"),
                data.get("years_in_relationship"),
                data.get("financial_health"),
            ))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Save failed: {e}")
        return False

def delete_onboarded_supplier(supplier_id: int):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM onboarded_suppliers WHERE id = ?", (supplier_id,))
    conn.commit()
    conn.close()

def get_personalized_risk_adjustments(supplier_name: str) -> dict:
    """
    Returns risk adjustments based on onboarded supplier data.
    Used by the orchestrator to personalize risk scoring.
    """
    supplier = get_supplier_by_name(supplier_name)
    if not supplier:
        return {"is_onboarded": False}

    adjustments = {"is_onboarded": True}

    # Criticality adjustment
    criticality = supplier.get("criticality", "")
    if "Critical" in criticality:
        adjustments["criticality_multiplier"] = 1.3
        adjustments["criticality_label"]      = "Critical Supplier"
    elif "High" in criticality:
        adjustments["criticality_multiplier"] = 1.15
        adjustments["criticality_label"]      = "High Criticality"
    else:
        adjustments["criticality_multiplier"] = 1.0
        adjustments["criticality_label"]      = "Standard"

    # Spend concentration adjustment
    spend_pct = supplier.get("spend_percentage")
    if spend_pct:
        if spend_pct >= 40:
            adjustments["single_source_override"] = True
            adjustments["spend_note"] = f"{spend_pct:.0f}% of budget"
        elif spend_pct >= 25:
            adjustments["spend_note"] = f"{spend_pct:.0f}% of budget — moderate concentration"

    # Contract expiry adjustment
    expiry = supplier.get("contract_expiry")
    if expiry:
        try:
            expiry_date = datetime.strptime(expiry, "%Y-%m-%d").date()
            days_left   = (expiry_date - date.today()).days
            if days_left <= 30:
                adjustments["contract_urgency"] = "CRITICAL"
                adjustments["contract_note"]    = f"Contract expires in {days_left} days"
            elif days_left <= 90:
                adjustments["contract_urgency"] = "HIGH"
                adjustments["contract_note"]    = f"Contract expires in {days_left} days"
            elif days_left <= 180:
                adjustments["contract_urgency"] = "MEDIUM"
                adjustments["contract_note"]    = f"Contract expires in {days_left} days"
        except:
            pass

    adjustments["what_they_supply"]      = supplier.get("what_they_supply", "")
    adjustments["annual_spend_usd"]      = supplier.get("annual_spend_usd")
    adjustments["tier_level"]            = supplier.get("tier_level")
    adjustments["sole_source_onboarded"] = bool(supplier.get("sole_source", 0))
    adjustments["on_time_delivery_rate"] = supplier.get("on_time_delivery_rate")
    adjustments["years_in_relationship"] = supplier.get("years_in_relationship")
    adjustments["financial_health"]      = supplier.get("financial_health")
    adjustments["contract_expiry"]       = supplier.get("contract_expiry")
    adjustments["supplier_data"]         = dict(supplier)

    return adjustments
import io

def process_excel_upload(file_bytes: bytes) -> dict:
    """Parse uploaded Excel file and save suppliers to database."""
    try:
        def _norm_col(c):
            # Normalize Excel header names into the keys used by the app.
            # Keep '%' because the app expects columns like 'spend_%_of_total_budget'.
            if c is None or (isinstance(c, float) and pd.isna(c)):
                return ""
            s = str(c).strip().lower()
            if not s:
                return ""
            s = s.replace(" ", "_").replace("(", "").replace(")", "")
            # Remove common punctuation/symbol noise from headers (but keep '_', '%' and letters/numbers).
            # Example: "Criticality Level" -> "criticality_level"
            cleaned = []
            for ch in s:
                if ch.isalnum() or ch in {"_", "%"}:
                    cleaned.append(ch)
            return "".join(cleaned)

        # Some templates include title rows above the real header row.
        # Read without headers first, then locate a row that contains the required column names.
        df_raw = pd.read_excel(io.BytesIO(file_bytes), header=None)
        required = {"supplier_name", "country", "what_they_supply", "criticality_level"}

        header_row = None
        search_rows = min(10, len(df_raw))
        for i in range(search_rows):
            row_cells = df_raw.iloc[i].tolist()
            normalized_cells = {_norm_col(cell) for cell in row_cells if _norm_col(cell)}
            if required.issubset(normalized_cells):
                header_row = i
                break

        if header_row is None:
            # Fall back to "normal" Excel behavior (first row as header).
            df = pd.read_excel(io.BytesIO(file_bytes))
            df.columns = [_norm_col(c) for c in df.columns]
        else:
            # Use located header row; data starts right after it.
            header_cells = df_raw.iloc[header_row].tolist()
            cols = []
            for idx, cell in enumerate(header_cells):
                name = _norm_col(cell)
                cols.append(name if name else f"unnamed_{idx}")
            df = df_raw.iloc[header_row + 1 :].copy()
            df.columns = cols

        missing  = required - set(df.columns)
        if missing:
            return {"success": False, "error": f"Missing columns: {missing}"}

        saved  = 0
        errors = []

        for _, row in df.iterrows():
            try:
                name = str(row.get("supplier_name", "")).strip()
                if not name or name.lower() == "nan":
                    continue

                # Parse spend percentage — stored as decimal in Excel
                spend_pct = row.get("spend_%_of_total_budget") or row.get("spend_percentage")
                if spend_pct and float(spend_pct) <= 1.0:
                    spend_pct = float(spend_pct) * 100

                # Parse contract expiry
                expiry = row.get("contract_expiry_date") or row.get("contract_expiry")
                if pd.notna(expiry) and expiry:
                    try:
                        expiry = pd.to_datetime(expiry).strftime("%Y-%m-%d")
                    except:
                        expiry = None
                else:
                    expiry = None

                # Parse annual spend
                spend_usd = row.get("annual_spend_usd")
                if pd.notna(spend_usd) and spend_usd:
                    spend_usd = float(str(spend_usd).replace("$", "").replace(",", ""))
                else:
                    spend_usd = None

                save_onboarded_supplier({
                    "name":             name,
                    "country":          str(row.get("country", "")).strip().upper(),
                    "what_they_supply": str(row.get("what_they_supply", "")).strip(),
                    "criticality":      str(row.get("criticality_level", "Medium")).strip(),
                    "annual_spend_usd": spend_usd,
                    "spend_percentage": float(spend_pct) if spend_pct and pd.notna(spend_pct) else None,
                    "contract_expiry":  expiry,
                    "category":         str(row.get("supply_category", "Other")).strip() if pd.notna(row.get("supply_category", "")) else "Other",
                    "notes":            str(row.get("notes", "")).strip() if pd.notna(row.get("notes", "")) else None,
                })
                saved += 1

            except Exception as e:
                errors.append(f"Row {_ + 4}: {str(e)}")

        return {
            "success": True,
            "saved":   saved,
            "errors":  errors,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}    