"""
FLYWAY-COMMUNICATOR: Pydantic AI Edition.

This agent acts as the 'Syntactic Head' of the SOC. It transforms technical
investigation conclusions into structured executive reports (Tri-Factor Report).

Utilizes Gemma 4 E4B via the ModelRegistry for high-fidelity JSON mapping.
"""

import asyncio
import json
import logging
import os
import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel

from soc.bootstrap import get_soc_path
from soc.bus.event_queue import EventBus
from soc.engine.core.model_registry import ModelRegistry

logger = logging.getLogger("RCA-Communicator")

# --- Structured Output Models ---
class TriFactorReport(BaseModel):
    """The final executive summary of a security incident."""
    financial_risk: str = Field(description="Estimated financial impact (e.g. '$50,000')")
    summary: str = Field(description="One-paragraph executive summary for management")
    page_string: str = Field(description="A short string to send to an analyst's pager (max 100 chars)")
    mitigation_priority: str = Field(description="HIGH | MEDIUM | LOW")

@dataclass
class CommunicatorDeps:
    """Dependencies for the Pydantic AI Communicator Agent."""
    out_bus: EventBus
    agent_id: str

# ---------------------------------------------------------------------------
# Communicator Agent
# ---------------------------------------------------------------------------
class CommunicatorAgent:
    def __init__(self):
        self.agent_id = "FLYWAY-COMMUNICATOR"
        self.in_bus = EventBus("investigation_reasoning")
        self.out_bus = EventBus("executive_reports")
        self.is_running = False
        
        # Initialize Syntactic Model (Gemma 4 E4B)
        self.model = ModelRegistry.get_syntactic_model()
        
        # Pydantic AI Agent
        self.ai_agent = Agent(
            self.model,
            result_type=TriFactorReport,
            retries=2
        )
        
        # [IQ] Dynamic Ethos Loading
        self._load_ethos()

    def _load_ethos(self):
        ethos_path = get_soc_path("ethos", "ethos_flyway_communicator.md")
        try:
            with open(ethos_path, "r") as f:
                self.ethos_content = f.read().strip()
                logger.info(f"Loaded doctrine from {ethos_path}")
        except Exception:
            self.ethos_content = "You are FLYWAY-COMMUNICATOR. You handle executive reporting and risk quantification."
            logger.warning(f"Ethos not found at {ethos_path}. Using default.")

    async def _process_event(self, event: Dict[str, Any]):
        # Target only CONCLUSION steps for final reporting
        if event.get("type") != "CONCLUSION":
            return
            
        case_id = event.get("investigation_id", "UNKNOWN")
        logger.info(f"[{case_id}] Generating Tri-Factor Report via Gemma 4 E4B...")
        
        prompt = f"""
        INVESTIGATION_CONCLUSION:
        {json.dumps(event.get('content', {}))}
        
        Generate the executive Tri-Factor report. Be precise with the financial risk quantification.
        """
        
        try:
            # Execution using the Syntactic Head
            result = await self.ai_agent.run(
                prompt,
                system_prompt=self.ethos_content,
                model_settings={"temperature": 0.1} # High precision for reporting
            )
            
            report_data = result.data
            
            final_report = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "agent_id": self.agent_id,
                "investigation_id": case_id,
                "financial_risk": report_data.financial_risk,
                "executive_summary": report_data.summary,
                "dispatch_page": report_data.page_string,
                "mitigation_priority": report_data.mitigation_priority
            }
            
            self.out_bus.push(final_report)
            logger.warning(f"[BROADCAST] Paged SOC Analyst: {final_report['dispatch_page']}")
            
        except Exception as e:
            logger.error(f"[{case_id}] Reporting failed: {e}")

    async def run(self):
        self.is_running = True
        logger.info("[SQ] Communicator started, listening to investigation_reasoning.")
        while self.is_running:
            event = await asyncio.to_thread(self.in_bus.pop)
            if event:
                await self._process_event(event)
            else:
                await asyncio.sleep(1.0)

if __name__ == "__main__":
    from dataclasses import dataclass # ensuring dataclass is available for deps if needed later
    agent = CommunicatorAgent()
    asyncio.run(agent.run())
