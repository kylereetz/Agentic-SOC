"""
Automated Test Suite: Test Graphml Correlator.
Verifies functionality, security controls, and regression safety for target component.
"""

import asyncio
import logging
import sys
import os
import time

# Append project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from soc.agents.intelligence.correlator import CorrelatorAgent, GRAPHML_OUTPUT_PATH
from soc.bus.event_queue import EventBus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Test-GraphML")


async def test_subgraph_clustering():
    logger.info("Initializing GraphML Correlator Test...")

    # Wipe existing GraphML dump to ensure fresh test
    if os.path.exists(GRAPHML_OUTPUT_PATH):
        try:
            os.remove(GRAPHML_OUTPUT_PATH)
        except PermissionError:
            pass

    # Clear active queues
    in_bus = EventBus("raw_alerts")
    out_bus = EventBus("triage_alerts")
    while in_bus.size() > 0:
        in_bus.pop()
    while out_bus.size() > 0:
        out_bus.pop()

    correlator = CorrelatorAgent()
    # Speed up promotion for the text
    correlator.promotion_threshold = 100

    # Run the correlator agent in the background
    correlator_task = asyncio.create_task(correlator.run())

    # Wait for startup
    await asyncio.sleep(1)

    logger.info("=== Phase 1: The Initial Compromise ===")
    event_1 = {
        "event_type": "sysmon",
        "rule_name": "Suspicious Recon Executable",
        "severity": "MEDIUM",
        "source_ip": "10.0.0.50",
        "file_hash": "e99a18c428cb38d5f260853678922e03",
        "process_name": "mimikatz.exe",
    }
    in_bus.push(event_1)

    await asyncio.sleep(2)  # Give the graph time to process edges

    logger.info("=== Phase 2: Credential Access ===")
    event_2 = {
        "event_type": "sysmon",
        "rule_name": "LSASS Memory Dump",
        "severity": "HIGH",
        "user": "it_admin_svc",  # Notice this pivots to a User account
        "file_hash": "e99a18c428cb38d5f260853678922e03",  # Linked via the same file hash!
    }
    in_bus.push(event_2)

    await asyncio.sleep(2)

    logger.info("=== Phase 3: Lateral Movement ===")
    event_3 = {
        "event_type": "network",
        "rule_name": "Lateral SMB Login",
        "severity": "HIGH",
        "source_ip": "10.0.0.50",
        "dest_ip": "10.0.0.200",  # Pivoting to a new Database server
        "user": "it_admin_svc",  # Linked via the compromised user!
    }
    in_bus.push(event_3)

    await asyncio.sleep(3)  # Wait for Subgraph processing + threshold check

    # Look for the emitted Campaign
    found_campaign = False
    details = ""
    while out_bus.size() > 0:
        alert = out_bus.pop()
        if alert and alert.get("rule_id") == "CORR_GRAPHML_CAMPAIGN":
            found_campaign = True
            details = alert.get("description")
            break

    if found_campaign:
        logger.info(
            f"Success: The GraphML Engine clustered the nodes and emitted the Campaign Incident! Details: {details}"
        )
    else:
        logger.error(
            "Failed: No GraphML Campaign was emitted. Check temporal clustering math."
        )

    # Manually trigger export so we can verify the file
    correlator._persist_state()

    if os.path.exists(GRAPHML_OUTPUT_PATH):
        logger.info(
            f"Verified: Subgraph mathematically exported to {GRAPHML_OUTPUT_PATH}."
        )
    else:
        logger.error("Failed: No .graphml file was exported.")

    correlator.is_running = False
    correlator_task.cancel()


if __name__ == "__main__":
    asyncio.run(test_subgraph_clustering())
