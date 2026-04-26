"""
n8n Executive Reporting Pipeline — FastAPI Backend
===================================================
Receives webhook from n8n, generates AI narrative with Claude API,
renders Quarto report and distributes via Slack + Gmail.

Endpoints:
  POST /webhook/report      ← n8n triggers this
  POST /generate/narrative  ← Claude API narrative generation
  GET  /health              ← health check
  GET  /reports             ← list generated reports
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from src.generators.narrative import generate_narrative
from src.generators.report import render_quarto_report
from src.generators.distributor import distribute_report

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("n8n-reporting")

app = FastAPI(
    title="n8n Executive Reporting Pipeline",
    description="Automated executive reporting: data → Claude AI narrative → Quarto → Slack + Gmail",
    version="0.1.0",
)

# ── Models ────────────────────────────────────────────────────────────────────

class ReportRequest(BaseModel):
    company_id: str
    period: str                          # e.g. "2024-Q4", "2025-01"
    report_type: str = "executive"       # executive | operational | financial
    data: dict                           # KPIs, metrics, financials
    recipients: list[str] = []          # email list
    slack_channel: Optional[str] = None
    send_email: bool = True
    send_slack: bool = True

class ReportResponse(BaseModel):
    report_id: str
    status: str
    message: str
    timestamp: str

# ── In-memory report registry ─────────────────────────────────────────────────
reports_registry = {}

# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.get("/reports")
def list_reports():
    return {"reports": list(reports_registry.values()), "total": len(reports_registry)}


@app.post("/webhook/report", response_model=ReportResponse)
async def webhook_report(request: ReportRequest, background_tasks: BackgroundTasks):
    """
    Main webhook — n8n calls this after extracting data from ERP/DB.
    Triggers async pipeline: narrative → render → distribute.
    """
    report_id = f"{request.company_id}_{request.period}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    reports_registry[report_id] = {
        "report_id": report_id,
        "company_id": request.company_id,
        "period": request.period,
        "status": "processing",
        "created_at": datetime.now().isoformat(),
    }

    logger.info(f"Report triggered: {report_id}")
    background_tasks.add_task(run_pipeline, report_id, request)

    return ReportResponse(
        report_id=report_id,
        status="processing",
        message="Report pipeline started. Check /reports for status.",
        timestamp=datetime.now().isoformat(),
    )


@app.post("/generate/narrative")
async def generate_narrative_endpoint(request: ReportRequest):
    """Direct narrative generation — useful for testing without full pipeline."""
    try:
        narrative = await generate_narrative(
            data=request.data,
            company_id=request.company_id,
            period=request.period,
            report_type=request.report_type,
        )
        return {"narrative": narrative, "tokens_used": len(narrative.split())}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Pipeline ──────────────────────────────────────────────────────────────────

async def run_pipeline(report_id: str, request: ReportRequest):
    """
    Full pipeline:
    1. Generate AI narrative with Claude API
    2. Render Quarto report (PDF + HTML)
    3. Distribute via Slack + Gmail
    """
    try:
        logger.info(f"[{report_id}] Step 1: Generating narrative...")
        narrative = await generate_narrative(
            data=request.data,
            company_id=request.company_id,
            period=request.period,
            report_type=request.report_type,
        )

        logger.info(f"[{report_id}] Step 2: Rendering Quarto report...")
        report_paths = await render_quarto_report(
            report_id=report_id,
            company_id=request.company_id,
            period=request.period,
            data=request.data,
            narrative=narrative,
        )

        logger.info(f"[{report_id}] Step 3: Distributing report...")
        distribution_result = await distribute_report(
            report_id=report_id,
            report_paths=report_paths,
            recipients=request.recipients,
            slack_channel=request.slack_channel,
            send_email=request.send_email,
            send_slack=request.send_slack,
            company_id=request.company_id,
            period=request.period,
        )

        reports_registry[report_id].update({
            "status": "completed",
            "narrative_preview": narrative[:200] + "...",
            "report_paths": report_paths,
            "distribution": distribution_result,
            "completed_at": datetime.now().isoformat(),
        })

        logger.info(f"[{report_id}] Pipeline completed successfully")

    except Exception as e:
        logger.error(f"[{report_id}] Pipeline failed: {e}")
        reports_registry[report_id].update({
            "status": "failed",
            "error": str(e),
            "failed_at": datetime.now().isoformat(),
        })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
