"""
Automated Test Suite: Test Graph Model.
Verifies functionality, security controls, and regression safety for target component.
"""

import asyncio
import json
import logging
import sys
import os
import shutil

# Append project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from soc.bootstrap import get_soc_path

# Force learning mode to 0 seconds so we can test detection instantly
os.environ["SIEVE_LEARNING_PERIOD"] = "0"

from soc.agents.operations.traffic_sieve import TrafficSieveAgent
from soc.bus.event_queue import EventBus
from soc.security.graph_persistence import GRAPH_FILE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Test-GraphModel")


async def test_graph_pipeline():
    logger.info("Initializing Graph Model Test...")

    # Ensure fresh state
    if os.path.exists(GRAPH_FILE):
        os.remove(GRAPH_FILE)

    discovery_bus = EventBus("discovery_events")

    # Clear backlog of discovery events
    while discovery_bus.pop():
        pass

    sieve = TrafficSieveAgent()

    logger.info("=== Test 1: Baseline Formation ===")
    flow_1 = {
        "src_ip": "10.0.0.5",
        "dst_ip": "10.0.0.10",
        "dst_port": 502,
        "protocol": "TCP",
        "bytes": 100,
    }
    await sieve._analyze_graph_flow(flow_1)

    # The first flow should trigger a Structural Relational Anomaly
    alert1 = discovery_bus.pop()
    if (
        alert1
        and alert1.get("unmapped", {}).get("graph_anomaly")
        == "Structural Relational Anomaly"
    ):
        logger.info(
            "Success: First interaction correctly triggered Structural deviation."
        )
    else:
        logger.error("Failed to trigger Structural deviation on novel edge.")

    logger.info("=== Test 2: Baseline Maturation (No Alerts) ===")
    await sieve._analyze_graph_flow(flow_1)
    await sieve._analyze_graph_flow(flow_1)

    alert2 = discovery_bus.pop()
    if not alert2:
        logger.info("Success: Subsequent established interactions were silent.")
    else:
        logger.error("Failed: Baseline interaction triggered an alert.")

    logger.info("=== Test 3: Zero-Day Path (Port Deviation) ===")
    flow_2 = {
        "src_ip": "10.0.0.5",
        "dst_ip": "192.168.1.100",
        "dst_port": 443,
        "protocol": "TCP",
        "bytes": 5000,
    }
    await sieve._analyze_graph_flow(flow_2)

    alert3 = discovery_bus.pop()
    if alert3 and "Structural" in alert3.get("unmapped", {}).get("graph_anomaly", ""):
        logger.info("Success: Detected novel internet exfiltration path.")
    else:
        logger.error("Failed to detect external zero-day deviation.")

    logger.info("=== Test 4: Lateral Movement Scanning ===")
    # Simulate scanning 35 hosts
    for i in range(20, 55):
        flow_scan = {
            "src_ip": "10.0.0.5",
            "dst_ip": f"10.0.0.{i}",
            "dst_port": 445,
            "protocol": "TCP",
            "bytes": 50,
        }
        await sieve._analyze_graph_flow(flow_scan)

    # Drain the queue, looking for the centrality spike
    found_spike = False
    while True:
        alert = discovery_bus.pop()
        if not alert:
            break
        desc = alert.get("unmapped", {}).get("graph_anomaly", "")
        if "Centrality" in desc:
            found_spike = True

    if found_spike:
        logger.info("Success: Degree Centrality Spike recognized.")
    else:
        logger.error("Failed to recognize Degree Centrality Spike.")

    logger.info("Graph Model test completed.")


if __name__ == "__main__":
    asyncio.run(test_graph_pipeline())
