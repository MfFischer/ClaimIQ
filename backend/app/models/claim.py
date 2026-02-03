"""
ClaimIQ — Database Models
Tables: claims, usage_tracking, feedback_log
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, Integer, Float, JSON, DateTime, ForeignKey
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
    summary: Mapped[str] = mapped_column(Text, nullable=True)
    summary_de: Mapped[str] = mapped_column(Text, nullable=True)

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
    error_message: Mapped[str] = mapped_column(Text, nullable=True)

    # Relations
    feedback: Mapped[list["FeedbackLog"]] = relationship(
        "FeedbackLog", back_populates="claim"
    )


class UsageTracking(Base):
    __tablename__ = "usage_tracking"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    month: Mapped[str] = mapped_column(String(7), nullable=False, index=True)
    google_vision_calls: Mapped[int] = mapped_column(Integer, default=0)
    total_claims_processed: Mapped[int] = mapped_column(Integer, default=0)
    total_ocr_fallbacks: Mapped[int] = mapped_column(Integer, default=0)
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
