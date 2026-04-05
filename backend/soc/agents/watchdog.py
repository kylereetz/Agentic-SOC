"""
GAGGLE-WATCHDOG: Heartbeat-Monitor & Agent Health.
Monitors other agents for hallucinations, lag, or downtime.

# Satisfies NIST 800-171 Rev 3:
# 3.14.3 - Monitor system security alerts and take action.
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict
from soc.bootstrap import get_soc_path
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
        self.out_bus = EventBus("triage_alerts")
        
        # [IQ] Doctrine Reference: GAGGLE-WATCHDOG
        from soc.bootstrap import get_soc_path
        logger.info(f"Synchronized with doctrine: {get_soc_path('ethos', 'ethos_gaggle_watchdog.md')}")
 # Or dispatch directly?
        self.is_running = False

    async def run(self):
        self.is_running = True
        logger.info("[SQ] Watchdog Health Specialist started.")
        
        # [IQ] Start Background Chron tasks
        asyncio.create_task(self._prune_dlq())
        
        while self.is_running:
            metrics = await asyncio.to_thread(self.health_bus.pop)
            if metrics:
                await self._check_health(metrics)
            else:
                await asyncio.sleep(1.0)

    async def _prune_dlq(self):
        """[IQ] Run a daily cron to prune DLQ JSON logs older than 7 days."""
        dlq_path = get_soc_path("reports", "triage", "triage_dlq.json")
        while self.is_running:
            try:
                if os.path.exists(dlq_path):
                    with open(dlq_path, "r") as fh:
                        data = json.load(fh)
                    
                    if isinstance(data, list):
                        now = datetime.now(timezone.utc)
                        pruned = [
                            a for a in data 
                            if a.get("timestamp") and (now - datetime.fromisoformat(a["timestamp"].replace("Z", "+00:00"))).days <= 7
                        ]
                        
                        if len(pruned) < len(data):
                            with open(dlq_path, "w") as fh:
                                json.dump(pruned, fh, indent=2)
                            logger.info(f"[VQ] Watchdog pruned {len(data) - len(pruned)} expired records from Triage DLQ state.")
            except Exception as e:
                logger.error(f"[!] Failed to prune DLQ: {e}")
            
            # Sleep 24 hours
            await asyncio.sleep(86400)

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
