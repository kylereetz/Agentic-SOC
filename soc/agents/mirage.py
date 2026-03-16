"""
SENTINEL-MIRAGE: Deception & Decoy Operations Specialist.
Deploys and monitors lightweight honeypots and decoy credentials.

IQ Capabilities:
- Decoy Management (PLC simulation, CAD file shares).
- Silent Monitoring (High-fidelity detection).

EQ Capabilities:
- High-Fidelity Escalation (Bypasses standard queues for immediate response).

# Satisfies NIST 800-171 Rev 3:
# 3.14.6 - Monitor organizational systems to detect attacks.
# 3.14.3 - Monitor system security alerts and take action.
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from soc.bootstrap import get_soc_path
from soc.bus.event_queue import EventBus

logger = logging.getLogger("RCA-Mirage")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - RCA Mirage - %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)

MIRAGE_RULES_PATH = get_soc_path("configs", "mirage_rules.json")

class MirageAgent:
    """
    Deception Specialist. Catching intruders via bait.
    """
    def __init__(self, rules_path: str = MIRAGE_RULES_PATH):
        self.in_bus = EventBus("deception_events")
        self.triage_bus = EventBus("triage_alerts")
        self.rules = self._load_rules(rules_path)
        self.is_running = False

    def _load_rules(self, path: str) -> Dict[str, Any]:
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load Mirage rules: {e}")
            return {"decoys": [], "escalation_logic": {}}

    async def run(self):
        self.is_running = True
        logger.info("[SQ] Mirage Deception Specialist started.")
        
        while self.is_running:
            event = await asyncio.to_thread(self.in_bus.pop)
            if event:
                await self._process_deception_event(event)
            else:
                await asyncio.sleep(0.5)

    async def _process_deception_event(self, event: Dict[str, Any]):
        decoy_id = event.get("decoy_id")
        source_ip = event.get("source_ip", "Unknown IP")
        
        # Match decoy with rules
        decoy_rule = next((d for d in self.rules.get("decoys", []) if d["id"] == decoy_id), None)
        
        if decoy_rule:
             await self._escalate_deception_hit(source_ip, decoy_rule, event)
        else:
            logger.warning(f"Decoy hit on unregistered ID: {decoy_id} from {source_ip}")

    async def _escalate_deception_hit(self, source_ip: str, rule: Dict[str, Any], event: Dict[str, Any]):
        """[EQ] High-Fidelity Escalation: Bypass queue logic."""
        logger.warning(f"[EQ] DECEPTION HIT on {rule['name']} ({rule['type']}) from {source_ip} - ESCALATING IMMEDIATELY")
        
        escalation_logic = self.rules.get("escalation_logic", {})
        
        alert = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "rule_id": f"MIRAGE_{rule['id']}",
            "rule_name": f"DECEPTION: {rule['name']}",
            "severity": rule["escalation_level"],
            "source_ip": source_ip,
            "description": f"High-fidelity decoy interaction detected. {rule['description']} Action: {event.get('action')}",
            "nist_control": "3.14.6",
            "mitre_ttp": "T1021", # Lateral Movement (Baiting)
            "metadata": {
                "BYPASS_STANDARD_QUEUE": escalation_logic.get("bypass_standard_queue", True),
                "IMMEDIATE_TRIAGE_BOOST": escalation_logic.get("immediate_triage_boost", True),
                "decoy_type": rule["type"]
            },
            "raw_event": event
        }
        
        # Pushing to triage bus
        self.triage_bus.push(alert)
        logger.info(f"[VQ] Deception Alert dispatched for {source_ip} (Standard Queue Bypass: {escalation_logic.get('bypass_standard_queue')})")

if __name__ == "__main__":
    mirage = MirageAgent()
    asyncio.run(mirage.run())
