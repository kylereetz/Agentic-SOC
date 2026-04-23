import asyncio
import logging
import sys
import os
import time

# Append project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Force learning period to 0 so anomalies fire immediately
os.environ["SIEVE_LEARNING_PERIOD"] = "0"

from soc.agents.operations.traffic_sieve import TrafficSieveAgent
from soc.bus.event_queue import EventBus
from soc.security.graph_persistence import GraphPersistenceManager, GRAPH_FILE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Test-TimeSeries")

async def test_time_series_anomaly():
    logger.info("Initializing Time Series Model Test...")
    
    # Wipe Graph DB for clean test
    if os.path.exists(GRAPH_FILE):
        try:
            os.remove(GRAPH_FILE)
        except PermissionError:
            pass
            
    # Purge triage alerts that might interfere
    triage_bus = EventBus("discovery_events")
    while triage_bus.pop():
        pass
        
    sieve = TrafficSieveAgent()
    
    logger.info("=== Phase 1: Establishing Welford's Statistical Baseline ===")
    
    src_test = "10.0.0.100"
    dst_test = "203.0.113.50" # Cloud S3 Bucket
    
    # Loop 15 times to build mean and variance
    # Normal usage: ~5MB uploads with marginal jitter
    base_flow = {
        "src_ip": src_test,
        "dst_ip": dst_test,
        "dst_port": 443,
        "protocol": "TCP",
        "bytes": 5000000 
    }
    
    for i in range(15):
        jitter = (i % 3) * 100000 # minor deviations
        simulated_flow = base_flow.copy()
        simulated_flow["bytes"] += jitter
        await sieve._analyze_graph_flow(simulated_flow)
        
    # Flush the 'novel edge' alert from the 1st connection
    while triage_bus.pop():
        pass
        
    logger.info("Success: Statistical Baseline modeled via Welford's Algorithm (15 events).")
    edge_stats = sieve.graph[src_test][dst_test]
    logger.info(f"Edge Memory State: Mean={edge_stats['mean_bytes']} bytes, Count={edge_stats['connection_count']}")
    
    logger.info("=== Phase 2: Active Simulation (Non-Anomalous Flow) ===")
    normal_flow = base_flow.copy()
    normal_flow["bytes"] += 50000
    await sieve._analyze_graph_flow(normal_flow)
    
    normal_alert = triage_bus.pop()
    if not normal_alert:
        logger.info("Success: Valid traffic accepted. No volumetric spike triggered.")
    else:
        logger.error(f"Failed: Normal traffic triggered a false anomaly! {normal_alert}")
        
    logger.info("=== Phase 3: Volumetric Data Exfiltration (3-Sigma Spike) ===")
    exfil_flow = base_flow.copy()
    # 50GB Upload
    exfil_flow["bytes"] = 50000000000 
    await sieve._analyze_graph_flow(exfil_flow)
    
    found_time_series_alert = False
    
    while triage_bus.size() > 0:
        alert = triage_bus.pop()
        if alert:
            unmapped = alert.get("unmapped", {})
            rule = unmapped.get("rule_id", "")
            if "GRAPH_VOLUMETRIC_SPIKE" in rule:
                found_time_series_alert = True
                logger.info("Success: Time Series Exfiltration caught!")
                logger.info(f"Mathematical Context: {unmapped.get('time_series_math')}")
        
    if found_time_series_alert:
        logger.info("Time Series Model Test completed successfully.")
    else:
        logger.error("Failed to trigger GRAPH_VOLUMETRIC_SPIKE on 50GB exfiltration anomaly.")

if __name__ == "__main__":
    asyncio.run(test_time_series_anomaly())
