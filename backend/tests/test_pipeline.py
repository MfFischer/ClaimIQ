import base64
import os
import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

TEST_DB_NAME = f"claimiq_test_{uuid.uuid4().hex}"
os.environ["DATABASE_URL"] = (
    f"sqlite+aiosqlite:///file:{TEST_DB_NAME}?mode=memory&cache=shared"
)
os.environ["WORKER_ENABLED"] = "false"

from app.main import app
from app.models.claim import ProcessingJob
from app.schemas.claim import ScoreBreakdown
from app.services import ai_service, claim_service
from app.db.database import AsyncSessionLocal, init_db


def auth_headers(role: str = "broker", user: str = "test-user") -> dict[str, str]:
    return {"X-ClaimIQ-Role": role, "X-ClaimIQ-User": user}


def minimal_pdf_bytes(text: str = "Kfz Schaden Test") -> bytes:
    return (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R"
        b"/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj\n"
        b"4 0 obj<</Length 44>>stream\nBT /F1 12 Tf 100 700 Td"
        + f"({text})".encode("utf-8")
        + b" Tj ET\nendstream\nendobj\n"
        b"5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
        b"xref\n0 6\n0000000000 65535 f \n"
        b"trailer<</Size 6/Root 1 0 R>>\nstartxref\n0\n%%EOF"
    )


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _initialize_database():
    await init_db()


@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_upload_pdf_queues():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post(
            "/api/v1/claims/upload",
            files={"file": ("test_schaden.pdf", minimal_pdf_bytes(), "application/pdf")},
            headers=auth_headers("broker"),
        )
    assert r.status_code == 200
    data = r.json()
    assert "claim_id" in data
    assert data["status"] in ("queued", "done", "error")


@pytest.mark.asyncio
async def test_upload_idempotency_replay():
    key = "upload-replay-key-1"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        first = await client.post(
            "/api/v1/claims/upload",
            files={"file": ("idem.pdf", minimal_pdf_bytes("A"), "application/pdf")},
            headers={**auth_headers("broker"), "Idempotency-Key": key},
        )
        second = await client.post(
            "/api/v1/claims/upload",
            files={"file": ("idem.pdf", minimal_pdf_bytes("A"), "application/pdf")},
            headers={**auth_headers("broker"), "Idempotency-Key": key},
        )
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["claim_id"] == second.json()["claim_id"]


@pytest.mark.asyncio
async def test_upload_idempotency_conflict():
    key = "upload-conflict-key-1"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        first = await client.post(
            "/api/v1/claims/upload",
            files={"file": ("idem.pdf", minimal_pdf_bytes("A"), "application/pdf")},
            headers={**auth_headers("broker"), "Idempotency-Key": key},
        )
        second = await client.post(
            "/api/v1/claims/upload",
            files={"file": ("idem.pdf", minimal_pdf_bytes("B"), "application/pdf")},
            headers={**auth_headers("broker"), "Idempotency-Key": key},
        )
    assert first.status_code == 200
    assert second.status_code == 409


@pytest.mark.asyncio
async def test_get_result_not_found():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get(
            "/api/v1/claims/nonexistent-id-00000000",
            headers=auth_headers("broker"),
        )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_feedback_not_found():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post(
            "/api/v1/claims/nonexistent-id/feedback",
            json={"general_comment": "Test"},
            headers=auth_headers("broker"),
        )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_usage_requires_admin():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        forbidden = await client.get("/api/v1/claims/usage", headers=auth_headers("broker"))
        allowed = await client.get("/api/v1/claims/usage", headers=auth_headers("admin"))
    assert forbidden.status_code == 403
    assert allowed.status_code == 200


@pytest.mark.asyncio
async def test_triage_patch_requires_lead():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        upload = await client.post(
            "/api/v1/claims/upload",
            files={"file": ("triage_patch_test.pdf", minimal_pdf_bytes(), "application/pdf")},
            headers=auth_headers("broker"),
        )
        claim_id = upload.json()["claim_id"]
        forbidden = await client.patch(
            f"/api/v1/claims/{claim_id}/triage",
            json={"triage_status": "needs_info"},
            headers=auth_headers("broker"),
        )
        allowed = await client.patch(
            f"/api/v1/claims/{claim_id}/triage",
            json={"triage_status": "needs_info"},
            headers=auth_headers("lead"),
        )
    assert forbidden.status_code == 403
    assert allowed.status_code == 200


