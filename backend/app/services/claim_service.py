"""
ClaimIQ — Claim Orchestration Service
Coordinates: save → OCR → AI → DB write → usage tracking
"""
import logging
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.claim import Claim, UsageTracking, FeedbackLog
from app.schemas.claim import FeedbackRequest
from app.core.config import get_settings
from app.services.ocr_service import extract_text
from app.services.ai_service import process_kfz_claim
from app.services.storage_service import save_file

logger = logging.getLogger(__name__)
settings = get_settings()


async def create_claim(
    file_bytes: bytes,
    filename: str,
    content_type: str,
    session_id: str,
    db: AsyncSession,
) -> Claim:
    """Full pipeline: upload → OCR → AI → store → return."""

    # Create record immediately so we have a claim_id
    claim = Claim(
        session_id=session_id,
        file_name=filename,
        file_type=content_type,
        file_url="",
        status="processing",
        claim_vertical="kfz",
    )
    db.add(claim)
    await db.commit()
    await db.refresh(claim)

    try:
        # 1. Save file
        file_url = await save_file(file_bytes, filename)
        claim.file_url = file_url

        # 2. OCR
        ocr = await extract_text(file_bytes, content_type)
        claim.raw_text = ocr.text
        claim.ocr_engine = ocr.engine
        claim.ocr_confidence = ocr.confidence

        if not ocr.text.strip() and not settings.mock_mode:
            raise ValueError(
                "OCR konnte keinen Text extrahieren. "
                "Bitte prüfen Sie die Bildqualität des Dokuments."
            )

        # 3. AI processing
        ai = await process_kfz_claim(ocr.text)

        # 4. Persist all outputs
        claim.structured_data = ai.structured_data
        claim.summary = ai.summary
        claim.summary_de = ai.summary_de
        claim.readiness_score = ai.readiness_score
        claim.score_completeness = ai.score_breakdown.completeness
        claim.score_consistency = ai.score_breakdown.consistency
        claim.score_fraud_signals = ai.score_breakdown.fraud_signals
        claim.score_documentation = ai.score_breakdown.documentation
        claim.flags = [f.model_dump() for f in ai.flags]
        claim.action_checklist = [c.model_dump() for c in ai.action_checklist]
        claim.suggestion = ai.suggestion
        claim.status = "done"

        # 5. Usage tracking
        await _track_usage(db, ocr.engine)

        await db.commit()
        await db.refresh(claim)
        return claim

    except Exception as e:
        logger.error(f"Claim {claim.id} processing failed: {e}", exc_info=True)
        claim.status = "error"
        claim.error_message = str(e)
        await db.commit()
        await db.refresh(claim)
        return claim


async def get_claim(claim_id: str, db: AsyncSession) -> Claim | None:
    result = await db.execute(select(Claim).where(Claim.id == claim_id))
    return result.scalar_one_or_none()


async def add_feedback(
    claim_id: str, feedback: FeedbackRequest, db: AsyncSession
) -> bool:
    claim = await get_claim(claim_id, db)
    if not claim:
        return False
    log = FeedbackLog(
        claim_id=claim_id,
        field_corrected=feedback.field_corrected,
        original_value=feedback.original_value,
        corrected_value=feedback.corrected_value,
        general_comment=feedback.general_comment,
    )
    db.add(log)
    await db.commit()
    return True


async def get_usage(db: AsyncSession) -> UsageTracking | None:
    month = datetime.now(timezone.utc).strftime("%Y-%m")
    result = await db.execute(
        select(UsageTracking).where(UsageTracking.month == month)
    )
    return result.scalar_one_or_none()


async def _track_usage(db: AsyncSession, ocr_engine: str):
    month = datetime.now(timezone.utc).strftime("%Y-%m")
    result = await db.execute(
        select(UsageTracking).where(UsageTracking.month == month)
    )
    usage = result.scalar_one_or_none()
    if not usage:
        usage = UsageTracking(month=month)
        db.add(usage)

    usage.total_claims_processed = (usage.total_claims_processed or 0) + 1
    if ocr_engine == "google_vision":
        usage.google_vision_calls = (usage.google_vision_calls or 0) + 1
        usage.total_ocr_fallbacks = (usage.total_ocr_fallbacks or 0) + 1

    await db.commit()
