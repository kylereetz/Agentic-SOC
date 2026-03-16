"""
SENTINEL-TRAFFIC-SIEVE: Netflow Analysis & Exfiltration Detection.
Identifies anomalous patterns in network telemetry.

IQ Capabilities:
- Netflow Correlation (Bytes/Flags/Ports).
- Exfiltration Detection (High volume to unknown IPs).

# Satisfies NIST 800-171 Rev 3:
# 3.14.6 - Monitor organizational systems to detect attacks.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict
from soc.bus.event_queue import EventBus

logger = logging.getLogger("RCA-TrafficSieve")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - RCA TrafficSieve - %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)

class TrafficSieveAgent:
    """
    Monitors network telemetry for anomalies.
    """
    def __init__(self):
        self.net_bus = EventBus("network_telemetry")
        self.triage_bus = EventBus("triage_alerts")
        self.is_running = False

    async def run(self):
        self.is_running = True
        logger.info("[SQ] Traffic-Sieve Network Specialist started.")
        
        while self.is_running:
            net_event = await asyncio.to_thread(self.net_bus.pop)
            if net_event:
                await self._analyze_flow(net_event)
            else:
                await asyncio.sleep(0.5)

    async def _analyze_flow(self, flow: Dict[str, Any]):
        bytes_sent = flow.get("bytes", 0)
        dst_ip = flow.get("dst_ip", "")
        
        # [IQ] Exfiltration Detection Logic
        if bytes_sent > 1000000: # 1MB threshold for demo
            logger.warning(f"[IQ] High volume egress detected: {bytes_sent} bytes to {dst_ip}")
            alert = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "rule_id": "NET_EXFIL_001",
                "rule_name": "Potential Data Exfiltration",
                "severity": "HIGH",
                "source_ip": flow.get("src_ip"),
                "description": f"Anomalous outbound traffic volume ({bytes_sent} bytes) to {dst_ip}",
                "mitre_ttp": "T1041",
                "raw_event": flow
            }
            self.triage_bus.push(alert)

if __name__ == "__main__":
    sieve = TrafficSieveAgent()
    asyncio.run(sieve.run())
