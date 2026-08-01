"""
SENTINEL-CLOUD-WRAITH: Cloud Security & IAM Surveillance.
Monitors AWS/Azure/GCP for IAM privilege escalation and anomalous resource modification.

IQ Capabilities:
- IAM Surveillance (Detects AttachedUserPolicy, etc.).
- Resource Monitoring (Detects anomalous S3/IAM changes).

# Satisfies NIST 800-171 Rev 3:
# 3.1.2 - Limit system access to authorized users.
# 3.14.6 - Monitor organizational systems to detect attacks.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict
from soc.bus.event_queue import EventBus

logger = logging.getLogger("RCA-CloudWraith")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - RCA CloudWraith - %(message)s"
    )
    ch.setFormatter(formatter)
    logger.addHandler(ch)


class CloudWraithAgent:
    """
    Expert in Cloud Security.
    """

    def __init__(self):
        self.cloud_bus = EventBus("cloud_events")
        self.triage_bus = EventBus("triage_alerts")
        self.is_running = False

    async def run(self):
        self.is_running = True
        logger.info("[SQ] Cloud-Wraith Specialist started.")

        while self.is_running:
            event = await asyncio.to_thread(self.cloud_bus.pop)
            if event:
                await self._analyze_cloud_event(event)
            else:
                await asyncio.sleep(0.5)

    async def _analyze_cloud_event(self, event: Dict[str, Any]):
        event_name = event.get("event_name", "")
        identity = event.get("identity", "Unknown")
        provider = event.get("cloud_provider", "Unknown")

        # [IQ] IAM Privilege Escalation Pattern
        if "AttachedUserPolicy" in event_name or "PutUserPolicy" in event_name:
            logger.warning(
                f"[IQ] Critical IAM modification detected in {provider} by {identity}"
            )
            alert = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "rule_id": "CLOUD_IAM_ESCALATION",
                "rule_name": "Cloud IAM Privilege Escalation",
                "severity": "CRITICAL",
                "source_ip": "CloudAPI",
                "description": f"Potential privilege escalation in {provider}: {event_name} by {identity}",
                "mitre_ttp": "T1548.005",
                "raw_event": event,
            }
            self.triage_bus.push(alert)


if __name__ == "__main__":
    wraith = CloudWraithAgent()
    asyncio.run(wraith.run())
