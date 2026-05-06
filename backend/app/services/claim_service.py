"""
ClaimIQ - Claim orchestration and production-hardening services.
"""
import hashlib
import logging
from datetime import datetime, timedelta, timezone
from time import perf_counter

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.claim import (
    Claim,
    FeedbackLog,
    IdempotencyKey,
    ProcessingJob,
    ProcessingMetric,
    UsageTracking,
)
from app.schemas.claim import FeedbackRequest, TriageUpdateRequest
from app.services.ai_service import LLMNonRetriableError, process_kfz_claim
from app.services.ocr_service import extract_text
from app.services.storage_service import load_file, save_file

logger = logging.getLogger(__name__)
settings = get_settings()
VALID_TRIAGE_STATUSES = {"ready", "needs_info", "review", "escalate"}


def _append_timeline_event(
    claim: Claim, event_type: str, message: str, metadata: dict | None = None
):
    events = list(claim.timeline_events or [])
    events.append(
        {
            "at": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "message": message,
            "metadata": metadata or {},
        }
    )
    claim.timeline_events = events


def _triage_from_suggestion(suggestion: str) -> str:
    mapping = {
        "approve": "ready",
        "review": "review",
        "reject": "escalate",
    }
    return mapping.get(suggestion, "review")


def _estimate_field_confidence(
    structured_data: dict, ocr_confidence: float | None
) -> dict[str, float]:
    base = float(ocr_confidence if ocr_confidence is not None else 0.8)
    confidence: dict[str, float] = {}
    for key, value in structured_data.items():
        if value in (None, "", []):
            confidence[key] = round(max(0.0, base - 0.35), 2)
        elif isinstance(value, bool):
            confidence[key] = round(min(0.98, base + 0.08), 2)
        elif isinstance(value, str) and len(value) < 4:
            confidence[key] = round(max(0.4, base - 0.15), 2)
        else:
            confidence[key] = round(min(0.99, base + 0.05), 2)
    return confidence


def _build_followup_draft(checklist: list[dict], lang: str = "de") -> str:
    required = [
        (item.get("item_de") if lang == "de" else item.get("item") or "")
        for item in checklist
        if item.get("required")
    ]
    optional = [
        (item.get("item_de") if lang == "de" else item.get("item") or "")
        for item in checklist
        if not item.get("required")
    ]
    if lang == "de":
        req_lines = "\n".join(f"- {r}" for r in required) or "- Keine"
        opt_lines = "\n".join(f"- {o}" for o in optional) or "- Keine"
        return (
            "Betreff: Nachforderung zu Ihrem Kfz-Schadenfall\n\n"
            "Guten Tag,\n\n"
            "fur die weitere Bearbeitung Ihres Schadenfalls benotigen wir bitte noch folgende Unterlagen:\n\n"
            f"{req_lines}\n\n"
            "Optional hilfreich:\n"
            f"{opt_lines}\n\n"
            "Vielen Dank fur Ihre Unterstutzung."
        )
    req_lines = "\n".join(f"- {r}" for r in required) or "- None"
    opt_lines = "\n".join(f"- {o}" for o in optional) or "- None"
    return (
        "Subject: Additional documents required for your vehicle claim\n\n"
        "Hello,\n\n"
        "To continue processing your claim, please provide:\n\n"
        f"{req_lines}\n\n"
        "Optional but helpful:\n"
        f"{opt_lines}\n\n"
        "Thank you."
    )


def _request_hash(
    *,
    file_bytes: bytes,
    filename: str,
    content_type: str,
    session_id: str,
) -> str:
    hasher = hashlib.sha256()
    hasher.update(file_bytes)
    hasher.update(filename.encode("utf-8"))
    hasher.update(content_type.encode("utf-8"))
    hasher.update(session_id.encode("utf-8"))
    return hasher.hexdigest()


def _estimate_claim_cost(provider: str, fallback_used: bool) -> float:
    if provider == "gemini":
        base = settings.llm_gemini_estimated_cost_usd
    elif provider == "openrouter":
        base = settings.llm_openrouter_estimated_cost_usd
    else:
        base = 0.0
    if fallback_used:
        base *= settings.llm_fallback_cost_multiplier
    return round(base, 6)


def _latency_percentile(values: list[int], percentile: float) -> int:
    if not values:
        return 0
    ordered = sorted(values)
    idx = int((len(ordered) - 1) * percentile)
    return ordered[idx]


def _is_non_retriable_error(exc: Exception) -> bool:
    return isinstance(exc, (LLMNonRetriableError, ValueError))


