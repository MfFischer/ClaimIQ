"""
ClaimIQ — Database Models
Tables: claims, usage_tracking, feedback_log
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    String,
    Text,
    Integer,
    Float,
    JSON,
    DateTime,
    ForeignKey,
    Boolean,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Claim(Base):
    __tablename__ = "claims"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    # Session — no login required for MVP
    session_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    # File info
    file_url: Mapped[str] = mapped_column(String(512), nullable=False)
    file_name: Mapped[str] = mapped_column(String(256), nullable=True)
    file_type: Mapped[str] = mapped_column(String(64), nullable=True)

    # Claim type
    claim_vertical: Mapped[str] = mapped_column(String(64), default="kfz")

    # OCR results
    raw_text: Mapped[str] = mapped_column(Text, nullable=True)
    ocr_engine: Mapped[str] = mapped_column(String(32), nullable=True)
    ocr_confidence: Mapped[float] = mapped_column(Float, nullable=True)

    # AI outputs
    structured_data: Mapped[dict] = mapped_column(JSON, nullable=True)
    field_confidence: Mapped[dict] = mapped_column(JSON, nullable=True)
    summary: Mapped[str] = mapped_column(Text, nullable=True)
    summary_de: Mapped[str] = mapped_column(Text, nullable=True)
    followup_draft: Mapped[str] = mapped_column(Text, nullable=True)

    # Claim Readiness Score
    readiness_score: Mapped[int] = mapped_column(Integer, nullable=True)
    score_completeness: Mapped[int] = mapped_column(Integer, nullable=True)
    score_consistency: Mapped[int] = mapped_column(Integer, nullable=True)
    score_fraud_signals: Mapped[int] = mapped_column(Integer, nullable=True)
    score_documentation: Mapped[int] = mapped_column(Integer, nullable=True)

    # Flags + checklist + suggestion
    flags: Mapped[list] = mapped_column(JSON, nullable=True)
    action_checklist: Mapped[list] = mapped_column(JSON, nullable=True)
    suggestion: Mapped[str] = mapped_column(String(32), nullable=True)

    # Status
    status: Mapped[str] = mapped_column(String(32), default="pending")
    triage_status: Mapped[str] = mapped_column(String(32), default="review")
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    timeline_events: Mapped[list] = mapped_column(JSON, default=list)

    # Relations
    feedback: Mapped[list["FeedbackLog"]] = relationship(
        "FeedbackLog", back_populates="claim"
    )


class UsageTracking(Base):
    __tablename__ = "usage_tracking"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    month: Mapped[str] = mapped_column(String(7), nullable=False, index=True)
    azure_vision_calls: Mapped[int] = mapped_column(Integer, default=0)
    total_claims_processed: Mapped[int] = mapped_column(Integer, default=0)
    total_ocr_fallbacks: Mapped[int] = mapped_column(Integer, default=0)
    llm_gemini_calls: Mapped[int] = mapped_column(Integer, default=0)
    llm_openrouter_calls: Mapped[int] = mapped_column(Integer, default=0)
    total_llm_fallbacks: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )


class FeedbackLog(Base):
    __tablename__ = "feedback_log"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    claim_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("claims.id"), nullable=False
    )
    field_corrected: Mapped[str] = mapped_column(String(128), nullable=True)
    original_value: Mapped[str] = mapped_column(Text, nullable=True)
    corrected_value: Mapped[str] = mapped_column(Text, nullable=True)
    general_comment: Mapped[str] = mapped_column(Text, nullable=True)

    claim: Mapped["Claim"] = relationship("Claim", back_populates="feedback")


class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    claim_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("claims.id"), nullable=False, unique=True, index=True
    )
    status: Mapped[str] = mapped_column(String(32), default="queued", index=True)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)
    last_error: Mapped[str] = mapped_column(Text, nullable=True)
    next_retry_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    locked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )


class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"
    __table_args__ = (
        UniqueConstraint("endpoint", "idempotency_key", name="uq_endpoint_idempotency_key"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    endpoint: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    claim_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("claims.id"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ProcessingMetric(Base):
    __tablename__ = "processing_metrics"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    claim_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("claims.id"), nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(String(32), nullable=True, index=True)
    llm_fallback_used: Mapped[bool] = mapped_column(Boolean, default=False)
    success: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    estimated_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    attempt_count: Mapped[int] = mapped_column(Integer, default=1)
    error_category: Mapped[str] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, index=True)
    actor_user: Mapped[str] = mapped_column(String(128), nullable=False)
    actor_role: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_id: Mapped[str] = mapped_column(String(128), nullable=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
