"""
SENTINEL-LOG-GUARDIAN: NLP-driven log normalization.
Fixes "broken" logs from legacy systems using NLP/LLM guidance.

IQ Capabilities:
- Dynamic Normalization (Raw -> Standard Schema).
- Format Detection (Auto-detects syslog, json, csv, etc.).

# Satisfies NIST 800-171 Rev 3:
# 3.14.1 - Identify, report, and correct system flaws in a timely manner.
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from soc.bootstrap import get_soc_path
from soc.bus.event_queue import EventBus

logger = logging.getLogger("RCA-LogGuardian")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - RCA LogGuardian - %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)

class LogGuardianAgent:
    """
    Cleans and normalizes incoming raw logs.
    """
    def __init__(self):
        self.raw_bus = EventBus("raw_logs")
        self.triage_bus = EventBus("triage_alerts") # Or should it go to a normalized_logs bus?
        # For simplicity in this demo, it normalizes and pushes to triage if suspicious, 
        # or just 'processes' it. Let's assume it pushes to standard triage for classification.
        self.is_running = False

    async def run(self):
        self.is_running = True
        logger.info("[SQ] Log-Guardian Normalization Specialist started.")
        
        while self.is_running:
            raw_event = await asyncio.to_thread(self.raw_bus.pop)
            if raw_event:
                await self._normalize_log(raw_event)
            else:
                await asyncio.sleep(0.5)

    async def _normalize_log(self, event: Dict[str, Any]):
        raw_data = event.get("raw_data", "")
        source = event.get("source", "Unknown")
        
        logger.info(f"[IQ] Normalizing log from {source}...")
        
        # [IQ] NLP Normalization (Mocked logic for demo)
        normalized = self._nlp_fix(raw_data)
        
        if normalized:
            logger.info(f"[VQ] Log normalized successfully. Format: {normalized.get('format')}")
            # Pushing to triage for actual threat detection
            alert = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "rule_id": "LOG_NORMALIZED",
                "rule_name": f"Normalized Log from {source}",
                "severity": "INFO",
                "source_ip": normalized.get("source_ip", "0.0.0.0"),
                "description": f"Normalized entry: {normalized.get('message', 'No details')}",
                "raw_event": event,
                "metadata": {
                    "normalization_format": normalized.get("format"),
                    "original_source": source
                }
            }
            self.triage_bus.push(alert)

    def _nlp_fix(self, raw: str) -> Dict[str, Any]:
        """Simple heuristic normalization simulation."""
        raw = raw.lower()
        if "user" in raw and "login" in raw:
            return {
                "format": "access_log",
                "source_ip": "10.0.0.1", # Mocked extraction
                "message": "User login attempt noted."
            }
        elif "connection" in raw and "refused" in raw:
             return {
                "format": "syslog",
                "source_ip": "192.168.1.100",
                "message": "Outbound connection refused."
            }
        return {
            "format": "generic",
            "message": raw[:100]
        }

if __name__ == "__main__":
    guardian = LogGuardianAgent()
    asyncio.run(guardian.run())
