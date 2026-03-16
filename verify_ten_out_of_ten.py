import asyncio
import os
import sys
import json
import time
from datetime import datetime, timezone
from dataclasses import asdict

# Ensure project root is in path
sys.path.append(os.getcwd())

from soc.agents.investigation_manager import InvestigationManager
from soc.agents.librarian import LibrarianAgent
from soc.agents.correlator import CorrelatorAgent
from soc.agents.triage import TriageAgent

async def run_maturity_validation():
    print("="*60)
    print("  SENTINEL 10/10 MATURITY VALIDATION")
    print("="*60)
    
    manager = InvestigationManager()
    librarian = LibrarianAgent()
    correlator = CorrelatorAgent()
    triage = TriageAgent()
    
    # Start agents
    bg_tasks = [
        asyncio.create_task(manager.run()),
        asyncio.create_task(librarian.run()),
        asyncio.create_task(correlator.run()),
        asyncio.create_task(triage.run())
    ]
    
    try:
        # --- TEST 1: RAG Synchronisation (The Race Condition Fix) ---
        print("\n[TEST 1] Verifying RAG Sync barrier...")
        test_case_id = "INC-RAG-SYNC-TEST"
        from soc.agents.investigation_manager import CaseRecord
        case = CaseRecord(
            case_id=test_case_id,
            created_at=datetime.now(timezone.utc).isoformat(),
            updated_at=datetime.now(timezone.utc).isoformat(),
            severity="CRITICAL",
            summary="RAG Synchronisation Stress Test",
            hypothesis="Testing for race condition fix."
        )
        
        # Save and immediately query
        await manager._save_case(case)
        
        results = []
        query_str = "RAG Synchronisation Stress Test"
        for _ in range(10):
            results = await librarian.search(query_str, limit=1)
            if results and results[0]["case_id"] == test_case_id:
                break
            await asyncio.sleep(0.2)
        
        if results and results[0]["case_id"] == test_case_id:
            print(f"  [PASS] Librarian retrieved case '{test_case_id}' (Score: {results[0]['similarity']})")
        else:
            print(f"  [FAIL] Librarian missed the query. Results: {results}")

        # --- TEST 2: Intel Feedback Loop (Correlator -> Triage) ---
        print("\n[TEST 2] Verifying Intel Feedback Loop...")
        bad_ip = "10.0.0.66" # OT SUBNET IP
        
        print(f"  - Feeding Recon and Lateral events for {bad_ip} to Correlator...")
        for i in range(5):
            manager.raw_alerts_bus.push({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "rule_id": "RECON", "rule_name": f"Scan Step {i}", "severity": "WARNING", "source_ip": bad_ip
            })
        manager.raw_alerts_bus.push({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "rule_id": "LATERAL", "rule_name": "SMB Exec", "severity": "CRITICAL", "source_ip": bad_ip
        })
        await asyncio.sleep(3) # Wait for promotion and intel push
        
        print(f"  - Sending VALID OT event (asset_new) from {bad_ip} to Triage...")
        triage.in_bus.push({
            "event_type": "asset_new", "ip": bad_ip, "protocol": "TCP", "status": "allowed",
            "rule_id": "SUSPICIOUS_001", "rule_name": "Unknown Asset on OT VLAN", "severity": "WARNING"
        })
        await asyncio.sleep(3) # Wait for triage cycle
        
        boosted_alerts = []
        while True:
            a = triage.out_bus.pop()
            if not a: break
            if a.get("source_ip") == bad_ip and "INTEL BOOST" in a.get("description", ""):
                boosted_alerts.append(a)
        
        if boosted_alerts:
            print(f"  [PASS] Triage boosted alert severity to {boosted_alerts[0]['severity']} via Intel Feedback!")
            print(f"  [LOG] {boosted_alerts[0]['description']}")
        else:
            print("  [FAIL] Intel Feedback loop did not result in severity boost.")

        # --- TEST 3: Hash Linkage (Forensics -> Correlator) ---
        print("\n[TEST 3] Verifying Hash Linkage...")
        mal_hash = "abc1234567890abcdef"
        test_ip_2 = "172.16.1.100"
        
        print(f"  - Forensics pushing malicious hash for {test_ip_2}...")
        manager.raw_alerts_bus.push({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "rule_id": "FORENSICS_THREAT_HASH",
            "rule_name": "Malicious Artifact",
            "severity": "WARNING",
            "source_ip": test_ip_2,
            "file_hash": mal_hash,
            "description": "Linked via hash."
        })
        await asyncio.sleep(2)
        
        print(f"  - Sending Recon from DIFFERENT IP (10.0.0.99) with SAME hash...")
        manager.raw_alerts_bus.push({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "rule_id": "RECON", "rule_name": "Follow-up Scan", "severity": "WARNING",
            "source_ip": "10.0.0.99",
            "file_hash": mal_hash
        })
        await asyncio.sleep(2)
        
        state = correlator.entity_map.get(test_ip_2)
        if state and len(state.events) > 1:
            print(f"  [PASS] Correlator linked 10.0.0.99 back to {test_ip_2} via malicious hash!")
        else:
            print(f"  [FAIL] Hash linkage failed. Events for {test_ip_2}: {len(state.events) if state else 0}")

    finally:
        manager.is_running = False
        librarian.is_running = False
        correlator.is_running = False
        triage.is_running = False
        for task in bg_tasks:
            task.cancel()
    
    print("\n" + "="*60)
    print("  MATURITY VALIDATION COMPLETE")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(run_maturity_validation())
