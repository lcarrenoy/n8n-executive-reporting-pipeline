"""
Quarto Report Renderer
======================
Generates Quarto .qmd file from data + narrative,
then renders to PDF and HTML.
"""

import os
import json
import subprocess
from datetime import datetime
from pathlib import Path


REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(exist_ok=True)


async def render_quarto_report(
    report_id: str,
    company_id: str,
    period: str,
    data: dict,
    narrative: str,
) -> dict:
    """
    Generate Quarto .qmd and render to PDF + HTML.

    Returns:
        dict with paths to generated files
    """
    report_dir = REPORTS_DIR / report_id
    report_dir.mkdir(parents=True, exist_ok=True)

    qmd_path = report_dir / "report.qmd"
    qmd_content = build_qmd(
        company_id=company_id,
        period=period,
        data=data,
        narrative=narrative,
        report_id=report_id,
    )

    with open(qmd_path, "w", encoding="utf-8") as f:
        f.write(qmd_content)

    paths = {"qmd": str(qmd_path)}

    # Render PDF
    try:
        result = subprocess.run(
            ["quarto", "render", str(qmd_path), "--to", "pdf"],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode == 0:
            paths["pdf"] = str(report_dir / "report.pdf")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        # Quarto not installed — skip render, return qmd only
        paths["pdf"] = None

    # Render HTML
    try:
        result = subprocess.run(
            ["quarto", "render", str(qmd_path), "--to", "html"],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode == 0:
            paths["html"] = str(report_dir / "report.html")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        paths["html"] = None

    return paths


def build_qmd(
    company_id: str,
    period: str,
    data: dict,
    narrative: str,
    report_id: str,
) -> str:
    """Build Quarto .qmd content from data and narrative."""

    generated_at = datetime.now().strftime("%B %d, %Y at %H:%M")

    # Build KPI table from data
    kpi_table = build_kpi_table(data)

    return f"""---
title: "Executive Report — {company_id}"
subtitle: "Period: {period}"
date: "{generated_at}"
format:
  pdf:
    toc: false
    number-sections: false
    geometry: margin=2cm
    fontsize: 11pt
  html:
    theme: cosmo
    toc: true
execute:
  echo: false
---

{narrative}

---

## Data Summary

{kpi_table}

---

*Report ID: `{report_id}`*
*Generated automatically by n8n Executive Reporting Pipeline*
*Narrative powered by Claude API (Anthropic)*
"""


def build_kpi_table(data: dict) -> str:
    """Build a Markdown table from KPI data."""
    if not data:
        return "*No data provided.*"

    rows = []
    for key, value in data.items():
        if isinstance(value, dict):
            for subkey, subval in value.items():
                rows.append(f"| {key} — {subkey} | {subval} |")
        else:
            rows.append(f"| {key} | {value} |")

    if not rows:
        return "*No KPIs available.*"

    table = "| Metric | Value |\n|--------|-------|\n"
    table += "\n".join(rows[:20])
    return table
