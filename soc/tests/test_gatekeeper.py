import asyncio
import json
import os
import sys
from datetime import datetime, timezone, timedelta

# Ensure project root is in path
sys.path.append(os.getcwd())

from soc.agents.gatekeeper import GatekeeperAgent
from soc.bus.event_queue import EventBus
from soc.bootstrap import get_soc_path

async def test_gatekeeper_intelligence():
    print("="*60)
    print("  SENTINEL-GATEKEEPER VALIDATION")
    print("="*60)
    
    gk = GatekeeperAgent()
    id_bus = EventBus("identity_events")
    triage_bus = EventBus("triage_alerts")
    
    # 1. Test MFA Fatigue
    print("\n[TEST 1] Verifying MFA Fatigue Detection...")
    user_id = "kyle.reetz@sentinel.io"
    for i in range(1, 7):
        id_bus.push({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "mfa_failure",
            "user_id": user_id,
            "source_ip": "192.168.1.50"
        })
        # Lockstep processing
        event = id_bus.pop()
        if event:
            await gk._process_identity_event(event)
        else:
            print(f"  [DEBUG] id_bus.pop() returned None on iteration {i}")
    
    # Check triage for alert
    alert = triage_bus.pop()
    if alert and alert["rule_id"] == "GK_MFA_001":
        print(f"  [PASS] Detected MFA Fatigue for {user_id}")
    else:
        print(f"  [FAIL] Failed to detect MFA Fatigue. Alert: {alert}")

    # 2. Test Impossible Travel
    print("\n[TEST 2] Verifying Impossible Travel Detection...")
    # Login from New York
    id_bus.push({
        "timestamp": (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat(),
        "event_type": "login_success",
        "user_id": user_id,
        "source_ip": "1.1.1.1",
        "location": {"city": "New York", "country": "US", "lat": 40.71, "lon": -74.00}
    })
    await gk._process_identity_event(id_bus.pop())
    
    # Login from London (5,500km away) 1 minute later
    id_bus.push({
        "timestamp": (datetime.now(timezone.utc) - timedelta(minutes=9)).isoformat(),
        "event_type": "login_success",
        "user_id": user_id,
        "source_ip": "2.2.2.2",
        "location": {"city": "London", "country": "UK", "lat": 51.50, "lon": -0.12}
    })
    await gk._process_identity_event(id_bus.pop())
    
    alert = triage_bus.pop()
    if alert and alert["rule_id"] == "GK_TRAV_001":
        print(f"  [PASS] Detected Impossible Travel (NY -> London)")
    else:
        print(f"  [FAIL] Failed to detect Impossible Travel. Alert: {alert}")

    # 3. Test NHI Governance (Key Rotation)
    print("\n[TEST 3] Verifying NHI Identity Rotation...")
    with open(get_soc_path("configs", "secrets.json"), "r") as f:
        old_secrets = json.load(f)
    
    await gk.rotate_identities()
    
    with open(get_soc_path("configs", "secrets.json"), "r") as f:
        new_secrets = json.load(f)
    
    if old_secrets != new_secrets:
        print("  [PASS] Agent API keys rotated and persisted to secrets.json")
    else:
        print("  [FAIL] Secrets.json was not updated.")

    print("\n" + "="*60)
    print("  GATEKEEPER VALIDATION COMPLETE")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(test_gatekeeper_intelligence())
