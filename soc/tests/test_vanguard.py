import asyncio
import os
import sys
from datetime import datetime, timezone

# Ensure project root is in path
sys.path.append(os.getcwd())

from soc.agents.vanguard import VanguardAgent
from soc.bus.event_queue import EventBus

async def test_vanguard_intelligence():
    print("="*60)
    print("  SENTINEL-VANGUARD VALIDATION")
    print("="*60)
    
    vg = VanguardAgent()
    v_bus = EventBus("vanguard_events")
    triage_bus = EventBus("triage_alerts")
    
    # Clear buses
    while triage_bus.pop(): pass
    
    # 1. Test SBOM Zero-Day Detection
    print("\n[TEST 1] Verifying SBOM Zero-Day Detection (Log4Shell)...")
    v_bus.push({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": "sbom_ingestion",
        "asset_id": "MFG-WS-01",
        "components": [
            {"name": "log4j", "version": "2.14.1", "type": "library"},
            {"name": "guava", "version": "30.1-jre", "type": "library"}
        ]
    })
    
    event = v_bus.pop()
    if event: await vg._process_vanguard_event(event)
    
    alert = triage_bus.pop()
    if alert and "CVE-2021-44228" in alert["description"]:
        print(f"  [PASS] Detected Log4Shell (CVE-2021-44228) on MFG-WS-01")
    else:
        print(f"  [FAIL] Failed to detect Log4Shell. Alert: {alert}")

    # 2. Test BEC Detection (Lookalike Domain)
    print("\n[TEST 2] Verifying BEC Detection (Lookalike Domain)...")
    v_bus.push({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": "external_comm",
        "sender": "support@micros0ft.com",
        "subject": "Security Update Required",
        "content": "Please click the link to secure your account."
    })
    
    event = v_bus.pop()
    if event: await vg._process_vanguard_event(event)
    
    alert = triage_bus.pop()
    if alert and "Lookalike domain" in alert["description"]:
        print(f"  [PASS] Detected Impersonation from micros0ft.com")
    else:
        print(f"  [FAIL] Failed to detect lookalike domain. Alert: {alert}")

    # 3. Test BEC Detection (Keywords)
    print("\n[TEST 3] Verifying BEC Detection (Keywords)...")
    v_bus.push({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": "external_comm",
        "sender": "vendor-finance@partner.com",
        "subject": "Change in Payment Details",
        "content": "Please update our bank account details for the next wire transfer."
    })
    
    event = v_bus.pop()
    if event: await vg._process_vanguard_event(event)
    
    alert = triage_bus.pop()
    if alert and "BEC Keywords" in alert["description"]:
        print(f"  [PASS] Detected BEC via keyword: wire transfer")
    else:
        print(f"  [FAIL] Failed to detect BEC keywords. Alert: {alert}")

    print("\n" + "="*60)
    print("  VANGUARD VALIDATION COMPLETE")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(test_vanguard_intelligence())
