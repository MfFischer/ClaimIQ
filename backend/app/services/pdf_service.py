"""
ClaimIQ — PDF Report Service
Generates a branded Claim Summary (Schadensübersicht) PDF.
Shared by brokers with their clients — carries ClaimIQ branding.
"""
import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, HRFlowable
)

BRAND_BLUE = colors.HexColor("#1A56A0")
BRAND_LIGHT = colors.HexColor("#D6E8F7")
GREEN = colors.HexColor("#22C55E")
AMBER = colors.HexColor("#F59E0B")
RED = colors.HexColor("#EF4444")
GRAY = colors.HexColor("#555555")
LIGHT_GRAY = colors.HexColor("#F5F5F5")

FIELD_LABELS_DE = {
    "schadennummer": "Schadennummer",
    "schadensdatum": "Schadendatum",
    "meldedatum": "Meldedatum",
    "kennzeichen": "Kennzeichen",
    "fahrzeugmarke": "Fahrzeugmarke",
    "fahrzeugmodell": "Fahrzeugmodell",
    "versicherungsnehmer": "Versicherungsnehmer",
    "geschaedigter": "Geschädigter",
    "kennzeichen_unfallgegner": "Kennzeichen Unfallgegner",
    "schadenshoehe": "Schadenshöhe",
    "selbstbeteiligung": "Selbstbeteiligung",
    "versicherungsscheinnummer": "Versicherungsscheinnummer",
    "versicherungsgesellschaft": "Versicherungsgesellschaft",
    "unfallort": "Unfallort",
    "polizeilich_aufgenommen": "Polizeilich aufgenommen",
    "polizeibericht_nummer": "Polizeibericht-Nr.",
}


def _score_color(score: int):
    if score >= 75:
        return GREEN
    if score >= 50:
        return AMBER
    return RED


def _suggestion_label(s: str) -> str:
    return {"approve": "✓ Annahme empfohlen", "review": "⚠ Prüfung erforderlich",
            "reject": "✗ Ablehnung empfohlen"}.get(s, "⚠ Prüfung erforderlich")


