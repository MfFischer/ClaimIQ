"""
ClaimIQ — AI Service (Google Gemini)
Extraction + scoring for Kfz claims.
Includes MOCK MODE when no API key is set — safe for development.
"""
import json
import logging
import re
from dataclasses import dataclass

from app.core.config import get_settings
from app.prompts.kfz_prompts import KFZ_EXTRACTION_PROMPT, KFZ_SCORING_PROMPT
from app.schemas.claim import ScoreBreakdown, Flag, ChecklistItem

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class ClaimAIResult:
    structured_data: dict
    summary: str
    summary_de: str
    readiness_score: int
    score_breakdown: ScoreBreakdown
    flags: list[Flag]
    action_checklist: list[ChecklistItem]
    suggestion: str


def _parse_json(text: str) -> dict:
    """Safely parse JSON. Strips markdown fences if model adds them."""
    text = text.strip()
    text = re.sub(r"^```json\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e} | Raw: {text[:300]}")
        return {}


def _mock_result() -> ClaimAIResult:
    """
    Returns realistic mock data when no Gemini API key is configured.
    Lets you test the full UI/UX flow without any API keys.
    """
    return ClaimAIResult(
        structured_data={
            "schadennummer": "SCH-2024-00123",
            "schadensdatum": "15.03.2024",
            "meldedatum": "16.03.2024",
            "kennzeichen": "M-AB 1234",
            "fahrzeugmarke": "BMW",
            "fahrzeugmodell": "3er (G20)",
            "fahrgestellnummer": "WBA5E71090AE12345",
            "versicherungsnehmer": "Max Mustermann",
            "geschaedigter": "Erika Musterfrau",
            "kennzeichen_unfallgegner": "FFB-XY 567",
            "schadenshoehe": "3.450,00 €",
            "selbstbeteiligung": "300,00 €",
            "versicherungsscheinnummer": "VS-9876543",
            "versicherungsgesellschaft": "Allianz Versicherung",
            "unfallort": "Leopoldstraße 45, 80802 München",
            "unfallhergang": "Auffahrunfall beim Anhalten an roter Ampel. Unfallgegner fuhr auf.",
            "polizeilich_aufgenommen": True,
            "polizeibericht_nummer": "POL-MUC-2024-1234",
        },
        summary="Rear-end collision at traffic light in Munich; claimant's BMW struck by vehicle with plate FFB-XY 567, damage estimated at €3,450.",
        summary_de="Auffahrunfall an einer Ampel in München; BMW des Versicherungsnehmers wurde von Fahrzeug mit Kennzeichen FFB-XY 567 gerammt, Schaden ca. 3.450 €.",
        readiness_score=82,
        score_breakdown=ScoreBreakdown(
            completeness=90,
            consistency=85,
            fraud_signals=95,
            documentation=60,
        ),
        flags=[
            Flag(
                field="score_dokumentation",
                message_de="Kein Kfz-Gutachten vorhanden — bei Schaden über 2.000 € empfohlen.",
                message="No damage assessment report found — recommended for claims over €2,000.",
                severity="warning",
            ),
            Flag(
                field="selbstbeteiligung",
                message_de="Selbstbeteiligung (300 €) wurde noch nicht vom Schadensbetrag abgezogen.",
                message="Deductible (€300) has not been subtracted from the claim amount.",
                severity="info",
            ),
        ],
        action_checklist=[
            ChecklistItem(
                item_de="Kfz-Gutachten oder Kostenvoranschlag einer Werkstatt anfordern",
                item="Request vehicle damage assessment or workshop estimate",
                required=True,
            ),
            ChecklistItem(
                item_de="Polizeibericht POL-MUC-2024-1234 als Kopie anfordern",
                item="Request copy of police report POL-MUC-2024-1234",
                required=True,
            ),
            ChecklistItem(
                item_de="Fotos vom Unfallschaden anfordern (mind. 4 Ansichten)",
                item="Request photos of vehicle damage (minimum 4 angles)",
                required=True,
            ),
            ChecklistItem(
                item_de="Selbstbeteiligung von 300 € mit Versicherungsnehmer klären",
                item="Clarify €300 deductible with policyholder",
                required=False,
            ),
        ],
        suggestion="review",
    )


async def process_kfz_claim(ocr_text: str) -> ClaimAIResult:
    """
    Two-call Gemini pipeline:
    1. Extract structured fields from OCR text
    2. Score + generate flags and action checklist

    Falls back to mock data if GEMINI_API_KEY is not set.
    """
    if settings.mock_mode:
        logger.info("MOCK MODE active (no GEMINI_API_KEY set) — returning mock result")
        return _mock_result()

    import google.generativeai as genai

    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel(
        model_name=settings.gemini_model,
        generation_config=genai.GenerationConfig(
            temperature=0.1,
            response_mime_type="application/json",
        ),
    )

    # ── Call 1: Extract ───────────────────────────────────────────────────────
    extraction_response = model.generate_content(
        KFZ_EXTRACTION_PROMPT.format(ocr_text=ocr_text)
    )
    extracted = _parse_json(extraction_response.text)

    summary_de = extracted.pop("zusammenfassung_de", "") or ""
    summary_en = extracted.pop("zusammenfassung_en", "") or ""

    # ── Call 2: Score ─────────────────────────────────────────────────────────
    scoring_response = model.generate_content(
        KFZ_SCORING_PROMPT.format(
            structured_data=json.dumps(extracted, ensure_ascii=False, indent=2),
            ocr_text=ocr_text[:2000],
        )
    )
    scored = _parse_json(scoring_response.text)

    score_breakdown = ScoreBreakdown(
        completeness=scored.get("score_vollstaendigkeit", 50),
        consistency=scored.get("score_konsistenz", 50),
        fraud_signals=scored.get("score_betrugshinweise", 50),
        documentation=scored.get("score_dokumentation", 50),
    )

    overall = scored.get("gesamtscore") or int(
        (score_breakdown.completeness + score_breakdown.consistency
         + score_breakdown.fraud_signals + score_breakdown.documentation) / 4
    )

    flags = [
        Flag(
            field=f.get("field", ""),
            message=f.get("message", ""),
            message_de=f.get("message_de", ""),
            severity=f.get("severity", "warning"),
        )
        for f in scored.get("flags", [])
    ]

    checklist = [
        ChecklistItem(
            item=a.get("item", ""),
            item_de=a.get("item_de", ""),
            required=a.get("required", True),
        )
        for a in scored.get("aktionsliste", [])
    ]

    empfehlung_map = {"annehmen": "approve", "pruefen": "review", "ablehnen": "reject"}
    suggestion = empfehlung_map.get(scored.get("empfehlung", "pruefen"), "review")

    return ClaimAIResult(
        structured_data=extracted,
        summary=summary_en,
        summary_de=summary_de,
        readiness_score=overall,
        score_breakdown=score_breakdown,
        flags=flags,
        action_checklist=checklist,
        suggestion=suggestion,
    )
