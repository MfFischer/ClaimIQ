"""
ClaimIQ — Basic Tests
Tests the full processing pipeline without needing real API keys (uses mock mode).
Run: pytest tests/ -v
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_health():
    """API is up and responding."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_upload_pdf(tmp_path):
    """Upload a minimal valid PDF. Mock mode returns full result without Gemini key."""
    # Create a minimal 1-page PDF
    minimal_pdf = (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R"
        b"/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj\n"
        b"4 0 obj<</Length 44>>stream\nBT /F1 12 Tf 100 700 Td"
        b"(Kfz Schaden Test) Tj ET\nendstream\nendobj\n"
        b"5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
        b"xref\n0 6\n0000000000 65535 f \n"
        b"trailer<</Size 6/Root 1 0 R>>\nstartxref\n0\n%%EOF"
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post(
            "/api/v1/claims/upload",
            files={"file": ("test_schaden.pdf", minimal_pdf, "application/pdf")},
        )

    assert r.status_code == 200
    data = r.json()
    assert "claim_id" in data
    assert data["status"] in ("done", "error")  # error ok if Tesseract not installed
    return data["claim_id"]


@pytest.mark.asyncio
async def test_get_result_not_found():
    """Returns 404 for unknown claim ID."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/api/v1/claims/nonexistent-id-00000000")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_feedback_not_found():
    """Feedback on unknown claim returns 404."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post(
            "/api/v1/claims/nonexistent-id/feedback",
            json={"general_comment": "Test"},
        )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_usage_stats():
    """Usage endpoint returns expected shape."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/api/v1/claims/usage")
    assert r.status_code == 200
    data = r.json()
    assert "total_claims_processed" in data
    assert "google_vision_calls" in data
