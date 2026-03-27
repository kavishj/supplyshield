import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
from config import DEFAULT_WEIGHTS

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 Table, TableStyle, HRFlowable)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from io import BytesIO
from datetime import datetime

# ── Colors — light document palette ──────────────────────────
WHITE     = colors.white
OFF_WHITE = colors.HexColor("#F8FAFC")
LIGHT_BG  = colors.HexColor("#F1F5F9")
BORDER    = colors.HexColor("#E2E8F0")
NAVY      = colors.HexColor("#0A1628")
NAVY_MID  = colors.HexColor("#1E3A5F")
CYAN      = colors.HexColor("#0891B2")
MUTED     = colors.HexColor("#64748B")
TEXT      = colors.HexColor("#1E293B")
TEXT_LIGHT= colors.HexColor("#475569")
RED       = colors.HexColor("#DC2626")
RED_BG    = colors.HexColor("#FEF2F2")
AMBER     = colors.HexColor("#D97706")
AMBER_BG  = colors.HexColor("#FFFBEB")
GREEN     = colors.HexColor("#059669")
GREEN_BG  = colors.HexColor("#F0FDF4")

def _decision_color(decision):
    return {"BLOCKED": RED, "REQUIRES_APPROVAL": AMBER, "AUTO_APPROVED": GREEN}.get(decision, MUTED)

def _decision_bg(decision):
    return {"BLOCKED": RED_BG, "REQUIRES_APPROVAL": AMBER_BG, "AUTO_APPROVED": GREEN_BG}.get(decision, LIGHT_BG)

def _score_color(score):
    if score >= 0.75: return RED
    if score >= 0.45: return AMBER
    return GREEN

