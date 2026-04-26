"""
Tests — n8n Executive Reporting Pipeline
Run: pytest tests/ -v
"""

import pytest
from httpx import AsyncClient, ASGITransport
from src.api.main import app

SAMPLE_DATA = {
    "revenue": {
        "total_revenue": 4_250_000,
        "mrr": 354_167,
        "growth_yoy": 12.3,
    },
    "profitability": {
        "gross_margin": 68.4,
        "ebitda_margin": 22.7,
        "net_margin": 14.2,
    },
    "liquidity": {
        "cash_position": 2_800_000,
        "runway_months": 18,
        "current_ratio": 2.1,
    },
    "operations": {
        "cac": 1_250,
        "ltv": 18_400,
        "churn_rate": 2.1,
        "nrr": 118,
    },
}


@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_list_reports_empty():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/reports")
    assert response.status_code == 200
    assert "reports" in response.json()


@pytest.mark.asyncio
async def test_webhook_report_triggers():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/webhook/report",
            json={
                "company_id": "TEST-001",
                "period": "2024-Q4",
                "report_type": "executive",
                "data": SAMPLE_DATA,
                "recipients": [],
                "send_email": False,
                "send_slack": False,
            },
        )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "processing"
    assert "report_id" in data
    assert "TEST-001" in data["report_id"]
    print(f"✅ Report triggered: {data['report_id']}")


@pytest.mark.asyncio
async def test_report_appears_in_registry():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Trigger
        trigger = await client.post(
            "/webhook/report",
            json={
                "company_id": "TEST-002",
                "period": "2025-01",
                "data": SAMPLE_DATA,
                "send_email": False,
                "send_slack": False,
            },
        )
        report_id = trigger.json()["report_id"]

        # Check registry
        reports = await client.get("/reports")
        names = [r["report_id"] for r in reports.json()["reports"]]
        assert report_id in names
        print(f"✅ Report {report_id} found in registry")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_health())
    print("✅ Health check passed")
    asyncio.run(test_webhook_report_triggers())
    print("✅ Webhook trigger passed")