@pytest.mark.asyncio
async def test_email_ingest_endpoint_success():
    payload = {
        "session_id": "email-ingest-session",
        "filename": "mail_claim.pdf",
        "content_type": "application/pdf",
        "document_base64": base64.b64encode(minimal_pdf_bytes()).decode("utf-8"),
        "source_email": "ops@example.com",
        "subject": "Neue Schadensmeldung",
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post(
            "/api/v1/claims/ingest/email",
            json=payload,
            headers=auth_headers("broker"),
        )
    assert r.status_code == 200
    assert r.json()["status"] in ("queued", "done", "error")


@pytest.mark.asyncio
async def test_metrics_and_audit_endpoints():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        providers = await client.get(
            "/api/v1/claims/metrics/providers",
            headers=auth_headers("lead"),
        )
        dashboard = await client.get(
            "/api/v1/claims/metrics/dashboard",
            headers=auth_headers("lead"),
        )
        audit = await client.get(
            "/api/v1/claims/audit/export",
            headers=auth_headers("admin"),
        )
    assert providers.status_code == 200
    assert "providers" in providers.json()
    assert dashboard.status_code == 200
    assert "throughput_per_hour" in dashboard.json()
    assert audit.status_code == 200
    assert "rows" in audit.json()


@pytest.mark.asyncio
async def test_dead_letter_on_non_retriable_failure(monkeypatch):
    async def _always_fail(*_args, **_kwargs):
        raise ValueError("bad document")

    monkeypatch.setattr(claim_service, "_run_claim_pipeline", _always_fail)

    async with AsyncSessionLocal() as db:
        claim, _ = await claim_service.create_claim_with_idempotency(
            file_bytes=minimal_pdf_bytes(),
            filename="dead_letter.pdf",
            content_type="application/pdf",
            session_id="dlq-session",
            db=db,
            endpoint="claims_upload",
            idempotency_key=None,
        )
        worked = await claim_service.process_next_queue_job(db)
        refreshed = await claim_service.get_claim(claim.id, db)
        job_result = await db.execute(
            select(ProcessingJob).where(ProcessingJob.claim_id == claim.id)
        )
        job = job_result.scalar_one()

    assert worked is True
    assert refreshed is not None
    assert refreshed.status == "error"
    assert job.status == "dead_letter"
    assert any(
        evt.get("event_type") == "dead_lettered"
        for evt in (refreshed.timeline_events or [])
    )


@pytest.mark.asyncio
async def test_llm_fallback_gemini_success(monkeypatch):
    monkeypatch.setattr(ai_service.settings, "llm_primary_provider", "gemini")
    monkeypatch.setattr(ai_service.settings, "gemini_api_key", "test-gemini")
    monkeypatch.setattr(ai_service.settings, "openrouter_api_key", "test-openrouter")

    def _gemini_ok(_ocr_text: str):
        return ai_service.ClaimAIResult(
            structured_data={},
            summary="ok",
            summary_de="ok",
            readiness_score=80,
            score_breakdown=ScoreBreakdown(
                completeness=80, consistency=80, fraud_signals=80, documentation=80
            ),
            flags=[],
            action_checklist=[],
            suggestion="review",
        )

    monkeypatch.setattr(ai_service, "_run_gemini_pipeline", _gemini_ok)
    result = await ai_service.process_kfz_claim("test")
    assert result.llm_provider == "gemini"
    assert result.llm_fallback_used is False


@pytest.mark.asyncio
async def test_llm_fallback_openrouter_on_gemini_failure(monkeypatch):
    monkeypatch.setattr(ai_service.settings, "llm_primary_provider", "gemini")
    monkeypatch.setattr(ai_service.settings, "gemini_api_key", "test-gemini")
    monkeypatch.setattr(ai_service.settings, "openrouter_api_key", "test-openrouter")

    def _gemini_fail(_ocr_text: str):
        raise ai_service.LLMRetriableError("gemini outage")

    def _openrouter_ok(_ocr_text: str):
        return ai_service.ClaimAIResult(
            structured_data={},
            summary="ok",
            summary_de="ok",
            readiness_score=81,
            score_breakdown=ScoreBreakdown(
                completeness=81, consistency=81, fraud_signals=81, documentation=81
            ),
            flags=[],
            action_checklist=[],
            suggestion="review",
        )

    monkeypatch.setattr(ai_service, "_run_gemini_pipeline", _gemini_fail)
    monkeypatch.setattr(ai_service, "_run_openrouter_pipeline", _openrouter_ok)
    result = await ai_service.process_kfz_claim("test")
    assert result.llm_provider == "openrouter"
    assert result.llm_fallback_used is True


@pytest.mark.asyncio
async def test_llm_non_retriable_does_not_fallback(monkeypatch):
    monkeypatch.setattr(ai_service.settings, "llm_primary_provider", "gemini")
    monkeypatch.setattr(ai_service.settings, "gemini_api_key", "test-gemini")
    monkeypatch.setattr(ai_service.settings, "openrouter_api_key", "test-openrouter")

    def _gemini_non_retriable(_ocr_text: str):
        raise ai_service.LLMNonRetriableError("schema mismatch")

    def _openrouter_ok(_ocr_text: str):
        return ai_service.ClaimAIResult(
            structured_data={},
            summary="ok",
            summary_de="ok",
            readiness_score=81,
            score_breakdown=ScoreBreakdown(
                completeness=81, consistency=81, fraud_signals=81, documentation=81
            ),
            flags=[],
            action_checklist=[],
            suggestion="review",
        )

    monkeypatch.setattr(ai_service, "_run_gemini_pipeline", _gemini_non_retriable)
    monkeypatch.setattr(ai_service, "_run_openrouter_pipeline", _openrouter_ok)
    with pytest.raises(ai_service.LLMNonRetriableError):
        await ai_service.process_kfz_claim("test")


@pytest.mark.asyncio
async def test_llm_fallback_both_unavailable_mock_mode(monkeypatch):
    monkeypatch.setattr(ai_service.settings, "gemini_api_key", "")
    monkeypatch.setattr(ai_service.settings, "openrouter_api_key", "")
    result = await ai_service.process_kfz_claim("test")
    assert result.llm_provider == "mock"
    assert result.llm_fallback_used is False
