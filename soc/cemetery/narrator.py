"""
SENTINEL-NARRATOR: Executive Reporting Specialist.
Generates board-level summaries from technical findings.

# Satisfies NIST 800-171 Rev 3:
# 3.12.4 - Develop and update system security plans.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict
from soc.bus.event_queue import EventBus

logger = logging.getLogger("RCA-Narrator")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - RCA Narrator - %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)

import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch
from soc.bootstrap import get_soc_path

REPORT_DIR = get_soc_path("reports", "business")

class NarratorAgent:
    def __init__(self):
        self.is_running = False
        self.bus = EventBus("business_intel")
        self.case_bus = EventBus("case_updates")
        self.token_usage = []
        self.closed_cases = []
        os.makedirs(REPORT_DIR, exist_ok=True)

    async def run(self):
        self.is_running = True
        logger.info("[SQ] Narrator Executive Reporting Specialist started.")
        
        # In a real environment, we'd have separate tasks for polling.
        # For this MVP, we poll sequentially.
        while self.is_running:
            # Check for business intel (tokens, impact)
            intel = self.bus.pop()
            if intel:
                self.token_usage.append(intel)
                if intel.get("type") == "report_trigger":
                    self._generate_weekly_snapshot()

            # Check for case updates
            case = self.case_bus.pop()
            if case and case.get("status") == "CLOSED":
                self.closed_cases.append(case)
                logger.info(f"[SQ] Narrator logged closed case: {case.get('case_id')}")

            await asyncio.sleep(1)

    def _generate_weekly_snapshot(self):
        """Aggregate all recent data into a PDF report."""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        filename = os.path.join(REPORT_DIR, f"SOC_Executive_Report_{timestamp}.pdf")
        
        c = canvas.Canvas(filename, pagesize=letter)
        width, height = letter

        # --- Header ---
        c.setFillColor(colors.HexColor("#0d1117"))
        c.rect(0, height - 1.5*inch, width, 1.5*inch, fill=1)
        c.setFillColor(colors.whitesmoke)
        c.setFont("Helvetica-Bold", 24)
        c.drawString(0.5*inch, height - 0.75*inch, "Agentic SOC: Executive Report")
        c.setFont("Helvetica", 10)
        c.drawString(0.5*inch, height - 1.1*inch, f"Generated: {datetime.now().strftime('%B %d, %Y %H:%M')}")
        
        # --- Body ---
        c.setFillColor(colors.black)
        y = height - 2*inch
        
        # Totals
        total_tokens = sum(t.get("total_tokens", 0) for t in self.token_usage)
        total_cases = len(self.closed_cases)
        
        c.setFont("Helvetica-Bold", 14)
        c.drawString(0.5*inch, y, "Operational Highlights")
        y -= 0.3*inch
        c.setFont("Helvetica", 12)
        c.drawString(0.7*inch, y, f"• Total Cases Closed: {total_cases}")
        y -= 0.2*inch
        c.drawString(0.7*inch, y, f"• LLM Cognitive Load: {total_tokens:,} tokens")
        y -= 0.5*inch
        
        # Closed Cases Section
        c.setFont("Helvetica-Bold", 14)
        c.drawString(0.5*inch, y, "Incident Resolutions")
        y -= 0.3*inch
        c.setFont("Helvetica", 10)
        
        for case in self.closed_cases[-10:]: # Show last 10
            if y < 1*inch: # Simple pagination
                c.showPage()
                y = height - 1*inch
            
            case_id = case.get("case_id", "Unknown")
            summary = case.get("summary", "No summary provided.")
            c.setFont("Helvetica-Bold", 11)
            c.drawString(0.6*inch, y, f"{case_id}:")
            c.setFont("Helvetica", 10)
            c.drawString(1.5*inch, y, summary[:80] + ("..." if len(summary)>80 else ""))
            y -= 0.25*inch

        c.save()
        logger.info(f"[SQ] Executive Report generated: {filename}")
        # Reset state after report? (Optional for MVP)
        # self.token_usage = []
        # self.closed_cases = []

if __name__ == "__main__":
    narrator = NarratorAgent()
    asyncio.run(narrator.run())
