"""
RCA SOC Integration Test: Scout -> Triage -> Responder.
Verifies the end-to-end file-backed event bus pipeline.
"""

import json
import logging
import os
import sys
import shutil

# Ensure we can import from the root
sys.path.append(os.getcwd())

from soc.bus.event_queue import EventBus
from soc.agents.intelligence.triage import TriageAgent
from soc.agents.action.responder import ResponderAgent
from soc.bootstrap import bootstrap_soc, get_soc_path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("IntegrationTest")


def run_test():
    logger.info("Starting RCA SOC Integration Test...")

    # 1. Clean bootstrap
    logger.info("[1/5] Bootstrapping SOC...")
    if not bootstrap_soc():
        logger.error("Bootstrap failed.")
        return False

    # 2. Simulate Scout: Push a 'Modbus Write' event
    logger.info("[2/5] Simulating Scout: Pushing Modbus Write event...")
    scout_bus = EventBus("discovery_events")
    # Simulate a critical Modbus Write event (FC 15)
    test_event = {
        "timestamp": "2026-03-15T22:00:00Z",
        "event_type": "industrial_activity",
        "protocol": "modbus",
        "function_code": 15,
        "severity": "WARNING",  # Initial severity from scout, triage will upgrade it
        "ip": "10.0.0.150",
        "mac": "aa:bb:cc:11:22:33",
        "detail": "Modbus Force Multiple Coils detected",
    }
    scout_bus.push(test_event)

    # 3. Use Triage: Classify discovery event
    logger.info("[3/5] Running Triage Agent...")
    triage = TriageAgent()
    alerts_created = triage.run_cycle()
    logger.info(f"Triage processed events. Alerts created: {alerts_created}")

    if alerts_created == 0:
        logger.error("Triage failed to create alerts.")
        return False

    # 4. Use Responder: Draft containment
    logger.info("[4/5] Running Responder Agent...")
    responder = ResponderAgent()
    actions_drafted = responder.run_cycle()
    logger.info(f"Responder cycle complete. Actions drafted: {actions_drafted}")

    pending_path = get_soc_path("reports", "incidents", "pending_actions.json")
    if os.path.exists(pending_path):
        with open(pending_path, "r") as fh:
            pending = json.load(fh)
            logger.info(f"PENDING ACTIONS DETECTED: {len(pending)}")
            for act in pending:
                logger.info(f"Strategy: {act['strategy']} | Target: {act['target_ip']}")
    else:
        logger.error("No pending actions file found!")
        return False

    # 5. Cleanup (Optional: Move events to processed already happened via pop)
    logger.info("[5/5] Integration Test SUCCESS.")
    return True


if __name__ == "__main__":
    if run_test():
        print("\nIntegration Test PASSED.")
    else:
        print("\nIntegration Test FAILED.")
        sys.exit(1)
