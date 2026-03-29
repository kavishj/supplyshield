"""
Run this script once to generate the supplier Excel:
    python generate_supplier_excel.py
Output: data/NexaCore_Suppliers_Demo.xlsx
"""

from pathlib import Path
import openpyxl
from openpyxl.styles import (Font, PatternFill, Alignment, Border, Side,
                              GradientFill)
from openpyxl.utils import get_column_letter

OUT = Path("data/NexaCore_Suppliers_Demo.xlsx")
OUT.parent.mkdir(parents=True, exist_ok=True)

# ── Column definitions ────────────────────────────────────────────────────────
COLUMNS = [
    "Supplier Name",
    "Country",
    "What They Supply",
    "Criticality Level",
    "Supply Category",
    "Annual Spend USD",
    "Spend % of Total Budget",
    "Contract Expiry Date",
    "Tier Level",
    "Sole Source",
    "On Time Delivery Rate",
    "Years In Relationship",
    "Financial Health",
    "Notes",
    "Order Fill Rate",
    "Audit Pass Rate",
    "Improvement Index",
    "Disruption Frequency",
    "Lead Time Variability",
    "Cyber Posture",
    "Inventory Buffer Days",
    "Has RTO Defined",
]

# ── Suppliers ─────────────────────────────────────────────────────────────────
SUPPLIERS = [
    {
        "Supplier Name":           "TexBoard Solutions LLC",
        "Country":                 "UNITED STATES",
        "What They Supply":        "Standard FR-4 double-sided PCBs and prototype boards for non-critical sub-assemblies",
        "Criticality Level":       "Medium",
        "Supply Category":         "PCB Fabrication",
        "Annual Spend USD":        1200000,
        "Spend % of Total Budget": 11.6,
        "Contract Expiry Date":    "2027-09-30",
        "Tier Level":              "Tier 2",
        "Sole Source":             0,
        "On Time Delivery Rate":   96.0,
        "Years In Relationship":   5,
        "Financial Health":        "Good",
        "Notes":                   "Domestic backup PCB vendor. Consistent quality and short lead times. Used for non-flight, non-safety-critical assemblies. No compliance concerns raised to date.",
        "Order Fill Rate":         96.0,
        "Audit Pass Rate":         97.0,
        "Improvement Index":       94.0,
        "Disruption Frequency":    0,
        "Lead Time Variability":   "Low",
        "Cyber Posture":           "Good",
        "Inventory Buffer Days":   30,
        "Has RTO Defined":         1,
    },
]

# ── Build workbook ────────────────────────────────────────────────────────────
wb = openpyxl.Workbook()
ws = wb.active
ws.title = "Suppliers"

# Colours
C_HEADER_BG  = "1A1F35"
C_HEADER_FG  = "E2E8F0"
C_ACCENT     = "6C63FF"
C_BORDER     = "CBD5E1"

THIN   = Side(style="thin", color=C_BORDER)
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

# ── Title row ─────────────────────────────────────────────────────────────────
ws.merge_cells(f"A1:{get_column_letter(len(COLUMNS))}1")
title_cell = ws["A1"]
title_cell.value     = "Supplier Onboarding Register — Import-ready for SupplyShield"
title_cell.font      = Font(name="Calibri", bold=True, size=14, color=C_HEADER_FG)
title_cell.fill      = PatternFill("solid", fgColor=C_HEADER_BG)
title_cell.alignment = Alignment(horizontal="center", vertical="center")
ws.row_dimensions[1].height = 28

# ── Sub-title row ─────────────────────────────────────────────────────────────
ws.merge_cells(f"A2:{get_column_letter(len(COLUMNS))}2")
sub = ws["A2"]
sub.value      = "All 22 fields required for full risk analysis"
sub.font       = Font(name="Calibri", italic=True, size=10, color="94A3B8")
sub.fill       = PatternFill("solid", fgColor=C_HEADER_BG)
sub.alignment  = Alignment(horizontal="center", vertical="center")
ws.row_dimensions[2].height = 18

# ── Header row ────────────────────────────────────────────────────────────────
for col_idx, col_name in enumerate(COLUMNS, start=1):
    cell = ws.cell(row=3, column=col_idx, value=col_name)
    cell.font      = Font(name="Calibri", bold=True, size=10, color=C_HEADER_FG)
    cell.fill      = PatternFill("solid", fgColor=C_ACCENT)
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    cell.border    = BORDER
ws.row_dimensions[3].height = 32