def generate_claim_pdf(claim_data: dict) -> bytes:
    """
    Build the Schadensübersicht PDF.
    claim_data keys: claim_id, summary_de, summary, structured_data,
                     readiness_score, score_breakdown, flags,
                     action_checklist, suggestion, created_at
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2.5*cm, bottomMargin=2*cm,
    )

    s_title = ParagraphStyle("T", fontSize=22, leading=28, textColor=BRAND_BLUE,
                              spaceAfter=2, fontName="Helvetica-Bold")
    s_sub   = ParagraphStyle("S", fontSize=10, leading=14, textColor=GRAY,
                              spaceAfter=0, fontName="Helvetica")
    s_section = ParagraphStyle("Sec", fontSize=11, leading=16, textColor=BRAND_BLUE,
                                spaceBefore=14, spaceAfter=5,
                                fontName="Helvetica-Bold")
    s_body  = ParagraphStyle("B", fontSize=10, leading=15, textColor=colors.black,
                              spaceAfter=4, fontName="Helvetica")
    s_check = ParagraphStyle("C", fontSize=9, leading=13, spaceAfter=4,
                              leftIndent=8, fontName="Helvetica")
    s_footer = ParagraphStyle("Ft", fontSize=7, leading=10, textColor=GRAY,
                               alignment=TA_CENTER, fontName="Helvetica")

    b = []  # story

    # ── Header ────────────────────────────────────────────────────────────────
    # Title and subtitle in a two-row table so spacing is explicit and stable
    hdr = Table(
        [
            [Paragraph("ClaimIQ", s_title)],
            [Paragraph("Schadensübersicht · Kfz-Schaden", s_sub)],
        ],
        colWidths=[17*cm],
    )
    hdr.setStyle(TableStyle([
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
    ]))
    b.append(hdr)
    b.append(Spacer(1, 0.35*cm))
    b.append(HRFlowable(width="100%", thickness=2, color=BRAND_BLUE, spaceAfter=8))

    # Meta
    created = claim_data.get("created_at", datetime.now())
    if isinstance(created, str):
        created = datetime.fromisoformat(created)
    meta = Table(
        [
            ["Schaden-ID:", (claim_data.get("claim_id") or "")[:12] + "..."],
            ["Erstellt:", created.strftime("%d.%m.%Y %H:%M Uhr")],
            ["Schadensart:", "Kfz / Kraftfahrzeug"],
        ],
        colWidths=[4*cm, 13*cm],
    )
    meta.setStyle(TableStyle([
        ("FONTNAME", (0,0),(0,-1), "Helvetica-Bold"),
        ("FONTSIZE", (0,0),(-1,-1), 9),
        ("TEXTCOLOR", (0,0),(0,-1), BRAND_BLUE),
        ("BOTTOMPADDING", (0,0),(-1,-1), 3),
    ]))
    b.append(meta)
    b.append(Spacer(1, 0.4*cm))

    # Summary
    b.append(Paragraph("Zusammenfassung", s_section))
    summary = claim_data.get("summary_de") or claim_data.get("summary") or "Keine Zusammenfassung verfügbar."
    b.append(Paragraph(summary, s_body))
    b.append(Spacer(1, 0.3*cm))

    # Score
    score = claim_data.get("readiness_score") or 0
    suggestion = claim_data.get("suggestion") or "review"
    b.append(Paragraph("Bearbeitungsreife (Claim Readiness Score)", s_section))
    score_tbl = Table(
        [[f"Gesamtscore: {score} / 100", _suggestion_label(suggestion)]],
        colWidths=[8.5*cm, 8.5*cm],
    )
    sc = _score_color(score)
    sl = _score_color(score)
    score_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0),(0,0), sc),
        ("BACKGROUND", (1,0),(1,0), {"approve": GREEN, "review": AMBER, "reject": RED}.get(suggestion, AMBER)),
        ("TEXTCOLOR", (0,0),(-1,-1), colors.white),
        ("FONTNAME", (0,0),(-1,-1), "Helvetica-Bold"),
        ("FONTSIZE", (0,0),(-1,-1), 11),
        ("ALIGN", (0,0),(-1,-1), "CENTER"),
        ("TOPPADDING", (0,0),(-1,-1), 8),
        ("BOTTOMPADDING", (0,0),(-1,-1), 8),
    ]))
    b.append(score_tbl)
    b.append(Spacer(1, 0.2*cm))

    # Score breakdown
    bd = claim_data.get("score_breakdown") or {}
    if bd:
        if hasattr(bd, "model_dump"):
            bd = bd.model_dump()
        bd_tbl = Table(
            [
                ["Vollständigkeit", f"{bd.get('completeness','—')}/100"],
                ["Konsistenz", f"{bd.get('consistency','—')}/100"],
                ["Betrugssignale", f"{bd.get('fraud_signals','—')}/100"],
                ["Dokumentation", f"{bd.get('documentation','—')}/100"],
            ],
            colWidths=[8.5*cm, 8.5*cm],
        )
        bd_tbl.setStyle(TableStyle([
            ("FONTNAME", (0,0),(-1,-1), "Helvetica"),
            ("FONTSIZE", (0,0),(-1,-1), 9),
            ("ROWBACKGROUNDS", (0,0),(-1,-1), [LIGHT_GRAY, colors.white]),
            ("GRID", (0,0),(-1,-1), 0.3, colors.HexColor("#DDDDDD")),
            ("TOPPADDING", (0,0),(-1,-1), 4),
            ("BOTTOMPADDING", (0,0),(-1,-1), 4),
        ]))
        b.append(bd_tbl)
    b.append(Spacer(1, 0.4*cm))

    # Extracted fields
    structured = claim_data.get("structured_data") or {}
    if structured:
        b.append(Paragraph("Extrahierte Daten", s_section))
        rows = []
        for key, label in FIELD_LABELS_DE.items():
            val = structured.get(key)
            if val is not None:
                if isinstance(val, bool):
                    val = "Ja" if val else "Nein"
                rows.append([label, str(val)])
        if rows:
            ft = Table(rows, colWidths=[6*cm, 11*cm])
            ft.setStyle(TableStyle([
                ("FONTNAME", (0,0),(0,-1), "Helvetica-Bold"),
                ("FONTNAME", (1,0),(1,-1), "Helvetica"),
                ("FONTSIZE", (0,0),(-1,-1), 9),
                ("ROWBACKGROUNDS", (0,0),(-1,-1), [LIGHT_GRAY, colors.white]),
                ("GRID", (0,0),(-1,-1), 0.3, colors.HexColor("#DDDDDD")),
                ("TOPPADDING", (0,0),(-1,-1), 3),
                ("BOTTOMPADDING", (0,0),(-1,-1), 3),
            ]))
            b.append(ft)
        b.append(Spacer(1, 0.4*cm))

    # Flags
    flags = claim_data.get("flags") or []
    if flags:
        b.append(Paragraph("Hinweise & Auffälligkeiten", s_section))
        for f in flags:
            if hasattr(f, "model_dump"):
                f = f.model_dump()
            msg = f.get("message_de") or f.get("message") or ""
            sev = f.get("severity", "warning")
            col = {"error": RED, "warning": AMBER, "info": BRAND_BLUE}.get(sev, AMBER)
            icon = {"error": "●", "warning": "▲", "info": "ℹ"}.get(sev, "▲")
            b.append(Paragraph(
                f'<font color="#{col.hexval()[2:]}"><b>{icon}</b></font>  {msg}',
                ParagraphStyle("fl", fontSize=9, spaceAfter=3, fontName="Helvetica",
                               textColor=col)
            ))
        b.append(Spacer(1, 0.4*cm))

    # Checklist
    checklist = claim_data.get("action_checklist") or []
    if checklist:
        b.append(Paragraph("Aktionsliste / To-Do für den Makler", s_section))
        for item in checklist:
            if hasattr(item, "model_dump"):
                item = item.model_dump()
            text = item.get("item_de") or item.get("item") or ""
            req = item.get("required", True)
            prefix = "☐  " + ("[Pflicht] " if req else "[Optional] ")
            b.append(Paragraph(prefix + text, s_check))
        b.append(Spacer(1, 0.4*cm))

    # Footer
    b.append(HRFlowable(width="100%", thickness=0.5,
                         color=colors.HexColor("#CCCCCC"),
                         spaceBefore=8, spaceAfter=4))
    b.append(Paragraph(
        "Erstellt mit ClaimIQ · KI-gestützte Auswertung · "
        "Kein Ersatz für rechtliche oder versicherungsfachliche Beratung · "
        "claimiq.app",
        s_footer,
    ))

    doc.build(b)
    return buf.getvalue()
