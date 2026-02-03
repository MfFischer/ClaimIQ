"""
ClaimIQ — API Schemas (Pydantic v2)
All request/response models for the API.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ── Nested output structures ───────────────────────────────────────────────────

class ScoreBreakdown(BaseModel):
    completeness: int = Field(ge=0, le=100)
    consistency: int = Field(ge=0, le=100)
    fraud_signals: int = Field(ge=0, le=100)
    documentation: int = Field(ge=0, le=100)


class Flag(BaseModel):
    field: str = ""
    message: str = ""
    message_de: str = ""
    severity: str = "warning"  # error | warning | info


class ChecklistItem(BaseModel):
    item: str = ""
    item_de: str = ""
    required: bool = True


# ── Upload ────────────────────────────────────────────────────────────────────

class UploadResponse(BaseModel):
    claim_id: str
    status: str
    message: str


# ── Claim result ──────────────────────────────────────────────────────────────

class ClaimResult(BaseModel):
    claim_id: str
    status: str
    created_at: datetime
    claim_vertical: str = "kfz"

    summary: Optional[str] = None
    summary_de: Optional[str] = None
    structured_data: Optional[dict] = None

    readiness_score: Optional[int] = None
    score_breakdown: Optional[ScoreBreakdown] = None

    flags: Optional[list[Flag]] = None
    action_checklist: Optional[list[ChecklistItem]] = None
    suggestion: Optional[str] = None

    ocr_engine: Optional[str] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


# ── Feedback ──────────────────────────────────────────────────────────────────

class FeedbackRequest(BaseModel):
    field_corrected: Optional[str] = None
    original_value: Optional[str] = None
    corrected_value: Optional[str] = None
    general_comment: Optional[str] = None


class FeedbackResponse(BaseModel):
    message: str = "Vielen Dank für Ihr Feedback!"


# ── Usage (admin) ─────────────────────────────────────────────────────────────

class UsageStats(BaseModel):
    month: str
    total_claims_processed: int
    google_vision_calls: int
    google_vision_limit: int
    total_ocr_fallbacks: int
