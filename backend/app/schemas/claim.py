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


class TimelineEvent(BaseModel):
    at: datetime
    event_type: str
    message: str
    metadata: dict = Field(default_factory=dict)


# ── Upload ────────────────────────────────────────────────────────────────────

class UploadResponse(BaseModel):
    claim_id: str
    status: str
    message: str


class EmailIngestRequest(BaseModel):
    session_id: str
    filename: str
    content_type: str
    document_base64: str
    source_email: Optional[str] = None
    subject: Optional[str] = None


# ── Claim result ──────────────────────────────────────────────────────────────

class ClaimResult(BaseModel):
    claim_id: str
    status: str
    created_at: datetime
    claim_vertical: str = "kfz"
    triage_status: Optional[str] = None

    summary: Optional[str] = None
    summary_de: Optional[str] = None
    structured_data: Optional[dict] = None
    field_confidence: Optional[dict[str, float]] = None
    followup_draft: Optional[str] = None

    readiness_score: Optional[int] = None
    score_breakdown: Optional[ScoreBreakdown] = None

    flags: Optional[list[Flag]] = None
    action_checklist: Optional[list[ChecklistItem]] = None
    suggestion: Optional[str] = None

    ocr_engine: Optional[str] = None
    error_message: Optional[str] = None
    timeline_events: Optional[list[TimelineEvent]] = None

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


# ── Triage ────────────────────────────────────────────────────────────────────

class TriageUpdateRequest(BaseModel):
    triage_status: str = Field(pattern="^(ready|needs_info|review|escalate)$")
    note: Optional[str] = None


class TriageUpdateResponse(BaseModel):
    claim_id: str
    triage_status: str
    message: str


# ── Usage (admin) ─────────────────────────────────────────────────────────────

class UsageStats(BaseModel):
    month: str
    total_claims_processed: int
    azure_vision_calls: int
    azure_vision_monthly_limit: int
    total_ocr_fallbacks: int
    llm_gemini_calls: int
    llm_openrouter_calls: int
    total_llm_fallbacks: int


class ProviderHealthMetrics(BaseModel):
    status: str
    requests: int
    failures: int
    success_rate: float
    fallback_rate: float


class ProviderHealthResponse(BaseModel):
    lookback_hours: int
    providers: dict[str, ProviderHealthMetrics]


class TelemetryDashboardResponse(BaseModel):
    lookback_hours: int
    total_jobs: int
    successful_jobs: int
    failed_jobs: int
    throughput_per_hour: float
    latency_ms_avg: int
    latency_ms_p95: int
    fallback_rate: float
    estimated_cost_usd: float


class AuditLogExportItem(BaseModel):
    created_at: datetime
    actor_user: str
    actor_role: str
    action: str
    resource_type: str
    resource_id: str
    details: dict


class AuditLogExportResponse(BaseModel):
    retention_days: int
    from_at: datetime
    to_at: datetime
    total_rows: int
    rows: list[AuditLogExportItem]
