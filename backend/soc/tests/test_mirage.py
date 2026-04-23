import asyncio
import os
import sys
from datetime import datetime, timezone

# Ensure project root is in path
sys.path.append(os.getcwd())

from soc.agents.intelligence.mirage import MirageAgent
from soc.bus.event_queue import EventBus

async def test_mirage_intelligence():
    print("="*60)
    print("  QUILL-MIRAGE VALIDATION")
    print("="*60)
    
    ma = MirageAgent()
    d_bus = EventBus("deception_events")
    triage_bus = EventBus("triage_alerts")
    
    # Clear buses
    while triage_bus.pop(): pass
    
    # 1. Test Honeypot PLC Interaction
    print("\n[TEST 1] Verifying Honeypot PLC Interaction (Industrial Deception)...")
    d_bus.push({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "decoy_id": "DEC_PLC_01",
        "decoy_type": "industrial_plc",
        "source_ip": "10.0.0.99",
        "action": "s7comm_read",
        "detail": "Attempted to read memory block DB1 from simulated PLC."
    })
    
    event = d_bus.pop()
    if event: await ma._process_deception_event(event)
    
    alert = triage_bus.pop()
    if alert and alert["severity"] == "CRITICAL" and "Siemens S7-1500" in alert["description"]:
        print(f"  [PASS] Detected Decoy Interaction on DEC_PLC_01. Severity: {alert['severity']}")
        if alert["metadata"].get("BYPASS_STANDARD_QUEUE"):
             print(f"  [PASS] Verified BYPASS_STANDARD_QUEUE flag.")
    else:
        print(f"  [FAIL] Failed to detect PLC interaction. Alert: {alert}")

    # 2. Test Decoy Credential Use
    print("\n[TEST 2] Verifying Decoy Credential Use (Baiting)...")
    d_bus.push({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "decoy_id": "DEC_CRED_01",
        "decoy_type": "decoy_credential",
        "source_ip": "192.168.1.102",
        "action": "login_attempt",
        "detail": "Login with svc_mfg_root credential detected in SQL log."
    })
    
    event = d_bus.pop()
    if event: await ma._process_deception_event(event)
    
    alert = triage_bus.pop()
    if alert and alert["severity"] == "CRITICAL" and "svc_mfg_root" in alert["rule_name"]:
        print(f"  [PASS] Detected Decoy Credential Use. Action: {alert['raw_event'].get('action')}")
    else:
        print(f"  [FAIL] Failed to detect credential use. Alert: {alert}")

    print("\n" + "="*60)
    print("  MIRAGE VALIDATION COMPLETE")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(test_mirage_intelligence())
