"""
ClaimIQ — Claims API Router
POST /claims/upload     — upload + process document
GET  /claims/{id}       — get result
POST /claims/{id}/feedback — submit correction
GET  /claims/{id}/pdf   — download Schadensübersicht PDF
GET  /claims/usage      — usage stats (internal)
"""
import uuid
import logging
from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import io

from app.core.config import get_settings
from app.db.database import get_db
from app.schemas.claim import (
    UploadResponse, ClaimResult, FeedbackRequest, FeedbackResponse,
    ScoreBreakdown, Flag, ChecklistItem, UsageStats,
)
from app.services.claim_service import (
    create_claim, get_claim, add_feedback, get_usage
)
from app.services.pdf_service import generate_claim_pdf

router = APIRouter(prefix="/claims", tags=["claims"])
logger = logging.getLogger(__name__)
settings = get_settings()


def _session_id(session_id: str | None = Query(default=None)) -> str:
    return session_id or str(uuid.uuid4())


@router.post("/upload", response_model=UploadResponse)
async def upload_claim(
    file: UploadFile = File(...),
    session_id: str = Depends(_session_id),
    db: AsyncSession = Depends(get_db),
):
    """Upload a Kfz claim document and receive the full analysis."""
    # Validate extension
    ext = Path(file.filename or "").suffix.lower().lstrip(".")
    if ext not in settings.allowed_extensions_set:
        raise HTTPException(
            status_code=400,
            detail=f"Dateityp '.{ext}' nicht unterstützt. "
                   f"Erlaubt: {', '.join(sorted(settings.allowed_extensions_set))}",
        )

    # Validate size
    file_bytes = await file.read()
    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > settings.max_file_size_mb:
        raise HTTPException(
            status_code=413,
            detail=f"Datei zu groß ({size_mb:.1f} MB). Maximum: {settings.max_file_size_mb} MB",
        )

    content_type = file.content_type or f"image/{ext}"
    claim = await create_claim(
        file_bytes=file_bytes,
        filename=file.filename or f"upload.{ext}",
        content_type=content_type,
        session_id=session_id,
        db=db,
    )

    msg = (
        "Schaden erfolgreich analysiert."
        if claim.status == "done"
        else f"Fehler: {claim.error_message}"
    )
    return UploadResponse(claim_id=claim.id, status=claim.status, message=msg)


@router.get("/usage", response_model=UsageStats)
async def usage_stats(db: AsyncSession = Depends(get_db)):
    """Current month usage. Used internally to watch API costs."""
    usage = await get_usage(db)
    if not usage:
        from datetime import datetime, timezone
        month = datetime.now(timezone.utc).strftime("%Y-%m")
        return UsageStats(
            month=month,
            total_claims_processed=0,
            google_vision_calls=0,
            google_vision_limit=settings.google_vision_monthly_limit,
            total_ocr_fallbacks=0,
        )
    return UsageStats(
        month=usage.month,
        total_claims_processed=usage.total_claims_processed or 0,
        google_vision_calls=usage.google_vision_calls or 0,
        google_vision_limit=settings.google_vision_monthly_limit,
        total_ocr_fallbacks=usage.total_ocr_fallbacks or 0,
    )


@router.get("/{claim_id}", response_model=ClaimResult)
async def get_claim_result(
    claim_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get the full result for a processed claim."""
    claim = await get_claim(claim_id, db)
    if not claim:
        raise HTTPException(status_code=404, detail="Schaden nicht gefunden.")

    score_breakdown = None
    if claim.score_completeness is not None:
        score_breakdown = ScoreBreakdown(
            completeness=claim.score_completeness,
            consistency=claim.score_consistency,
            fraud_signals=claim.score_fraud_signals,
            documentation=claim.score_documentation,
        )

    flags = [Flag(**f) for f in (claim.flags or [])]
    checklist = [ChecklistItem(**c) for c in (claim.action_checklist or [])]

    return ClaimResult(
        claim_id=claim.id,
        status=claim.status,
        created_at=claim.created_at,
        summary=claim.summary,
        summary_de=claim.summary_de,
        structured_data=claim.structured_data,
        claim_vertical=claim.claim_vertical,
        readiness_score=claim.readiness_score,
        score_breakdown=score_breakdown,
        flags=flags,
        action_checklist=checklist,
        suggestion=claim.suggestion,
        ocr_engine=claim.ocr_engine,
        error_message=claim.error_message,
    )


@router.post("/{claim_id}/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    claim_id: str,
    feedback: FeedbackRequest,
    db: AsyncSession = Depends(get_db),
):
    """Submit a correction. Logged to feedback_log — builds our training dataset."""
    success = await add_feedback(claim_id, feedback, db)
    if not success:
        raise HTTPException(status_code=404, detail="Schaden nicht gefunden.")
    return FeedbackResponse()


@router.get("/{claim_id}/pdf")
async def download_pdf(
    claim_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Download a branded Schadensübersicht PDF for the broker to share."""
    claim = await get_claim(claim_id, db)
    if not claim:
        raise HTTPException(status_code=404, detail="Schaden nicht gefunden.")
    if claim.status != "done":
        raise HTTPException(
            status_code=400, detail="Schaden noch nicht verarbeitet."
        )

    score_breakdown = None
    if claim.score_completeness is not None:
        score_breakdown = ScoreBreakdown(
            completeness=claim.score_completeness,
            consistency=claim.score_consistency,
            fraud_signals=claim.score_fraud_signals,
            documentation=claim.score_documentation,
        )

    pdf_bytes = generate_claim_pdf({
        "claim_id": claim.id,
        "summary": claim.summary,
        "summary_de": claim.summary_de,
        "structured_data": claim.structured_data or {},
        "readiness_score": claim.readiness_score,
        "score_breakdown": score_breakdown,
        "flags": [Flag(**f) for f in (claim.flags or [])],
        "action_checklist": [ChecklistItem(**c) for c in (claim.action_checklist or [])],
        "suggestion": claim.suggestion,
        "created_at": claim.created_at,
    })

    safe_id = claim.id[:8]
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="ClaimIQ_Schaden_{safe_id}.pdf"'
        },
    )