def generate_supplier_pdf(result: dict) -> bytes:
    buffer = BytesIO()
    doc    = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
        title=f"SupplyShield Risk Report — {result.get('company_name', '')}",
    )
    story  = []
    W      = A4[0] - 4*cm

    # ── Style helpers ─────────────────────────────────────────
    def S(name, **kw):
        return ParagraphStyle(name, **kw)

    s_body    = S("body",    fontSize=9,   textColor=TEXT,       fontName="Helvetica",      leading=14, spaceAfter=4)
    s_muted   = S("muted",   fontSize=8,   textColor=MUTED,      fontName="Helvetica",      leading=12)
    s_section = S("section", fontSize=7,   textColor=MUTED,      fontName="Helvetica-Bold",
                  spaceAfter=8, leading=10)
    s_summary = S("summary", fontSize=9.5, textColor=TEXT,       fontName="Helvetica",      leading=16, spaceAfter=6)

    # ── Header ────────────────────────────────────────────────
    hdr = Table([[
        Paragraph('<font color="#FFFFFF" size="16"><b>SupplyShield</b></font><br/>'
                  '<font color="#94A3B8" size="7">SUPPLY CHAIN RISK INTELLIGENCE</font>', s_muted),
        Paragraph(f'<font color="#94A3B8" size="8">Generated {datetime.now().strftime("%d %b %Y, %H:%M UTC")}</font>',
                  S("r", fontSize=8, textColor=MUTED, fontName="Helvetica", alignment=TA_RIGHT)),
    ]], colWidths=[W*0.6, W*0.4])
    hdr.setStyle(TableStyle([
        ("BACKGROUND",   (0,0),(-1,-1), NAVY),
        ("TOPPADDING",   (0,0),(-1,-1), 16),
        ("BOTTOMPADDING",(0,0),(-1,-1), 16),
        ("LEFTPADDING",  (0,0),(-1,-1), 18),
        ("RIGHTPADDING", (0,0),(-1,-1), 18),
        ("VALIGN",       (0,0),(-1,-1), "MIDDLE"),
    ]))
    story.append(hdr)

    # Cyan accent line
    story.append(HRFlowable(width="100%", thickness=2.5, color=CYAN, spaceAfter=0, spaceBefore=0))
    story.append(Spacer(1, 0.4*cm))

    # ── Company name + gate decision ──────────────────────────
    company  = result.get("company_name", "Unknown")
    country  = result.get("country") or "N/A"
    gate     = result.get("gate_decision", "")
    gate_col = _decision_color(gate)
    gate_bg  = _decision_bg(gate)
    gate_label = {
        "BLOCKED":           "BLOCKED — OFAC SANCTIONS MATCH",
        "REQUIRES_APPROVAL": "REQUIRES PROCUREMENT APPROVAL",
        "AUTO_APPROVED":     "AUTO-APPROVED",
    }.get(gate, gate)

    story.append(Paragraph(
    f'<font size="18" color="#0A1628"><b>{company}</b></font>',
    S("cn", fontSize=18, textColor=NAVY, fontName="Helvetica-Bold",
      spaceAfter=4, spaceBefore=4)
                            ))
    story.append(Paragraph(
    f'Country of Origin: {country}',
    S("co", fontSize=9, textColor=MUTED, fontName="Helvetica",
      spaceAfter=12, spaceBefore=0)
                            ))

    # Gate badge
    gate_tbl = Table([[
        Paragraph(f'<b>{gate_label}</b>',
                  S("gb", fontSize=10, textColor=gate_col,
                    fontName="Helvetica-Bold")),
        Paragraph(result.get("gate_reason", ""),
                  S("gr", fontSize=8.5, textColor=TEXT_LIGHT,
                    fontName="Helvetica", leading=13)),
    ]], colWidths=[W*0.35, W*0.65])
    gate_tbl.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (0,0),  gate_bg),
        ("BACKGROUND",   (1,0), (1,0),  LIGHT_BG),
        ("TOPPADDING",   (0,0), (-1,-1), 12),
        ("BOTTOMPADDING",(0,0), (-1,-1), 12),
        ("LEFTPADDING",  (0,0), (-1,-1), 14),
        ("RIGHTPADDING", (0,0), (-1,-1), 14),
        ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
        ("LINEBEFORE",   (0,0), (0,-1),  4, gate_col),
        ("BOX",          (0,0), (-1,-1), 0.5, BORDER),
    ]))
    story.append(gate_tbl)
    story.append(Spacer(1, 0.5*cm))

    # ── Key metrics ───────────────────────────────────────────
    story.append(Paragraph("KEY METRICS", s_section))

    score     = result.get("risk_score", 0)
    score_col = _score_color(score)
    ofac_col  = RED if result.get("ofac_status") == "SANCTIONED" else GREEN

    metrics = [
        ("Risk Score",    f"{score:.3f}", score_col),
        ("Risk Category", result.get("risk_category", "N/A"), score_col),
        ("OFAC Status",   result.get("ofac_status", "N/A"), ofac_col),
        ("SDN Matches",   str(result.get("ofac_matches", 0)),
         RED if result.get("ofac_matches", 0) > 0 else GREEN),
        ("News Risk",     result.get("news_risk", "N/A"), AMBER),
        ("Approval",      "Required" if result.get("approval_required") else "Not Required",
         RED if result.get("approval_required") else GREEN),
    ]

    cells = []
    for label, value, col in metrics:
        c = Table([
            [Paragraph(label, S("ml", fontSize=7, textColor=MUTED,
                                fontName="Helvetica", leading=9))],
            [Paragraph(f'<b>{value}</b>',
           S("mv", fontSize=10, textColor=col,
             fontName="Helvetica-Bold", leading=13, wordWrap="CJK"))],
        ], colWidths=[W/6 - 0.3*cm])
        c.setStyle(TableStyle([
            ("BACKGROUND",   (0,0),(-1,-1), WHITE),
            ("TOPPADDING",   (0,0),(-1,-1), 12),
            ("BOTTOMPADDING",(0,0),(-1,-1), 12),
            ("LEFTPADDING",  (0,0),(-1,-1), 10),
            ("RIGHTPADDING", (0,0),(-1,-1), 6),
            ("BOX",          (0,0),(-1,-1), 0.5, BORDER),
            ("LINEBELOW",    (0,0),(-1,-1), 2.5, col),
            ("ROWHEIGHT",    (0,0), (-1,-1), 0.9*cm),
        ]))
        cells.append(c)

    metrics_row = Table([cells], colWidths=[W/6]*6)
    metrics_row.setStyle(TableStyle([
        ("LEFTPADDING",  (0,0),(-1,-1), 3),
        ("RIGHTPADDING", (0,0),(-1,-1), 3),
        ("VALIGN",       (0,0),(-1,-1), "TOP"),
    ]))
    story.append(metrics_row)
    story.append(Spacer(1, 0.5*cm))

    # ── Risk breakdown table ──────────────────────────────────
    story.append(Paragraph("RISK COMPONENT BREAKDOWN", s_section))

    comps   = result.get("risk_components", {})
    weights = result.get("risk_weights", DEFAULT_WEIGHTS)
    factor_labels = {
        "ofac":          "OFAC Sanctions Status",
        "geography":     "Geographic Concentration",
        "news":          "News Sentiment Risk",
        "single_source": "Single-Source Dependency",
        "lead_time":     "Lead Time Risk",
    }

    hdr_style = S("th", fontSize=8, textColor=WHITE,
                  fontName="Helvetica-Bold", leading=11)
    cell_style = S("td", fontSize=8.5, textColor=TEXT,
                   fontName="Helvetica", leading=12)

    rows = [[
        Paragraph("Risk Factor",   hdr_style),
        Paragraph("Weight",        hdr_style),
        Paragraph("Raw Score",     hdr_style),
        Paragraph("Weighted",      hdr_style),
        Paragraph("Contribution",  hdr_style),
    ]]
    for key, label in factor_labels.items():
        raw      = comps.get(key, 0)
        w        = weights.get(key, 0)
        weighted = raw * w
        contrib  = f"{(weighted/score*100):.1f}%" if score > 0 else "—"
        rows.append([
            Paragraph(label,           cell_style),
            Paragraph(f"{w:.0%}",      cell_style),
            Paragraph(f"{raw:.3f}",    cell_style),
            Paragraph(f"{weighted:.4f}",cell_style),
            Paragraph(contrib,         cell_style),
        ])

    comp_tbl = Table(rows, colWidths=[W*0.38, W*0.12, W*0.15, W*0.15, W*0.20])
    comp_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  NAVY_MID),
        ("BACKGROUND",    (0,1), (-1,-1), WHITE),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [WHITE, LIGHT_BG]),
        ("TOPPADDING",    (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ("LEFTPADDING",   (0,0), (-1,-1), 10),
        ("RIGHTPADDING",  (0,0), (-1,-1), 10),
        ("GRID",          (0,0), (-1,-1), 0.3, BORDER),
        ("ALIGN",         (1,0), (-1,-1), "CENTER"),
    ]))
    story.append(comp_tbl)
    story.append(Spacer(1, 0.5*cm))

    # ── OFAC matches ──────────────────────────────────────────
    if result.get("matched_entities"):
        story.append(Paragraph("OFAC SDN MATCHED ENTITIES", s_section))
        e_rows = [[
            Paragraph("Entity Name", hdr_style),
            Paragraph("Type",        hdr_style),
            Paragraph("Program",     hdr_style),
            Paragraph("Similarity",  hdr_style),
        ]]
        for e in result["matched_entities"][:10]:
            e_rows.append([
                Paragraph(e.get("name", ""),    cell_style),
                Paragraph(e.get("type", ""),    cell_style),
                Paragraph(e.get("program", ""), cell_style),
                Paragraph(f"{e.get('similarity', 0):.1f}%", cell_style),
            ])
        e_tbl = Table(e_rows, colWidths=[W*0.40, W*0.15, W*0.30, W*0.15])
        e_tbl.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,0),  RED),
            ("BACKGROUND",    (0,1), (-1,-1), RED_BG),
            ("ROWBACKGROUNDS",(0,1), (-1,-1), [RED_BG, WHITE]),
            ("TOPPADDING",    (0,0), (-1,-1), 7),
            ("BOTTOMPADDING", (0,0), (-1,-1), 7),
            ("LEFTPADDING",   (0,0), (-1,-1), 10),
            ("GRID",          (0,0), (-1,-1), 0.3, BORDER),
        ]))
        story.append(e_tbl)
        story.append(Spacer(1, 0.5*cm))

    # ── News ──────────────────────────────────────────────────
    if result.get("news_headlines"):
        story.append(Paragraph("LIVE NEWS INTELLIGENCE", s_section))
        for headline in result["news_headlines"][:5]:
            n_tbl = Table([[Paragraph(f"• {headline}", s_body)]],
                          colWidths=[W])
            n_tbl.setStyle(TableStyle([
                ("BACKGROUND",   (0,0),(-1,-1), LIGHT_BG),
                ("LEFTPADDING",  (0,0),(-1,-1), 14),
                ("TOPPADDING",   (0,0),(-1,-1), 7),
                ("BOTTOMPADDING",(0,0),(-1,-1), 7),
                ("LINEBEFORE",   (0,0),(0,-1),  3, AMBER),
                ("BOX",          (0,0),(-1,-1), 0.3, BORDER),
            ]))
            story.append(n_tbl)
            story.append(Spacer(1, 0.15*cm))
        story.append(Spacer(1, 0.3*cm))

    # ── AI Summary ────────────────────────────────────────────
    if result.get("ai_summary"):
        story.append(Paragraph("AI EXECUTIVE BRIEFING", s_section))
        story.append(Paragraph(
            f"Generated by {result.get('summary_model', 'SupplyShield AI')}",
            S("sm", fontSize=7, textColor=MUTED, fontName="Helvetica", spaceAfter=6)
        ))
        sum_tbl = Table([[Paragraph(
            result["ai_summary"].replace("\n\n", "<br/><br/>"), s_summary
        )]], colWidths=[W])
        sum_tbl.setStyle(TableStyle([
            ("BACKGROUND",   (0,0),(-1,-1), LIGHT_BG),
            ("LEFTPADDING",  (0,0),(-1,-1), 16),
            ("RIGHTPADDING", (0,0),(-1,-1), 16),
            ("TOPPADDING",   (0,0),(-1,-1), 14),
            ("BOTTOMPADDING",(0,0),(-1,-1), 14),
            ("LINEBEFORE",   (0,0),(0,-1),  3, CYAN),
            ("BOX",          (0,0),(-1,-1), 0.3, BORDER),
        ]))
        story.append(sum_tbl)
        story.append(Spacer(1, 0.5*cm))

    # ── Recommendation ────────────────────────────────────────
    story.append(Paragraph("RECOMMENDED ACTION", s_section))
    rec_col = _decision_color(gate)
    rec_tbl = Table([[Paragraph(result.get("recommendation", ""), s_body)]],
                    colWidths=[W])
    rec_tbl.setStyle(TableStyle([
        ("BACKGROUND",   (0,0),(-1,-1), _decision_bg(gate)),
        ("LEFTPADDING",  (0,0),(-1,-1), 16),
        ("TOPPADDING",   (0,0),(-1,-1), 12),
        ("BOTTOMPADDING",(0,0),(-1,-1), 12),
        ("LINEBEFORE",   (0,0),(0,-1),  3, rec_col),
        ("BOX",          (0,0),(-1,-1), 0.3, BORDER),
    ]))
    story.append(rec_tbl)
    story.append(Spacer(1, 0.5*cm))

    # ── AI Recommendations (if available) ─────────────────────
    recs = result.get("recommendations")
    if recs and (recs.get("immediate_actions") or recs.get("long_term_actions")):
        story.append(Paragraph("AI-GENERATED RISK MITIGATION RECOMMENDATIONS", s_section))
        story.append(Paragraph(
            f"Generated by {recs.get('model', 'SupplyShield AI')}",
            S("rm", fontSize=7, textColor=MUTED, fontName="Helvetica", spaceAfter=8),
        ))

        def _action_table(actions, label_col, accent_col):
            if not actions:
                return
            story.append(Paragraph(label_col, S("ah", fontSize=8, textColor=accent_col,
                                                 fontName="Helvetica-Bold", spaceAfter=4)))
            for i, act in enumerate(actions, 1):
                action_text  = act.get("action", "")
                rationale    = act.get("rationale", "")
                extra        = act.get("timeline") or act.get("priority", "")
                source       = act.get("source", "")

                row_content = f"<b>{i}. {action_text}</b><br/>{rationale}"
                if extra:
                    row_content += f"<br/><i>{extra}</i>"
                if source and source != "Internal Analysis":
                    row_content += f"<br/><font color='#0891B2' size='7'>{source[:80]}</font>"

                a_tbl = Table([[Paragraph(row_content,
                                          S("at", fontSize=8, textColor=TEXT,
                                            fontName="Helvetica", leading=12))
                               ]], colWidths=[W])
                a_tbl.setStyle(TableStyle([
                    ("BACKGROUND",   (0,0),(-1,-1), LIGHT_BG),
                    ("LEFTPADDING",  (0,0),(-1,-1), 14),
                    ("RIGHTPADDING", (0,0),(-1,-1), 14),
                    ("TOPPADDING",   (0,0),(-1,-1), 8),
                    ("BOTTOMPADDING",(0,0),(-1,-1), 8),
                    ("LINEBEFORE",   (0,0),(0,-1),  3, accent_col),
                    ("BOX",          (0,0),(-1,-1), 0.3, BORDER),
                ]))
                story.append(a_tbl)
                story.append(Spacer(1, 0.15*cm))
            story.append(Spacer(1, 0.2*cm))

        _action_table(recs.get("immediate_actions", []),
                      "IMMEDIATE ACTIONS (within 30 days)", RED)
        _action_table(recs.get("long_term_actions", []),
                      "LONG-TERM ACTIONS (3–18 months)", CYAN)

        # Web sources
        sources = [s for s in recs.get("web_sources", []) if s.get("url") and s.get("title")]
        if sources:
            story.append(Paragraph("INTELLIGENCE SOURCES", s_section))
            src_rows = [[
                Paragraph("Source", hdr_style),
                Paragraph("URL", hdr_style),
            ]]
            for s in sources[:6]:
                src_rows.append([
                    Paragraph(s.get("title", "")[:60], cell_style),
                    Paragraph(s.get("url",   "")[:70],
                              S("su", fontSize=7, textColor=CYAN,
                                fontName="Helvetica", leading=10)),
                ])
            src_tbl = Table(src_rows, colWidths=[W*0.40, W*0.60])
            src_tbl.setStyle(TableStyle([
                ("BACKGROUND",   (0,0), (-1,0), NAVY_MID),
                ("BACKGROUND",   (0,1), (-1,-1), WHITE),
                ("ROWBACKGROUNDS",(0,1),(-1,-1), [WHITE, LIGHT_BG]),
                ("TOPPADDING",   (0,0), (-1,-1), 6),
                ("BOTTOMPADDING",(0,0), (-1,-1), 6),
                ("LEFTPADDING",  (0,0), (-1,-1), 10),
                ("GRID",         (0,0), (-1,-1), 0.3, BORDER),
            ]))
            story.append(src_tbl)
            story.append(Spacer(1, 0.3*cm))

    story.append(Spacer(1, 0.3*cm))

    # ── Footer ────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER))
    story.append(Spacer(1, 0.2*cm))
    ft = Table([[
        Paragraph("SupplyShield — Confidential Risk Intelligence Report",
                  S("fl", fontSize=7, textColor=MUTED, fontName="Helvetica")),
        Paragraph(
            f"Report ID: SS-{datetime.now().strftime('%Y%m%d%H%M%S')} · "
            f"OFAC Records: {result.get('records_searched', 18708):,}",
            S("fr", fontSize=7, textColor=MUTED, fontName="Helvetica",
              alignment=TA_RIGHT)
        ),
    ]], colWidths=[W*0.6, W*0.4])
    ft.setStyle(TableStyle([
        ("TOPPADDING",  (0,0),(-1,-1), 4),
        ("LEFTPADDING", (0,0),(-1,-1), 0),
        ("RIGHTPADDING",(0,0),(-1,-1), 0),
    ]))
    story.append(ft)

    doc.build(story)
    return buffer.getvalue()