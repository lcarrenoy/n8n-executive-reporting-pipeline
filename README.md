# n8n Executive Reporting Pipeline

> Automated executive reporting pipeline: **schedule trigger → data extraction → Claude API narrative → Quarto render → Slack + Gmail delivery**. Reduces 15h/week of manual reporting to under 5 minutes end-to-end.

**Stack:** n8n · Claude API · Quarto · FastAPI · Slack API · Gmail API · Docker

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    n8n Workflow                                   │
│                                                                   │
│  Schedule ──► Fetch ERP ──► Transform ──► Trigger API ──► Slack │
│  (cron)       (HTTP)        (Code)        (HTTP POST)    (notify)│
└──────────────────────────────────┬──────────────────────────────┘
                                   │ POST /webhook/report
                    ┌──────────────▼──────────────┐
                    │     FastAPI Backend           │
                    │                               │
                    │  1. Claude API narrative      │
                    │  2. Quarto render (PDF+HTML)  │
                    │  3. Slack notification        │
                    │  4. Gmail delivery            │
                    └───────────────────────────────┘
```

## Pipeline Steps

| Step | Tool | Action |
|------|------|--------|
| 1 | n8n Schedule | Triggers on 1st of month at 8am |
| 2 | n8n HTTP | Fetches KPIs from ERP/DB API |
| 3 | n8n Code | Transforms and validates data |
| 4 | FastAPI | Receives webhook, starts pipeline |
| 5 | Claude API | Generates executive narrative |
| 6 | Quarto | Renders PDF + HTML report |
| 7 | Slack API | Sends notification with summary |
| 8 | Gmail | Delivers PDF to recipients |

## How to Run

```bash
# 1. Clone
git clone https://github.com/lcarrenoy/n8n-executive-reporting-pipeline.git
cd n8n-executive-reporting-pipeline

# 2. Configure
cp .env.example .env
# Edit .env with your API keys

# 3. Start with Docker
docker-compose -f docker/docker-compose.yml up -d

# 4. Access n8n
open http://localhost:5678
# Import workflow from workflows/executive_reporting_pipeline.json

# 5. Run tests
pip install -e .
pytest tests/ -v
```

## Manual Test (without n8n)

```bash
# Start API
uvicorn src.api.main:app --reload

# Trigger report
curl -X POST http://localhost:8000/webhook/report \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": "YUMMY-001",
    "period": "2024-Q4",
    "report_type": "executive",
    "data": {
      "revenue": {"total": 4250000, "growth_yoy": 12.3},
      "profitability": {"gross_margin": 68.4, "net_margin": 14.2},
      "liquidity": {"cash": 2800000, "runway_months": 18},
      "operations": {"churn": 2.1, "nrr": 118, "ltv_cac": 14.7}
    },
    "recipients": ["cfo@company.com"],
    "slack_channel": "#reports",
    "send_email": true,
    "send_slack": true
  }'
```

## Project Structure

```
n8n-executive-reporting-pipeline/
├── workflows/
│   └── executive_reporting_pipeline.json  # n8n workflow (importable)
├── src/
│   ├── api/
│   │   └── main.py                        # FastAPI backend + webhook
│   └── generators/
│       ├── narrative.py                   # Claude API narrative generation
│       ├── report.py                      # Quarto render (PDF + HTML)
│       └── distributor.py                 # Slack + Gmail delivery
├── tests/
│   └── test_pipeline.py                   # Pytest async tests
├── docker/
│   └── docker-compose.yml                 # n8n + API containers
├── Dockerfile
├── .env.example
└── pyproject.toml
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | Claude API key |
| `SLACK_BOT_TOKEN` | Slack bot token (xoxb-...) |
| `SLACK_CHANNEL` | Slack channel for notifications |
| `GMAIL_USER` | Gmail address |
| `GMAIL_APP_PASSWORD` | Google App Password |
| `EMAIL_RECIPIENTS` | Comma-separated email list |
| `ERP_API_URL` | Your ERP/data source API URL |
| `COMPANY_ID` | Default company identifier |

---

*Part of [Luis Carreño's Portfolio](https://github.com/lcarrenoy) · AI Engineer · n8n · Claude API · Quarto*
