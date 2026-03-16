"""
SENTINEL-WATCHDOG: Heartbeat-Monitor & Agent Health.
Monitors other agents for hallucinations, lag, or downtime.

# Satisfies NIST 800-171 Rev 3:
# 3.14.3 - Monitor system security alerts and take action.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict
from soc.bus.event_queue import EventBus

logger = logging.getLogger("RCA-Watchdog")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - RCA Watchdog - %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)

class WatchdogAgent:
    """
    Ensures the Hive is healthy.
    """
    def __init__(self):
        self.health_bus = EventBus("agent_metrics")
        self.dispatch_bus = EventBus("triage_alerts") # Or dispatch directly?
        self.is_running = False

    async def run(self):
        self.is_running = True
        logger.info("[SQ] Watchdog Health Specialist started.")
        
        while self.is_running:
            metrics = await asyncio.to_thread(self.health_bus.pop)
            if metrics:
                await self._check_health(metrics)
            else:
                await asyncio.sleep(1.0)

    async def _check_health(self, metrics: Dict[str, Any]):
        status = metrics.get("status")
        agent = metrics.get("agent_name")
        
        if status != "healthy":
            logger.error(f"[IQ] Agent {agent} is reporting {status}!")
            alert = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "rule_id": "AGENT_HEALTH_ISSUE",
                "rule_name": f"Agent Health: {agent}",
                "severity": "MEDIUM",
                "source_ip": "Management",
                "description": f"Agent {agent} status: {status}. Metrics: {metrics.get('metrics')}",
                "raw_event": metrics
            }
            self.dispatch_bus.push(alert)

if __name__ == "__main__":
    dog = WatchdogAgent()
    asyncio.run(dog.run())
