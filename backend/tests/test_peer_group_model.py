import asyncio
import logging
import sys
import os

# Append project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from soc.agents.endpoint_analyst import EndpointAnalystAgent
from soc.bus.event_queue import EventBus
from soc.bootstrap import get_soc_path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Test-PeerGroupModel")

# Path to the database
DB_PATH = get_soc_path("reports", "endpoint_clustering.db")

async def test_peer_group_deviation():
    logger.info("Initializing Peer Group Deviation Test...")

    # Wipe DB for a fresh cluster start
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
        except PermissionError:
            pass

    triage_bus = EventBus("triage_alerts")
    # Clean the queue
    while triage_bus.size() > 0:
        triage_bus.pop()

    analyst = EndpointAnalystAgent()

    logger.info("=== Phase 1: Establishing the Finance Cluster ===")
    
    # We simulate 3 users working throughout the day
    # They all use Chrome, Excel, Outlook.
    users = ["alicew", "bobm", "charliej"]
    standard_processes = ["chrome.exe", "excel.exe", "outlook.exe"]

    for u in users:
        for p in standard_processes:
            event = {
                "event_type": "sysmon",
                "eid": 1,
                "user": u,
                "process_name": p,
                "command_line": "",
                "source_ip": "10.0.0.99"
            }
            await analyst._process_event(event)
            
    # At this point, Alice, Bob, and Charlie share 100% of their executed processes.
    # The Jaccard similarity is 1.0. They should be clustered into a single 3-person peer group.
    
    finance_cluster = None
    for c in analyst.clusters:
        if "alicew" in c:
            finance_cluster = c
            break
            
    if finance_cluster and len(finance_cluster) == 3:
        logger.info(f"Success: Zero-Config UEBA automatically clustered {finance_cluster} together.")
    else:
        logger.error(f"Failed: Clustering failed. Current clusters: {analyst.clusters}")

    # Flush triage queue from any native EID detections that might have randomly triggered
    while triage_bus.size() > 0:
        triage_bus.pop()

    logger.info("=== Phase 2: Simulating Peer Group Deviation ===")
    # Alice randomly runs Powershell. Bob and Charlie do not.
    incident_event = {
        "event_type": "sysmon",
        "eid": 1,
        "user": "alicew",
        "process_name": "whoami.exe", # A generic post-exploitation recon tool
        "command_line": "whoami /priv",
        "source_ip": "10.0.0.99"
    }

    await analyst._process_event(incident_event)

    found_dev_alert = False
    while triage_bus.size() > 0:
        alert = triage_bus.pop()
        if alert and alert.get("rule_id") == "PEER_GROUP_DEVIATION":
            found_dev_alert = True
            logger.info("Success: Peer Group Deviation caught!")
            logger.info(f"Description: {alert.get('description')}")
            
    if found_dev_alert:
        logger.info("Peer Group UEBA Test completed successfully.")
    else:
        logger.error("Failed to trigger PEER_GROUP_DEVIATION on anomalous process.")
        
    # Close DB connection
    analyst.conn.close()

if __name__ == "__main__":
    asyncio.run(test_peer_group_deviation())