async def create_claim(
    file_bytes: bytes,
    filename: str,
    content_type: str,
    session_id: str,
    db: AsyncSession,
) -> Claim:
    claim, _ = await create_claim_with_idempotency(
        file_bytes=file_bytes,
        filename=filename,
        content_type=content_type,
        session_id=session_id,
        db=db,
        endpoint="claims_upload",
        idempotency_key=None,
    )
    return claim


async def create_claim_with_idempotency(
    *,
    file_bytes: bytes,
    filename: str,
    content_type: str,
    session_id: str,
    db: AsyncSession,
    endpoint: str,
    idempotency_key: str | None = None,
) -> tuple[Claim, bool]:
    request_hash = _request_hash(
        file_bytes=file_bytes,
        filename=filename,
        content_type=content_type,
        session_id=session_id,
    )

    if idempotency_key:
        existing_claim = await _resolve_idempotency_claim(
            db=db,
            endpoint=endpoint,
            idempotency_key=idempotency_key,
            request_hash=request_hash,
        )
        if existing_claim:
            return existing_claim, True

    file_url = await save_file(file_bytes, filename)
    claim = Claim(
        session_id=session_id,
        file_name=filename,
        file_type=content_type,
        file_url=file_url,
        status="queued",
        triage_status="review",
        claim_vertical="kfz",
        timeline_events=[],
    )
    _append_timeline_event(
        claim,
        event_type="claim_received",
        message="Claim document received.",
        metadata={"filename": filename, "content_type": content_type},
    )
    _append_timeline_event(
        claim,
        event_type="claim_queued",
        message="Claim queued for asynchronous processing.",
        metadata={"worker_enabled": settings.worker_enabled},
    )

    db.add(claim)
    await db.flush()
    db.add(
        ProcessingJob(
            claim_id=claim.id,
            status="queued",
            attempt_count=0,
            max_attempts=settings.worker_max_attempts,
        )
    )

    if idempotency_key:
        ttl = datetime.now(timezone.utc) + timedelta(hours=settings.idempotency_ttl_hours)
        db.add(
            IdempotencyKey(
                endpoint=endpoint,
                idempotency_key=idempotency_key,
                request_hash=request_hash,
                claim_id=claim.id,
                expires_at=ttl,
            )
        )

    await db.commit()
    await db.refresh(claim)
    return claim, False


async def _resolve_idempotency_claim(
    *,
    db: AsyncSession,
    endpoint: str,
    idempotency_key: str,
    request_hash: str,
) -> Claim | None:
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(IdempotencyKey).where(
            IdempotencyKey.endpoint == endpoint,
            IdempotencyKey.idempotency_key == idempotency_key,
            IdempotencyKey.expires_at > now,
        )
    )
    token = result.scalar_one_or_none()
    if not token:
        return None
    if token.request_hash != request_hash:
        raise ValueError(
            "Idempotency key was already used with a different request payload."
        )
    return await get_claim(token.claim_id, db)


async def process_next_queue_job(db: AsyncSession) -> bool:
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(ProcessingJob)
        .where(
            ProcessingJob.status == "queued",
            (ProcessingJob.next_retry_at.is_(None)) | (ProcessingJob.next_retry_at <= now),
        )
        .order_by(ProcessingJob.created_at.asc())
        .limit(1)
    )
    job = result.scalar_one_or_none()
    if not job:
        return False
    await _process_job(job.id, db)
    return True


