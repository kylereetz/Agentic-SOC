import asyncio
import os
import sys
import json
from datetime import datetime, timezone, timedelta

# Ensure project root is in path
sys.path.append(os.getcwd())

from soc.agents.hunter import HunterAgent
from soc.bus.event_queue import EventBus
from soc.bootstrap import get_soc_path

async def test_hunter_intelligence():
    print("="*60)
    print("  QUILL-HUNTER VALIDATION")
    print("="*60)
    
    ha = HunterAgent()
    h_bus = EventBus("hunting_events")
    triage_bus = EventBus("triage_alerts")
    id_bus = EventBus("identity_events")
    
    # Clear buses
    while triage_bus.pop(): pass
    
    # 1. Setup Historical Data (Pre-Hunt)
    print("\n[STEP 1] Injecting historical data into id_bus.processed...")
    # We push an event then manually 'pop' it to move it to processed
    id_bus.push({
        "timestamp": (datetime.now(timezone.utc) - timedelta(days=5)).isoformat(),
        "event_type": "mfa_failure",
        "user_id": "malicious.actor@apt29.com",
        "source_ip": "1.2.3.4"
    })
    id_bus.pop() # Move to processed
    
    # 2. Test Proactive Hunt
    print("\n[TEST 1] Verifying Proactive Hunt (Backtracking)...")
    h_bus.push({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": "new_intel_lead",
        "intel_source": "CISA-AL-2026-003",
        "hypothesis": "APT29 Campaign Targeting Manufacturing MFA",
        "keywords": ["apt29.com", "1.2.3.4"],
        "lookback_days": 10
    })
    
    event = h_bus.pop()
    if event: await ha._process_hunting_event(event)
    
    alert = triage_bus.pop()
    if alert and "HUNT MATCH" in alert["rule_name"]:
        print(f"  [PASS] Hunter identified historical match for APT29 lead.")
        print(f"  [PASS] Matches found: {alert['metadata']['matched_events']}")
    else:
         print(f"  [FAIL] Hunter failed to find historical match. Alert: {alert}")

    print("\n" + "="*60)
    print("  HUNTER VALIDATION COMPLETE")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(test_hunter_intelligence())
