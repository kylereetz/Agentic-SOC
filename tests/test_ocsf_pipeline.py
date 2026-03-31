import asyncio
import json
import logging
import sys
import os

# Append project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from soc.agents.log_guardian import LogGuardianAgent
from soc.agents.triage import TriageEngine
from soc.security.ocsf_schema import OCSFProprietaryOT, OCSFMetadata, OCSFEndpoint

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Test-OCSF")

async def test_pipeline():
    logger.info("Initializing Agents...")
    guardian = LogGuardianAgent()
    triage = TriageEngine()
    
    # Optional Mocking of the LLM Fallback if Ollama isn't active
    # We will just inject a mock response instead of waiting for a timeout
    async def mock_generate_json(prompt, model=None):
        return {
            "ip": "10.0.0.50",
            "inferred_meaning": "Detected anomalous Modbus stop command.",
            "proprietary_codes": "0A 4F 33"
        }
    guardian.llm_client.generate_json = mock_generate_json

    logger.info("=== Test 1: Standard IT Log (Fast-Path) ===")
    raw_it = "Jul 15 12:00:00 server sshd[1234]: Accepted password for admin from 10.0.0.1 port 50222 ssh2"
    
    ocsf_it = guardian._fast_path_parse(raw_it, "syslog")
    if ocsf_it:
        logger.info(f"Fast-Path Success. UID: {ocsf_it.ocsf_class_uid}")
        event_dict = ocsf_it.model_dump()
        alert = triage.classify_event(event_dict)
        if alert:
            logger.info(f"Triage successfully classified IT OCSF Alert: {alert.rule_name} (Severity: {alert.severity})")
        else:
            logger.info("Triage correctly bypassed the IT event (no malicious rules hit).")
    else:
        logger.error("Fast-Path Failed on IT log.")
        
    logger.info("=== Test 2: Proprietary OT Log (Agentic LLM Fallback) ===")
    raw_ot = "0xERR_CRIT_MODBUS PLC_ID:44 [VAR_TMP>99] SYSTEM HALTED"
    
    ocsf_ot = await guardian._agentic_fallback(raw_ot, "factory_plc_44")
    if ocsf_ot:
        logger.info(f"Agentic Fallback Success. UID: {ocsf_ot.ocsf_class_uid}")
        logger.info(f"Extracted meaning: {ocsf_ot.unmapped.get('inferred_meaning')}")
        event_dict = ocsf_ot.model_dump()
        alert = triage.classify_event(event_dict)
        if alert:
            logger.info(f"Triage successfully classified OT OCSF Alert: {alert.rule_name} (Severity: {alert.severity})")
            logger.info(f"Semantic detail preserved: {alert.semantic_detail}")
        else:
            logger.info("Triage bypassed OT event.")
            
    else:
        logger.error("Agentic Fallback failed.")

if __name__ == "__main__":
    asyncio.run(test_pipeline())