async def _process_job(job_id: str, db: AsyncSession):
    result = await db.execute(select(ProcessingJob).where(ProcessingJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        return

    claim = await get_claim(job.claim_id, db)
    if not claim:
        job.status = "dead_letter"
        job.last_error = "Claim record missing."
        await db.commit()
        return

    started = perf_counter()
    job.status = "processing"
    job.locked_at = datetime.now(timezone.utc)
    job.attempt_count = (job.attempt_count or 0) + 1
    await db.commit()

    provider = ""
    fallback_used = False
    try:
        provider, fallback_used = await _run_claim_pipeline(claim, db)
        job.status = "done"
        job.last_error = None
        job.next_retry_at = None
        job.locked_at = None
        latency_ms = int((perf_counter() - started) * 1000)
        db.add(
            ProcessingMetric(
                claim_id=claim.id,
                provider=provider,
                llm_fallback_used=fallback_used,
                success=True,
                latency_ms=max(1, latency_ms),
                estimated_cost_usd=_estimate_claim_cost(provider, fallback_used),
                attempt_count=job.attempt_count,
            )
        )
        await db.commit()
    except Exception as exc:
        non_retriable = _is_non_retriable_error(exc)
        exhausted = job.attempt_count >= job.max_attempts
        dead_letter = non_retriable or exhausted

        claim.status = "error" if dead_letter else "queued"
        claim.triage_status = "escalate" if dead_letter else "needs_info"
        claim.error_message = str(exc)
        job.last_error = str(exc)
        job.locked_at = None

        if dead_letter:
            job.status = "dead_letter"
            _append_timeline_event(
                claim,
                event_type="dead_lettered",
                message="Claim moved to dead-letter queue after processing failures.",
                metadata={"attempt_count": job.attempt_count, "error": str(exc)},
            )
        else:
            delay = settings.worker_retry_backoff_seconds * max(1, job.attempt_count)
            job.status = "queued"
            job.next_retry_at = datetime.now(timezone.utc) + timedelta(seconds=delay)
            _append_timeline_event(
                claim,
                event_type="retry_scheduled",
                message="Claim processing failed; retry scheduled.",
                metadata={
                    "attempt_count": job.attempt_count,
                    "retry_in_seconds": delay,
                    "error": str(exc),
                },
            )

        latency_ms = int((perf_counter() - started) * 1000)
        db.add(
            ProcessingMetric(
                claim_id=claim.id,
                provider=provider or "unknown",
                llm_fallback_used=fallback_used,
                success=False,
                latency_ms=max(1, latency_ms),
                estimated_cost_usd=0.0,
                attempt_count=job.attempt_count,
                error_category=exc.__class__.__name__,
            )
        )
        await db.commit()
        logger.error("Claim %s processing failed: %s", claim.id, exc, exc_info=True)


async def _run_claim_pipeline(claim: Claim, db: AsyncSession) -> tuple[str, bool]:
    file_bytes = await load_file(claim.file_url)
    content_type = claim.file_type or "application/octet-stream"

    ocr = await extract_text(file_bytes, content_type)
    claim.raw_text = ocr.text
    claim.ocr_engine = ocr.engine
    claim.ocr_confidence = ocr.confidence
    _append_timeline_event(
        claim,
        event_type="ocr_completed",
        message="OCR extraction finished.",
        metadata={"ocr_engine": ocr.engine, "ocr_confidence": ocr.confidence},
    )

    if not ocr.text.strip() and not settings.mock_mode:
        raise ValueError(
            "OCR returned no extractable text. Please verify image quality."
        )

    ai = await process_kfz_claim(ocr.text)
    _append_timeline_event(
        claim,
        event_type="ai_completed",
        message="AI extraction and scoring completed.",
        metadata={
            "llm_provider": ai.llm_provider,
            "llm_fallback_used": ai.llm_fallback_used,
        },
    )

    claim.structured_data = ai.structured_data
    claim.field_confidence = _estimate_field_confidence(
        ai.structured_data, claim.ocr_confidence
    )
    claim.summary = ai.summary
    claim.summary_de = ai.summary_de
    claim.readiness_score = ai.readiness_score
    claim.score_completeness = ai.score_breakdown.completeness
    claim.score_consistency = ai.score_breakdown.consistency
    claim.score_fraud_signals = ai.score_breakdown.fraud_signals
    claim.score_documentation = ai.score_breakdown.documentation
    claim.flags = [f.model_dump() for f in ai.flags]
    claim.action_checklist = [c.model_dump() for c in ai.action_checklist]
    claim.followup_draft = _build_followup_draft(claim.action_checklist, lang="de")
    claim.suggestion = ai.suggestion
    claim.status = "done"
    claim.triage_status = _triage_from_suggestion(ai.suggestion)
    claim.error_message = None
    _append_timeline_event(
        claim,
        event_type="triage_assigned",
        message="Initial triage status assigned.",
        metadata={"triage_status": claim.triage_status, "suggestion": ai.suggestion},
    )

    await _track_usage(
        db,
        ocr_engine=ocr.engine,
        llm_provider=ai.llm_provider,
        llm_fallback_used=ai.llm_fallback_used,
    )
    await db.commit()
    return ai.llm_provider, ai.llm_fallback_used


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


async def update_triage_status(
    claim_id: str, payload: TriageUpdateRequest, db: AsyncSession
) -> Claim | None:
    claim = await get_claim(claim_id, db)
    if not claim:
        return None
    if payload.triage_status not in VALID_TRIAGE_STATUSES:
        raise ValueError("Invalid triage_status")
    previous = claim.triage_status
    claim.triage_status = payload.triage_status
    _append_timeline_event(
        claim,
        event_type="triage_updated",
        message="Triage status manually updated by ops.",
        metadata={
            "from": previous,
            "to": payload.triage_status,
            "note": payload.note or "",
        },
    )
    await db.commit()
    await db.refresh(claim)
    return claim


async def get_usage(db: AsyncSession) -> UsageTracking | None:
    month = datetime.now(timezone.utc).strftime("%Y-%m")
    result = await db.execute(
        select(UsageTracking).where(UsageTracking.month == month)
    )
    return result.scalar_one_or_none()


async def _track_usage(
    db: AsyncSession,
    ocr_engine: str,
    llm_provider: str,
    llm_fallback_used: bool,
):
    month = datetime.now(timezone.utc).strftime("%Y-%m")
    result = await db.execute(
        select(UsageTracking).where(UsageTracking.month == month)
    )
    usage = result.scalar_one_or_none()
    if not usage:
        usage = UsageTracking(month=month)
        db.add(usage)

    usage.total_claims_processed = (usage.total_claims_processed or 0) + 1
    if ocr_engine == "azure_vision":
        usage.azure_vision_calls = (usage.azure_vision_calls or 0) + 1
        usage.total_ocr_fallbacks = (usage.total_ocr_fallbacks or 0) + 1
    if llm_provider == "gemini":
        usage.llm_gemini_calls = (usage.llm_gemini_calls or 0) + 1
    if llm_provider == "openrouter":
        usage.llm_openrouter_calls = (usage.llm_openrouter_calls or 0) + 1
    if llm_fallback_used:
        usage.total_llm_fallbacks = (usage.total_llm_fallbacks or 0) + 1


async def get_provider_health_metrics(
    db: AsyncSession, lookback_hours: int | None = None
) -> dict:
    hours = lookback_hours or settings.telemetry_lookback_hours
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    result = await db.execute(
        select(ProcessingMetric).where(ProcessingMetric.created_at >= since)
    )
    rows = list(result.scalars().all())
    providers = {"gemini", "openrouter", "mock", "unknown"}
    health = {}
    for provider in providers:
        items = [r for r in rows if (r.provider or "unknown") == provider]
        total = len(items)
        failures = len([r for r in items if not r.success])
        fallbacks = len([r for r in items if r.llm_fallback_used])
        success_rate = round((total - failures) / total, 4) if total else 0.0
        fallback_rate = round(fallbacks / total, 4) if total else 0.0
        if total == 0:
            status = "unknown"
        elif success_rate >= 0.97:
            status = "healthy"
        elif success_rate >= 0.9:
            status = "degraded"
        else:
            status = "unhealthy"
        health[provider] = {
            "status": status,
            "requests": total,
            "failures": failures,
            "success_rate": success_rate,
            "fallback_rate": fallback_rate,
        }
    return {"lookback_hours": hours, "providers": health}


async def get_telemetry_dashboard(
    db: AsyncSession, lookback_hours: int | None = None
) -> dict:
    hours = lookback_hours or settings.telemetry_lookback_hours
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    result = await db.execute(
        select(ProcessingMetric).where(ProcessingMetric.created_at >= since)
    )
    rows = list(result.scalars().all())
    successes = [r for r in rows if r.success]
    latencies = [r.latency_ms for r in successes]
    fallback_count = len([r for r in successes if r.llm_fallback_used])
    total = len(rows)
    throughput_per_hour = round(total / max(hours, 1), 2)
    total_cost = round(sum(r.estimated_cost_usd for r in rows), 6)
    return {
        "lookback_hours": hours,
        "total_jobs": total,
        "successful_jobs": len(successes),
        "failed_jobs": total - len(successes),
        "throughput_per_hour": throughput_per_hour,
        "latency_ms_avg": int(sum(latencies) / len(latencies)) if latencies else 0,
        "latency_ms_p95": _latency_percentile(latencies, 0.95),
        "fallback_rate": round(fallback_count / len(successes), 4) if successes else 0.0,
        "estimated_cost_usd": total_cost,
    }


async def cleanup_expired_idempotency_keys(db: AsyncSession) -> int:
    now = datetime.now(timezone.utc)
    result = await db.execute(
        delete(IdempotencyKey).where(IdempotencyKey.expires_at <= now)
    )
    await db.commit()
    return result.rowcount or 0
