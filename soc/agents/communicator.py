"""
SENTINEL-COMMUNICATOR
Unified reporting agent that handles Dispatch, Narrator, and Risk Quantifier duties.
"""
import asyncio
import json
import logging
import os
import hashlib
from datetime import datetime, timezone
import google.generativeai as genai
from typing import Any, Dict

from soc.bootstrap import get_soc_path
from soc.bus.event_queue import EventBus
from soc.security.vault import Vault

logger = logging.getLogger("RCA-Communicator")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - RCA Communicator - %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)

class CommunicatorAgent:
    def __init__(self):
        # We listen to finalized cases or escalated investigation outputs
        self.in_bus = EventBus("investigation_reasoning") 
        self.out_bus = EventBus("executive_reports")
        self.is_running = False
        self.agent_id = "SENTINEL-COMMUNICATOR"
        
        vault = Vault(get_soc_path("configs", "secrets.json"))
        secrets_data = vault.load()
        self.api_key = secrets_data.get("llm_api_keys", {}).get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")

        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(
                "gemini-1.5-pro",
                system_instruction=(
                    "You are SENTINEL-COMMUNICATOR. You handle executive reporting, financial risk quantification, "
                    "and paging dispatch. You must output exactly one JSON object: "
                    "{'financial_risk': '$X', 'summary': 'C-level summary...', 'page_string': 'URGENT: ...'}"
                )
            )
        else:
            self.model = None
            logger.warning("[!] GEMINI_API_KEY not found in Vault. Defaulting to empty reporting.")

        # Naive fatigue filter
        self._last_report_hash: str = ""

    async def run(self):
        self.is_running = True
        logger.info("[SQ] Communicator started, listening to investigation_reasoning.")
        while self.is_running:
            event = await asyncio.to_thread(self.in_bus.pop)
            if event:
                await self._process_event(event)
            else:
                await asyncio.sleep(1.0)
                
    async def _process_event(self, event: Dict[str, Any]):
        # Target only CONCLUSION steps from the Investigator for final reporting
        if event.get("type") != "CONCLUSION":
            return
            
        case_hash = hashlib.md5(json.dumps(event.get("content", "")).encode()).hexdigest()
        if case_hash == self._last_report_hash:
            logger.info("Alert fatigue filter triggered. Skipping duplicate report.")
            return

        self._last_report_hash = case_hash

        if self.model:
            prompt = f"""
            Generate the Tri-Factor Report for the following investigation conclusion:
            {json.dumps(event)}
            
            Remember, reply purely in JSON:
            {{"financial_risk": "$...", "summary": "...", "page_string": "..."}}
            """
            try:
                response = await asyncio.to_thread(self.model.generate_content, prompt)
                txt = response.text.strip()
                if txt.startswith("```json"): txt = txt[7:]
                if txt.endswith("```"): txt = txt[:-3]
                res = json.loads(txt)
                
                report = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "agent_id": self.agent_id,
                    "investigation_id": event.get("investigation_id", "UNKNOWN"),
                    "financial_risk": res.get("financial_risk", "Unknown"),
                    "executive_summary": res.get("summary", "N/A"),
                    "dispatch_page": res.get("page_string", "Alert")
                }
                
                self.out_bus.push(report)
                logger.warning(f"[BROADCAST] Paged SOC Analyst: {report['dispatch_page']}")
            except Exception as e:
                logger.error(f"[!] Reporting failed: {e}")

if __name__ == "__main__":
    agent = CommunicatorAgent()
    asyncio.run(agent.run())
