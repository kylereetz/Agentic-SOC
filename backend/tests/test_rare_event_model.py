import asyncio
import json
import logging
import sys
import os
import time

# Append project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Force testing Threshold to 2 seconds
os.environ["SILENCE_THRESHOLD_TEST_SECONDS"] = "2"

from soc.agents.business.historian import HistorianAgent, HISTORIAN_DB_PATH
from soc.bus.event_queue import EventBus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Test-Historian")

async def test_historian_pipeline():
    logger.info("Initializing Historian Model Test...")
    
    # Ensure fresh DB state for testing
    if os.path.exists(HISTORIAN_DB_PATH):
        try:
            os.remove(HISTORIAN_DB_PATH)
        except PermissionError:
            pass # Handle Windows locking if needed, though sqlite connections should be closed
            
    triage_bus = EventBus("triage_alerts")
    
    # Clear backlog of triage alerts
    while triage_bus.pop():
        pass
        
    historian = HistorianAgent()
    
    logger.info("=== Test 1: First Observation (Setting the Baseline) ===")
    user_login = {"src_endpoint": {"ip": "10.0.0.51"}, "user": "admin_service", "action": "login"}
    await historian._process_event(user_login)
    
    alert1 = triage_bus.pop()
    if not alert1:
        logger.info("Success: First observation recorded silently.")
    else:
        logger.error("Failed: Unwarranted alert on first observation.")
        
    logger.info("=== Test 2: Active Observation (Below Threshold) ===")
    time.sleep(0.5)
    await historian._process_event(user_login)
    
    alert2 = triage_bus.pop()
    if not alert2:
        logger.info("Success: Active observation recorded silently (noise filtered).")
    else:
        logger.error("Failed: Active observation fired an alert.")
        
    logger.info("=== Test 3: Threshold of Silence Broken ===")
    # Wait for silence to exceed threshold (2 seconds)
    logger.info("Sleeping 2.5 seconds to simulate 30-day dormancy...")
    time.sleep(2.5)
    
    await historian._process_event(user_login)
    
    alert3 = triage_bus.pop()
    alert4 = triage_bus.pop() # Because we extract TWO entities (IP and User)
    
    logger.info(f"DEBUG alert3: {alert3}")
    logger.info(f"DEBUG alert4: {alert4}")
    
    found_user_alert = False
    found_ip_alert = False
    
    for alert in [alert3, alert4]:
        if alert and "Dormant" in alert.get("rule_name", ""):
            if "USER::admin_service" in alert.get("description", ""):
                found_user_alert = True
                logger.info(f"Success: Dormant User awakening caught! Severity: {alert.get('severity')}")
            if "IP::10.0.0.51" in alert.get("description", ""):
                found_ip_alert = True
                logger.info(f"Success: Dormant IP awakening caught! Severity: {alert.get('severity')}")
                
    if found_user_alert and found_ip_alert:
        logger.info("Historian Test completed successfully. Both User and IP entities tracked.")
    else:
        logger.error("Historian test failed to trigger threshold alerts on all entities.")
        
    # Cleanup DB connection to release lock
    historian.conn.close()

if __name__ == "__main__":
    asyncio.run(test_historian_pipeline())
