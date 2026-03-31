import sys
import os
import logging

# Append project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.core.sentinel import SentinelEngine
from soc.agents.scout import ScoutAgent, InventoryDiff

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Test-PQC-Scout")

def test_pqc_discovery():
    logger.info("Initializing PQC Inventory Validation Test...")
    
    # Instantiate SentinelEngine to test the _get_tls_metadata actively first
    # (Since passive sniffing requires live traffic we can't easily mock offline)
    sentinel = SentinelEngine()
    
    logger.info("Testing Quantum Vulnerability Metadata extraction against a public endpoint (google.com) ...")
    # This will securely connect to port 443 and strip the cipher
    tls_info = sentinel._get_tls_metadata("google.com", 443, timeout=5)
    
    if tls_info:
        logger.info(f"Successfully extracted TLS Metadata: {tls_info}")
        if "pqc_vulnerable" in tls_info:
            logger.info("Success! The 'pqc_vulnerable' boolean is successfully integrated into the scanner.")
        else:
            logger.error("Failed to find 'pqc_vulnerable' flag.")
    else:
        logger.warning("Could not reach google.com or extract TLS metadata.")
        
    logger.info("Testing ScoutAgent InventoryDiff PQC event generation...")
    # Mock an inventory shift where a machine suddenly degrades its cipher suite
    before = {
        "10.0.0.5": {
            "ip_address": "10.0.0.5",
            "pqc_vulnerable": False,
            "legacy_ciphers_used": []
        }
    }
    
    after = {
         "10.0.0.5": {
            "ip_address": "10.0.0.5",
            "pqc_vulnerable": True,   # Detected legacy cipher!
            "legacy_ciphers_used": ["TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256"]
        }       
    }
    
    diff = InventoryDiff(before, after)
    events = diff.to_events()
    
    pqc_event_found = False
    for e in events:
        if e.get("event_type") == "asset_pqc_vulnerable":
            pqc_event_found = True
            logger.info(f"Verified Event Emission: {e.get('semantic_detail')} - Ciphers: {e.get('legacy_ciphers')}")
            
    if pqc_event_found:
        logger.info("Success! The Scout Agent correctly formats PQC alerts for the SOC Triage bus.")
    else:
        logger.error("Failed to generate PQC event.")

if __name__ == "__main__":
    test_pqc_discovery()
