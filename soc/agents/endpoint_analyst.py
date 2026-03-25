"""
SENTINEL-ENDPOINT-ANALYST
Dedicated agent for real-time host execution monitoring (Sysmon EID 1, EID 8, etc).
"""
import asyncio
import json
import logging
import os
import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from soc.bootstrap import get_soc_path
from soc.bus.event_queue import EventBus
from soc.security.vault import Vault
from engine.core.llm_client import LLMClient

logger = logging.getLogger("RCA-EndpointAnalyst")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - RCA Endpoint Analyst - %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)

class EndpointAnalystAgent:
    def __init__(self):
        self.in_bus = EventBus("endpoint_telemetry")
        self.out_bus = EventBus("triage_alerts")
        self.is_running = False
        self.agent_id = "SENTINEL-ENDPOINT-ANALYST"
        
        self.llm_client = LLMClient()

    async def run(self):
        self.is_running = True
        logger.info("[SQ] Endpoint Analyst started, listening to endpoint_telemetry.")
        while self.is_running:
            event = await asyncio.to_thread(self.in_bus.pop)
            if event:
                await self._process_event(event)
            else:
                await asyncio.sleep(1.0)
                
    async def _process_event(self, event: Dict[str, Any]):
        event_type = event.get("event_type", "unknown")
        command_line = event.get("command_line", "").lower()
        
        # Heuristic 1: Encoded PowerShell (EID 1)
        if event_type == "sysmon" and event.get("eid") == 1:
            if "powershell" in event.get("process_name", "").lower():
                if "-enc" in command_line or "-encodedcommand" in command_line or "hidden" in command_line:
                    await self._escalate(event, "WARNING", "Heuristic: Obfuscated PowerShell execution detected natively.", 0.9)
                    return
        
        # Heuristic 2: Memory Injection (EID 8)
        if event_type == "sysmon" and event.get("eid") == 8:
            await self._escalate(event, "CRITICAL", "Heuristic: Remote Thread Creation (Code Injection) detected natively.", 0.95)
            return

        # LLM Fallback Analysis for ambiguous behavioral chains
        if command_line:
            prompt = f"""
            Analyze this command line for malicious intent. Look for lateral movement, recon, or defense evasion.
            Event: {json.dumps(event)}
            Reply purely in JSON: {{"malicious": true/false, "reason": "...", "severity": "WARNING"}}
            """
            try:
                res = await self.llm_client.generate_json(prompt)
                
                if res.get("malicious"):
                    await self._escalate(event, res.get("severity", "WARNING"), f"LLM Match: {res.get('reason')}", 0.8)
            except Exception as e:
                logger.error(f"[!] LLM Parsing failed for Endpoint Analyst: {e}")

    async def _escalate(self, event: Dict[str, Any], severity: str, reason: str, confidence: float):
        # Package and ship directly to Triage
        alert = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "rule_id": "EP_001",
            "rule_name": "Endpoint Behavioral Anomaly",
            "severity": severity,
            "classification": "malicious" if severity == "CRITICAL" else "suspicious",
            "source_ip": event.get("source_ip", "Unknown"),
            "description": reason,
            "nist_control": "3.14.6",
            "mitre_ttp": event.get("mitre_ttp", "T1059"),
            "raw_event": event,
            "confidence": confidence,
            "agent_id": self.agent_id,
            "evidence_array": [hashlib.sha256(json.dumps(event, sort_keys=True).encode()).hexdigest()],
            "vector_id": "endpoint_behavior_vector"
        }
        self.out_bus.push(alert)
        logger.warning(f"[{severity}] Endpoint Analyst Escalated to Triage: {reason}")

if __name__ == "__main__":
    agent = EndpointAnalystAgent()
    asyncio.run(agent.run())