# ── Data rows ─────────────────────────────────────────────────────────────────
for row_idx, supplier in enumerate(SUPPLIERS, start=4):
    fill = PatternFill("solid", fgColor="D1FAE5")  # green — LOW risk
    for col_idx, col_name in enumerate(COLUMNS, start=1):
        val  = supplier.get(col_name, "")
        cell = ws.cell(row=row_idx, column=col_idx, value=val)
        cell.fill      = fill
        cell.border    = BORDER
        cell.font      = Font(name="Calibri", size=9)
        cell.alignment = Alignment(vertical="center", wrap_text=(col_idx == 3 or col_idx == 14))
    ws.row_dimensions[row_idx].height = 40

# ── Column widths ─────────────────────────────────────────────────────────────
WIDTHS = [
    38,   # Supplier Name
    18,   # Country
    52,   # What They Supply
    16,   # Criticality Level
    28,   # Supply Category
    18,   # Annual Spend USD
    22,   # Spend %
    20,   # Contract Expiry Date
    12,   # Tier Level
    12,   # Sole Source
    22,   # On Time Delivery Rate
    22,   # Years In Relationship
    16,   # Financial Health
    55,   # Notes
    18,   # Order Fill Rate
    16,   # Audit Pass Rate
    18,   # Improvement Index
    22,   # Disruption Frequency
    22,   # Lead Time Variability
    14,   # Cyber Posture
    22,   # Inventory Buffer Days
    16,   # Has RTO Defined
]
for i, w in enumerate(WIDTHS, start=1):
    ws.column_dimensions[get_column_letter(i)].width = w

# ── Legend sheet ──────────────────────────────────────────────────────────────
ls = wb.create_sheet("Legend")
ls.column_dimensions["A"].width = 28
ls.column_dimensions["B"].width = 55

legend_rows = [
    ("FIELD", "ACCEPTED VALUES / FORMAT", C_HEADER_BG, C_HEADER_FG),
    ("Criticality Level",       "Critical / High / Medium / Low",                        "E2E8F0", "1E293B"),
    ("Supply Category",         "Semiconductors & ICs / PCB Fabrication / Electronic Components / Connectors & Interconnects / RF & Electronic Systems / Electronics Manufacturing Services / Mechanical Components / Other", "E2E8F0", "1E293B"),
    ("Tier Level",              "Tier 1 / Tier 2 / Tier 3",                              "E2E8F0", "1E293B"),
    ("Sole Source",             "1 = Yes, 0 = No",                                       "E2E8F0", "1E293B"),
    ("On Time Delivery Rate",   "0-100 (percentage, e.g. 95.5)",                         "E2E8F0", "1E293B"),
    ("Financial Health",        "Good / Fair / Poor",                                    "E2E8F0", "1E293B"),
    ("Order Fill Rate",         "0-100 (OTIF in-full %, e.g. 92)",                       "E2E8F0", "1E293B"),
    ("Audit Pass Rate",         "0-100 (compliance audit pass %, e.g. 85)",              "E2E8F0", "1E293B"),
    ("Improvement Index",       "0-100 (corrective action closure %, e.g. 78)",          "E2E8F0", "1E293B"),
    ("Disruption Frequency",    "Integer -- incidents per year (e.g. 2)",                "E2E8F0", "1E293B"),
    ("Lead Time Variability",   "Low / Medium / High",                                   "E2E8F0", "1E293B"),
    ("Cyber Posture",           "Good / Fair / Poor",                                    "E2E8F0", "1E293B"),
    ("Inventory Buffer Days",   "Integer -- days of supply on hand (e.g. 45)",           "E2E8F0", "1E293B"),
    ("Has RTO Defined",         "1 = Yes (RTO documented), 0 = No",                      "E2E8F0", "1E293B"),
    ("Contract Expiry Date",    "YYYY-MM-DD format (e.g. 2027-06-30)",                   "E2E8F0", "1E293B"),
    ("Annual Spend USD",        "Numeric USD value -- no $ or commas (e.g. 1500000)",    "E2E8F0", "1E293B"),
    ("Spend % of Total Budget", "0-100 (e.g. 12.5)",                                     "E2E8F0", "1E293B"),
]

for r, (field, desc, bg, fg) in enumerate(legend_rows, start=1):
    c1 = ls.cell(row=r, column=1, value=field)
    c2 = ls.cell(row=r, column=2, value=desc)
    for c in (c1, c2):
        c.fill      = PatternFill("solid", fgColor=bg)
        c.font      = Font(name="Calibri", bold=(r == 1), size=9, color=fg)
        c.alignment = Alignment(vertical="center", wrap_text=True)
        c.border    = BORDER
    ls.row_dimensions[r].height = 22

wb.save(OUT)
print(f"Excel saved -> {OUT}")
print(f"  {len(SUPPLIERS)} supplier(s)")
print(f"  Columns: {len(COLUMNS)}")
