import sys
import os
import logging

# Append project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.core.sentinel import SentinelEngine
from soc.agents.operations.scout import ScoutAgent, InventoryDiff

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Test-Scout-Features")

def test_ot_discovery():
    logger.info("Initializing OT Inventory Validation Test...")
    
    # Instantiate SentinelEngine to test the _get_tls_metadata actively first
    sentinel = SentinelEngine()
    
    logger.info("Testing TLS Metadata extraction against a public endpoint (google.com) ...")
    tls_info = sentinel._get_tls_metadata("google.com", 443, timeout=5)
    
    if tls_info:
        logger.info(f"Successfully extracted TLS Metadata: {tls_info}")
    else:
        logger.warning("Could not reach google.com or extract TLS metadata.")
        
    logger.info("Testing ScoutAgent InventoryDiff OT event generation...")
    # Mock an inventory shift where a machine suddenly exposes default PLC credentials and is identified as legacy
    before = {
        "10.0.0.5": {
            "ip_address": "10.0.0.5",
            "shadow_it": False,
            "unpatched_legacy": False,
            "default_credentials_exposed": False
        }
    }
    
    after = {
         "10.0.0.5": {
            "ip_address": "10.0.0.5",
            "shadow_it": True,
            "unpatched_legacy": True,
            "default_credentials_exposed": True
        }       
    }
    
    diff = InventoryDiff(before, after)
    events = diff.to_events()
    
    found_shadow_it = False
    found_legacy = False
    found_default_creds = False
    
    for e in events:
        if e.get("event_type") == "asset_shadow_it_detected":
            found_shadow_it = True
            logger.info(f"Verified Event Emission: {e.get('semantic_detail')}")
        elif e.get("event_type") == "asset_unpatched_legacy":
            found_legacy = True
            logger.info(f"Verified Event Emission: {e.get('semantic_detail')}")
        elif e.get("event_type") == "asset_default_credentials":
            found_default_creds = True
            logger.info(f"Verified Event Emission: {e.get('semantic_detail')}")
            
    if found_shadow_it and found_legacy and found_default_creds:
        logger.info("Success! The Scout Agent correctly formats OT alerts for the SOC Triage bus.")
    else:
        logger.error("Failed to generate required OT events.")

if __name__ == "__main__":
    test_ot_discovery()
