"""
SENTINEL-GOVERNOR
Consolidation of the Agentic Governance Pool (Auditor + Policy-Architect).
"""
import asyncio
import json
import logging
import os
import hashlib
from typing import Any, Dict

import google.generativeai as genai

from soc.bootstrap import get_soc_path
from soc.bus.event_queue import EventBus
from soc.security.vault import Vault

logger = logging.getLogger("RCA-Governor")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - RCA Governor - %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)


class GovernorAgent:
    """
    Analyzes finalized incidents asynchronously for both strict Compliance Mapping 
    and adaptive Triage Tuning thresholds.
    """
    def __init__(self):
        self.in_bus = EventBus("investigation_reasoning")
        self.out_bus = EventBus("governance_metrics")
        self.is_running = False
        self.agent_id = "SENTINEL-GOVERNOR"
        self._processed_cases = set()
        
        vault = Vault(get_soc_path("configs", "secrets.json"), role="governor")
        secrets_data = vault.load()
        self.api_key = secrets_data.get("llm_api_keys", {}).get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")

        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(
                "gemini-1.5-pro",
                system_instruction=(
                    "You are SENTINEL-GOVERNOR. You merge compliance mapping and continuous triage tuning into one step. "
                    "Analyze the finalized SOC investigation and output ONLY JSON. No markdown wrappers. "
                    "{'nist_mapping': ['AC-2', 'AU-3'], 'cmmc_level': 'L2', 'triage_feedback': {'rule_id': '...', 'suggested_action': 'Tune Down', 'reason': '...'}, 'confidence_score': 0.95}"
                )
            )
        else:
            self.model = None
            logger.warning("[!] LLM API keys are missing. Sentinel Governor falling back to offline retrieval mode.")

    async def run(self):
        self.is_running = True
        logger.info("[SQ] Governor started, listening to investigation_reasoning.")
        while self.is_running:
            event = await asyncio.to_thread(self.in_bus.pop)
            if event:
                await self._process_event(event)
            else:
                await asyncio.sleep(1.0)

    async def _process_event(self, event: Dict[str, Any]):
        if event.get("type") != "CONCLUSION":
            return
            
        case_id = event.get("investigation_id")
        if not case_id or case_id in self._processed_cases:
            return
            
        self._processed_cases.add(case_id)

        if self.model:
            prompt = f"Analyze and finalize the governance feedback for case {case_id}: {json.dumps(event)}"
            try:
                response = await asyncio.to_thread(self.model.generate_content, prompt)
                txt = response.text.strip()
                if txt.startswith("```json"): txt = txt[7:]
                if txt.endswith("```"): txt = txt[:-3]
                
                res = json.loads(txt)
                
                governance_payload = {
                    "agent_id": self.agent_id,
                    "case_id": case_id,
                    "compliance": {
                        "nist": res.get("nist_mapping", []),
                        "cmmc": res.get("cmmc_level", "Unknown")
                    },
                    "triage_feedback": res.get("triage_feedback", {}),
                    "confidence_score": res.get("confidence_score", 0.0),
                    "evidence_array": hashlib.sha256(json.dumps(event).encode()).hexdigest()
                }
                
                self.out_bus.push(governance_payload)
                logger.info(f"[COMPLIANCE] Generated combined feedback loop for {case_id}: {governance_payload['compliance']['nist']}")
            except Exception as e:
                logger.error(f"[!] Governance execution failed: {e}")

if __name__ == "__main__":
    agent = GovernorAgent()
    asyncio.run(agent.run())
