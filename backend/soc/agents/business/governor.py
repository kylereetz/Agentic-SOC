"""
FLYWAY-GOVERNOR
Consolidation of the Agentic Governance Pool (Auditor + Policy-Architect).
"""

import asyncio
import json
import logging
import os
import hashlib
from typing import Any, Dict

from soc.bootstrap import get_soc_path
from soc.bus.event_queue import EventBus
from soc.security.vault import Vault
from engine.core.llm_client import LLMClient

logger = logging.getLogger("RCA-Governor")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - RCA Governor - %(message)s"
    )
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
        self.agent_id = "FLYWAY-GOVERNOR"
        self._processed_cases = set()

        # [IQ] Dynamic Ethos Loading
        ethos_path = get_soc_path("ethos", "ethos_flyway_governor.md")
        try:
            with open(ethos_path, "r") as f:
                self.ethos_content = f.read().strip()
                logger.info(f"Loaded doctrine from {ethos_path}")
        except Exception:
            self.ethos_content = "You are FLYWAY-GOVERNOR. You merge compliance mapping and continuous triage tuning into one step."
            logger.warning(f"Ethos not found at {ethos_path}. Using default.")

        self.llm_client = LLMClient()

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

        prompt = f"Analyze and finalize the governance feedback for case {case_id}: {json.dumps(event)}"
        try:
            system_inst = f"{self.ethos_content}\n\nAnalyze the finalized SOC investigation and output ONLY JSON.\n{{'nist_mapping': ['AC-2', 'AU-3'], 'cmmc_level': 'L2', 'triage_feedback': {{'rule_id': '...', 'suggested_action': 'Tune Down', 'reason': '...'}}, 'confidence_score': 0.95}}"
            res = await self.llm_client.generate_json(
                prompt, system_instruction=system_inst
            )

            governance_payload = {
                "agent_id": self.agent_id,
                "case_id": case_id,
                "compliance": {
                    "nist": res.get("nist_mapping", []),
                    "cmmc": res.get("cmmc_level", "Unknown"),
                },
                "triage_feedback": res.get("triage_feedback", {}),
                "confidence_score": res.get("confidence_score", 0.0),
                "evidence_array": hashlib.sha256(
                    json.dumps(event).encode()
                ).hexdigest(),
            }

            self.out_bus.push(governance_payload)
            logger.info(
                f"[COMPLIANCE] Generated combined feedback loop for {case_id}: {governance_payload['compliance']['nist']}"
            )
        except Exception as e:
            logger.error(f"[!] Governance execution failed: {e}")


if __name__ == "__main__":
    agent = GovernorAgent()
    asyncio.run(agent.run())
