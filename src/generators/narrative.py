"""
Narrative Generator — Claude API
=================================
Generates executive financial narrative from KPI data using Claude API.
Produces structured, professional narrative ready for Quarto rendering.
"""

import os
import json
import anthropic
from typing import Literal


async def generate_narrative(
    data: dict,
    company_id: str,
    period: str,
    report_type: Literal["executive", "operational", "financial"] = "executive",
) -> str:
    """
    Generate AI narrative from financial/operational data using Claude API.

    Args:
        data: KPIs, metrics, financials dict
        company_id: Company identifier
        period: Report period (e.g. "2024-Q4")
        report_type: Type of report to generate

    Returns:
        Structured narrative string in Markdown format
    """

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    system_prompt = """You are a senior financial analyst and business writer.
Your task is to generate concise, professional executive reports in English.

Rules:
- Use clear business language — no jargon
- Highlight key insights and risks with specific numbers
- Structure: Executive Summary → Key Results → Risks → Recommendations
- Use Markdown formatting (##, **bold**, bullet points)
- Be specific: cite exact numbers, percentages, comparisons vs prior period
- Keep it under 600 words
- Flag RED if any metric is critical"""

    user_prompt = f"""Generate an {report_type} report for:
- Company: {company_id}
- Period: {period}
- Data: {json.dumps(data, indent=2)}

Structure the report in Markdown with these sections:
## Executive Summary
## Key Results
## Risk Flags
## Recommendations"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )

    return message.content[0].text


def build_data_summary(data: dict) -> str:
    """Build a human-readable summary of the data for logging."""
    summary = []
    for key, value in data.items():
        if isinstance(value, dict):
            summary.append(f"{key}: {json.dumps(value)}")
        else:
            summary.append(f"{key}: {value}")
    return " | ".join(summary[:5])
