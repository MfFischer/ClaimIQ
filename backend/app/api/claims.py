"""
ClaimIQ - Claims API Router
"""
import base64
import io
import logging
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, File, Header, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import AuthContext, require_role
from app.core.config import get_settings
from app.db.database import get_db
from app.schemas.claim import (
    AuditLogExportItem,
    AuditLogExportResponse,
    ChecklistItem,
    ClaimResult,
    EmailIngestRequest,
    FeedbackRequest,
    FeedbackResponse,
    Flag,
    ProviderHealthResponse,
    ScoreBreakdown,
    TelemetryDashboardResponse,
    TimelineEvent,
    TriageUpdateRequest,
    TriageUpdateResponse,
    UploadResponse,
    UsageStats,
)
from app.services.audit_service import export_audit_logs, write_audit_log
from app.services.claim_service import (
    add_feedback,
    create_claim_with_idempotency,
    get_claim,
    get_provider_health_metrics,
    get_telemetry_dashboard,
    get_usage,
    update_triage_status,
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
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    auth: AuthContext = Depends(require_role("broker")),
    db: AsyncSession = Depends(get_db),
):
    ext = Path(file.filename or "").suffix.lower().lstrip(".")
    if ext not in settings.allowed_extensions_set:
        raise HTTPException(
            status_code=400,
            detail=f"File extension '.{ext}' is not supported.",
        )

    file_bytes = await file.read()
    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > settings.max_file_size_mb:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({size_mb:.1f} MB). Max: {settings.max_file_size_mb} MB.",
        )

    content_type = file.content_type or f"image/{ext}"
    try:
        claim, replayed = await create_claim_with_idempotency(
            file_bytes=file_bytes,
            filename=file.filename or f"upload.{ext}",
            content_type=content_type,
            session_id=session_id,
            db=db,
            endpoint="claims_upload",
            idempotency_key=idempotency_key,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    await write_audit_log(
        db,
        actor_user=auth.user_id,
        actor_role=auth.role,
        action="claim.upload",
        resource_type="claim",
        resource_id=claim.id,
        details={
            "status": claim.status,
            "replayed": replayed,
            "idempotency_key_present": bool(idempotency_key),
        },
    )
    await db.commit()

    if replayed:
        message = "Idempotent replay; returning existing claim."
    else:
        message = "Claim accepted and queued for processing."
    return UploadResponse(claim_id=claim.id, status=claim.status, message=message)


@router.post("/ingest/email", response_model=UploadResponse)
async def ingest_email_claim(
    payload: EmailIngestRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    auth: AuthContext = Depends(require_role("broker")),
    db: AsyncSession = Depends(get_db),
):
    ext = Path(payload.filename or "").suffix.lower().lstrip(".")
    if ext not in settings.allowed_extensions_set:
        raise HTTPException(status_code=400, detail="Unsupported file extension.")
    try:
        file_bytes = base64.b64decode(payload.document_base64, validate=True)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid base64 attachment.") from exc

    try:
        claim, replayed = await create_claim_with_idempotency(
            file_bytes=file_bytes,
            filename=payload.filename,
            content_type=payload.content_type,
            session_id=payload.session_id,
            db=db,
            endpoint="claims_ingest_email",
            idempotency_key=idempotency_key,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    await write_audit_log(
        db,
        actor_user=auth.user_id,
        actor_role=auth.role,
        action="claim.ingest_email",
        resource_type="claim",
        resource_id=claim.id,
        details={"status": claim.status, "replayed": replayed},
    )
    await db.commit()

    message = (
        "Idempotent replay; returning existing claim."
        if replayed
        else "Claim ingested from email and queued for processing."
    )
    return UploadResponse(claim_id=claim.id, status=claim.status, message=message)


@router.get("/usage", response_model=UsageStats)
async def usage_stats(
    _: AuthContext = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    usage = await get_usage(db)
    if not usage:
        month = datetime.now(timezone.utc).strftime("%Y-%m")
        return UsageStats(
            month=month,
            total_claims_processed=0,
            azure_vision_calls=0,
            azure_vision_monthly_limit=settings.azure_vision_monthly_limit,
            total_ocr_fallbacks=0,
            llm_gemini_calls=0,
            llm_openrouter_calls=0,
            total_llm_fallbacks=0,
        )
    return UsageStats(
        month=usage.month,
        total_claims_processed=usage.total_claims_processed or 0,
        azure_vision_calls=usage.azure_vision_calls or 0,
        azure_vision_monthly_limit=settings.azure_vision_monthly_limit,
        total_ocr_fallbacks=usage.total_ocr_fallbacks or 0,
        llm_gemini_calls=usage.llm_gemini_calls or 0,
        llm_openrouter_calls=usage.llm_openrouter_calls or 0,
        total_llm_fallbacks=usage.total_llm_fallbacks or 0,
    )


@router.get("/metrics/providers", response_model=ProviderHealthResponse)
async def provider_metrics(
    lookback_hours: int = Query(default=settings.telemetry_lookback_hours, ge=1, le=168),
    _: AuthContext = Depends(require_role("lead")),
    db: AsyncSession = Depends(get_db),
):
    return await get_provider_health_metrics(db, lookback_hours=lookback_hours)


@router.get("/metrics/dashboard", response_model=TelemetryDashboardResponse)
async def telemetry_dashboard(
    lookback_hours: int = Query(default=settings.telemetry_lookback_hours, ge=1, le=168),
    _: AuthContext = Depends(require_role("lead")),
    db: AsyncSession = Depends(get_db),
):
    return await get_telemetry_dashboard(db, lookback_hours=lookback_hours)


@router.get("/audit/export", response_model=AuditLogExportResponse)
async def audit_export(
    days: int = Query(default=7, ge=1, le=90),
    limit: int = Query(default=1000, ge=1, le=5000),
    auth: AuthContext = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    to_at = datetime.now(timezone.utc)
    from_at = to_at - timedelta(days=days)
    rows = await export_audit_logs(db, from_at=from_at, to_at=to_at, limit=limit)
    return AuditLogExportResponse(
        retention_days=settings.audit_retention_days,
        from_at=from_at,
        to_at=to_at,
        total_rows=len(rows),
        rows=[
            AuditLogExportItem(
                created_at=row.created_at,
                actor_user=row.actor_user,
                actor_role=row.actor_role,
                action=row.action,
                resource_type=row.resource_type,
                resource_id=row.resource_id,
                details=row.details or {},
            )
            for row in rows
        ],
    )


@router.get("/{claim_id}", response_model=ClaimResult)
async def get_claim_result(
    claim_id: str,
    _: AuthContext = Depends(require_role("broker")),
    db: AsyncSession = Depends(get_db),
):
    claim = await get_claim(claim_id, db)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found.")

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
        field_confidence=claim.field_confidence,
        followup_draft=claim.followup_draft,
        claim_vertical=claim.claim_vertical,
        triage_status=claim.triage_status,
        readiness_score=claim.readiness_score,
        score_breakdown=score_breakdown,
        flags=flags,
        action_checklist=checklist,
        suggestion=claim.suggestion,
        ocr_engine=claim.ocr_engine,
        error_message=claim.error_message,
        timeline_events=[TimelineEvent(**e) for e in (claim.timeline_events or [])],
    )


@router.post("/{claim_id}/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    claim_id: str,
    feedback: FeedbackRequest,
    auth: AuthContext = Depends(require_role("broker")),
    db: AsyncSession = Depends(get_db),
):
    success = await add_feedback(claim_id, feedback, db)
    if not success:
        raise HTTPException(status_code=404, detail="Claim not found.")

    await write_audit_log(
        db,
        actor_user=auth.user_id,
        actor_role=auth.role,
        action="claim.feedback",
        resource_type="claim",
        resource_id=claim_id,
        details={"field_corrected": feedback.field_corrected or ""},
    )
    await db.commit()
    return FeedbackResponse()


@router.patch("/{claim_id}/triage", response_model=TriageUpdateResponse)
async def patch_triage_status(
    claim_id: str,
    payload: TriageUpdateRequest,
    auth: AuthContext = Depends(require_role("lead")),
    db: AsyncSession = Depends(get_db),
):
    try:
        claim = await update_triage_status(claim_id, payload, db)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found.")

    await write_audit_log(
        db,
        actor_user=auth.user_id,
        actor_role=auth.role,
        action="claim.triage_update",
        resource_type="claim",
        resource_id=claim.id,
        details={"triage_status": claim.triage_status, "note": payload.note or ""},
    )
    await db.commit()
    return TriageUpdateResponse(
        claim_id=claim.id,
        triage_status=claim.triage_status or "review",
        message="Triage status updated.",
    )


@router.get("/{claim_id}/pdf")
async def download_pdf(
    claim_id: str,
    _: AuthContext = Depends(require_role("broker")),
    db: AsyncSession = Depends(get_db),
):
    claim = await get_claim(claim_id, db)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found.")
    if claim.status != "done":
        raise HTTPException(
            status_code=400, detail="Claim is not fully processed yet."
        )

    score_breakdown = None
    if claim.score_completeness is not None:
        score_breakdown = ScoreBreakdown(
            completeness=claim.score_completeness,
            consistency=claim.score_consistency,
            fraud_signals=claim.score_fraud_signals,
            documentation=claim.score_documentation,
        )

    pdf_bytes = generate_claim_pdf(
        {
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
        }
    )

    safe_id = claim.id[:8]
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="ClaimIQ_Claim_{safe_id}.pdf"'
        },
    )
